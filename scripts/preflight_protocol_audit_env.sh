#!/usr/bin/env bash
set -euo pipefail

INSTALL_MISSING="false"
REQUIRE_GH_AUTH="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --install-missing)
      INSTALL_MISSING="true"
      shift
      ;;
    --require-gh-auth)
      REQUIRE_GH_AUTH="true"
      shift
      ;;
    -h|--help)
      cat <<'USAGE'
usage: bash scripts/preflight_protocol_audit_env.sh [--install-missing] [--require-gh-auth]

Checks local audit execution prerequisites:
  - GitHub CLI auth readiness (gh auth status -h github.com)
  - actionlint availability
  - ast-grep availability (sg or ast-grep)
  - gitleaks availability

Options:
  --install-missing   Try to install missing actionlint/ast-grep/gitleaks locally.
  --require-gh-auth   Exit non-zero when gh auth is not ready.
USAGE
      exit 0
      ;;
    *)
      echo "[FAIL] unknown argument: $1"
      exit 2
      ;;
  esac
done

ACTIONLINT_CMD=""
AST_GREP_CMD=""
GITLEAKS_CMD=""
GH_CMD=""
MISSING_TOOLS=()

if command -v gh >/dev/null 2>&1; then
  GH_CMD="$(command -v gh)"
fi

resolve_actionlint() {
  if command -v actionlint >/dev/null 2>&1; then
    ACTIONLINT_CMD="$(command -v actionlint)"
    return 0
  fi
  if [[ -x "/tmp/identity-tools/bin/actionlint" ]]; then
    ACTIONLINT_CMD="/tmp/identity-tools/bin/actionlint"
    return 0
  fi
  ACTIONLINT_CMD=""
  return 1
}

resolve_ast_grep() {
  if command -v sg >/dev/null 2>&1; then
    AST_GREP_CMD="$(command -v sg)"
    return 0
  fi
  if command -v ast-grep >/dev/null 2>&1; then
    AST_GREP_CMD="$(command -v ast-grep)"
    return 0
  fi
  if [[ -x "/tmp/identity-tools/node_modules/.bin/ast-grep" ]]; then
    AST_GREP_CMD="/tmp/identity-tools/node_modules/.bin/ast-grep"
    return 0
  fi
  AST_GREP_CMD=""
  return 1
}

resolve_gitleaks() {
  if command -v gitleaks >/dev/null 2>&1; then
    GITLEAKS_CMD="$(command -v gitleaks)"
    return 0
  fi
  GITLEAKS_CMD=""
  return 1
}

install_actionlint() {
  if resolve_actionlint; then
    return 0
  fi
  echo "[INFO] actionlint missing, attempting install..."
  if command -v brew >/dev/null 2>&1; then
    brew install actionlint || true
  elif command -v go >/dev/null 2>&1; then
    go install github.com/rhysd/actionlint/cmd/actionlint@latest || true
  else
    echo "[WARN] cannot auto-install actionlint (brew/go unavailable)"
  fi
  resolve_actionlint || return 1
  return 0
}

install_ast_grep() {
  if resolve_ast_grep; then
    return 0
  fi
  echo "[INFO] ast-grep missing, attempting install..."
  if command -v npm >/dev/null 2>&1; then
    npm install -g @ast-grep/cli || true
  else
    echo "[WARN] cannot auto-install ast-grep (npm unavailable)"
  fi
  resolve_ast_grep || return 1
  return 0
}

install_gitleaks() {
  if resolve_gitleaks; then
    return 0
  fi
  echo "[INFO] gitleaks missing, attempting install..."
  if command -v brew >/dev/null 2>&1; then
    brew install gitleaks || true
  else
    echo "[WARN] cannot auto-install gitleaks (brew unavailable)"
  fi
  resolve_gitleaks || return 1
  return 0
}

if [[ "$INSTALL_MISSING" == "true" ]]; then
  install_actionlint || true
  install_ast_grep || true
  install_gitleaks || true
else
  resolve_actionlint || true
  resolve_ast_grep || true
  resolve_gitleaks || true
fi

if [[ -z "$ACTIONLINT_CMD" ]]; then
  MISSING_TOOLS+=("actionlint")
else
  echo "[OK] actionlint ready: $ACTIONLINT_CMD"
fi

if [[ -z "$AST_GREP_CMD" ]]; then
  MISSING_TOOLS+=("ast-grep")
else
  echo "[OK] ast-grep ready: $AST_GREP_CMD"
fi

if [[ -z "$GITLEAKS_CMD" ]]; then
  MISSING_TOOLS+=("gitleaks")
else
  echo "[OK] gitleaks ready: $GITLEAKS_CMD"
fi

GH_AUTH_READY="false"
if [[ -n "$GH_CMD" ]]; then
  if "$GH_CMD" auth status -h github.com >/dev/null 2>&1; then
    GH_AUTH_READY="true"
    echo "[OK] gh auth ready: $GH_CMD (host=github.com)"
  else
    echo "[WARN] gh auth not ready (host=github.com)"
    echo "[INFO] readiness in strict-union mode may fail with IP-CAP-003; this is expected environment state, not protocol regression."
    echo "[INFO] fix: gh auth login -h github.com --web -s \"repo,read:org,gist,workflow\""
  fi
else
  echo "[WARN] gh command not found; GitHub capability checks may block readiness (IP-CAP-003)."
fi

if [[ "${#MISSING_TOOLS[@]}" -gt 0 ]]; then
  echo "[FAIL] missing local audit tools: ${MISSING_TOOLS[*]}"
  echo "[INFO] retry with: bash scripts/preflight_protocol_audit_env.sh --install-missing"
  exit 1
fi

if [[ "$REQUIRE_GH_AUTH" == "true" && "$GH_AUTH_READY" != "true" ]]; then
  echo "[FAIL] gh auth is required by this preflight profile but is not ready"
  exit 2
fi

echo "[OK] protocol audit preflight completed"
echo "     tools_ready=true gh_auth_ready=${GH_AUTH_READY} require_gh_auth=${REQUIRE_GH_AUTH}"
exit 0
