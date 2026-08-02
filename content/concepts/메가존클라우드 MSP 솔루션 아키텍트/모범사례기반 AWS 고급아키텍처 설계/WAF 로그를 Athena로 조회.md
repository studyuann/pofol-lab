---
title: "WAF 로그를 Athena로 조회"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "모범사례기반 AWS 고급아키텍처 설계"]
is_public: true
draft: false
---

# WAF 로그를 Athena로 조회

## 실습 목표

S3에 저장된 WAF 로그를 Athena에서 조회한다.

이번 실습에서 할 일은 딱 4단계다.

1. Athena에서 쿼리 결과 저장 위치 설정

2. Athena에서 데이터베이스 생성

3. WAF 로그 테이블 생성

4. SELECT 쿼리로 로그 조회

Athena에서 데이터베이스는 Query Editor에서 `CREATE DATABASE`로 만들고, 쿼리를 실행하려면 먼저 쿼리 결과 저장 위치를 S3에 지정해야 한다.

---

# 1. 실습 전 준비

이미 끝난 상태

* WAF 로그 수집 설정 완료

* Firehose로 S3 저장 완료

* S3 버킷에 로그 파일 존재

추가로 필요한 것

* Athena 사용 권한

* Athena 결과 저장용 S3 버킷 또는 경로

예시

```
WAF 로그 버킷: s3://my-waf-log-bucket/waf-logs/
Athena 결과 버킷: s3://my-athena-result-bucket/
```

---

# 2. 1단계 - Athena 열기

AWS 콘솔에서 다음으로 이동한다.

```
AWS Console → Athena → Query editor
```

처음 들어가면 Query Editor 화면이 보인다.

---

# 3. 2단계 - Athena 결과 저장 위치 설정

Athena는 쿼리 결과를 S3에 저장해야 한다.

이 설정이 안 되어 있으면 쿼리가 실행되지 않을 수 있다. Athena 콘솔에서는 Settings에서 Query result location을 지정하거나, Workgroup 설정이 이를 덮어쓸 수 있다.

## 3.1 설정 메뉴 이동

Athena Query Editor 화면에서

* 우측 상단 또는 상단 메뉴의 **Settings**

* 또는 **Edit settings**

으로 들어간다.

## 3.2 Query result location 입력

예시

```
s3://my-athena-result-bucket/
```

또는 폴더까지 지정 가능

```
s3://my-athena-result-bucket/query-results/
```

## 3.3 저장

**Save** 를 눌러 저장한다.

---

# 4. 3단계 - 데이터베이스 생성

이제 Athena 안에 WAF 로그용 데이터베이스를 만든다.

## 4.1 쿼리 입력

Athena Query Editor에 아래 SQL 입력

```
CREATE DATABASE IF NOT EXISTS waf_logs_db;
```

## 4.2 실행

**Run** 버튼 클릭

정상 실행되면 오류 없이 완료된다.

## 4.3 데이터베이스 선택

다음 SQL 실행

```
USE waf_logs_db;
```

또는 왼쪽 데이터베이스 목록에서 `waf_logs_db` 를 직접 선택해도 된다.

### 설명

여기서 만드는 데이터베이스는 **실제 로그 파일 저장 공간이 아님**.

실제 로그는 S3에 있고, Athena 데이터베이스는 **테이블 메타데이터를 관리하는 논리 공간**이다.

---

# 5. 4단계 - S3 로그 경로 확인

이 단계가 중요하다.

S3 콘솔에 들어가서 **WAF 로그가 실제로 저장된 경로**를 확인한다.

예를 들어 S3 안에 이런 식으로 로그가 있을 수 있다.

```
s3://my-waf-log-bucket/waf-logs/
```

또는

```
s3://my-waf-log-bucket/AWSLogs/123456789012/WAFLogs/ap-northeast-2/my-webacl/
```

### 중요한 기준

Athena 테이블의 `LOCATION` 은

**로그 파일들이 계속 쌓이는 상위 경로**를 지정하면 된다.

예를 들어 로그가 계속 아래에 쌓이면

```
s3://my-waf-log-bucket/waf-logs/2026/04/01/10/...
```

테이블 LOCATION은 이렇게 준다.

```
s3://my-waf-log-bucket/waf-logs/
```

WAF 로그 테이블 생성 시 `LOCATION` 을 실제 로그 저장 S3 경로로 수정해서 사용.

---

# 6. 5단계 - 최소 컬럼 버전 테이블 생성

처음 실습은 **전체 컬럼을 다 넣지 말고**,

자주 보는 컬럼만 넣는 **최소 버전 테이블**로 시작하는 것이 가장 쉽다.

아래 SQL에서 `LOCATION` 만 본인 S3 경로로 바꿔서 실행한다.

```
CREATE EXTERNAL TABLE IF NOT EXISTS waf_logs_db.waf_logs_simple (
  `timestamp` bigint,
  formatversion int,
  webaclid string,
  terminatingruleid string,
  terminatingruletype string,
  action string,
  httprequest struct<
    clientip:string,
    country:string,
    uri:string,
    args:string,
    httpversion:string,
    httpmethod:string,
    requestid:string
  >
)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
LOCATION 's3://my-waf-log-bucket/waf-logs/';
```

## 실행 방법

1. Athena Query Editor에 붙여넣기

2. `LOCATION` 경로 수정

3. **Run** 클릭

### 설명

* `CREATE EXTERNAL TABLE`

  S3에 있는 파일을 외부 테이블처럼 읽겠다는 의미

* `timestamp`

  로그 발생 시간

* `action`

  `ALLOW`, `BLOCK`, `COUNT` 같은 처리 결과

* `terminatingruleid`

  요청을 최종적으로 처리한 룰 ID

* `httprequest`

  요청 IP, 국가, URI, 메서드 같은 실제 요청 정보

Athena의 WAF 로그 예제는 OpenX JSON SerDe를 사용하며, WAF 로그 테이블 예제는 v1/v2 모두에 사용할 수 있게 설계되어 있다.

---

# 7. 6단계 - 테이블 생성 확인

테이블이 만들어졌는지 확인한다.

왼쪽 목록에서

* Database: `waf_logs_db`

* Table: `waf_logs_simple`

가 보이면 성공이다.

또는 SQL로 확인할 수도 있다.

```
SHOW TABLES IN waf_logs_db;
```

---

# 8. 7단계 - 로그가 읽히는지 바로 확인

가장 먼저 이 쿼리를 실행한다.

```
SELECT *
FROM waf_logs_db.waf_logs_simple
LIMIT 10;
```

## 정상일 때

* 결과가 1건 이상 보임

* `timestamp`

* `action`

* `terminatingruleid`

* `httprequest`

컬럼이 출력됨

## 안 보일 때 확인할 것

* LOCATION 경로가 맞는지

* S3에 실제 로그 파일이 있는지

* Athena 결과 저장 위치 설정이 됐는지

* 다른 리전에서 Athena를 보고 있지 않은지

---

# 9. 8단계 - 사람이 읽기 쉬운 형태로 조회

`timestamp` 는 밀리초 기준이라 그대로 보면 불편하다.

그래서 시간을 변환해서 본다.

```
SELECT
  from_unixtime("timestamp"/1000) AS event_time,
  action,
  terminatingruleid,
  httprequest.clientip,
  httprequest.country,
  httprequest.httpmethod,
  httprequest.uri
FROM waf_logs_db.waf_logs_simple
LIMIT 20;
```

## 이 쿼리에서 보는 것

* `event_time` : 사람이 읽을 수 있는 시간

* `action` : 허용/차단 여부

* `terminatingruleid` : 어떤 룰이 처리했는지

* `clientip` : 요청 보낸 IP

* `country` : 요청 국가

* `uri` : 요청 경로

---

# 10. 9단계 - 차단된 요청만 보기

이제 실무에서 가장 많이 보는 `BLOCK` 요청만 따로 조회한다.

```
SELECT
  from_unixtime("timestamp"/1000) AS event_time,
  action,
  terminatingruleid,
  httprequest.clientip,
  httprequest.country,
  httprequest.uri
FROM waf_logs_db.waf_logs_simple
WHERE action = 'BLOCK'
ORDER BY "timestamp" DESC
LIMIT 50;
```

## 확인 포인트

* 누가 차단됐는지

* 어떤 URI에 접근했는지

* 어떤 룰이 차단했는지

---

# 11. 10단계 - 가장 많이 차단된 IP 보기

```
SELECT
  httprequest.clientip AS client_ip,
  COUNT(*) AS block_count
FROM waf_logs_db.waf_logs_simple
WHERE action = 'BLOCK'
GROUP BY httprequest.clientip
ORDER BY block_count DESC
LIMIT 20;
```

## 확인 포인트

* 반복적으로 공격하는 IP가 있는지

* 특정 IP가 비정상적으로 많은 요청을 보내는지

---

# 12. 11단계 - 많이 공격받는 URI 보기

```
SELECT
  httprequest.uri AS request_uri,
  COUNT(*) AS blocked_count
FROM waf_logs_db.waf_logs_simple
WHERE action = 'BLOCK'
GROUP BY httprequest.uri
ORDER BY blocked_count DESC
LIMIT 20;
```

## 확인 포인트

* `/login`

* `/admin`

* `/wp-login.php`

이런 경로가 많이 보이는지 확인한다.

---

# 13. 12단계 - 국가별 차단 요청 보기

```
SELECT
  httprequest.country AS country,
  COUNT(*) AS blocked_count
FROM waf_logs_db.waf_logs_simple
WHERE action = 'BLOCK'
GROUP BY httprequest.country
ORDER BY blocked_count DESC
LIMIT 20;
```

---

# 14. 가장 많이 발생하는 실수

## 14.1 테이블은 생성됐는데 조회 결과가 없음

원인

* S3 경로 잘못 입력

* 상위 폴더가 너무 위거나 너무 아래임

* 실제 로그가 아직 없음

조치

* S3 콘솔에서 실제 로그 파일 경로 다시 확인

* `LOCATION` 수정 후 테이블 다시 생성

## 14.2 `NULL` 이 많이 보임

원인

* 실제 로그 JSON 구조와 컬럼 구조가 일부 다름

* 해당 로그에 그 값이 없음

## 14.3 쿼리가 실행 안 됨

원인

* Athena 결과 저장 위치 미설정

* Workgroup 설정이 덮어씀

* S3 권한 부족

Athena는 쿼리 실행 전에 결과 저장 위치가 필요하고, 경우에 따라 Workgroup 설정이 클라이언트 설정을 override할 수 있다.

---

# 15. 명령 모음

학생이 따라하기 쉽게 최소 명령만 다시 모으면 아래 4개다.

## 1) 데이터베이스 생성

```
CREATE DATABASE IF NOT EXISTS waf_logs_db;
```

## 2) 데이터베이스 선택

```
USE waf_logs_db;
```

## 3) 테이블 생성

```
CREATE EXTERNAL TABLE IF NOT EXISTS waf_logs_db.waf_logs_simple (
  `timestamp` bigint,
  formatversion int,
  webaclid string,
  terminatingruleid string,
  terminatingruletype string,
  action string,
  httprequest struct<
    clientip:string,
    country:string,
    uri:string,
    args:string,
    httpversion:string,
    httpmethod:string,
    requestid:string
  >
)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
LOCATION 's3://my-waf-log-bucket/waf-logs/';
```

## 4) 조회

```
SELECT
  from_unixtime("timestamp"/1000) AS event_time,
  action,
  terminatingruleid,
  httprequest.clientip,
  httprequest.country,
  httprequest.uri
FROM waf_logs_db.waf_logs_simple
LIMIT 20;
```

---