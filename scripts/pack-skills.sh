#!/usr/bin/env bash
# claude.ai 웹 업로드용 .skill 아카이브를 만든다.
#
#   bash scripts/pack-skills.sh              dist/ 에 두 개를 만든다
#   bash scripts/pack-skills.sh --verify     기존 아카이브가 skills/ 와 같은지만 본다
#
# .skill 은 스킬 폴더를 최상위로 담은 zip 이다.
# 폴더가 한 겹 더 들어가면 인식되지 않으므로 반드시 skills/ 안에서 압축한다.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS=(korean-report-doc korean-report-style)
OUT="$ROOT/dist"
MODE="${1:-pack}"

command -v zip >/dev/null || { echo "zip 이 필요하다" >&2; exit 1; }
mkdir -p "$OUT"

for s in "${SKILLS[@]}"; do
  target="$OUT/$s.skill"
  if [[ "$MODE" == "--verify" ]]; then
    [[ -f "$target" ]] || { echo "  없음  $target — 먼저 pack 한다" >&2; exit 1; }
    tmp="$(mktemp -d)"
    unzip -q "$target" -d "$tmp"
    if diff -r -x '__pycache__' -x '*.pyc' "$ROOT/skills/$s" "$tmp/$s" >/dev/null; then
      echo "  일치  $s.skill"
    else
      echo "  불일치 $s.skill — skills/$s 와 내용이 다르다. 다시 pack 한다." >&2
      diff -r -x '__pycache__' -x '*.pyc' "$ROOT/skills/$s" "$tmp/$s" || true
      rm -rf "$tmp"; exit 1
    fi
    rm -rf "$tmp"
  else
    rm -f "$target"
    ( cd "$ROOT/skills" && zip -q -r -X "$target" "$s" -x '*/__pycache__/*' '*.pyc' )
    echo "  생성  $target  ($(unzip -l "$target" | tail -1 | awk '{print $2}') 파일)"
  fi
done
