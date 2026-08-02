---
title: "MySQL 이중화"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "데이터베이스", "RDB(Relational DataBase)"]
is_public: true
draft: false
---

# MySQL 이중화

## 1. MySQL 이중화란 무엇인가?

**MySQL 이중화 = Replication**

* **Primary(Master)** : 쓰기(INSERT/UPDATE/DELETE)

* **Replica(Slave)** : 읽기(SELECT), 백업, 장애 대비

* **Binary Log(binlog)** 기반으로 데이터 변경사항 전달

> 핵심 포인트
>
> * 고가용성(HA) ≠ 자동 장애조치
>
> * 부하 분산, 데이터 보호, 읽기 확장

---

## 2. MySQL 이중화 기본 구조

[![](MySQL%20%EC%9D%B4%EC%A4%91%ED%99%94/image.png)](MySQL%20%EC%9D%B4%EC%A4%91%ED%99%94/image.png)

### 구조 요약

```
[ Client ]
    |
    v
[ Primary ]
  - binlog 기록
    |
    v
[ Replica ]
  - relay log
  - read only
```

---

## 3. 이중화 방식 종류

### ① Single Primary – Replica (가장 기본)

* 실습용 / 교육용 **최적**

* 대부분의 회사에서 기본으로 사용

### ② Primary – Multiple Replicas

* 읽기 부하 분산

* 리포트/백업 전용 Replica 분리

### ③ Dual Primary (Master–Master)

* **주의 필요**

* 충돌 관리 필요 (`auto_increment_offset`)

* 실무에서는 제한적으로 사용

---

## 4. 실습 환경 구성 (강의 추천)

### VM 구성 예시

| 서버 | 역할 | IP |
| --- | --- | --- |
| mysql1 | Primary | 192.168.80.110 |
| mysql2 | Replica | 192.168.80.120 |

* OS: Ubuntu 22.04

* MySQL 8.0

* 포트: 3306

---

## 5. Primary 서버 설정 (실습)

### ① MySQL 설정 수정

```
sudo vi /etc/mysql/mysql.conf.d/mysqld.cnf
```

```
[mysqld]
server-id=1
log-bin=mysql-bin
binlog_format=ROW
```

```
sudo systemctl restart mysql
```

---

### ② Replication 전용 계정 생성

```
CREATE USER 'repl'@'%' IDENTIFIED BY 'repl1234';
GRANT REPLICATION SLAVE ON *.* TO 'repl'@'%';
FLUSH PRIVILEGES;
```

---

### ③ 현재 binlog 위치 확인 ⭐

```
SHOW MASTER STATUS;
```

출력 예시:

```
File: mysql-bin.000001
Position: 157
```

* **이 값이 Replica 설정에 필요**

---

## 6. Replica 서버 설정 (실습)

### ① MySQL 설정

```
[mysqld]
server-id=2
relay-log=relay-bin
read_only=ON
```

```
sudo systemctl restart mysql
```

---

### ② Replication 연결 설정

```
CHANGE MASTER TO
  MASTER_HOST='192.168.56.101',
  MASTER_USER='repl',
  MASTER_PASSWORD='repl1234',
  MASTER_LOG_FILE='mysql-bin.000001',
  MASTER_LOG_POS=157;
```

```
START REPLICA;
```

---

### ③ 상태 확인 (중요 ⭐)

```
SHOW REPLICA STATUS\G
```

아래 두 값이 **Yes**여야 정상

```
Slave_IO_Running: Yes
Slave_SQL_Running: Yes
```

---

## 7. 동작 검증 실습

### Primary에서 데이터 생성

```
CREATE DATABASE repl_test;
USE repl_test;

CREATE TABLE users (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(50)
);

INSERT INTO users (name) VALUES ('Alice'), ('Bob');
```

### Replica에서 확인

```
USE repl_test;
SELECT * FROM users;
```

* **자동으로 데이터 동기화됨**

---

## 8. 장애 상황 시나리오

### ❗ Primary 장애 발생 시

* Replica는 **자동 승격 안 됨**

* 수동 조치 필요 : 쓰기 가능한 상태로 변경 후 REPLICA 동작을 멈추고 Primary 설정을 해야함.

```
STOP SLAVE;
SET GLOBAL read_only = OFF;
```

* **이게 MySQL Replication의 한계**

* **REPLICA 동작 중지 및 REPLICA 설정 초기화**

```
REPLICA STOP;
RESET REPLICA ALL;
```

---

## 9. 실무에서는 이렇게 확장된다

[![](https://www.haproxy.com/assets/posts/haproxy_mysql_replication.png)](https://www.haproxy.com/assets/posts/haproxy_mysql_replication.png)[![](https://severalnines.com/sites/default/files/blog/node_4620/image08.png)](https://severalnines.com/sites/default/files/blog/node_4620/image08.png)

### 실무 구성

```
Client
  |
[ HAProxy ]
  ├── Write → Primary
  └── Read  → Replicas
```