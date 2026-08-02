---
title: "Aurora PostgreSQL 생성 및 고가용성 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 클라우드 기술 기초(TESS)"]
is_public: true
draft: false
---

# Aurora PostgreSQL 생성 및 고가용성 실습

## 실습 목표

이번 실습에서는 **Amazon Aurora PostgreSQL 데이터베이스 클러스터**를 생성하고 다음 기능을 확인한다.

* Aurora PostgreSQL 생성

* Database Subnet 구성

* DB Security Group 구성

* DB Subnet Group 생성

* PostgreSQL 접속

* Database / User 생성

* Parameter Group 적용

* Read Replica 동작 확인

* Aurora Failover 테스트

---

# 1. Database Network Baseline 생성

Aurora는 **서로 다른 AZ에 최소 2개의 DB Subnet**이 필요하다.

## 1️⃣ Database Subnet 생성

AWS 콘솔 이동

```
VPC → Subnets → Subnet 생성
```

다음 명세로 생성한다.

| 항목 | Database Subnet 01 | Database Subnet 02 |
| --- | --- | --- |
| VPC | 이니셜-vpc-ap-01 | 이니셜-vpc-ap-01 |
| Subnet Name | 이니셜-sub-db-01 | 이니셜-sub-db-02 |
| AZ | ap-northeast-2a | ap-northeast-2c |
| CIDR | 10.0.80.0/24 | 10.0.81.0/24 |

* 서로 다른 AZ에 DB Subnet이 존재해야 Aurora Multi-AZ 구성이 가능하다.

---

## 2️⃣ Database Routing Table 생성

AWS 콘솔 이동

```
VPC → Route Tables → 생성
```

설정

| 항목 | 값 |
| --- | --- |
| Name | 이니셜-rtb-db |
| VPC | 이니셜-vpc-ap-01 |

생성 후 다음 서브넷 연결

* 이니셜-sub-db-01

* 이니셜-sub-db-02

---

# 2. Security Group 생성

AWS 콘솔 이동

```
EC2 → Security Groups → 생성
```

설정

| 항목 | 값 |
| --- | --- |
| Name | 이니셜-sg-aurora |
| VPC | 이니셜-vpc-ap-01 |

### Inbound Rule

| Type | Port | Source |
| --- | --- | --- |
| PostgreSQL | 5432 | 10.0.0.0/16 |

💡 VPC 내부에서만 DB 접속 허용한다.

---

# 3. DB Subnet Group 생성

Aurora는 **DB Subnet Group**을 통해 DB 인스턴스를 배치할 서브넷을 지정한다.

AWS 콘솔 이동

```
RDS → Subnet Groups → Create
```

설정

| 항목 | 값 |
| --- | --- |
| Name | 이니셜-subgroup-aurora |
| VPC | 이니셜-vpc-ap-01 |
| AZ | ap-northeast-2a, ap-northeast-2c |
| Subnet | 이니셜-sub-db-01, 이니셜-sub-db-02 |

---

# 4. Aurora PostgreSQL 생성

AWS 콘솔 이동

```
RDS → Databases → Create database
```

## Engine 설정

| 항목 | 값 |
| --- | --- |
| Engine | Aurora PostgreSQL |
| Version | Aurora PostgreSQL 15 |
| Template | Dev/Test |

---

## Database 설정

| 항목 | 값 |
| --- | --- |
| Cluster identifier | 이니셜-rds-aurora |
| Master username | postgres |
| Password | qwer1234 |

---

## Instance 설정

| 항목 | 값 |
| --- | --- |
| Instance type | db.t3.medium |
| Multi-AZ | 생성 안함 |

---

## Network 설정

| 항목 | 값 |
| --- | --- |
| VPC | 이니셜-vpc-ap-01 |
| DB Subnet Group | 이니셜-subgroup-aurora |
| Public Access | No |
| Security Group | 이니셜-sg-aurora |

---

# 5. PostgreSQL 접속

## 1️⃣ PostgreSQL client 설치

```
sudo apt update
sudo apt install postgresql-client
```

---

## 2️⃣ Aurora Endpoint 확인

AWS 콘솔 이동

```
RDS → Databases → 이니셜-rds-aurora
```

다음 값 복사

```
Cluster Endpoint
```

---

## 3️⃣ PostgreSQL 접속

```
psql -U postgres -h {RDS_AURORA_ENDPOINT}
```

비밀번호 입력

```
qwer1234
```

정상 접속 화면

```
postgres=>
```

---

# 6. Database 및 User 생성

Aurora 접속 상태에서 실행

```
create database trip_advisor;

create user "user" with password 'qwer1234';

grant all privileges on database trip_advisor to "user";

alter database trip_advisor owner to "user";
```

---

## user 계정 접속 테스트

```
psql -U user -d trip_advisor -h {RDS_AURORA_ENDPOINT}
```

---

# 7. Custom Parameter Group 생성

Parameter Group은 **DB 설정값 관리 기능**이다.

### Parameter Group 생성

AWS 콘솔 이동

```
RDS → Parameter Groups → Create
```

설정

| 항목 | 값 |
| --- | --- |
| Name | 이니셜-pg-postgresql |
| Engine | Aurora PostgreSQL |
| Family | aurora-postgresql15 |
| Type | DB Cluster Parameter Group |

---

### timezone 설정

Parameter Group 수정

```
timezone = Asia/Seoul
```

---

### Parameter Group 적용

```
RDS → Databases → 이니셜-rds-aurora → Modify
```

다음 변경

```
DB Cluster Parameter Group
→ 이니셜-pg-postgresql
```

---

### 적용 확인

```
SHOW timezone;
```

결과

```
Asia/Seoul
```

---

# 8. Read Replica 테스트

Aurora Reader 인스턴스를 생성한다.

AWS 콘솔 이동

```
RDS → Databases → 이니셜-rds-aurora → Actions → Add reader
```

---

# 9. Writer / Reader 테스트

## Writer 접속

```
psql -U user -d trip_advisor -h {WRITER_ENDPOINT}
```

---

## 테스트 테이블 생성

```
CREATE TABLE attractions (
 id SERIAL PRIMARY KEY,
 name VARCHAR(255),
 location VARCHAR(255),
 average_rating VARCHAR(10),
 photo_url VARCHAR(255)
);
```

---

## Reader 조회 반복

```
while true; do
 PGPASSWORD="qwer1234" psql \
 -h {READER_ENDPOINT} \
 -U user \
 -d trip_advisor \
 -c "select * from attractions;";
 sleep 10;
done
```

---

## Writer에서 데이터 입력

```
INSERT INTO attractions
(name,location,average_rating)
VALUES
('Eiffel Tower','Paris',4.7),
('Statue of Liberty','New York',4.6),
('Taj Mahal','India',4.9);
```

10초 후 Reader에서 데이터 확인 가능하다.

---

# 10. Aurora Failover 테스트

Aurora는 Writer 장애 시 Reader가 자동 승격된다.

---

## Writer IP 확인

```
nslookup {WRITER_ENDPOINT} \
| grep -E "Address: 10\." \
| awk '{print $2}'
```

---

## Writer IP 반복 조회

```
while true; do
 nslookup {WRITER_ENDPOINT} \
 | grep -E "Address: 10\." \
 | awk '{print $2}'
 sleep 1
done
```

---

## Failover 실행

AWS 콘솔 이동

```
RDS → Databases → 이니셜-rds-aurora → Actions → Failover
```

---

## 결과 확인

터미널에서 Writer IP가 변경된다.

즉

```
기존 Reader → 새로운 Writer
```

승격된 것이다.

---

# 핵심 정리

Aurora 특징

| 항목 | 설명 |
| --- | --- |
| Multi-AZ | 여러 AZ에 DB 배치 |
| Reader Instance | 읽기 확장 |
| Failover | 자동 장애 조치 |
| Endpoint | 고정 IP 대신 DNS 사용 |

---