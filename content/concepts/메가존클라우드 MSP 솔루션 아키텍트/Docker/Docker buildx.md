---
title: "Docker buildx"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Docker"]
is_public: true
draft: false
---

# Docker buildx

## 1. buildx가 필요한 이유

### 1.1 기존 `docker build`의 한계

* 기본 `docker build`는 “현재 머신 아키텍처” 기준으로 이미지를 빌드함
  + 예: M1/M2(Mac arm64)에서 빌드한 이미지를 x86 서버(amd64)에서 실행 시 `exec format error` 발생할 수 있음

* 멀티 아키텍처 이미지를 만들려면 “이미지 2개를 따로 빌드해서 관리”해야 해서 운영이 번거로움

### 1.2 buildx가 해결하는 것

* **멀티 아키텍처 이미지**를 한 번에 생성 가능 (amd64 + arm64)

* **BuildKit 기반**으로 빌드 성능/캐시/병렬 처리 개선

* CI/CD에서 표준적으로 사용하는 빌드 방식

---

## 2. 핵심 개념 정리

### 2.1 BuildKit

* 도커 빌드 엔진의 차세대 구현체임

* 장점: 캐시 활용 최적화, 병렬 빌드, 출력 유형 다양(로컬 로드/레지스트리 푸시 등)

### 2.2 buildx

* BuildKit을 CLI에서 쉽게 쓰도록 만든 도커 플러그인임

* `docker buildx build` 명령으로 BuildKit 기능을 사용함

### 2.3 멀티 아키텍처 이미지(Manifest List)

* 하나의 태그(`myapp:1.0`) 아래에
  + amd64 이미지
  + arm64 이미지

    를 함께 묶어둔 “목록(Manifest List)”을 생성함

* 클라이언트가 `docker pull myapp:1.0` 하면 **자기 CPU에 맞는 이미지가 자동 선택됨**

---

## 3. 사전 점검

### 3.1 버전 및 기능 확인

```
docker version
docker buildx version
```

* `docker buildx version`이 동작하면 buildx 사용 가능 상태임

### 3.2 현재 빌더 목록 확인

```
docker buildx ls
```

* 여기서 표시가 붙은 빌더가 현재 사용 중인 빌더임

---

## 4. 실습 1: buildx 빌더 생성 및 전환

### 4.1 빌더 생성

```
docker buildx create --name bootcamp-builder --use
```

* `create`: 새로운 buildx 빌더 인스턴스를 생성함

* `-name`: 빌더 이름 지정함

* `-use`: 생성 직후 해당 빌더를 기본 빌더로 전환함

### 4.2 빌더 상태 확인

```
docker buildx inspect --bootstrap
```

* `inspect`: 빌더 설정/드라이버/플랫폼 지원 정보를 출력함

* `-bootstrap`: 빌더 백엔드(BuildKit)를 실제로 기동함(초기화 수행함)

---

## 5. 실습 2: 단일 플랫폼 빌드 (기본 감 잡기)

### 5.1 예제 프로젝트 준비

아래 구조를 사용한다고 가정함.

```
app/
 ├─ Dockerfile
 └─ server.py
```

### server.py

```
from flask import Flask
import platform

app = Flask(__name__)

@app.get("/")
def home():
    return f"hello buildx! arch={platform.machine()}\n"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```

### Dockerfile

```
FROM python:3.12-slim
WORKDIR /app
RUN pip install flask
COPY server.py .
EXPOSE 8080
CMD ["python", "server.py"]
```

### 5.2 빌드 결과를 로컬에 로드해서 실행

```
docker buildx build -t myflask:local --load .
```

* `t`: 이미지 태그 지정함

* `-load`: 빌드 결과를 **로컬 도커 엔진 이미지 저장소**로 로드함
  + `docker images`에서 보이게 됨
  + 단점: 멀티 아키 빌드 결과는 `--load`로 바로 로드하지 못함(대신 `--push` 사용함)

### 5.3 실행 확인

```
docker run --rm -p 8080:8080 myflask:local
```

---

## 6. 실습 3: 멀티 아키텍처 빌드 + 레지스트리 푸시

### 6.1 왜 `--push`가 필요한가

* 멀티 아키 이미지는 “Manifest List”까지 생성해야 하므로 로컬 로드보다 **레지스트리 푸시가 자연스러운 결과물**임

* 즉, 멀티 아키는 보통 `--push`를 사용함

### 6.2 Docker Hub 로그인

```
docker login
```

### 6.3 멀티 아키 빌드 및 푸시

```
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t <도커허브ID>/myflask:1.0 \
  --push .
```

* `--platform`: 빌드 대상 플랫폼을 지정함

* `--push`: 결과를 레지스트리에 푸시함(Manifest List 포함)

### 6.4 결과 검증

```
docker buildx imagetools inspect <도커허브ID>/myflask:1.0
```

* amd64/arm64 digest가 함께 보이면 멀티 아키 구성 완료됐음

---

## 7. 실습 4: QEMU 기반 크로스 빌드 이해

### 7.1 크로스 빌드가 가능한 이유

* x86 머신에서 arm64를 빌드할 때 실제로는 **QEMU 에뮬레이션**이 동작함

* 빌더가 지원 플랫폼 목록을 가지고, 해당 플랫폼용으로 빌드 파이프라인을 수행함

### 7.2 플랫폼 지원 여부 확인

```
docker buildx inspect --bootstrap
```

* 출력에 `Platforms:` 항목이 있으며, `linux/amd64`, `linux/arm64`가 포함되면 준비됐음

---

## 8. 실습 5: 캐시 적용

### 8.1 캐시가 중요한 이유

* 매 빌드마다 `pip install`, `npm install` 같은 단계가 반복되면 빌드 시간이 폭증함

* buildx는 캐시를 레지스트리에 저장/재사용 가능함
  + CI 환경(빌드 머신이 매번 바뀌는 환경)에서 특히 중요함

### 8.2 레지스트리 캐시 사용 예시

```
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t <도커허브ID>/myflask:1.1 \
  --cache-to type=registry,ref=<도커허브ID>/myflask:buildcache,mode=max \
  --cache-from type=registry,ref=<도커허브ID>/myflask:buildcache \
  --push .
```

* `--cache-to`: 캐시를 어디에 저장할지 지정함
  + `type=registry`: 레지스트리에 캐시 레이어 저장함
  + `mode=max`: 가능한 많은 캐시를 저장함

* `--cache-from`: 저장된 캐시를 가져와서 재사용함

---

## 9. 쿠버네티스로 이어지는 포인트

### 9.1 쿠버네티스는 “이미지 pull”만 한다

* 쿠버네티스 노드는 이미지를 “빌드”하지 않음

* 따라서 실무에서는
  + 빌드(=buildx)
  + 푸시(=registry)
  + 배포(=k8s)

    흐름이 표준임

### 9.2 멀티 아키가 왜 중요하나

* 노드가 amd64/arm64 혼재 가능함(클라우드/엣지/개발환경 포함)

* 동일 태그로 배포했는데 노드에 따라 실행 실패하면 운영이 깨짐

* buildx 멀티 아키는 이 문제를 구조적으로 제거함

---

## 10. 트러블슈팅 체크리스트

### 10.1 `--load` 했는데 이미지가 안 보임

* 멀티 아키 빌드인 경우 `--load`가 제약 있음

* 해결: 멀티 아키는 `--push` 사용했음

### 10.2 `docker buildx build`가 느림

* QEMU 에뮬레이션이 들어가면 느려질 수 있음

* 캐시(`--cache-from/--cache-to`) 적용했음

* 가능한 경우, 각 아키텍처 네이티브 빌드 러너(CI에서 amd64 runner, arm64 runner) 분리했음

### 10.3 `docker buildx imagetools inspect`가 안 됨

* 구버전 도커/플러그인 이슈일 수 있음

* `docker buildx version` 확인했음

---

```
docker buildx create --driver docker-container --name multi-builder --platform linux/amd64,linux/arm64

docker buildx use --default multi-builder

docker buildx ls
```