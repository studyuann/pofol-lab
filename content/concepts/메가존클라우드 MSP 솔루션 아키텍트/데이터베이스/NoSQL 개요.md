---
title: "NoSQL 개요"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "데이터베이스"]
is_public: true
draft: false
---

# NoSQL 개요

## 1. NoSQL이란?

**NoSQL(Not Only SQL)** 은

✔ 고정된 스키마를 강제하지 않고

✔ 대용량 데이터를 **분산 환경에서 수평 확장(scale-out)** 하기 위해 설계된 데이터베이스 계열이다.

> ❗ 핵심 포인트
>
> * “SQL을 안 쓴다” ❌
>
> * “**관계형 모델이 아닌 저장 구조를 사용한다**” ⭕

---

## 2. 왜 NoSQL이 등장했는가? (RDB 한계)

### RDB의 강점

* 정합성(ACID)

* 조인 기반의 정규화된 데이터 모델

* 트랜잭션 처리

### RDB의 구조적 한계

| 문제 | 설명 |
| --- | --- |
| 수평 확장 | 서버 추가가 어려움 (Scale-up 중심) |
| 스키마 변경 | 운영 중 ALTER 부담 큼 |
| 대용량 로그/이벤트 | 조인 구조에 부적합 |
| 글로벌 서비스 | 단일 DB 병목 발생 |

➡ **대규모 웹 서비스 / 클라우드 환경**에서 새로운 대안 필요

---

## 3. NoSQL의 핵심 특징

| 구분 | 설명 |
| --- | --- |
| Schema-less | 미리 테이블 구조를 고정하지 않음 |
| Scale-out | 서버 추가로 성능/용량 확장 |
| 분산 저장 | 데이터가 여러 노드에 분산 |
| 고가용성 | 복제(replica) 기반 장애 대응 |
| 유연한 데이터 | JSON, Key-Value 등 |

---

## 4. NoSQL 유형 분류

[![](https://images.openai.com/static-rsc-3/qzyiOhOQBtGbDUSPPzxS7ngVB9lQMcZf1rOUUv2Mh83SePw8Q8Z2YpSofmZPE4_tSNNiE1FgeSrFfeNrD2hmS-zvdxdIbSbSuKp-6htWZuI)](https://images.openai.com/static-rsc-3/qzyiOhOQBtGbDUSPPzxS7ngVB9lQMcZf1rOUUv2Mh83SePw8Q8Z2YpSofmZPE4_tSNNiE1FgeSrFfeNrD2hmS-zvdxdIbSbSuKp-6htWZuI)[![](https://hazelcast.com/wp-content/uploads/2024/12/diagram-key-value-store.svg)](https://hazelcast.com/wp-content/uploads/2024/12/diagram-key-value-store.svg)[![](https://www.couchbase.com/blog/wp-content/uploads/2021/05/data-model-sql-to-json.png)](https://www.couchbase.com/blog/wp-content/uploads/2021/05/data-model-sql-to-json.png)

### ① Key-Value Store

* 예: Redis

* 구조: `key → value`

* 용도: 캐시, 세션

### ② Document Store

* 예: **MongoDB**

* 구조: JSON(Document)

* 용도: 웹 서비스, API, 로그

### ③ Wide Column Store

* 예: Cassandra

* 구조: Row + Column Family

* 용도: 대규모 로그/분석

### ④ Graph DB

* 예: Neo4j

* 구조: Node + Edge

* 용도: 추천, 관계 분석

---

## 5. Document DB 구조 이해 (MongoDB 기준)

### RDB vs Document DB 비교

| RDB | MongoDB |
| --- | --- |
| Database | Database |
| Table | Collection |
| Row | Document |
| Column | Field |
| Schema 고정 | Schema 유연 |

### 예시 데이터 구조

```
{
  "name": "Kim",
  "age": 29,
  "skills": ["AWS", "Docker", "Kubernetes"],
  "created_at": "2026-01-01"
}
```

* **컬럼 추가/삭제 자유**

* **조인 대신 문서 중첩(Embedded)**

---