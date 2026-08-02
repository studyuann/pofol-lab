---
title: "MySQL 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "데이터베이스", "RDB(Relational DataBase)"]
is_public: true
draft: false
---

# MySQL 실습

## 실습 환경

* Ubuntu 22.04 LTS (서버 1대)

* MySQL 8.x

* MySQL Workbench (윈도우)

* 네트워크: Workbench PC ↔ Ubuntu 서버 3306/TCP 통신 가능

## 실습 계정 표준

* DB: `bootcamp_shop`

* User: `labuser`

* Password: `1234` (교육용 예시)

---

# 1. 설치/접속/스키마/기본 SQL

## 목표

* MySQL 설치 및 서비스 운영 기본(systemctl)

* 계정/권한/원격 접속 구성

* 샘플 스키마/데이터 로딩

* 기본 조회/정렬/필터/집계 기초

---

## - Ubuntu에 MySQL 설치 및 서비스 확인

### 실습: 설치

```
sudo apt update
sudo apt install -y mysql-server
```

### 실습: 서비스 상태/부팅 자동 실행 확인

```
sudo systemctl status mysql --no-pager
sudo systemctl is-enabled mysql
```

### 운영 포인트

* `mysqld`는 서비스 형태로 동작하며 장애/재시작 대응이 필요

* 로그/디렉토리 위치 확인(운영의 기본)
  + 데이터: `/var/lib/mysql`
  + 설정: `/etc/mysql/`
  + 로그(환경에 따라): `/var/log/mysql/`

---

## - 초기 보안 설정 및 root 접근 방식

### 실습: 보안 초기화(권장)

```
sudo mysql_secure_installation
```

### 운영 포인트

* root 원격 로그인 금지 권장

* 애플리케이션/운영용 계정 분리(최소 권한)

* 비밀번호 정책(교육에서는 완화 가능하지만 실제 운영은 강화)

---

## - 원격 접속 계정/권한 구성 + 바인딩/방화벽

### 실습: DB 생성 및 사용자 생성

```
sudo mysql
```

```
CREATE DATABASE IF NOT EXISTS bootcamp_shop
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

CREATE USER IF NOT EXISTS 'labuser'@'%' IDENTIFIED BY '1234';
GRANT ALL PRIVILEGES ON bootcamp_shop.* TO 'labuser'@'%';
FLUSH PRIVILEGES;

SELECT user, host FROM mysql.user WHERE user='labuser';
```

### 실습: bind-address 수정(원격 접속 허용)

```
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
# bind-address = 127.0.0.1  -> 0.0.0.0 로 변경(또는 주석)
sudo systemctl restart mysql
```

### 실습: UFW 사용 시 포트 허용

```
sudo ufw status
sudo ufw allow 3306/tcp
sudo ufw reload
```

### 운영 포인트(클라우드 관점)

* 보안그룹/방화벽은 “최소 오픈”:
  + 가능하면 `0.0.0.0/0` 금지
  + 특정 IP(예: 관리자PC)만 허용

* DB는 퍼블릭 서브넷 배치 지양(클라우드에서는 프라이빗 서브넷 권장)

---

## - Workbench 연결 & 기본 사용법

### Workbench 설정 가이드

* Hostname: `<Ubuntu IP>`

* Port: `3306`

* Username: `labuser`

* Default Schema: `bootcamp_shop`

### 연결 실패 시 체크리스트

* Ubuntu에서 `mysql` 서비스 실행 중인가?

* `bind-address`가 127.0.0.1로 묶여 있지 않은가?

* 계정 host가 `%` 또는 해당 IP로 되어 있는가?

* 비밀번호 오타/권한 부여 누락은 없는가?

---

## - 스키마/샘플 데이터 로딩(워크북 스크립트 실행)

> customers/products/orders/order\_items/payments 스키마 및 데이터 스크립트를 Workbench에서 실행합니다.

### 실행 후 검증 쿼리

```
USE bootcamp_shop;
SHOW TABLES;

SELECT COUNT(*) customers FROM customers;
SELECT COUNT(*) products FROM products;
SELECT COUNT(*) orders FROM orders;
SELECT COUNT(*) order_items FROM order_items;
SELECT COUNT(*) payments FROM payments;
```

### 운영 포인트

* 외래키(FK)는 실수를 줄이고 데이터 무결성을 보장하지만,
  + 대량 적재/마이그레이션 시 성능/순서 고려 필요

* `utf8mb4`는 운영 표준(이모지/다국어 고려)

---

# 2. 기본 조회/정렬/필터/집계 실습

# 1) 기본 조회(SELECT) 실습

## 1-1. 전체 조회 vs 필요한 컬럼만 조회

> 실무에서는 SELECT \*는 디버깅 외엔 지양(네트워크/IO 비용 증가).

```
-- (나쁜 습관) 전체 컬럼
SELECT * FROM customers;

-- (권장) 필요한 컬럼만
SELECT customer_id, email, name, status, created_at
FROM customers;
```

### 실습 문제

1. customers에서 **name, phone, status**만 조회하라.

2. products에서 **sku, name, price**만 조회하라.

---

## 1-2. 별칭(alias)과 계산 컬럼

```
SELECT
  product_id AS id,
  name AS product_name,
  price,
  stock,
  price * stock AS stock_value
FROM products;
```

### 실습 문제

1. products에서 `price * 1.1`을 **vat\_included\_price**로 계산해 조회하라.

---

## 1-3. DISTINCT (중복 제거)

```
SELECT DISTINCT category
FROM products;
```

### 실습 문제

1. orders에서 **status 종류**를 중복 없이 조회하라.

---

# 2) 정렬(ORDER BY) 실습

## 2-1. 최신 가입자/최신 상품

```
SELECT customer_id, name, created_at
FROM customers
ORDER BY created_at DESC;
```

```
SELECT product_id, name, created_at
FROM products
ORDER BY created_at DESC
LIMIT 5;
```

### 실습 문제

1. products를 **price 내림차순**으로 정렬하고 상위 10개만 조회하라.

2. products를 **category 오름차순, price 내림차순**으로 다중 정렬하라.

---

## 2-2. 값이 같을 때 2차 정렬

```
SELECT product_id, category, name, price
FROM products
ORDER BY category ASC, price DESC, name ASC;
```

---

# 3) 필터(WHERE) 실습

## 3-1. 비교 연산자(=, !=, >, >=, <, <=)

```
SELECT product_id, name, price
FROM products
WHERE price >= 50000;
```

### 실습 문제

1. stock이 100 이상인 상품만 조회하라.

2. price가 10000 미만인 상품만 조회하라.

---

## 3-2. 범위(BETWEEN) / 목록(IN)

```
-- 1만원~5만원 사이
SELECT product_id, name, price
FROM products
WHERE price BETWEEN 10000 AND 50000;

-- 특정 카테고리만
SELECT product_id, name, category
FROM products
WHERE category IN ('DEVICE','STORAGE');
```

### 실습 문제

1. orders에서 ordered\_at이 최근 7일 이내인 것만 조회하라.

```
-- 힌트
-- WHERE ordered_at >= NOW() - INTERVAL 7 DAY
```

---

## 3-3. 패턴 검색(LIKE)

```
-- name에 'Cable'이 포함된 상품
SELECT product_id, name
FROM products
WHERE name LIKE '%Cable%';
```

### 실습 문제

1. email이 user1로 시작하는 고객을 조회하라.

   (예: [user01@example.com](mailto:user01@example.com), [user10@example.com](mailto:user10@example.com) 등)

---

## 3-4. NULL 체크(IS NULL / IS NOT NULL)

현재 샘플은 phone이 모두 존재하지만, 실무 필수 문법이므로 형태만 익힌다.

```
SELECT customer_id, name, phone
FROM customers
WHERE phone IS NULL;
```

---

## 3-5. AND / OR / 괄호 우선순위

```
SELECT product_id, category, name, price
FROM products
WHERE (category = 'DEVICE' OR category = 'STORAGE')
  AND price >= 100000;
```

### 실습 문제

1. category가 ACCESSORY이고 price가 10000 이상 30000 이하인 상품을 조회하라.

---

# 4) 집계(AGGREGATION) 실습

## 4-1. 전체 집계(COUNT, MIN, MAX, AVG, SUM)

```
-- 상품 평균 가격
SELECT AVG(price) AS avg_price
FROM products;

-- 최고/최저 가격
SELECT MIN(price) AS min_price, MAX(price) AS max_price
FROM products;

-- 전체 재고 합
SELECT SUM(stock) AS total_stock
FROM products;
```

### 실습 문제

1. orders에서 총 주문 건수를 조회하라.

2. payments에서 결제 방법(method)별 건수를 세지 말고, 먼저 **전체 결제 건수**를 조회하라.

---

## 4-2. GROUP BY (카테고리별 상품 수/평균가격)

```
SELECT
  category,
  COUNT(*) AS product_count,
  AVG(price) AS avg_price
FROM products
GROUP BY category
ORDER BY product_count DESC;
```

### 실습 문제

1. category별 **총 재고(stock) 합계**를 구하라.

2. orders에서 status별 주문 건수를 구하라.

---

## 4-3. HAVING (그룹 결과 필터)

> WHERE는 “행(row) 필터”, HAVING은 “그룹 결과 필터”

```
-- 상품이 3개 이상인 카테고리만
SELECT category, COUNT(*) AS cnt
FROM products
GROUP BY category
HAVING COUNT(*) >= 3
ORDER BY cnt DESC;
```

### 실습 문제

1. orders에서 status별 건수를 구하되, **2건 이상인 status만** 출력하라.

---

# 5) 서비스 관점 집계

> 조회/필터/정렬/집계를 한 번에 사용

## 5-1. 최근 14일 주문 중 취소(CANCELLED) 제외하고 최신순 20건

```
SELECT order_id, customer_id, status, ordered_at, total_amount
FROM orders
WHERE ordered_at >= NOW() - INTERVAL 14 DAY
  AND status <> 'CANCELLED'
ORDER BY ordered_at DESC
LIMIT 20;
```

## 5-2. 고객별 주문 건수 TOP 5

```
SELECT customer_id, COUNT(*) AS order_cnt
FROM orders
GROUP BY customer_id
ORDER BY order_cnt DESC
LIMIT 5;
```

## 5-3. 결제수단(method)별 총 결제금액 합계

```
SELECT method, SUM(paid_amount) AS total_paid
FROM payments
GROUP BY method
ORDER BY total_paid DESC;
```

## 5-4. 주문 상태(status)별 총 매출(orders.total\_amount) 합계

```
SELECT status, SUM(total_amount) AS total_sales
FROM orders
GROUP BY status
ORDER BY total_sales DESC;
```

## 5-5. 평균 주문금액(취소 제외)

```
SELECT AVG(total_amount) AS avg_order_amount
FROM orders
WHERE status <> 'CANCELLED';
```

## 5-6. “고액 주문” 기준: 주문금액 100,000 이상 주문 수

```
SELECT COUNT(*) AS high_value_orders
FROM orders
WHERE total_amount >= 100000;
```

---

# 7) 주의

* `WHERE`는 개별 행 필터, `HAVING`은 그룹 결과 필터

* `ORDER BY`는 최종 결과 정렬 (WHERE/GROUP BY 이후)

* 집계는 기본적으로 **GROUP BY 대상 컬럼** + **집계 함수** 조합으로만 선택 가능

---

# 3. 조인

---

# 1) JOIN이 필요한 이유

현재 테이블 구조는 의도적으로 **정규화**되어 있다. 즉, 데이터가 중복되지 않도록 테이블이 나뉘어져 있음.

| 테이블 | 역할 |
| --- | --- |
| customers | 고객 정보 |
| products | 상품 정보 |
| orders | 주문(누가 언제 주문했는지) |
| order\_items | 주문에 포함된 상품 |
| payments | 결제 정보 |

예를 들어:

> “누가 무엇을 얼마에 주문했는가?”

이 질문은 **단일 테이블로는 절대 답할 수 없다.**

👉 그래서 **JOIN이 필요하다.**

---

# 2) JOIN 기본 문법

```
SELECT 컬럼들
FROM 테이블A a
JOIN 테이블B b ON a.공통컬럼 = b.공통컬럼;
```

* JOIN의 기준은 **항상 관계(FK → PK)**

* ON 조건이 **JOIN의 핵심**

---

# 3) INNER JOIN 실습

## 3-1. 주문 + 고객 정보 JOIN

> “주문 목록에 고객 이름을 같이 보고 싶다”

```
SELECT
  o.order_id,
  o.ordered_at,
  o.status,
  o.total_amount,
  c.name AS customer_name
FROM orders o
JOIN customers c
  ON o.customer_id = c.customer_id;
```

### 핵심

* orders.customer\_id → customers.customer\_id (FK → PK)

* INNER JOIN: **양쪽에 모두 존재하는 데이터만**

---

### 실습 문제

1. orders + customers를 JOIN하여 **order\_id, 고객명, 주문상태, 주문일자**를 조회하라.

---

## 3-2. 주문 + 주문상품 JOIN

> “주문 하나에 어떤 상품들이 들어 있는가?”

```
SELECT
  o.order_id,
  oi.product_id,
  oi.quantity,
  oi.unit_price,
  oi.line_amount
FROM orders o
JOIN order_items oi
  ON o.order_id = oi.order_id;
```

### 실습 문제

1. order\_items + products를 JOIN하여 **상품명, 수량, 단가, 금액**을 조회하라.

---

## 3-3. 주문 + 주문상품 + 상품 (3테이블 JOIN)

```
SELECT
  o.order_id,
  p.name AS product_name,
  oi.quantity,
  oi.unit_price,
  oi.line_amount
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p     ON oi.product_id = p.product_id
ORDER BY o.order_id;
```

### 강의 포인트

* JOIN은 **여러 개를 연속으로 연결 가능**

* 기준 테이블은 보통 **업무 질문의 중심**

---

### 실습 문제

1. 주문별로 **상품명 + 수량 + 금액**을 모두 조회하라.

---

# 4) JOIN + WHERE (조건 결합)

## 4-1. 특정 고객의 주문 내역

```
SELECT
  o.order_id,
  o.ordered_at,
  o.total_amount
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE c.name = 'Kim Mina'
ORDER BY o.ordered_at DESC;
```

### 실습 문제

1. 고객 이름이 `Lee Jisu`인 고객의 주문 내역을 조회하라.

---

## 4-2. 취소되지 않은 주문만 조회

```
SELECT
  o.order_id,
  c.name,
  o.status,
  o.total_amount
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.status <> 'CANCELLED';
```

---

# 5) LEFT JOIN 실습 (중요)

## 5-1. 주문 + 결제 (결제 없는 주문 포함)

> “결제가 아직 안 된 주문도 보고 싶다”

```
SELECT
  o.order_id,
  o.status AS order_status,
  p.method,
  p.status AS payment_status
FROM orders o
LEFT JOIN payments p
  ON o.order_id = p.order_id
ORDER BY o.order_id;
```

### 핵심

* LEFT JOIN: **왼쪽 테이블은 무조건 유지**

* 결제가 없는 주문 → payment 컬럼은 NULL

---

### 실습 문제

1. 모든 주문을 조회하되, **결제 정보가 있으면 같이 출력**하라.

---

## 5-2. “결제되지 않은 주문 찾기”

```
SELECT
  o.order_id,
  o.status,
  o.total_amount
FROM orders o
LEFT JOIN payments p ON o.order_id = p.order_id
WHERE p.order_id IS NULL;
```

### 실습 문제

1. 주문이력이 없는 이용자 조회하라.

---

# 6) JOIN + GROUP BY

## 6-1. 고객별 주문 건수

```
SELECT
  c.customer_id,
  c.name,
  COUNT(o.order_id) AS order_count
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name
ORDER BY order_count DESC;
```

### 핵

* 집계 시 GROUP BY는 **비집계 컬럼 전부 포함**

* LEFT JOIN → 주문 없는 고객도 포함 가능

---

### 실습 문제

1. 고객별 **총 주문 금액 합계**를 구하라.

---

## 6-2. 상품별 판매 수량

```
SELECT
  p.product_id,
  p.name,
  SUM(oi.quantity) AS total_qty
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.product_id, p.name
ORDER BY total_qty DESC;
```

### 실습 문제

1. 상품별 **총 매출 금액**(quantity \* unit\_price)을 구하라.

---

# 7) 종합

## 7-1. 최근 7일 주문 상세 리포트

```
SELECT
  o.order_id,
  c.name AS customer_name,
  o.ordered_at,
  p.name AS product_name,
  oi.quantity,
  oi.line_amount
FROM orders o
JOIN customers c   ON o.customer_id = c.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p     ON oi.product_id = p.product_id
WHERE o.ordered_at >= NOW() - INTERVAL 7 DAY
ORDER BY o.ordered_at DESC;
```

---

## 7-2. 결제 수단별 매출

```
SELECT
  p.method,
  SUM(p.paid_amount) AS total_sales
FROM payments p
GROUP BY p.method
ORDER BY total_sales DESC;
```

---

# 8) 요약

* JOIN은 **테이블을 합치는 기술이 아니라 관계를 해석하는 기술**

* INNER JOIN → “둘 다 있어야 의미 있음”

* LEFT JOIN → “기준 테이블은 무조건 살린다”

* 실무 리포트 = **JOIN + WHERE + GROUP BY**

---

# 4. 서브쿼리(Subquery)

---

## 1) 서브쿼리란

> 서브쿼리는“쿼리 안에서 또 다른 쿼리를 실행해그 결과를 조건이나 값으로 사용하는 방법”이다.

---

## 2) 왜 서브쿼리가 필요한가?

SQL을 쓰다 보면 이런 상황이 생긴다.

> “이 조건을 만족하는 값들을 먼저 구한 뒤, 그 결과를 가지고 다시 조회하고 싶다.”

* 이럴 때 쓰는 게 **서브쿼리**

---

## 3) 서브쿼리의 기본 구조

```
SELECT 컬럼
FROM 테이블
WHERE 컬럼 IN (
  SELECT 컬럼
  FROM 테이블
  WHERE 조건
);
```

* **안쪽 쿼리(서브쿼리)** 먼저 실행

* 결과를 바깥 쿼리에서 사용

---

## 4) 서브쿼리의 위치별 분류

서브쿼리는 **어디에 쓰이느냐**에 따라 나뉜다.

---

### 4-1) WHERE 절 서브쿼리

### 예제: 주문이 있는 고객만 조회

```
SELECT *
FROM customers
WHERE customer_id IN (
  SELECT customer_id
  FROM orders
);
```

의미:

> orders에 등장한 customer\_id만 고객에서 조회

---

### 4-2) SELECT 절 서브쿼리 (스칼라 서브쿼리)

### 예제: 주문별 총 아이템 수 출력

```
SELECT
  o.order_id,
  (
    SELECT SUM(quantity)
    FROM order_items oi
    WHERE oi.order_id = o.order_id
  ) AS total_qty
FROM orders o;
```

특징:

* 서브쿼리는 **반드시 단일 값(1행 1열)** 반환

* 행마다 실행됨 → **성능 주의**

---

### 4-3) FROM 절 서브쿼리 (파생 테이블)

### 예제: 주문 합계를 먼저 계산하고 조회

```
SELECT *
FROM (
  SELECT order_id, SUM(quantity) AS qty
  FROM order_items
  GROUP BY order_id
) t
WHERE t.qty >= 3;
```

의미:

* 서브쿼리 결과를 **임시 테이블처럼 사용**

* 복잡한 집계 → 단계 분리할 때 유용

---

## 5) 서브쿼리 vs JOIN

### 같은 문제, 두 가지 방식

### 서브쿼리

```
SELECT *
FROM customers
WHERE customer_id IN (
  SELECT customer_id
  FROM orders
);
```

### JOIN

```
SELECT DISTINCT c.*
FROM customers c
JOIN orders o
  ON c.customer_id = o.customer_id;
```

---

### 차이 요약

| 구분 | 서브쿼리 | JOIN |
| --- | --- | --- |
| 가독성 | 직관적 | 관계 명확 |
| 성능 | 느릴 수 있음 | 일반적으로 빠름 |
| 옵티마이저 | 제한적 | 최적화 유리 |
| 실무 | 제한적 | 주력 |

* **실무에서는 JOIN이 우선**,

* **서브쿼리는 “의도가 명확할 때”**

---

## 6) 상관 서브쿼리

> 바깥 쿼리의 값을안쪽 쿼리가 참조하는 구조

---

### 예제: 고객별 주문 수가 2건 이상인 고객

```
SELECT *
FROM customers c
WHERE (
  SELECT COUNT(*)
  FROM orders o
  WHERE o.customer_id = c.customer_id
) >= 2;
```

문제점:

* customers 한 행마다

* orders를 다시 조회

>> **데이터 많아지면 성능 급락**

---

### JOIN으로 바꾸면

```
SELECT c.*
FROM customers c
JOIN orders o
  ON c.customer_id = o.customer_id
GROUP BY c.customer_id
HAVING COUNT(*) >= 2;
```

---

## 7) EXISTS 서브쿼리

### 특징

* 결과 값 자체가 중요 ❌

* **존재 여부만 체크**

---

### 예제: 주문이 있는 고객 조회

```
SELECT *
FROM customers c
WHERE EXISTS (
  SELECT 1
  FROM orders o
  WHERE o.customer_id = c.customer_id
);
```

장점:

* 조건 만족하면 즉시 종료

* IN보다 효율적인 경우 많음

---

# 5. DML :INSERT / UPDATE / DELETE

## 1) DML이란?

> DML(Data Manipulation Language) 은
>
> DB에 저장된 **데이터(행)** 를 추가/수정/삭제하는 SQL이다.

| 명령 | 목적 | 위험도 |
| --- | --- | --- |
| INSERT | 새 행 추가 | 중 |
| UPDATE | 기존 행 변경 | 상 |
| DELETE | 행 삭제 | 최상 |

📌 SELECT는 엄밀하게 DQL(Data Query Language)에 속함.

---

## 2) INSERT (추가)

## 2-1) 기본 INSERT (권장: 컬럼 명시)

```
INSERT INTO customers (email, name, phone)
VALUES ('user21@example.com', 'Hong Gil', '010-1111-0021');
```

* 지정하지 않은 컬럼은 DEFAULT / NULL 적용

* created\_at은 DEFAULT CURRENT\_TIMESTAMP로 자동 입력

---

## 2-2) 다중 행 INSERT (성능상 유리)

```
INSERT INTO products (sku, name, category, price, stock)
VALUES
('SKU-2001','USB Fan','DEVICE',15000,50),
('SKU-2002','Desk Pad','LIVING',12000,80);
```

---

## 2-3) INSERT + SELECT (조회 결과를 삽입)

```
INSERT INTO orders (customer_id, status, ordered_at, total_amount)
SELECT customer_id, 'CREATED', NOW(), 0
FROM customers
WHERE created_at >= NOW() - INTERVAL 7 DAY;
```

---

## 2-4) 중복 처리 패턴 ①: UPSERT (MySQL)

> 재고 누적/동기화에 자주 사용

```
INSERT INTO products (sku, name, category, price, stock)
VALUES ('SKU-1001','USB-C Cable 1m','ACCESSORY',9000,10)
ON DUPLICATE KEY UPDATE
  stock = stock + VALUES(stock);
```

* UNIQUE(sku) 충돌 시 UPDATE 수행

---

## 2-5) INSERT 후 생성된 ID 받기 (AUTO\_INCREMENT)

```
INSERT INTO orders (customer_id, status) VALUES (1, 'CREATED');
SET @oid := LAST_INSERT_ID();

SELECT @oid AS new_order_id;
```

📌 `LAST_INSERT_ID()`는 **세션 단위**라 동시성에서도 안전.

---

## 3) UPDATE (수정)

## 3-1) 가장 안전한 UPDATE: PK로 단건 수정

```
UPDATE customers
SET phone = '010-9999-9999'
WHERE customer_id = 1;
```

* 안전한 이유: 대상 행이 명확함

---

## 3-2) 조건 UPDATE (WHERE 필수)

```
UPDATE orders
SET status = 'CANCELLED'
WHERE status = 'CREATED'
  AND ordered_at < NOW() - INTERVAL 7 DAY;
```

* 이런 UPDATE는 **인덱스 유무**에 따라 성능이 갈림

→ `orders(status, ordered_at)` 같은 인덱스가 없으면 스캔 커짐

---

## 3-3) JOIN UPDATE

> 결제 승인 → 주문 상태 변경

```
UPDATE orders o
JOIN payments p ON p.order_id = o.order_id
SET o.status = 'PAID'
WHERE p.status = 'APPROVED'
  AND o.status = 'CREATED';
```

* 두 테이블의 관계 기반으로 업데이트

* 조인키 인덱스(FK 인덱스)가 매우 중요

---

## 4) DELETE (삭제)

## 4-1) 단건 DELETE (PK 기준)

```
DELETE FROM payments
WHERE payment_id = 3;
```

---

## 4-2) 조건 DELETE

```
DELETE FROM orders
WHERE status = 'CANCELLED'
  AND ordered_at < NOW() - INTERVAL 30 DAY;
```

* 운영에서는 대량 삭제 대신 “아카이빙/논리삭제”가 흔함

---

## 4-3) FK와 DELETE: CASCADE / RESTRICT 이해

현재 스키마 기준:

* `orders → customers` : `ON DELETE RESTRICT`
  + 고객 삭제 시, 주문 있으면 삭제 불가

* `order_items → orders` : `ON DELETE CASCADE`
  + 주문 삭제 시, 주문상세 자동 삭제

* `payments → orders` : `ON DELETE CASCADE`
  + 주문 삭제 시, 결제 자동 삭제

### 확인 실습

```
-- (1) 주문이 있는 고객 삭제 시도 → 실패(Restrict)
DELETE FROM customers WHERE customer_id = 1;

-- (2) 주문 삭제 → order_items/payments 연쇄 삭제(Cascade)
DELETE FROM orders WHERE order_id = 1;
```

---

## 5) 논리 삭제(Soft Delete) 패턴

실제 서비스에서는 물리 DELETE 대신 **상태값 변경**을 많이 쓴다.

```
UPDATE customers
SET status = 'DELETED'
WHERE customer_id = 20;
```

장점:

* 복구 가능

* 감사/추적 가능

* FK 충돌 줄어듦

---

# 6. DDL : CREATE, ALTER, DROP, TRUNCATE

## 1) DDL이란?

> DDL(Data Definition Language) 은
>
> 데이터 자체가 아니라 **데이터의 구조(스키마)** 를 정의·변경·삭제하는 SQL이다.

| 분류 | 명령 |
| --- | --- |
| 생성 | CREATE |
| 변경 | ALTER |
| 삭제 | DROP |
| 초기화 | TRUNCATE |

* **DDL은 “데이터의 틀”을 바꾼다.** → 영향 범위가 크다

---

## 2) DDL vs DML

| 구분 | DDL | DML |
| --- | --- | --- |
| 대상 | 구조(스키마) | 데이터(행) |
| 트랜잭션 | ❌ (자동 커밋) | ⭕ |
| 롤백 | ❌ | ⭕ |
| 위험도 | 매우 높음 | 높음 |
| 운영 영향 | 큼 | 중~큼 |

* **DDL은 실행 순간 확정**

---

## 3) CREATE : 구조 생성

### 3-1) 테이블 생성 (기본형)

```
CREATE TABLE categories (
  category_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(50) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

---

### 3-2) 제약조건 포함 CREATE

```
CREATE TABLE coupons (
  coupon_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  code VARCHAR(50) NOT NULL UNIQUE,
  discount_rate INT NOT NULL CHECK (discount_rate BETWEEN 1 AND 100),
  expires_at DATETIME
) ;
```

* **CREATE 시 제약조건을 넣는 것이 가장 안전**

---

### 3-3) 외래키(FK) 포함 CREATE

```
CREATE TABLE reviews (
  review_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  product_id BIGINT NOT NULL,
  rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
  comment TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_reviews_product
    FOREIGN KEY (product_id)
    REFERENCES products(product_id)
    ON DELETE CASCADE
) ;
```

* **관계 정의는 DDL에서 결정**

---

## 4) ALTER : 구조 변경

---

### 4-1) 컬럼 추가

```
ALTER TABLE customers
ADD COLUMN last_login_at DATETIME;
```

---

### 4-2) 컬럼 수정

```
ALTER TABLE products
MODIFY COLUMN price BIGINT NOT NULL;
```

⚠️ 주의:

* 데이터 타입 변경

* 데이터 손실 가능성

* 대량 테이블은 장애 유발

---

### 4-3) 컬럼 이름 변경

```
ALTER TABLE customers
CHANGE phone phone_number VARCHAR(30);
```

---

### 4-4) 제약조건 추가

```
ALTER TABLE orders
ADD CONSTRAINT chk_total_amount
CHECK (total_amount >= 0);
```

---

---

## 5) DROP : 구조 삭제

### 5-1) 테이블 삭제

```
DROP TABLE coupons;
```

* 데이터 + 구조 **완전 삭제**

* 복구 불가 (백업 없으면 끝)

---

### 5-2) 데이터베이스 삭제

```
DROP DATABASE bootcamp_shop;
```

---

## 6) TRUNCATE : 테이블 초기화

```
TRUNCATE TABLE order_items;
```

| 항목 | DELETE | TRUNCATE |
| --- | --- | --- |
| WHERE | ⭕ | ❌ |
| 롤백 | ⭕ | ❌ |
| 속도 | 느림 | 빠름 |
| 로그 | 남음 | 거의 없음 |
| 실무 사용 | ⭕ | 제한적 |

---

## 7) DDL과 트랜잭션

```
START TRANSACTION;
ALTER TABLE customers ADD COLUMN test INT;
ROLLBACK;
```

* **롤백되지 않는다**

* DDL은:

자동 COMMIT

실행 즉시 반영

---

# 7. DCL : 권한 제어 (GRANT / REVOKE)

---

## 1) DCL이란?

> DCL(Data Control Language) 은
>
> 데이터베이스에 **누가, 무엇을 할 수 있는지**를 제어하는 SQL이다.

| 구분 | 역할 |
| --- | --- |
| DDL | 구조 생성/변경 |
| DML | 데이터 변경 |
| **DCL** | **권한 제어** |
| TCL | 트랜잭션 제어 |

* **DCL은 데이터가 아니라 “사람의 행동”을 제어한다**

---

## 2) 사용자(User)와 권한(Privilege)

### 2-1) 사용자(User)

* DB에 접속하는 주체

* 애플리케이션

* 운영자

* 배치 프로그램

```
CREATE USER 'app_user'@'%' IDENTIFIED BY 'password';
```

---

### 2-2) 권한(Privilege)

* 사용자가 수행할 수 있는 행동

| 권한 | 의미 |
| --- | --- |
| SELECT | 조회 |
| INSERT | 추가 |
| UPDATE | 수정 |
| DELETE | 삭제 |
| CREATE | 테이블 생성 |
| DROP | 테이블 삭제 |
| ALL | 모든 권한 |

* **DCL의 대상은 권한**

---

## 3) GRANT : 권한 부여

### 3-1) 가장 기본적인 GRANT

```
GRANT SELECT ON bootcamp_shop.* TO 'app_user'@'%';
```

의미:

* bootcamp\_shop DB의

* 모든 테이블에 대해

* SELECT만 허용

* **읽기 전용 계정**

---

### 3-2) 특정 테이블만 권한 부여

```
GRANT SELECT, INSERT ON bootcamp_shop.orders TO 'app_user'@'%';
```

* orders 테이블만 접근 가능

* 다른 테이블 접근 ❌

---

### 3-3) 운영 계정 권한 예시

```
GRANT SELECT, INSERT, UPDATE
ON bootcamp_shop.*
TO 'operator'@'%';
```

* 조회/수정 가능

* DROP, TRUNCATE 불가

* **운영 사고 방지**

---

### 3-4) 관리자 권한 (주의)

```
GRANT ALL PRIVILEGES ON bootcamp_shop.* TO 'admin'@'%';
```

---

## 4) REVOKE : 권한 회수(제거)

### 4-1) 특정 권한 제거

```
REVOKE UPDATE ON bootcamp_shop.* FROM 'app_user'@'%';
```

* UPDATE만 제거

* SELECT는 유지

---

### 4-2) 모든 권한 제거

```
REVOKE ALL PRIVILEGES ON bootcamp_shop.* FROM 'app_user'@'%';
```

---

## 5) 권한 확인

### 현재 사용자 권한 확인

```
SHOW GRANTS FOR 'app_user'@'%';
```

* **운영 전 반드시 확인**

---

# 8. VIEW : 가상테이블

---

## 1) VIEW를 한 문장으로

> VIEW는실제 데이터를 저장하지 않는“SELECT 결과를 이름 붙여 저장한 가상 테이블”이다.

---

## 2) 왜 VIEW가 필요한가?

실무 SQL은 점점 이렇게 변한다 👇

```
SELECT ...
FROM orders o
JOIN customers c ON ...
JOIN payments p ON ...
WHERE ...
```

문제점:

* 길다

* 복잡하다

* 매번 다시 써야 한다

* 실수하기 쉽다

👉 **VIEW는 이 문제를 해결한다**

---

## 3) VIEW의 기본 구조

```
CREATE VIEW view_name AS
SELECT ...
FROM ...
WHERE ...;
```

---

## 4) 기본 예제: 주문 + 고객 + 결제 VIEW

### 4-1) VIEW 생성

```
CREATE VIEW v_order_summary AS
SELECT
  o.order_id,
  o.ordered_at,
  o.status        AS order_status,
  o.total_amount,

  c.customer_id,
  c.name          AS customer_name,
  c.email,

  p.payment_id,
  p.method        AS payment_method,
  p.status        AS payment_status
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
LEFT JOIN payments p ON p.order_id = o.order_id;
```

---

### 4-2) VIEW 사용

```
SELECT *
FROM v_order_summary
WHERE order_status = 'PAID'
ORDER BY ordered_at DESC;
```

* **마치 테이블처럼 사용**

---

## 5) VIEW vs 테이블

| 구분 | VIEW | 테이블 |
| --- | --- | --- |
| 데이터 저장 | ❌ | ⭕ |
| 실제 공간 | 없음 | 있음 |
| 최신성 | 항상 최신 | 데이터 시점 |
| 생성 목적 | 가독성/보안 | 데이터 저장 |
| 성능 | 원본 쿼리 영향 | 인덱스 영향 |

* VIEW는 **“저장”이 아니라 “표현”**

---

## 6) VIEW와 보안

### 요구사항

> “운영자는 고객 이름은 보되,
>
> 이메일/전화번호는 못 보게 하자”

---

### VIEW로 해결

```
CREATE VIEW v_customer_public AS
SELECT
  customer_id,
  name,
  status,
  created_at
FROM customers;
```

---

### 권한 부여

```
GRANT SELECT ON v_customer_public TO 'report_user'@'%';
REVOKE SELECT ON customers FROM 'report_user'@'%';
```

* **테이블 직접 접근 차단 + 필요한 컬럼만 공개**

---

## 7) VIEW와 DML (INSERT / UPDATE / DELETE)

### 7-1) VIEW로 조회 (항상 가능)

```
SELECT * FROM v_order_summary;
```

---

### 7-2) VIEW로 UPDATE 가능한 경우 (제한적)

가능 조건(단순 VIEW):

* 단일 테이블 기반

* 집계(GROUP BY) 없음

* DISTINCT 없음

```
UPDATE v_customer_public
SET status = 'SUSPENDED'
WHERE customer_id = 5;
```

* 내부적으로 **원본 테이블 UPDATE**

---

### 7-3) 대부분의 복잡한 VIEW는 읽기 전용

```
-- JOIN + 집계 VIEW
UPDATE v_order_summary SET total_amount = 0;
```

❌ 실패 (대부분 DB에서)

* **VIEW는 기본적으로 읽기 전용으로 생각**

---

## 8) VIEW와 성능 (중요한 오해)

> ❌ “VIEW를 쓰면 성능이 좋아진다”
>
> ⭕ “VIEW는 성능을 바꾸지 않는다”

### 이유

* VIEW는 **쿼리 저장**

* 실행 시 원본 쿼리 그대로 수행

>> **성능은 인덱스/쿼리에 달려 있음**

---

## 9) VIEW vs 서브쿼리 vs CTE

| 구분 | VIEW | 서브쿼리 | CTE |
| --- | --- | --- | --- |
| 재사용 | ⭕ | ❌ | 제한적 |
| 가독성 | ⭕ | ❌ | ⭕ |
| 저장 | ⭕ | ❌ | ❌ |
| 권한 제어 | ⭕ | ❌ | ❌ |

* **보안/공용 로직 → VIEW**

* **일회성 계산 → CTE/서브쿼리**

---

## 10) VIEW 관리 명령

### VIEW 조회

```
SHOW FULL TABLES WHERE Table_type = 'VIEW';
```

---

### VIEW 정의 확인

```
SHOW CREATE VIEW v_order_summary;
```

---

### VIEW 수정

```
CREATE OR REPLACE VIEW v_order_summary AS
SELECT ...
```

---

### VIEW 삭제

```
DROP VIEW v_order_summary;
```

---

## 11) 실습 과제

1. customers 기반 VIEW 생성 (개인정보 제외)

2. 해당 VIEW에 SELECT 권한만 부여

3. 원본 테이블 접근 차단

4. VIEW로 조회 테스트

5. VIEW 수정 후 반영 확인

---

# 9. 트랜잭션

---

## 1) 트랜잭션이 필요한 이유

이 쇼핑몰 스키마에서 “주문 1건”은 실제로 **여러 작업**으로 이루어진다.

* `orders`에 주문 헤더 생성

* `order_items`에 주문 상세 여러 건 생성

* `products.stock` 재고 차감

* `orders.total_amount` 계산/반영

* `payments` 결제 생성/승인

이 작업 중 **하나라도 실패**하면 서비스 데이터가 깨진다.

예시(깨지는 케이스):

* `orders`는 만들어졌는데 `payments`가 실패 → “주문은 있는데 결제가 없음”

* 재고 차감만 되고 주문 생성 실패 → “재고는 줄었는데 주문이 없음”

* 주문상세 일부만 저장 → “주문 금액이 틀림”

>> 트랜잭션은 여러 SQL을 하나의 ‘원자적 작업’으로 묶어, **성공이면 전부 반영, 실패면 전부 취소**하게 해준다.

---

## 2) 트랜잭션 핵심 개념

## A (Atomicity, 원자성)

* 주문 처리 5단계 중 1개라도 실패하면 **전체 롤백**

* “부분 성공” 금지

## C (Consistency, 일관성)

* FK, UNIQUE, CHECK(비슷한 제약) 등을 지키면서 **규칙 위반 불가**

* 예: 존재하지 않는 order\_id로 결제 생성 불가

## I (Isolation, 격리성)

* 동시에 여러 사용자가 주문해도 **서로의 중간 상태가 보이지 않게**

* “동시성 문제(더티 리드/팬텀/갱신 손실)” 방지

## D (Durability, 지속성)

* COMMIT 된 주문/결제는 서버가 죽어도 남아야 함

---

## 3) 실습 준비: 오토커밋 확인

MySQL은 기본이 `autocommit=1`인 경우가 많다. (각 SQL이 자동 COMMIT)

```
SHOW VARIABLES LIKE 'autocommit';
```

* `autocommit = ON`이면, 트랜잭션을 명시적으로 시작해야 한다.

---

## 4) 실습 1: 트랜잭션 기본 TCL(COMMIT / ROLLBACK)

## 4-1. COMMIT

```
START TRANSACTION;

UPDATE products
SET stock = stock - 1
WHERE product_id = 1;

COMMIT;
```

## 4-2. ROLLBACK

```
START TRANSACTION;

UPDATE products
SET stock = stock - 1
WHERE product_id = 2;

ROLLBACK;  -- 방금 UPDATE 취소
```

검증:

```
SELECT product_id, name, stock
FROM products
WHERE product_id IN (1,2);
```

---

# 5) 실습 2: “주문 생성”을 하나의 트랜잭션으로 처리하기

## 목표

고객 1명이 상품 2개를 주문하고 결제까지 생성하는 과정을 **한 트랜잭션**으로 묶는다.

* 상품 1: product\_id=1, qty=2

* 상품 2: product\_id=2, qty=1

* 주문 상태: PAID

* 결제 상태: APPROVED

## 5-1. 트랜잭션 스크립트 (성공 케이스)

```
START TRANSACTION;

-- 1) 주문 헤더 생성
INSERT INTO orders (customer_id, status, ordered_at, total_amount)
VALUES (1, 'PAID', NOW(), 0);

-- 방금 생성된 주문 ID 확보
SET @oid := LAST_INSERT_ID();

-- 2) 주문 상세 생성 (단가를 products에서 가져와 “그 시점 가격”으로 고정하는 게 포인트)
INSERT INTO order_items (order_id, product_id, quantity, unit_price)
SELECT @oid, p.product_id, v.qty, p.price
FROM products p
JOIN (
  SELECT 1 AS product_id, 2 AS qty
  UNION ALL
  SELECT 2, 1
) v ON v.product_id = p.product_id;

-- 3) 재고 차감 (재고 부족 방지 조건 포함)
UPDATE products
SET stock = stock - CASE product_id
  WHEN 1 THEN 2
  WHEN 2 THEN 1
  ELSE 0
END
WHERE product_id IN (1,2)
  AND (
    (product_id = 1 AND stock >= 2) OR
    (product_id = 2 AND stock >= 1)
  );

-- 재고 차감이 2개 상품 모두 반영됐는지 검증 (실무 포인트)
-- 둘 다 성공해야 즉, rowcount=2가 나와야 정상
SELECT ROW_COUNT() AS updated_rows;

-- 4) 주문 합계 계산 후 업데이트
UPDATE orders o
JOIN (
  SELECT order_id, SUM(line_amount) AS s
  FROM order_items
  WHERE order_id = @oid
  GROUP BY order_id
) x ON x.order_id = o.order_id
SET o.total_amount = x.s
WHERE o.order_id = @oid;

-- 5) 결제 생성 (orders.total_amount를 그대로 결제금액으로)
INSERT INTO payments (order_id, method, paid_amount, paid_at, status)
SELECT @oid, 'CARD', total_amount, NOW(), 'APPROVED'
FROM orders
WHERE order_id = @oid;

COMMIT;
```

검증:

```
SELECT * FROM orders WHERE order_id = @oid;
SELECT * FROM order_items WHERE order_id = @oid;
SELECT * FROM payments WHERE order_id = @oid;
SELECT product_id, stock FROM products WHERE product_id IN (1,2);
```

---

## 6) 실습 3: 실패 케이스를 만들고 ROLLBACK 확인

## 케이스: 결제 테이블은 order\_id에 UNIQUE(주문당 결제 1개)가 있음

```
SHOW INDEX FROM payments;
-- uk_payments_order (order_id) 확인
```

### 6-1. 일부러 결제를 두 번 넣어 실패 유도 → 전체 롤백 확인

```
START TRANSACTION;

INSERT INTO orders (customer_id, status, ordered_at, total_amount)
VALUES (2, 'PAID', NOW(), 0);
SET @oid2 := LAST_INSERT_ID();

INSERT INTO order_items (order_id, product_id, quantity, unit_price)
SELECT @oid2, 3, 1, price FROM products WHERE product_id=3;

UPDATE orders
SET total_amount = (
  SELECT SUM(line_amount) FROM order_items WHERE order_id=@oid2
)
WHERE order_id=@oid2;

-- 결제 1회
INSERT INTO payments (order_id, method, paid_amount, paid_at, status)
SELECT @oid2, 'KAKAO', total_amount, NOW(), 'APPROVED'
FROM orders WHERE order_id=@oid2;

-- 결제 2회 (UNIQUE 위반 -> 에러 발생)
INSERT INTO payments (order_id, method, paid_amount, paid_at, status)
SELECT @oid2, 'NAVER', total_amount, NOW(), 'APPROVED'
FROM orders WHERE order_id=@oid2;

-- 여기까지 오면 안 됨 (두 번째 INSERT에서 에러)
COMMIT;
```

에러가 났다면 **반드시**:

```
ROLLBACK;
```

검증(주문 자체가 없어야 정상):

```
SELECT * FROM orders WHERE order_id=@oid2;
SELECT * FROM order_items WHERE order_id=@oid2;
SELECT * FROM payments WHERE order_id=@oid2;
```

---

## 7) 실습 4: SAVEPOINT (부분 롤백)

“결제만 실패하면 주문을 취소 상태로 남기고 싶다” 같은 운영 정책을 사용할 경우.

```
START TRANSACTION;

INSERT INTO orders (customer_id, status, ordered_at, total_amount)
VALUES (3, 'CREATED', NOW(), 0);
SET @oid3 := LAST_INSERT_ID();

INSERT INTO order_items (order_id, product_id, quantity, unit_price)
SELECT @oid3, 4, 1, price FROM products WHERE product_id=4;

UPDATE orders
SET total_amount = (SELECT SUM(line_amount) FROM order_items WHERE order_id=@oid3)
WHERE order_id=@oid3;

SAVEPOINT before_payment;

-- 일부러 결제 실패 유도 (없는 ENUM 값 등)
INSERT INTO payments (order_id, method, paid_amount, paid_at, status)
SELECT @oid3, 'CASH', total_amount, NOW(), 'APPROVED'
FROM orders WHERE order_id=@oid3;

-- 실패 시 여기로 돌아간다
ROLLBACK TO SAVEPOINT before_payment;

-- 결제 실패했으니 주문 상태를 CANCELLED로 변경 후 마무리
UPDATE orders SET status='CANCELLED' WHERE order_id=@oid3;

COMMIT;
```

검증:

```
SELECT * FROM orders WHERE order_id=@oid3;
SELECT * FROM payments WHERE order_id=@oid3; -- 없어야 정상
```

---

## 8) 트랜잭션 격리 수준(Isolation Level)

MySQL(InnoDB) 기본 격리 수준은 보통 `REPEATABLE READ`이다.(환경에 따라 확인 필요).

```
SHOW VARIABLES LIKE 'transaction_isolation';
```

격리 수준 체감은 **2세션 실습**이 좋다.

---

## 9) 실습 5: 2세션으로 “동시성” 체험 (재고 갱신 충돌)

## 목표

동시에 같은 상품 재고를 차감하려 할 때 **락이 어떻게 걸리는지** 본다.

### 세션 A

```
START TRANSACTION;

-- 같은 행을 잡고(잠그고) 있는 상태 유지
SELECT product_id, stock
FROM products
WHERE product_id = 5
FOR UPDATE;

-- (여기서 COMMIT/ROLLBACK 하지 말고 대기)
```

### 세션 B (동시에 실행)

```
START TRANSACTION;

UPDATE products
SET stock = stock - 1
WHERE product_id = 5;

-- 세션 A가 COMMIT할 때까지 대기(락 대기)하게 된다.
```

### 세션 A에서 마무리

```
COMMIT;
```

### 세션 B도 이어서

```
COMMIT;
```

* `SELECT ... FOR UPDATE`는 **해당 행에 배타 락**

* 동시 주문에서 “재고 같은 공유 자원”은 **락/격리**가 없으면 깨짐

---

# 10. 인덱스

# 1) 인덱스의 정의

> 인덱스(Index)란
>
> **테이블의 특정 컬럼(또는 컬럼 조합)을 정렬된 구조(B-Tree 등)로 별도 저장**해서
>
> **검색(WHERE), 정렬(ORDER BY), 조인(JOIN)** 을 빠르게 만드는 자료구조다.

* 데이터(테이블) = 본문

* 인덱스 = 목차

목차가 없으면 책을 처음부터 끝까지 훑어야 한다(Full Table Scan).

---

# 2) 인덱스가 필요한 쿼리 패턴 3가지

## 2-1) WHERE 조건 검색

```
SELECT * FROM customers WHERE email = 'user10@example.com';
```

## 2-2) ORDER BY + LIMIT (Top-N)

```
SELECT * FROM orders ORDER BY ordered_at DESC LIMIT 20;
```

## 2-3) JOIN 키 (FK ↔ PK)

```
SELECT ...
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id;
```

---

# 3) 현재 스키마에 이미 존재하는 인덱스 확인

```
SHOW INDEX FROM customers;
SHOW INDEX FROM products;
SHOW INDEX FROM orders;
SHOW INDEX FROM order_items;
SHOW INDEX FROM payments;
```

### 스키마상 핵심 인덱스

* `customers` : `PRIMARY(customer_id)`, `UNIQUE(email)`

* `products` : `PRIMARY(product_id)`, `UNIQUE(sku)`

* `orders` : `PRIMARY(order_id)`, `INDEX idx_orders_customer_ordered(customer_id, ordered_at)`

* `order_items` : `INDEX idx_order_items_order(order_id)`, `INDEX idx_order_items_product(product_id)`

* `payments` : `UNIQUE(order_id)` (주문당 결제 1개)

---

# 4) EXPLAIN으로 “인덱스가 쓰였는지” 확인하는 법

## 4-1) 고객 이메일 검색 (UNIQUE 인덱스)

```
EXPLAIN
SELECT customer_id, name, status
FROM customers
WHERE email = 'user10@example.com';
```

### 확인:

* `key`에 `uk_customers_email`이 잡히면 인덱스 사용

* `type`이 `const` 또는 `ref`면 매우 좋음

* `rows`가 작을수록 좋음

---

## 4-2) 주문: 고객별 최근 주문 10건 (복합 인덱스 사용)

```
EXPLAIN
SELECT order_id, ordered_at, total_amount
FROM orders
WHERE customer_id = 1
ORDER BY ordered_at DESC
LIMIT 10;
```

* `idx_orders_customer_ordered(customer_id, ordered_at)`가 **딱 맞는 이유**
  + WHERE에서 customer\_id로 좁히고
  + ordered\_at으로 정렬 + LIMIT

---

# 5) 인덱스 설계 원칙

## 5-1) “선행 컬럼” 규칙 (복합 인덱스의 핵심)

복합 인덱스 `(A, B)`는 아래는 빠름:

* `WHERE A = ...`

* `WHERE A = ... AND B = ...`

* `WHERE A = ... ORDER BY B ...`

하지만 아래는 보통 못 씀(인덱스 효율 낮음):

* `WHERE B = ...` 만

예: 현재 존재하는 인덱스

* `idx_orders_customer_ordered(customer_id, ordered_at)`
  + 고객별 주문 조회/정렬에 최적

---

## 5-2) 선택도(Selectivity)가 높은 컬럼이 유리

* 값 종류가 많아야(중복이 적어야) 인덱스 효과 큼

예:

* email(거의 유일) → 인덱스 매우 유리

* status(종류 3~5개) → 인덱스 효율 낮을 수 있음

---

## 5-3) 인덱스는 “읽기”를 빠르게 하지만 “쓰기”는 느리게 한다

INSERT/UPDATE/DELETE 시:

* 테이블 변경 + 인덱스도 같이 갱신해야 함

따라서 **인덱스를 무작정 많이 만들면**:

* 쓰기 성능 하락

* 디스크/메모리 사용 증가

---

# 6) 실습: 인덱스 유무 비교

## 6-1) PK 조회 (인덱스 사용)

```
EXPLAIN
SELECT product_id, name
FROM products
WHERE product_id=1;
```

### 실행 계획 핵심

```
type = const
key  = PRIMARY
rows = 1
```

* DB가 **딱 1건만 읽고 끝냄**

* 가장 이상적인 접근 방식

---

## 6-2) 인덱스 없는 컬럼 조회 (Full Scan)

```
EXPLAIN
SELECT product_id, name
FROM products
WHERE name='USB-C Cable 1m';
```

### 실행 계획 예상

```
type = ALL
key  = NULL
rows = 30
```

---

# 7) JOIN에서 인덱스가 중요한 이유

## 7-1) 주문상세에서 주문별 아이템 조회

```
EXPLAIN
SELECT *
FROM order_items
WHERE order_id = 1;
```

* `idx_order_items_order(order_id)` 덕분에 빠름

* 없다면 order\_items 전체 스캔 위험

---

### JOIN 쿼리

```
SELECT*
FROM orders o
JOIN order_items oi
ON o.order_id= oi.order_id
WHERE o.order_id=1;
```

## 인덱스가 있을 때 vs 없을 때 (JOIN 관점)

### 🔹 인덱스 있음

```
order_items.idx_order_items_order(order_id)
```

* DB가:
  + order\_id = 1 인 위치로 **바로 점프**
  + 해당 주문의 아이템 몇 건만 읽음

>> JOIN 시:

* orders 1건

* order\_items 2~3건

* **총 읽는 row 수 매우 작음**

---

## 🔹 인덱스 없음

```
WHERE order_id = 1
```

* DB가:
  + order\_items **전체를 다 읽고**
  + order\_id = 1 인 row만 골라냄

👉 JOIN 시:

* orders 1건

* order\_items 전체 N건 스캔

# 8) 운영 관점 체크리스트

* “느린 쿼리”가 발생하면
  1. `EXPLAIN`으로 실행계획 확인
  2. Full Scan인지 확인(`type=ALL`)
  3. WHERE/JOIN/ORDER BY 컬럼 기준으로 인덱스 검토

* 인덱스 추가는 성능 만능 해결책이 아님
  + 쓰기량 많은 테이블은 인덱스 최소화

* RDS 같은 Managed DB에서도
  + 인덱스 설계는 사용자가 책임짐

---

# 11. 백업/복구

# 1) 왜 백업/복구는 “옵션”이 아닌가

> “DB 장애는 ‘언젠가 반드시’ 발생한다.문제는 ‘발생하느냐’가 아니라‘얼마나 빨리 복구하느냐’다.”

---

## 실제로 자주 발생하는 사고

| 사고 유형 | 결과 |
| --- | --- |
| DELETE / UPDATE 실수 | 데이터 영구 손실 |
| 애플리케이션 버그 | 대량 데이터 오염 |
| 디스크 장애 | DB 기동 불가 |
| 잘못된 마이그레이션 | 구조/데이터 파손 |
| 랜섬웨어 | 전체 암호화 |

* **오직 백업/복구만 가능**

---

# 2) 백업의 기본 개념

## 백업 ≠ 복구

> ❌ “백업 파일이 있다”
>
> ⭕ “복구가 실제로 된다”

### 반드시 세트로 기억할 것

* 백업만 있고 복구 테스트 안 함 → **백업 없음과 동일**

* 운영에서는 **“복구 시점”이 핵심**

---

# 3) 백업의 두 가지 큰 분류

## 3-1) 논리 백업 (Logical Backup)

### 개념

* SQL 형태로 데이터 덤프

* 사람이 읽을 수 있음

### 대표 도구

* `mysqldump`

---

### 예제: 전체 DB 백업

```
mysqldump -u root -p bootcamp_shop > bootcamp_shop.sql
```

---

### 특정 테이블만 백업

```
mysqldump -u root -p bootcamp_shop orders order_items > orders_backup.sql
```

---

### 장점 / 단점

| 장점 | 단점 |
| --- | --- |
| 단순 | 대용량 느림 |
| 이식성 좋음 | 복구 시간 김 |
| 부분 복구 쉬움 | 락/성능 영향 |

* **교육/소규모 서비스/테이블 단위 복구**에 적합

---

## 3-2) 물리 백업 (Physical Backup)

### 개념

* DB 데이터 파일 자체를 복사

* 사람이 직접 보긴 어려움

### 대표 도구

* `Percona XtraBackup`

* 클라우드 스냅샷(EBS, Disk Snapshot)

---

### 특징

| 장점 | 단점 |
| --- | --- |
| 매우 빠름 | 구조 의존 |
| 대용량 적합 | 부분 복구 어려움 |
| 운영 서비스 친화 | 설정 복잡 |

>> **운영 서비스 / 대규모 DB 필수**

---

# 4) 트랜잭션과 백업의 관계

### 질문

> “백업 중에 데이터가 바뀌면 어떻게 되나?”

### 답

* **트랜잭션 로그(Log)** 덕분에 **일관성 있는 백업 가능**

---

### InnoDB + 트랜잭션 덕분에 가능한 것

* 백업 도중에도:
  + 읽기/쓰기 계속 가능
  + 깨진 데이터 없이 백업

>> **InnoDB + 트랜잭션 = 백업 가능성의 전제 조건**

---

# 5) 복구(RESTORE)의 실제 의미

## 복구란 무엇인가?

> “DB를 특정 시점 상태로 되돌리는 작업”

---

## 5-1) 논리 백업 복구

```
mysql -u root -p bootcamp_shop < bootcamp_shop.sql
```

>> 특징:

* 테이블 DROP 후 다시 생성됨

* 인덱스도 같이 재생성됨

* 시간 오래 걸릴 수 있음

---

## 5-2) 특정 시점 복구(Point-in-Time Recovery, PITR)

### 개념

* 전체 백업 + **Binary Log**

* “어제 14:32:10 상태로 복구”

---

### 개념 흐름

```
[전체 백업] + [binlog 재생]
```

---

### binlog 확인

```
SHOW VARIABLES LIKE 'log_bin';
```

---

### binlog 기반 복구 흐름

```
mysqlbinlog binlog.000001 | mysql -u root -p

- 특정 시간으로 복구
mysqlbinlog \
  --stop-datetime="2026-01-29 14:30:00" \
  binlog.000001 | mysql -u root -p
```

---

# 6) 인덱스와 백업/복구의 관계

## 중요한 사실

> 인덱스도 데이터다.백업/복구 대상이다.

---

### 논리 백업 시

* `CREATE INDEX` 문도 함께 저장

* 복구 시 **인덱스 재생성 → 시간 소요**

### 물리 백업 시

* 인덱스 포함된 상태로 복구

* **훨씬 빠름**

📌 대규모 DB에서 물리 백업을 쓰는 이유

---

# 7) 클라우드 환경에서의 백업

## 7-1) Managed DB (RDS, Cloud SQL)

### 제공 기능

* 자동 백업

* 스냅샷

* PITR

> ❗ 설정과 책임은 사용자에게 있음

* 보존 기간

* 백업 주기

* 복구 테스트 여부

---

## 7-2) EC2 / VM 직접 설치 DB

> **전부 엔지니어 책임**

* 백업 스크립트

* 스케줄링(cron)

* 외부 저장소(S3, NFS)

* 암호화

---