---
title: "5장 GKE 서비스 노출과 Gateway API"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Google 쿠버네티스 아키텍처 설계 및 구축"]
is_public: true
draft: false
---

# 5장. GKE 서비스 노출과 Gateway API

## 장 개요

## 학습 목표

이 장을 마치면 다음이 가능해야 한다.

* GKE에서 Service 노출 방식의 큰 그림을 설명할 수 있음

* Ingress와 Gateway API의 차이를 설명할 수 있음

* Gateway, HTTPRoute 같은 핵심 리소스의 역할을 설명할 수 있음

* GKE Gateway API가 Google Cloud Load Balancer와 어떻게 연결되는지 설명할 수 있음

* 운영 관점에서 왜 Gateway API가 더 나은 모델이 될 수 있는지 설명할 수 있음

* 샘플 애플리케이션을 외부에 노출하는 기본 흐름을 따라갈 수 있음

---

## 핵심 키워드

* Service

* LoadBalancer Service

* Ingress

* Gateway API

* Gateway

* GatewayClass

* HTTPRoute

* Listener

* ParentRef

* Traffic Policy

* Application Load Balancer

---

# 1. 왜 이 장이 중요한가

Kubernetes 일반적인 애플리케이션 노출 흐름

* ClusterIP

* NodePort

* LoadBalancer

* Ingress

하지만 GKE를 운영 플랫폼 관점에서 보면, 단순히 “외부 IP를 붙인다”가 아니라 **어떤 방식으로 외부 진입 구조를 운영할 것인가**가 더 중요하다.

예를 들어 이런 질문이 생긴다.

* 하나의 진입점에서 여러 서비스로 경로 기반 분기할 수 있는가

* TLS 정책은 누가 관리하는가

* 네트워크팀과 앱팀의 역할을 분리할 수 있는가

* 트래픽 정책을 더 구조적으로 분리할 수 있는가

* 멀티클러스터, 운영 표준화와도 연결할 수 있는가

Gateway API는 이런 문제를 더 잘 풀기 위한 모델이다.

**Ingress는 “애플리케이션을 외부에 노출하는 도구”로 이해하기 쉬웠다면, Gateway API는 “트래픽 진입 구조를 운영형으로 설계하는 모델”로 이해하는 편이 좋다.**

---

# 2. Kubernetes Service 노출 방식

## 2.1 ClusterIP

* 클러스터 내부 전용

* 외부 직접 접근 불가

* 서비스 간 내부 통신용

## 2.2 NodePort

* 각 노드의 특정 포트를 열어 외부 접근 가능

* 운영형 구조로는 다소 거칠고 직접적

* 테스트용으로는 이해가 쉬움

## 2.3 LoadBalancer Service

* 클라우드 로드밸런서를 붙이는 방식

* 단일 서비스 노출에는 직관적

* 하지만 복잡한 라우팅, 역할 분리, 고급 정책은 한계가 있음

---

# 3. Ingress는 무엇을 해결했는가

Ingress는 여러 서비스 앞에 하나의 HTTP(S) 진입점을 두고, 호스트/경로 기반 라우팅을 구성하는 방식으로 많이 사용됐다. Kubernetes Ingress는 표준화된 HTTP 진입 리소스지만, 구현 세부는 컨트롤러마다 다를 수 있다.

## Ingress가 해결한 것

* 여러 서비스를 하나의 진입점 뒤로 숨김

* 경로 기반 라우팅 가능

* TLS 설정 가능

* 애플리케이션 외부 노출 구조를 단순화

## 한계

* 역할 분리가 충분히 명확하지 않음

* 고급 정책 확장에 제약

* 구현이 컨트롤러별로 달라질 수 있음

* 네트워크팀/플랫폼팀/앱팀의 책임을 분리해 표현하기 어려움

---

# 4. Gateway API란 무엇인가

Gateway API는 Kubernetes에서 서비스 노출과 트래픽 진입을 더 구조적으로 다루기 위한 API 세트다.

## 쉽게 이해하면

* Ingress보다 더 구조적이고 역할 분리가 가능한 API

* 진입점(Gateway)과 라우팅(HTTPRoute 등)을 분리

* 운영팀과 애플리케이션팀이 각자 다룰 리소스를 나누기 쉬움

* GKE에서는 Google Cloud Load Balancer와 자연스럽게 연결됨

---

# 6. Gateway API의 핵심 리소스

* GatewayClass

* Gateway

* Listener

* HTTPRoute

## 6.1 GatewayClass

GatewayClass는

**어떤 종류의 Gateway를 어떤 구현체가 처리할 것인가**를 정의하는 클래스 개념이다.

### 쉽게 이해하면

* StorageClass, IngressClass 같은 감각

* “이 Gateway는 누가 구현하나”를 지정

### GKE에서 의미

* GKE Gateway controller가 이해하는 클래스 사용

* 외부 / 내부 Application Load Balancer 종류와 연결되는 출발점

---

## 6.2 Gateway

Gateway는 **실제 트래픽 진입점**을 표현한다.

### 역할

* 어떤 포트로 받을지

* 어떤 프로토콜을 받을지

* 어떤 리스너를 가질지

* 어떤 Route가 붙을 수 있는지

### 쉽게 이해하면

* Ingress보다 더 명시적인 “진입 장치”라고 보면 됨

---

## 6.3 Listener

Listener는 Gateway가 어떤 방식으로 요청을 받을지를 정의한다.

예시

* HTTP 80

* HTTPS 443

* 특정 hostname

* 특정 protocol

### 의미

* 외부에서 들어오는 요청을 어떤 포트/프로토콜/호스트 기준으로 받을지 정함

---

## 6.4 HTTPRoute

HTTPRoute는

**들어온 HTTP 요청을 어떤 서비스로 어떻게 보낼지** 정의한다.

### 역할

* 경로 기반 라우팅

* 호스트 기반 라우팅

* 백엔드 서비스 연결

* 일부 정책 적용

### 쉽게 이해하면

* Ingress에서 하던 URL routing rules를 더 구조적으로 분리한 느낌

---

# 7. Ingress와 Gateway API 비교

## Ingress의 감각

* 한 리소스 안에 진입과 라우팅이 같이 들어가는 느낌

* 단순하고 익숙함

* 앱 중심 관점에서 보기 쉬움

## Gateway API의 감각

* 진입점(Gateway)과 라우팅(HTTPRoute)이 분리됨

* 역할 기반 분리가 쉬움

* 정책과 운영 모델이 더 명확함

* 플랫폼팀/네트워크팀/앱팀 협업에 유리함

**Ingress가 “서비스를 노출하는 단순한 입구”에 가깝다면, Gateway API는 “운영 가능한 트래픽 진입 구조”에 가깝다.**

---

# 8. 역할 분리 관점에서의 장점

Gateway API의 큰 장점 중 하나가 역할 분리다.

## 예시 구조

### 플랫폼팀 / 네트워크팀

* GatewayClass 정의

* Gateway 생성

* 외부 진입 정책 관리

* TLS와 공통 정책 관리

### 애플리케이션팀

* HTTPRoute 작성

* 어떤 경로를 어떤 서비스에 연결할지 정의

* 앱 단위 라우팅 룰 제출

## 왜 중요한가

운영 환경에서는 모든 팀이 하나의 Ingress 리소스를 같이 만지면 충돌이 나기 쉽다.

Gateway API는 이런 문제를 더 잘 분리해준다.

---

# 9. GKE에서의 Gateway API 동작

GKE에서는 Gateway API 리소스를 적용하면, GKE Gateway controller가 이를 읽고 적절한 Google Cloud Load Balancer를 생성/갱신한다.

* Kubernetes 리소스를 작성함

* GKE가 이를 보고 Google Cloud 로드밸런서를 조정함

* 사용자는 YAML만 보고 있어도, 실제로는 클라우드 네트워크 리소스가 뒤에서 움직임

**Gateway API는 쿠버네티스 객체이지만, GKE에서는 클라우드 로드밸런서까지 제어하는 인터페이스다.**

---

# 10. 장 요약

* Gateway API는 Kubernetes에서 서비스 노출과 트래픽 진입을 더 구조적으로 다루기 위한 API다.

* GKE에서는 Gateway API가 Google Cloud Application Load Balancer와 연결된다.

* Ingress보다 역할 분리, 확장성, 표현력이 더 좋다.

* Gateway는 외부 진입점이고, HTTPRoute는 요청을 서비스로 연결하는 규칙이다.

* Service는 여전히 백엔드 연결의 핵심 요소다.

* GKE 운영 관점에서는 Gateway API를 “쿠버네티스 YAML”이 아니라 “로드밸런서 운영 인터페이스”로 이해하는 것이 중요하다.

### 핵심 결론

**GKE에서 Gateway API는 단순한 Ingress 대체재가 아니라, 운영 가능한 트래픽 진입 구조를 설계하는 핵심 도구다.**