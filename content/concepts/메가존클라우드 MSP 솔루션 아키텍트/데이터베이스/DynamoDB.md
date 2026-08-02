---
title: "DynamoDB"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "데이터베이스"]
is_public: true
draft: false
---

# DynamoDB

---

## 1. DynamoDB란?

### 1.1 정의

* **Amazon DynamoDB**는 AWS에서 제공하는 **완전관리형(NoSQL) Key-Value & Document 데이터베이스**

* 서버 관리 없이 **자동 확장**, **고가용성**, **고성능** 제공

### 1.2 주요 특징

* 서버리스(Serverless)

* 밀리초(ms) 단위의 낮은 지연 시간

* 자동 확장 (Auto Scaling)

* 다중 AZ에 데이터 자동 복제

* 강력한 보안 (IAM, KMS)

---

## 2. DynamoDB 사용 사례

### 2.1 대표적인 활용 예

* 사용자 프로필 저장

* 세션(Session) 관리

* 게임 점수(Leaderboard)

* IoT 데이터 저장

* 실시간 로그 / 이벤트 데이터

### 2.2 DynamoDB가 적합한 경우

* 대량의 트래픽 처리 필요

* 단순한 조회 패턴 (Key 기반)

* 관계형 JOIN이 불필요한 경우

---

## 3. DynamoDB 기본 개념

### 3.1 테이블(Table)

* DynamoDB의 최상위 데이터 구조

* 무제한 데이터 저장 가능

### 3.2 아이템(Item)

* 테이블의 한 행(Row)

* JSON 형태와 유사

### 3.3 속성(Attribute)

* 아이템을 구성하는 컬럼

* 스키마 유연 (Schema-less)

---

## 4. 키(Key) 구조

### 4.1 파티션 키 (Partition Key)

* 데이터를 분산 저장하기 위한 기준 키

* **필수 요소**

* 동일 파티션 키는 같은 논리적 파티션에 저장

### 4.2 정렬 키 (Sort Key)

* 선택 사항

* 파티션 키 내부에서 정렬 기준 제공

### 4.3 기본 키 유형

1. **단일 기본 키**
   * Partition Key만 사용

2. **복합 기본 키**
   * Partition Key + Sort Key

📌 **중요**

> DynamoDB 조회 성능은 기본 키 설계에 의해 결정됨

---

## 5. 데이터 타입

### 5.1 기본 데이터 타입

* String (S)

* Number (N)

* Boolean (BOOL)

* Binary (B)

### 5.2 복합 데이터 타입

* List

* Map

* Set (String Set, Number Set)

---

## 6. 읽기 / 쓰기 처리 방식

### 6.1 프로비저닝 모드

### 1) Provisioned Mode

* 읽기/쓰기 용량(RCU/WCU) 사전 설정

* 트래픽 예측 가능한 경우 적합

### 2) On-Demand Mode

* 요청량에 따라 자동 확장

* 트래픽 예측이 어려운 경우 적합

---

## 7. 읽기 일관성 (Read Consistency)

### 7.1 Eventually Consistent Read

* 기본 설정

* 빠르고 비용 저렴

### 7.2 Strongly Consistent Read

* 최신 데이터 보장

* 비용 증가, 지연 증가 가능

---

## 8. 인덱스(Index)

### 8.1 GSI (Global Secondary Index)

* 다른 Partition Key / Sort Key 사용

* 테이블 전체 데이터 기준

### 8.2 LSI (Local Secondary Index)

* 같은 Partition Key

* 다른 Sort Key

* 테이블 생성 시에만 설정 가능

---

## 9. 주요 API 작업

### 9.1 데이터 조작

* PutItem : 데이터 삽입

* GetItem : 단건 조회

* UpdateItem : 데이터 수정

* DeleteItem : 데이터 삭제

### 9.2 조회

* Query : 키 기반 조회 (권장)

* Scan : 전체 테이블 검색 (비권장)

---

## 10. 성능 최적화 전략

* Scan 대신 Query 사용

* 파티션 키 균등 분산

* 핫 파티션(Hot Partition) 방지

* 적절한 GSI 설계

* TTL(Time To Live) 활용

---

## 11. 보안

* IAM 정책으로 접근 제어

* KMS를 통한 데이터 암호화

* VPC Endpoint 사용 가능

---

## 12. DynamoDB 장단점 정리

### 장점

* 무한 확장성

* 높은 가용성

* 운영 부담 최소화

### 단점

* 복잡한 쿼리 불가

* JOIN 미지원

* 설계 미흡 시 비용 증가

---

## 13. DynamoDB vs RDB

| 항목 | DynamoDB | RDB |
| --- | --- | --- |
| 스키마 | 유연 | 고정 |
| 확장성 | 매우 우수 | 제한적 |
| JOIN | 불가 | 가능 |
| 트랜잭션 | 제한적 | 강력 |

---

## 14. 정리

* DynamoDB는 **설계가 핵심**

* 키 설계 → 성능 → 비용에 직접 영향

* 대규모 트래픽 시스템에 매우 적합

---