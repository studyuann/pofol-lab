---
title: "MySQL · PostgreSQL 외부 접속 설정"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "데이터베이스", "RDB(Relational DataBase)"]
is_public: true
draft: false
---

# MySQL · PostgreSQL 외부 접속 설정

## 목적

* Ubuntu 서버에 설치된 DB에 외부 클라이언트(Workbench, pgAdmin, DBeaver 등)가 접속 가능하도록 설정

* 보안/운영 관점에서 **왜 이 설정이 필요한지** 이해

---

# 1. 전체 구조 한눈에 보기

| 구분 | MySQL | PostgreSQL |
| --- | --- | --- |
| 기본 포트 | 3306 | 5432 |
| 네트워크 수신 설정 | `bind-address` | `listen_addresses` |
| 인증/접근 제어 | 계정의 host(`'user'@'%'`) | `pg_hba.conf` |
| 설정 파일 수 | 1개 중심 | **2개 필수** |
| 초보자 난이도 | 낮음 | 상대적으로 높음 |
| 자주 나는 실수 | bind-address 미수정 | `pg_hba.conf` 누락 |

---

# 2. MySQL 외부 접속 설정

## 2-1. 설정 파일 위치

```
/etc/mysql/mysql.conf.d/mysqld.cnf
```

---

## 2-2. bind-address 설정

기본값(외부 접속 불가):

```
bind-address = 127.0.0.1
```

외부 접속 허용(교육/실습용):

```
bind-address = 0.0.0.0
```

> 의미

* `127.0.0.1` : 로컬 접속만 허용

* `0.0.0.0` : 모든 IPv4 인터페이스에서 접속 허용

---

## 2-3. 사용자 계정 host 설정 (매우 중요)

MySQL은 **계정 단위로 접속 위치를 제한**합니다.

### 예시: 외부 접속 가능한 계정

```
CREATE USER 'labuser'@'%' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON bootcamp_shop.* TO 'labuser'@'%';
FLUSH PRIVILEGES;
```

* `'%'` : 모든 IP 허용

* `'192.168.10.%’` : 특정 대역만 허용(운영 권장)

확인:

```
SELECT user, host FROM mysql.user;
```

---

## 2-4. 서비스 재시작

```
sudo systemctl restart mysql
```

---

## 2-5. 방화벽(UFW)

```
sudo ufw allow 3306/tcp
sudo ufw reload
```

---

## 2-6. 정상 동작 확인

```
sudo ss -lntp | grep 3306
```

정상 예:

```
LISTEN 0 151 0.0.0.0:3306
```

---

## 2-7. MySQL 외부 접속 실패 TOP 3

1. `bind-address`를 안 바꿈

2. 계정 host가 `'localhost'`로 되어 있음

3. 방화벽/보안그룹에서 3306 미허용

---

# 3. PostgreSQL 외부 접속 설정

> PostgreSQL은 “네트워크 수신”과 “인증/접근 제어”를 분리해서 관리
>
> → **파일 2개를 반드시 설정해야 함**

---

## 3-1. 설정 파일 위치

### ① 서버 수신 설정

```
/etc/postgresql/*/main/postgresql.conf
```

### ② 접속 허용/인증 규칙

```
/etc/postgresql/*/main/pg_hba.conf
```

---

## 3-2. listen\_addresses 설정 (`postgresql.conf`)

기본값:

```
#listen_addresses = 'localhost'
```

외부 접속 허용:

```
listen_addresses = '*'
```

또는

```
listen_addresses = '0.0.0.0'
```

> 의미

* `'*'` : 모든 IPv4/IPv6 인터페이스

* `'0.0.0.0'` : 모든 IPv4 인터페이스

---

## 3-3. 접속 허용 규칙 (`pg_hba.conf`)

### 형식

```
TYPE   DATABASE   USER   ADDRESS        METHOD
```

### 실습용(모든 IP 허용 ❌ 운영 비권장)

```
host    all    all    0.0.0.0/0    scram-sha-256
```

### 운영 권장 예시(특정 DB + 사용자 + 대역)

```
host    bootcamp_shop    labuser    203.0.113.0/24    scram-sha-256
```

> PostgreSQL은 여기서 허용하지 않으면 절대 접속 불가
>
> → `listen_addresses`만 바꾸고 안 되는 이유의 90%

---

## 3-4. 서비스 재시작

```
sudo systemctl restart postgresql
```

---

## 3-5. 방화벽(UFW)

```
sudo ufw allow 5432/tcp
sudo ufw reload
```

---

## 3-6. 정상 동작 확인

```
sudo ss -lntp | grep 5432
```

정상 예:

```
LISTEN 0 244 0.0.0.0:5432
```

PostgreSQL 내부 확인:

```
sudo -u postgres psql
```

```
SHOW listen_addresses;
```

---

## 3-7. PostgreSQL 외부 접속 실패 TOP 3

1. `pg_hba.conf` 설정 누락

2. IP 대역 오타 (`/32` vs `/24`)

3. 설정 변경 후 재시작 안 함

---

# 4. MySQL vs PostgreSQL 외부 접속 핵심 비교 요약

| 항목 | MySQL | PostgreSQL |
| --- | --- | --- |
| 네트워크 설정 | bind-address 1개 | listen\_addresses |
| 인증/허용 | 계정 host | **pg\_hba.conf** |
| 설정 난이도 | 쉬움 | 상대적으로 복잡 |
| 실무 유연성 | 보통 | 매우 높음 |
| 보안 통제 정밀도 | 중 | 높음 |

---

# 5. Mysql vs Postgresql

> MySQL은 bind-address + 계정 host
>
> **PostgreSQL은 listen\_addresses + pg\_hba.conf**

---

# 6. 운영 관점 주의사항 (공통)

* DB 포트를 **0.0.0.0/0으로 여는 것은 교육용만 허용**

* 운영 환경에서는:
  + 특정 IP만 허용
  + 프라이빗 서브넷 배치
  + 보안그룹 + 방화벽 이중 제어

* root/superuser 외부 접속 지양

* 비밀번호는 코드/문서에 남기지 않기(Secrets Manager 등)

---

# 7. 외부 접속 안 될 때 점검 체크리스트

### MySQL

* mysqld 실행 중

* bind-address = 0.0.0.0

* user@'%' 또는 허용 IP

* 3306 방화벽 허용

### PostgreSQL

* postgres 실행 중

* listen\_addresses 설정

* pg\_hba.conf 허용 규칙

* 5432 방화벽 허용

---