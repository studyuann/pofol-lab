---
title: "6장 GitHub Actions Workflow 구조"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "DevOps 환경에서의 CI CD"]
is_public: true
draft: false
---

# 6장. GitHub Actions Workflow 구조

## 장 목표

이 장에서는 GitHub Actions Workflow가 어떤 구조로 작성되는지 이해하고, Workflow를 구성하는 핵심 문법 요소를 체계적으로 학습한다.

또한 Jenkins Pipeline과 비교했을 때 GitHub Actions의 Workflow가 어떤 방식으로 자동화 절차를 표현하는지 이해하고, **YAML 기반 자동화 정의를 읽고 설명할 수 있는 수준**을 목표로 한다.

---

## 핵심 주제

* Workflow 파일의 위치와 역할

* YAML 기반 Workflow 정의 구조

* `name`, `on`, `jobs`, `steps` 개념

* `runs-on`, `uses`, `run` 차이

* `env`, `defaults`, `if`, `needs`, `strategy`, `matrix` 개요

* 아티팩트, 시크릿, 변수 개념

* 조건 분기와 병렬 실행 구조

* GitHub Actions Workflow를 설계할 때의 실무 관점

---

## 1. Workflow란 무엇인가

### 1.1 Workflow의 정의

GitHub Actions에서 Workflow는 자동화 절차 전체를 정의하는 단위다.

하나의 Workflow는 보통 하나의 목적을 가진다.

예를 들면 다음과 같은 Workflow를 각각 만들 수 있음.

* 코드 push 시 빌드/테스트 수행

* Pull Request 생성 시 검증 수행

* 태그 생성 시 릴리스 빌드 수행

* 운영 배포용 Workflow 수행

* 스케줄 기반 점검 작업 수행

즉, Workflow는 Jenkins에서의 Pipeline과 유사하게, **자동화된 작업 흐름 하나를 정의하는 파일 단위**라고 보면 됨.

---

### 1.2 Workflow 파일의 위치

GitHub Actions Workflow는 저장소 내부의 다음 경로에 위치해야 함.

```
.github/workflows/
```

예를 들면 다음과 같음.

```
my-app/
 ├─ src/
 ├─ tests/
 ├─ Dockerfile
 └─ .github/
     └─ workflows/
         ├─ ci.yml
         ├─ pr-check.yml
         └─ deploy.yml
```

GitHub는 이 디렉터리 안의 YAML 파일을 Workflow로 인식함.

즉, Workflow는 GitHub UI에서 따로 클릭해서 만드는 것이 아니라,

**저장소 안의 파일로 정의되고 버전 관리되는 구조**다.

---

## 2. YAML 기반 Workflow 정의

### 2.1 왜 YAML을 사용하는가

GitHub Actions는 Workflow를 YAML 형식으로 정의함.

YAML은 구조적 데이터를 사람이 읽기 쉽게 표현하기 위한 형식으로, 설정 파일에서 많이 사용됨.

GitHub Actions에서 YAML을 쓰는 이유는 다음과 같음.

* 구조를 계층적으로 표현하기 쉬움

* 텍스트 기반이라 Git으로 관리하기 쉬움

* 자동화 정의를 코드처럼 저장할 수 있음

* 사람이 읽고 수정하기 상대적으로 편함

즉, GitHub Actions는 **UI 기반 설정보다 파일 기반 선언형 정의**를 중심으로 동작함.

---

### 2.2 선언형 구조의 특징

GitHub Actions Workflow는 절차를 명령형 스크립트로만 길게 작성하는 방식이 아니라,

"무엇을 언제 어떤 환경에서 실행할지"를 선언형으로 기술하는 성격이 강함.

예를 들어 다음 항목을 선언함.

* 어떤 이벤트에서 실행할지

* 어떤 Runner에서 실행할지

* 어떤 Job이 먼저 실행될지

* 어떤 Step을 거칠지

* 어떤 조건일 때 실행할지

이 구조는 Jenkins Declarative Pipeline과 유사한 면이 있음.

---

## 3. Workflow 기본 골격

GitHub Actions Workflow는 보통 다음과 같은 형태를 가짐.

```
name: CI Workflow

on:
  push:
    branches:
      - main

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: 소스코드 체크아웃
        uses: actions/checkout@v4

      - name: 메시지 출력
        run: echo "hello github actions"
```

* `name`

* `on`

* `jobs`

* `runs-on`

* `steps`

* `uses`

* `run`

---

## 4. `name` 요소

### 4.1 역할

`name`은 Workflow의 표시 이름이다.

GitHub Actions UI에서 사용자가 보게 되는 Workflow 이름이라고 생각하면 됨.

예:

```
name: CI Workflow
```

이 이름은 실행 결과 목록, Workflow 화면, 실행 이력에서 보이게 됨.

---

### 4.2 왜 중요한가

이름은 단순 라벨처럼 보일 수 있지만, 실무에서는 꽤 중요함.

이유는 다음과 같음.

* 여러 Workflow를 쉽게 구분할 수 있음

* 목적이 명확한 이름일수록 운영성이 좋아짐

* 빌드용, 배포용, 릴리스용 Workflow를 분리해 인식하기 쉬움

좋은 예:

* `CI`

* `Pull Request Validation`

* `Build and Push Docker Image`

* `Deploy to Staging`

애매한 예:

* `test`

* `run`

* `workflow1`

즉, 이름만 봐도 무슨 자동화인지 알 수 있게 정하는 편이 좋음.

---

## 5. `on` 요소

### 5.1 역할

`on`은 이 Workflow가 **어떤 이벤트를 기준으로 실행될 것인지**를 정의하는 부분이다.

GitHub Actions의 핵심 문법 중 하나다.

예:

```
on:
  push:
    branches:
      - main
```

이 설정은 `main` 브랜치에 push가 발생했을 때 Workflow를 실행하라는 의미다.

---

### 5.2 이벤트 기반 구조의 핵심

GitHub Actions는 GitHub 안에서 발생하는 이벤트를 기준으로 자동화가 시작됨.

따라서 `on`은 "트리거 정의"라고 이해하면 됨.

대표 이벤트는 다음과 같음.

* `push`

* `pull_request`

* `workflow_dispatch`

* `release`

* `schedule`

* `pull_request_target`

* `issues`

즉, `on`은 Workflow의 시작 조건이다.

---

### 5.3 대표적인 `on` 사용 예

### 1) push 기준 실행

```
on:
  push:
    branches:
      - main
```

의미:

* main 브랜치로 코드가 push되면 실행

---

### 2) pull request 기준 실행

```
on:
  pull_request:
    branches:
      - main
```

의미:

* main 브랜치를 대상으로 Pull Request가 생성/업데이트될 때 실행

---

### 3) 수동 실행

```
on:
  workflow_dispatch:
```

의미:

* GitHub UI에서 사용자가 수동 실행 버튼을 눌렀을 때 실행

이 기능은 배포 Workflow나 운영 점검 Workflow에서 자주 사용됨.

---

### 4) 여러 이벤트 동시 지정

```
on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main
```

의미:

* main 브랜치 push 시 실행

* main 대상 PR 시 실행

즉, 하나의 Workflow가 여러 이벤트에 반응할 수도 있음.

---

### 5.4 브랜치, 태그, 경로 기준 필터링

`on`은 이벤트만 지정하는 것이 아니라, 어떤 브랜치나 태그, 파일 경로에 반응할지도 제한할 수 있음.

예:

* main 브랜치에만 반응

* release 태그에만 반응

* 특정 디렉터리 변경 시에만 반응

이런 필터링은 불필요한 Workflow 실행을 줄이는 데 중요함.

---

## 6. `jobs` 요소

### 6.1 역할

`jobs`는 Workflow 안에서 실제로 수행할 작업 단위들을 정의하는 영역이다.

예:

```
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: hello
        run: echo "build"
```

여기서 `build`는 Job 이름(정확히는 Job ID)에 해당함.

---

### 6.2 Workflow와 Job의 관계

* Workflow는 전체 자동화 흐름

* Job은 그 안의 큰 작업 블록

예를 들어 하나의 Workflow 안에 다음 Job을 둘 수 있음.

* `build`

* `test`

* `docker`

* `deploy`

즉, Job은 Jenkins Pipeline의 Stage보다 조금 더 큰 단위로 보는 것이 자연스러움.

각 Job은 독립 실행 환경을 가질 수 있고, 병렬 실행도 가능함.

---

### 6.3 Job이 중요한 이유

Job 단위로 다음을 나눌 수 있음.

* 실행 환경 분리

* 의존 관계 설정

* 병렬 수행

* 조건부 실행

* 역할 구분

예:

* build Job은 Ubuntu에서

* test Job은 matrix로 여러 버전에서

* deploy Job은 build 성공 후에만

이처럼 Job은 Workflow 구조 설계의 중심이다.

---

## 7. `runs-on` 요소

### 7.1 역할

`runs-on`은 해당 Job이 어떤 Runner 환경에서 실행될지를 지정하는 요소다.

예:

```
runs-on: ubuntu-latest
```

의미:

* 이 Job은 Ubuntu 최신 Runner에서 실행하라는 뜻

---

### 7.2 왜 필요한가

GitHub Actions는 실제로 Job을 수행할 실행 환경이 필요함.

Job은 Runner 위에서 동작하므로, 어떤 OS/환경을 사용할지 지정해야 함.

대표 예:

* `ubuntu-latest`

* `windows-latest`

* `macos-latest`

* self-hosted

---

### 7.3 `runs-on`을 이해할 때 중요한 점

Job마다 서로 다른 Runner를 사용할 수 있음.

예:

* build Job은 Ubuntu

* test Job은 Windows

* release Job은 macOS

즉, Workflow 전체가 하나의 머신에서 도는 것이 아니라,

**Job마다 별도의 실행 환경에서 독립적으로 수행될 수 있음**.

이 점은 Jenkins와 비교했을 때 사고방식 차이로 이어짐.

---

## 8. `steps` 요소

### 8.1 역할

`steps`는 Job 안에서 실제로 수행할 세부 실행 단계를 나열하는 부분이다.

예:

```
steps:
  - name: 소스코드 체크아웃
    uses: actions/checkout@v4

  - name: 테스트 실행
    run: pytest
```

즉, Job이 큰 작업 단위라면 Step은 그 안의 세부 명령 단위다.

---

### 8.2 실행 순서

Step은 기본적으로 위에서 아래로 순차 실행됨.

앞 단계가 실패하면 보통 다음 Step은 실행되지 않음.

이 구조는 Jenkins Pipeline의 `steps`와 유사하게 이해할 수 있음.

---

### 8.3 Step에 이름을 붙이는 이유

`name`은 각 Step의 표시 이름이다.

예:

```
- name: Docker 로그인
```

이름을 잘 붙이면 실행 로그와 UI에서 현재 무엇을 하고 있는지 쉽게 파악할 수 있음.

좋은 예:

* `Checkout source`

* `Set up Python`

* `Install dependencies`

* `Run unit tests`

* `Build Docker image`

애매한 예:

* `run`

* `step1`

* `do it`

즉, Step 이름도 운영성과 가독성에 영향을 줌.

---

## 9. `uses`와 `run`의 차이

GitHub Actions Step을 이해할 때 가장 중요한 포인트 중 하나가 `uses`와 `run`의 차이임.

---

### 9.1 `uses`

`uses`는 이미 만들어진 Action을 재사용하는 방식이다.

예:

```
- name: 소스코드 체크아웃
  uses: actions/checkout@v4
```

이 의미는 GitHub가 제공하거나 외부에서 제공하는 Action을 가져와 실행하라는 뜻이다.

즉, `uses`는 **재사용 가능한 자동화 컴포넌트 호출**에 해당함.

---

### 9.2 `run`

`run`은 Runner 안에서 직접 쉘 명령을 실행하는 방식이다.

예:

```
- name: 테스트 실행
  run: pytest
```

이 의미는 현재 Runner 환경에서 `pytest` 명령을 실행하라는 뜻이다.

즉, `run`은 **직접 명령 실행**이다.

---

### 9.3 둘의 차이를 정리하면

* `uses`: 미리 만들어진 Action 사용

* `run`: 직접 명령어 실행

예를 들어,

* 저장소 checkout은 `uses`

* 패키지 설치나 테스트 명령은 `run`

이렇게 많이 구성됨.

---

## 10. 자주 사용하는 Workflow 구성 요소

기본 구조 외에도 실무에서는 몇 가지 요소를 자주 함께 사용함.

---

## 10.1 `env`

`env`는 환경 변수를 정의하는 영역이다.

예:

```
env:
  APP_NAME: sample-app
  ENV: dev
```

이렇게 정의한 값은 Step 안에서 공통으로 참조할 수 있음.

---

### 왜 필요한가

파이프라인에는 반복되는 값이 많음.

예:

* 애플리케이션 이름

* 이미지 이름

* 실행 환경

* 레지스트리 주소

이를 직접 여러 번 쓰는 대신 변수화하면 유지보수가 쉬워짐.

---

## 10.2 `defaults`

`defaults`는 기본 실행 옵션을 지정할 때 사용함.

예를 들어 모든 `run` 명령에 대해 bash 쉘을 기본으로 쓰거나, 특정 working-directory를 지정할 수 있음.

즉, 반복 설정을 줄이는 데 사용됨.

---

## 10.3 `if`

`if`는 특정 조건에서만 Job 또는 Step이 실행되도록 제어하는 기능이다.

예:

* main 브랜치일 때만 실행

* PR 이벤트일 때만 실행

* 특정 입력값이 있을 때만 실행

이 기능은 실무에서 매우 중요함.

모든 상황에서 같은 Workflow가 동일하게 동작할 필요는 없기 때문임.

---

## 10.4 `needs`

`needs`는 Job 간 실행 순서를 정의하는 데 사용함.

예:

* build Job이 끝난 뒤 test Job 실행

* test가 성공해야 deploy 실행

즉, Job 간 의존 관계를 나타냄.

아무 설정이 없으면 Job은 병렬 실행될 수 있지만, `needs`를 쓰면 순서를 강제할 수 있음.

---

## 10.5 `strategy`와 `matrix`

`strategy`와 `matrix`는 같은 Job을 여러 조건으로 반복 실행할 때 사용함.

예:

* Python 3.10, 3.11에서 테스트

* Ubuntu와 Windows에서 동시에 테스트

* 여러 Node.js 버전에서 빌드 확인

이 구조는 GitHub Actions의 강력한 장점 중 하나다.

동일한 Workflow 논리를 여러 환경에 쉽게 확장할 수 있기 때문임.

---

## 11. Job 간 관계 이해

### 11.1 기본은 병렬

GitHub Actions에서 여러 Job을 정의하면, 별도의 의존 관계가 없을 때는 병렬 실행될 수 있음.

예:

* lint Job

* unit-test Job

* security-scan Job

이 셋은 서로 독립적이면 동시에 실행 가능함.

---

### 11.2 순차 실행이 필요한 경우

하지만 모든 Job이 병렬이면 안 되는 경우도 많음.

예:

* build 후에만 docker build 가능

* docker push 후에만 deploy 가능

* test 실패 시 deploy 금지

이 경우 `needs`를 이용해 의존 관계를 설정함.

즉, GitHub Actions Workflow 설계에서는 **무엇을 병렬로 하고 무엇을 순차로 할지**를 나누는 것이 중요함.

---

## 12. 변수, Secret, 입력값 개념

### 12.1 변수와 Secret의 차이

Workflow에는 일반 변수와 민감 정보가 함께 등장할 수 있음.

* 일반 변수: 환경 이름, 앱 이름, 버전 문자열

* Secret: 토큰, 비밀번호, API Key

민감 정보는 일반 `env`에 직접 적는 것이 아니라 GitHub Secret 기능을 사용해야 함.

즉, 편의성과 보안은 구분해서 생각해야 함.

---

### 12.2 Secret이 중요한 이유

Workflow는 코드 파일이므로 저장소에 남음.

여기에 토큰이나 비밀번호를 직접 적으면 즉시 보안 문제가 생김.

따라서 다음 정보는 Secret으로 관리해야 함.

* Docker Registry 비밀번호

* 클라우드 Access Key

* SSH Key

* API Token

이 점은 Jenkins의 Credential 관리와 같은 맥락으로 매우 중요함.

---

### 12.3 수동 실행 입력값

`workflow_dispatch`를 사용하면 수동 실행 시 입력값을 받을 수도 있음.

예:

* 배포 환경 선택

* 이미지 태그 입력

* 운영 배포 여부 확인

즉, GitHub Actions도 완전 자동만이 아니라 **통제된 수동 실행**이 가능함.

---

## 13. 아티팩트와 결과물 개념

Workflow는 실행 중에 생성한 결과물을 다음 단계나 나중 실행에서 사용할 수 있어야 할 때가 있음.

이때 아티팩트 개념이 중요해짐.

예:

* 빌드 결과 ZIP 파일 저장

* 테스트 리포트 업로드

* 로그 파일 저장

* 패키지 결과물 보관

즉, GitHub Actions도 단순히 명령만 실행하는 것이 아니라,

**결과물을 저장하고 전달하는 흐름**을 갖는다.

---

## 14. Workflow 설계 관점

### 14.1 Workflow를 너무 크게 만들지 말 것

하나의 YAML 안에 CI, Docker Build, Release, Deploy, 운영 점검까지 모두 넣으면 관리가 어려워질 수 있음.

보통 목적별로 나누는 편이 좋음.

예:

* `ci.yml`

* `docker.yml`

* `deploy.yml`

---

### 14.2 Job 단위 역할을 명확히 나눌 것

Job 이름과 역할이 분명해야 함.

예:

* `lint`

* `test`

* `build-image`

* `deploy-staging`

애매한 Job 구분은 로그 해석을 어렵게 만듦.

---

### 14.3 재사용 가능한 Action과 직접 명령을 적절히 조합할 것

모든 것을 `run`으로만 작성하면 길고 복잡해질 수 있음.

반대로 모든 것을 외부 Action에만 의존하면 내부 동작이 보이지 않을 수 있음.

즉, 적절한 균형이 필요함.

---

### 14.4 브랜치 전략과 Workflow를 함께 설계할 것

예:

* feature 브랜치: 빠른 테스트만

* main 브랜치: Docker Build 포함

* tag: release workflow 실행

이처럼 브랜치 목적과 Workflow 수준은 함께 가야 함.

---

## 15. Jenkins Pipeline과의 비교 관점

GitHub Actions Workflow를 Jenkins Pipeline과 비교하면 다음처럼 이해할 수 있음.

| Jenkins | GitHub Actions |
| --- | --- |
| Jenkinsfile | Workflow YAML |
| Pipeline | Workflow |
| Stage | Job 또는 Step 관점으로 분산 |
| Agent | Runner |
| steps 블록 | steps |
| environment | env |
| post 처리 | 별도 step 조건 처리 또는 후속 job |

완전히 1:1 대응은 아니지만, 이런 식으로 연결해서 보면 이해가 쉬움.

특히 GitHub Actions는 Jenkins보다 **Job 중심 분리와 이벤트 중심 실행** 색채가 강하다고 볼 수 있음.

---

## 요약

* Workflow는 GitHub Actions의 자동화 흐름 전체를 정의하는 파일 단위임

* Workflow 파일은 `.github/workflows` 경로에 YAML로 저장됨

* 핵심 구성 요소는 `name`, `on`, `jobs`, `runs-on`, `steps`임

* `on`은 실행 이벤트, `jobs`는 큰 작업 단위, `steps`는 실제 실행 단계임

* `uses`는 재사용 Action 호출, `run`은 직접 명령 실행임

* `env`, `if`, `needs`, `strategy`, `matrix` 등을 통해 실무형 제어가 가능함

* Secret과 변수는 반드시 구분해서 관리해야 함

* 좋은 Workflow는 단순히 동작하는 것이 아니라 읽기 쉽고 역할이 분명해야 함