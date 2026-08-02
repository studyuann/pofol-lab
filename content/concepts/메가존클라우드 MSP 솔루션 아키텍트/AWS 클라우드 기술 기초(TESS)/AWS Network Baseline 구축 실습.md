---
title: "AWS Network Baseline 구축 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 클라우드 기술 기초(TESS)"]
is_public: true
draft: false
---

# AWS Network Baseline 구축 실습

AWS에서 기본 네트워크 환경을 구축한다.

```
VPC
 → Subnet
 → Routing Table
 → Internet Gateway
 → NAT Gateway
```

이 구조는 AWS에서 가장 기본적인 **3-Tier 아키텍처 네트워크 구조의 기반이 되는 구성**이다.

[![](AWS%20Network%20Baseline%20%EA%B5%AC%EC%B6%95%20%EC%8B%A4%EC%8A%B5/image.png)](AWS%20Network%20Baseline%20%EA%B5%AC%EC%B6%95%20%EC%8B%A4%EC%8A%B5/image.png)

---

# 실습 규칙 (이니셜 Prefix 사용)

이번 실습에서는 **모든 AWS 리소스 이름 앞에 자신의 이름 이니셜 Prefix를 붙여 생성한다.**

이유

* 여러 학생이 동일한 계정을 사용

* 리소스 이름 충돌 방지

* 관리 편의성

---

## 이니셜 생성 규칙

```
이름 : Hong Gi Dong
Prefix : hgd
```

예

| 이름 | Prefix |
| --- | --- |
| Hong Gi Dong | hgd |
| Kim Min Su | kms |
| Lee Ji Eun | lje |

---

## 리소스 네이밍 규칙

```
[이니셜]-[리소스]-[번호]
```

예

```
hgd-vpc-01
hgd-sub-pub-01
hgd-sub-pri-01
hgd-rtb-pub
hgd-igw
hgd-natgw
```

---

# Network Baseline 생성 정보

## 네트워크 자원 명세서

학생 Prefix를 기준으로 리소스를 생성한다.

예 (Prefix = hgd)

| Region | VPC Name | CIDR | Subnet Name | CIDR | Routing Table |
| --- | --- | --- | --- | --- | --- |
| ap-northeast-2 | hgd-vpc-01 | 10.X.0.0/16 | hgd-sub-pub-01 | 10.X.10.0/24 | hgd-rtb-pub |
|  |  |  | hgd-sub-pub-02 | 10.X.20.0/24 | hgd-rtb-pub |
|  |  |  | hgd-sub-pri-01 | 10.X.30.0/24 | hgd-rtb-pri-01 |
|  |  |  | hgd-sub-pri-02 | 10.X.40.0/24 | hgd-rtb-pri-02 |

---

## 라우팅 테이블 명세

| Table Name | Associate Subnet | Destination | Target |
| --- | --- | --- | --- |
| hgd-rtb-pub | hgd-sub-pub-01, hgd-sub-pub-02 | 10.X.0.0/16 | Local |
|  |  | 0.0.0.0/0 | hgd-igw |
| hgd-rtb-pri-01 | hgd-sub-pri-01 | 10.X.0.0/16 | Local |
|  |  | 0.0.0.0/0 | hdg-natgw |
| hgd-rtb-pri-02 | hgd-sub-pri-02 | 10.X.0.0/16 | Local |

---

# VPC 생성

## 1. VPC 콘솔 이동

AWS Console 접속

```
Services
 → VPC
```

---

## 2. VPC 생성

메뉴

```
VPC
 → VPC 생성
```

---

## 3. VPC 생성 정보 입력

| 항목 | 값 |
| --- | --- |
| 생성 리소스 | VPC만 |
| 이름 태그 | hgd-vpc-01 |
| IPv4 CIDR | 10.X.0.0/16 |

설명

VPC는 AWS에서 사용하는 **가상 네트워크**이다.

CIDR

```
10.X.0.0/16
```

은 다음 IP 범위를 의미한다.

```
10.X.0.0 ~ 10.X.255.255
```

총

```
65536개 IP
```

사용 가능.

---

# Subnet 생성

Subnet은 VPC 네트워크를 **작은 네트워크로 분할한 것**이다.

---

## 1. Subnet 메뉴 이동

```
VPC
 → Subnets
```

---

## 2. Subnet 생성

```
Subnet 생성
```

버튼 클릭

---

## 3. Subnet 생성 정보 입력

| Subnet | AZ | CIDR |
| --- | --- | --- |
| hgd-sub-pub-01 | ap-northeast-2a | 10.X.10.0/24 |
| hgd-sub-pub-02 | ap-northeast-2c | 10.X.20.0/24 |
| hgd-sub-pri-01 | ap-northeast-2a | 10.X.30.0/24 |
| hgd-sub-pri-02 | ap-northeast-2c | 10.X.40.0/24 |

설명

```
/24
```

Subnet은

```
256개 IP
```

사용 가능.

---

# Public Subnet 설정

Public Subnet에서 생성되는 EC2 인스턴스는 **자동으로 Public IP를 할당받도록 설정해야 한다.**

설정 경로

```
Subnets
 → hgd-sub-pub-01 선택
 → 작업
 → 서브넷 설정 편집
```

옵션

```
Auto-assign Public IPv4
```

활성화.

동일하게

```
hgd-sub-pub-02
```

에도 적용.

---

# Routing Table 생성

라우팅 테이블은 **패킷이 어디로 이동할지를 결정하는 네트워크 경로 정보**이다.

---

## Routing Table 생성

생성할 테이블

```
hgd-rtb-pub
hgd-rtb-pri-01
hgd-rtb-pri-02
```

---

## Subnet 연결

| Routing Table | Subnet |
| --- | --- |
| hgd-rtb-pub | hgd-sub-pub-01 |
| hgd-rtb-pub | hgd-sub-pub-02 |
| hgd-rtb-pri-01 | hgd-sub-pri-01 |
| hgd-rtb-pri-02 | hgd-sub-pri-02 |

설정 경로

```
Routing Table
 → Subnet associations
 → Edit
```

---

# Internet Gateway 생성

Internet Gateway는 **VPC와 Internet을 연결하는 Gateway**이다.

---

## 생성

메뉴

```
VPC
 → Internet Gateway
 → 생성
```

설정

| 항목 | 값 |
| --- | --- |
| 이름 | hgd-igw |

---

## VPC 연결

```
Actions
 → Attach to VPC
```

선택

```
hgd-vpc-01
```

---

## Public Routing 설정

라우팅 테이블

```
hgd-rtb-pub
```

라우팅 추가

| Destination | Target |
| --- | --- |
| 0.0.0.0/0 | Internet Gateway |

---

# NAT Gateway 생성

NAT Gateway는 **Private Subnet에서 Internet으로 나가는 트래픽을 허용하는 장비**이다.

Private 인스턴스는 Internet에서 직접 접근할 수 없지만

NAT Gateway를 통해 **Outbound 인터넷 연결**이 가능하다.

생성해서 사용 후 삭제함. - 비용 발생

---

## NAT Gateway 생성

메뉴

```
VPC
 → NAT Gateway
 → 생성
```

설정

| 항목 | 값 |
| --- | --- |
| 이름 | hgd-natgw |
| Subnet | hgd-sub-pub-01 |
| Elastic IP | Allocate |

---

## Private Routing 설정

라우팅 테이블

```
hgd-rtb-pri-01
```

라우팅 추가

| Destination | Target |
| --- | --- |
| 0.0.0.0/0 | NAT Gateway |

---

# 실습 결과 네트워크 구조

```
Internet
   │
   │
Internet Gateway
   │
Public Subnet
   │
   │
NAT Gateway
   │
Private Subnet
```

---

# 정리

이를 통해 다음 네트워크 개념을 이해한다.

* Public / Private 네트워크 구조

* Internet Gateway 역할

* NAT Gateway 역할

* Routing Table 동작 방식

---