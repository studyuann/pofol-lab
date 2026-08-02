---
title: "4장 Jenkins Pipeline 개념과 구성 요소"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "DevOps 환경에서의 CI CD"]
is_public: true
draft: false
---

# 4장. Jenkins Pipeline 개념과 구성 요소

## 1. Jenkins Pipeline이란 무엇인가

### 1.1 Pipeline의 정의

Jenkins Pipeline은 빌드, 테스트, 패키징, 배포 같은 여러 작업을 **단계별 흐름으로 정의하고 실행하는 방식**이다.

즉, 단순히 "명령어 몇 개 실행"이 아니라, **작업 순서, 실행 조건, 실패 처리, 후속 동작**까지 포함해 전체 자동화 흐름을 코드 형태로 표현하는 구조다.

예를 들어 다음과 같은 흐름을 하나의 Pipeline으로 정의할 수 있음.

* Git에서 소스코드 가져오기

* 애플리케이션 빌드

* 단위 테스트 수행

* Docker 이미지 생성

* 이미지 레지스트리 업로드

* 특정 환경에 배포

* 결과 알림 전송

이처럼 Pipeline은 CI/CD 절차 전체를 **하나의 실행 가능한 프로세스**로 묶어준다.

---

### 1.2 왜 Pipeline이 중요한가

Jenkins 초창기에는 Freestyle Job 방식이 많이 사용됐음.

하지만 Job이 많아지고 절차가 복잡해질수록 UI 기반 설정만으로는 한계가 뚜렷해졌음.

대표적인 한계는 다음과 같음.

* 누가 어떤 설정을 바꿨는지 추적하기 어려움

* Job 설정을 다른 환경으로 복제하기 어려움

* 브랜치별로 다른 흐름을 반영하기 어려움

* 조건 분기, 병렬 실행, 승인 단계 같은 복잡한 흐름 표현이 불편함

* 코드 리뷰 없이 운영 파이프라인이 변경될 수 있음

Pipeline은 이런 문제를 해결하기 위해 등장한 방식이며, 핵심은 **파이프라인을 코드로 관리한다**는 데 있음.

---

## 2. Pipeline as Code 개념

### 2.1 Pipeline as Code란

Pipeline as Code는 말 그대로 파이프라인 정의를 웹 UI에만 저장하지 않고,

**코드 파일 형태로 저장소에 함께 보관하는 방식**이다.

Jenkins에서는 이 파일이 보통 `Jenkinsfile`이다.

즉, 애플리케이션 코드와 같은 저장소 안에 다음이 함께 존재할 수 있음.

* 애플리케이션 소스코드

* Dockerfile

* Kubernetes 배포 매니페스트

* Jenkinsfile

이 구조가 되면 CI/CD 절차도 애플리케이션과 함께 버전 관리할 수 있음.

---

### 2.2 Pipeline as Code의 장점

### 1) 변경 이력 추적 가능

누가 언제 어떤 파이프라인 단계를 수정했는지 Git 기록으로 남음.

### 2) 코드 리뷰 가능

파이프라인 변경도 Pull Request 리뷰 대상으로 포함할 수 있음.

### 3) 재현성 향상

환경이 바뀌어도 같은 Jenkinsfile을 사용하면 같은 흐름을 다시 만들 수 있음.

### 4) 프로젝트와 파이프라인의 일체화

소스 변경과 파이프라인 변경이 함께 관리되므로 운영 흐름이 분리되지 않음.

### 5) 브랜치별 독립성

브랜치마다 Jenkinsfile이 다를 수 있으므로, 브랜치 목적에 맞는 파이프라인을 자연스럽게 적용할 수 있음.

즉, Pipeline as Code는 단순 편의 기능이 아니라,

**CI/CD 자체를 형상관리 대상에 포함시키는 DevOps 방식**이라고 볼 수 있음.

---

## 3. Jenkinsfile의 역할

### 3.1 Jenkinsfile이란

`Jenkinsfile`은 Jenkins Pipeline을 정의하는 파일이다.

이 파일 안에는 다음 내용이 들어갈 수 있음.

* 어떤 Agent에서 실행할지

* 어떤 Stage를 거칠지

* 각 Stage에서 어떤 명령을 수행할지

* 환경 변수는 무엇인지

* 실패했을 때 어떤 처리를 할지

* 특정 브랜치에서만 어떤 단계를 실행할지

* 사용자 승인을 어디서 받을지

즉, Jenkinsfile은 **CI/CD 절차의 설계도**라고 볼 수 있음.

---

### 3.2 Jenkinsfile의 위치

보통 Jenkinsfile은 저장소 루트에 두는 경우가 많음.

예:

```
my-app/
 ├─ src/
 ├─ tests/
 ├─ Dockerfile
 ├─ package.json
 └─ Jenkinsfile
```

이렇게 하면 저장소를 기준으로 Jenkins가 Jenkinsfile을 자동 인식해서 파이프라인을 실행할 수 있음.

---

### 3.3 Jenkinsfile이 중요한 이유

Jenkinsfile이 없으면 파이프라인 설정이 Jenkins 서버 안에만 머무르게 됨.

이 경우 다음 문제가 생기기 쉬움.

* 서버를 옮기면 설정 복원이 번거로움

* Job이 많아질수록 관리가 어려움

* 프로젝트 코드와 자동화 흐름이 분리됨

* 브랜치 전략과 연결이 약해짐

반면 Jenkinsfile을 사용하면 파이프라인이 프로젝트의 일부가 됨.

---

## 4. Declarative Pipeline과 Scripted Pipeline

Jenkins Pipeline은 크게 두 가지 스타일로 작성할 수 있음.

* Declarative Pipeline

* Scripted Pipeline

둘 다 Pipeline이지만, 표현 방식과 관리 난이도가 다름.

---

### 4.1 Declarative Pipeline

Declarative Pipeline은 구조가 비교적 명확하고, 미리 정해진 문법 틀 안에서 파이프라인을 작성하는 방식이다.

대표 형태는 다음과 같음.

```
pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                echo 'build'
            }
        }
    }
}
```

### 특징

* 구조가 명확함

* 읽기 쉬움

* 표준화된 작성이 쉬움

* 입문자가 이해하기 좋음

* 실무에서 공통 규칙을 적용하기 좋음

---

### 4.2 Scripted Pipeline

Scripted Pipeline은 Groovy 스크립트 방식으로 보다 자유롭게 작성하는 형태다.

예를 들면 다음과 비슷한 스타일이다.

```
node {
    stage('Build') {
        echo 'build'
    }
}
```

### 특징

* 자유도가 높음

* 복잡한 로직 구현 가능

* 세밀한 제어가 가능함

### 한계

* 가독성이 떨어질 수 있음

* 팀 공통 규칙 유지가 어려울 수 있음

* 초보자가 이해하기 어려움

즉, Scripted는 강력하지만 관리 난이도가 올라감.

---

### 4.3 어떤 방식을 우선 이해해야 하는가

대부분의 강의나 실무 입문에서는 **Declarative Pipeline**을 먼저 이해하는 것이 좋음.

그 이유는 다음과 같음.

* 구조가 안정적임

* Jenkins 공식 권장 방향과 잘 맞음

* 공통 템플릿화가 쉬움

* 코드 리뷰가 쉬움

실무에서도 Scripted가 완전히 사라진 것은 아니지만, 기본 설명과 표준 파이프라인 작성은 Declarative 중심으로 가져가는 경우가 많음.

---

## 5. Declarative Pipeline의 기본 구조

Declarative Pipeline은 보통 다음 구조를 가짐.

```
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                echo 'checkout'
            }
        }

        stage('Build') {
            steps {
                echo 'build'
            }
        }

        stage('Test') {
            steps {
                echo 'test'
            }
        }
    }

    post {
        success {
            echo 'success'
        }
        failure {
            echo 'failure'
        }
    }
}
```

이 구조를 정확히 이해하는 것이 Jenkins Pipeline 학습의 핵심이다.

---

## 6. 주요 구성 요소 상세 설명

## 6.1 `pipeline`

`pipeline` 블록은 Declarative Pipeline 전체를 감싸는 최상위 영역이다.

이 안에서 Agent, Stage, 환경 변수, 후처리 등을 정의함.

즉, Jenkins는 `pipeline { ... }` 구조를 기준으로 하나의 파이프라인 실행 단위를 이해함.

---

## 6.2 `agent`

### 의미

`agent`는 이 파이프라인 또는 특정 Stage가 **어느 실행 환경에서 동작할지**를 지정하는 요소다.

예:

```
agent any
```

이 의미는 Jenkins가 사용할 수 있는 어떤 Agent든 선택해서 실행하라는 뜻이다.

---

### 왜 필요한가

Jenkins는 Controller / Agent 구조를 가질 수 있기 때문에,

실제 작업이 어디서 실행될지 지정할 수 있어야 함.

예를 들어:

* Linux 환경에서만 빌드 가능

* Docker 명령이 설치된 노드에서만 실행 가능

* 특정 Label이 붙은 Agent에서만 실행 가능

이런 경우 `agent` 설정이 중요해짐.

---

### 대표 방식

### 1) `any`

사용 가능한 아무 Agent에서나 실행함.

### 2) `label`

특정 Label이 있는 Agent에서 실행함.

예:

```
agent {
    label 'docker'
}
```

이 경우 `docker`라는 Label을 가진 Agent에서 실행됨.

### 3) `none`

파이프라인 전체에는 Agent를 지정하지 않고, 각 Stage별로 따로 지정할 때 사용함.

---

## 6.3 `stages`

`stages` 블록은 파이프라인의 주요 절차들을 담는 영역이다.

즉, 실제 CI/CD 흐름의 큰 단계들을 여기에 정의함.

예:

* Checkout

* Build

* Test

* Package

* Deploy

파이프라인이 하나의 "프로세스"라면, Stage는 그 안의 **구간**이라고 보면 됨.

---

## 6.4 `stage`

`stage`는 개별 단계 하나를 의미한다.

예:

```
stage('Build') {
    steps {
        echo 'build'
    }
}
```

이 코드에서 `Build`는 Stage 이름이다.

Stage를 나누는 이유는 단순 보기 좋게 하기 위해서만이 아님.

다음 목적이 있음.

* 파이프라인 진행 상황을 명확히 보여줌

* 실패 지점을 빠르게 파악하게 해줌

* 논리적 단위로 절차를 나눔

* 조건부 실행이나 병렬 실행을 구성하기 쉬워짐

즉, Stage는 가독성과 운영성 दोनों에 모두 중요함.

---

## 6.5 `steps`

`steps`는 각 Stage 안에서 실제로 수행할 작업을 정의하는 영역이다.

즉, Stage가 "무슨 구간인가"를 나타낸다면, Steps는 "그 구간에서 실제로 무엇을 할 것인가"를 적는 부분이다.

예:

```
steps {
    sh 'npm install'
    sh 'npm test'
}
```

이 경우 쉘 명령 두 개가 순서대로 실행됨.

---

### 자주 사용하는 step 예시

### `echo`

간단한 메시지를 로그에 출력함.

```
echo '빌드 시작'
```

### `sh`

리눅스/유닉스 계열 쉘 명령을 실행함.

```
sh 'mvn clean package'
```

### `bat`

Windows 배치 명령을 실행함.

```
bat 'dir'
```

### `git`

Git 저장소에서 코드를 가져옴.

### `checkout`

소스코드 체크아웃을 보다 세밀하게 제어할 때 사용함.

즉, Steps는 Jenkins 파이프라인에서 실제 명령 실행의 핵심이다.

---

## 6.6 `post`

`post`는 파이프라인 또는 Stage가 끝난 뒤 수행할 후처리 작업을 정의하는 블록이다.

예:

```
post {
    success {
        echo '성공'
    }
    failure {
        echo '실패'
    }
}
```

---

### 왜 필요한가

파이프라인은 성공했을 때와 실패했을 때 후속 처리가 다를 수 있음.

예:

* 성공 시 배포 완료 알림 발송

* 실패 시 담당자에게 에러 알림 발송

* 항상 로그 파일 정리

* 테스트 리포트 업로드

이런 작업을 `post`에서 처리함.

---

### 자주 사용하는 조건

### `always`

성공/실패와 관계없이 항상 실행됨.

### `success`

성공했을 때만 실행됨.

### `failure`

실패했을 때만 실행됨.

### `unstable`

테스트 불안정 등으로 상태가 unstable일 때 실행됨.

### `changed`

이전 실행과 결과가 달라졌을 때 실행됨.

즉, `post`는 운영 관점에서 매우 중요함.

결과 정리, 알림, 리포트 수집이 여기서 많이 이루어짐.

---

## 7. 자주 사용하는 보조 구성 요소

Pipeline은 기본 구조만으로도 동작하지만, 실제로는 여러 보조 요소를 함께 사용하게 됨.

---

## 7.1 `environment`

`environment`는 환경 변수를 정의하는 블록이다.

예:

```
environment {
    APP_NAME = 'sample-app'
    ENV = 'dev'
}
```

이렇게 정의하면 이후 Stage나 Step 안에서 공통으로 사용할 수 있음.

---

### 왜 필요한가

파이프라인에는 반복해서 사용하는 값이 많음.

예:

* 애플리케이션 이름

* 이미지 태그

* 배포 환경 이름

* 레지스트리 주소

* 경로 정보

이런 값을 하드코딩하지 않고 변수화하면 유지보수가 쉬워짐.

---

## 7.2 `parameters`

`parameters`는 파이프라인 실행 시 사용자가 값을 입력하거나 선택하도록 만드는 기능이다.

예:

* 배포 대상 환경 선택

* 특정 브랜치 선택

* 운영 배포 여부 확인

즉, 완전 자동 실행만이 아니라, **제어된 수동 실행**도 구성할 수 있음.

---

## 7.3 `tools`

`tools`는 Jenkins에 사전 등록된 도구를 파이프라인에서 사용하도록 선언하는 기능이다.

예:

* JDK

* Maven

* Gradle

* Node.js

이 블록을 사용하면 파이프라인 실행 시 필요한 툴체인을 통일성 있게 적용할 수 있음.

---

## 7.4 `when`

`when`은 특정 조건에서만 Stage를 실행하도록 제어하는 기능이다.

예를 들면 다음 조건이 가능함.

* 특정 브랜치일 때만 실행

* 태그 빌드일 때만 실행

* 특정 환경 파라미터일 때만 실행

즉, 파이프라인을 모든 상황에 동일하게 실행하지 않고, 맥락에 맞게 분기할 수 있게 해줌.

이 기능은 실무에서 매우 자주 쓰임.

예:

* `main` 브랜치에서만 Deploy Stage 실행

* feature 브랜치에서는 Docker Push 생략

* 운영 환경 선택 시 승인 단계 추가

---

## 7.5 `input`

`input`은 파이프라인 중간에 사람의 승인을 받기 위해 사용됨.

예:

* 운영 배포 전에 승인

* 특정 단계 진입 전 확인

* 긴급 배포 여부 선택

즉, Jenkins Pipeline은 완전 자동만 지원하는 것이 아니라,

**자동화와 통제를 섞은 구조**도 지원함.

---

## 7.6 `options`

`options`는 파이프라인 동작 전반의 실행 정책을 정하는 데 사용함.

예:

* 중복 실행 방지

* 타임아웃 설정

* 로그 보존 정책

* timestamps 출력

이 요소는 실무 운영성에 직접 영향을 줌.

예를 들어 타임아웃이 없으면 무한 대기 상태가 생길 수 있고,

중복 실행 방지가 없으면 같은 파이프라인이 동시에 실행돼 충돌할 수 있음.

---

## 8. Stage 설계 관점

Pipeline을 구성할 때는 Stage를 어떻게 나눌지 고민해야 함.

이건 단순 문법 문제가 아니라 설계 문제다.

---

### 8.1 좋은 Stage 분리의 기준

### 1) 논리적으로 구분될 것

예:

* Checkout

* Build

* Test

* Package

* Deploy

### 2) 실패 원인을 빠르게 찾을 수 있을 것

Build 실패인지 Test 실패인지 Deploy 실패인지 즉시 보여야 함.

### 3) 너무 잘게 쪼개지지 않을 것

Stage가 지나치게 많으면 오히려 흐름 파악이 어려워질 수 있음.

### 4) 운영 관점에서 의미가 있을 것

예를 들어 "Install Dependencies"를 Stage로 뺄지 Build 안에 넣을지는 프로젝트 규모에 따라 결정할 수 있음.

---

### 8.2 Stage 이름의 중요성

Stage 이름은 로그와 UI에서 그대로 보이기 때문에 명확해야 함.

좋은 예:

* Checkout

* Build

* Unit Test

* Docker Build

* Push Image

* Deploy to Dev

애매한 예:

* Step1

* Process

* Run

* Execute

즉, Stage 이름만 봐도 현재 파이프라인이 무엇을 하고 있는지 알 수 있어야 함.

---

## 9. 병렬 실행과 조건 분기 개요

Jenkins Pipeline은 단순 순차 실행만 되는 것이 아님.

필요하면 병렬 실행과 조건 분기를 구성할 수 있음.

---

### 9.1 병렬 실행

예:

* 여러 테스트 세트를 동시에 실행

* Linux와 Windows 빌드를 동시에 수행

* 서비스별 독립 빌드를 동시에 수행

이렇게 하면 전체 파이프라인 시간을 줄일 수 있음.

다만 병렬 실행은 자원 사용량과 로그 해석 난이도를 높일 수 있으므로, 무조건 많이 쓰는 것이 좋은 것은 아님.

---

### 9.2 조건 분기

예:

* 브랜치가 `main`일 때만 배포

* 태그가 있을 때만 릴리스 아티팩트 생성

* 파라미터가 `prod`일 때만 승인 단계 실행

이 구조는 실무 파이프라인의 핵심이다.

모든 변경이 같은 수준의 절차를 거쳐야 하는 것은 아니기 때문임.

---

## 10. Freestyle Job과 Pipeline 비교

| 항목 | Freestyle Job | Pipeline |
| --- | --- | --- |
| 설정 방식 | UI 중심 | 코드 중심 |
| 버전 관리 | 어려움 | 쉬움 |
| 복잡한 흐름 표현 | 제한적 | 강력함 |
| 조건 분기/병렬 처리 | 불편함 | 유연함 |
| 코드 리뷰 | 어려움 | 가능 |
| 재현성 | 낮음 | 높음 |

Jenkins를 현대적으로 사용한다는 것은 대부분 **Pipeline 중심 운영**을 의미.

---

## 11. 아키텍처 관점 정리

Jenkins Pipeline을 아키텍처 관점에서 보면 다음처럼 정리할 수 있음.

```
Jenkinsfile
   ↓
Jenkins Controller가 파이프라인 해석
   ↓
지정된 Agent에서 Stage별 실행
   ↓
각 Stage에서 Steps 수행
   ↓
성공/실패 상태 기록
   ↓
post 처리 및 결과 알림
```

즉, Jenkins Pipeline은 단순 스크립트 파일이 아니라

**Jenkins Controller가 해석하고 Agent에서 실행하는 절차 정의서**다.

---

## 요약

* Jenkins Pipeline은 CI/CD 절차를 단계별로 정의하고 실행하는 구조임

* 핵심 철학은 Pipeline as Code이며, 이를 구현하는 파일이 Jenkinsfile임

* Declarative Pipeline은 구조가 명확해 입문과 표준화에 유리함

* 주요 구성 요소는 `pipeline`, `agent`, `stages`, `stage`, `steps`, `post`임

* `environment`, `parameters`, `when`, `input`, `options` 같은 요소를 통해 실무형 제어가 가능함

* 좋은 Pipeline은 단순히 동작하는 것이 아니라, 읽기 쉽고 추적 가능하며 운영하기 쉬워야 함

* Jenkins를 현대적으로 사용하려면 Freestyle보다 Pipeline 중심 관점이 중요함