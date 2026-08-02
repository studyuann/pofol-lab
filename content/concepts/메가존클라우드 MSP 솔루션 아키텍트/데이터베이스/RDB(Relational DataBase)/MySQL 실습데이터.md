---
title: "MySQL 실습데이터"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "데이터베이스", "RDB(Relational DataBase)"]
is_public: true
draft: false
---

# MySQL 실습데이터

```
USE bootcamp_shop;

-- 안전을 위해 기존 테이블 제거 (실습 재실행 용이)
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;
SET FOREIGN_KEY_CHECKS = 1;

-- 1) 고객
CREATE TABLE customers (
  customer_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  email VARCHAR(255) NOT NULL,
  name VARCHAR(100) NOT NULL,
  phone VARCHAR(30),
  status ENUM('ACTIVE','SUSPENDED','DELETED') NOT NULL DEFAULT 'ACTIVE',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_customers_email (email)
) ENGINE=InnoDB;

-- 2) 상품
CREATE TABLE products (
  product_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  sku VARCHAR(50) NOT NULL,
  name VARCHAR(200) NOT NULL,
  category VARCHAR(50) NOT NULL,
  price INT NOT NULL,
  stock INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_products_sku (sku)
) ENGINE=InnoDB;

-- 3) 주문(헤더)
CREATE TABLE orders (
  order_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  customer_id BIGINT NOT NULL,
  status ENUM('CREATED','PAID','SHIPPED','CANCELLED','REFUNDED') NOT NULL DEFAULT 'CREATED',
  ordered_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  total_amount INT NOT NULL DEFAULT 0,
  INDEX idx_orders_customer_ordered (customer_id, ordered_at),
  CONSTRAINT fk_orders_customer
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 4) 주문상세
CREATE TABLE order_items (
  order_item_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  order_id BIGINT NOT NULL,
  product_id BIGINT NOT NULL,
  quantity INT NOT NULL,
  unit_price INT NOT NULL,
  line_amount INT GENERATED ALWAYS AS (quantity * unit_price) STORED,
  INDEX idx_order_items_order (order_id),
  INDEX idx_order_items_product (product_id),
  CONSTRAINT fk_order_items_order
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_order_items_product
    FOREIGN KEY (product_id) REFERENCES products(product_id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 5) 결제
CREATE TABLE payments (
  payment_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  order_id BIGINT NOT NULL,
  method ENUM('CARD','BANK','KAKAO','NAVER') NOT NULL,
  paid_amount INT NOT NULL,
  paid_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  status ENUM('REQUESTED','APPROVED','FAILED','CANCELLED') NOT NULL DEFAULT 'APPROVED',
  UNIQUE KEY uk_payments_order (order_id),
  CONSTRAINT fk_payments_order
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- -----------------------------
-- 샘플 데이터 입력
-- -----------------------------

-- 고객 20명
INSERT INTO customers (email, name, phone, status, created_at) VALUES
('user01@example.com','Kim Mina','010-1111-0001','ACTIVE', NOW() - INTERVAL 40 DAY),
('user02@example.com','Lee Jisu','010-1111-0002','ACTIVE', NOW() - INTERVAL 35 DAY),
('user03@example.com','Park Jun','010-1111-0003','ACTIVE', NOW() - INTERVAL 30 DAY),
('user04@example.com','Choi Hana','010-1111-0004','ACTIVE', NOW() - INTERVAL 25 DAY),
('user05@example.com','Jung Sora','010-1111-0005','ACTIVE', NOW() - INTERVAL 20 DAY),
('user06@example.com','Kang Dae','010-1111-0006','ACTIVE', NOW() - INTERVAL 18 DAY),
('user07@example.com','Yoon Ara','010-1111-0007','ACTIVE', NOW() - INTERVAL 16 DAY),
('user08@example.com','Han Sol','010-1111-0008','ACTIVE', NOW() - INTERVAL 14 DAY),
('user09@example.com','Shin Woo','010-1111-0009','ACTIVE', NOW() - INTERVAL 12 DAY),
('user10@example.com','Lim Hye','010-1111-0010','ACTIVE', NOW() - INTERVAL 10 DAY),
('user11@example.com','Oh Jin','010-1111-0011','ACTIVE', NOW() - INTERVAL 9 DAY),
('user12@example.com','Seo Yuri','010-1111-0012','ACTIVE', NOW() - INTERVAL 8 DAY),
('user13@example.com','Song Min','010-1111-0013','ACTIVE', NOW() - INTERVAL 7 DAY),
('user14@example.com','Ahn Jae','010-1111-0014','ACTIVE', NOW() - INTERVAL 6 DAY),
('user15@example.com','Jeon Nari','010-1111-0015','ACTIVE', NOW() - INTERVAL 5 DAY),
('user16@example.com','Baek Hyun','010-1111-0016','ACTIVE', NOW() - INTERVAL 4 DAY),
('user17@example.com','Kwon Bora','010-1111-0017','ACTIVE', NOW() - INTERVAL 3 DAY),
('user18@example.com','Hwang Kyu','010-1111-0018','ACTIVE', NOW() - INTERVAL 2 DAY),
('user19@example.com','Woo Sena','010-1111-0019','ACTIVE', NOW() - INTERVAL 1 DAY),
('user20@example.com','Ryu Taek','010-1111-0020','ACTIVE', NOW()),
('user21@example.com','No Order User1','010-1111-0021','ACTIVE', NOW()),
('user22@example.com','No Order User2','010-1111-0022','ACTIVE', NOW());


-- 상품 30개
INSERT INTO products (sku, name, category, price, stock, created_at) VALUES
('SKU-1001','USB-C Cable 1m','ACCESSORY',9000, 200, NOW() - INTERVAL 60 DAY),
('SKU-1002','USB-C Charger 20W','ACCESSORY',19000, 150, NOW() - INTERVAL 55 DAY),
('SKU-1003','Bluetooth Mouse','DEVICE',25000, 120, NOW() - INTERVAL 50 DAY),
('SKU-1004','Mechanical Keyboard','DEVICE',85000, 80, NOW() - INTERVAL 45 DAY),
('SKU-1005','27-inch Monitor','DEVICE',260000, 40, NOW() - INTERVAL 40 DAY),
('SKU-1006','Laptop Stand','ACCESSORY',29000, 140, NOW() - INTERVAL 35 DAY),
('SKU-1007','Webcam 1080p','DEVICE',49000, 60, NOW() - INTERVAL 30 DAY),
('SKU-1008','Noise Cancel Headset','DEVICE',139000, 30, NOW() - INTERVAL 28 DAY),
('SKU-1009','Portable SSD 1TB','STORAGE',129000, 50, NOW() - INTERVAL 26 DAY),
('SKU-1010','USB Hub','ACCESSORY',22000, 110, NOW() - INTERVAL 24 DAY),
('SKU-1011','Desk Lamp','LIVING',30000, 90, NOW() - INTERVAL 22 DAY),
('SKU-1012','Ergo Chair','LIVING',199000, 20, NOW() - INTERVAL 20 DAY),
('SKU-1013','Notebook A5','STATIONERY',4000, 500, NOW() - INTERVAL 18 DAY),
('SKU-1014','Pen Set','STATIONERY',6000, 400, NOW() - INTERVAL 16 DAY),
('SKU-1015','Backpack','FASHION',59000, 70, NOW() - INTERVAL 15 DAY),
('SKU-1016','T-Shirt','FASHION',19000, 200, NOW() - INTERVAL 14 DAY),
('SKU-1017','Hoodie','FASHION',49000, 100, NOW() - INTERVAL 13 DAY),
('SKU-1018','Water Bottle','LIVING',15000, 180, NOW() - INTERVAL 12 DAY),
('SKU-1019','Coffee Beans 1kg','FOOD',32000, 60, NOW() - INTERVAL 11 DAY),
('SKU-1020','Mug Cup','LIVING',12000, 160, NOW() - INTERVAL 10 DAY),
('SKU-1021','Smart Plug','DEVICE',18000, 90, NOW() - INTERVAL 9 DAY),
('SKU-1022','Router AX1800','DEVICE',89000, 35, NOW() - INTERVAL 8 DAY),
('SKU-1023','Ethernet Cable 5m','ACCESSORY',7000, 300, NOW() - INTERVAL 7 DAY),
('SKU-1024','NAS 2-bay','STORAGE',399000, 10, NOW() - INTERVAL 6 DAY),
('SKU-1025','HDD 8TB','STORAGE',219000, 15, NOW() - INTERVAL 6 DAY),
('SKU-1026','SSD 2TB','STORAGE',179000, 25, NOW() - INTERVAL 5 DAY),
('SKU-1027','HDMI Cable 2m','ACCESSORY',8000, 250, NOW() - INTERVAL 4 DAY),
('SKU-1028','Phone Case','ACCESSORY',12000, 220, NOW() - INTERVAL 3 DAY),
('SKU-1029','Screen Protector','ACCESSORY',6000, 350, NOW() - INTERVAL 2 DAY),
('SKU-1030','Gift Card 50k','ETC',50000, 9999, NOW() - INTERVAL 1 DAY);

-- 주문 60건 생성 (간단히 반복 느낌을 수동으로 구성)
-- 주문 금액은 나중에 UPDATE로 계산
INSERT INTO orders (customer_id, status, ordered_at, total_amount) VALUES
(1,'PAID', NOW() - INTERVAL 29 DAY, 0),
(2,'PAID', NOW() - INTERVAL 28 DAY, 0),
(3,'PAID', NOW() - INTERVAL 27 DAY, 0),
(4,'SHIPPED', NOW() - INTERVAL 26 DAY, 0),
(5,'PAID', NOW() - INTERVAL 25 DAY, 0),
(6,'CANCELLED', NOW() - INTERVAL 24 DAY, 0),
(7,'PAID', NOW() - INTERVAL 23 DAY, 0),
(8,'PAID', NOW() - INTERVAL 22 DAY, 0),
(9,'SHIPPED', NOW() - INTERVAL 21 DAY, 0),
(10,'PAID', NOW() - INTERVAL 20 DAY, 0),
(11,'PAID', NOW() - INTERVAL 19 DAY, 0),
(12,'PAID', NOW() - INTERVAL 18 DAY, 0),
(13,'PAID', NOW() - INTERVAL 17 DAY, 0),
(14,'REFUNDED', NOW() - INTERVAL 16 DAY, 0),
(15,'PAID', NOW() - INTERVAL 15 DAY, 0),
(16,'PAID', NOW() - INTERVAL 14 DAY, 0),
(17,'PAID', NOW() - INTERVAL 13 DAY, 0),
(18,'SHIPPED', NOW() - INTERVAL 12 DAY, 0),
(19,'PAID', NOW() - INTERVAL 11 DAY, 0),
(20,'PAID', NOW() - INTERVAL 10 DAY, 0),
(1,'PAID', NOW() - INTERVAL 9 DAY, 0),
(2,'PAID', NOW() - INTERVAL 8 DAY, 0),
(3,'CANCELLED', NOW() - INTERVAL 7 DAY, 0),
(4,'PAID', NOW() - INTERVAL 6 DAY, 0),
(5,'PAID', NOW() - INTERVAL 5 DAY, 0),
(6,'PAID', NOW() - INTERVAL 4 DAY, 0),
(7,'PAID', NOW() - INTERVAL 3 DAY, 0),
(8,'PAID', NOW() - INTERVAL 2 DAY, 0),
(9,'PAID', NOW() - INTERVAL 1 DAY, 0),
(10,'CREATED', NOW(), 0);

-- 주문상세(각 주문당 2~3개 품목 느낌으로 수동 구성)
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
(1, 1, 2, 9000), (1, 2, 1, 19000),
(2, 3, 1, 25000), (2, 10, 1, 22000),
(3, 4, 1, 85000), (3, 13, 3, 4000),
(4, 5, 1, 260000), (4, 27, 2, 8000),
(5, 6, 1, 29000), (5, 11, 1, 30000),
(6, 8, 1, 139000), (6, 20, 2, 12000),
(7, 9, 1, 129000), (7, 23, 2, 7000),
(8, 12, 1, 199000), (8, 18, 2, 15000),
(9, 7, 1, 49000), (9, 10, 1, 22000), (9, 1, 1, 9000),
(10, 22, 1, 89000), (10, 23, 3, 7000),
(11, 15, 1, 59000), (11, 16, 2, 19000),
(12, 17, 1, 49000), (12, 14, 2, 6000),
(13, 19, 1, 32000), (13, 20, 2, 12000),
(14, 3, 1, 25000), (14, 2, 1, 19000), (14, 28, 1, 12000),
(15, 24, 1, 399000), (15, 25, 1, 219000),
(16, 26, 1, 179000), (16, 27, 2, 8000),
(17, 21, 2, 18000), (17, 1, 2, 9000),
(18, 5, 1, 260000), (18, 8, 1, 139000),
(19, 29, 3, 6000), (19, 28, 1, 12000),
(20, 30, 1, 50000), (20, 13, 5, 4000);

-- 결제는 PAID/SHIPPED/REFUNDED 주문에 대해 생성(일부만)
INSERT INTO payments (order_id, method, paid_amount, paid_at, status) VALUES
(1,'CARD',0, NOW() - INTERVAL 29 DAY, 'APPROVED'),
(2,'KAKAO',0, NOW() - INTERVAL 28 DAY, 'APPROVED'),
(3,'CARD',0, NOW() - INTERVAL 27 DAY, 'APPROVED'),
(4,'BANK',0, NOW() - INTERVAL 26 DAY, 'APPROVED'),
(5,'NAVER',0, NOW() - INTERVAL 25 DAY, 'APPROVED'),
(7,'CARD',0, NOW() - INTERVAL 23 DAY, 'APPROVED'),
(8,'BANK',0, NOW() - INTERVAL 22 DAY, 'APPROVED'),
(9,'CARD',0, NOW() - INTERVAL 21 DAY, 'APPROVED'),
(10,'KAKAO',0, NOW() - INTERVAL 20 DAY, 'APPROVED'),
(14,'CARD',0, NOW() - INTERVAL 16 DAY, 'APPROVED'),
(15,'BANK',0, NOW() - INTERVAL 15 DAY, 'APPROVED'),
(18,'CARD',0, NOW() - INTERVAL 12 DAY, 'APPROVED'),
(19,'NAVER',0, NOW() - INTERVAL 11 DAY, 'APPROVED'),
(20,'CARD',0, NOW() - INTERVAL 10 DAY, 'APPROVED');

-- 주문 합계 계산: order_items 합계로 orders.total_amount 업데이트
UPDATE orders o
JOIN (
  SELECT order_id, SUM(line_amount) AS s
  FROM order_items
  GROUP BY order_id
) x ON x.order_id = o.order_id
SET o.total_amount = x.s;

-- payments.paid_amount도 orders.total_amount로 맞춤
UPDATE payments p
JOIN orders o ON o.order_id = p.order_id
SET p.paid_amount = o.total_amount;

-- 데이터 확인
SELECT COUNT(*) AS customers FROM customers;
SELECT COUNT(*) AS products FROM products;
SELECT COUNT(*) AS orders FROM orders;
SELECT COUNT(*) AS order_items FROM order_items;
SELECT COUNT(*) AS payments FROM payments;
```