#!/usr/bin/env bash
set -euo pipefail

REPO_PATH="${1:-identity-protocol-local}"
TARGET_BRANCH="${2:-main}"

if [ ! -d "$REPO_PATH/.git" ]; then
  echo "[FAIL] repo not found: $REPO_PATH"
  echo "hint: git clone https://github.com/brianlyang/identity-protocol.git $REPO_PATH"
  exit 1
fi

cd "$REPO_PATH"

echo "[INFO] repo: $(pwd)"

git fetch origin "$TARGET_BRANCH" >/dev/null
LOCAL_SHA="$(git rev-parse HEAD)"
REMOTE_SHA="$(git rev-parse "origin/${TARGET_BRANCH}")"

if [ "$LOCAL_SHA" != "$REMOTE_SHA" ]; then
  echo "[FAIL] local protocol repo is stale"
  echo "local : $LOCAL_SHA"
  echo "remote: $REMOTE_SHA"
  echo "run: git checkout $TARGET_BRANCH && git pull --ff-only"
  exit 1
fi

echo "[OK] local protocol repo synced with origin/$TARGET_BRANCH"
echo "sync_sha=$LOCAL_SHA"
