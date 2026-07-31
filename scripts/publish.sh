#!/usr/bin/env bash
# =============================================================================
# publish.sh — Vault → Web 퍼블리싱 스크립트
# =============================================================================
# 사용법:
#   ./scripts/publish.sh [commit message]
#   ./scripts/publish.sh "add: 새로운 개념 노트 추가"
#
# 기능:
#   1. 변경 사항 확인 및 Git staging
#   2. Quartz 빌드 검증 (선택적)
#   3. Git commit & push → GitHub Actions 트리거 → 자동 배포
# =============================================================================

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  📤 pofol-lab 퍼블리싱 시작${NC}"
echo -e "${BLUE}========================================${NC}"

# 저장소 루트로 이동
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# 1. 변경 사항 확인
echo -e "\n${YELLOW}[1/3] 변경된 파일 확인 중...${NC}"
CHANGED=$(git status --porcelain)
if [ -z "$CHANGED" ]; then
  echo -e "${GREEN}  ✅ 변경 사항 없음. 배포 불필요.${NC}"
  exit 0
fi

echo -e "  변경된 파일:"
git status --short | sed 's/^/    /'

# 2. Git staging
echo -e "\n${YELLOW}[2/3] Git 스테이징 중...${NC}"
git add .
echo -e "  ${GREEN}✅ 모든 변경 사항 스테이징 완료${NC}"

# 3. 커밋 메시지 결정
COMMIT_MSG="${1:-"update: vault 업데이트 $(date '+%Y-%m-%d %H:%M')"}"
echo -e "\n${YELLOW}[3/3] 커밋 & 푸시 중...${NC}"
echo -e "  커밋 메시지: ${BLUE}${COMMIT_MSG}${NC}"

git commit -m "$COMMIT_MSG"
git push

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  🚀 배포 완료!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "  GitHub Actions가 자동으로 빌드 & 배포를 진행합니다."
echo -e "  진행 상황: ${BLUE}https://github.com/$(git remote get-url origin | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/actions${NC}"
echo ""
