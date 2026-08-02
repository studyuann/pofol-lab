---
title: "7장 GKE와 AWS 리소스 간 통신 시나리오"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Google 쿠버네티스 아키텍처 설계 및 구축"]
is_public: true
draft: false
---

# 7장. GKE와 AWS 리소스 간 통신 시나리오

## 학습 목표

* GKE Pod → AWS 내부 API 호출 시나리오를 설명할 수 있음

* AWS EC2/EKS → GKE 내부 서비스 접근 시나리오를 설명할 수 있음

* GKE Node IP, Pod IP, Service IP 차이를 설명할 수 있음

* 라우팅, 방화벽, 보안그룹, 이름 해석을 함께 고려해야 하는 이유를 설명할 수 있음

* 내부 서비스 노출 방식과 외부 서비스 노출 방식을 구분할 수 있음

* 멀티클라우드 통신 문제를 단계적으로 점검하는 흐름을 설명할 수 있음

---

## 핵심 키워드

* Pod IP

* Service IP

* Node IP

* VPC-native

* Alias IP

* Internal Load Balancer

* Private DNS

* Forwarding Zone

* Peering Zone

* Route Exchange

* Security Group

* Firewall Rule

* East-West Traffic

---

# 1. VPN이 연결되면 무엇이 되고, 무엇은 아직 안 되는가

AWS와 GCP를 HA VPN으로 연결하면 **두 VPC 사이에 사설 네트워크 경로**가 생긴다. Cloud VPN은 피어 네트워크와 Google Cloud 네트워크 사이를 IPsec으로 연결하고, Cloud Router는 BGP로 경로를 동적으로 교환한다. 하지만 이것은 어디까지나 **네트워크 경로**가 생겼다는 뜻이지, 애플리케이션 통신이 바로 완성된다는 뜻은 아니다.

## VPN이 만들어주는 것

* GCP VPC CIDR ↔ AWS VPC CIDR 간 사설 경로

* BGP 기반 동적 경로 교환

* 장애 시 우회 가능한 기본 네트워크 기반

## VPN만으로 해결되지 않는 것

* 어떤 대역을 실제로 광고할지

* 보안그룹/방화벽 허용 여부

* DNS 이름 해석

* GKE 내부 Service 접근 방식

* Pod 대역과 Node 대역 중 무엇을 쓸지 결정

* 애플리케이션 레벨 인증/권한

---

# 2. 먼저 구분해야 할 3가지 주소

GKE와 AWS 통신을 설명할 때 가장 먼저 정리해야 하는 것이 주소 체계다.

## 2.1 Node IP

* GKE 노드 VM이 사용하는 IP

* GCP VPC 서브넷의 기본 주소 체계에 속함

## 2.2 Pod IP

* GKE Pod가 사용하는 IP

* VPC-native 클러스터에서는 alias IP 기반으로 할당됨

* VPC 안에서 라우팅 가능한 주소 체계로 설계됨

## 2.3 Service IP

* ClusterIP 같은 Kubernetes Service가 사용하는 가상 IP

* 일반적으로 클러스터 내부용이며, 다른 VPC에서 그대로 접근 대상으로 보기 어렵다.

---

# 3. 시나리오 1: GKE Pod → AWS 내부 API 호출

## 예시 상황

* GKE에서 실행되는 마이크로서비스가 있음

* 기존 AWS EC2 또는 EKS 내부에 API 서버가 있음

* GKE Pod가 AWS 내부 API를 사설 IP 또는 내부 DNS 이름으로 호출해야 함

## 이 시나리오가 쉬운 이유

* 호출 시작점이 GKE Pod임

* 대상이 AWS 내부 서비스임

* GKE 쪽은 아웃바운드 호출만 하면 됨

* AWS 쪽에서 해당 소스 대역을 허용하면 됨

### 필요한 조건

* GCP에서 AWS 대역으로 가는 경로 존재

* AWS에서 GCP Pod 대역 또는 Node 대역에 대한 응답 경로 존재

* AWS 보안그룹이 GKE 쪽 소스 대역을 허용

* DNS 이름을 쓸 경우 이름 해석 경로 존재

---

# 4. 시나리오 2: AWS EC2/EKS → GKE 내부 서비스 접근

## 예시 상황

* AWS 쪽 애플리케이션이 GKE 내부 서비스에 접근해야 함

* GKE 안의 특정 서비스가 AWS 쪽 시스템에 백엔드 역할을 함

## 왜 더 복잡한가

* GKE Service IP는 보통 클러스터 내부 가상 IP라서 그대로 외부 VPC에서 접근 대상으로 보기 어렵다

* GKE 내부 서비스는 **Internal LoadBalancer Service** 나 Gateway/로드밸런서 기반으로 적절히 노출해야 하는 경우가 많다

* 어떤 주소를 AWS가 목적지로 볼 것인지 설계해야 한다.

### 권장 접근 감각

* GKE Service를 **내부용 LoadBalancer** 형태로 노출

* 또는 Gateway/로드밸런서 구조로 내부 진입점 구성

* AWS는 그 내부 VIP 또는 내부 LB 주소로 접근

---

# 5. 시나리오 3: GKE Pod ↔ AWS DB 또는 공용 서비스 아닌 내부 서비스

## 예시

* GKE Pod가 AWS 내부 RDS 프록시나 내부 DB 엔드포인트에 접근

* AWS 내부 Redis, 내부 MQ, 내부 API Gateway private endpoint에 접근

## 고려할 점

* DB를 정말 클라우드 간에 직접 열어야 하는가

* 지연 시간과 장애 도메인을 감수할 수 있는가

* 네트워크만 여는 것으로 끝나는가, 애플리케이션 재시도와 타임아웃도 맞춰야 하는가

* 운영 중 어느 쪽 장애가 어느 쪽에 전파되는가

---

# 6. DNS는 왜 같이 설계해야 하는가

Google Cloud DNS는 **forwarding zones** 와 **peering zones** 같은 기능을 제공해 하이브리드/멀티클라우드 이름 해석 구조를 만들 수 있다. Forwarding zone은 쿼리를 다른 이름 서버로 전달하고, peering zone은 다른 VPC 네트워크의 이름 해석 권한을 재사용하는 개념이다.

## 자주 나오는 방식

* AWS 내부 DNS 이름을 그대로 쓰고 싶음

* GCP 내부 서비스 이름을 AWS에서 해석하고 싶음

* 공통 사설 도메인 체계를 운영하고 싶음

## 설계 선택지 예시

* 각 클라우드의 사설 DNS를 그대로 두고 forwarding 구성

* 공통 private zone 운영

* 일부 서비스는 IP로만 접근

* DNS는 한쪽에서 authoritative 하게 유지하고 반대편은 포워딩만 수행

---

# 7. 보안은 방화벽과 보안그룹을 같이 봐야 한다

GCP와 AWS는 보안 제어 방식이 다르다.

## GCP 쪽

* VPC Firewall Rule 중심

* 대상 태그/서비스 계정 기반 제어 가능

## AWS 쪽

* Security Group / NACL 중심

* ENI 또는 리소스 부착형 감각이 강함

멀티클라우드 통신에서는 양쪽을 모두 맞춰야 한다.

### 예시

* AWS 보안그룹에서 GKE Pod 대역 또는 Node 대역 허용

* GCP 방화벽에서 AWS VPC 대역 허용

* 필요한 포트만 최소 허용

* SSH/RDP 같은 관리 포트는 IAP나 제한된 소스만 허용 권장

---

# 8. 어떤 대역을 광고할 것인가

BGP가 경로를 자동 교환한다고 해도, 무엇을 광고할지는 여전히 설계 문제다.

## 선택지

* GCP VPC 서브넷만 광고

* GKE 노드 대역 포함

* GKE Pod 대역 포함

* 특정 대역만 제한적으로 광고

Cloud Router는 동적 경로 교환을 담당하고, 광고 범위를 설계에 따라 조정할 수 있다.

---

# 9. GKE 내부 서비스 노출 방식 선택

AWS에서 GKE 서비스를 호출해야 할 때는 노출 방식을 먼저 정해야 한다.

## 후보

* ClusterIP: 보통 외부 VPC 접근 대상으로는 부적합

* NodePort: 가능하지만 운영형 구조로는 거칠고 관리가 불편함

* Internal LoadBalancer Service: 운영형 내부 진입점으로 적합

* Gateway/Load Balancer 기반 내부 노출: 더 표준화된 구조 가능 ([Google Cloud Documentation](https://docs.cloud.google.com/docs/get-started/aws-azure-gcp-service-comparison?utm_source=chatgpt.com))

---

# 10. 관찰성과 장애 분석은 어떻게 볼 것인가

멀티클라우드에서는 장애가 나면 한쪽만 보면 안 된다.

## 봐야 할 것

* VPN 터널 상태

* BGP 세션 상태

* GCP 방화벽 로그

* AWS 보안그룹/라우트 상태

* GKE 애플리케이션 로그

* AWS 대상 서비스 로그

* DNS 질의 실패 여부

---

# 11. 장 요약

* AWS-GCP VPN이 연결되었다고 해서 애플리케이션 통신이 자동으로 완성되는 것은 아니다.

* 멀티클라우드 통신에서는 Node IP, Pod IP, Service IP를 구분해서 봐야 한다. GKE는 VPC-native/alias IP 기반 구조를 사용한다.

* GKE Pod → AWS 내부 API 시나리오는 비교적 직관적이지만, AWS → GKE 내부 서비스 시나리오는 내부 노출 방식 설계가 더 중요하다.

* DNS는 VPN과 별개로 설계해야 하며, forwarding/peering 같은 이름 해석 전략이 필요할 수 있다.

* 멀티클라우드 보안은 GCP 방화벽과 AWS 보안그룹을 함께 봐야 한다.

* 장애 분석은 터널, BGP, 라우트, 보안정책, DNS, 애플리케이션 순으로 계층적으로 봐야 한다.

### 핵심 결론

**멀티클라우드 통신은 VPN 연결 위에서 라우팅, 보안, DNS, 서비스 노출 방식을 모두 맞춰야 완성된다.**

---