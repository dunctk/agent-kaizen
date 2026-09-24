#!/usr/bin/env bash
set -euo pipefail

bad_files="$(
  git ls-files |
    grep -E '(^|/).env$|(^|/).env.[^/]+$|.(pem|key|p12|pfx)$|(^|/)id_(rsa|dsa|ecdsa|ed25519)$' |
    grep -vE '(^|/).env.example$' || true
)"

if [[ -n "$bad_files" ]]; then
  echo "Potential secret-bearing files are tracked:"
  echo "$bad_files"
  exit 1
fi

pattern='-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----|(AKIA|ASIA)[A-Z0-9]{16}|gh[pousr]_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}'

if git grep -nEI "$pattern" -- .   ':(exclude)scripts/check-secrets.sh'   ':(exclude)SECURITY.md' >/tmp/agent-kaizen-secret-hits.txt 2>/dev/null; then
  echo "Potential committed secret detected:"
  cat /tmp/agent-kaizen-secret-hits.txt
  echo
  echo "If this is a false positive, replace the realistic token with an obviously fake placeholder."
  exit 1
fi

echo "Secret check passed."
