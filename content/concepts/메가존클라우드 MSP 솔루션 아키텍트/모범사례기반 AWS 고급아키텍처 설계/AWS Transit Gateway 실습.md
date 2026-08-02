---
title: "AWS Transit Gateway 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "모범사례기반 AWS 고급아키텍처 설계"]
is_public: true
draft: false
---

# AWS Transit Gateway 실습

# 1. 실습 목표

이번 실습에서는 여러 개의 VPC를 하나의 허브 네트워크에 연결하는 **Transit Gateway**를 구성한다.

실습을 통해 다음 내용을 이해한다.

* Transit Gateway 개념

* Hub & Spoke 네트워크 구조

* VPC Peering의 Full Mesh 문제

* Transit Gateway Route Table 동작

* 여러 VPC 간 Private 통신

---

# 2. Transit Gateway 개념

Transit Gateway는 **여러 VPC와 온프레미스 네트워크를 중앙 허브로 연결하는 라우팅 서비스**다.

즉 AWS 네트워크의 **Core Router 역할**을 한다.

특징

* 중앙 라우터 역할

* 수백 개 VPC 연결 가능

* VPN 연결 가능

* Direct Connect 연결 가능

* 라우팅 중앙 관리

---

# 3. Peering 문제 (Full Mesh 문제)

VPC Peering은 VPC 수가 증가하면 연결이 복잡해진다.

예

VPC 3개

```
VPC-A ↔ VPC-B
VPC-B ↔ VPC-C
VPC-A ↔ VPC-C
```

총 연결 수

```
3개
```

VPC 10개

```
45개 Peering
```

즉

```
N(N-1)/2
```

관리 어려움 발생.

---

# 4. Transit Gateway 해결 방식

Transit Gateway는 중앙 허브 구조다.

```
             Transit Gateway
                    │
     ┌──────────────┼──────────────┐
     │              │              │
   VPC-A          VPC-B          VPC-C
```

장점

* 연결 단순

* 라우팅 중앙관리

* 확장성 좋음

---

# 5. 실습 아키텍처

이번 실습에서는 **3개의 VPC를 Transit Gateway에 연결한다.**

```
                  Transit Gateway
                        │
        ┌───────────────┼───────────────┐
        │               │               │
      VPC-A           VPC-B           VPC-C
   10.10.0.0/16    10.20.0.0/16     10.30.0.0/16

      EC2-A          EC2-B           EC2-C
```

실습 목표

```
EC2-A → EC2-B ping
EC2-A → EC2-C ping
```

---

# 6. 실습 순서

```
1 VPC 3개 생성
2 Subnet 생성
3 EC2 생성
4 Transit Gateway 생성
5 VPC Attachment 생성
6 Route Table 설정
7 VPC Route Table 설정
8 Security Group 설정
9 Ping 테스트
```

---

# 7. VPC 생성

## VPC-A

```
Name : 이니셜-vpc-a
CIDR : 10.10.0.0/16
```

---

## VPC-B

```
Name : 이니셜-vpc-b
CIDR : 10.20.0.0/16
```

---

## VPC-C

```
Name : 이니셜-vpc-c
CIDR : 10.30.0.0/16
```

---

# 8. Subnet 생성

각 VPC에 Subnet 생성

### VPC-A

```
Name : 이니셜-subnet-a
CIDR : 10.10.1.0/24
```

---

### VPC-B

```
Name : 이니셜-subnet-b
CIDR : 10.20.1.0/24
```

---

### VPC-C

```
Name : 이니셜-subnet-c
CIDR : 10.30.1.0/24
```

---

# 9. EC2 생성

각 VPC에 EC2 생성

### EC2-A

```
Name : 이니셜-ec2-a
VPC : vpc-a
Subnet : subnet-a
```

---

### EC2-B

```
Name : 이니셜-ec2-b
VPC : vpc-b
Subnet : subnet-b
```

---

### EC2-C

```
Name : 이니셜-ec2-c
VPC : vpc-c
Subnet : subnet-c
```

---

# 10. Security Group 설정

모든 EC2

```
SSH    22      MyIP
ICMP   ALL     10.0.0.0/8
```

---

# 11. Transit Gateway 생성

VPC Console

```
Transit Gateway
Create
```

설정

```
Name : 이니셜-tgw
ASN : 64512
```

ASN

* AWS 내부 BGP 번호

* VPN 연결 시 사용

---

# 12. VPC Attachment 생성

Transit Gateway는 **VPC Attachment**를 통해 연결한다.

---

## VPC-A 연결

```
Transit Gateway Attachment
```

설정

```
Transit Gateway : 이니셜-tgw
VPC : 이니셜-vpc-a
Subnet : subnet-a
```

---

## VPC-B 연결

```
VPC : 이니셜-vpc-b
Subnet : subnet-b
```

---

## VPC-C 연결

```
VPC : 이니셜-vpc-c
Subnet : subnet-c
```

---

# 13. Transit Gateway Route Table

Transit Gateway에는 자체 라우팅 테이블이 존재한다.

추가

```
Destination      Target
10.10.0.0/16     VPC-A
10.20.0.0/16     VPC-B
10.30.0.0/16     VPC-C
```

---

# 14. VPC Route Table 설정

각 VPC Route Table 수정

---

### VPC-A

추가

```
Destination     Target
10.20.0.0/16    Transit Gateway
10.30.0.0/16    Transit Gateway
```

---

### VPC-B

```
Destination     Target
10.10.0.0/16    Transit Gateway
10.30.0.0/16    Transit Gateway
```

---

### VPC-C

```
Destination     Target
10.10.0.0/16    Transit Gateway
10.20.0.0/16    Transit Gateway
```

---

# 15. 네트워크 흐름

EC2-A → EC2-C 통신

```
EC2-A
10.10.1.10
      │
Route Table
10.30.0.0/16 → TGW
      │
Transit Gateway
      │
VPC-C
      │
EC2-C
10.30.1.10
```

---

# 16. Ping 테스트

EC2-A 접속

```
ssh ec2-user@EC2-A
```

---

EC2-B ping

```
ping 10.20.1.10
```

---

EC2-C ping

```
ping 10.30.1.10
```

정상

```
64 bytes from 10.30.1.10
```

---

# 17. Transit Gateway 특징

### Hub Router

Transit Gateway는 AWS 내부 **Core Router 역할** 수행

---

### 확장성

```
5000개 VPC 연결 가능
```

---

### 다양한 연결 지원

지원 연결

```
VPC
VPN
Direct Connect
Peering
```

---

# 18. Peering vs Transit Gateway

| 항목 | VPC Peering | Transit Gateway |
| --- | --- | --- |
| 연결 방식 | VPC 간 직접 연결 | 중앙 라우터 |
| 확장성 | 낮음 | 매우 높음 |
| 라우팅 관리 | 개별 | 중앙 |
| 네트워크 구조 | Mesh | Hub |

---

# 19. 실습 정리

이번 실습에서 수행한 내용

```
VPC 3개 생성
EC2 생성
Transit Gateway 생성
VPC Attachment
Transit Gateway Route Table
VPC Route Table
Ping 테스트
```

---