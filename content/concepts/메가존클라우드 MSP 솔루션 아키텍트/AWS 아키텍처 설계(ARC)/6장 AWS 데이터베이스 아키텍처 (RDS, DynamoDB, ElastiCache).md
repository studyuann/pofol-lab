---
title: "6장 AWS 데이터베이스 아키텍처 (RDS, DynamoDB, ElastiCache)"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 아키텍처 설계(ARC)"]
is_public: true
draft: false
---

# 6장 AWS 데이터베이스 아키텍처 (RDS, DynamoDB, ElastiCache)

---

# 6.1 데이터베이스 아키텍처 개요

애플리케이션을 구성할 때 데이터 저장소는 매우 중요한 계층임.

웹 서버나 애플리케이션 서버는 요청을 처리하는 역할을 담당하지만, 실제 서비스의 핵심 데이터는 결국 데이터베이스에 저장됨.

예를 들어

* 회원 정보 저장

* 주문 정보 저장

* 게시글 저장

* 세션 정보 저장

* 캐시 데이터 저장

* 로그성 데이터 저장

이처럼 같은 “데이터 저장”이라도 데이터의 성격이 서로 다름.

따라서 모든 데이터를 하나의 데이터베이스에 넣는 것이 아니라, **데이터 특성에 맞는 저장소를 선택해야 함.**

AWS에서 대표적인 데이터베이스 관련 서비스

| 서비스 | 유형 | 설명 |
| --- | --- | --- |
| Amazon RDS | 관계형 데이터베이스 | 관리형 RDBMS |
| Amazon Aurora | 관계형 데이터베이스 | AWS 최적화 관계형 DB |
| Amazon DynamoDB | NoSQL | 키-값/문서 기반 DB |
| Amazon ElastiCache | 캐시 | Redis, Memcached |
| Amazon Redshift | 데이터 웨어하우스 | 분석용 |
| Amazon DocumentDB | 문서형 DB | MongoDB 호환 |

이 장에서는 ARC 커리큘럼 기준으로 다음 3가지를 중심으로 학습함.

* RDS

* DynamoDB

* ElastiCache

---

# 6.2 데이터베이스 유형 구분

데이터베이스를 설계할 때 먼저 해야 하는 일은 “어떤 데이터베이스를 쓸지”를 정하는 것임.

대표적인 분류

| 유형 | 설명 | 예시 서비스 |
| --- | --- | --- |
| 관계형 데이터베이스 | 테이블 구조, SQL 사용 | RDS, Aurora |
| NoSQL 데이터베이스 | 유연한 구조, 대규모 확장 | DynamoDB |
| 캐시 저장소 | 빠른 응답을 위한 메모리 저장소 | ElastiCache |

---

## 6.2.1 관계형 데이터베이스

관계형 데이터베이스는 데이터를 **테이블 구조**로 저장함.

예

* users 테이블

* orders 테이블

* products 테이블

특징

* 행(Row), 열(Column) 구조

* SQL 사용

* 정합성이 중요함

* 트랜잭션 처리 가능

* JOIN 가능

적합한 예

* 쇼핑몰 주문 시스템

* 회원 관리 시스템

* ERP

* 게시판 서비스

---

## 6.2.2 NoSQL 데이터베이스

NoSQL은 관계형 구조를 사용하지 않는 데이터베이스를 의미함.

DynamoDB는 AWS의 대표적인 NoSQL 서비스임.

특징

* 매우 빠른 확장성

* 유연한 데이터 구조

* 대량 요청 처리에 강함

* 단순한 키 기반 조회에 적합함

적합한 예

* 사용자 세션 저장

* 대규모 클릭 데이터 저장

* 게임 랭킹 데이터

* IoT 데이터

* 짧은 응답 시간이 중요한 서비스

---

## 6.2.3 캐시 저장소

캐시는 원본 데이터베이스의 부하를 줄이고 응답 속도를 높이기 위해 사용함.

예

* 자주 조회되는 상품 목록

* 로그인 세션

* API 응답 캐시

* 인기 게시글 목록

즉, 캐시는 **원본 데이터 저장소를 대체하는 것이 아니라 보조하는 계층**임.

---

# 6.3 Amazon RDS 개요

Amazon RDS는 **Relational Database Service**의 약자임.

AWS에서 관계형 데이터베이스를 쉽게 운영할 수 있도록 제공하는 관리형 서비스임.

온프레미스나 EC2에 직접 DB를 설치하면 다음 작업을 직접 해야 함.

* 운영체제 관리

* DB 설치

* 패치

* 백업

* 장애 복구

* 복제 구성

* 모니터링

RDS를 사용하면 이런 관리 작업 상당 부분을 AWS가 대신 처리함.

즉, RDS는 “DB를 직접 설치하는 것”이 아니라

**운영 부담을 줄인 관리형 관계형 DB 서비스**라고 보면 됨.

---

# 6.4 RDS 지원 엔진

RDS는 여러 DB 엔진을 지원함.

| 엔진 | 설명 |
| --- | --- |
| MySQL | 오픈소스 관계형 DB |
| MariaDB | MySQL 계열 |
| PostgreSQL | 오픈소스 고기능 관계형 DB |
| Oracle | 상용 DB |
| SQL Server | Microsoft 관계형 DB |

---

# 6.5 RDS의 장점

### 1. 관리형 서비스

백업, 패치, 모니터링, 장애 조치 기능을 AWS가 많이 지원함.

### 2. 쉬운 배포

콘솔 몇 단계만으로 DB를 배포할 수 있음.

### 3. 고가용성 지원

Multi-AZ 구성이 가능함.

### 4. 읽기 확장 가능

Read Replica 구성이 가능함.

### 5. 보안 통합

VPC, 보안 그룹, KMS와 쉽게 연동 가능함.

---

# 6.6 RDS 아키텍처 핵심 요소

RDS를 생성할 때 중요한 요소

* DB Engine

* DB Instance Class

* Storage Type

* VPC/Subnet Group

* Security Group

* Backup

* Multi-AZ

* Read Replica

---

## 6.6.1 DB Instance Class

RDS도 결국 컴퓨팅 자원이 필요하므로 인스턴스 클래스가 있음.

예

* db.t3.micro

* db.t3.small

* db.m6i.large

실습에서는 보통 비용을 고려해 작은 사양을 사용함.

---

## 6.6.2 Storage

RDS는 내부적으로 스토리지를 사용함.

예

* gp3

* io1/io2

보통 실습 환경에서는 범용 SSD 계열을 많이 사용함.

---

## 6.6.3 DB Subnet Group

RDS는 VPC 안에서 배포되며, 어느 서브넷에서 동작할지 정하기 위해 **DB Subnet Group**을 사용함.

보통 원칙

* 최소 2개 AZ의 private subnet 포함

* public subnet보다 private subnet 사용 권장

즉, RDS는 일반적으로 인터넷에서 직접 접근하지 않도록 private subnet에 배치함.

---

# 6.7 RDS 보안

RDS 보안은 매우 중요함.

특히 교육 환경에서는 “접속이 되게 만드는 것”에 집중하다가 잘못된 보안 구성을 하기 쉬움.

RDS 보안 핵심 요소

* Private Subnet 배치

* Security Group 제한

* IAM과 연동되는 주변 권한 통제

* 암호화

* 백업 보호

---

## 6.7.1 보안 그룹 설계

예를 들어 애플리케이션 서버만 RDS에 접속해야 한다면

RDS 보안 그룹 인바운드에 3306 포트를 전체 인터넷에 열면 안 됨.

좋은 방식

* Source를 App 서버 보안 그룹으로 제한

예

| 방향 | 프로토콜 | 포트 | 소스 |
| --- | --- | --- | --- |
| Inbound | TCP | 3306 | 이니셜-sg-app |

즉, “누구나 접속 가능”이 아니라 “특정 앱 서버만 접속 가능”하게 설계해야 함.

---

## 6.7.2 Public Access 여부

RDS는 생성 시 Public access 옵션이 있음.

원칙적으로 운영 환경에서는 보통 다음이 권장됨.

```
Public access: No
```

이유

* DB를 인터넷에 직접 노출하지 않기 위함

* DB는 앱 서버를 통해서만 접근하는 구조가 일반적임

---

# 6.8 Multi-AZ

Multi-AZ는 고가용성을 위한 RDS 기능임.

주 DB 인스턴스와 동기 복제되는 대기 인스턴스를 다른 AZ에 두는 구조임.

구조 예

```
Primary DB (AZ-a)
       │
동기 복제
       │
Standby DB (AZ-b)
```

특징

* 장애 시 자동 장애 조치 가능

* 읽기 확장용이 아님

* 고가용성 목적임

즉, Multi-AZ는 성능 향상용이 아니라 **장애 대비용**임.

---

# 6.9 Read Replica

Read Replica는 읽기 부하를 분산하기 위한 기능임.

구조 예

```
Primary DB
   ├ Read Replica 1
   └ Read Replica 2
```

특징

* 읽기 전용 복제본

* 비동기 복제

* 조회 성능 분산 가능

* 보고서/통계/조회용 분리 가능

즉, Read Replica는 **읽기 확장용** 기능임.

---

# 6.10 Multi-AZ와 Read Replica 차이

| 항목 | Multi-AZ | Read Replica |
| --- | --- | --- |
| 목적 | 고가용성 | 읽기 확장 |
| 복제 방식 | 동기 | 비동기 |
| 사용자 접근 | 일반적으로 Primary만 접근 | 읽기 전용 접근 |
| 장애 조치 | 자동 가능 | 일반적으로 자동 장애 조치 목적 아님 |

# RDS와 Aurora 비교

|  |  |  |
| --- | --- | --- |
| **구분** | **Amazon RDS (Standard)** | **Amazon Aurora** |
| **기반 구조** | 전통적인 DB 엔진 (MySQL, MariaDB 등) | **클라우드 네이티브** (AWS 전용 설계) |
| **성능** | 표준적인 성능 (EC2 기반) | MySQL 대비 최대 **5배**, PostgreSQL 대비 **3배** |
| **스토리지** | 미리 할당한 용량 (EBS) | **자동 확장** (최대 128TB, 사용한 만큼만 지불) |
| **복제(Replica)** | 최대 5개, 약간의 지연 시간 발생 | 최대 **15개**, 지연 시간이 거의 없음 (ms 미만) |
| **가용성** | 다중 AZ 설정 시 대기용 DB로 전환 | 3개 AZ에 **6개의 데이터 복사본** 유지 (복구 빠름) |
| **비용** | 상대적으로 저렴 (소규모에 유리) | 성능만큼 **가격대가 높음** (대규모/중요 서비스) |
| **적합한 상황** | 비용 절감, 소규모 프로젝트, 특정 엔진 필요 | 고가용성, 대규모 트래픽, 자동 확장 필요 |
| **비용 구조** | 상대적으로 낮음 (프리티어 가능) | 상대적으로 높음 (I/O 비용 별도) |
| **스토리지** | 수동 또는 자동 확장 필요 | 자동 확장 (최대 128TB) |
| **복제 속도** | 상대적으로 느림 (Binlog 방식) | 매우 빠름 (밀리초 단위) |

# 6.11 DynamoDB 개요

DynamoDB는 AWS의 완전관리형 NoSQL 데이터베이스임.

특징

* 매우 빠른 응답 속도

* 서버 관리 불필요

* 자동 확장 가능

* 대규모 요청 처리에 적합

* 키-값 및 문서형 구조 지원

DynamoDB는 관계형 DB처럼 복잡한 JOIN이나 강한 스키마 구조를 중심으로 쓰기보다는,

**대규모 키 기반 조회**나 **서버리스 환경의 상태 저장**에 적합함.

즉, DynamoDB는 다음과 같은 상황에서 특히 강점을 가짐.

* 사용자별 상태 정보 저장

* 대량의 요청을 처리해야 하는 키 기반 조회

* 서버리스 애플리케이션의 상태 저장소

* IoT / 이벤트성 데이터 저장

* 게임, 모바일, API 중심 서비스

---

# 6.12 DynamoDB의 핵심 개념

DynamoDB 핵심 개념

* Table

* Item

* Attribute

* Partition Key

* Sort Key

---

## 6.12.1 Table

데이터를 저장하는 논리적 단위임.

예

* Users

* Orders

* DeviceStatus

* SessionState

* ApiRequestLog

---

## 6.12.2 Item

관계형 DB의 행(Row)에 대응되는 개념임.

예

```
{
  "UserId": "user001",
  "Name": "Kim",
  "Status": "active"
}
```

---

## 6.12.3 Attribute

Item 내부의 각 필드임.

예

* UserId

* Name

* Status

* UpdatedAt

---

## 6.12.4 Partition Key

DynamoDB에서 데이터를 저장하고 조회할 때 기준이 되는 핵심 키임.

DynamoDB 설계에서 가장 중요하게 보는 항목 중 하나임.

예

* UserId

* OrderId

* DeviceId

* ApiKey

Partition Key 설계가 좋지 않으면 데이터가 한쪽으로 몰릴 수 있으므로,

조회 패턴을 먼저 보고 키를 정해야 함.

---

## 6.12.5 Sort Key

선택적으로 함께 사용하는 두 번째 키임.

같은 Partition Key 내부에서 정렬 기준 역할을 함.

예

* UserId + OrderDate

* RoomId + MessageTime

* DeviceId + EventTime

---

# 6.13 DynamoDB 사용 사례

**대규모 키 기반 조회가 필요한 시스템**에서 매우 자주 사용됨.

### 1. 사용자 프로필 / 상태 조회

사용자 ID로 빠르게 조회해야 하는 정보 저장.

### 2. 서버리스 애플리케이션 상태 저장

API Gateway + Lambda 조합에서 상태 저장소로 자주 사용함.

### 3. IoT 장비 상태 정보 저장

장비 ID 기준으로 상태를 저장하고 조회하는 구조에 적합함.

### 4. 게임 / 모바일 서비스

짧은 응답 시간과 대규모 동시 요청 처리에 적합함.

### 5. 이벤트성 데이터 / 메타데이터 저장

정형화된 관계형 모델보다 키 중심 조회가 중요한 경우에 적합함.

---

# 6.14 DynamoDB와 RDS 비교

| 항목 | RDS | DynamoDB |
| --- | --- | --- |
| 구조 | 관계형 | NoSQL |
| 질의 | SQL | API 기반 조회 |
| JOIN | 가능 | 일반적으로 없음 |
| 트랜잭션/정합성 | 강함 | 패턴 중심 설계 |
| 확장성 | 전통적 확장 구조 | 매우 뛰어남 |
| 대표 용도 | 주문, 결제, 회원, 업무 DB | 대규모 키 조회, 상태 저장 |

즉, DynamoDB는 RDS를 대체하는 개념이 아니라 **RDS와 다른 문제를 해결하는 저장소**라고 보는 것이 맞음.

---

# 6.15 Amazon ElastiCache 개요

ElastiCache는 AWS의 관리형 인메모리 캐시 서비스임.

메모리에 데이터를 저장해서 매우 빠른 응답을 제공함.

지원 엔진

* Redis

* Memcached

---

# 6.16 캐시가 필요한 이유

애플리케이션에서 같은 데이터를 반복해서 조회하면 원본 DB에 부하가 쌓임.

예

* 메인 페이지 인기 글 목록

* 사용자 프로필 정보

* 공지사항 목록

* 상품 상세 정보

* API 응답 결과

이런 데이터를 매번 RDS에서 조회하면 응답 시간이 길어지고 DB 부하가 증가함.

그래서 자주 조회되는 값을 메모리에 저장해 빠르게 응답함.

구조 예

```
사용자 요청
   │
App Server
   │
Cache 확인
 ├ 있으면 캐시 반환
 └ 없으면 DB 조회 후 캐시에 저장
```

이 구조를 통해

* 응답 속도 향상

* DB 부하 감소

* 전체 시스템 처리량 향상

효과를 얻을 수 있음.

---

# 6.17 Redis와 Memcached 차이

| 항목 | Redis | Memcached |
| --- | --- | --- |
| 데이터 구조 | 문자열, 해시, 리스트 등 다양함 | 단순 Key-Value |
| TTL | 지원 | 지원 |
| 영속성 | 일부 지원 가능 | 없음 |
| 기능 | 풍부함 | 단순함 |
| 대표 용도 | 세션, 캐시, 순위표 | 단순 캐시 |

---

# 6.18 ElastiCache Redis 주요 사용 사례

### 1. 로그인 세션 저장

가장 대표적인 사용 사례 중 하나임.

### 2. 조회 캐시

RDS 조회 결과를 임시 저장하여 빠르게 응답함.

### 3. 공용 상태 저장

웹 서버 여러 대가 공통으로 참조해야 하는 임시 상태값 저장.

### 4. 랭킹 / 카운터

Redis 자료구조를 활용해 빠르게 처리 가능함.

### 5. 일시적 데이터 저장

짧은 시간 유지되는 임시 데이터에 적합함.

---

# 6.19 로그인 세션 저장소로서 Redis

로그인 세션은 보통 다음 특징을 가짐.

* 매우 자주 조회됨

* 짧은 응답 시간이 중요함

* 만료 시간이 존재함

* 여러 웹 서버가 공유해야 할 수 있음

이 조건에 Redis가 매우 잘 맞음.

---

## 6.19.1 왜 Redis가 세션에 적합한가

### 1. 메모리 기반이라 매우 빠름

세션 조회는 거의 모든 요청마다 일어날 수 있음.

Redis는 이 패턴에 적합함.

### 2. TTL 설정이 자연스러움

예

```
SET session:abc123 "user1" EX 1800
```

이 명령은 `session:abc123` 키를 1800초 동안 유지한 뒤 자동 만료시킴.

세션 만료 처리에 매우 적합함.

### 3. 여러 서버가 세션을 공유하기 쉬움

예를 들어 ALB 뒤에 Web 서버가 2대 이상 있으면 요청이 서로 다른 서버로 갈 수 있음.

이때 각 서버 로컬 메모리에 세션을 두면 로그인 상태가 유지되지 않을 수 있음.

Redis를 공용 세션 저장소로 두면 이 문제를 해결할 수 있음.

### 4. 세션 삭제와 갱신이 쉬움

로그아웃 시 세션 삭제, 활동 시 만료 시간 연장 같은 동작이 자연스러움.

---

# 6.20 DynamoDB와 Redis 역할 구분

| 구분 | Redis | DynamoDB |
| --- | --- | --- |
| 주 용도 | 세션, 캐시, 임시 상태 | 대규모 키-값 저장, 서버리스 상태 저장 |
| 저장 매체 | 메모리 중심 | 영속 저장 중심 |
| 응답 속도 | 매우 빠름 | 빠름 |
| TTL 활용 | 매우 자연스러움 | 가능 |
| 세션 저장 적합성 | 매우 높음 | 가능하지만 보조적 선택 |
| 서버리스 친화성 | 보통 | 매우 높음 |

즉, 실무적으로 보면 다음을 고려.

```
로그인 세션, 캐시 → Redis 우선 고려
대규모 키 기반 상태 저장, 서버리스 저장소 → DynamoDB 고려
```

---

# 6.21 데이터베이스 계층 아키텍처 예

기존 3계층 아키텍처에 데이터 계층을 연결하면 다음처럼 정리할 수 있음.

```
Internet
   │
ALB
   │
Web / App EC2
   │
├ RDS         → 핵심 트랜잭션 데이터
├ Redis       → 로그인 세션 / 캐시
└ DynamoDB    → 대규모 키 기반 상태 저장
```

예시 해석

* **RDS** : 회원, 주문, 게시글 같은 핵심 데이터

* **Redis** : 로그인 세션, 자주 조회되는 캐시 데이터

* **DynamoDB** : 서버리스 상태 저장, 키 기반 빠른 조회 데이터

---

# 6.22 실습 3 : DynamoDB 테이블 생성

실습 목표

* DynamoDB를 세션 저장소가 아니라 **대규모 키 기반 상태 저장소** 관점으로 이해함

* Partition Key 설계 개념을 이해함

* 콘솔과 CLI로 Item을 저장하고 조회함

---

## 예시 시나리오

“사용자 상태 정보 저장소”

예를 들어 사용자별 앱 설정, 장치 상태, API 상태 정보 같은 데이터를 저장한다고 가정함.

---

## 6.22.1 테이블 생성

DynamoDB 콘솔 → Create table

설정 예

| 항목 | 값 |
| --- | --- |
| Table name | UserState |
| Partition key | UserId |
| Sort key | StateType |

설명

* `UserId` : 사용자 기준 조회

* `StateType` : 상태 종류 구분

즉, 같은 사용자에 대해 여러 상태 정보를 저장할 수 있음.

---

## 6.22.2 콘솔에서 아이템 추가

예시 값

```
{
  "UserId": "user-01",
  "StateType": "theme",
  "Value": "dark",
  "UpdatedAt": "2026-03-16T12:00:00"
}
```

---

## 6.22.3 CLI로 아이템 추가

```
aws dynamodb put-item \
  --table-name UserState \
  --item '{
    "UserId": {"S": "user-02"},
    "StateType": {"S": "language"},
    "Value": {"S": "ko"},
    "UpdatedAt": {"S": "2026-03-16T12:10:00"}
  }'
```

* 윈도우 cmd

```
aws dynamodb put-item ^
  --table-name UserState ^
  --item "{\"UserId\": {\"S\": \"user-02\"}, \"StateType\": {\"S\": \"language\"}, \"Value\": {\"S\": \"ko\"}, \"UpdatedAt\": {\"S\": \"2026-03-16T12:10:00\"}}" ^
  --profile=kyt
```

### 명령어 설명

### `put-item`

DynamoDB 테이블에 데이터를 1건 저장하는 명령임.

---

### `--table-name`

대상 테이블 이름을 지정함.

---

---

### `--item`

저장할 데이터를 JSON 형식으로 정의함.

여기서 `"S"`는 문자열 타입을 의미함.

---

## 6.22.4 CLI로 아이템 조회

```
aws dynamodb get-item \
  --table-name UserState \
  --key '{
    "UserId": {"S": "user-02"},
    "StateType": {"S": "language"}
  }'
```

이 명령은 특정 사용자(`user-02`)의 특정 상태(`language`)를 조회함.

---

# 6.23 실습 4 : ElastiCache Redis 생성 및 세션 저장 예시

실습 목표

* Redis를 로그인 세션 / 캐시 저장소 관점에서 이해함

* Redis 기본 set/get 및 TTL 동작을 확인함

---

## 6.23.1 Redis 클러스터 생성 예시

ElastiCache 콘솔 → Redis OSS → Create

설정 예

| 항목 | 값 |
| --- | --- |
| Cluster mode | Disabled |
| Node type | cache.t3.micro 또는 최소 사양 |
| Replicas | 0 또는 실습 환경에 맞춤 |
| VPC | 이니셜-vpc-main |
| Subnet group | private subnet 포함 |
| Security group | 이니셜-sg-redis |

보안 그룹 인바운드

| 방향 | 프로토콜 | 포트 | 소스 |
| --- | --- | --- | --- |
| Inbound | TCP | 6379 | 이니셜-sg-app |

---

## 6.23.2 EC2에서 Redis 클라이언트 설치

Amazon Linux 예시

```
sudo dnf install -y redis6
```

설치 확인

```
redis6-cli --version
```

---

## 6.23.3 Redis 접속

```
redis6-cli -h <REDIS-ENDPOINT>
```

예

```
redis-cli -h myredis.xxxxxx.use1.cache.amazonaws.com -c --tls
```

---

## 6.23.4 세션 저장 예시

```
SET session:abc123 '{"user_id":"u1001","role":"student"}' EX 1800
```

### 명령어 설명

### `SET`

Redis에 key-value를 저장하는 기본 명령임.

### `session:abc123`

세션 ID를 key로 사용하는 예시임.

### `'{"user_id":"u1001","role":"student"}'`

세션에 저장할 사용자 정보 예시임.

### `EX 1800`

1800초 뒤 자동 만료되도록 TTL을 설정함.

즉, 로그인 세션을 저장하면서 동시에 만료 시간도 같이 지정한 것임.

조회

```
GET session:abc123
```

TTL 확인

```
TTL session:abc123
```

삭제

```
DEL session:abc123
```

이 흐름은 각각

* 로그인 시 세션 저장

* 요청 처리 시 세션 조회

* 로그아웃 시 세션 삭제

에 대응.

---

# 6.24 데이터 저장소 선택 기준

| 요구사항 | 적합한 서비스 |
| --- | --- |
| SQL, 트랜잭션, JOIN 필요 | RDS |
| 로그인 세션 저장 | ElastiCache Redis |
| 자주 조회되는 데이터 캐시 | ElastiCache Redis |
| 대규모 키 기반 조회 | DynamoDB |
| 서버리스 상태 저장 | DynamoDB |
| DB 고가용성 | RDS Multi-AZ |
| 읽기 부하 분산 | RDS Read Replica |