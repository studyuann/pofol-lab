---
title: "실습 문제(MySQL)"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "데이터베이스", "RDB(Relational DataBase)"]
is_public: true
draft: false
---

# 실습 문제(MySQL)

### A. 단일 쿼리 (10문제)

**Q1.** customers 테이블에서 `ACTIVE` 고객만 조회하고, `created_at` 최신순으로 10명만 출력하시오.

(출력: customer\_id, email, name, created\_at)

**Q2.** products에서 `category='STORAGE'` 인 상품 중 `price >= 150000` 인 상품을 가격 내림차순으로 조회하시오.

(출력: product\_id, sku, name, price)

**Q3.** products에서 `stock <= 30` 인 “재고 부족” 상품을 stock 오름차순으로 조회하시오.

(출력: product\_id, name, stock)

**Q4.** orders에서 `status='CANCELLED'` 주문만 조회하시오. (출력: order\_id, customer\_id, ordered\_at)

**Q5.** orders에서 최근 7일 이내 주문을 조회하시오. (출력: order\_id, customer\_id, status, ordered\_at)

**Q6.** customers에서 email이 `user%` 패턴인 고객을 조회하시오. (출력: customer\_id, email, name)

**Q7.** orders에서 `total_amount`가 100,000 이상인 주문을 total\_amount 내림차순으로 조회하시오.

(출력: order\_id, total\_amount)

**Q8.** products에서 `name`에 “Cable”이 포함된 상품을 조회하시오. (출력: product\_id, name)

**Q9.** payments에서 결제수단별(method) 결제 건수를 조회하시오. (출력: method, cnt)

**Q10.** orders에서 status별 주문 건수를 조회하고, 건수 내림차순 정렬하시오. (출력: status, cnt)

---

### B. 조인 (10문제)

**Q11.** 주문 1건(order\_id=1)의 주문자 이름과 주문일시를 조회하시오.

(orders + customers)

**Q12.** 결제가 존재하는 주문에 대해 주문번호, 고객명, 결제수단, 결제금액을 조회하시오.

(orders + customers + payments)

**Q13.** 각 주문의 주문금액(orders.total\_amount)과 “실제 주문상세 합계(SUM(order\_items.line\_amount))”를 함께 보여 차이가 있는 주문만 조회하시오.

(orders + order\_items)

**Q14.** 주문상세 기준으로, 주문번호별 아이템 개수(라인 수)를 조회하시오.

(출력: order\_id, item\_lines)

**Q15.** 주문상세 기준으로 상품별 총 판매수량(quantity 합)을 조회하고, 판매수량 TOP 5를 출력하시오.

(order\_items + products)

**Q16.** 고객별 총 주문금액(orders.total\_amount 합)을 조회하고, 총액 TOP 5를 출력하시오.

(orders + customers)

**Q17.** 아직 결제가 없는 주문(미결제)을 조회하시오.

(orders LEFT JOIN payments)

**Q18.** 주문상세와 상품을 조인해서, 주문 10번의 상품명/수량/단가/라인금액을 출력하시오.

(order\_items + products)

**Q19.** 고객별 주문 건수와 최근 주문일(ordered\_at MAX)을 함께 조회하시오.

(orders + customers)

**Q20.** `SHIPPED` 상태 주문에 대해 주문번호, 고객명, 주문일시, 주문금액을 조회하시오.

(orders + customers)

---

### C. 함수/집계/날짜 (10문제)

**Q21.** orders에서 주문일(ordered\_at)을 날짜(YYYY-MM-DD)로만 보여 주문일별 주문 건수를 조회하시오.

(출력: order\_date, cnt)

**Q22.** payments에서 결제일(paid\_at) 기준 월(YYYY-MM)별 결제 합계를 조회하시오.

(출력: pay\_month, total\_paid)

**Q23.** customers에서 가입일(created\_at) 기준 “며칠 전 가입했는지”를 day\_diff로 출력하시오.

(출력: customer\_id, name, day\_diff)

**Q24.** products에서 카테고리별 평균가격(AVG)과 최고가(MAX), 최저가(MIN)를 조회하시오.

(출력: category, avg\_price, max\_price, min\_price)

**Q25.** orders에서 주문금액 구간을 분류해(CASE) 집계하시오.

* 0~49999: 'LOW'

* 50000~199999: 'MID'

* 200000 이상: 'HIGH'

  (출력: bucket, cnt)

**Q26.** customers에서 phone이 NULL인 고객 수를 조회하시오.

**Q27.** products에서 sku가 'SKU-10%' 인 상품 수를 조회하시오.

**Q28.** orders에서 고객별 평균 주문금액을 구하되, 주문이 2건 이상인 고객만 출력하시오.

(출력: customer\_id, avg\_amount, order\_cnt)

**Q29.** payments에서 결제수단별 평균 결제금액을 조회하시오. (출력: method, avg\_paid)

**Q30.** order\_items에서 주문당 총 수량(quantity 합)을 구하고, 총 수량이 4 이상인 주문만 출력하시오.

(출력: order\_id, total\_qty)

---

### D. 뷰 (10문제)

**Q31. (생성)** 고객 기본정보 뷰 `v_customers_active` 를 생성하시오.

조건: status='ACTIVE' / 컬럼: customer\_id, email, name, created\_at

**Q32. (생성)** 주문+고객 조합 뷰 `v_orders_customer` 를 생성하시오.

컬럼: order\_id, customer\_id, customer\_name, status, ordered\_at, total\_amount

**Q33. (생성)** 주문상세 확장 뷰 `v_order_items_detail` 을 생성하시오.

(order\_items + products)

컬럼: order\_id, order\_item\_id, product\_id, product\_name, category, quantity, unit\_price, line\_amount

**Q34. (생성)** 결제 포함 주문 뷰 `v_paid_orders` 를 생성하시오.

(orders + payments)

컬럼: order\_id, status as order\_status, method, paid\_amount, paid\_at, payment\_status

**Q35. (생성)** 고객별 누적 구매액 뷰 `v_customer_total_spend` 를 생성하시오.

(orders + customers)

컬럼: customer\_id, customer\_name, total\_spend, order\_cnt

**Q36. (활용)** `v_customers_active`에서 가입일 최신 5명을 조회하시오.

**Q37. (활용)** `v_orders_customer`에서 최근 14일 주문만 조회하시오. (정렬: ordered\_at DESC)

**Q38. (활용)** `v_order_items_detail`에서 category='DEVICE' 상품의 총 판매수량을 조회하시오.

(출력: product\_id, product\_name, total\_qty)

**Q39. (활용)** `v_paid_orders`에서 결제수단별 결제합계를 조회하시오. (출력: method, total\_paid)

**Q40. (활용)** `v_customer_total_spend`에서 total\_spend TOP 5를 조회하시오.

---

## 2) 트랜잭션 실습 (5문제)

> 핵심: COMMIT/ROLLBACK, 재고 차감, 주문 생성, 결제 반영(샘플 수준)

**T1.** 트랜잭션을 시작하고, customers에 신규 고객 1명을 INSERT 후 ROLLBACK 하시오.

→ ROLLBACK 이후 고객이 남아있지 않아야 함.

**T2.** 트랜잭션을 시작하고, order\_id=30 주문의 status를 'PAID'로 변경한 뒤 COMMIT 하시오.

**T3.** 트랜잭션으로 “주문 1건 + 주문상세 1~2건”을 생성하시오.

요구:

1. orders에 customer\_id=1, status='CREATED'로 1건 생성

2. 방금 생성된 order\_id로 order\_items 2건 추가 (상품 1,2 적당 수량)

3. orders.total\_amount를 order\_items 합계로 업데이트

4. COMMIT

**T4.** (실패 시 롤백) 트랜잭션에서 아래를 수행하시오.

* products.product\_id=24(NAS 2-bay)의 stock을 1 감소

* 만약 stock이 0 미만이 되면 ROLLBACK 처리(수동으로 조건 체크 쿼리 작성)

**T5.** 트랜잭션에서 주문 취소 처리: order\_id=5를 'CANCELLED'로 변경하고, 해당 주문의 결제(payments)가 있으면 payment.status='CANCELLED'로 변경 후 COMMIT 하시오.

---

## 3) 인덱스 실습 (5문제)

> 핵심: 인덱스 생성/확인/플랜 비교

**I1.** orders에서 최근 7일 주문 조회 쿼리에 대해 EXPLAIN을 실행하시오.

**I2.** payments에서 method 조건 조회를 빠르게 하기 위해 (method, paid\_at) 복합 인덱스를 생성하시오.

인덱스명: idx\_payments\_method\_paidat

**I3.** products에서 category + price 조건에 대한 복합 인덱스를 생성하시오.

인덱스명: idx\_products\_category\_price

**I4.** order\_items에서 (product\_id, order\_id) 복합 인덱스를 생성하시오.

인덱스명: idx\_order\_items\_product\_order

**I5.** 방금 생성한 인덱스 목록을 확인하는 쿼리를 작성하시오.

(테이블별로 확인)

---