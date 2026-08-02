---
title: "5장 GitHub Actions 개요"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "DevOps 환경에서의 CI CD"]
is_public: true
draft: false
---

# 5장. GitHub Actions 개요

## 1. GitHub Actions란 무엇인가

### 1.1 GitHub Actions의 정의

GitHub Actions는 GitHub 저장소를 중심으로 다양한 자동화 작업을 수행할 수 있도록 제공되는 워크플로우 자동화 기능이다.

가장 대표적으로는 다음 작업에 사용됨.

* 코드를 push하면 자동 빌드

* Pull Request 생성 시 테스트 수행

* Docker 이미지 빌드

* 아티팩트 업로드

* 배포 자동화

* 이슈나 릴리스 이벤트 기반 작업 실행

* 보안 검사 및 정적 분석

즉, GitHub Actions는 **GitHub 이벤트를 기준으로 동작하는 자동화 플랫폼**.

---

### 1.2 왜 GitHub Actions가 주목받게 되었는가

과거에는 GitHub 저장소를 사용하더라도 CI/CD는 별도의 외부 도구로 연결하는 경우가 많았음.

예:

* GitHub + Jenkins

* GitHub + Travis CI

* GitHub + CircleCI

* GitHub + GitLab Runner

* GitHub + 사내 빌드 서버

이 구조는 가능은 하지만 연결 지점이 많아짐.

* Webhook 설정 필요

* 외부 시스템 권한 연동 필요

* 저장소와 CI 결과가 분리됨

* UI와 관리 포인트가 여러 군데로 흩어짐

GitHub Actions는 이 문제를 줄이기 위해 **GitHub 안에서 바로 자동화 워크플로우를 정의하고 실행할 수 있게 한 구조**다.

즉, 코드 저장소와 자동화 실행 기반을 하나의 플랫폼으로 만듬.

---

## 2. GitHub Actions의 역할

GitHub Actions는 GitHub 안에서 다양한 자동화를 수행할 수 있지만, DevOps와 CI/CD 맥락에서는 주로 다음 역할로 설명할 수 있음.

---

### 2.1 CI 자동화 도구

개발자가 GitHub 저장소에 코드를 push하면 다음이 가능함.

* 소스코드 체크아웃

* 의존성 설치

* 빌드 수행

* 테스트 실행

* 결과 표시

즉, GitHub Actions는 GitHub 기반 CI 도구로 바로 사용할 수 있음.

---

### 2.2 CD 파이프라인의 일부 또는 전부 수행

GitHub Actions는 빌드까지만이 아니라 CD 단계로도 확장 가능함.

예:

* Docker 이미지 빌드 후 레지스트리 업로드

* 클라우드 환경에 배포

* Kubernetes 매니페스트 변경

* GitOps 저장소 자동 업데이트

* 릴리스 생성 및 태그 배포

즉, 조직 정책에 따라 GitHub Actions를 **CI 전용**으로 쓸 수도 있고, **CI/CD 전체**에 활용할 수도 있음.

---

### 2.3 저장소 이벤트 기반 자동화

GitHub Actions의 가장 큰 특징 중 하나는 GitHub 이벤트를 자연스럽게 자동화 트리거로 삼는다는 점이다.

대표 이벤트 예시는 다음과 같음.

* `push`

* `pull_request`

* `workflow_dispatch`

* `release`

* `schedule`

* `issue`

* `tag`

* `repository_dispatch`

즉, GitHub Actions는 **GitHub 내부 이벤트를 기준으로 작동하는 자동화 엔진**이다.

---

## 3. GitHub Actions의 기본 동작 구조

GitHub Actions의 핵심 구성요소.

---

## 3.1 Workflow

Workflow는 자동화 절차 전체를 정의하는 단위다.

보통 하나의 YAML 파일로 작성하며, 저장소 내 `.github/workflows` 디렉터리에 위치함.

예:

```
my-repo/
 └─ .github/
     └─ workflows/
         ├─ ci.yml
         ├─ deploy.yml
         └─ release.yml
```

즉, Workflow는 Jenkins의 Pipeline과 비슷한 개념으로 볼 수 있음.

하나의 목적을 가진 자동화 흐름을 정의하는 파일 단위다.

---

## 3.2 Job

Job은 Workflow 안에서 실행되는 작업 단위다.

하나의 Workflow 안에 여러 Job이 들어갈 수 있음.

예:

* build Job

* test Job

* docker Job

* deploy Job

Job은 순차적으로도 실행할 수 있고, 독립적이면 병렬 실행도 가능함.

즉, Workflow가 큰 흐름이라면 Job은 그 안의 **큰 작업 블록**이다.

---

## 3.3 Step

Step은 Job 안에서 수행되는 개별 실행 단위다.

보통 다음 중 하나 형태임.

* 쉘 명령 실행

* GitHub Action 재사용

* 스크립트 호출

* 환경 설정 수행

예:

* 코드 체크아웃

* Python 설치

* 테스트 명령 실행

* Docker 로그인

* 이미지 빌드

즉, Step은 Job 안에서 실제로 수행되는 가장 작은 실행 단위에 가깝다.

---

## 3.4 Runner

Runner는 GitHub Actions Workflow를 실제로 실행하는 환경이다.

즉, Job과 Step은 Runner 위에서 돌아감.

Runner는 크게 두 가지로 나뉨.

* GitHub-hosted Runner

* Self-hosted Runner

이 구분은 GitHub Actions를 이해할 때 매우 중요함.

---

## 4. GitHub-hosted Runner와 Self-hosted Runner

## 4.1 GitHub-hosted Runner

GitHub-hosted Runner는 GitHub가 제공하는 실행 환경이다.

사용자는 별도 서버를 직접 운영하지 않고도 Workflow를 실행할 수 있음.

대표 특징은 다음과 같음.

* GitHub가 실행 환경을 제공함

* 운영체제 선택 가능
  + Ubuntu
  + Windows
  + macOS

* 실행 후 초기화되는 일회성 환경에 가까움

* 빠르게 시작할 수 있음

* 관리 부담이 적음

즉, GitHub-hosted Runner는 GitHub Actions가 빠르게 확산된 가장 큰 이유 중 하나다.

---

## 4.2 Self-hosted Runner

Self-hosted Runner는 사용자가 직접 운영하는 서버나 환경에 Runner를 설치해서 사용하는 방식이다.

예:

* 사내 Linux 서버

* 온프레미스 빌드 서버

* 자체 Kubernetes 클러스터 노드

* 특정 툴이 설치된 전용 머신

### 왜 Self-hosted Runner를 쓰는가

* 사내망 리소스 접근 필요

* 특정 도구나 SDK가 필요

* 장시간 빌드나 고성능 자원 필요

* 네트워크/보안 정책상 외부 Runner 사용 제한

* 자체 인프라에서 실행해야 하는 규정 존재

즉, GitHub Actions도 Jenkins처럼 완전히 SaaS에만 묶인 것이 아니라, 필요하면 자체 실행 환경과 연결할 수 있음.

---

## 4.3 두 방식의 차이

| 항목 | GitHub-hosted Runner | Self-hosted Runner |
| --- | --- | --- |
| 운영 주체 | GitHub | 사용자 |
| 관리 부담 | 낮음 | 높음 |
| 시작 속도 | 빠름 | 환경에 따라 다름 |
| 커스터마이징 | 제한적 | 높음 |
| 사내망 접근 | 어려울 수 있음 | 가능 |
| 보안 통제 | GitHub 의존 | 직접 통제 가능 |

이 비교는 이후 Jenkins와 GitHub Actions를 비교할 때도 중요한 기준이 됨.

---

## 5. GitHub Actions의 이벤트 기반 구조

GitHub Actions의 핵심 특징은 **이벤트 기반 자동화**다.

---

### 5.1 이벤트란 무엇인가

이벤트는 GitHub 안에서 발생하는 특정 행동이나 상태 변화를 의미함.

예:

* 누군가 코드를 push함

* Pull Request가 생성됨

* 릴리스가 발행됨

* 특정 시간(schedule)이 됨

* 사용자가 수동 실행 버튼을 누름

GitHub Actions는 이런 이벤트를 감지해서 Workflow를 실행함.

---

### 5.2 왜 이벤트 기반 구조가 중요한가

전통적인 CI 도구에서는 저장소 변경을 감지하기 위해 다음 방식이 필요했음.

* 주기적으로 저장소를 확인하는 polling

* Webhook을 외부 시스템에 연결

* 별도 인증과 네트워크 설정

반면 GitHub Actions는 GitHub 안에서 이벤트를 바로 인식하기 때문에 구조가 단순해짐.

즉, GitHub Actions는

**저장소와 자동화 시스템이 같은 플랫폼 안에 있기 때문에 트리거 구조가 자연스럽고 간단함**.

---

## 6. GitHub Actions의 장점

GitHub Actions가 널리 쓰이는 이유는 구조적 장점이 분명하기 때문임.

---

### 6.1 GitHub와의 높은 통합성

GitHub Actions는 저장소, 브랜치, Pull Request, Release, Secret, Environment와 자연스럽게 연결됨.

즉, 별도 도구를 붙이는 느낌보다 GitHub 안에서 바로 자동화가 이어짐.

예:

* PR 화면에서 CI 결과 바로 확인

* Commit 단위로 체크 상태 표시

* Secret을 저장소/조직 단위로 관리

* 브랜치 보호 규칙과 연계 가능

이 통합성은 실무 효율에 큰 영향을 줌.

---

### 6.2 빠른 시작과 낮은 진입 장벽

Jenkins처럼 서버 설치, Java 설정, 플러그인 구성부터 시작할 필요가 없음.

YAML 파일 하나로 빠르게 시작 가능함.

즉, 소규모 팀이나 GitHub 중심 조직에서는 CI/CD 도입 속도가 매우 빠름.

---

### 6.3 워크플로우 파일 기반 관리

GitHub Actions Workflow도 YAML 파일이므로 Git으로 버전 관리 가능함.

장점은 다음과 같음.

* 변경 이력 추적 가능

* Pull Request 리뷰 가능

* 브랜치별 워크플로우 차별화 가능

* 저장소와 자동화 정의를 함께 관리 가능

즉, Jenkinsfile과 유사하게 **Workflow as Code** 구조를 가짐.

---

### 6.4 Marketplace 기반 재사용

GitHub Actions는 Marketplace를 통해 다양한 Action을 재사용할 수 있음.

예:

* 코드 체크아웃 Action

* Docker 로그인 Action

* 언어 런타임 설치 Action

* 클라우드 로그인 Action

* Slack 알림 Action

즉, 자주 쓰는 작업을 처음부터 다 작성하지 않고 재사용 가능한 컴포넌트처럼 활용할 수 있음.

---

### 6.5 GitHub 중심 협업 흐름과 잘 맞음

GitHub Actions는 다음 흐름과 특히 잘 맞음.

* Pull Request 기반 협업

* 브랜치 보호 정책

* Code Review

* Tag / Release 관리

* GitHub Packages / Container Registry 연계

즉, GitHub를 개발 협업의 중심 플랫폼으로 쓰는 조직에서는 매우 자연스러운 선택지가 됨.

---

## 7. GitHub Actions의 한계와 고려사항

GitHub Actions도 환경에 따라 제약이 있음.

---

### 7.1 GitHub 종속성이 커질 수 있음

GitHub Actions는 GitHub와 깊게 통합되는 대신, 구조적으로 GitHub 의존성이 강함.

즉:

* 저장소 중심 구조가 GitHub에 맞춰짐

* 타 플랫폼 이식성이 떨어질 수 있음

* 조직 정책상 GitHub 사용이 제한되면 활용이 어렵다

---

### 7.2 복잡한 자체 인프라 제어에는 한계가 있을 수 있음

사내망, 폐쇄망, 복잡한 레거시 툴체인, 특수한 네트워크 연결 구조에서는 GitHub-hosted Runner만으로 부족할 수 있음.

이 경우 Self-hosted Runner를 써야 할 수 있는데, 그러면 운영 부담이 늘어남.

즉, GitHub Actions도 규모가 커질수록 단순 SaaS 사용만으로는 부족해질 수 있음.

---

### 7.3 실행 시간과 비용, 자원 제한 고려 필요

관리형 Runner는 매우 편하지만, 사용량이 늘어나면 실행 시간, 동시성, 비용, 제한 정책을 고려해야 함.

즉, 작은 프로젝트에서는 매우 편하지만 대규모 사용 시에는 운영 정책과 비용 관리도 함께 봐야 함.

---

### 7.4 워크플로우가 지나치게 비대해질 수 있음

처음에는 단순한 YAML이지만, 점점 조건 분기와 배포 로직, 스크립트가 늘어나면 관리가 어려워질 수 있음.

즉, GitHub Actions도 "간단해서 무조건 관리가 쉬움"이라고 단정할 수는 없음.

복잡해지면 공통 모듈화, 재사용 전략, Runner 정책이 필요함.

---

## 8. Jenkins와 GitHub Actions의 구조적 차이

GitHub Actions를 제대로 이해하려면 Jenkins와의 차이를 함께 봐야 함.

---

### 8.1 설치형 vs 플랫폼 내장형

* Jenkins는 사용자가 직접 설치하고 운영하는 자동화 서버임

* GitHub Actions는 GitHub 플랫폼 안에 내장된 자동화 기능임

즉, Jenkins는 "운영형 플랫폼", GitHub Actions는 "플랫폼 내 자동화 기능"이라는 출발점 차이가 있음.

---

### 8.2 플러그인 중심 vs Action 재사용 중심

* Jenkins는 Plugin 생태계가 핵심

* GitHub Actions는 재사용 가능한 Action과 YAML 기반 조합이 핵심

둘 다 확장성은 있지만 구조가 다름.

---

### 8.3 Controller / Agent 사고 vs Workflow / Runner 사고

* Jenkins는 Controller가 있고 Agent에 작업을 분산하는 구조

* GitHub Actions는 Workflow가 있고 Runner가 작업을 실행하는 구조

개념상 비슷한 부분은 있지만, 운영 책임과 구조 복잡도는 Jenkins 쪽이 더 큼.

---

### 8.4 운영 부담의 차이

* Jenkins는 서버, 보안, 백업, 플러그인, 업그레이드를 직접 관리해야 함

* GitHub Actions는 hosted runner 기준으로 운영 부담이 훨씬 낮음

이 차이는 도구 선택에 큰 영향을 줌.

---

## 9. GitHub Actions가 잘 맞는 환경

### 9.1 GitHub 중심 개발 조직

코드 저장소, PR, 리뷰, 릴리스가 모두 GitHub에서 이루어지는 조직에는 매우 잘 맞음.

### 9.2 빠르게 CI를 도입하려는 환경

별도 서버 설치 없이 YAML만으로 시작 가능하므로 초기 도입이 쉬움.

### 9.3 소규모~중간 규모 서비스

복잡한 사내 인프라 제약이 적다면 매우 효율적임.

### 9.4 클라우드 네이티브 개발 환경

컨테이너, 레지스트리, Kubernetes, GitOps와 연계하기 좋음.

---

## 10. GitHub Actions가 부담이 될 수 있는 환경

### 10.1 폐쇄망 / 강한 사내망 환경

외부 플랫폼 연동이 어렵거나 제한이 강하면 불편할 수 있음.

### 10.2 복잡한 레거시 빌드 환경

특수 SDK, 사내 전용 툴, 고정 실행 서버가 필요한 경우 Self-hosted Runner 운영 부담이 생김.

### 10.3 플랫폼 종속성을 줄이고 싶은 경우

GitHub 중심으로 묶이는 것을 부담스러워하는 경우에는 대안 검토가 필요함.

---

## 11. 아키텍처 관점에서 본 GitHub Actions

GitHub Actions의 기본 구조를 단순화하면 다음과 같음.

```
Developer
   ↓
GitHub Repository
   ↓
GitHub Event 발생
   ↓
Workflow 실행
   ↓
Runner에서 Job / Step 수행
   ↓
Artifact / Image / Deploy 결과 생성
   ↓
GitHub UI에서 결과 확인
```

이 구조의 핵심은 다음임.

* 저장소와 자동화가 같은 플랫폼 안에 있음

* 이벤트 기반으로 자연스럽게 동작함

* Runner가 실제 실행 환경 역할을 함

* 결과가 Commit, PR, Workflow 화면에 통합 표시됨

즉, GitHub Actions는 GitHub 중심 DevOps 흐름에 매우 잘 맞는 구조다.

---

## 요약

* GitHub Actions는 GitHub 이벤트를 기반으로 동작하는 자동화 플랫폼임

* CI뿐 아니라 CD, 릴리스, 배포, GitOps 연계까지 확장 가능함

* 핵심 구성 요소는 Workflow, Job, Step, Runner임

* GitHub-hosted Runner는 관리 부담이 적고 빠르게 시작할 수 있음

* Self-hosted Runner를 사용하면 자체 인프라와도 연결 가능함

* GitHub와의 높은 통합성이 가장 큰 강점임

* 반면 GitHub 종속성, Runner 운영, 복잡한 워크플로우 관리 이슈는 고려해야 함

* GitHub 중심 개발 문화에서는 매우 강력한 선택지임

---