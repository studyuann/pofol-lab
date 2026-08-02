---
title: "7장 Load Balancing과 확장 구조"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Google 클라우드 핵심 서비스"]
is_public: true
draft: false
---

# 7장. Load Balancing과 확장 구조

## 1. 장 개요

앞 장에서 Compute Engine과 Cloud SQL을 각각 봤다면, 이제는 단일 VM 기반 구조에서 한 단계 올라가 **여러 VM에 트래픽을 분산하고, 장애를 자동으로 우회하고, 수요에 따라 확장하는 구조**를 이해하는 단계다.

AWS를 먼저 학습한 상태라면 보통 다음 감각이 익숙하다.

* ALB/NLB 같은 로드밸런서를 둔다

* Auto Scaling Group으로 인스턴스를 늘리고 줄인다

* Health Check로 비정상 인스턴스를 제외한다

* 웹 계층을 다중 인스턴스로 구성한다

GCP에서도 큰 흐름은 비슷하지만, 특히 주목해야 할 부분이 있다.

* GCP의 Cloud Load Balancing은 **단일 anycast IP**와 **글로벌 프런트엔드** 개념이 강하다.

* 외부 Application Load Balancer는 **프록시 기반 L7 로드밸런서**로 동작한다.

* 백엔드로 Managed Instance Group을 연결하고, Health Check를 통해 정상 인스턴스만 서비스할 수 있다. 백엔드 서비스에서 인스턴스 그룹이나 zonal NEG(Network Endpoint Group)를 사용할 때는 Health Check가 필요하다.

* MIG는 Autoscaling과 Autohealing을 지원한다. Autoscaling은 부하에 따라 VM 수를 자동 조정하고, Autohealing은 애플리케이션 기반 Health Check를 토대로 비정상 인스턴스를 재생성할 수 있다.

---

## 2. 학습 목표

* GCP Load Balancing의 기본 개념을 설명할 수 있음

* 글로벌 프런트엔드와 단일 anycast IP 개념을 설명할 수 있음

* External Application Load Balancer의 역할을 설명할 수 있음

* Health Check의 목적과 동작 방식을 설명할 수 있음

* Managed Instance Group의 역할을 설명할 수 있음

* MIG의 Autoscaling과 Autohealing 개념을 설명할 수 있음

* AWS ALB / Auto Scaling Group과 GCP 구조를 비교할 수 있음

* 확장 가능한 웹 계층 아키텍처를 설명할 수 있음

---

## 3. 핵심 키워드

* Cloud Load Balancing

* External Application Load Balancer

* Anycast IP

* Global Frontend

* Backend Service

* Health Check

* Managed Instance Group

* Instance Template

* Autoscaling

* Autohealing

* Capacity

* HTTP Load Balancer

---

# 4. GCP Load Balancing이란 무엇인가

Cloud Load Balancing은 Google Cloud의 관리형 로드밸런싱 서비스다. Cloud Load Balancing은 단일 anycast IP를 프런트엔드로 사용하고, 사용자·트래픽·백엔드 상태 변화에 즉시 반응하는 관리형 서비스이다.

## 쉽게 이해하면

* AWS의 ELB 계열과 대응되는 서비스

* 백엔드 서버 여러 대에 트래픽을 분산

* 비정상 서버를 자동으로 제외

* 확장 구조와 함께 동작

## 왜 필요한가

단일 VM 한 대만 서비스하면 아래 문제가 생긴다.

* 트래픽 증가 시 처리량 한계

* 서버 장애 시 서비스 중단

* 유지보수 시 무중단 처리 어려움

로드밸런서는 이 문제를 해결하는 출발점이다.

---

# 5. GCP에서 로드밸런싱이 중요한 이유

GCP는 특히 **글로벌 네트워크와 글로벌 프런트엔드** 감각이 강하다. 외부 Application Load Balancer는 글로벌 외부 모드와 리전 외부 모드가 있으며, 글로벌 외부 Application Load Balancer는 Google Front Ends(GFEs) 상의 관리형 서비스로 구현된다. GFEs는 Google의 글로벌 네트워크와 제어 평면 위에서 동작한다.

* 단일 anycast IP

* 글로벌 프런트엔드

* 다중 리전 백엔드 확장 가능성

* 자동 멀티리전 페일오버

Cloud Load Balancing은 단일 anycast IP를 사용하며, 여러 리전 백엔드에 대한 크로스리전 로드밸런싱과 자동 멀티리전 페일오버를 지원한다.

---

# 6. External Application Load Balancer

외부 Application Load Balancer는 HTTP/HTTPS 트래픽을 처리하는 **프록시 기반 Layer 7 로드밸런서**다. 단일 외부 IP 주소 뒤에서 서비스를 실행하고 확장할 수 있게 해준다.

## 6.1 특징

* HTTP/HTTPS 처리

* 단일 외부 IP 제공

* 백엔드 서비스로 트래픽 전달

* 다양한 백엔드 유형 지원

* 고급 트래픽 제어 기능 지원 가능

---

# 7. GCP 로드밸런서 구성 요소

웹 계층 기준으로 보면 보통 아래 순서로 이해하면 된다.

1. Frontend

2. URL Map / Listener 개념

3. Backend Service

4. Health Check

5. Backend Instance Group

* 사용자는 외부 IP로 접속

* 로드밸런서가 요청을 받음

* 백엔드 서비스가 트래픽을 어떤 서버 그룹으로 보낼지 결정

* Health Check가 정상 서버만 대상으로 유지

* MIG가 실제 VM 집합을 제공

백엔드 서비스는 인스턴스 그룹을 백엔드로 사용할 수 있고, 이 경우 Health Check가 필요하다.

---

# 8. Health Check

Health Check는 백엔드 인스턴스가 정상인지 판단하는 메커니즘이다.

백엔드 서비스가 인스턴스 그룹 또는 zonal NEG를 사용하는 경우 Health Check를 연결해야 한다.

## 왜 필요한가

로드밸런서는 단순히 서버가 살아 있는지만 보는 것이 아니라,

**서비스 가능한 상태인지**를 알아야 한다.

예를 들어

* VM은 살아 있음

* 하지만 nginx는 죽어 있음

이 경우 Health Check가 없으면 사용자는 계속 장애 서버로 트래픽을 받을 수 있다.

---

# 9. Managed Instance Group(MIG)

Managed Instance Group은 동일한 템플릿으로 관리되는 VM 인스턴스 집합이다.

## 9.1 왜 필요한가

VM 여러 대를 손으로 각각 만들고 관리하면 일관성이 깨지고 운영이 어려워진다.

MIG를 사용하면 같은 템플릿으로 복수 인스턴스를 자동 관리할 수 있다.

## 9.2 핵심 구성

* Instance Template

* 대상 인스턴스 수

* Autoscaling 정책

* Autohealing 정책

* 배포 위치(단일 존 또는 다중 존)

## AWS 비교

* AWS Auto Scaling Group과 가장 유사한 개념으로 이해하면 된다.

---

# 10. Instance Template

MIG는 인스턴스를 직접 하나씩 정의하지 않고, **Instance Template** 을 기반으로 만든다.

템플릿에는 VM의 표준 사양이 들어간다.

예시

* 머신 타입

* OS 이미지

* 부팅 디스크

* 네트워크

* 태그

* Service Account

* Startup Script

---

# 11. Autoscaling

MIG는 Autoscaling을 지원하며, 부하 증가나 감소에 따라 VM 수를 자동 조정할 수 있다.

## 11.1 어떤 기준으로 확장하는가

대표 예시

* CPU 사용률

* 로드밸런서 기반 용량

* 스케줄 기반

* 커스텀 모니터링 지표

## 11.2 왜 중요한가

* 피크 시간에는 인스턴스를 늘림

* 한가할 때는 인스턴스를 줄임

* 성능과 비용 사이 균형을 맞춤

## AWS 비교

* AWS Auto Scaling Group의 정책 기반 확장과 같은 감각으로 이해하면 된다.

---

# 12. Autohealing

Autohealing은 비정상 인스턴스를 자동으로 교체하거나 복구하는 기능이다.

MIG에 Health Check 기반 Autohealing 정책을 연결할 수 있다.

## 왜 필요한가

단순히 트래픽을 우회하는 것만으로는 충분하지 않다.

문제가 있는 인스턴스를 계속 남겨두면 전체 풀의 건강성이 나빠진다.

Autohealing은 아래 흐름으로 이해하면 된다.

* Health Check 실패

* 인스턴스가 비정상으로 판단됨

* MIG가 해당 인스턴스를 재생성하거나 교체

로드밸런서의 Health Check와 MIG의 Autohealing Health Check는 목적이 비슷해 보여도 운영 관점이 다르다.

* 로드밸런서 Health Check: 트래픽을 어디로 보낼지 판단

* Autohealing Health Check: 어떤 인스턴스를 복구/재생성할지 판단

---

# 13. 확장 가능한 웹 계층 구조

* External Application Load Balancer

* Backend Service

* Health Check

* Managed Instance Group

* 여러 VM 인스턴스

* 필요 시 Cloud SQL 연결

## 구조 흐름

1. 사용자는 단일 외부 IP로 접속

2. 로드밸런서가 요청을 받음

3. Health Check 결과를 참고해 정상 백엔드로 전달

4. MIG가 백엔드 VM을 관리

5. Autoscaling으로 트래픽 증가 대응

6. Autohealing으로 비정상 VM 자동 복구

이 구조는 소규모 단일 VM 실습에서 운영형 웹 계층 구조로 넘어가는 가장 기본적인 패턴이다.

---

# 14. AWS와의 비교

## AWS 쪽 감각

* ALB

* Target Group

* Health Check

* Auto Scaling Group

* Launch Template

## GCP 쪽 감각

* External Application Load Balancer

* Backend Service

* Health Check

* Managed Instance Group

* Instance Template

**AWS는 ALB + Target Group + ASG 조합으로 익히는 경우가 많고, GCP는 Load Balancer + Backend Service + MIG 조합으로 익히는 흐름이 강함**

---

# 15. 장 요약

* Cloud Load Balancing은 관리형 로드밸런싱 서비스이며, 단일 anycast IP와 글로벌 프런트엔드 개념이 중요하다.

* External Application Load Balancer는 HTTP/HTTPS용 프록시 기반 L7 로드밸런서다.

* 인스턴스 그룹을 백엔드로 쓰는 경우 Health Check가 필요하다.

* Managed Instance Group은 동일 템플릿 기반 VM 집합을 관리하며 Autoscaling을 지원한다.

* MIG는 Health Check 기반 Autohealing도 구성할 수 있다.

* 이 구조를 통해 단일 VM 기반 서비스에서 확장 가능한 웹 계층 구조로 발전할 수 있다.