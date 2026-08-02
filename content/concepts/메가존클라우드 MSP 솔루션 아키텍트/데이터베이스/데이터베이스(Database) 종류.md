---
title: "데이터베이스(Database) 종류"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "데이터베이스"]
is_public: true
draft: false
---

# 데이터베이스(Database) 종류

## 1. 데이터베이스 분류 개요

데이터베이스는 **데이터 구조 + 접근 방식 + 확장 방법**에 따라 분류한다.

> 실무에서는 보통 다음 3단계로 사고한다
>
> **① 데이터 구조 → ② 트랜잭션 요구 → ③ 확장/운영 방식**

---

## 2. 관계형 데이터베이스 (RDBMS)

[![](%EB%8D%B0%EC%9D%B4%ED%84%B0%EB%B2%A0%EC%9D%B4%EC%8A%A4(Database)%20%EC%A2%85%EB%A5%98/image.png)](%EB%8D%B0%EC%9D%B4%ED%84%B0%EB%B2%A0%EC%9D%B4%EC%8A%A4(Database)%20%EC%A2%85%EB%A5%98/image.png)[![](https://images.openai.com/static-rsc-3/KDU2ZBfPnPuIgnZ4SgvDxC3EkQBc0Mk89w4RbKFPT5Ai55LPEyHamaRSGtJmePjyCr2s1dp4SIHgde_6tlklGvnX9Lh6TQk3njc7e_Qj2ig?purpose=fullsize)](https://images.openai.com/static-rsc-3/KDU2ZBfPnPuIgnZ4SgvDxC3EkQBc0Mk89w4RbKFPT5Ai55LPEyHamaRSGtJmePjyCr2s1dp4SIHgde_6tlklGvnX9Lh6TQk3njc7e_Qj2ig?purpose=fullsize)

### 2.1 개념

* **행(Row)과 열(Column)** 기반의 정형 데이터

* **테이블 간 관계(Relationship)** 를 명확히 정의

* **SQL** 사용

### 2.2 핵심 특징

* 스키마 고정 (Schema-on-write)

* ACID 트랜잭션 보장

* JOIN 가능

* 데이터 무결성 매우 강함

### 2.3 대표 DB

* MySQL

* PostgreSQL

* Oracle Database

* MariaDB

### 2.4 언제 사용?

* 금융, 결제, 주문, 회원 관리

* 데이터 정합성이 가장 중요한 시스템

---

## 3. NoSQL 데이터베이스 (비관계형 DB)

[![](https://images.openai.com/static-rsc-3/hxTs4fV9Ydn-DW5mEgekMWJMf0x2xs7zdrKEq8uQGpT_d-lV29mV7NY8iFU58MiBkSkvjs91RTlrkQ-2keemwTTIU1-oh8W053KpDlaNJJ4?purpose=fullsize)](https://images.openai.com/static-rsc-3/hxTs4fV9Ydn-DW5mEgekMWJMf0x2xs7zdrKEq8uQGpT_d-lV29mV7NY8iFU58MiBkSkvjs91RTlrkQ-2keemwTTIU1-oh8W053KpDlaNJJ4?purpose=fullsize)[![](https://miro.medium.com/1%2AKXoIoFnJCN8o4Sssmaqokw.png)](https://miro.medium.com/1%2AKXoIoFnJCN8o4Sssmaqokw.png)

### 3.1 개념

* **관계보다는 확장성과 유연성** 중심

* JOIN 없음 또는 제한적

* 대규모 분산 환경에 최적화

### 3.2 공통 특징

* Schema-less 또는 Schema-on-read

* 수평 확장(Scale-out) 쉬움

* ACID 대신 **BASE** 모델 채택

---

## 4. NoSQL 세부 유형

---

### 4.1 Key-Value Store

[![](https://substackcdn.com/image/fetch/%24s_%21y3zr%21%2Cf_auto%2Cq_auto%3Agood%2Cfl_progressive%3Asteep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F3705740a-695f-4294-88ce-547fe8723227_1610x1090.png)](https://substackcdn.com/image/fetch/%24s_%21y3zr%21%2Cf_auto%2Cq_auto%3Agood%2Cfl_progressive%3Asteep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F3705740a-695f-4294-88ce-547fe8723227_1610x1090.png)[![](https://d2908q01vomqb2.cloudfront.net/887309d048beef83ad3eabf2a79a64a389ab1c9f/2018/09/10/dynamodb-partition-key-1.gif)](https://d2908q01vomqb2.cloudfront.net/887309d048beef83ad3eabf2a79a64a389ab1c9f/2018/09/10/dynamodb-partition-key-1.gif)

### 특징

* `key → value` 단순 구조

* 초고속 조회

* 데이터 구조 단순

### 대표 DB

* Redis

* Amazon DynamoDB

* etcd

### 사용 사례

* 캐시

* 세션 저장소

* 토큰 관리

---

### 4.2 Document Store

[![](https://cdn.thenewstack.io/media/2023/06/8b510bed-image1.png)](https://cdn.thenewstack.io/media/2023/06/8b510bed-image1.png)[![](https://d1.awsstatic.com/onedam/marketing-channels/website/aws/en_US/product-categories/databases/non-relational/approved/images/7b76d177-1107-3103-8f42-514e3adaf0e1.792a31fed465f9eda21506f7daf8078bb52eea6e.png)](https://d1.awsstatic.com/onedam/marketing-channels/website/aws/en_US/product-categories/databases/non-relational/approved/images/7b76d177-1107-3103-8f42-514e3adaf0e1.792a31fed465f9eda21506f7daf8078bb52eea6e.png)

### 특징

* JSON / BSON 문서 구조

* 컬럼 고정 X

* 애플리케이션 친화적

### 대표 DB

* MongoDB

* Amazon DocumentDB

### 사용 사례

* 로그 데이터

* 사용자 프로필

* CMS, API 서버

---

### 4.3 Wide Column Store

[![](https://i.sstatic.net/rDWwy.png)](https://i.sstatic.net/rDWwy.png)

### 특징

* 컬럼 단위 저장

* 대용량 쓰기/읽기 성능 우수

* RDB처럼 보이지만 JOIN 없음

### 대표 DB

* Apache Cassandra

* HBase

### 사용 사례

* 로그 분석

* IoT 데이터

* 타임시리즈 데이터

---

### 4.4 Graph Database

[![](https://neo4j.com/docs/getting-started/_images/roles-graph.svg)](https://neo4j.com/docs/getting-started/_images/roles-graph.svg)

### 특징

* Node + Edge 구조

* 관계 탐색에 특화

* JOIN 대신 그래프 탐색

### 대표 DB

* Neo4j

### 사용 사례

* SNS 친구 추천

* 추천 시스템

* 네트워크 토폴로지 분석

---

## 5. 인메모리 데이터베이스 (In-Memory DB)

[![](https://media.licdn.com/dms/image/v2/D5612AQGRAwL_wmwxDA/article-cover_image-shrink_720_1280/article-cover_image-shrink_720_1280/0/1677033825935?e=2147483647&t=AyPT5YoLW6FfsKrYBtHiKKCQJNW2gjYLg1sjsfF2774&v=beta)](https://media.licdn.com/dms/image/v2/D5612AQGRAwL_wmwxDA/article-cover_image-shrink_720_1280/article-cover_image-shrink_720_1280/0/1677033825935?e=2147483647&t=AyPT5YoLW6FfsKrYBtHiKKCQJNW2gjYLg1sjsfF2774&v=beta)

### 특징

* 디스크가 아닌 **RAM 기반**

* 매우 빠름

* 영속성은 선택 사항

### 대표

* Redis

* Memcached

### 사용

* 캐시 계층

* DB 부하 감소용

---

## 6. 클라우드 관리형 데이터베이스 (DBaaS)

[![](https://d2908q01vomqb2.cloudfront.net/fc074d501302eb2b93e2554793fcaf50b3bf7291/2024/03/08/fig1-lseg-chaos-engineering-1024x584.png)](https://d2908q01vomqb2.cloudfront.net/fc074d501302eb2b93e2554793fcaf50b3bf7291/2024/03/08/fig1-lseg-chaos-engineering-1024x584.png)

### 개념

* 설치/백업/패치/확장 자동화

* 인프라 엔지니어의 운영 부담 감소

### 대표

* Amazon RDS

* Amazon Aurora

* Google Cloud Spanner

---

## 7. 데이터베이스 선택 기준

| 기준 | 선택 방향 |
| --- | --- |
| 트랜잭션 중요 | RDB |
| 스키마 유연 | Document DB |
| 초고속 조회 | Key-Value |
| 대규모 분산 | NoSQL |
| 관계 탐색 | Graph |
| 운영 최소화 | Managed DB |

---

## 8. DB 포지션

```
AWS / Kubernetes / Network
  ├ CloudWatch Logs
  ├ VPC Flow Logs
  ├ ALB Logs
  ├ Billing
        ↓
PostgreSQL  → 로그·메트릭·이벤트·임베딩
DynamoDB   → 알람 상태·룰·트래킹
MySQL     → 계정·프로젝트·정책·비용 기준
Redis     → 실시간 상태·쿼리 캐시
```

---