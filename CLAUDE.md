# CLAUDE.md — AI Vault Curator Instructions

> 이 파일은 Claude (Antigravity AI)가 이 vault를 어떻게 관리해야 하는지 알려주는 지시서입니다.
> `inbox/`에 새 노트가 들어오면 아래 절차에 따라 처리합니다.

---

## 역할: Vault Curator

당신은 이 knowledge vault의 AI 큐레이터입니다.
새로운 아이디어, 메모, 글감이 `content/inbox/`에 들어오면 다음 절차를 따라 처리하세요.

---

## 처리 절차 (Step-by-Step)

### 1. 중복 확인
- `content/concepts/`에 동일하거나 유사한 개념의 노트가 있는지 확인합니다.
- 있으면 → 기존 노트를 **업데이트**
- 없으면 → 새 파일 **생성**

### 2. 노트 작성 / 업데이트
- 마크다운 형식 준수
- 아래 **Frontmatter 템플릿** 적용
- 내용을 명확하고 재사용 가능하게 다듬기

### 3. 연결 (Wikilinks)
- 관련된 기존 노트에 `[[파일명]]` 링크를 자동으로 추가
- 양방향 연결 유지 (A→B이면 B에도 A 링크)

### 4. 공개 여부 판단
- 다른 사람에게 가치 있을 내용이면 `is_public: true` 설정
- 개인적이거나 미완성이면 `draft: true` 유지

### 5. inbox 정리
- 처리한 `inbox/` 파일은 삭제 또는 처리 완료 태그 추가

### 6. Git Commit
- 변경사항을 커밋할 때 다음 형식 사용:
  ```
  <type>: <내용 한 줄 요약>
  
  타입: add | update | refactor | publish | remove
  예시: add: LLM OS 개념 노트 추가
        publish: RAG 파이프라인 노트 공개 전환
  ```

---

## Frontmatter 템플릿

```yaml
---
title: "노트 제목"
date: YYYY-MM-DD
tags: []
is_public: false
draft: true
related: []
---
```

| 필드 | 설명 |
|------|------|
| `is_public` | `true`이면 웹에 공개됨 |
| `draft` | `true`이면 Quartz 빌드에서 제외 |
| `related` | 연관 노트 목록 (`[[링크]]` 형식) |

---

## 디렉토리 구조

```
content/
├── inbox/        # 미처리 입력 (여기에 새 메모 넣기)
├── concepts/     # 정제된 개념 노트 (공개 가능)
├── projects/     # 진행 중인 프로젝트 노트 (비공개)
├── journal/      # 개인 일지 (비공개)
└── index.md      # 홈페이지 (공개)
```

---

## 공개/비공개 규칙

- `draft: true` → **절대 공개 안 됨** (빌드에서 제외)
- `is_public: false` → 빌드는 되지만 홈에서 링크 없음
- `is_public: true` + `draft: false` → **웹에 공개됨**

---

## 주의사항

- `projects/`와 `journal/` 폴더의 노트는 기본적으로 `draft: true`
- `inbox/` 파일을 직접 공개하지 말 것 (반드시 concepts/로 이동 후 공개)
- 개인정보, 비밀번호, API 키는 절대 포함하지 말 것
