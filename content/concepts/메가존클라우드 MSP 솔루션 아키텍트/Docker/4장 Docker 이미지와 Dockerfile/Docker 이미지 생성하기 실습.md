---
title: "Docker 이미지 생성하기 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Docker", "4장 Docker 이미지와 Dockerfile"]
is_public: true
draft: false
---

# Docker 이미지 생성하기 실습

---

## 1) 이미지 생성하기: `docker build`

참고: Docker build 명령 공식 문서

* `docker build`: Docker Engine CLI build

* `docker buildx build`: BuildKit 기반 확장 빌더(멀티 플랫폼/캐시 고급 기능)

### 1.1 기본 문법 (정확한 형태)

```
docker build [OPTIONS] <BUILD_CONTEXT>
```

Dockerfile 위치를 따로 지정하면:

```
docker build -f <DOCKERFILE_PATH> -t <IMAGE:TAG> <BUILD_CONTEXT>
```

예시:

```
docker build -t myapp:1.0 .
docker build -f Dockerfile.alpine -t myapp:alpine .
```

### (중요) `<BUILD_CONTEXT>`란?

`docker build ... <BUILD_CONTEXT>`의 마지막 인자(보통 `.`)는 **빌드 컨텍스트(Build Context)** 이다.

* Docker는 빌드 시 `<BUILD_CONTEXT>` 디렉터리를 **스냅샷처럼 묶어서** 빌더로 전달함.

* Dockerfile의 `COPY`, `ADD`는 **컨텍스트 안의 파일만** 가져올 수 있다.

* 즉, Dockerfile에 상대 경로가 있으면 기준은 항상 **빌드 컨텍스트**이다.

---

## 2) `docker build` 주요 옵션

| Option | Short | 설명 | 언제 쓰나(실무 관점) |
| --- | --- | --- | --- |
| `--build-arg` |  | Dockerfile의 `ARG`에 값 전달 | OS/버전 등 빌드 분기 |
| `--file` | `-f` | 사용할 Dockerfile 경로 지정 | 여러 Dockerfile 운영 |
| `--label` |  | 이미지 메타데이터 라벨 추가 | 버전/빌드정보 기록 |
| `--no-cache` |  | 캐시 없이 처음부터 빌드 | 캐시 오염 의심/최신 패키지 확인 |
| `--platform` |  | 아키텍처 지정 | amd64/arm64 교차 빌드 |
| `--pull` |  | 베이스 이미지 강제 최신 pull | 보안 패치 반영 |
| `--tag` | `-t` | 이미지 이름:태그 지정 | 버전 관리/배포 |

> 주의: `--build-arg` (단수)입니다.

---

## 3) `.dockerignore`

빌드 컨텍스트가 커지면:

* 빌드가 느려지고

* 불필요 파일/민감 정보가 이미지에 섞일 위험이 커집니다.

`.dockerignore`로 컨텍스트에 포함되지 않게 제외합니다.

예시:

```
.git
*.log
node_modules
dist
target
```

> 체크포인트
>
> “컨텍스트는 작을수록 좋다”
>
> → 빌드 속도, 보안, 재현성 모두에 영향을 준다.

---

## 4) Dockerfile 핵심 Instruction

| Instruction | 설명 | 동작 시점 |
| --- | --- | --- |
| `FROM` | 베이스 이미지 지정 | 빌드 |
| `ARG` | 빌드 타임 변수 | 빌드 |
| `ENV` | 런타임 환경 변수 | 실행(컨테이너) |
| `ADD` | 복사 + (압축 해제/URL 등) 기능 | 빌드 |
| `COPY` | 파일/디렉터리 복사(권장) | 빌드 |
| `LABEL` | 이미지 라벨(메타데이터) | 빌드 |
| `EXPOSE` | 포트 “문서화” 메타데이터 | 빌드(메타) |
| `USER` | 실행 사용자 지정 | 실행 |
| `WORKDIR` | 작업 디렉터리 지정 | 빌드/실행 |
| `RUN` | 빌드 중 명령 실행(레이어 생성) | 빌드 |
| `CMD` | 기본 실행 명령(덮어쓰기 쉬움) | 실행 |
| `ENTRYPOINT` | “항상 실행”되는 명령 | 실행 |

### RUN vs CMD

* `RUN` : 이미지 만들 때 실행 (결과가 이미지 레이어로 굳음)

* `CMD/ENTRYPOINT` : 컨테이너 시작할 때 실행 (PID 1 프로세스)

---

## 5) 주의사항

1. `f`를 지정하지 않으면 기본 파일명 `Dockerfile`을 사용한다.

2. Dockerfile의 상대 경로는 **빌드 컨텍스트 기준**으로 계산된다.

3. 캐시가 켜져 있으면 `apt-get update` 결과가 오래된 상태로 재사용될 수 있다.
   * 해결: `-no-cache`

---

## 6) 많이 사용하는 Base 이미지

### 6.1 scratch

* “빈 이미지”

* 정적 바이너리(예: Go static) 같은 최소 실행 파일만 넣을 때 사용

* 레이어를 추가하지 않는다는 의미: scratch 자체는 빈 기반이므로 **필요한 파일만 올리게 됨**

### 6.2 alpine

* 매우 작은 리눅스(경량)

* 패키지 관리: `apk`

* 디버깅 도구를 넣기 쉽고, 작고 빠름

### 6.3 distroless

* 실행에 필요한 런타임만 포함 (쉘, 패키지 매니저 없음)

* 운영 환경에서 **공격 표면(attack surface)** 감소

* 디버깅은 어렵지만 보안/경량에 유리

---

## 7) Multi-stage build

### 7.1 왜 쓰나?

빌드에 필요한 도구(컴파일러 등)와 실행에 필요한 파일은 다르다.

* 빌드 스테이지: 컴파일러/빌드도구 포함 (무거워도 됨)

* 런타임 스테이지: 실행 파일만 포함 (가볍고 안전)

결과:

* **이미지 크기 감소**

* **보안 강화**(운영 이미지에 bash/curl/gcc 등 제거)

* **운영 표준 패턴**

---

# 8) 실습/연습 1: Go 서버 이미지 제작하기 (Ubuntu/Alpine/Scratch 비교)

## 8.1 폴더 구조

```
.
├── src
│   ├── go.mod
│   └── main.go
└── Dockerfile
```

### go.mod

```
module example/hello
go 1.19
```

### main.go

```
package main

import (
  "io"
  "net/http"
  "log"
)

func HelloServer(w http.ResponseWriter, req *http.Request) {
  io.WriteString(w, "Hello, Worlds!\n")
}

func main() {
  http.HandleFunc("/", HelloServer)
  log.Fatal(http.ListenAndServe(":80", nil))
}
```

---

## 8.2 Dockerfile (Debian bullseye 기반)

```
FROM golang:1.19-bullseye

WORKDIR /app
COPY src ./

# CGO_ENABLED=0: 정적 링크에 가깝게 빌드(런타임 의존성 감소)
RUN CGO_ENABLED=0 go build -o main

CMD ["/app/main"]
```

## 8.3 Dockerfile (Alpine 기반)

```
FROM golang:1.19-alpine

WORKDIR /app
COPY src ./
RUN CGO_ENABLED=0 go build -o main

CMD ["/app/main"]
```

## 8.4 Dockerfile (Scratch 기반, Multi-stage)

```
FROM golang:1.19-alpine AS build

WORKDIR /app
COPY src ./
RUN CGO_ENABLED=0 go build -o main

FROM scratch
COPY --from=build /app/main /app/main
CMD ["/app/main"]
```

---

## 8.5 빌드 & 실행

```
docker build -t go:debian -f Dockerfile.debian .
docker build -t go:alpine -f Dockerfile.alpine .
docker build -t go:scratch -f Dockerfile.scratch .
```

실행 테스트:

```
docker run -d -p 80:80 go:scratch
curl localhost:80
# Hello, Worlds!
```

이미지 크기 비교:

```
docker images go
```

> 체크포인트(강의 질문)
>
> * 왜 scratch가 가장 작나? (OS/쉘/패키지 없음, 바이너리만 포함)
>
> * 왜 debian이 큰가? (유틸/라이브러리/패키지 포함)

---

# 9) 연습 2: 실습용 Ubuntu 이미지 제작하기 (Docker CLI 설치)

## 9.1 파일 구조

```
.
├── Dockerfile
└── install_docker_engine.sh
```

> 이 이미지는 “Docker 엔진을 설치한 이미지”일 뿐, 컨테이너 안에서 데몬이 자동으로 뜨지 않.
>
> 그래서 `docker version`은 Client는 나오고 Server 연결은 실패할 수 있습니다(정상).

---

**install\_docker\_engine.sh**

> <https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository>

```
# Add Docker's official GPG key:
apt-get update && apt-get upgrade
apt-get install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update
```

**Dockerfile**

```
FROM ubuntu:22.04

RUN mkdir -p /scripts
COPY install_docker_engine.sh /scripts

WORKDIR /scripts

RUN chmod +x install_docker_engine.sh
RUN ./install_docker_engine.sh

RUN apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

## 9.4 빌드 & 확인

```
docker build -t mgzmsp:base.v1 .
docker run --rm mgzmsp:base.v1 docker version
```

### 왜 정상인가?

* 컨테이너 안에 `dockerd` 데몬이 실행 중이 아니기 때문

* 컨테이너는 systemd 서비스가 기본으로 자동 구동되지 않음

> 보너스(선택 실습): 호스트 도커 소켓 공유 시 “Server”도 보이게 만들기

```
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock mgzmsp:base.v1 docker version
```

---

# 10) 실습 3: ARG로 base 이미지 변경하기

## 요구사항

* ARG 이름: `OS`

* `FROM golang:1.19-${OS}` 형태로 베이스 변경

* ARG 값을 `ENV BASE`에 저장

* `-build-arg`로 `bullseye`, `alpine` 빌드

* `docker exec`로 환경변수 확인

## 예시 Dockerfile

```
ARG OS=bullseye
FROM golang:1.19-${OS}

ARG OS
ENV BASE=${OS}

WORKDIR /app
COPY src ./
RUN CGO_ENABLED=0 go build -o main

CMD ["sh", "-c", "echo BASE=$BASE && /app/main"]
```

빌드:

```
docker build --build-arg OS=bullseye -t go:debian .
docker build --build-arg OS=alpine  -t go:alpine .
```

실행 후 확인:

```
docker run -d --name go1 -p 8080:80 go:alpine
docker exec go1 env | grep BASE
# BASE=alpine
```

> 오해 방지
>
> `ARG`는 컨테이너에 남지 않음.
>
> `ENV BASE=${OS}` 에 의해 BASE에는 남아 있음.

---