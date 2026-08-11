---
title: "4장 Docker 이미지와 Dockerfile"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Docker"]
is_public: true
draft: false
---

# 4장. Docker 이미지와 Dockerfile

---

## 4장 학습 목표

* Docker 이미지의 **정확한 정의와 역할**을 설명할 수 있다.

* 이미지와 컨테이너의 **구조적 차이**를 이해한다.

* Docker 이미지의 **레이어 구조와 불변성(immutability)** 을 설명할 수 있다.

* Dockerfile을 작성하여 **직접 이미지를 빌드**할 수 있다.

* 이미지 **캐시, dangling image, digest** 개념을 이해하고 운영 관점에서 설명할 수 있다.

* “좋은 Docker 이미지”의 기준을 설명할 수 있다.

---

## 4.1 Docker 이미지란 무엇인가

### 4.1.1 이미지(Image)의 정의

Docker 이미지란 다음을 포함한 **읽기 전용 패키지**이다.

* 애플리케이션 실행 파일

* 라이브러리 및 런타임

* 설정 파일

* 환경 변수 정보

* 기본 실행 명령(CMD / ENTRYPOINT)

👉 **이미지는 실행되지 않는다**

👉 이미지를 실행한 결과가 **컨테이너(Container)** 다

---

### 4.1.2 이미지와 컨테이너 관계

비유로 이해하면:

* **이미지(Image)** : 설계도, 클래스

* **컨테이너(Container)** : 실행된 인스턴스, 객체

| 구분 | 이미지 | 컨테이너 |
| --- | --- | --- |
| 상태 | 정적 | 동적 |
| 수정 | 불가 | 가능 |
| 실행 | ❌ | ⭕ |
| 수명 | 영구 | 프로세스 종료 시 종료 |

---

## 4.2 Docker 이미지 레이어 구조 (핵심)

### 4.2.1 이미지 레이어란?

Docker 이미지는 하나의 파일이 아니라

**여러 개의 파일시스템 레이어가 쌓인 구조**다.

* Dockerfile의 **각 명령어 = 하나의 레이어**

* 레이어는 **불변(immutable)**

예시 개념:

```
Layer 1: ubuntu base
Layer 2: apt install nginx
Layer 3: copy index.html
Layer 4: CMD nginx
```

---

### 4.2.2 컨테이너 실행 시 구조

컨테이너가 실행되면:

```
[ Image Layers (Read Only) ]
[ Container Writable Layer ]
```

* 파일 수정은 **컨테이너 쓰기 레이어**에만 기록

* 이미지 레이어는 절대 변경되지 않음

👉 같은 이미지를 여러 컨테이너가 **공유 가능**

---

### 4.2.3 레이어 확인

```
docker history nginx
```

* 각 레이어의 생성 명령과 용량 확인

* Dockerfile 최적화의 근거 자료

---

## 4.3 Dockerfile 개요

### 4.3.1 Dockerfile이란?

Dockerfile은 **이미지를 만들기 위한 설계서**다.

* 텍스트 파일

* 위에서 아래로 순차 실행

* 한 줄 = 한 레이어

파일명:

```
Dockerfile
```

---

### 4.3.2 docker build 기본 구조

```
docker build -t myimage:1.0 .
```

| 요소 | 의미 |
| --- | --- |
| -t | 이미지 이름과 태그 |
| . | build context (현재 디렉터리) |

⚠️ build context 안의 모든 파일은 **Docker 데몬으로 전송됨**

---

## 4.4 Dockerfile 주요 명령어

### 4.4.1 FROM (필수)

```
FROM ubuntu:22.04
```

* 베이스 이미지 지정

* Dockerfile 첫 줄 필수

---

### 4.4.2 RUN

```
RUN apt update && apt install -y nginx
```

* 빌드 시 실행

* 결과가 이미지 레이어로 저장됨

👉 여러 RUN을 하나로 묶는 이유

→ 레이어 수 감소, 이미지 최적화

---

### 4.4.3 COPY / ADD

```
COPY index.html /usr/share/nginx/html/
```

* 호스트 파일을 이미지로 복사

* **COPY 권장**

* ADD는 압축 해제, URL 다운로드 등 부가기능 포함

---

### 4.4.4 WORKDIR

```
WORKDIR /app
```

* 작업 디렉터리 지정

* cd 대체

---

### 4.4.5 ENV / ARG

```
ARG VERSION
ENV APP_ENV=production
```

| 구분 | ARG | ENV |
| --- | --- | --- |
| 사용 시점 | 빌드 타임 | 런타임 |
| 컨테이너 유지 | ❌ | ⭕ |

---

### 4.4.6 EXPOSE

```
EXPOSE 80
```

* 문서화 용도

* 실제 포트 오픈은 `docker run -p`

---

### 4.4.7 CMD vs ENTRYPOINT

```
CMD ["nginx", "-g", "daemon off;"]
```

* CMD: 기본 실행 명령 (덮어쓰기 가능)

* ENTRYPOINT: 고정 실행 명령

👉 실무에서는 CMD 단독 사용이 가장 흔함

---

## 4.5 Dockerfile에서 레이어를 생성하지 않는 명령들

> **Dockerfile의 모든 명령이 이미지 레이어를 만드는 것은 아니다.**
>
> 일부 명령은 **메타데이터만 변경**하며, 파일시스템 레이어를 생성하지 않는다.

---

### 4.5.1 레이어를 생성하는 명령 (파일시스템 변경)

이 명령들은 **이미지 레이어가 하나씩 추가**된다.

* `FROM`

* `RUN`

* `COPY`

* `ADD`

👉 파일시스템에 **실제 변경**이 발생

👉 `docker history`에서 용량 변화 확인 가능

---

### 4.5.2 레이어를 생성하지 않는 명령 (메타데이터만 변경)

아래 명령들은 **새 레이어를 만들지 않는다.**

* `CMD`

* `ENTRYPOINT`

* `ENV`

* `ARG`

* `WORKDIR`

* `EXPOSE`

* `LABEL`

* `USER`

* `STOPSIGNAL`

* `ONBUILD`

* `SHELL`

👉 이미지의 **동작 방식 / 속성**만 정의

👉 파일시스템 자체는 변경하지 않음

### 이유 1) 파일시스템을 건드리지 않기 때문

레이어는 기본적으로 **파일시스템 스냅샷**이다.

* `RUN` → 파일 생성/수정 ❌⭕ → 레이어 필요

* `CMD` → “어떻게 실행할지” 정보만 기록 → 레이어 불필요

---

### 이유 2) 메타데이터는 설정 정보이기 때문

예를 들어:

```
CMD ["nginx", "-g", "daemon off;"]
```

이 줄은:

* 파일을 만들지도

* 파일을 수정하지도 않음

👉 단지

> “컨테이너가 시작될 때 이 명령을 실행해라”
>
> 라는 **설정 정보(metadata)** 만 기록

---

### 4.5.3 ENV는 레이어를 만들까?

```
ENV APP_ENV=production
```

❌ 파일시스템 레이어는 생성되지 않음

⭕ 이미지 메타데이터에 환경 변수만 기록

👉 하지만 **캐시에는 영향**을 줌

(ENV 값이 바뀌면 이후 RUN 캐시는 무효화)

---

### 4.5.4 WORKDIR는 레이어를 만들까?

```
WORKDIR /app
```

* 디렉터리가 **없으면 생성**됨

* 하지만 Docker는 이를 **메타데이터 변경으로 처리**

* 용량 증가 없음

---

### 4.5.5 CMD / ENTRYPOINT는 왜 레이어가 없을까?

```
CMD ["python", "app.py"]
```

* 실행 시점에만 사용

* 이미지 파일시스템과 무관

👉 그래서 **docker history에 용량 0B로 표시**

---

### 4.5.6 docker history로 확인

```
docker history myimage:1.0
```

출력 예:

```
IMAGE          CREATED BY                       SIZE
<id>           CMD ["nginx"]                    0B
<id>           EXPOSE 80                        0B
<id>           RUN apt install nginx            50MB
```

👉 **0B로 표시되는 항목 = 레이어 없는 명령**

## 4.6 .dockerignore

### 4.6.1 왜 필요한가?

* build context 전송 최적화

* 이미지 용량 감소

* 민감 정보 유출 방지

### 예시

```
.git
node_modules
.env
```

---

## 4.6 이미지 빌드 실습

### 디렉터리 구조

```
webapp/
 ├ Dockerfile
 └ index.html
```

### Dockerfile

```
FROM nginx:latest
COPY index.html /usr/share/nginx/html/index.html
```

### 빌드 및 실행

```
docker build -t myweb:1.0 .
docker run -d -p 8080:80 myweb:1.0
```

---

## 4.7 이미지 캐시(Cache) 동작

* Dockerfile 각 줄 단위로 캐시 판단

* 변경된 줄 이후는 전부 재빌드

```
docker build --no-cache -t myweb:1.0 .
```

---

## 4.8 Dangling Image

### 4.8.1 정의

**태그가 없는 이미지(**`<none>:<none>`**)**

* 이미지 자체는 정상

* 참조(tag)만 사라진 상태

---

### 4.8.2 발생 원인

* 같은 태그로 이미지 재빌드 시

* 기존 이미지는 dangling 상태가 됨

---

### 4.8.3 확인 및 삭제

```
docker images -f dangling=true
docker image prune
```

---

## 4.9 Image Digest (이미지의 실제 식별자)

### 4.9.1 Digest란?

* 이미지 내용을 기준으로 계산된 **SHA256 해시**

* 이미지의 **진짜 신원**

```
sha256:abcd1234...
```

---

### 4.9.2 Tag vs Digest

| 구분 | Tag | Digest |
| --- | --- | --- |
| 변경 가능 | ⭕ | ❌ |
| 의미 | 별명 | 고유 지문 |
| 신뢰성 | 낮음 | 높음 |

👉 Docker는 내부적으로 **digest 기준으로 이미지 관리**

---

### 4.9.3 Digest 확인

```
docker images --digests
docker inspect nginx
```

---

### 4.9.4 Dangling과의 관계

* dangling image도 **digest는 유지**

* 태그만 없는 상태

---

### 4.10 좋은 Docker 이미지의 기준

* 작다

* 재현 가능하다

* 불필요한 파일이 없다

* 태그와 digest 개념이 명확하다

* 빌드 캐시를 효율적으로 사용한다

---

- [[Docker 이미지 생성하기 실습]]