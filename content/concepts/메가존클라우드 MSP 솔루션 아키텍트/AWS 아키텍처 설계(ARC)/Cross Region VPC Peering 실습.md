---
title: "Cross Region VPC Peering 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 아키텍처 설계(ARC)"]
is_public: true
draft: false
---

# Cross Region VPC Peering 실습

# 1. 실습 목표

이번 실습에서는 **서로 다른 AWS Region의 VPC를 연결하는 Cross Region VPC Peering**을 구성한다.

이 실습을 통해 다음 내용을 이해한다.

* Cross Region VPC Peering 개념

* Region 간 AWS Backbone Network 통신

* Route Table 설정 방식

* Private IP 기반 Region 간 통신

---

# 2. Cross Region VPC Peering 개념

VPC Peering은 기본적으로 **같은 Region 뿐 아니라 다른 Region 간에도 연결 가능**하다.

이를 **Cross Region VPC Peering**이라고 한다.

특징

* AWS Global Backbone 사용

* Public Internet 사용하지 않음

* Private IP 통신 가능

* Latency 낮음

* Encryption 적용됨 (AWS 내부)

구조

```
ap-northeast-2 (Seoul)

VPC-A
10.10.0.0/16
      │
      │  VPC Peering
      │
VPC-B
10.20.0.0/16

us-east-1 (N. Virginia)
```

---

# 3. 실습 아키텍처

```
Region 1 : ap-northeast-2 (Seoul)

 VPC-A
 10.10.0.0/16

 Subnet
 10.10.1.0/24

 EC2-A


                Cross Region
                VPC Peering


Region 2 : us-east-1 (N. Virginia)

 VPC-B
 10.20.0.0/16

 Subnet
 10.20.1.0/24

 EC2-B
```

실습 목표

```
EC2-A → EC2-B Private IP Ping
```

---

# 4. 실습 순서

```
1 VPC 생성
2 Subnet 생성
3 EC2 생성
4 Cross Region Peering 생성
5 Peering Accept
6 Route Table 설정
7 Security Group 설정
8 Ping 테스트
```

---

# 5. Region 1 VPC 생성 (Seoul)

Region 변경

```
ap-northeast-2
```

VPC 생성

```
Name : 이니셜-vpc-seoul
CIDR : 10.10.0.0/16
```

---

# 6. Subnet 생성

```
Name : 이니셜-subnet-seoul
CIDR : 10.10.1.0/24
AZ : ap-northeast-2a
```

---

# 7. Internet Gateway 생성

```
Name : 이니셜-igw-seoul
Attach : 이니셜-vpc-seoul
```

Route Table

```
Destination      Target
0.0.0.0/0        IGW
```

---

# 8. EC2 생성 (Seoul)

```
Name : 이니셜-ec2-seoul
AMI : Amazon Linux
VPC : 이니셜-vpc-seoul
Subnet : 이니셜-subnet-seoul
Public IP : Enable
```

Security Group

```
SSH     22        MyIP
ICMP    ALL       10.20.0.0/16
```

---

# 9. Region 변경

AWS Console에서 Region 변경

```
us-east-1 (N. Virginia)
```

---

# 10. VPC 생성 (Virginia)

```
Name : 이니셜-vpc-virginia
CIDR : 10.20.0.0/16
```

---

# 11. Subnet 생성

```
Name : 이니셜-subnet-virginia
CIDR : 10.20.1.0/24
AZ : us-east-1a
```

---

# 12. Internet Gateway 생성

```
Name : 이니셜-igw-virginia
Attach : 이니셜-vpc-virginia
```

Route Table

```
Destination      Target
0.0.0.0/0        IGW
```

---

# 13. EC2 생성 (Virginia)

```
Name : 이니셜-ec2-virginia
AMI : Amazon Linux
VPC : 이니셜-vpc-virginia
Subnet : 이니셜-subnet-virginia
Public IP : Enable
```

Security Group

```
SSH     22        MyIP
ICMP    ALL       10.10.0.0/16
```

---

# 14. Cross Region VPC Peering 생성

Region

```
ap-northeast-2
```

VPC Console

```
Peering Connections
Create Peering
```

설정

```
Name : 이니셜-cross-peering

Requester VPC
이니셜-vpc-seoul

Accepter VPC
Another Region

Region
us-east-1

VPC
이니셜-vpc-virginia
```

Create

---

# 15. Peering Accept

Region 변경

```
us-east-1
```

VPC → Peering Connections

```
Actions
Accept Request
```

상태

```
Active
```

---

# 16. Route Table 설정

## Seoul Route Table

추가

```
Destination : 10.20.0.0/16
Target : VPC Peering
```

---

## Virginia Route Table

추가

```
Destination : 10.10.0.0/16
Target : VPC Peering
```

---

# 17. 통신 테스트

EC2-Seoul 접속

```
ssh ec2-user@EC2-Seoul-PublicIP
```

---

Virginia Private IP 확인

예

```
10.20.1.10
```

---

Ping 테스트

```
ping 10.20.1.10
```

정상 결과

```
64 bytes from 10.20.1.10
```

---

# 18. 네트워크 흐름

```
EC2-Seoul
10.10.1.10
     │
Route Table
10.20.0.0/16 → Peering
     │
AWS Global Backbone
     │
EC2-Virginia
10.20.1.10
```

특징

* Public Internet 사용하지 않음

* AWS Backbone Network 사용

* Private IP 통신

---

# 19. 비용 특징

Cross Region Peering은 **데이터 전송 비용 발생**

예

```
Region 간 데이터 전송
약 $0.01 ~ $0.02 / GB
```

같은 Region Peering은 대부분 무료에 가깝다.

---

# 20. Cross Region Peering 제한

### Transitive Routing 불가

```
VPC-A ↔ VPC-B
VPC-B ↔ VPC-C

A → C 통신 불가
```

---

### CIDR 중복 불가

```
10.10.0.0/16
10.10.0.0/16
```

Peering 불가능

---

# 21. CLI 확인

Peering 확인

```
aws ec2 describe-vpc-peering-connections
```

---

Route 확인

```
aws ec2 describe-route-tables
```

---

# 22. 실습 정리

이번 실습에서 수행한 내용

```
Seoul VPC 생성
Virginia VPC 생성
EC2 생성
Cross Region VPC Peering 생성
Route Table 설정
Security Group 설정
Private IP Ping 테스트
```

---

## 강의에서 추가로 설명하면 좋은 내용

Peering 다음에는 보통 이걸 같이 설명한다.

### VPC 연결 방식 비교

```
VPC Peering
Transit Gateway
PrivateLink
VPN
```

간단한 구조

```
Small Architecture → Peering
Large Multi VPC → Transit Gateway
Service Access → PrivateLink
On-prem → VPN
```