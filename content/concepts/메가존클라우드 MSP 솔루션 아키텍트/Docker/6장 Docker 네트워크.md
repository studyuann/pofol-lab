---
title: "6장 Docker 네트워크"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Docker"]
is_public: true
draft: false
---

# 6장. Docker 네트워크

## bridge · host · none · 포트 포워딩 · 컨테이너 간 통신

## 6장 학습 목표

* Docker 컨테이너의 **네트워크 격리 구조**를 이해한다.

* 기본 bridge 네트워크(`docker0`)의 동작 원리를 설명할 수 있다.

* `p` 옵션이 **무엇을 설정하는지** 정확히 설명할 수 있다.

* 사용자 정의 네트워크에서 **컨테이너 간 통신 방식(DNS)** 을 이해한다.

* 운영 환경에서 **어떤 네트워크 방식을 선택해야 하는지** 판단할 수 있다.

---

## 6.1 Docker 네트워크가 필요한 이유

### 6.1.1 컨테이너는 기본적으로 격리된다

컨테이너는 다음 자원을 **namespace**로 격리한다.

* 프로세스(PID)

* 파일시스템(MNT)

* 네트워크(NET)

👉 즉,

> 컨테이너는 실행만 하면
>
> **외부와 자동으로 통신할 수 없다.**

---

### 6.1.2 Docker 네트워크의 역할

Docker 네트워크의 역할은 다음과 같다.

* 컨테이너에 IP 주소 할당

* 컨테이너 ↔ 컨테이너 통신

* 컨테이너 ↔ 호스트 통신

* 외부 ↔ 컨테이너 통신

---

## 6.2 Docker 네트워크 드라이버 개요

### 6.2.1 기본 네트워크 드라이버

| 드라이버 | 설명 | 사용 목적 |
| --- | --- | --- |
| bridge | 가상 브리지 기반 | 기본값, 가장 많이 사용 |
| host | 호스트 네트워크 공유 | 성능 최우선 |
| none | 네트워크 없음 | 완전 격리 |

---

## 6.3 bridge 네트워크 (기본이자 핵심)

[![](https://www.docker.com/app/uploads/2022/12/networking-drivers-use-cases-3.png)](https://www.docker.com/app/uploads/2022/12/networking-drivers-use-cases-3.png)

### 6.3.1 docker0 브리지란?

Docker 설치 시 자동으로 생성되는 **가상 브리지 인터페이스**

```
ip addr show docker0
```

* 리눅스 브리지

* 사설 IP 대역 할당 (보통 172.17.0.0/16)

* 컨테이너는 docker0에 연결됨

---

### 6.3.2 컨테이너 네트워크 연결 구조

컨테이너 하나당 다음이 생성된다.

* veth 인터페이스 2개
  + 한쪽: 컨테이너 내부 `eth0`
  + 다른 쪽: 호스트의 `docker0`에 연결

👉 컨테이너는 **가상 스위치에 연결된 서버**처럼 동작

---

### 6.3.3 컨테이너 IP 확인

```
docker inspect <컨테이너명>
```

또는 컨테이너 내부에서:

```
ip addr
```

---

## 6.4 포트 포워딩 (`p` 옵션)

### 6.4.1 왜 포트 포워딩이 필요한가?

컨테이너는 사설 IP를 사용한다.

* 외부 → 컨테이너 직접 접근 ❌

* **호스트 포트를 통해서만 접근 가능**

---

### 6.4.2 포트 포워딩 기본 형식

```
-p [호스트포트]:[컨테이너포트]
```

예:

```
docker run -d -p 8080:80 nginx
```

의미:

* 호스트 8080 → 컨테이너 80

---

### 6.4.3 실제 내부 동작

* iptables NAT 규칙 자동 생성

* DNAT / SNAT 사용

* 사용자는 iptables를 직접 다루지 않음

---

### 6.4.4 포트 확인

```
docker ps
docker port <컨테이너명>
```

---

## 6.5 사용자 정의 bridge 네트워크 (매우 중요)

### 6.5.1 왜 기본 bridge를 쓰지 않을까?

기본 bridge의 한계:

* 컨테이너 이름 기반 통신 ❌

* IP 직접 사용 필요

👉 **운영에서는 사용자 정의 네트워크 사용이 기본**

---

### 6.5.2 사용자 정의 네트워크 생성

```
docker network create mynet
```

확인:

```
docker network ls
docker network inspect mynet
```

---

### 6.5.3 사용자 정의 네트워크의 장점

* 컨테이너 이름으로 통신 가능

* 내장 DNS 제공

* 네트워크 단위 격리

---

### 6.5.4 컨테이너 간 통신 실습

```
docker run -d --name web \
  --network mynet nginx

docker run -it --name client \
  --network mynet ubuntu bash
```

컨테이너 내부에서:

```
apt update && apt install -y curl
curl http://web
```

👉 **IP 없이 이름으로 통신 성공**

---

## 6.6 host 네트워크

### 6.6.1 host 네트워크란?

```
docker run --network host nginx
```

* 컨테이너가 **호스트 네트워크를 그대로 사용**

* IP 분리 ❌

* 포트 포워딩 ❌

---

### 6.6.2 장단점

| 장점 | 단점 |
| --- | --- |
| 성능 우수 | 포트 충돌 |
| 단순 구조 | 격리 약함 |
| NAT 없음 | 보안 위험 |

👉 **특수 목적(고성능)** 에서만 사용

---

## 6.7 none 네트워크

### 6.7.1 none이란?

```
docker run --network none ubuntu
```

* 네트워크 인터페이스 없음

* 완전 격리

---

### 사용 사례

* 보안 테스트

* 배치 처리

* 네트워크 불필요 작업

---

## 6.8 컨테이너 ↔ 호스트 통신

### 6.8.1 컨테이너에서 호스트 접근

* 기본 bridge에서는 **게이트웨이 IP** 사용

```
ip route
```

보통:

```
172.17.0.1
```

---

### 6.8.2 host.docker.internal

* Docker Desktop (Mac/Windows) 제공

* Linux 서버 환경에서는 기본 제공 ❌

---

## 6.9 네트워크 관리 명령 요약

```
docker network ls
docker network inspect mynet
docker network rm mynet
```

⚠️ 사용 중인 컨테이너가 있으면 삭제 불가

---

## 6.10 운영 환경 네트워크 설계 기준

### 운영 권장 패턴

* 외부 공개 서비스:

  → 사용자 정의 bridge + 포트 포워딩

* 내부 서비스 통신:

  → 사용자 정의 bridge + DNS

* 고성능 특수 목적:

  → host 네트워크

* 완전 격리 작업:

  → none 네트워크

---

- [[Docker Network 실습]]
- [[bridge 네트워크를 이용하여 컨테이너 연결하기|bridge 네트워크를 이용하여 컨테이너 연결하기]]