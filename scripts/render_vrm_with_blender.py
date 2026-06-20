#!/usr/bin/env python3
"""Blender で import 配下の VRM 素材からアップロード用動画を生成します。"""

from __future__ import annotations

import argparse
import math
import sys
import tarfile
from datetime import datetime
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    """Blender 実行時に受け取る動画生成用の引数パーサーを作成します。"""

    parser = argparse.ArgumentParser(description="Blender で VRM 素材をレンダリングします。")
    parser.add_argument("--repo-root", default=".", help="repository root のパス。")
    parser.add_argument("--target", default="video", choices=["video", "shorts", "both"], help="生成対象。")
    parser.add_argument("--output", default="export/update.mp4", help="通常動画の出力先。")
    parser.add_argument("--shorts-output", default="export/update-shorts.mp4", help="Shorts 動画の出力先。")
    parser.add_argument("--duration", type=int, default=10, help="通常動画の秒数。")
    parser.add_argument("--shorts-duration", type=int, default=5, help="Shorts 動画の秒数。")
    parser.add_argument("--title", default="", help="通常動画のタイトル。")
    parser.add_argument("--message", default="", help="通常動画の補足メッセージ。")
    parser.add_argument("--shorts-title", default="", help="Shorts 動画のタイトル。")
    parser.add_argument("--shorts-message", default="", help="Shorts 動画の補足メッセージ。")
    parser.add_argument("--render-mode", default="viewport", choices=["viewport", "final", "prepare"], help="レンダリング方式。")
    return parser


def resolve_path(repo_root: Path, value: str) -> Path:
    """相対パスを repository root 基準の絶対パスへ変換します。"""

    path = Path(value)
    if path.is_absolute():
        return path
    return repo_root / path


def find_first_file(directory: Path, pattern: str) -> Path | None:
    """指定ディレクトリ内で最初に見つかったファイルを返します。"""

    matches = sorted(path for path in directory.glob(pattern) if path.is_file())
    if not matches:
        return None
    return matches[0]


def count_unity_assets(unitypackage: Path | None) -> int:
    """unitypackage 内の asset エントリ数を数えます。"""

    if unitypackage is None or not unitypackage.exists():
        return 0

    try:
        with tarfile.open(unitypackage, "r:gz") as archive:
            return sum(1 for member in archive.getmembers() if member.name.endswith("/asset"))
    except tarfile.TarError:
        return 0


def blender_imports():
    """Blender 実行環境でのみ bpy と mathutils を import します。"""

    import bpy  # type: ignore
    from mathutils import Vector  # type: ignore

    return bpy, Vector


def clear_scene(bpy) -> None:
    """現在の Blender scene 内の object をすべて削除します。"""

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def import_vrm(bpy, vrm_path: Path) -> list:
    """VRM ファイルを glTF として Blender scene に読み込みます。"""

    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(vrm_path))
    imported = [obj for obj in bpy.data.objects if obj not in before]
    return imported


def scene_bounds(objects: list, Vector):
    """読み込んだ object 群の world 座標 bounding box を計算します。"""

    points = []
    for obj in objects:
        if obj.type != "MESH":
            continue
        points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)

    if not points:
        return Vector((0.0, 0.0, 0.0)), 1.0

    min_point = Vector((min(point.x for point in points), min(point.y for point in points), min(point.z for point in points)))
    max_point = Vector((max(point.x for point in points), max(point.y for point in points), max(point.z for point in points)))
    center = (min_point + max_point) * 0.5
    size = max((max_point - min_point).x, (max_point - min_point).y, (max_point - min_point).z)
    return center, max(size, 0.001)


def parent_to_turntable(bpy, objects: list, center) -> object:
    """読み込んだ object を回転用 Empty に親子付けします。"""

    empty = bpy.data.objects.new("VRM turntable root", None)
    bpy.context.collection.objects.link(empty)
    empty.location = center

    for obj in objects:
        if obj.parent is None:
            obj.parent = empty
            obj.matrix_parent_inverse = empty.matrix_world.inverted()

    return empty


def find_armature(bpy):
    """scene 内で最初に見つかった Armature object を返します。"""

    for obj in bpy.data.objects:
        if obj.type == "ARMATURE":
            return obj
    return None


def add_text(bpy, text: str, location: tuple[float, float, float], size: float, align: str = "CENTER") -> object:
    """scene 内に説明用の text object を追加します。"""

    bpy.ops.object.text_add(location=location, rotation=(math.radians(72), 0.0, 0.0))
    obj = bpy.context.object
    obj.name = "caption"
    obj.data.body = text
    obj.data.align_x = align
    obj.data.align_y = "CENTER"
    obj.data.size = size
    obj.data.materials.append(make_material(bpy, "caption material", (0.08, 0.07, 0.16, 1.0)))
    return obj


def make_material(bpy, name: str, color: tuple[float, float, float, float]) -> object:
    """指定色の diffuse material を作成または取得します。"""

    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name)
    material.diffuse_color = color
    return material


def add_background(bpy, Vector, horizontal: bool) -> None:
    """動画用の床、背景、装飾を配置します。"""

    bg_color = (0.72, 0.87, 0.96, 1.0)
    accent_color = (1.0, 0.38, 0.67, 1.0)
    floor_material = make_material(bpy, "soft blue background", bg_color)
    accent_material = make_material(bpy, "pink accent", accent_color)

    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, -0.02))
    floor = bpy.context.object
    floor.name = "background floor"
    floor.data.materials.append(floor_material)

    for index, x in enumerate((-2.8, 2.8) if horizontal else (-1.4, 1.4)):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.08, location=(x, -0.6, 1.2 + index * 0.45))
        sphere = bpy.context.object
        sphere.name = "accent sphere"
        sphere.scale = (1.0, 1.0, 0.15)
        sphere.data.materials.append(accent_material)

    bpy.context.scene.world.color = (0.92, 0.96, 1.0)


def configure_camera_and_light(bpy, Vector, center, size: float, horizontal: bool) -> None:
    """モデル全体が見える camera と light を配置します。"""

    camera_distance = max(size * (2.2 if horizontal else 2.7), 2.2)
    camera_z = center.z + size * (0.14 if horizontal else 0.22)
    target = Vector((center.x, center.y, center.z + size * (0.05 if horizontal else 0.08)))

    bpy.ops.object.light_add(type="AREA", location=(0.0, -2.6, center.z + size * 1.4))
    light = bpy.context.object
    light.name = "main softbox"
    light.data.energy = 520
    light.data.size = 4.0

    bpy.ops.object.camera_add(location=(center.x, center.y - camera_distance, camera_z))
    camera = bpy.context.object
    bpy.context.scene.camera = camera
    direction = target - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    camera.data.lens = 36 if horizontal else 48
    camera.data.dof.use_dof = True
    camera.data.dof.focus_distance = camera_distance
    camera.data.dof.aperture_fstop = 8


def configure_render_settings(bpy, output: Path, width: int, height: int, duration: int) -> None:
    """Blender の MP4 レンダリング設定を適用します。"""

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 1
    scene.cycles.preview_samples = 1
    scene.cycles.use_denoising = False
    scene.frame_start = 1
    scene.frame_end = duration * 30
    scene.render.fps = 30
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(output)
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    scene.render.ffmpeg.ffmpeg_preset = "GOOD"
    scene.render.ffmpeg.audio_codec = "AAC"


def animate_turntable(bpy, root: object, duration: int, shorts: bool) -> None:
    """VRM model をゆっくり回転させる keyframe animation を設定します。"""

    scene = bpy.context.scene
    scene.frame_set(scene.frame_start)
    root.rotation_euler = (0.0, 0.0, math.radians(-18 if shorts else -30))
    root.keyframe_insert(data_path="rotation_euler", frame=scene.frame_start)

    scene.frame_set(scene.frame_end)
    root.rotation_euler = (0.0, 0.0, math.radians(18 if shorts else 330))
    root.keyframe_insert(data_path="rotation_euler", frame=scene.frame_end)

    if root.animation_data and root.animation_data.action:
        for curve in root.animation_data.action.fcurves:
            for keyframe in curve.keyframe_points:
                keyframe.interpolation = "BEZIER"


def set_pose_rotation(armature, bone_name: str, rotation: tuple[float, float, float], frame: int) -> None:
    """指定ボーンへ Euler 回転を設定し、keyframe を追加します。"""

    pose_bone = armature.pose.bones.get(bone_name)
    if pose_bone is None:
        return
    pose_bone.rotation_mode = "XYZ"
    pose_bone.rotation_euler = tuple(math.radians(value) for value in rotation)
    pose_bone.keyframe_insert(data_path="rotation_euler", frame=frame)


def set_root_motion(root: object, rotation_z: float, frame: int, rotation_x: float = 0.0) -> None:
    """モデル全体の向きに keyframe を追加します。"""

    root.rotation_euler = (math.radians(rotation_x), 0.0, math.radians(rotation_z + 180))
    root.keyframe_insert(data_path="rotation_euler", frame=frame)


def set_pose_location(armature, bone_name: str, location: tuple[float, float, float], frame: int) -> None:
    """指定ボーンへ位置を設定し、keyframe を追加します。"""

    pose_bone = armature.pose.bones.get(bone_name)
    if pose_bone is None:
        return
    pose_bone.location = location
    pose_bone.keyframe_insert(data_path="location", frame=frame)


def animate_radio_exercise(bpy, root: object, duration: int) -> None:
    """30秒のラジオ体操風モーションを設定します。

    厳密な公式振り付けではなく、腕を開く、上げる、前後屈、体をひねる、
    屈伸するといった動きが動画内で分かるようにした簡易モーションです。
    """

    scene = bpy.context.scene
    armature = find_armature(bpy)
    if armature is None:
        animate_turntable(bpy, root, duration, shorts=False)
        return

    fps = scene.render.fps
    end_frame = scene.frame_end
    keyframes = [
        (1, "準備", -10, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        (fps * 2, "左ステップ", -6, -12, 10, -18, 12, -10, 18, -1, 0, 0),
        (fps * 4, "右ステップ", 4, 4, 0, -4, -4, 0, 4, 1, 0, 0),
        (fps * 6, "腕を上へ", 0, -62, 0, -28, 62, 0, 28, 0, 0, 0),
        (fps * 8, "前屈", -2, 8, 16, -10, -8, -16, 10, 0, 34, 18),
        (fps * 10, "後屈", 28, -38, 8, -12, 38, -8, 12, 0, -34, 6),
        (fps * 12, "深い屈伸", -20, -18, 18, -16, 18, -18, 16, 0, 8, 34),
        (fps * 14, "立ち上がり", 0, -8, 0, -10, 8, 0, 10, 0, 0, 0),
        (fps * 16, "左ひねり", -18, -34, -12, -26, 34, 12, 26, -1, 0, 8),
        (fps * 18, "中央屈伸", 16, -14, 10, -14, 14, -10, 14, 0, 4, 24),
        (fps * 20, "右ひねり", 18, -34, 12, -26, 34, -12, 26, 1, 0, 8),
        (fps * 22, "左足前", -10, -12, 32, -22, 12, -32, 22, -1, 6, 10),
        (fps * 24, "右足前", 10, -12, -28, 22, 12, 28, -22, 1, 6, 10),
        (fps * 26, "前後屈戻し", -18, -18, 14, -18, 18, -14, 18, 0, -18, 12),
        (fps * 28, "大きく深呼吸", -6, -55, 8, -24, 55, -8, 24, -1, 0, 0),
        (end_frame, "終了", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    ]

    left_arm = "Character1_LeftArm"
    left_forearm = "Character1_LeftForeArm"
    right_arm = "Character1_RightArm"
    right_forearm = "Character1_RightForeArm"
    lower_spine = "Character1_Spine"
    spine = "Character1_Spine1"
    upper_spine = "Character1_Spine2"
    hips = "Character1_Hips"
    left_leg = "Character1_LeftUpLeg"
    right_leg = "Character1_RightUpLeg"
    left_knee = "Character1_LeftLeg"
    right_knee = "Character1_RightLeg"
    left_foot = "Character1_LeftFoot"
    right_foot = "Character1_RightFoot"
    neck = "Character1_Neck"
    head = "Character1_Head"

    for index, (frame, _label, root_z, left_x, left_y, left_z, right_x, right_y, right_z, step, bow, squat) in enumerate(keyframes):
        frame = min(int(frame), end_frame)
        step_phase = math.sin(index * math.pi * 0.5)
        bounce = 0.022 if step == 0 else 0.052
        squat_drop = squat * 0.0036
        root_pitch = bow * 0.42 - squat * 0.05
        set_root_motion(root, root_z, frame, rotation_x=root_pitch)
        root.location.x = step * 0.035
        root.location.z = abs(step_phase) * bounce - squat_drop - max(bow, 0) * 0.0008
        root.keyframe_insert(data_path="location", frame=frame)
        set_pose_rotation(armature, left_arm, (left_x, left_y, left_z), frame)
        set_pose_rotation(armature, left_forearm, (left_x * 0.35, 0, left_z * 0.4), frame)
        set_pose_rotation(armature, right_arm, (right_x, right_y, right_z), frame)
        set_pose_rotation(armature, right_forearm, (right_x * 0.35, 0, right_z * 0.4), frame)
        set_pose_rotation(armature, lower_spine, (bow * 0.35, 0, root_z * 0.25), frame)
        set_pose_rotation(armature, spine, (bow * 0.75 + step * -4, 0, root_z * 0.55), frame)
        set_pose_rotation(armature, upper_spine, (bow * 0.55, 0, root_z * 0.35), frame)
        set_pose_rotation(armature, hips, (4 + bow * 0.34 + squat * 0.30 + abs(root_z) * 0.25, step * 3, root_z * 0.22), frame)
        set_pose_rotation(armature, neck, (-bow * 0.45, 0, root_z * -0.15), frame)
        set_pose_rotation(armature, head, (-bow * 0.35, 0, root_z * -0.15), frame)
        set_pose_location(armature, hips, (step * 0.006, bow * -0.0008, abs(step_phase) * 0.012 - squat_drop * 0.35), frame)

        left_stride = -18 if step < 0 else 15 if step > 0 else 7
        right_stride = 15 if step < 0 else -18 if step > 0 else 7
        left_knee_bend = (18 if step < 0 else 6 if step > 0 else 14) + squat * 1.35
        right_knee_bend = (6 if step < 0 else 18 if step > 0 else 14) + squat * 1.35
        left_ankle = -8 if step < 0 else 6 if step > 0 else 0
        right_ankle = 6 if step < 0 else -8 if step > 0 else 0
        set_pose_rotation(armature, left_leg, (left_stride + squat * 0.46 - bow * 0.12, step * 4, -step * 3), frame)
        set_pose_rotation(armature, right_leg, (right_stride + squat * 0.46 - bow * 0.12, step * 4, -step * 3), frame)
        set_pose_rotation(armature, left_knee, (left_knee_bend, 0, 0), frame)
        set_pose_rotation(armature, right_knee, (right_knee_bend, 0, 0), frame)
        set_pose_rotation(armature, left_foot, (left_ankle - squat * 0.48 + bow * 0.15, 0, step * 2), frame)
        set_pose_rotation(armature, right_foot, (right_ankle - squat * 0.48 + bow * 0.15, 0, step * 2), frame)

    for animated in [root, armature]:
        if animated.animation_data and animated.animation_data.action:
            for curve in animated.animation_data.action.fcurves:
                for keyframe in curve.keyframe_points:
                    keyframe.interpolation = "BEZIER"


def render_video(
    repo_root: Path,
    output: Path,
    title: str,
    message: str,
    duration: int,
    shorts: bool,
    render_mode: str,
) -> None:
    """VRM と unitypackage 情報を使って 1 本の MP4 動画をレンダリングします。"""

    bpy, Vector = blender_imports()
    import_dir = repo_root / "import"
    vrm_path = find_first_file(import_dir, "*.vrm")
    unitypackage_path = find_first_file(import_dir, "*.unitypackage")
    if vrm_path is None:
        raise FileNotFoundError("import/*.vrm が見つかりません。")

    output.parent.mkdir(parents=True, exist_ok=True)
    clear_scene(bpy)
    imported = import_vrm(bpy, vrm_path)
    center, size = scene_bounds(imported, Vector)
    root = parent_to_turntable(bpy, imported, center)

    unity_assets = count_unity_assets(unitypackage_path)
    horizontal = not shorts
    add_background(bpy, Vector, horizontal=horizontal)
    configure_camera_and_light(bpy, Vector, center, size, horizontal=horizontal)

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if shorts:
        width, height = 1080, 1920
        add_text(bpy, title, (0.0, -1.25, center.z + size * 1.35), 0.22)
        add_text(bpy, message, (0.0, -1.25, center.z - size * 0.55), 0.095)
        add_text(bpy, f"{vrm_path.name} / Unity assets {unity_assets} / {generated_at}", (0.0, -1.25, center.z - size * 0.85), 0.065)
    else:
        width, height = 1280, 720
        add_text(bpy, title, (0.0, -1.35, center.z + size * 1.1), 0.18)
        add_text(bpy, message, (0.0, -1.35, center.z - size * 0.52), 0.075)
        add_text(bpy, f"source {vrm_path.name} + {unitypackage_path.name if unitypackage_path else 'no unitypackage'} / Unity assets {unity_assets}", (0.0, -1.35, center.z - size * 0.78), 0.055)
        add_text(bpy, f"rendered with Blender / {generated_at}", (0.0, -1.35, center.z - size * 0.95), 0.05)

    configure_render_settings(bpy, output, width, height, duration)
    if shorts:
        animate_turntable(bpy, root, duration, shorts=shorts)
    else:
        animate_radio_exercise(bpy, root, duration)
    bpy.ops.wm.save_as_mainfile(filepath=str(output.with_suffix(".blend")))
    if render_mode == "prepare":
        return
    if render_mode == "viewport":
        bpy.ops.render.opengl(animation=True, view_context=False)
    else:
        bpy.ops.render.render(animation=True)


def main() -> None:
    """Blender background mode から通常動画または Shorts を生成します。"""

    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    args = build_parser().parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    title_suffix = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if args.target in {"video", "both"}:
        render_video(
            repo_root=repo_root,
            output=resolve_path(repo_root, args.output),
            title=args.title or f"VRM更新動画 {title_suffix}",
            message=args.message or "Blender が import/avator.vrm を読み込んで生成しました。",
            duration=args.duration,
            shorts=False,
            render_mode=args.render_mode,
        )

    if args.target in {"shorts", "both"}:
        render_video(
            repo_root=repo_root,
            output=resolve_path(repo_root, args.shorts_output),
            title=args.shorts_title or f"VRM Shorts {title_suffix} #Shorts",
            message=args.shorts_message or "VRM素材から生成した要約Shortsです。",
            duration=args.shorts_duration,
            shorts=True,
            render_mode=args.render_mode,
        )


if __name__ == "__main__":
    main()
