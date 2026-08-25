#!/usr/bin/env bash
# Every offline suite. test_live.py is separate: it needs an API key and costs money.
set -uo pipefail
cd "$(dirname "$0")"
fail=0
for t in test_static test_twolevel test_layouts test_poster; do
  printf '%-16s ' "$t"
  out=$(python3 "$t.py" 2>&1 | grep -v "ScriptRunContext\|WARNING streamlit")
  if printf '%s' "$out" | grep -q "PASSED"; then
    printf '%s\n' "$(printf '%s' "$out" | grep 'PASSED' | tail -1)"
  else
    echo "FAILED"; printf '%s\n' "$out" | tail -12; fail=1
  fi
done
exit $fail
