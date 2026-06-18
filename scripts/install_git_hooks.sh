#!/usr/bin/env bash
set -euo pipefail

# repository ルートを基準に、同梱の .githooks を Git hooks として有効化します。
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
git -C "${repo_root}" config core.hooksPath .githooks
chmod +x "${repo_root}/.githooks/pre-push"
echo "Git hooks installed: core.hooksPath=.githooks"
