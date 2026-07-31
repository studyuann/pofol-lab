# 🧠 pofol-lab — 개인 지식 퍼블리싱 스택

> **Obsidian + AI (Claude) + Git + Quartz** 기반 자동화 지식 공개 시스템
> 마크다운으로 쓰고, AI가 정제하고, `git push` 하나로 웹에 배포됩니다.

---

## ⚡ 전체 흐름 한눈에 보기

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   ① 작성                ② AI 처리              ③ 배포          │
│                                                                 │
│  [Obsidian]   ───►   [Claude AI]   ───►   [Git Push]  ───► 🌐  │
│  content/             CLAUDE.md           GitHub             Web│
│  inbox/에             지시에 따라          Actions가          에 │
│  메모 작성            정제·분류·연결        자동 빌드          공개│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 단계별 상세

| 단계 | 누가 | 무엇을 | 어디서 |
|------|------|--------|--------|
| **① 작성** | 나 | 생각나는 대로 메모 | `content/inbox/` |
| **② AI 정제** | Claude | 분류 · 중복 체크 · 링크 연결 · 공개 여부 판단 | `content/concepts/` |
| **③ 커밋** | 나 | `./scripts/publish.sh "커밋 메시지"` 실행 | 터미널 |
| **④ 자동 배포** | GitHub Actions | Quartz 빌드 → GitHub Pages 배포 | 클라우드 |
| **⑤ 공개** | — | 웹사이트에 노트 공개 | `https://<username>.github.io/<repo>` |

---

## 📁 디렉토리 구조

```
pofol-lab/
├── 📂 content/                  # Obsidian Vault 루트 (여기를 vault로 열기)
│   ├── 📥 inbox/                # 미처리 메모 (비공개, AI가 처리 전)
│   ├── 📚 concepts/             # 정제된 개념 노트 (공개 가능)
│   ├── 🛠 projects/             # 프로젝트 기록 (기본 비공개)
│   ├── 📓 journal/              # 개인 일지 (항상 비공개)
│   └── 🏠 index.md              # 웹사이트 홈페이지
│
├── 📂 .github/
│   └── 📂 workflows/
│       └── deploy.yml           # 자동 배포 워크플로우 (수정 불필요)
│
├── 📂 scripts/
│   └── publish.sh               # 퍼블리싱 원클릭 스크립트
│
├── 📂 quartz/                   # Quartz 내부 설정 (수정 거의 불필요)
│   ├── components/
│   └── styles/
│
├── quartz.config.ts             # ⚙️ 사이트 이름·색상 등 커스터마이징
├── quartz.layout.ts             # 레이아웃 설정
├── CLAUDE.md                    # 🤖 AI 큐레이터 지시서 (수정하면 AI 동작 변경)
└── README.md                    # 📖 이 파일
```

---

## 🚀 최초 설정 가이드 (처음 한 번만)

### Step 1: GitHub Repository 생성

1. [github.com/new](https://github.com/new) 에서 새 저장소 생성
   - 이름 예시: `pofol-lab` 또는 `<username>.github.io`
   - **Public** 설정 (GitHub Pages 무료 사용)

2. 원격 저장소 연결:

```bash
# 기존 quartz remote 제거 후 내 저장소로 교체
git remote remove origin
git remote add origin https://github.com/<YOUR_USERNAME>/<YOUR_REPO>.git
git branch -M main
git push -u origin main
```

### Step 2: GitHub Pages 설정

GitHub 저장소 → **Settings** → **Pages**
- Source: **GitHub Actions** 선택 후 저장

### Step 3: quartz.config.ts 수정

```typescript
const config: QuartzConfig = {
  configuration: {
    pageTitle: "🧠 ANN's Knowledge Garden",        // ← 사이트 이름
    baseUrl: "<YOUR_USERNAME>.github.io/<REPO>",   // ← 실제 URL
    // ...
  }
}
```

### Step 4: Obsidian Vault 열기

Obsidian 실행 → **Open folder as vault** → `pofol-lab/content/` 선택

---

## ✍️ 매일 사용하는 워크플로우

### 1. 메모 쓰기 (Obsidian에서)

`content/inbox/아이디어.md` 파일 생성 후 자유롭게 작성

### 2. AI에게 처리 요청 (Antigravity에서)

```
"inbox 처리해줘"
또는
"inbox/아이디어.md 내용을 concepts로 정리하고 공개 여부 판단해줘"
```

### 3. 퍼블리싱 (터미널에서)

```bash
# 커밋 메시지 포함
bash scripts/publish.sh "add: RAG 파이프라인 개념 노트 추가"

# 커밋 메시지 없이 (날짜+시간 자동 생성)
bash scripts/publish.sh
```

### 4. 배포 확인

GitHub 저장소 → **Actions** 탭에서 진행 상황 확인 (약 1~2분 소요)

---

## 🔖 Frontmatter 공개/비공개 제어

노트 최상단에 아래 형식으로 설정합니다:

```yaml
---
title: "노트 제목"
date: 2026-07-31
tags: [AI, 생산성]
is_public: true    # true = 웹에 공개
draft: false       # true = 빌드에서 완전 제외 (비공개 강제)
---
```

| `draft` | `is_public` | 결과 |
|---------|-------------|------|
| `true` | 무관 | ❌ 빌드 제외 (완전 비공개) |
| `false` | `false` | 🔒 빌드는 되지만 홈에서 링크 없음 |
| `false` | `true` | ✅ 웹에 공개됨 |

---

## 🛠 커스터마이징

### 사이트 테마 변경

`quartz.config.ts`에서 `theme` 섹션 수정:

```typescript
theme: {
  typography: {
    header: "Schibsted Grotesk",
    body: "Source Serif 4",
    code: "IBM Plex Mono",
  },
  colors: {
    lightMode: { /* 라이트 모드 색상 */ },
    darkMode:  { /* 다크 모드 색상 */ },
  },
},
```

### AI 동작 변경

`CLAUDE.md` 파일을 수정하면 AI 큐레이터의 동작 방식이 바뀝니다.

---

## 📦 기술 스택

| 컴포넌트 | 역할 | 링크 |
|----------|------|------|
| **Obsidian** | 로컬 마크다운 에디터 | [obsidian.md](https://obsidian.md) |
| **Claude (Antigravity)** | AI 큐레이터 (정제·분류·연결) | — |
| **Git + GitHub** | 버전 관리 + 배포 트리거 | [github.com](https://github.com) |
| **Quartz v4** | 마크다운 → 정적 사이트 | [quartz.jzhao.xyz](https://quartz.jzhao.xyz) |
| **GitHub Pages** | 무료 웹 호스팅 | — |
| **GitHub Actions** | CI/CD 자동 배포 | — |

---

## ❓ 자주 묻는 질문

**Q. 로컬에서 미리 보고 싶어요**

```bash
npx quartz build --serve
# → http://localhost:8080 에서 미리보기
```

**Q. 특정 폴더 전체를 비공개로 하고 싶어요**

`quartz.config.ts`에서 ignorePatterns에 폴더 추가:

```typescript
ignorePatterns: ["private", "templates", ".obsidian", "projects/**", "journal/**"],
```

**Q. 커스텀 도메인을 연결하고 싶어요**

GitHub Pages Settings → Custom domain에 도메인 입력 후
`quartz.config.ts`의 `baseUrl`을 해당 도메인으로 변경.

---

## 🔗 참고 자료

- [Quartz 공식 문서](https://quartz.jzhao.xyz)
- [Quartz GitHub](https://github.com/jackyzha0/quartz)
- [원본 아이디어 블로그 포스트](https://wikidocs.net/blog/@Allen/20309/)
- [GitHub Pages 문서](https://docs.github.com/en/pages)
