---
title: "2장 Docker 설치 및 기본 환경 구성"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Docker"]
is_public: true
draft: false
---

# 2장. Docker 설치 및 기본 환경 구성

---

## 2장 학습 목표

* Docker가 **어떤 서비스 형태로 동작**하는지 이해한다.

* Linux 서버에서 Docker를 **공식 권장 방식**으로 설치할 수 있다.

* docker 명령 실행 시 **권한 문제가 왜 발생하는지** 설명할 수 있다.

* Docker Engine의 **기본 구성 정보**를 읽고 해석할 수 있다.

---

## 2.1 Docker 설치 개요

### 2.1.1 Docker 설치 전 반드시 이해해야 할 점

Docker는 단순한 실행 파일 하나가 아닙니다.

Docker 구성 요소를 정리하면:

* **dockerd** : 실제 컨테이너/이미지를 관리하는 데몬

* **docker CLI** : 사용자가 입력하는 명령어 도구

* **containerd / runc** : 컨테이너 실행을 담당하는 저수준 런타임

👉 즉, Docker는 **백그라운드 서비스 + CLI 도구의 조합**.

---

### 2.1.2 설치 환경 기준

* OS: **Ubuntu 22.04 LTS**

* 아키텍처: x86\_64

* 사용자: sudo 권한 보유

* 인터넷 연결 가능

> 다른 배포판(CentOS/RHEL/Amazon Linux)은 패키지 관리 도구만 다를 뿐, 개념은 동일

---

## 2.2 Docker 설치 (공식 Repository 방식)

> ⚠️ apt 기본 저장소의 docker 패키지는 **버전이 오래된 경우가 많음**
>
> → 반드시 **Docker 공식 저장소**를 사용

---

### 2.2.1 기존 Docker 관련 패키지 제거

```
sudo apt remove -y docker docker-engine docker.io containerd runc
```

### 설명

* 과거 버전 또는 배포판 기본 Docker 제거

* 충돌 방지 목적

* 실제 운영에서도 “깨끗한 설치”가 원칙

---

### 2.2.2 패키지 업데이트 및 필수 패키지 설치

```
sudo apt update
sudo apt install -y \
  ca-certificates \
  curl \
  gnupg \
  lsb-release
```

### 패키지 설명

* `ca-certificates` : HTTPS 인증서 검증

* `curl` : Docker GPG 키 다운로드

* `gnupg` : GPG 키 관리

* `lsb-release` : 배포판 정보 확인

---

### 2.2.3 Docker 공식 GPG 키 등록

```
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
```

### 왜 필요한가?

* Docker 패키지가 **신뢰할 수 있는 출처**임을 검증하기 위함

* GPG 키가 없으면 apt는 설치를 거부

---

### 2.2.4 Docker 공식 Repository 등록

```
echo \
  "deb [arch=$(dpkg --print-architecture) \
  signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

### 설명

* `$(lsb_release -cs)`

  → jammy, focal 등 배포판 코드명 자동 삽입

* `stable`

  → 운영 환경에 적합한 안정 버전 사용

---

### 2.2.5 Docker Engine 설치

```
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io
```

### 설치되는 주요 패키지

* `docker-ce` : Docker Engine

* `docker-ce-cli` : docker 명령어

* `containerd.io` : 컨테이너 런타임

---

## 2.3 Docker 서비스 관리(systemd)

### 2.3.1 Docker 서비스 상태 확인

```
sudo systemctl status docker
```

### 확인 포인트

* `Active: active (running)`

* dockerd 프로세스 실행 여부

👉 Docker는 **systemd 서비스**로 동작

---

### 2.3.2 Docker 서비스 제어 명령

```
sudo systemctl start docker
sudo systemctl stop docker
sudo systemctl restart docker
```

### 실무 포인트

* 설정 변경 후에는 반드시 `restart`

* 컨테이너 실행 중 `stop` 시 모든 컨테이너도 중지됨

---

### 2.3.3 부팅 시 자동 실행 설정

```
sudo systemctl enable docker
```

```
sudo systemctl is-enabled docker
```

👉 운영 서버에서는 **항상 enable 상태**가 기본

---

## 2.4 Docker 명령어 권한 구조 이해

### 2.4.1 docker 명령에 sudo가 필요한 이유

```
docker ps
```

→ Permission denied 오류 발생

### 이유

* docker 명령은 **/var/run/docker.sock** 파일을 통해 dockerd와 통신

* 이 소켓 파일의 기본 소유자는 `root:docker`

---

### 2.4.2 docker 그룹에 사용자 추가

```
sudo usermod -aG docker $USER
```

### 설명

* `aG` : 기존 그룹 유지한 채 docker 그룹 추가

* `$USER` : 현재 로그인 사용자

⚠️ **중요**

```
logout
# 또는
newgrp docker
```

→ 그룹 변경은 **재로그인 후 적용**

---

### 2.4.3 sudo 없이 docker 명령 실행 확인

```
docker ps
```

👉 정상 출력되면 설정 완료

---

## 2.5 Docker 설치 확인 및 정보 분석

### 2.5.1 Docker 버전 확인

```
docker version
```

### 출력 해석

* Client 버전

* Server(dockerd) 버전

* API Version

👉 Client/Server 구조를 눈으로 확인

---

### 2.5.2 Docker 시스템 정보 확인

```
docker info
```

### 반드시 짚고 넘어갈 항목

* `Cgroup Driver`

* `Storage Driver`

* `Kernel Version`

* `Operating System`

* `CPUs`, `Total Memory`

👉 **이 정보가 컨테이너 자원 제한, 성능, 장애 분석의 기준**

---

## 2.6 Docker 저장 구조 이해

### 2.6.1 Docker 데이터 디렉터리

```
/var/lib/docker
```

### 내부 구성 개념

* images : 이미지 레이어 저장

* containers : 컨테이너 메타데이터

* volumes : 볼륨 데이터

* overlay2 : 실제 파일시스템 레이어

---

## 2.7 Docker 설치 후 기본 점검 실습

### 실습 1) 테스트 컨테이너 실행

```
docker run hello-world
```

### 의미

* Docker Hub에서 이미지 pull

* 컨테이너 실행

* 출력 후 종료

👉 Docker **Client → Daemon → Registry → Container** 전체 흐름 확인

---

### 실습 2) Docker 데몬 프로세스 확인

```
ps -ef | grep dockerd
```

### 확인 포인트

* dockerd는 항상 실행 중인 백그라운드 프로세스

* 컨테이너 실행과 무관하게 상시 대기

---