---
title: "1장 AWS 아키텍처 설계 기본"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 아키텍처 설계(ARC)"]
is_public: true
draft: false
---

# 1장 AWS 아키텍처 설계 기본

## 1.1 AWS 아키텍처 설계 개요

AWS에서 아키텍처를 설계할 때는 단순히 서버를 만드는 것이 아니라 **확장성, 가용성, 보안, 비용**을 고려한 구조를 설계해야 함.

AWS에서는 이러한 설계를 위해 **Well-Architected Framework**라는 설계 기준을 제공함.

AWS 아키텍처 설계의 핵심 특징

* 확장 가능한 구조 (Scalable Architecture)

* 장애에 강한 구조 (Highly Available Architecture)

* 자동화 기반 인프라 (Infrastructure as Code)

* 비용 효율적인 구조 (Cost Optimized Architecture)

온프레미스와 AWS 설계 방식 차이

| 구분 | 온프레미스 | AWS |
| --- | --- | --- |
| 서버 확장 | 장비 구매 필요 | Auto Scaling |
| 가용성 | 장비 이중화 필요 | Multi AZ |
| 네트워크 | 물리 네트워크 | VPC |
| 스토리지 | NAS / SAN | S3 / EBS |

---

# 1.2 AWS Well-Architected Framework

AWS에서 권장하는 아키텍처 설계 기준

총 **6개의 Pillar**로 구성됨.

## 1. Operational Excellence (운영 우수성)

시스템을 효율적으로 운영하고 지속적으로 개선하는 능력.

주요 내용

* Infrastructure as Code

* 자동화

* 운영 모니터링

* 운영 절차 관리

사용 서비스 예

* CloudFormation

* CloudWatch

* Systems Manager

---

## 2. Security (보안)

데이터와 시스템을 보호하는 능력.

주요 내용

* 최소 권한 원칙

* 데이터 암호화

* 네트워크 보안

* 로그 감사

사용 서비스 예

* IAM

* KMS

* WAF

* GuardDuty

---

## 3. Reliability (신뢰성)

시스템이 장애 상황에서도 계속 동작하도록 설계하는 것.

주요 내용

* 장애 자동 복구

* Multi AZ

* 자동 확장

* 백업 및 복구

사용 서비스 예

* Auto Scaling

* Elastic Load Balancer

* Route53

* AWS Backup

---

## 4. Performance Efficiency (성능 효율성)

필요한 성능을 효율적으로 제공하는 능력.

주요 내용

* 적절한 인스턴스 선택

* 캐싱 활용

* CDN 사용

사용 서비스 예

* CloudFront

* ElastiCache

* DynamoDB

---

## 5. Cost Optimization (비용 최적화)

불필요한 비용을 줄이는 설계.

주요 내용

* Auto Scaling

* Spot Instance

* Storage Lifecycle

사용 서비스 예

* Cost Explorer

* Savings Plan

* S3 Lifecycle

---

## 6. Sustainability (지속 가능성)

환경 친화적인 아키텍처 설계.

주요 내용

* 리소스 효율적 사용

* 자동 확장

* 서버리스 활용

---