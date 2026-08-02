---
title: "MongoDB 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "데이터베이스"]
is_public: true
draft: false
---

# MongoDB 실습

# 1장. MongoDB 설치 및 기본 실습

---

## 1-1. 실습 환경

| 항목 | 내용 |
| --- | --- |
| OS | Ubuntu 22.04 LTS (jammy) |
| 권한 | sudo 사용자 |
| 네트워크 | 인터넷 연결 필수 |
| MongoDB 버전 | 8.0 |

---

## 1-2. MongoDB 공식 GPG 키 등록 (정석)

### 필수 패키지 설치

```
sudo apt update
sudo apt install -y gnupg curl
```

### MongoDB 공식 GPG 키 등록

```
curl -fsSL https://www.mongodb.org/static/pgp/server-8.0.asc \
| sudo gpg --dearmor -o /usr/share/keyrings/mongodb-server-8.0.gpg
```

### 확인

```
ls -l /usr/share/keyrings/mongodb-server-8.0.gpg
```

➡️ 파일이 존재하면 정상

---

## 1-3. MongoDB APT 저장소 등록 (signed-by 필수)

```
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] \
https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/8.0 multiverse" \
| sudo tee /etc/apt/sources.list.d/mongodb-org-8.0.list
```

---

## 1-4. MongoDB 설치

```
sudo apt update
sudo apt install -y mongodb-org
```

### 설치 확인

```
mongod --version
```

* 버전 정보 출력되면 성공

---

## 1-5. MongoDB 서비스 기동

```
sudo systemctl enable --now mongod
systemctl status mongod --no-pager
```

### 접속 테스트

```
mongosh --eval 'db.runCommand({ ping: 1 })'
```

```
{ ok: 1 }
```

* 출력되면 정상 동작

---

## 1-6. MongoDB 기본 개념 실습 준비

```
mongosh
```

```
use lab
db.customers.drop()
db.orders.drop()
```

---

## 1-7. customers 컬렉션 샘플 데이터

```
db.customers.insertMany([
  { customerId: 1, name: "Kim",  region: "seoul", tier: "gold" },
  { customerId: 2, name: "Lee",  region: "busan", tier: "silver" },
  { customerId: 3, name: "Park", region: "seoul", tier: "gold" },
  { customerId: 4, name: "Choi", region: "incheon", tier: "bronze" }
])
```

### 확인

```
db.customers.find()
```

---

## 1-8. orders 컬렉션 (JOIN 제거 설계)

> ❗ MongoDB에서는 JOIN 대신 중첩 구조 설계

```
db.orders.insertMany([
  {
    orderId: 1001,
    status: "PAID",
    orderedAt: ISODate("2026-01-01"),
    customer: { name: "Kim", region: "seoul" },
    amount: 120000
  },
  {
    orderId: 1002,
    status: "CART",
    orderedAt: ISODate("2026-01-05"),
    customer: { name: "Lee", region: "busan" },
    amount: 99000
  },
  {
    orderId: 1003,
    status: "PAID",
    orderedAt: ISODate("2026-01-10"),
    customer: { name: "Park", region: "seoul" },
    amount: 150000
  }
])
```

---

## 1-9. SQL ↔ MongoDB 쿼리 대응 실습

## SELECT / WHERE

### SQL

```
SELECT name, tier
FROM customers
WHERE tier = 'gold';
```

### MongoDB

```
db.customers.find(
  { tier: "gold" },
  { _id: 0, name: 1, tier: 1 }
)
```

---

## ORDER BY / LIMIT

```
db.orders.find(
  { status: "PAID" },
  { _id: 0, orderId: 1, amount: 1, orderedAt: 1 }
).sort({ orderedAt: -1 }).limit(5)
```

---

## GROUP BY (Aggregation)

### SQL

```
SELECT customer, SUM(amount)
FROM orders
WHERE status = 'PAID'
GROUP BY customer;
```

### MongoDB

```
db.orders.aggregate([
  { $match: { status: "PAID" } },
  {
    $group: {
      _id: "$customer.name",
      totalAmount: { $sum: "$amount" }
    }
  }
])
```

---

## 1-10. Projection 규칙

### ❌ 잘못된 예

```
{ name: 1, tier: 1, region: 0 }
```

### ✔ 올바른 방식

```
{ _id: 0, name: 1, tier: 1 }
```

### 핵심 규칙

* 포함 or 제외 중 하나만 사용

* `_id`만 예외적으로 제외 가능

---

## 1-11. 인덱스 & 성능 실습

## 인덱스 없이 실행계획

```
db.orders.find({ status: "PAID" }).explain("executionStats")
```

확인 포인트:

* `COLLSCAN`

* `totalDocsExamined`

---

## 인덱스 생성

```
db.orders.createIndex({ status: 1, orderedAt: -1 })
```

---

## 인덱스 후 재확인

```
db.orders.find({ status: "PAID" })
  .sort({ orderedAt: -1 })
  .explain("executionStats")
```

* `IXSCAN`으로 변경 확인

---

# 2. Ubuntu 서버 3대로 MongoDB Replica Set(HA) 실습

## 2-0. 실습 토폴로지

---

예시(수정 가능):

* 서버1: `mongo1` (IP: `192.168.80.110`)

* 서버2: `mongo2` (IP: `192.168.80.120`)

* 서버3: `mongo3` (IP: `192.168.80.130`)

Replica Set 이름: `rs0`

모든 노드: **Data node (Primary/Secondary)**

---

## 2-1. 실습 목표

1. Replica Set에서 **PRIMARY/SECONDARY** 구조 설명

2. 선출(election)이 왜 필요한지(과반수) 설명

3. Primary 다운 시 **자동 Failover** 확인

4. `rs.status()`, `db.hello()`로 상태 점검 가능

---

## 2-2. 사전 준비 (3대 공통)

### (1) 시간 동기화(권장)

```
sudo apt update
sudo apt install -y chrony
sudo systemctl enable --now chrony
timedatectl
```

### (2) 호스트 해석 설정 (/etc/hosts 권장)

3대 모두 동일하게 추가:

```
sudo tee -a /etc/hosts >/dev/null <<'EOF'
192.168.80.110 mongo1
192.168.80.120 mongo2
192.168.80.130 mongo3
EOF
```

확인:

```
getent hosts mongo1 mongo2 mongo3
```

### (3) 통신 확인 (서로 ping)

예: mongo1에서

```
ping -c 2 mongo2
ping -c 2 mongo3
```

---

## 2-3. MongoDB 설치 (3대 공통)

> 1장에서 했던 설치 방식과 동일.

```
sudo rm -f /etc/apt/sources.list.d/mongodb-org-*.list
sudo rm -f /usr/share/keyrings/mongodb-*.gpg

sudo apt update
sudo apt install -y gnupg curl

curl -fsSL https://www.mongodb.org/static/pgp/server-8.0.asc \
| sudo gpg --dearmor -o /usr/share/keyrings/mongodb-server-8.0.gpg

echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] \
https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/8.0 multiverse" \
| sudo tee /etc/apt/sources.list.d/mongodb-org-8.0.list

sudo apt update
sudo apt install -y mongodb-org
```

버전 확인:

```
mongod --version
mongosh --version
```

---

## 2-4. Replica Set 설정 (3대 공통)

### (1) mongod 설정 백업

```
sudo cp /etc/mongod.conf /etc/mongod.conf.bak
```

### (2) `/etc/mongod.conf` 수정 (중요)

아래 항목이 **반드시** 들어가야 함:

```
# /etc/mongod.conf

net:
  port: 27017
  bindIp: 0.0.0.0   # 실습용 (운영에서는 내부망 IP로 제한 권장)

replication:
  replSetName: rs0
```

### (3) 서비스 재시작

```
sudo systemctl enable --now mongod
sudo systemctl restart mongod
sudo systemctl status mongod --no-pager
```

---

## 2-5. 방화벽(UFW) 사용 시 포트 허용 (방화벽 사용시)

UFW를 켜둔 환경이라면 3대 모두에서(내부망만 허용)

```
sudo ufw allow from 10.0.0.0/24 to any port 27017 proto tcp
sudo ufw status
```

---

## 2-6. Replica Set 초기화 (mongo1에서만)

### (1) mongo1에서 접속

```
mongosh
```

### (2) rs.initiate 실행

```
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "mongo1:27017" },
    { _id: 1, host: "mongo2:27017" },
    { _id: 2, host: "mongo3:27017" }
  ]
})
```

### (3) 상태 확인

```
rs.status()
```

확인 :

* members 3개가 보이는지

* `stateStr`가 PRIMARY 1개, SECONDARY 2개인지

---

## 2-7. Primary/Secondary 확인 실습

mongo1에서:

```
db.hello()
```

출력 포인트:

* `isWritablePrimary: true` 인 노드가 PRIMARY

다른 노드에서도 확인(각 서버에서 mongosh 실행):

```
mongosh --eval 'db.hello()'
```

---

## 2-8. 데이터 쓰기/복제 확인

### (1) Primary에서 쓰기

(현재 PRIMARY인 서버에서 실행)

```
use lab
db.replica_test.insertMany([
  { msg: "write1", ts: new Date() },
  { msg: "write2", ts: new Date() }
])
db.replica_test.find()
```

### (2) Secondary에서 읽기(읽기 허용 필요)

Secondary 노드에서:

```
mongosh
```

```
rs.secondaryOk()
use lab
db.replica_test.find()
```

확인 :

* Primary에 쓴 데이터가 Secondary에서도 보이면 복제 OK

---

## 2-9. 장애 시뮬레이션: Primary 다운 → Failover 확인 (핵심)

### (1) 현재 Primary가 누구인지 확인

아무 노드에서나:

```
rs.status().members.map(m => ({name:m.name, stateStr:m.stateStr}))
```

예: Primary가 mongo1이라고 가정

### (2) Primary 서버에서 mongod 중지

**Primary 서버에서**:

```
sudo systemctl stop mongod
```

### (3) 다른 서버에서 선출 결과 확인

예: mongo2에서

```
mongosh --eval 'rs.status().members.map(m => ({name:m.name, stateStr:m.stateStr}))'
```

확인 포인트:

* mongo2 또는 mongo3가 **PRIMARY로 승격**

* 대체로 수 초 내 변경

---

## 2-10. Failover 후 “쓰기”가 되는지 확인

새 Primary가 된 노드에서:

```
mongosh
```

```
use lab
db.replica_test.insertOne({ msg: "after_failover", ts: new Date() })
db.replica_test.find().sort({ ts: -1 }).limit(5)
```

* “장애가 나도 서비스는 계속된다”를 체감시키는 구간

---

## 2-11. 다운된 노드 복구 및 재동기화 확인

아까 내렸던 서버(예: mongo1)에서:

```
sudo systemctl start mongod
```

다른 노드에서 상태 확인:

```
mongosh --eval 'rs.status().members.map(m => ({name:m.name, stateStr:m.stateStr}))'
```

확인 :

* 복구된 노드는 보통 **SECONDARY**로 합류

* 데이터가 자동 동기화됨

---

## MongoDB Replica Set에서 **남은 노드 중 누가 Primary가 되는 기준**

[![](https://www.xuchao.org/docs/mongodb/_images/replica-set-trigger-election.bakedsvg.svg)](https://www.xuchao.org/docs/mongodb/_images/replica-set-trigger-election.bakedsvg.svg)[![](https://www.mongodb.com/docs/manual/images/replica-set-trigger-election.bakedsvg.svg)](https://www.mongodb.com/docs/manual/images/replica-set-trigger-election.bakedsvg.svg)

---

> **Election에서 Primary가 되는 노드는“가장 최신 데이터 + 과반수 지지 + (설정상) 우선순위가 높은 노드”다.**

아래 **조건을 통과한 노드만 후보**가 되고, 그중 **투표로 결정**.

---

## 1) 1차 조건: 살아 있고 통신 가능해야 한다

당연하지만 가장 먼저 봅니다.

* 프로세스 정상 동작

* 다른 노드들과 네트워크 통신 가능

❌ 죽어 있거나

❌ 네트워크로 고립된 노드는 **후보 탈락**

---

## 2) 2차 조건: 데이터가 “최신”이어야 한다 (가장 중요)

### 🔑 기준: **oplog 동기화 상태**

MongoDB는 각 노드에 \*\*oplog(작업 로그)\*\*를 유지합니다.

Election 시 비교하는 것:

* “이 노드가 **Primary의 마지막 쓰기까지 따라왔는가?**”

### 결과

* 최신 oplog를 가진 노드 → **후보 가능**

* 한참 뒤처진 노드 → **후보 탈락**

👉 **이게 가장 결정적인 기준**

---

## 3) 3차 조건: priority 설정 (관리자가 정한 우선순위)

Replica Set 멤버에는 `priority` 값이 있다.

```
rs.conf().members
```

기본값:

```
priority: 1
```

### 예시

```
mongo1 priority: 2
mongo2 priority: 1
mongo3 priority: 0.5
```

* **priority가 높은 노드가 Primary가 될 가능성이 큼**

> ⚠️ 단, **priority가 높아도 데이터가 최신이 아니면 탈락**

---

## 4) 4차 조건: 과반수 투표 확보

후보가 되었다고 끝이 아님.

* Replica Set 전체 투표 수의 **과반수(majority)** 필요

예: 3대 구성

* 과반수 = 2표

👉 **자기 자신 1표 + 다른 노드 1표 이상**

---

## 5) 실제 Election 흐름을 예로 보면

### 상황

* mongo1 (Primary) ❌ 다운

* mongo2, mongo3 살아 있음

### Step-by-step

1. mongo2, mongo3가 Primary 다운 감지

2. mongo2가 후보 선언

3. mongo3가 확인:
   * mongo2 살아 있음? ⭕
   * oplog 최신? ⭕
   * 이미 투표했나? ❌

4. mongo3 → mongo2에게 1표

5. **mongo2 과반수 확보 → Primary 승격**

* mongo3는 Secondary 유지

---

## 6) “그럼 둘 다 최신이면?”

우선순위:

1. **priority 값**

2. Election 타이밍(먼저 요청한 쪽)

3. 내부 타이브레이커(임의성)

👉 그래서 **priority를 명시적으로 주면 예측 가능**

---

## 7) 권장 패턴

* Primary가 되길 원하는 노드 → `priority` 높게

* 절대 Primary가 되면 안 되는 노드 → `priority: 0`

```
rs.reconfig({
  _id: "rs0",
  members: [
    { _id: 0, host: "mongo1:27017", priority: 2 },
    { _id: 1, host: "mongo2:27017", priority: 1 },
    { _id: 2, host: "mongo3:27017", priority: 0 }
  ]
})
```

* mongo3는 **절대 Primary가 안 됨**

---

## 점검 명령 모음

* 전체 상태 요약:

```
rs.status().members.map(m => ({name:m.name, health:m.health, stateStr:m.stateStr}))
```

* 내가 Primary인지:

```
db.hello().isWritablePrimary
```

* Secondary 읽기 허용:

```
rs.secondaryOk()
```

---