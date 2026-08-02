---
title: "PostgreSQL 이중화"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "데이터베이스", "RDB(Relational DataBase)"]
is_public: true
draft: false
---

# PostgreSQL 이중화

---

## 1. PostgreSQL 이중화 개요

PostgreSQL 이중화의 목적은 MySQL과 동일.

* **고가용성(HA)** : Primary 장애 시 빠른 복구

* **읽기 부하 분산** : Read Replica 활용

* **백업/DR** : 운영 데이터 보호

PostgreSQL의 핵심 특징은 **WAL (Write-Ahead Log)** 기반 복제.

---

## 2. PostgreSQL 이중화 방식 한눈에 정리

| 구분 | 설명 |
| --- | --- |
| Streaming Replication | WAL을 실시간으로 전송 |
| Logical Replication | 테이블 단위 논리 복제 |
| File-based Replication | WAL 아카이빙 |
| 동기 / 비동기 | Commit 시점 제어, 비동기는 Primary가 Standby commit유무와 상관없이 commit |

---

## 3. PostgreSQL Streaming Replication

[![](https://www.postgresql.fastware.com/hubfs/Images/PI/img-pi-dgm-ha-str-rep-wal-how-to-transfer.png)](https://www.postgresql.fastware.com/hubfs/Images/PI/img-pi-dgm-ha-str-rep-wal-how-to-transfer.png)

### 구조

```
[ Primary ]
   │  WAL
   ▼
[ Standby ]
```

* Primary에서 트랜잭션 발생

* WAL 로그 생성

* Standby가 WAL을 받아 **동일한 상태로 재현**

📌 **MySQL Binary Log 복제와 개념적으로 동일**

---

## 4. 동기(Synchronous) vs 비동기(Asynchronous)

### 1) 비동기 (기본값)

* Primary는 Standby 응답을 기다리지 않음

* 성능 우수

* 장애 시 일부 데이터 유실 가능

```
- 비동기 설정
# postgresql.conf (Primary)
# synchronous_commit = on
or
synchronous_commit = off
```

### 2) 동기

* Standby가 WAL 수신 완료해야 commit 성공

* 데이터 정합성 ↑

* 성능 ↓

```
- 동기 설정
# postgresql.conf (Primary)
synchronous_commit = on
synchronous_standby_names = 'standby1'
```

---

## 5. 기본 실습 시나리오 (Ubuntu 2대 기준)

```
node1 : Primary
node2 : Standby
```

---

## 6. 실습 ① Primary 서버 설정

### 1) PostgreSQL 설치

```
sudo apt update
sudo apt install -y postgresql
```

### 2) WAL 복제 설정

```
# /etc/postgresql/14/main/postgresql.conf
listen_addresses = '*'

wal_level = replica
max_wal_senders = 10
wal_keep_size = 64MB
```

### 3) 복제 계정 생성

```
sudo -iu postgres psql
```

```
CREATE ROLE repl WITH REPLICATION LOGIN PASSWORD 'replpass';
```

### 4) 접근 허용

```
# pg_hba.conf
host replication repl 192.168.80.0/24 scram-sha-256
```

```
sudo systemctl restart postgresql
```

---

## 7. 실습 ② Standby 서버 구성

### 1) PostgreSQL 중지

```
sudo systemctl stop postgresql
```

### 2) 기존 데이터 디렉토리 제거

```
sudo rm -rf /var/lib/postgresql/14/main/*
```

### 3) basebackup 수행

```
pg_basebackup \
  -h 192.168.80.130 \
  -D /var/lib/postgresql/14/main \
  -U repl \
  -Fp -Xs -P -R
```

📌 `-R` 옵션 → 자동으로 `standby.signal` 생성

### 4) PostgreSQL 시작

```
sudo systemctl start postgresql
```

---

## 8. 복제 상태 확인

### Primary에서

```
SELECT client_addr, state, sync_state
FROM pg_stat_replication;
```

### Standby에서

```
SELECT pg_is_in_recovery();
```

* `true` → Standby 정상

---

## 9. 장애 전환(Failover) 개념 정리

[![](https://www.enterprisedb.com/sites/default/files/DisplayImage8.png)](https://www.enterprisedb.com/sites/default/files/DisplayImage8.png)

### 수동 승격

```
sudo pg_ctlcluster 14 main promote
```

### 자동화 도구

* Patroni

* repmgr

* Pacemaker

---

## 10. MySQL 이중화와 비교

| 항목 | MySQL | PostgreSQL |
| --- | --- | --- |
| 로그 | Binary Log | WAL |
| 기본 복제 | 비동기 | 비동기 |
| 동기 복제 | 제한적 | 내장 지원 |
| Replica 읽기 | 가능 | 가능 |
| 승격 | RESET SLAVE | pg\_ctl promote |

---