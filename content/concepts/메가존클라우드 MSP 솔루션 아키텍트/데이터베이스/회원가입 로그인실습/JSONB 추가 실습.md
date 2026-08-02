---
title: "JSONB 추가 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "데이터베이스", "회원가입 로그인실습"]
is_public: true
draft: false
---

# JSONB 추가 실습

> “운영 중에 **로그에 새로운 정보가 필요해졌다.**
>
> 그런데 이미 서비스는 돌아가고 있다.
>
> 이때 PostgreSQL JSONB는 **테이블 변경 없이** 바로 확장할 수 있다.”

---

# 실습 개요

### 기존 상태

* `auth_events` 테이블

* `payload JSONB` 컬럼 하나에 이벤트 정보 저장

```
{
  "reason": "bad_password"
}
```

### 실습 후 상태

* **컬럼 추가 없음**

* payload에 **새 필드가 계속 추가됨**

```
{
  "reason": "bad_password",
  "attempt": 3,
  "user_agent": "Mozilla/5.0 ...",
  "geo": { "country": "KR", "city": "Seoul" }
}
```

→ **DDL 없음, 서비스 중단 없음**

---

# 1단계 실습: “요구사항이 늘어남”

### 시나리오

> 보안팀에서 요청이 왔다
>
> “로그인 실패 시 **몇 번째 실패인지(attempt)** 와 **브라우저 정보(user\_agent)** 도 같이 남겨달라”

---

# 2단계 실습: 코드 수정

📍 **VM1 –** `server.js`

### 기존 로그인 실패 로그 (이미 있음)

```
await logEvent({
  eventType: "login_fail",
  actor: email,
  ip,
  payload: { reason: "bad_password" }
});
```

---

### 🔽 필드 추가

```
await logEvent({
  eventType: "login_fail",
  actor: email,
  ip,
  payload: {
    reason: "bad_password",
    attempt: 1,
    user_agent: req.headers["user-agent"]
  }
});
```

> ✔️ **중요**
>
> * DB 테이블 수정 ❌
>
> * 컬럼 추가 ❌
>
> * 인덱스 변경 ❌
>
>   👉 **코드만 바꿈**

> “이 상태로 바로 서버 재시작”

```
node server.js
```

---

# 3단계 실습: 실제로 필드가 늘어났는지 확인

## 3-1) 로그인 실패 2~3회 발생

* 비밀번호 틀리게 로그인

---

## 3-2) PostgreSQL에서 확인 (VM3)

```
sudo -u postgres psql -d monitor_lab
```

```
SELECT payload
FROM auth_events
WHERE event_type = 'login_fail'
ORDER BY ts DESC
LIMIT 3;
```

### 기대 결과

```
{
  "reason": "bad_password",
  "attempt": 1,
  "user_agent": "Mozilla/5.0 (X11; Linux x86_64)..."
}
```

👉 **컬럼 추가 없이 필드가 늘어남**

---

# 4단계 실습: “추가된 필드로 검색”

### 4-1) JSONB 필드 조건 검색

```
SELECT ts, actor, payload->>'user_agent'
FROM auth_events
WHERE payload->>'reason' = 'bad_password'
ORDER BY ts DESC;
```

### 4-2) attempt 조건으로 검색

```
SELECT ts, actor, payload
FROM auth_events
WHERE payload->>'attempt' = '1';
```

> ✔️ JSONB 내부 필드를 **컬럼처럼** 검색

---

# 5단계 실습(확장): 구조가 더 복잡해져도 됨.

### 코드에서 payload를 이렇게 더 확장

```
payload: {
  reason: "bad_password",
  attempt: 2,
  user_agent: req.headers["user-agent"],
  geo: {
    country: "KR",
    city: "Seoul"
  }
}
```

---

### PostgreSQL에서 중첩 구조 조회

```
SELECT
  payload->'geo'->>'country' AS country,
  payload->'geo'->>'city' AS city
FROM auth_events
WHERE event_type = 'login_fail';
```

👉 **RDB인데 NoSQL처럼 쓸 수 있음.**

---

# 6단계 실습: JSONB에 인덱스 적용

GIN 인덱스 생성:

```
CREATE INDEX idx_auth_events_payload_gin
ON auth_events USING GIN (payload);
```

### 실행 계획 비교(강사용 시연)

```
EXPLAIN ANALYZE
SELECT *
FROM auth_events
WHERE payload->>'reason' = 'bad_password';
```

👉 인덱스 없을 때 / 있을 때 비교 설명

---

# 7단계: 정리

### PostgreSQL JSONB를 별도로 쓰는 이유

| 항목 | MySQL(RDB) | PostgreSQL(JSONB) |
| --- | --- | --- |
| 필드 추가 | ALTER TABLE 필요 | ❌ 필요 없음 |
| 서비스 중단 위험 | 있음 | 없음 |
| 로그/이벤트 | 부적합 | **매우 적합** |
| 구조 변경 | 어려움 | **자유로움** |
| 인덱스 | 제한적 | **GIN으로 JSON 내부까지** |

---