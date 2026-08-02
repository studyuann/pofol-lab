---
title: "kubens 설치"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "쿠버네티스", "2장 실습환경구축"]
is_public: true
draft: false
---

# kubens 설치

---

### 1단계: winget으로 기본 도구 설치

`kubens`는 인터랙티브 모드(선택 화면)를 위해 `fzf`가 필요하며, 쾌적한 환경을 위해 **Windows 터미널** 사용을 권장합니다.

PowerShell `# fzf 설치 (kubens의 색상 및 선택 기능을 위해 필수)  
winget install junegunn.fzf`

### 2단계: Scoop 설치 (패키지 관리자)

`winget`에는 `kubens` 공식 패키지가 없으므로, 설치가 간편한 `scoop`을 먼저 설치합니다.

1. **PowerShell** 실행 (일반 권한도 가능)

2. 설치 권한 허용:PowerShell

   `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

3. Scoop 설치:PowerShell

   `irm get.scoop.sh | iex`

### 3단계: Scoop으로 kubens 설치

이제 `scoop`을 이용해 `kubens`를 설치합니다. (동시에 `kubectx`도 설치됩니다.)

PowerShell

`scoop install kubens`