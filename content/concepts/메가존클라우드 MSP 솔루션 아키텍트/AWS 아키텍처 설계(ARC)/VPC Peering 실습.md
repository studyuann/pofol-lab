---
title: "VPC Peering 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 아키텍처 설계(ARC)"]
is_public: true
draft: false
---

# VPC Peering 실습

## 1. 실습 목표

이번 실습에서는 서로 다른 VPC 간 네트워크를 연결하는 **VPC Peering**을 구성한다.

실습을 통해 다음 내용을 이해하는 것이 목표다.

* VPC Peering 개념 이해

* 서로 다른 VPC 간 Private IP 통신

* Route Table 설정 방식

* Security Group과 Network 통신 흐름

---

## 2. VPC Peering 개념

VPC Peering은 **두 개의 VPC를 직접 연결하는 네트워크 기능**이다.

특징

* AWS 내부 네트워크로 통신

* Internet Gateway 필요 없음

* NAT Gateway 필요 없음

* Private IP로 통신

* Low Latency

즉 다음 구조가 된다.

```
VPC-A 10.10.0.0/16
   │
   │  VPC Peering
   │
VPC-B 10.20.0.0/16
```

두 VPC는 **라우팅을 통해 서로 접근**할 수 있다.

단 반드시 다음 조건이 필요하다.

* CIDR 대역이 겹치면 안 됨

* Route Table 설정 필요

* Security Group 허용 필요

---

# 3. 실습 아키텍처

## 전체 아키텍처

```
                 VPC Peering
        ┌─────────────────────────┐
        │                         │
        │                         │
   VPC-A                       VPC-B
 10.10.0.0/16                10.20.0.0/16

 Public Subnet               Public Subnet
 10.10.1.0/24                10.20.1.0/24

    EC2-A                       EC2-B
```

실습 목표

EC2-A → EC2-B 로 **Private IP ping 통신**

---

# 4. 실습 단계

실습 순서

```
1 VPC 생성
2 Subnet 생성
3 EC2 생성
4 VPC Peering 생성
5 Route Table 수정
6 Security Group 수정
7 Ping 테스트
```

---

# 5. VPC 생성

## VPC-A 생성

VPC Console → Create VPC

설정

```
Name : 이니셜-vpc-a
CIDR : 10.10.0.0/16
```

생성

---

## VPC-B 생성

```
Name : 이니셜-vpc-b
CIDR : 10.20.0.0/16
```

---

# 6. Subnet 생성

## VPC-A Subnet

```
Name : 이니셜-subnet-a
CIDR : 10.10.1.0/24
AZ : ap-northeast-2a
```

---

## VPC-B Subnet

```
Name : 이니셜-subnet-b
CIDR : 10.20.1.0/24
AZ : ap-northeast-2c
```

---

# 7. Internet Gateway 생성

EC2 접속 테스트를 위해 생성한다.

### IGW-A

```
Name : 이니셜-igw-a
Attach : 이니셜-vpc-a
```

### IGW-B

```
Name : 이니셜-igw-b
Attach : 이니셜-vpc-b
```

---

# 8. Route Table 설정

## VPC-A Route Table

```
Destination     Target
0.0.0.0/0       IGW-A
```

---

## VPC-B Route Table

```
Destination     Target
0.0.0.0/0       IGW-B
```

---

# 9. EC2 생성

각 VPC에 EC2를 하나씩 생성한다.

---

## EC2-A

```
Name : 이니셜-ec2-a
VPC : 이니셜-vpc-a
Subnet : 이니셜-subnet-a
AMI : Amazon Linux
Public IP : Enable
```

Security Group

```
Inbound

SSH     22      MyIP
ICMP    ALL     10.20.0.0/16
```

---

## EC2-B

```
Name : 이니셜-ec2-b
VPC : 이니셜-vpc-b
Subnet : 이니셜-subnet-b
Public IP : Enable
```

Security Group

```
Inbound

SSH     22      MyIP
ICMP    ALL     10.10.0.0/16
```

---

# 10. VPC Peering 생성

VPC Console → Peering Connections → Create

설정

```
Name : 이니셜-vpc-peer
Requester VPC : 이니셜-vpc-a
Accepter VPC : 이니셜-vpc-b
```

생성 후

```
Actions → Accept Request
```

상태

```
Active
```

---

# 11. Route Table 수정

VPC Peering은 **라우팅이 반드시 필요**하다.

---

## VPC-A Route Table

추가

```
Destination : 10.20.0.0/16
Target : VPC Peering
```

---

## VPC-B Route Table

추가

```
Destination : 10.10.0.0/16
Target : VPC Peering
```

---

# 12. 통신 테스트

## EC2 접속

```
ssh ec2-user@EC2-A-PublicIP
```

---

## EC2-B Private IP 확인

EC2 Console

예

```
10.20.1.15
```

---

## Ping 테스트

EC2-A에서 실행

```
ping 10.20.1.15
```

정상

```
64 bytes from 10.20.1.15
```

---

# 13. 네트워크 흐름 분석

패킷 흐름

```
EC2-A
 10.10.1.10
      │
      │
Route Table
10.20.0.0/16 → VPC Peering
      │
      │
AWS Backbone Network
      │
      │
EC2-B
10.20.1.15
```

이때 통신 특징

* 인터넷 사용 안함

* NAT Gateway 사용 안함

* Private IP 사용

* AWS 내부망 사용

---

# 14. VPC Peering 제한 사항

중요 특징

### 1. Transitive Routing 불가능

```
VPC-A ↔ VPC-B
VPC-B ↔ VPC-C

A → C 통신 불가능
```

즉

```
A → B → C
```

라우팅 불가능

---

### 2. CIDR 중복 불가능

다음 구성 불가능

```
VPC-A 10.10.0.0/16
VPC-B 10.10.0.0/16
```

---

### 3. Security Group 필요

라우팅만 설정하면 통신되지 않는다.

Security Group 허용 필요

---

# 15. CLI로 확인

Peering 확인

```
aws ec2 describe-vpc-peering-connections
```

---

라우팅 확인

```
aws ec2 describe-route-tables
```

---

# 16. 실습 정리

이번 실습에서 수행한 내용

* VPC 2개 생성

* Subnet 생성

* EC2 생성

* VPC Peering 생성

* Route Table 설정

* Security Group 설정

* Private IP Ping 테스트