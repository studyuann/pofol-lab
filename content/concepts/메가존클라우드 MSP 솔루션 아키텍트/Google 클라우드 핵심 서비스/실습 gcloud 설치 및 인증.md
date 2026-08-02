---
title: "실습 gcloud 설치 및 인증"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Google 클라우드 핵심 서비스"]
is_public: true
draft: false
---

# 실습. gcloud 설치 및 인증

## 1. 실습 개요

이 실습에서는 로컬 PC에 **Google Cloud CLI(gcloud CLI)** 를 설치하고, Google 계정으로 인증한 뒤, 프로젝트를 선택하고 기본 동작 여부를 확인한다.

또한 `gcloud auth login` 과 `gcloud auth application-default login` 의 차이도 함께 확인한다. `gcloud init` 은 설치 후 초기 설정 절차를 수행하며, `gcloud auth application-default login` 으로 만드는 ADC 자격 증명은 **gcloud CLI 자체가 사용하는 인증과는 별개이다.**

---

## 2. 학습 목표

이 실습을 완료하면 다음을 할 수 있어야 한다.

* Windows에서 gcloud CLI를 설치할 수 있음

* Linux에서 gcloud CLI를 설치할 수 있음

* `gcloud init` 를 통해 초기 설정을 수행할 수 있음

* 사용자 계정으로 gcloud CLI 인증을 수행할 수 있음

* ADC 인증을 별도로 구성할 수 있음

* 현재 로그인 계정, 프로젝트, CLI 버전을 확인할 수 있음

---

## 3. 사전 준비

실습 전에 다음을 준비한다.

* Google 계정

* Google Cloud 프로젝트 1개

* 인터넷 연결

* 관리자 권한이 있는 Windows 또는 sudo 권한이 있는 Linux 계정

또한 Google Cloud CLI는 Cloud Shell에는 기본 포함되지만, **로컬 환경에서는 직접 설치해야 한다**. 로컬 환경에서는 일반적으로 사용자 계정으로 로그인해서 gcloud CLI를 사용하며, 필요하면 서비스 계정 또는 서비스 계정 가장(impersonation)도 사용할 수 있다.

---

# 4. gcloud 인증 개념 먼저 이해하기

실습 전에 인증 개념을 먼저 정리한다.

## 4.1 `gcloud auth login`

이 명령은 **사용자가 gcloud CLI 자체를 사용할 때 필요한 로그인**이다.

브라우저가 열리고 Google 계정으로 로그인하면, 로컬 PC에 사용자 자격 증명이 저장된다.

## 4.2 `gcloud auth application-default login`

이 명령은 **애플리케이션 기본 사용자 인증 정보(ADC)** 를 구성하는 명령이다.

즉, Python 코드, SDK, 클라이언트 라이브러리 등이 “기본 자격 증명”을 찾을 때 사용하도록 만드는 인증이다.

중요한 점은 이 인증은 **gcloud CLI용 로그인과 별개**라는 점이다.

## 4.3 `gcloud init`

설치 후 초기 설정을 수행하는 명령이다.

이 명령은 로그인, 기본 프로젝트 선택, 기본 리전/존 등 여러 설정을 구성하는 데 사용된다. 또한 필요하면 새 configuration을 만들거나 기존 설정을 바꾸는 데도 사용된다.

---

# 5. Windows에서 gcloud 설치 실습

## 5.1 설치 목적

Windows PC에 Google Cloud CLI를 설치하고, 명령 프롬프트 또는 PowerShell에서 `gcloud` 명령을 실행할 수 있도록 구성한다.

## 5.2 설치 방법 개요

Google은 Windows에서 **설치 프로그램 방식**과 **압축 아카이브 방식**을 제공한다. 일반 실습에서는 설치 프로그램 방식이 가장 쉽다.

## 5.3 설치 절차

### 1단계. 설치 파일 다운로드

브라우저에서 Google Cloud CLI 설치 페이지에 접속한다.

<https://docs.cloud.google.com/sdk/docs/install-sdk?hl=ko>

Windows용 설치 프로그램을 내려받는다.

### 2단계. 설치 프로그램 실행

다운로드한 설치 파일을 실행한다.

설치 진행 중 보게 되는 일반적인 흐름은 다음과 같다.

* 설치 경로 선택

* PATH 등록 여부 설정

* 명령줄 완성 기능 관련 설정

* Python 포함 여부 또는 내부 번들 Python 사용 여부 확인

### 3단계. PowerShell 또는 CMD 열기

설치가 끝나면 새 PowerShell 또는 CMD 창을 연다.

이미 열려 있던 창에서는 PATH 반영이 안 될 수 있으므로, **반드시 새 창** 을 연다.

### 4단계. 설치 확인

아래 명령을 실행한다.

```
gcloud version
```

## 5.4 예상 결과

정상 출력 예시는 다음과 비슷하다.

```
Google Cloud SDK 564.0.0
bq ...
core ...
gsutil ...
```

버전 번호는 시점에 따라 달라질 수 있다.

## 5.5 명령 인식이 안 될 때 점검

`gcloud` 를 입력했는데 명령을 찾을 수 없다고 나오면 다음을 점검한다.

* 설치가 정상 완료되었는지 확인

* 새 터미널 창을 열었는지 확인

* PATH가 반영되었는지 확인

* 재부팅 또는 로그아웃 후 재로그인

---

# 6. Windows에서 gcloud 인증 실습

## 6.1 사용자 로그인

다음 명령을 실행한다.

```
gcloud auth login
```

실행하면 브라우저가 열리고 Google 로그인 창이 나온다.

사용할 Google 계정으로 로그인한다.

권한 요청 창이 나타나면 승인한다.

### 설명

이 명령은 **gcloud CLI 사용을 위한 사용자 로그인**이다.

## 6.2 초기 설정 수행

로그인 후 아래 명령을 실행한다.

```
gcloud init
```

이 명령은 다음 작업을 도와준다.

* 로그인 상태 확인

* 기본 configuration 선택 또는 생성

* 기본 프로젝트 선택

* 기본 리전/존 설정 가능

Google 문서에 따르면 `gcloud init` 은 설치 후 초기 설정을 수행하며, 설정 변경이나 새 구성 생성에도 사용할 수 있다. ([Google Cloud Documentation](https://docs.cloud.google.com/sdk/docs/initializing?utm_source=chatgpt.com))

## 6.3 현재 로그인 계정 확인

```
gcloud auth list
```

이 명령은 현재 저장된 계정 목록을 보여준다.

활성 계정에는 표시가 붙는다.

## 6.4 현재 프로젝트 확인

```
gcloud config list
```

또는 더 직접적으로 다음 명령을 사용할 수 있다.

```
gcloud config get-value project
```

## 6.5 프로젝트 변경

```
gcloud config set project 프로젝트ID
```

예시:

```
gcloud config set project my-gcp-lab-001
```

## 6.6 동작 확인용 테스트 명령

```
gcloud projects list
```

또는 Compute Engine API가 사용 가능한 프로젝트라면 다음처럼도 확인할 수 있다.

```
gcloud compute zones list
```

정상적으로 결과가 보이면 인증과 기본 설정이 잘 된 상태다.

---

# 7. Windows에서 ADC 인증 실습

## 7.1 왜 추가로 필요한가

`gcloud auth login` 은 CLI용 로그인이다.

하지만 Python 코드나 Terraform, 클라이언트 라이브러리가 **Application Default Credentials** 를 요구하는 경우가 많다.

그때는 별도로 ADC를 구성해야 한다.

## 7.2 실행 명령

```
gcloud auth application-default login
```

브라우저가 열리면 같은 방식으로 로그인한다.

## 7.3 설명

이 명령은 로컬 파일 시스템의 **운영체제별 well-known location** 에 ADC용 JSON 자격 증명을 만든다. 운영체제마다 저장 위치가 다르며, 사용자 계정 기반 ADC는 일반적으로 `cloud-platform` 범위의 액세스 토큰을 사용한다.

## 7.4 확인용 예시

```
gcloud auth application-default print-access-token
```

토큰이 출력되면 ADC가 준비된 것이다.

---

# 8. Linux에서 gcloud 설치 실습

## 8.1 설치 목적

Linux 서버 또는 Linux VM에 gcloud CLI를 설치하고 쉘에서 바로 사용할 수 있도록 구성한다.

## 8.2 설치 방식

Linux에서는 대표적으로 다음 방식이 있다.

* 패키지 저장소 방식

* 버전 아카이브 압축 해제 방식

* 인터랙티브 설치 스크립트 방식

## 8.3 Linux 설치 예시 1: 압축 아카이브 방식

아래는 일반적인 x86\_64 Linux 기준 예시다.

### 1단계. 패키지 다운로드

```
curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-x86_64.tar.gz
```

### 2단계. 압축 해제

```
tar -xf google-cloud-cli-linux-x86_64.tar.gz
```

### 3단계. 설치 스크립트 실행

```
./google-cloud-sdk/install.sh
```

### 4단계. 쉘 반영

설치 도중 안내된 내용을 적용하거나, 새 터미널을 연다.

필요하면 아래처럼 쉘 설정을 반영한다.

```
source ~/.bashrc
```

또는 zsh라면:

```
source ~/.zshrc
```

### 5단계. 설치 확인

```
gcloud version
```

---

# 9. Linux에서 gcloud 인증 실습

## 9.1 사용자 로그인

```
gcloud auth login
```

리눅스 데스크톱 환경이라면 브라우저가 열리고 로그인하면 된다.

SSH 접속 환경처럼 브라우저가 바로 열리지 않으면, 명령 출력에 표시되는 URL을 복사해서 로컬 브라우저에서 열어 인증한다.

## 9.2 초기 설정

```
gcloud init
```

실행 후 프로젝트를 선택한다.

필요하면 기본 compute region/zone 도 설정한다.

## 9.3 로그인 계정 확인

```
gcloud auth list
```

## 9.4 프로젝트 확인

```
gcloud config list
```

## 9.5 프로젝트 변경

```
gcloud config set project 프로젝트ID
```

## 9.6 테스트 명령

```
gcloud projects list
```

또는

```
gcloud compute regions list
```

정상적으로 조회되면 인증과 프로젝트 설정이 완료된 것이다.

---

# 10. Linux에서 ADC 인증 실습

## 10.1 실행

```
gcloud auth application-default login
```

## 10.2 확인

```
gcloud auth application-default print-access-token
```

## 10.3 설명

ADC는 gcloud CLI 전용 로그인과 별개다.

즉, 다음처럼 구분해서 이해하면 된다.

* `gcloud auth login` → 사람이 CLI를 쓰기 위한 로그인

* `gcloud auth application-default login` → 코드나 SDK가 기본 인증으로 쓰기 위한 로그인

---

# 11. 공통 실습: 기본 설정 점검 명령

설치와 인증이 끝나면 아래 명령을 순서대로 실행해본다.

## 11.1 버전 확인

```
gcloud version
```

## 11.2 로그인 계정 확인

```
gcloud auth list
```

## 11.3 현재 프로젝트 확인

```
gcloud config get-value project
```

## 11.4 전체 설정 확인

```
gcloud config list
```

## 11.5 프로젝트 목록 조회

```
gcloud projects list
```

## 11.6 현재 설정된 인증 토큰 기반 테스트

```
gcloud auth print-access-token
```

---

# 12. 실습용 정리 명령

수업 중 계정 또는 설정이 꼬였을 때 자주 쓰는 명령이다.

## 12.1 현재 설정된 계정 로그아웃

```
gcloud auth revoke
```

특정 계정만 지우려면 계정을 지정할 수 있다.

```
gcloud auth revoke user@example.com
```

## 12.2 ADC 제거 또는 재설정 전 정리

ADC를 새로 만들기 전에 기존 구성을 정리해야 할 때가 있다.

## 12.3 새 설정으로 다시 초기화

```
gcloud init
```

---

# 13. 실습 중 자주 발생하는 문제

## 13.1 `gcloud: command not found`

원인:

* PATH 반영 안 됨

* 새 터미널 안 열었음

* 설치 실패

조치:

* 새 터미널 열기

* `gcloud version` 재확인

* Linux는 `source ~/.bashrc`

* Windows는 새 PowerShell 실행

## 13.2 로그인은 했는데 프로젝트가 없음

원인:

* 다른 계정으로 로그인했음

* 권한 없는 계정 사용 중

* 프로젝트가 삭제되었거나 접근 권한 없음

조치:

```
gcloud auth list
gcloud projects list
```

확인 후 올바른 계정으로 재로그인한다.

## 13.3 코드에서는 인증이 안 되는데 CLI는 됨

원인:

* `gcloud auth login` 만 했고 ADC는 만들지 않았음

조치:

```
gcloud auth application-default login
```

## 13.4 오래된 CLI 사용

원인:

* 예전 버전을 설치했음

* 업데이트가 안 되었음

조치:

* 공식 설치 문서 확인

* 최신 버전으로 업그레이드

* `gcloud version` 확인

---

# 15. 최종 정리

* gcloud CLI는 로컬 환경에서는 직접 설치해야 함

* 설치 후에는 `gcloud init` 으로 초기 설정을 수행함

* `gcloud auth login` 은 CLI 사용을 위한 사용자 로그인임

* `gcloud auth application-default login` 은 코드와 SDK가 사용하는 ADC 구성임

* 두 인증은 목적이 다르므로 둘 다 필요한 경우가 많음

---