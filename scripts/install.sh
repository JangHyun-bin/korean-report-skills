#!/usr/bin/env bash
# 한국어 문서 스킬 설치
#
#   bash scripts/install.sh                 Claude Code + Codex + Cursor 전부에 파일 복사
#   bash scripts/install.sh claude          Claude Code 만
#   bash scripts/install.sh codex cursor    골라서
#   bash scripts/install.sh --project       현재 저장소에만
#
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/plugins/korean-report/skills"
SKILLS=(korean-report-doc korean-report-style)
KNOWN=(claude codex cursor)

AGENTS=(); SCOPE="global"
for a in "$@"; do
  case "$a" in
    claude|codex|cursor) AGENTS+=("$a") ;;
    all) AGENTS=("${KNOWN[@]}") ;;
    --project) SCOPE="project" ;;
    -h|--help) sed -n '2,9p' "$0"; exit 0 ;;
    *) echo "사용법: bash scripts/install.sh [claude|codex|cursor|all]... [--project]" >&2; exit 1 ;;
  esac
done
[[ ${#AGENTS[@]} -eq 0 ]] && AGENTS=("${KNOWN[@]}")

for ag in "${AGENTS[@]}"; do
  if [[ "$SCOPE" == "global" ]]; then base="$HOME/.$ag/skills"; else base="./.$ag/skills"; fi
  mkdir -p "$base"
  for s in "${SKILLS[@]}"; do
    rm -rf "${base:?}/$s"
    cp -R "$SRC/$s" "$base/$s"
    [[ -f "$base/$s/SKILL.md" ]] || { echo "  실패  $base/$s" >&2; exit 1; }
    echo "  설치됨  $base/$s"
  done
done

echo
echo "완료. 세션을 새로 시작하면 적용된다."
echo "확인 — /skills 를 입력해 목록에 보이는지 본다."
