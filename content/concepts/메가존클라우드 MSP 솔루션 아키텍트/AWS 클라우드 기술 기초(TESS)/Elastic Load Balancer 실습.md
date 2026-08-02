---
title: "Elastic Load Balancer 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 클라우드 기술 기초(TESS)"]
is_public: true
draft: false
---

# Elastic Load Balancer 실습

---

# 실습 목표

본 실습에서는 AWS에서 **Application Load Balancer(ALB)** 를 생성하고 EC2 인스턴스를 대상으로 트래픽을 분산하는 방법을 학습한다.

실습을 통해 다음 내용을 이해한다.

* Load Balancer의 역할

* Target Group의 개념

* EC2 인스턴스를 대상으로 트래픽 분산

* ALB DNS를 이용한 웹 서비스 접속

---

# 실습 아키텍처

```
Internet
    │
    │
Application Load Balancer (이니셜-alb-web)
    │
    │
Target Group (이니셜-tg-web)
    │
    │
EC2 Instance (이니셜-ec2-web)
```

Load Balancer는 외부에서 들어오는 트래픽을 받아 Target Group에 등록된 EC2 인스턴스로 전달하는 역할을 한다.

---

# 1. Security Group 생성

ALB에서 사용할 보안 그룹을 생성한다.

EC2 콘솔 → **보안 그룹(Security Groups)** → **보안 그룹 생성**

아래 정보를 입력한다.

| Security Group Name | VPC Name | Rule | Port | Protocol | Source |
| --- | --- | --- | --- | --- | --- |
| 이니셜-sg-alb | 이니셜-vpc-ap-01 | Inbound | 80 | HTTP | 0.0.0.0/0 |
|  |  | Inbound | 443 | HTTPS | 0.0.0.0/0 |

설정 후 **보안 그룹 생성(Create Security Group)** 클릭

---

# 2. Load Balancer Target Group 생성

Load Balancer는 직접 EC2로 트래픽을 보내지 않고 **Target Group**을 통해 전달한다.

EC2 콘솔 → **Target Groups** → **Create Target Group**

다음 정보를 입력한다.

### 기본 설정

대상 유형

```
Instance
```

대상 그룹 이름

```
이니셜-tg-web
```

프로토콜

```
HTTP
```

포트

```
80
```

VPC

```
이니셜-vpc-ap-01
```

설정 후 **Next** 클릭

---

## 2.1 Target 등록

Target Group에 EC2 인스턴스를 등록한다.

등록 대상

```
이니셜-ec2-web
```

포트

```
80
```

설정 후

```
아래에 보류 중인 것으로 포함
```

버튼 클릭

그 다음

```
Create Target Group
```

버튼 클릭

---

# 3. Load Balancer 생성

EC2 콘솔 → **Load Balancers** → **Create Load Balancer**

다음 중 선택

```
Application Load Balancer
```

---

## 3.1 기본 설정

Load Balancer 이름

```
이니셜-alb-web
```

Scheme

```
Internet-facing
```

IP address type

```
IPv4
```

VPC

```
이니셜-vpc-ap-01
```

---

## 3.2 가용 영역 설정

두 개 이상의 AZ를 선택해야 고가용성이 확보된다.

AZ 설정

```
ap-northeast-2a → 이니셜-sub-pub-01
ap-northeast-2c → 이니셜-sub-pub-02
```

---

## 3.3 Security Group 설정

다음 보안 그룹 선택

```
이니셜-sg-alb
```

---

## 3.4 Listener 설정

리스너 설정

Protocol

```
HTTP
```

Port

```
80
```

Default action

```
이니셜-tg-web
```

설정 완료 후

```
Create Load Balancer
```

클릭

---

# 4. Load Balancer DNS 확인

Load Balancer 생성이 완료되면 DNS 주소가 자동으로 생성된다.

EC2 콘솔 → **Load Balancers**

다음 Load Balancer 선택

```
이니셜-alb-web
```

다음 항목 확인

```
DNS name
```

예시

```
이니셜-alb-web-123456.ap-northeast-2.elb.amazonaws.com
```

---

# 5. 웹 서비스 접속 테스트

브라우저에서 다음 주소 입력

```
http://ALB-DNS주소
```

예시

```
http://이니셜-alb-web-123456.ap-northeast-2.elb.amazonaws.com
```

정상적으로 설정되었다면 EC2 웹 서버 페이지가 출력된다.

---

# 동작 원리 정리

사용자가 웹 브라우저로 요청을 보내면 다음 순서로 동작한다.

```
Client
   │
   │ HTTP Request
   ▼
Application Load Balancer
   │
   │ Target Group
   ▼
EC2 Web Server
```

Load Balancer는 여러 서버로 트래픽을 분산하여 다음과 같은 장점을 제공한다.

* 서버 부하 분산

* 고가용성

* 확장성 확보

* 장애 서버 자동 제외

---

# 실습 검증

다음 항목을 확인한다.

1️⃣ Load Balancer 상태

```
Active
```

2️⃣ Target Group 상태

```
Healthy
```

3️⃣ 웹 접속 정상 여부

```
ALB DNS 접속 시 웹 페이지 출력
```

---

# 정리

이번 실습에서 수행한 작업

1. Security Group 생성

2. Target Group 생성

3. EC2 인스턴스 등록

4. Application Load Balancer 생성

5. DNS 주소를 이용한 웹 서비스 접속 확인

Application Load Balancer는 AWS에서 가장 많이 사용하는 L7 Load Balancer이며 다음과 같은 기능을 제공한다.

* HTTP/HTTPS 트래픽 처리

* Path 기반 라우팅

* Host 기반 라우팅

* Auto Scaling 연동

---