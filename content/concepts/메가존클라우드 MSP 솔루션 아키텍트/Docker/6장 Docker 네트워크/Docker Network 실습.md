---
title: "Docker Network 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Docker", "6장 Docker 네트워크"]
is_public: true
draft: false
---

# Docker Network 실습

---

## 실습 개요

### 실습 목표

이 실습을 통해 다음을 직접 확인한다.

* Docker 기본 bridge 네트워크의 동작 방식

* 컨테이너 IP 기반 통신의 한계

* User-defined bridge 네트워크의 필요성

* 컨테이너 이름(DNS) 기반 통신

* 포트 퍼블리시(`p`)가 동작하는 위치

* 네트워크 모드에 따른 통신 차이

---

## 실습 환경

* OS: Ubuntu (Docker 설치 완료)

* 이미지:
  + `nginx:alpine`
  + `curlimages/curl`

---

## 실습 1. 기본 bridge 네트워크 확인

### 1-1. Docker 네트워크 목록 확인

```
docker network ls
```

### 확인 포인트

* 기본적으로 다음 네트워크가 존재함
  + `bridge`
  + `host`
  + `none`

---

### 1-2. 기본 bridge 네트워크 상세 확인

```
docker network inspect bridge
```

### 확인 포인트

* Subnet (예: `172.17.0.0/16`)

* Gateway

* `Containers` 항목

---

## 실습 2. 기본 bridge 네트워크에서 컨테이너 실행

### 2-1. 컨테이너 2개 실행

```
docker run -d --name web1 nginx:alpine
docker run -d --name web2 nginx:alpine
```

> 네트워크를 지정하지 않았으므로
>
> 두 컨테이너는 자동으로 **기본 bridge 네트워크**에 연결된다.

---

### 2-2. 컨테이너 IP 확인

```
docker inspect -f '{{ .NetworkSettings.IPAddress }}' web1
docker inspect -f '{{ .NetworkSettings.IPAddress }}' web2
```

예시:

```
web1 → 172.17.0.2
web2 → 172.17.0.3
```

---

## 실습 3. 기본 bridge에서 컨테이너 간 통신

### 3-1. web1에서 web2로 IP 기반 접근

```
docker exec -it web1 sh
```

```
apk add --no-cache curl
curl http://172.17.0.3
```

### 기대 결과

* nginx 기본 페이지 HTML 출력

* IP 기반 통신은 가능

---

### 3-2. 컨테이너 이름으로 접근 시도

```
curl http://web2
```

### 기대 결과

```
curl: (6) Could not resolve host: web2
```

### 정리

* 기본 bridge 네트워크는 **컨테이너 이름 DNS를 제공하지 않음**

* IP 기반 통신만 가능 → 운영 환경에 부적합

---

## 실습 4. User-defined bridge 네트워크 생성

### 4-1. 사용자 정의 네트워크 생성

```
docker network create mynet
```

```
docker network ls
```

---

### 4-2. 새 네트워크에 컨테이너 실행

```
docker run -d --name app1 --network mynet nginx:alpine
docker run -d --name app2 --network mynet nginx:alpine
```

---

## 실습 5. User-defined bridge 네트워크 통신

### 5-1. IP 확인

```
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' app1
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' app2
```

---

### 5-2. 컨테이너 이름 기반 통신 (DNS)

```
docker exec -it app1 sh
```

```
apk add --no-cache curl
curl http://app2
```

### 기대 결과

* nginx HTML 정상 출력

### 핵심 포인트

* User-defined bridge는 **자동 DNS 제공**

* 컨테이너 이름으로 통신 가능

* IP 변경에도 영향 없음

---

## 실습 6. 포트 퍼블리시(`p`) 이해하기

### 6-1. 컨테이너 실행 + 포트 퍼블리시

```
docker run -d --name web-pub -p 8080:80 nginx:alpine
```

---

### 6-2. 호스트에서 접근

```
curl http://127.0.0.1:8080
```

### 확인 포인트

* 포트 퍼블리시는 **호스트 ↔ 컨테이너** 통신

* 컨테이너 ↔ 컨테이너 통신과는 무관

---

## 실습 7. 컨테이너 내부 OK / 외부 접속 실패 디버깅

### 7-1. 컨테이너 내부에서 서비스 확인

```
docker exec -it web-pub sh
apk add --no-cache curl
curl http://127.0.0.1
```

---

### 7-2. 호스트에서 포트 확인

```
docker port web-pub
```

출력 예:

```
80/tcp -> 0.0.0.0:8080
```

---

### 정리

* 내부 OK + 외부 실패 →
  + 포트 퍼블리시
  + 호스트 방화벽
  + Docker 네트워크 상태
  + OS 네트워크 문제

---

## 실습 8. 네트워크 모드 비교

### 8-1. none 네트워크

```
docker run -d --name nonet --network none nginx:alpine
```

```
docker inspect -f '{{.NetworkSettings.IPAddress}}' nonet
```

### 결과

* IP 없음

* 외부/내부 통신 불가

---

### 8-2. host 네트워크 (Linux 전용)

```
docker run -d --name hostnet --network host nginx:alpine
```

```
curl http://127.0.0.1
```

### 결과

* 포트 퍼블리시 필요 없음

* 호스트 포트 직접 사용

* 격리 약화 → 운영에서는 주의

---

## 실습 정리

### 핵심 요약

* 기본 bridge:
  + IP 통신 가능
  + 이름 기반 통신 불가

* User-defined bridge:
  + 컨테이너 이름 DNS 제공
  + 운영 환경 권장

* `p`:
  + 호스트 ↔ 컨테이너 통신
  + 컨테이너 간 통신과 무관

* 내부 OK / 외부 실패:
  + 앱 문제 아님
  + 네트워크/호스트 OS 문제 가능성 큼

---

## 실습 종료 – 리소스 정리

```
docker rm -f web1 web2 app1 app2 web-pub nonet hostnet
docker network rm mynet
```

---