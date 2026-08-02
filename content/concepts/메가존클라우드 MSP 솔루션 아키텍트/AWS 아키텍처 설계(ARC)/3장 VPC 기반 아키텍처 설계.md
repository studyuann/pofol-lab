---
title: "3장 VPC 기반 아키텍처 설계"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 아키텍처 설계(ARC)"]
is_public: true
draft: false
---

# 3장 VPC 기반 아키텍처 설계

# 3.1 아키텍처 설계에서 VPC의 의미

Amazon VPC는 AWS 환경에서 애플리케이션과 데이터, 보안 정책, 통신 경로를 담는 네트워크 영역이다.

아키텍처를 설계할 때 VPC는 단순한 네트워크 리소스가 아니라, 서비스의 경계를 나누고 트래픽 흐름을 통제하는 기반이 된다.

하나의 서비스는 보통 여러 계층으로 구성된다.

* 외부 요청을 수신하는 계층

* 비즈니스 로직을 처리하는 계층

* 데이터를 저장하는 계층

이 계층들을 모두 하나의 동일한 네트워크 성격으로 두지 않고, 역할에 따라 분리해서 배치하는 것이 중요하다.

이때 VPC와 Subnet, Route Table, Gateway, Security Group이 함께 사용된다.

즉 VPC 설계의 핵심은 다음과 같다.

* 어떤 리소스를 외부에 노출할 것인가

* 어떤 리소스를 내부에만 둘 것인가

* 각 계층이 어떤 경로로 통신해야 하는가

* 장애와 확장을 고려했을 때 어떤 구조가 적절한가

---

# 3.2 계층형 아키텍처와 네트워크 분리

일반적인 웹 서비스는 계층형 구조로 설계한다.

```
사용자
  │
Load Balancer
  │
Application Server
  │
Database
```

이 구조를 AWS 네트워크에 배치하면 다음과 같이 구성할 수 있다.

```
VPC
 ├─ Public Subnet
 │   └─ Load Balancer
 ├─ Private Application Subnet
 │   └─ EC2 / ECS / EKS
 └─ Private Database Subnet
     └─ RDS
```

이 구조의 목적은 각 계층의 역할을 명확하게 분리하는 데 있다.

* 외부 요청을 받는 계층은 인터넷과 연결된 영역에 배치

* 애플리케이션 처리 계층은 내부 네트워크에 배치

* 데이터베이스 계층은 가장 안쪽 네트워크에 배치

이렇게 구성하면 외부 노출 범위를 최소화할 수 있고, 보안 정책도 계층별로 분리해서 적용할 수 있다.

---

# 3.3 Public Subnet과 Private Subnet의 역할

Subnet은 단순히 IP 대역을 나누는 용도만이 아니라,

리소스의 역할과 접근 범위를 구분하는 수단이 된다.

## Public Subnet

Public Subnet에는 인터넷과 직접 통신해야 하는 리소스를 배치한다.

대표적인 예시는 다음과 같다.

* Internet-facing Load Balancer

* NAT Gateway

* Bastion Host

* 외부에서 직접 접근이 필요한 관리용 서버

Public Subnet의 핵심은 인터넷 연결 경로를 가진다는 점이다.

다만 인터넷 연결 경로가 있다고 해서 그 안의 모든 리소스가 자동으로 외부에 공개되는 것은 아니다.

실제 외부 접근 가능 여부는 Public IP 할당 여부와 보안 정책에 따라 결정된다.

## Private Subnet

Private Subnet에는 외부에서 직접 접근할 필요가 없는 리소스를 배치한다.

대표적인 예시는 다음과 같다.

* Application Server

* 내부 API 서버

* Database

* Cache

* Batch Server

Private Subnet은 외부 사용자로부터 직접 접근되지 않도록 구성하는 것이 목적이다.

이 계층의 리소스는 보통 Load Balancer, 내부 서비스, 관리 채널 등을 통해서만 접근한다.

---

# 3.4 Route Table과 트래픽 흐름 설계

Route Table은 네트워크 트래픽이 목적지에 따라 어디로 전달되는지 정의한다.

아키텍처 설계에서는 Route Table이 각 서브넷의 성격을 결정하는 중요한 요소가 된다.

예를 들어 다음과 같은 경로는 인터넷 연결이 가능한 서브넷에 사용된다.

```
Destination        Target
10.0.0.0/16        local
0.0.0.0/0          Internet Gateway
```

이 설정은 다음 의미를 가진다.

* VPC 내부 주소로 향하는 트래픽은 내부에서 처리

* 그 외의 외부 목적지는 Internet Gateway를 통해 전달

반면 Private Subnet에서는 다음과 같이 구성할 수 있다.

```
Destination        Target
10.0.0.0/16        local
0.0.0.0/0          NAT Gateway
```

이 설정은 외부로 나가는 통신은 허용하지만, 외부에서 직접 들어오는 통신은 허용하지 않는 구조에 적합하다.

또한 외부 인터넷 연결이 전혀 필요 없는 내부 전용 계층은 다음과 같이 구성할 수 있다.

```
Destination        Target
10.0.0.0/16        local
```

이 경우 해당 서브넷은 VPC 내부 통신만 수행하게 된다.

따라서 Route Table은 단순 조회 정보가 아니라,

서브넷의 역할과 통신 범위를 결정하는 정책 요소로 봐야 한다.

---

# 3.5 Internet Gateway와 NAT Gateway의 배치 원칙

## Internet Gateway

Internet Gateway는 VPC를 인터넷과 연결한다.

인터넷에서 직접 접근 가능한 진입 계층을 구성하려면 Internet Gateway가 필요하다.

다만 Internet Gateway가 연결되어 있어도 다음 조건이 함께 맞아야 실제 인터넷 통신이 가능하다.

* 해당 서브넷의 Route Table에 인터넷 방향 경로가 있어야 함

* 인스턴스에 Public IP 또는 Elastic IP가 있어야 함

* Security Group에서 필요한 포트가 허용되어 있어야 함

즉 Internet Gateway는 인터넷 연결을 위한 구성 요소 중 하나이며,

라우팅과 IP, 보안 정책이 함께 맞물려야 한다.

## NAT Gateway

NAT Gateway는 Private Subnet 리소스가 외부 인터넷으로 나갈 수 있게 한다.

중요한 점은 아웃바운드 연결만 허용하고, 외부에서 Private 리소스로 직접 들어오는 연결은 허용하지 않는다는 점이다.

이 구조는 다음과 같은 경우에 필요하다.

* 운영체제 패키지 업데이트

* 외부 API 호출

* 컨테이너 이미지 다운로드

* 보안 에이전트 업데이트

* 저장소 접근

NAT Gateway는 Public Subnet에 배치하고, Private Subnet의 Route Table에서 NAT Gateway를 대상으로 설정한다.

---

# 3.6 보안 그룹 설계 원칙

Security Group은 인스턴스 또는 네트워크 인터페이스 단위에서 적용되는 보안 제어 수단이다.

아키텍처 설계에서는 포트만 보고 설정하기보다, **어느 계층에서 어느 계층으로 허용할 것인지**를 기준으로 설계하는 것이 중요하다.

예를 들어 다음과 같은 구조를 생각할 수 있다.

## Load Balancer Security Group

* 80/443 허용

* 소스: `0.0.0.0/0`

## Application Security Group

* 애플리케이션 포트 허용

* 소스: Load Balancer Security Group

## Database Security Group

* 데이터베이스 포트 허용

* 소스: Application Security Group

이렇게 설계하면 다음과 같은 흐름이 만들어진다.

* 사용자는 Load Balancer까지만 직접 접근 가능

* 애플리케이션 서버는 Load Balancer를 통해서만 요청 수신

* 데이터베이스는 애플리케이션 계층에서만 접근 가능

즉 Security Group은 단순 포트 목록이 아니라, 서비스 구조를 네트워크 정책으로 표현하는 수단이다.

---

# 3.7 데이터 계층 분리의 중요성

데이터베이스는 일반적으로 서비스 구조에서 가장 안쪽 계층에 위치한다.

이 계층은 외부에서 직접 접근할 필요가 거의 없으며, 애플리케이션 계층을 통해서만 접근하는 것이 일반적이다.

따라서 데이터베이스 계층은 다음 원칙을 따른다.

* Private Subnet에 배치

* 전용 Security Group 사용

* 애플리케이션 계층만 접근 허용

* 다중 AZ 구성을 고려

* 백업 및 장애 복구 구조 함께 고려

이러한 구조는 보안뿐 아니라 운영 안정성 측면에서도 중요하다.

---

# 3.8 고가용성을 고려한 VPC 구조

서비스 운영 환경에서는 단일 AZ에만 리소스를 배치하지 않는다.

하나의 AZ에 장애가 발생해도 서비스가 유지될 수 있도록 여러 AZ에 분산 배치하는 것이 일반적이다.

예를 들면 다음과 같은 구조가 된다.

```
VPC
 ├─ Public Subnet A
 ├─ Public Subnet C
 ├─ Private App Subnet A
 ├─ Private App Subnet C
 ├─ Private DB Subnet A
 └─ Private DB Subnet C
```

이 구조를 사용하면 다음과 같은 설계가 가능하다.

* Load Balancer를 다중 AZ에 연결

* 애플리케이션 서버를 여러 AZ에 분산 배치

* 데이터베이스를 Multi-AZ 또는 클러스터 구조로 운영

* 장애 시 특정 AZ 영향 범위를 축소

즉 VPC 설계는 단순 연결이 아니라, 장애 대응 구조까지 포함하는 네트워크 설계라고 볼 수 있다.

---

# 3.9 VPC 아키텍처 설계 시 고려할 사항

VPC를 설계할 때는 다음 요소를 함께 고려해야 한다.

## 1) 노출 범위 최소화

외부에 직접 노출해야 하는 자원만 Public 영역에 둔다.

내부 처리 계층과 데이터 계층은 Private 영역에 두는 것이 기본이다.

## 2) 계층 간 통신 경로 명확화

모든 계층이 모든 계층과 직접 통신하도록 두지 않는다.

필요한 방향과 포트만 허용해야 한다.

## 3) 다중 AZ 설계

단일 AZ 구조는 장애 시 서비스 전체에 영향을 줄 수 있다.

고가용성을 고려하면 여러 AZ에 분산해야 한다.

## 4) 아웃바운드 경로 설계

Private Subnet 리소스가 외부와 통신해야 하는 경우 NAT Gateway 또는 VPC Endpoint를 검토해야 한다.

## 5) IP 대역 계획

향후 확장, 피어링, VPN, 멀티클라우드 연결 가능성을 고려해 CIDR을 설계해야 한다.

---

# 3.10 권장 아키텍처 예

일반적인 웹 서비스 아키텍처는 다음과 같이 설계할 수 있다.

```
사용자
  │
Internet
  │
Internet Gateway
  │
Public Subnet
  │
Application Load Balancer
  │
Private Application Subnet
  │
EC2 / ECS / EKS
  │
Private Database Subnet
  │
RDS
```

필요에 따라 다음 구성 요소를 추가할 수 있다.

* NAT Gateway

* Auto Scaling Group

* VPC Endpoint

* Bastion Host 또는 SSM 기반 관리 접속

* WAF

* Transit Gateway / VPN / Direct Connect

이 구조의 핵심은 외부 진입 지점을 최소화하고, 내부 계층을 단계적으로 보호하는 데 있다.

---

# 3.11 정리

VPC 기반 아키텍처 설계의 핵심은 다음과 같다.

* VPC는 서비스 전체의 네트워크 경계를 정의한다

* Subnet은 리소스 역할과 접근 범위를 나누는 단위가 된다

* Route Table은 각 서브넷의 통신 정책을 결정한다

* Internet Gateway는 외부 진입 계층에 사용된다

* NAT Gateway는 Private 계층의 아웃바운드 통신에 사용된다

* Security Group은 계층 간 통신 정책을 표현하는 중요한 수단이다

* 고가용성을 위해 여러 AZ에 서브넷과 리소스를 분산 배치해야 한다

즉 VPC 아키텍처는 리소스를 배치하는 단순한 공간이 아니라,

**보안, 가용성, 확장성, 운영성을 함께 반영하는 인프라 설계의 핵심 구조**다.

---