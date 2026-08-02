---
title: "3장 GKE 클러스터 생성 시 필수 설계 요소"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Google 쿠버네티스 아키텍처 설계 및 구축"]
is_public: true
draft: false
---

# 3장. GKE 클러스터 생성 시 필수 설계 요소

## 1. 장 개요

GKE 클러스터를 생성할 때 반드시 고려해야 하는 핵심 설계 요소들이 있다.

* 리전형으로 만들 것인가, 존형으로 만들 것인가

* 어떤 VPC와 서브넷을 사용할 것인가

* Pod IP와 Service IP는 어떻게 할당할 것인가

* 노드풀은 몇 개로 나눌 것인가

* Private Cluster가 필요한가

* kubectl 접근은 어떻게 할 것인가

* 릴리스 채널은 무엇을 쓸 것인가

GKE 클러스터 생성 시 네트워크 접근성, 업그레이드 방식, 버전 관리, 노드풀, VPC-native 네트워킹 등을 주요 선택지이다. 또 VPC-native 클러스터는 GKE의 권장 네트워크 모델이며, Pod IP가 VPC 내에서 직접 라우팅 가능해 네트워크 설계를 단순화한다.

---

## 2. 학습 목표

* GKE 클러스터 생성 시 반드시 결정해야 하는 핵심 항목을 설명할 수 있음

* 존형 클러스터와 리전형 클러스터의 차이를 설명할 수 있음

* VPC-native 클러스터의 의미를 설명할 수 있음

* Pod CIDR / Service CIDR 개념을 설명할 수 있음

* 노드풀 설계가 왜 중요한지 설명할 수 있음

* kubectl 접근과 인증 흐름을 설명할 수 있음

* 샘플 클러스터 생성 절차를 따라갈 수 있음

---

## 3. 핵심 키워드

* Zonal Cluster

* Regional Cluster

* Node Pool

* VPC-native Cluster

* Alias IP

* Pod CIDR

* Service CIDR

* Secondary Range

* Private Cluster

* Release Channel

* kubeconfig

* kubectl credentials

---

# 4. 클러스터 생성 전 가장 먼저 결정할 것

GKE 클러스터 생성 전에는 아래 4가지를 먼저 정리해야 한다.

## 4.1 운영 모드

* Standard

* Autopilot

## 4.2 배치 범위

* 존형(Zonal)

* 리전형(Regional)

## 4.3 네트워크 구조

* 어느 VPC를 사용할 것인가

* 어느 서브넷을 사용할 것인가

* Pod IP / Service IP를 어떻게 할당할 것인가

## 4.4 노드 운영 방식

* 노드풀을 어떻게 나눌 것인가

* 하나의 공용 노드풀로 갈 것인가

* 역할별로 분리할 것인가

---

# 5. 존형 클러스터와 리전형 클러스터

클러스터 배치 방식은 매우 중요한 첫 번째 설계 요소다.

## 5.1 존형 클러스터

존형 클러스터는 특정 **하나의 Zone** 을 중심으로 제어 평면과 노드가 배치되는 형태로 이해하면 된다.

### 특징

* 구조가 단순함

* 테스트 및 학습용으로 적합함

* 비용과 구성이 단순한 편임

* 단일 존 장애 도메인 영향을 더 직접적으로 받음

## 5.2 리전형 클러스터

리전형 클러스터는 **여러 Zone에 걸쳐 더 높은 가용성**을 제공하는 구조다.

### 특징

* 가용성이 더 높음

* 운영 환경에 적합함

* 제어 평면과 노드가 다중 존에 분산되는 감각이 강함

* 비용과 구성이 더 복잡할 수 있음

---

# 6. GKE 네트워킹의 기본: VPC-native 클러스터

GKE는 기본적으로 **VPC-native 클러스터**를 권장한다.

## 6.1 왜 중요한가

Kubernetes 네트워크를 단순히 “Pod끼리 통신된다”로 보면 안 된다.

GKE에서는 Pod IP, Node IP, Service IP가 **Google Cloud VPC 구조와 어떻게 연결되는가**를 함께 봐야 한다.

## 6.2 VPC-native의 의미

* Pod IP가 VPC 내부에서 직접 라우팅 가능

* 네트워크 설계가 더 일관적임

* Compute Engine, Cloud SQL 같은 GCP 리소스와 연결성이 좋아짐

* GKE의 권장 네트워크 모델임

---

# 7. Pod CIDR와 Service CIDR

## 7.1 Pod CIDR

Pod들이 사용할 IP 대역이다.

VPC-native 클러스터에서는 보통 서브넷의 **secondary range** 를 Pod IP 용도로 사용한다.

## 7.2 Service CIDR

ClusterIP 같은 Service 리소스가 사용할 IP 대역이다.

이 역시 보통 별도 secondary range로 관리한다.

## 왜 중요한가

클러스터를 많이 만들거나, 클러스터가 커지거나, 멀티클러스터/하이브리드 구조로 가면 IP 대역 충돌이 매우 큰 문제가 된다.

---

# 8. Secondary Range란 무엇인가

GKE VPC-native 클러스터는 보통 서브넷의 secondary range를 사용한다.

## 구조 예시

* Primary subnet range: 노드 IP

* Secondary range 1: Pod IP

* Secondary range 2: Service IP

## 왜 이렇게 나누는가

* 역할별 주소 공간 분리

* 충돌 방지

* 운영 가시성 향상

* 멀티클러스터 및 하이브리드 확장에 유리

---

# 9. 노드풀(Node Pool)

노드풀은 GKE 클러스터 안에서 동일한 구성의 노드 그룹이다.

Standard 모드에서는 노드풀 설계가 매우 중요하다.

## 9.1 왜 노드풀을 나누는가

* 역할별 워크로드 분리

* 머신 타입 분리

* 스케일링 정책 분리

* 운영 정책 분리

## 예시

* 일반 웹 애플리케이션용 노드풀

* 배치 작업용 노드풀

* 고성능 워크로드용 노드풀

* 시스템 워크로드용 노드풀

---

# 10. 릴리스 채널과 버전 선택

클러스터 생성 시 릴리스 채널을 선택할 수 있고, 클러스터 업그레이드 수신 방식에 영향을 준다. Autopilot은 릴리스 채널 등록이 필수고, Standard는 선택 여지가 있다.

* 버전은 단순히 최신을 고르는 문제가 아님

* 릴리스 채널은 업그레이드 운영과 연결됨

* Autopilot에서는 더 기본적인 선택지로 들어옴

---

# 11. Private Cluster 여부

Private Cluster는 **노드가 내부 IP만 사용**하고, 제어 평면 접근 범위를 조정할 수 있는 VPC-native 클러스터 유형이다.

---

# 12. kubectl 접근과 인증 흐름

운영자는 `kubectl` 로 접근할 수 있어야 한다.

## 기본 흐름

1. GKE 클러스터 생성

2. `gcloud` 로 클러스터 자격증명 가져오기

3. kubeconfig 업데이트

4. `kubectl` 로 API 서버 접근

## 대표 명령

```
gcloud container clusters get-credentials CLUSTER_NAME \
  --region REGION
```

또는 존형이면:

```
gcloud container clusters get-credentials CLUSTER_NAME \
  --zone ZONE
```

`get-credentials` 명령이 kubeconfig 엔트리를 생성하고 향후 `kubectl` 이 해당 클러스터를 기본 사용하도록 설정한다. 또한 기본적으로 내부 IP를 사용하지 않고, 내부 IP를 사용하려면 `--internal-ip` 옵션을 쓴다.

---

# 13. 클러스터 생성 시 체크리스트

## 생성 전 체크리스트

* 운영 모드가 무엇인가

* 존형인가, 리전형인가

* 어떤 VPC/서브넷을 쓸 것인가

* Pod/Service IP 대역은 어떻게 할 것인가

* Private Cluster가 필요한가

* 릴리스 채널은 무엇인가

* 노드풀은 어떻게 나눌 것인가

* 생성 후 kubectl 접근은 어떻게 할 것인가

---

# 14. 장 요약

* GKE 클러스터 생성은 단순한 배포 작업이 아니라 **운영 구조 설계**다.

* 클러스터 생성 전에 운영 모드, 존형/리전형, 네트워크, IP 대역, 노드풀, 접근 방식 등을 먼저 정리해야 한다.

* GKE는 **VPC-native 클러스터**를 권장하며, Pod IP가 VPC 내에서 직접 라우팅 가능하다. Autopilot은 VPC-native가 기본이며 변경할 수 없다.

* Pod CIDR와 Service CIDR는 secondary range 설계와 연결되며, 확장성과 충돌 방지 관점에서 중요하다.

* 노드풀은 단순한 노드 묶음이 아니라 운영 정책 단위다.

* 클러스터 생성 후에는 `get-credentials` 와 `kubectl get nodes` 로 기본 동작을 먼저 확인해야 한다.

---