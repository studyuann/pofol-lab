---
title: "Redis 데이터모델"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "데이터베이스", "Redis 실습"]
is_public: true
draft: false
---

# Redis 데이터모델

## 1. Redis에서 Key / Value 구조

👉 Redis는 `:`를 **아무 의미 없는 문자**로 취급합니다.

👉 **계층 구조나 하위 키 개념은 없음**

---

## 2. 왜 `cache:product:100` 같은 키를 쓰는가?

이건 **Redis의 네임스페이싱 관례**입니다.

```
[용도] : [도메인] : [식별자]
```

예시:

```
session:SID123
cache:product:100
cart:user:1001
view:product:100
```

📌 목적

* 키 충돌 방지

* 관리/가독성 향상

* SCAN/MATCH로 그룹 조회 가능

```
SCAN 0 MATCH cache:product:*
```

---

* Redis에는 **테이블 개념이 없음.**

---

* 아래 두 키는 **완전히 다른 키임**.

```
cache:product:100
product:100
```

---

**전체 키 문자열**만 삭제 가능함.

```
DEL cache:product:100   # ⭕
DEL product:100         # ❌ (다른 키)
```

---