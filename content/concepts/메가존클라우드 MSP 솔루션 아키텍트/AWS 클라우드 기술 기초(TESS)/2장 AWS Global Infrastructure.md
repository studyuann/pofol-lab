---
title: "2장 AWS Global Infrastructure"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 클라우드 기술 기초(TESS)"]
is_public: true
draft: false
---

# 2장 AWS Global Infrastructure

## 2.1 AWS Global Infrastructure 개요

AWS는 전 세계 여러 지역에 데이터센터를 운영하고 있음.

하지만 AWS는 단순히 **하나의 데이터센터**로 서비스를 제공하지 않음.

대신 다음과 같은 **계층 구조**로 구성되어 있음.

```
Global Infrastructure
   │
Region
   │
Availability Zone
   │
Data Center
```

즉 AWS 인프라는 다음과 같이 구성된다.

```
World
 └ Region
     └ Availability Zone
         └ Data Center
```

이 구조는 **확장성(Scalability)** 과 **고가용성(High Availability)** 을 제공하기 위해 설계됨.

[![](2%EC%9E%A5%20AWS%20Global%20Infrastructure/image.png)](2%EC%9E%A5%20AWS%20Global%20Infrastructure/image.png)

---

# 2.2 Region

Region은 **AWS 서비스가 제공되는 지리적 위치**이다.

예를 들어 AWS는 다음과 같은 Region을 운영한다.

```
ap-northeast-2   (Seoul)
ap-northeast-1   (Tokyo)
us-east-1        (Virginia)
eu-central-1     (Frankfurt)
ap-southeast-1   (Singapore)
```

각 Region은 **완전히 독립된 클라우드 환경**이다.

즉 다음 특징을 가진다.

```
각 Region은 물리적으로 분리됨
Region 간 장애 전파 없음
Region 간 네트워크 연결 필요
```

예를 들어 서울 Region에서 장애가 발생하더라도

```
Tokyo Region
Virginia Region
```

에는 영향을 주지 않음.

이러한 구조를 통해 AWS는 **서비스 안정성을 높인다**.

---

# 2.3 Region 선택 기준

AWS 아키텍처를 설계할 때 **Region 선택은 매우 중요한 요소**이다.

대표적인 선택 기준은 다음과 같다.

---

## 1. Latency

사용자와 가까운 Region을 선택하면 **네트워크 지연시간이 감소한다**.

예

```
User : Korea
Region : Seoul
```

반대로 한국 사용자가 미국 Region을 사용하면

```
Korea → USA network
```

로 인해 응답 시간이 증가한다.

---

## 2. Compliance

일부 데이터는 특정 국가에 저장해야 한다.

예

```
Financial data
Medical data
Personal data
```

이러한 데이터는 **법적 규제**가 존재할 수 있다.

따라서 기업은 **데이터 저장 위치를 고려하여 Region을 선택해야 한다**.

---

## 3. Service Availability

AWS 서비스는 Region마다 제공 여부가 다를 수 있다.

예

```
AI services
Machine learning services
Data analytics services
```

따라서 필요한 서비스가 해당 Region에서 제공되는지 확인해야 한다.

---

# 2.4 Availability Zone (AZ)

Availability Zone은 **독립적인 데이터센터 그룹**이다.

하나의 Region에는 여러 AZ가 존재한다.

예

```
ap-northeast-2a
ap-northeast-2b
ap-northeast-2c
ap-northeast-2d
```

각 AZ는 다음 특징을 가진다.

```
Independent power
Independent networking
Physical separation
```

즉 **하나의 AZ에서 장애가 발생하더라도 다른 AZ에는 영향을 주지 않도록 설계됨**.

---

# 2.5 Region 내부 구조

AWS Region 내부 구조는 다음과 같다.

```
Region
 ├ AZ-A
 │   ├ Data Center
 │   └ Data Center
 │
 ├ AZ-B
 │   ├ Data Center
 │   └ Data Center
 │
 └ AZ-C
     ├ Data Center
     └ Data Center
```

중요한 특징

```
AZ 내부에는 여러 데이터센터 존재
AZ 간 고속 네트워크 연결
```

즉 AZ는 단일 데이터센터가 아니라 **데이터센터 집합**이다.

---

# 2.6 Multi-AZ Architecture

AWS 아키텍처 설계에서 매우 중요한 개념이 **Multi-AZ**이다.

Multi-AZ는 **서비스를 여러 AZ에 분산 배치하는 구조**이다.

예

```
                Load Balancer
                     │
           ┌─────────┴─────────┐
           │                   │
         AZ-A                AZ-B
           │                   │
          EC2                 EC2
           │                   │
           └─────────┬─────────┘
                     │
                    RDS
```

이 구조의 장점

```
AZ 장애 발생
→ 다른 AZ에서 서비스 유지
```

즉 **서비스 가용성이 크게 향상된다**.

---

# 2.7 Edge Location

Edge Location은 **콘텐츠 전송을 위한 AWS 네트워크 거점**이다.

Edge Location을 사용하는 대표 서비스

```
Amazon CloudFront
Amazon Route53
AWS Global Accelerator
```

Edge Location의 역할

```
Content caching
DNS response
Network acceleration
```

구조

```
User
 │
Edge Location
 │
AWS Region
```

사용자는 **가장 가까운 Edge Location으로 연결된다**.

이 구조는 **콘텐츠 전달 속도를 향상시킨다**.

---

# 2.8 Multi-Region Architecture

Multi-Region은 **여러 Region에 서비스를 배포하는 구조**이다.

예

```
User
 │
Route53
 │
 ├ Seoul Region
 │   └ Application
 │
 └ Tokyo Region
     └ Application
```

이 구조는 다음 목적을 가진다.

```
Disaster recovery
Global service
Latency optimization
```

예

```
Seoul Region 장애
→ Tokyo Region 서비스 유지
```

---

# 요약

AWS 글로벌 인프라는 다음 구조로 이루어져 있다.

```
Global Infrastructure
   │
Region
   │
Availability Zone
   │
Data Center
```

핵심 개념

```
Region = Geographic location
AZ = Isolated data center group
```

AWS 아키텍처 설계에서 중요한 개념

```
Multi AZ
Multi Region
High Availability
Fault Isolation
```

---