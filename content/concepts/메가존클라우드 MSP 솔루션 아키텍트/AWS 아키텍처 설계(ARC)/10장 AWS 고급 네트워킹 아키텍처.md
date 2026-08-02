---
title: "10장 AWS 고급 네트워킹 아키텍처"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 아키텍처 설계(ARC)"]
is_public: true
draft: false
---

# 10장 AWS 고급 네트워킹 아키텍처

## VPC Endpoint, VPC Peering, Direct Connect, VPN, Transit Gateway

---

# 10.1 고급 네트워킹의 필요성

실제 운영 환경으로 가면 네트워크 요구사항이 훨씬 복잡해짐.

예를 들면 다음과 같음.

* Private Subnet의 EC2가 인터넷을 통하지 않고 S3에 접근해야 함

* 서로 다른 VPC 간 통신이 필요함

* AWS와 온프레미스 데이터센터를 연결해야 함

* 여러 계정과 여러 VPC를 중앙에서 연결해야 함

* 대역폭, 지연시간, 보안 요구사항에 따라 연결 방식을 달리해야 함

즉, 고급 네트워킹은 단순히 연결의 문제가 아니라

* 보안

* 성능

* 확장성

* 운영 단순성

* 비용

을 함께 고려하는 아키텍처 문제임.

---

# 10.2 네트워크 연결을 보는 큰 관점

AWS 고급 네트워킹은 크게 다음 3가지 방향으로 나누어 이해하면 좋음.

### 1. VPC 내부에서 AWS 서비스로 프라이빗 연결

예

* S3

* DynamoDB

* Systems Manager

* EC2 API

대표 서비스

* VPC Endpoint

### 2. VPC와 VPC 간 연결

예

* 개발 VPC와 운영 VPC 연결

* Shared Services VPC 연결

대표 서비스

* VPC Peering

* Transit Gateway

### 3. AWS와 온프레미스 연결

예

* 사내 데이터센터와 AWS 연결

* 지사 네트워크와 AWS 연결

대표 서비스

* Site-to-Site VPN

* Direct Connect

즉, 아래 서비스들은 모두 “연결”과 관련 있지만, 연결 대상과 규모가 서로 다름.

---

# 10.3 VPC Endpoint 개요

VPC Endpoint는 VPC 내부 리소스가 인터넷 게이트웨이, NAT Gateway, 퍼블릭 IP 없이 AWS 서비스에 프라이빗하게 접근할 수 있도록 해주는 기능임.

예를 들어 Private Subnet의 EC2가 S3에 접근해야 한다고 가정하면, 기본적으로는 NAT Gateway를 통해 인터넷 방향으로 나가게 구성할 수 있음.

하지만 실제로 S3는 AWS 내부 서비스이므로, 굳이 공용 인터넷 경로를 통과하지 않고 더 직접적이고 안전하게 접근하고 싶을 수 있음.

이때 사용하는 것이 VPC Endpoint임.

즉, VPC Endpoint는

```
VPC 내부에서 AWS 서비스로 가는 사설 경로
```

라고 이해하면 됨.

---

# 10.4 VPC Endpoint가 필요한 이유

VPC Endpoint를 사용하는 이유는 다음과 같음.

### 1. 인터넷 경로 제거

Private Subnet 리소스가 AWS 서비스에 접근할 때 인터넷 게이트웨이나 NAT를 거치지 않아도 됨.

### 2. 보안 향상

트래픽이 공용 인터넷으로 나가지 않고 AWS 백본 내부를 통해 이동함.

### 3. NAT 비용 절감 가능

일부 트래픽은 NAT Gateway를 거치지 않아도 되므로 비용 최적화에 도움이 될 수 있음.

### 4. 프라이빗 아키텍처 구현

인터넷 차단 환경에서도 AWS 서비스 연동이 가능해짐.

즉, VPC Endpoint는 보안과 네트워크 단순화 측면에서 매우 중요함.

---

# 10.5 VPC Endpoint 종류

VPC Endpoint는 크게 다음 유형으로 구분함.

* Gateway Endpoint

* Interface Endpoint

---

## 10.5.1 Gateway Endpoint

Gateway Endpoint는 다음 서비스에 사용됨.

* Amazon S3

* DynamoDB

특징

* Route Table에 대상 경로를 추가하는 방식

* 별도 ENI 생성이 아님

* 특정 AWS 서비스에 대해 단순하고 효율적인 연결 제공

즉, Gateway Endpoint는 S3와 DynamoDB처럼 사용 빈도가 일부 서비스에 대해 특별히 제공되는 방식임.

---

## 10.5.2 Interface Endpoint

Interface Endpoint는 VPC 내부에 **ENI(Elastic Network Interface)** 를 생성해서 AWS 서비스에 연결하는 방식임.

주요 대상 예

* Systems Manager

* EC2 API

* CloudWatch Logs

* Secrets Manager

* KMS

* SNS

* SQS

* PrivateLink 기반 서비스

특징

* Subnet 안에 프라이빗 IP를 가진 엔드포인트가 생성됨

* Security Group을 적용할 수 있음

* 매우 다양한 서비스에 사용 가능함

즉, Interface Endpoint는 보다 범용적인 프라이빗 연결 방식임.

---

# 10.6 Gateway Endpoint와 Interface Endpoint 차이

| 항목 | Gateway Endpoint | Interface Endpoint |
| --- | --- | --- |
| 주요 대상 | S3, DynamoDB | 대부분의 AWS 서비스 |
| 동작 방식 | Route Table 경로 추가 | ENI 생성 |
| Security Group 적용 | 직접적 개념 약함 | 가능 |
| 비용 구조 | 서비스별 특성 다름 | 보통 시간/데이터 처리 과금 고려 |
| 배치 위치 | 라우팅 수준 | 서브넷 내부 엔드포인트 |

즉,

* **S3/DynamoDB 프라이빗 연결**이면 Gateway Endpoint

* **그 외 AWS 서비스 프라이빗 연결**이면 Interface Endpoint

---

# 10.7 PrivateLink 개념

PrivateLink는 AWS 서비스나 타사 서비스, 또는 다른 계정의 서비스를 프라이빗하게 노출하고 연결할 수 있게 해주는 기술임. Interface Endpoint가 이에 해당함.

즉, **서비스 제공자와 소비자 사이를 사설 네트워크 방식으로 연결하는 구조**를 가능하게 함.

예를 들어

* 다른 계정의 내부 서비스 소비

* SaaS 서비스에 프라이빗 접근

* 중앙 서비스 VPC를 여러 소비자 VPC가 사용

같은 구조에 활용할 수 있음.

---

# 10.8 VPC Peering 개요

VPC Peering은 두 개의 VPC를 직접 연결해서 서로 프라이빗 IP로 통신할 수 있게 하는 기능임.

즉, 서로 다른 VPC가 마치 하나의 네트워크처럼 사설 통신을 하게 만드는 단순한 연결 방식임.

예

```
VPC-A  ←→  VPC-B
```

VPC Peering이 설정되면 두 VPC 안의 리소스는 각자의 사설 IP를 이용해 통신할 수 있음.

---

# 10.9 VPC Peering의 특징

### 1. 단순한 1:1 연결

Peering은 기본적으로 두 VPC 사이의 직접 연결임.

### 2. 사설 IP 통신

공인 IP나 인터넷 게이트웨이를 거치지 않고 프라이빗 통신이 가능함.

### 3. 낮은 지연과 단순 구조

규모가 작을 때는 이해와 운영이 비교적 쉬움.

즉, VPC Peering은 소규모 연결에서는 매우 직관적인 선택임.

---

# 10.10 VPC Peering의 제약

VPC Peering은 단순하지만 확장성이 제한됨.

### 1. Transitive Routing 미지원

가장 중요한 특징임.

예를 들어

```
VPC-A ←→ VPC-B ←→ VPC-C
```

이 구조가 있어도 A와 C가 B를 통해 자동 통신할 수는 없음.

즉, A-B, B-C가 연결되었다고 해서 A-C가 자동 연결되지 않음.

### 2. 연결 수 증가 시 복잡도 증가

VPC가 많아질수록 필요한 피어링 수가 급격히 증가함.

### 3. 중앙 허브 구조에 부적합

대규모 멀티 VPC 환경에서는 관리가 복잡해짐.

즉, VPC Peering은 적은 수의 VPC를 직접 연결할 때는 좋지만,

VPC 수가 많아질수록 관리 효율이 떨어짐.

---

# 10.11 VPC Peering이 적합한 경우

다음과 같은 경우에 적합함.

* VPC 수가 적음

* 두 VPC 사이만 직접 연결하면 됨

* 중앙 허브 구조가 필요 없음

* 단순하고 빠른 연결이 필요함

예

* 개발 VPC ↔ 공유 서비스 VPC

* 앱 VPC ↔ 데이터 VPC

즉, 작고 단순한 구조에서는 여전히 유효한 선택임.

---

# 10.12 Site-to-Site VPN 개요

Site-to-Site VPN은 AWS와 온프레미스 네트워크를 IPsec 터널로 연결하는 방식임.

즉, 인터넷을 기반으로 하지만 암호화된 터널을 통해 사설 네트워크처럼 연결하는 기술임.

구조 예

```
온프레미스 라우터
     │
인터넷(IPsec VPN)
     │
AWS VPN Endpoint
     │
VPC
```

즉, VPN은 전용선이 아니라 **인터넷 기반의 암호화 연결**임.

---

# 10.13 VPN의 특징

### 1. 비교적 빠른 구축

전용 회선보다 준비가 빠름.

### 2. 초기 비용이 상대적으로 낮음

Direct Connect보다 진입 장벽이 낮음.

### 3. 암호화 지원

IPsec 기반으로 트래픽 보호 가능.

### 4. 인터넷 품질의 영향

기반이 인터넷이므로 지연시간과 품질이 전용선만큼 안정적이지 않을 수 있음.

즉, VPN은 유연하고 빠르지만, 네트워크 품질 면에서는 한계가 있을 수 있음.

---

# 10.14 VPN의 주요 구성 요소

Site-to-Site VPN을 이해할 때 자주 나오는 요소

* Customer Gateway (CGW)

* Virtual Private Gateway (VGW) 또는 Transit Gateway

* VPN Connection

* Tunnel

* BGP 또는 Static Routing

---

## 10.14.1 Customer Gateway

온프레미스 측 VPN 장비 또는 그것의 논리적 표현임.

즉, AWS 입장에서 “고객 측 라우터”를 의미함.

---

## 10.14.2 Virtual Private Gateway

VPC 쪽에 연결되는 AWS 측 VPN 종단점 역할을 함.

전통적인 VPC 기반 VPN 구성에서 사용됨.

---

## 10.14.3 Tunnel

AWS Managed Site-to-Site VPN은 보통 이중화된 두 개의 터널을 제공함.

이는 가용성 확보 목적임.

즉, VPN은 논리적으로 하나처럼 보이지만 내부적으로는 보통 복수 터널을 사용함.

---

## 10.14.4 BGP와 Static Routing

VPN 연결의 라우팅 방식은 크게 두 가지임.

### Static Routing

관리자가 고정 라우트를 직접 정의함.

### BGP

동적 라우팅을 통해 경로를 교환함.

일반적으로 규모가 커지고 경로 유연성이 중요해질수록 BGP가 유리함.

---

# 10.15 VPN이 적합한 경우

* 빠르게 하이브리드 연결을 구성해야 할 때

* 테스트/개발/초기 운영 단계

* 비용을 비교적 낮게 가져가고 싶을 때

* 전용선 구축까지의 임시 연결

* 백업 연결로 사용할 때

즉, VPN은 “빠르고 유연한 연결”에 강점이 있음.

---

# 10.16 AWS Direct Connect 개요

Direct Connect는 AWS와 온프레미스 또는 코로케이션 환경을 **전용 네트워크 회선**으로 연결하는 서비스임.

즉, VPN처럼 공용 인터넷을 거치는 것이 아니라,

AWS와 고객 네트워크 사이를 전용 경로로 연결하는 방식임.

구조 관점에서는 다음처럼 이해하면 됨.

```
온프레미스 네트워크
      │
전용 회선
      │
AWS Direct Connect Location
      │
AWS 네트워크
```

즉, DX는 인터넷 기반 연결이 아니라 **전용선 기반 연결**임.

---

# 10.17 Direct Connect의 장점

### 1. 안정적인 네트워크 품질

공용 인터넷보다 예측 가능한 지연시간과 품질을 기대할 수 있음.

### 2. 높은 대역폭

대용량 데이터 전송에 적합함.

### 3. 하이브리드 아키텍처 적합

온프레미스와 AWS를 장기적으로 연결하는 환경에 적합함.

### 4. 대규모 데이터 이전에 유리

백업, 복제, 분석 데이터 이동 등에서 장점이 큼.

즉, Direct Connect는 품질과 대역폭이 중요한 환경에 적합함.

---

# 10.18 Direct Connect의 한계

### 1. 구축 시간이 상대적으로 걸림

전용 회선 준비와 통신사/시설 연계가 필요할 수 있음.

### 2. 초기 진입 장벽

VPN보다 도입 과정이 복잡할 수 있음.

### 3. 비용 구조 고려 필요

장기 운영에는 가치가 크지만, 소규모 단기 환경에는 과할 수 있음.

즉, Direct Connect는 강력하지만 모든 환경에 필요한 것은 아님.

---

# 10.19 VPN과 Direct Connect 비교

| 항목 | Site-to-Site VPN | Direct Connect |
| --- | --- | --- |
| 기반 | 인터넷 + IPsec | 전용 회선 |
| 구축 속도 | 빠름 | 상대적으로 느림 |
| 비용 | 비교적 낮음 | 상대적으로 큼 |
| 품질 예측성 | 인터넷 영향 받음 | 높음 |
| 대역폭/대용량 전송 | 제한적일 수 있음 | 유리 |
| 대표 용도 | 빠른 하이브리드 연결, 백업 연결 | 장기적 하이브리드 핵심 연결 |

즉,

* **빠른 연결과 저비용**이면 VPN

* **안정성과 대역폭**이면 Direct Connect

라고 정리할 수 있음.

---

# 10.20 Transit Gateway 개요

Transit Gateway는 여러 VPC와 온프레미스 연결을 중앙 허브 방식으로 연결하는 서비스임.

즉, 복잡하게 얽힌 다수의 VPC 연결을 하나의 중앙 라우팅 허브로 단순화하는 역할을 함.

구조 예

```
         VPC-A
           │
         TGW
       /  |  \
   VPC-B VPC-C On-Prem
```

즉, Transit Gateway는 **네트워크 허브**임.

---

# 10.21 Transit Gateway가 필요한 이유

VPC 수가 적을 때는 Peering으로도 충분할 수 있음.

하지만 VPC가 많아지면 Peering은 관리가 매우 복잡해짐.

예를 들어 VPC가 10개면 가능한 연결 조합이 크게 늘어남.

이런 구조에서는

* 라우팅 관리

* 연결 생성/삭제

* 운영 추적

* 계정 간 연결 관리

가 매우 복잡해짐.

Transit Gateway를 사용하면 각 VPC는 TGW에만 연결하면 되고, 전체 연결 구조를 중앙에서 관리할 수 있음.

즉, Transit Gateway는 **확장 가능한 멀티 VPC 연결 구조**를 위한 서비스임.

---

# 10.22 Transit Gateway의 특징

### 1. 허브 앤 스포크 구조

중앙 허브(TGW)에 여러 VPC와 연결을 붙이는 구조임.

### 2. Transitive Routing 가능

Peering과 다르게 중앙 라우팅을 통해 간접 연결이 가능함.

### 3. 온프레미스와도 연결 가능

VPN, Direct Connect와 결합해 중앙 연결 허브로 사용할 수 있음.

### 4. 대규모 멀티 계정 구조에 적합

Organizations, RAM 등과 함께 대규모 네트워크 설계에 자주 사용됨.

즉, TGW는 단순 연결 서비스가 아니라 **대규모 네트워크 토폴로지 관리 도구**에 가까움.

---

# 10.23 VPC Peering과 Transit Gateway 차이

| 항목 | VPC Peering | Transit Gateway |
| --- | --- | --- |
| 연결 구조 | 1:1 직접 연결 | 중앙 허브 연결 |
| Transitive Routing | 불가 | 가능 |
| 소규모 환경 | 적합 | 가능 |
| 대규모 멀티 VPC | 비효율적 | 적합 |
| 운영 복잡도 | VPC 수 증가 시 커짐 | 중앙 관리 가능 |

즉,

* **소규모 단순 연결**이면 Peering

* **대규모 허브형 연결**이면 Transit Gateway

라고 이해하면 됨.

---

# 10.24 고급 네트워킹 선택 기준

이 장의 서비스들은 비슷해 보이지만 해결하려는 문제가 다름.

그래서 “무엇을 연결하려는가”를 먼저 봐야 함.

---

## 10.24.1 AWS 서비스에 프라이빗하게 접근하고 싶은가

* VPC Endpoint 고려

예

* Private EC2 → S3

* Private EC2 → Systems Manager

* Private App → Secrets Manager

---

## 10.24.2 두 개의 VPC만 단순히 연결하면 되는가

* VPC Peering 고려

예

* Dev VPC ↔ Shared VPC

---

## 10.24.3 여러 VPC와 온프레미스를 중앙에서 연결해야 하는가

* Transit Gateway 고려

예

* Shared Services Hub

* Multi-Account Network Hub

---

## 10.24.4 온프레미스와 빠르게 연결해야 하는가

* Site-to-Site VPN 고려

---

## 10.24.5 온프레미스와 안정적이고 대역폭 큰 연결이 필요한가

* Direct Connect 고려

---

# 10.25 보안 관점에서의 의미

고급 네트워킹은 단순 연결 이상의 보안 의미를 가짐.

### 1. 인터넷 노출 최소화

VPC Endpoint를 사용하면 AWS 서비스 접근을 인터넷 없이 처리 가능함.

### 2. 네트워크 경계 통제

Peering, TGW, VPN, DX는 어떤 네트워크가 어떤 네트워크와 연결되는지 설계하는 문제임.

### 3. 세분화된 라우팅

경로를 중앙에서 관리할수록 통제가 쉬워질 수 있음.

### 4. 계정/네트워크 분리와 연결의 균형

멀티 계정 구조에서는 분리도 중요하고, 필요한 연결을 안전하게 만드는 것도 중요함.

즉, 네트워킹2 장은 보안 아키텍처와도 강하게 연결됨.

---

# 10.26 운영 관점의 설계 포인트

### 1. 단순성 우선

작은 구조인데 무조건 TGW나 DX를 쓰는 것은 과할 수 있음.

규모에 맞는 설계를 해야 함.

### 2. 라우팅 복잡성 관리

연결 자체보다 경로 관리가 더 어려워질 수 있음.

### 3. 장애 대비

VPN은 백업 연결, DX는 주 연결 등으로 조합하는 경우도 많음.

### 4. 비용과 구조 균형

NAT 비용 절감을 위해 Endpoint를 쓰는 것처럼, 연결 방식은 비용과도 관련됨.

### 5. 미래 확장 고려

현재는 VPC 2개라도 나중에 10개가 될 수 있다면 처음부터 확장 구조를 염두에 두는 것이 좋음.

---

# 10.27 예시 아키텍처 흐름 정리

## 예시 1. Private Subnet에서 S3 접근

* 인터넷 경로 대신 Gateway Endpoint 사용

## 예시 2. 운영 VPC와 공용 서비스 VPC 연결

* 단순 구조라면 VPC Peering 사용 가능

## 예시 3. 여러 계정의 VPC를 중앙 서비스망에 연결

* Transit Gateway 적합

## 예시 4. 사내 IDC와 AWS를 빠르게 연결

* Site-to-Site VPN 적합

## 예시 5. 대용량 데이터 백업을 AWS로 전송

* Direct Connect 적합 가능성 높음

---

# 10.28 멀티 티어 아키텍처와의 연결

앞에서 만든 멀티 티어 구조를 확장해서 보면 다음처럼 연결될 수 있음.

```
On-Prem
   │
VPN 또는 DX
   │
Transit Gateway
   ├ App VPC
   ├ Data VPC
   └ Shared Services VPC
```

그리고 각 VPC 내부에서는

* Private EC2 → S3 via VPC Endpoint

* Shared Services → Interface Endpoint / PrivateLink

* 계정 간 서비스 공유

같은 구조가 가능해짐.

즉, 이 장은 기존 단일 VPC 구조를 **엔터프라이즈 네트워크 구조로 확장하는 장**이라고 볼 수 있음.

---

# 10.29 서비스 역할 한 번에 정리

## VPC Endpoint

VPC 내부 리소스가 AWS 서비스에 프라이빗하게 접근하도록 한다.

## VPC Peering

두 VPC를 직접 연결한다.

## Site-to-Site VPN

온프레미스와 AWS를 인터넷 기반 암호화 터널로 연결한다.

## Direct Connect

온프레미스와 AWS를 전용 회선으로 연결한다.

## Transit Gateway

여러 VPC와 온프레미스 연결을 중앙 허브로 통합한다.

---

# 10.30 장 요약

이번 장에서 학습한 핵심 내용

* 고급 네트워킹이 필요한 이유

* VPC Endpoint의 개념과 필요성

* Gateway Endpoint와 Interface Endpoint 차이

* PrivateLink 개념

* VPC Peering의 구조와 제약

* Site-to-Site VPN의 개념과 특징

* Direct Connect의 개념과 특징

* VPN과 DX 비교

* Transit Gateway의 필요성과 역할

* Peering과 TGW 비교

* 연결 방식 선택 기준

* 보안과 운영 관점의 설계 포인트

---

# 10.31 한 줄 정리

```
VPC Endpoint는 AWS 서비스로의 프라이빗 접근을 만든다.
VPC Peering은 두 VPC를 직접 연결한다.
VPN과 Direct Connect는 온프레미스와 AWS를 연결한다.
Transit Gateway는 여러 네트워크 연결을 중앙 허브로 통합한다.
```

---