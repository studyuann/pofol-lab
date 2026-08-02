---
title: "Compose Override"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Docker"]
is_public: true
draft: false
---

# Compose Override

* `compose.yml` : 공통(베이스)

* `compose.dev.yml` : 개발 환경 덮어쓰기

* `compose.prod.yml` : 운영 환경 덮어쓰기

Compose는 **뒤에 오는 파일이 앞 파일을 덮어씀**.

### 예시: compose.yml (공통)

```
services:
  app:
    image: myid/myapp:base
    ports:
      -"8080:8080"
    environment:
      APP_MODE:"base"
    depends_on:
      - redis

  redis:
    image: redis:7
```

### 예시: compose.dev.yml (개발 오버라이드)

```
services:
  app:
    image: myid/myapp:dev
    environment:
      APP_MODE:"dev"
      DEBUG:"true"
    volumes:
      - ./src:/app/src
```

### 예시: compose.prod.yml (운영 오버라이드)

```
services:
  app:
    image: myid/myapp:1.1.0
    environment:
      APP_MODE:"prod"
      DEBUG:"false"
    ports: []# 운영은 보통 외부 포트 직접 노출 안 함(프록시/LB 사용)
    restart: always
```

### 실행

개발:

```
docker compose-f compose.yml-f compose.dev.yml up-d
```

운영:

```
docker compose-f compose.yml-f compose.prod.yml up-d
```