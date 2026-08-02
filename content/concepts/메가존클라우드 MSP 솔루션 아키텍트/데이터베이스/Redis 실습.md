---
title: "Redis 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "데이터베이스"]
is_public: true
draft: false
---

# Redis 실습

## 0. 실습 목표 및 환경

### 목표

1. Ubuntu에 Redis 설치 및 서비스 운영(systemd)

2. `redis-cli`로 핵심 명령 실습(STRING/LIST/SET/HASH/ZSET)

3. TTL/캐시 패턴(캐시 미스/갱신/무효화) 이해

4. RDB/AOF 영속화 설정 및 복구 실습

5. 외부 노출 시 필수 보안 설정(바인딩/비밀번호/방화벽)

6. 운영 관점 점검(로그/메모리/Slowlog/지표)

### 준비물

* Ubuntu VM 1대 (권장: 2 vCPU / 2GB RAM 이상)

* sudo 권한

* 터미널 사용

---

## 1. Redis 설치 및 서비스 확인

### 1-1) 패키지 설치

```
sudo apt update
sudo apt install -y redis-server
```

### 1-2) 서비스 상태 확인

```
sudo systemctl status redis-server --no-pager
```

### 1-3) Redis 버전/접속 테스트

```
redis-server --version
redis-cli ping
```

* 기대 출력: `PONG`

### 1-4) 포트 리스닝 확인(기본 6379)

```
ss -lntp | grep 6379 || sudo lsof -i:6379
```

---

## 2. redis-cli 기본 사용법

### 2-1) 접속

```
redis-cli
```

### 2-2) 도움말/명령 탐색

```
HELP
COMMAND COUNT
COMMAND INFO GET SET
```

### 2-3) 서버 정보/설정 확인

```
INFO
INFO server
INFO memory
CONFIG GET *
CONFIG GET dir
CONFIG GET appendonly   => AOF기능 활성화 여부 확인
```

### 2-4) 키 탐색 주의

운영에서는 `KEYS *` 금지(블로킹). 실습에서는 데이터가 적으므로 비교 용도만.

```
KEYS *
SCAN 0 MATCH * COUNT 10    => 10개씩 조회
```

---

## 3. Redis 데이터 모델(자료구조) 실습

---

### 실습 전, 데이터 초기화

```
FLUSHDB   : 현재 DB 삭제
FLUSHALL  : 모든 DB 삭제
```

**설명**

* 현재 선택된 Redis DB(기본 0번)에 저장된 모든 키를 삭제. DB는 0~15까지 16개가 있음.

* 실습을 처음부터 깨끗한 상태로 시작하기 위함

* `FLUSHALL`은 모든 DB를 삭제하므로 실습에서는 `FLUSHDB` 권장

---

 [[Redis 데이터모델]] 

## 3-1) STRING

```
SET user:1:name "kim"
```

* `user:1:name`이라는 키에 문자열 `"kim"` 저장

* 동일한 키가 있으면 **덮어쓰기**

```
GET user:1:name
```

* 해당 키에 저장된 값을 조회

* 결과: `"kim"`

---

```
INCR page:view
```

* `page:view` 값을 **1 증가**

* 키가 없으면 `0`으로 간주한 뒤 `1`로 생성

* 문자열 타입이지만 **숫자 형태의 문자열**이어야 함

* 한 번 더 증가 → 누적 증가 확인

```
INCR page:view
```

* 현재 조회수(카운터) 값 확인

```
GET page:view
```

---

* 여러 키를 **한 번에 저장**

* 내부적으로 원자적(atomic)으로 실행

```
MSET k1 v1 k2 v2
```

* 여러 키를 한 번에 조회

* 결과는 입력한 순서대로 반환

```
MGET k1 k2
```

---

### 실습

* `SET counter 0` 실행

* `INCR counter`를 5회 실행

* 최종 값이 `5`인지 확인

  👉 **조회수, 접속 수 카운터에 사용되는 패턴**

---

## 3-2) LIST (큐 / 스택)

* 기존 리스트 키 삭제 (실습 재실행 대비)

```
DEL queue:email
```

* 리스트 **왼쪽(Head)** 에 데이터 삽입

* 여러 값일 경우 왼쪽부터 순차 삽입

* 최종 순서: `mail3 → mail2 → mail1`

```
LPUSH queue:email "mail1" "mail2" "mail3"
```

* 리스트 전체 조회

* `0` = 첫 번째, `1` = 마지막

```
LRANGE queue:email 0 -1
```

---

* 리스트 **오른쪽(Tail)** 에서 데이터 하나 제거 후 반환

* 큐(FIFO) 구조에서 **꺼내기** 동작

```
RPOP queue:email
```

* pop 이후 남은 데이터 확인

```
LRANGE queue:email 0 -1
```

---

### 블로킹 POP (워크 큐 스타일)

### 터미널 A

```
redis-cli
```

* `queue:job` 리스트에 값이 들어올 때까지 **대기**

* `0`은 무한 대기 의미

* 작업 큐(worker) 구현 시 사용

```
BLPOP queue:job 0
```

### 터미널 B

```
redis-cli
```

```
LPUSH queue:job "job1"
```

* 값이 들어오는 순간, 터미널 A가 즉시 값을 받음

---

### 과제

* `RPUSH`로 데이터 추가

* `LPOP`으로 데이터 제거

* **FIFO 큐 구조 직접 구성해보기**

---

## 3-3) SET (중복 없는 집합)

* 집합에 값 추가

* `"kim"`은 중복이므로 **한 번만 저장**

```
SADD class:students "kim" "lee" "park" "kim"
```

* 집합에 저장된 모든 값 조회

* **순서는 보장되지 않음**

```
SMEMBERS class:students
```

* `"kim"`이 집합에 있는지 확인

* 결과: `1`(있음), `0`(없음)

```
SISMEMBER class:students "kim"
```

* 집합에 포함된 원소 개수 반환

```
SCARD class:students
```

* `"park"`를 집합에서 제거

```
SREM class:students "park"
```

* 제거 후 최종 상태 확인

```
SMEMBERS class:students
```

---

### 집합 연산

* 두 개의 집합 생성

```
SADD class:A "kim" "lee"
SADD class:B "lee" "choi"
```

* 교집합 (공통 요소) → `"lee"`

```
SINTER class:A class:B
```

* 합집합 (전체 요소)

```
SUNION class:A class:B
```

* 차집합 (A에는 있고 B에는 없는 값)

```
SDIFF class:A class:B
```

---

## 3-4) HASH (객체 / 레코드)

* 하나의 키(`user:1`)에 여러 필드-값 저장

* 객체(JSON)와 유사한 구조

```
HSET user:1 name "kim" age "29" role "student"
```

* 특정 필드 값만 조회

```
HGET user:1 name
```

* 해당 키의 모든 필드와 값 조회

```
HGETALL user:1
```

* `login_count` 필드를 1 증가

* 필드가 없으면 `0`으로 간주 후 증가

```
HINCRBY user:1 login_count 1
```

* 누적 증가 확인

```
HINCRBY user:1 login_count 1
```

* 최종 로그인 횟수 조회

```
HGET user:1 login_count
```

---

### 과제

* `user:2` 생성

* 필드 3개 이상 저장(job:sa, team:cloud, floor:3

* `HGETALL user:2` 결과 확인

---

## 3-5) ZSET (정렬된 집합: 랭킹 / 점수)

* `ranking`이라는 ZSET에 데이터 추가

* 숫자(score)를 기준으로 자동 정렬됨

```
ZADD ranking 100 "alice" 80 "bob" 120 "chris"
```

* **점수 오름차순** 정렬 결과 조회

```
ZRANGE ranking 0 -1 WITHSCORES
```

* **점수 내림차순** 정렬 결과 조회 (랭킹용)

```
ZREVRANGE ranking 0 -1 WITHSCORES
```

---

* `"bob"`의 점수를 `+30` 증가

```
ZINCRBY ranking 30 "bob"
```

* 점수 변경 후 순위 자동 재정렬 확인

```
ZREVRANGE ranking 0 -1 WITHSCORES
```

---

### Top-N 조회

* 점수가 높은 순으로 **상위 3개** 조회

* Top-N 랭킹 조회의 대표적인 패턴

```
ZREVRANGE ranking 0 2 WITHSCORES
```

---

## 4. TTL과 캐시 동작 이해

### 4-1) TTL 기본

* 세션 데이터 저장

```
SET session:abc "user1"
```

* 60초 뒤 자동 삭제 설정

```
EXPIRE session:abc 60
```

* 남은 TTL 시간(초 단위) 확인

```
TTL session:abc
```

* TTL 만료 전이면 값 반환

* 만료 후면 `(nil)` 반환

```
GET session:abc
```

---

### 4-2) SETEX / PSETEX

* 값을 저장하면서 TTL(초) 동시에 설정

```
SETEX otp:001 30 "123456"
```

* 남은 시간 확인

```
TTL otp:001
```

* TTL을 **밀리초(ms)** 단위로 설정

```
PSETEX otp:ms 5000 "999999"
```

* 남은 시간을 ms 단위로 확인

```
PTTL otp:ms
```

---

### 4-3) 캐시 패턴 실습 (수동 시뮬레이션)

**상황: DB 조회 결과를 Redis에 10초 캐싱**

* 기존 캐시 삭제

```
DEL cache:product:100
```

* 값 없음 → **캐시 미스(Cache Miss)**

```
GET cache:product:100
```

* DB 조회 결과를 Redis에 저장

```
SET cache:product:100 "{'name':'mouse','price':12000}"
```

* 10초 뒤 자동 삭제

```
EXPIRE cache:product:100 10
```

* 캐시 만료까지 남은 시간 확인

```
TTL cache:product:100
```

* TTL 만료 전 → **캐시 히트(Cache Hit)**

```
GET cache:product:100
```

---

**과제**

* TTL 만료 후 다시 GET 했을 때 값을 확인하고, 재캐싱을 수행하시오.

---

## 5. 영속화(Persistence): RDB / AOF

Redis 설정 파일 위치(우분투 패키지 기본):

* `/etc/redis/redis.conf`

* 데이터 디렉터리: 보통 `/var/lib/redis`

### 5-1) 현재 설정 확인

```
sudo grep -E "^(save|appendonly|appendfsync|dir|dbfilename)" /etc/redis/redis.conf
sudo egrep "^(save|appendonly|appendfsync|dir|dbfilename)" /etc/redis/redis.conf
```

또는 redis-cli에서:

```
redis-cli CONFIG GET save
redis-cli CONFIG GET appendonly
redis-cli CONFIG GET dir
```

---

### 5-2) RDB 스냅샷(기본)

수동 저장:

```
redis-cli SAVE
```

백그라운드 저장:

```
redis-cli BGSAVE
```

RDB 파일 위치 확인:

```
redis-cli CONFIG GET dir
redis-cli CONFIG GET dbfilename
sudo ls -al /var/lib/redis
```

**복구 실습(안전하게 진행)**

1. 샘플 데이터 생성

```
redis-cli FLUSHDB
redis-cli SET rdb:test "hello"
redis-cli BGSAVE
```

1. Redis 중지 후 데이터 파일 확인

```
sudo systemctl stop redis-server
sudo ls -al /var/lib/redis
```

1. Redis 재시작 후 데이터 확인

```
sudo systemctl start redis-server
redis-cli GET rdb:test
```

---

### 5-3) AOF 활성화(권장: 데이터 중요 시)

1. 설정 변경

```
sudo cp /etc/redis/redis.conf /etc/redis/redis.conf.bak
sudo sed -i 's/^appendonly no/appendonly yes/' /etc/redis/redis.conf
sudo sed -i 's/^# appendfsync everysec/appendfsync everysec/' /etc/redis/redis.conf
```

1. 서비스 재시작

```
sudo systemctl restart redis-server
```

1. AOF 파일 생성 확인

```
sudo ls -al /var/lib/redis
redis-cli CONFIG GET appendonly
```

**AOF 재작성(압축)**

```
redis-cli BGREWRITEAOF
```

**과제**

* AOF 켠 상태에서 키 3개 저장 후 재시작해도 남아있는지 검증

---

## 6. 운영 관점 필수 점검(메모리/모니터링/슬로우로그)

### 6-1) 메모리 확인

```
INFO memory
MEMORY STATS
MEMORY USAGE user:1
```

### 6-2) 실시간 모니터링(주의: 운영에서 과다 사용 금지)

```
redis-cli MONITOR
```

### 6-3) Slowlog

```
CONFIG SET slowlog-log-slower-than 10000
CONFIG SET slowlog-max-len 128
SLOWLOG LEN
SLOWLOG GET 10
```

### 6-4) 클라이언트/연결 확인

```
INFO clients
CLIENT LIST
```

---

## 7. 보안 기본(실습 환경 기준)

### 7-1) 기본 바인딩/접근 제한 확인

```
sudo grep -E "^(bind|protected-mode|requirepass)" /etc/redis/redis.conf
```

* 실습 로컬에서만 쓸 거면: `bind 127.0.0.1 ::1` 유지 권장

* 외부 접속 허용은 매우 신중(비밀번호 + 방화벽 + 네트워크 분리 전제)

### 7-2) 비밀번호 설정(requirepass)

```
sudo sed -i 's/^# requirepass .*/requirepass StrongPassw0rd!/' /etc/redis/redis.conf
sudo systemctl restart redis-server
```

접속 테스트:

```
redis-cli ping
# (NOAUTH 에러 기대)
redis-cli -a 'StrongPassw0rd!' ping
```

### 7-3) UFW 방화벽(외부 차단)

```
sudo ufw status
sudo ufw allow OpenSSH
sudo ufw enable
sudo ufw deny 6379/tcp
sudo ufw status
```

---

## 8. 복제(Replication) 실습: 2대 VM 또는 2개 인스턴스

아래는 **노션에 그대로 붙여넣기 가능한 Redis Master–Replica 복제 실습 교안**입니다.

(우분투 기준, 2대 VM 또는 1대에서 포트만 다르게 2인스턴스 모두 제공)

---

## 0. 실습 준비

## 권장 환경

* Ubuntu 22.04 서버 2대 (또는 1대에서 2인스턴스)

* IP 예시
  + Master: `192.168.80.110`
  + Replica: `192.168.80.120`

## 포트

* 기본: `6379`

---

## 1) Redis 설치 (두 서버 모두)

```
sudo apt update
sudo apt install -y redis-server
redis-server --version
```

서비스 상태 확인:

```
sudo systemctl status redis-server --no-pager
```

---

## 2) 방화벽/네트워크 확인 (두 서버 모두)

UFW를 쓰는 경우(예시):

```
sudo ufw allow 6379/tcp
sudo ufw status
```

서로 통신 확인(Replica → Master):

```
nc -zv 192.168.80.110 6379
```

---

## 3) Master 설정 (192.168.80.110)

설정 파일:

```
sudo vi /etc/redis/redis.conf
```

아래 항목을 찾아 수정/확인:

```
bind 0.0.0.0
port 6379

protected-mode yes

requirepass StrongPassw0rd!

# (선택) 실습 중 위험 명령 막기 - 운영용 권장
# rename-command FLUSHALL ""
# rename-command FLUSHDB  ""
```

재시작:

```
sudo systemctl restart redis-server
```

외부 접속 확인(로컬에서):

```
redis-cli -a StrongPassw0rd! PING
# PONG
```

Master 역할 확인:

```
redis-cli -a StrongPassw0rd! INFO replication | egrep "role|connected_slaves"
# role:master
# connected_slaves:0
```

---

## 4) Replica 설정 (192.168.80.120)

설정 파일:

```
sudo vi /etc/redis/redis.conf
```

아래 항목을 찾아 수정/확인:

```
bind 0.0.0.0
port 6379

protected-mode yes

requirepass StrongPassw0rd!

# Master 인증 (Master에 requirepass가 있을 때 필수)
masterauth StrongPassw0rd!

# 복제 대상 지정 (중요)
replicaof 192.168.80.110 6379
```

재시작:

```
sudo systemctl restart redis-server
```

Replica 역할 확인:

```
redis-cli -a StrongPassw0rd! INFO replication | egrep "role|master_host|master_link_status"
```

정상 출력 예:

```
role:slave
master_host:192.168.80.110
master_link_status:up
```

Master에서 Replica 연결 확인:

```
redis-cli -a StrongPassw0rd! INFO replication | egrep "connected_slaves|slave0"
```

---

## 5) 복제 동작 확인

## 5-1) Master에 데이터 쓰기

Master에서:

```
redis-cli -a StrongPassw0rd! SET demo:key "hello"
redis-cli -a StrongPassw0rd! INCR demo:counter
redis-cli -a StrongPassw0rd! INCR demo:counter
redis-cli -a StrongPassw0rd! GET demo:key
redis-cli -a StrongPassw0rd! GET demo:counter
```

## 5-2) Replica에서 동일 데이터 읽기

Replica에서:

```
redis-cli -a StrongPassw0rd! GET demo:key
redis-cli -a StrongPassw0rd! GET demo:counter
```

기대 결과:

* `demo:key` → `"hello"`

* `demo:counter` → `"2"`

---

## 6) Replica 쓰기 금지 확인

Replica에서:

```
redis-cli -a StrongPassw0rd! SET replica:write "no"
```

기대 결과:

```
(error) READONLY You can't write against a read only replica.
```

---

## 7) 복제 해제 / 전환 실습

## 7-1) Replica 복제 해제(Standalone로 전환)

Replica에서:

```
redis-cli -a StrongPassw0rd! REPLICAOF NO ONE
```

확인:

```
redis-cli -a StrongPassw0rd! INFO replication | egrep "role|master_host"
# role:master
```

이제 Replica였던 서버에서 쓰기 가능:

```
redis-cli -a StrongPassw0rd! SET now:master "ok"
```

---

## 7-2) 다시 Master(192.168.80.110) 따라가도록 재설정

Replica(전환된 서버)에서:

```
redis-cli -a StrongPassw0rd! REPLICAOF 192.168.80.110 6379
```

---

## 8) 장애/운영 관점 포인트

## 8-1) 복제는 자동 승격이 아님

* Master가 죽어도 Replica가 자동으로 Master가 되지 않음

* 자동 장애조치가 필요하면:
  + **Redis Sentinel** 또는
  + 클러스터/관리형(예: ElastiCache Multi-AZ) 고려

## 8-2) 보안 필수 요소

* `bind`를 내부망 IP로 제한하거나 보안그룹/방화벽으로 제한

* `requirepass` 설정

* 복제에는 `masterauth` 설정

---

### 연결이 안 될 때(Replica에서)

Replica에서:

```
redis-cli -a StrongPassw0rd! INFO replication | egrep "master_link_status|master_last_io_seconds_ago|master_host"
```

Master에서:

```
redis-cli -a StrongPassw0rd! INFO replication | egrep "connected_slaves|slave0"
```

로그 확인:

```
sudo journalctl -u redis-server -n 200 --no-pager
```

자주 원인:

* Master 포트(6379) 방화벽 차단

* Master `bind 127.0.0.1`로 외부 접속 불가

* `requirepass`는 있는데 Replica에 `masterauth` 누락

* 서로 다른 Redis 인스턴스/포트에 붙음

---