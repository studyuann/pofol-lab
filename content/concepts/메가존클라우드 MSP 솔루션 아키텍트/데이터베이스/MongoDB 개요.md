---
title: "MongoDB 개요"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "데이터베이스"]
is_public: true
draft: false
---

# MongoDB 개요

[![](https://media.licdn.com/dms/image/v2/D5612AQEx619XKsDxvw/article-cover_image-shrink_600_2000/article-cover_image-shrink_600_2000/0/1685953986947?e=2147483647&t=sDim3pLSr-Er9JU8EForEAJ7P1MW5lW1pYjuYpyyQWU&v=beta)](https://media.licdn.com/dms/image/v2/D5612AQEx619XKsDxvw/article-cover_image-shrink_600_2000/article-cover_image-shrink_600_2000/0/1685953986947?e=2147483647&t=sDim3pLSr-Er9JU8EForEAJ7P1MW5lW1pYjuYpyyQWU&v=beta)

---

## 1. MongoDB란 무엇인가?

* \*MongoDB\*\*는

👉 **문서(Document) 기반 NoSQL 데이터베이스**이다.

### MongoDB의 핵심 한 줄 정의

> JSON 형태의 데이터를 스키마 없이 저장하고, 수평 확장에 최적화된 DB

---

## 2. MongoDB가 등장한 이유 (RDB의 한계)

### 기존 RDBMS의 구조적 한계

| 항목 | RDBMS |
| --- | --- |
| 스키마 | 사전 정의 필수 |
| 변경 | ALTER TABLE 비용 큼 |
| 확장 | 수직 확장 중심 |
| 데이터 형태 | 정형 데이터 위주 |

### 현대 서비스의 데이터 특성

* 사용자 행동 로그

* 이벤트 데이터

* AI 학습용 데이터

* JSON 기반 API 응답

👉 **테이블 구조로 고정하기 어려움**

---

## 3. MongoDB 데이터 모델

### 3-1. 기본 구성 단위

```
Database
 └── Collection
      └── Document (JSON)
```

### RDBMS와 비교

| RDBMS | MongoDB |
| --- | --- |
| Database | Database |
| Table | Collection |
| Row | Document |
| Column | Field |

---

## 4. Document 구조 (BSON)

MongoDB는 내부적으로 **BSON(Binary JSON)** 사용

```
{
  "_id": ObjectId("65b1f9a1a9c8e0a1a1111111"),
  "name": "Kim",
  "age": 30,
  "skills": ["linux", "docker", "kubernetes"],
  "created_at": ISODate("2026-01-01T10:00:00Z")
}
```

### 특징

* 중첩 가능 (Embedded Document)

* 배열(Array) 지원

* 각 Document마다 구조 달라도 됨

---

## 5. MongoDB가 스키마가 없다는 의미

❌ **아무 규칙도 없다** → 아님

⭕ **DB가 강제하지 않는다**

```
{ "name": "Lee", "age": 25 }
{ "name": "Park", "email": "park@test.com" }
```

👉 애플리케이션 또는 설계자가 책임

---

## 6. MongoDB 사용 시나리오

### MongoDB가 적합한 경우

* 로그 저장

* 이벤트 수집

* 사용자 프로필

* AI 학습 데이터

* 마이크로서비스 간 데이터 교환

### 부적합한 경우

* 복잡한 JOIN 필수

* 금융 트랜잭션

* 강한 정합성 요구

---