---
title: "Redis 개요"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "데이터베이스"]
is_public: true
draft: false
---

# Redis 개요

---

## 1. Redis란 무엇인가?

### 정의

> Redis는 메모리 기반의 Key-Value 데이터 저장소(In-Memory Data Store) 이다.

* 디스크가 아닌 **RAM**에 데이터를 저장

* 매우 빠른 읽기/쓰기 성능

* 단순 KV 저장소가 아니라 **여러 자료구조를 제공**

---

> Redis는 “빠른 판단을 위해 잠깐 데이터를 기억하는 서버”다.

---

## 2. Redis가 등장한 이유

### 전통적인 웹 서비스 구조

```
Client → Web Server → Database
```

### 문제점

* 모든 요청이 DB로 집중

* 로그인, 세션 확인, 조회수 증가 같은 **단순 작업도 DB 처리**

* 트래픽 증가 시 DB 병목 발생

---

### Redis가 추가된 구조

[![](https://substackcdn.com/image/fetch/%24s_%21OsiQ%21%2Cf_auto%2Cq_auto%3Agood%2Cfl_progressive%3Asteep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F778a7e21-455b-45f6-8487-63f9eb41e88b_2000x1414.jpeg)](https://substackcdn.com/image/fetch/%24s_%21OsiQ%21%2Cf_auto%2Cq_auto%3Agood%2Cfl_progressive%3Asteep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F778a7e21-455b-45f6-8487-63f9eb41e88b_2000x1414.jpeg)

```
Client → Web Server → Redis → Database
```

* **Redis가 DB 앞단에서 요청을 흡수**

* DB는 “진짜 중요한 데이터”만 처리

---

## 3. Redis의 핵심 특징

### 1️⃣ In-Memory (메모리 기반)

* 디스크 I/O 없음

* 매우 빠른 응답 속도 (μs ~ ms)

### 2️⃣ Key-Value 구조

```
key → value
```

```
session:SID123 → user_id=1001
```

---

### 3️⃣ 다양한 자료구조 지원

| 자료구조 | 용도 예시 |
| --- | --- |
| STRING | 세션, 캐시 |
| LIST | 큐, 작업 대기열 |
| SET | 중복 제거, 이벤트 참여 |
| HASH | 객체(장바구니, 프로필) |
| ZSET | 랭킹, 점수 |

👉 단순 캐시보다 **활용 범위가 훨씬 넓음**

---

## 4. Redis는 “DB인가?”

### ❌ 아니다 (중요)

| 항목 | Redis | RDB |
| --- | --- | --- |
| 저장 위치 | 메모리 | 디스크 |
| 기본 데이터 | 없음 | 있음 |
| 스키마 | 없음 | 있음 |
| 영구성 | 선택적 | 기본 |
| 목적 | 속도 | 정확성 |

---

### 정확한 표현

> Redis는 “Primary Database”가 아니라“보조 데이터 저장소(Secondary Data Store)”다.

---

## 5. Redis에 저장되는 데이터의 성격

### Redis에 적합한 데이터

* 다시 만들 수 있는 데이터

* 잠깐만 필요한 데이터

* 빠른 판단용 데이터

### 예시

* 로그인 세션

* 상품 캐시

* 장바구니

* 조회수

* 인기 랭킹

* 이벤트 참여 여부

---

### Redis에 ❌ 부적합한 데이터

* 원본 사용자 정보

* 결제 정보

* 로그 데이터

* 반드시 영구 보존해야 하는 데이터

---

## 6. Redis 기본 동작 흐름 (로그인 예시)

[![](https://miro.medium.com/1%2AbHjur1DT0beob4xvxSZ6-w.png)](https://miro.medium.com/1%2AbHjur1DT0beob4xvxSZ6-w.png)

### 로그인 최초 요청

1. 사용자 로그인 요청

2. DB에서 인증

3. 성공 시 세션 생성

4. Redis에 세션 저장

```
session:SID123 → user_id=1001 (TTL 30분)
```

---

### 이후 요청

1. 요청 + 세션 ID

2. Redis에서 세션 조회

3. 있으면 인증 OK

4. DB 접근 ❌

👉 **대부분의 요청은 Redis에서 끝남**

---

## 7. TTL (Time To Live) – Redis의 핵심 기능

### TTL이란?

* 데이터에 **유효 시간**을 설정

* 시간이 지나면 **자동 삭제**

```
로그인 세션 → 30분
OTP → 3분
캐시 → 1분
```

👉 **자동 로그아웃 / 자동 캐시 만료**

---

## 8. Redis 영속화

> Redis는 메모리 기반이지만
>
> **장애 복구를 위해 디스크 저장 기능도 제공**

### 2가지 방식

* **RDB**: 스냅샷 (사진)

* **AOF**: 명령 로그 (영상)

👉 목적은 **DB 대체가 아니라 서비스 복구**

---

## 9. Redis를 쓰면 얻는 효과

### 성능 측면

* 응답 속도 대폭 향상

* DB 부하 감소

* 트래픽 급증에도 안정적

### 아키텍처 측면

* 확장성 향상

* Stateless 서버 구성 가능

* 클라우드 환경에 최적

---

## 10. Redis는 어디에 쓰이는가?

| 분야 | 사용 목적 |
| --- | --- |
| 웹 서비스 | 세션, 캐시 |
| 이커머스 | 장바구니, 랭킹 |
| 게임 | 실시간 점수 |
| API 서버 | Rate Limit |
| 마이크로서비스 | 공용 상태 저장 |

---

## 11. Redis를 도입하면 생기는 변화

### Redis 도입 전

* DB 중심

* 병목 발생

* 확장 어려움

### Redis 도입 후

* Redis가 완충 역할

* DB 안정

* 대규모 트래픽 처리 가능

---

> Redis는 “데이터를 저장하기 위한 서버”가 아니라“서비스를 빠르게 만들기 위한 서버”다.

---