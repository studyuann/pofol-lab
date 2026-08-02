---
title: "DynamoDB 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "데이터베이스"]
is_public: true
draft: false
---

# DynamoDB 실습

---

## 실습 개요

* 목표:
  + DynamoDB 기본 개념 이해
  + 테이블/아이템/키 구조 체험
  + Query vs Scan 차이 이해
  + GSI 활용 경험

---

## 실습 0. 사전 준비

### 준비 사항

* AWS 계정

* Region: **ap-northeast-2 (서울)** 권장

* IAM 사용자 (DynamoDB Full Access)

---

## 실습 1. DynamoDB 테이블 생성

### 1) 목표

* DynamoDB 테이블 구조 이해

* Partition Key / Sort Key 개념 습득

### 2) 시나리오

> 사용자 주문 정보를 저장하는 테이블 생성

---

### 3) 테이블 설계

| 항목 | 값 |
| --- | --- |
| 테이블 이름 | `Orders` |
| Partition Key | `userId` (String) |
| Sort Key | `orderId` (String) |
| Billing Mode | On-Demand |

---

### 4) 실습 단계

1. AWS Console → DynamoDB → **Tables**

2. **Create table**

3. 설정
   * Table name: `Orders`
   * Partition key: `userId` (String)
   * Sort key: `orderId` (String)

4. Billing mode: **On-Demand**

5. Create table

---

### >> 확인 포인트

* 테이블 상태가 **Active**

* Primary key 구조 확인

---

## 실습 2. 아이템(Item) 추가

### 1) 목표

* Item과 Attribute 구조 이해

---

### 2) 실습 단계

1. `Orders` 테이블 클릭

2. **Explore table items**

3. **Create item**

4. JSON View 선택 후 입력

```
{
  "userId": "user-001",
  "orderId": "order-001",
  "product": "Keyboard",
  "price": 50000,
  "orderDate": "2026-01-01",
  "status": "PAID"
}
```

5. **Create item**

---

### ➕ 추가 아이템

```
{
  "userId": "user-001",
  "orderId": "order-002",
  "product": "Mouse",
  "price": 30000,
  "orderDate": "2026-01-02",
  "status": "SHIPPED"
}
```

```
{
  "userId": "user-002",
  "orderId": "order-001",
  "product": "Monitor",
  "price": 250000,
  "orderDate": "2026-01-03",
  "status": "PAID"
}
```

---

### >> 확인 포인트

* 같은 `userId` 내에서 `orderId` 기준 정렬

* 서로 다른 `userId`는 다른 파티션

---

## 실습 3. GetItem vs Query

### - 목표

* 단건 조회와 조건 조회 차이 이해

---

### 1) GetItem (기본 키 전체 필요)

1. **Explore table items**

2. Partition key: `user-001`

3. Sort key: `order-001`

4. Get item

📌 특징

* 빠름

* 정확한 키 값 필요

---

### 2) Query (Partition Key 기준)

1. **Query** 탭 선택

2. Partition key = `user-001`

3. 실행

📌 특징

* 동일 사용자 주문 전체 조회

* 실무에서 가장 많이 사용

---

### >> 확인 포인트

* Query는 **Partition Key 필수**

* Scan보다 훨씬 빠름

---

## 실습 4. Scan 사용해보기 (비권장)

### 1) 목표

* Scan의 문제점 체감

---

### 2) 실습 단계

1. **Scan** 탭 선택

2. 실행

---

### >> 확인 포인트

* 모든 아이템을 읽음

* 데이터 많을수록 비용 & 속도 문제

📌 **결론**

> Scan은 테스트용, 운영 환경에서는 지양

---

## 실습 5. GSI (Global Secondary Index) 생성

### 1) 목표

* 기본 키 외 조회 패턴 해결

---

### 2) 요구사항

> 주문 상태(status)로 주문 조회

---

### 3) GSI 생성

1. `Orders` 테이블 → **Indexes**

2. **Create index**

3. 설정
   * Index name: `status-index`
   * Partition key: `status` (String)
   * Sort key: `orderDate` (String)
   * Projection: All

---

### >> 확인 포인트

* GSI 생성 완료 상태

* 별도 용량 관리 없음 (On-Demand)

---

## 실습 6. GSI Query

### 1) 목표

* GSI 기반 조회 수행

---

### 2) 실습 단계

1. **Explore table items**

2. Index 선택: `status-index`

3. Partition key = `PAID`

4. Query 실행

---

### 3) 확인 포인트

* `PAID` 상태 주문만 조회

* 기본 테이블 키 없이도 조회 가능

---

## 실습 7. UpdateItem

### 1) 목표

* 특정 속성만 수정

---

### 2) 실습 단계

1. `user-001` / `order-001` 선택

2. **Edit**

3. `status` → `DELIVERED`

4. Save changes

---

### >> 확인 포인트

* 전체 아이템 덮어쓰지 않음

* 필요한 필드만 수정

---

## 실습 8. TTL(Time To Live)

### 1) 목표

* 자동 데이터 삭제 기능 이해

---

### 2) TTL 설정

1. Table settings → **TTL**

2. Attribute name: `expireAt`

3. Enable TTL

---

### 3) 아이템 수정

```
"expireAt": 1767225600
```

(Unix Timestamp)

---

### >> 확인 포인트

* 지정 시간 이후 자동 삭제

* 로그 / 세션 데이터에 유용

---

## 실습 9. 테이블 삭제 (정리)

1. DynamoDB → Tables

2. `Orders` 선택

3. Delete table

---

## 실습 마무리 정리

### >> 핵심 정리

* DynamoDB는 **키 설계가 성능**

* Query > Scan

* GSI는 조회 패턴 확장 수단

* On-Demand는 실습 & 초기 서비스에 적합

---