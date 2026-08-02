---
title: "3장 AWS 네트워크 기초"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 클라우드 기술 기초(TESS)"]
is_public: true
draft: false
---

# 3장 AWS 네트워크 기초

## 3.1 AWS 네트워크가 왜 중요한가

온프레미스 환경에서도 네트워크는 중요했지만, AWS에서도 중요함.

이유는 AWS에서 대부분의 서비스가 **네트워크 위에서 연결**되기 때문임.

예를 들어 하나의 웹 서비스를 생각해보면 다음과 같은 흐름이 생김.

```
User
 │
Internet
 │
Load Balancer
 │
Web Server
 │
Database
```

이 구조에서 각 구성 요소가 정상적으로 통신하려면 다음이 모두 맞아야 함.

* 어떤 네트워크에 배치할 것인가

* 외부와 연결할 것인가

* 내부에서만 통신하게 할 것인가

* 어떤 경로로 패킷이 이동할 것인가

* 어떤 포트를 허용할 것인가

즉 AWS 네트워크를 이해한다는 것은 단순히 VPC라는 이름을 아는 것이 아니라,

**리소스가 어디에 배치되고 어떤 경로로 통신하는지 이해하는 것**이다.

---

## 3.2 VPC란 무엇인가

VPC는 **Virtual Private Cloud**의 약자다. 말 그대로 AWS 안에서 만드는 **가상의 사설 네트워크**이다.

쉽게 말하면 AWS는 하나의 거대한 클라우드 인프라를 제공하지만, 사용자는 그 안에서 **자신만의 독립된 네트워크 공간**을 만들 수 있음. 그 공간이 바로 VPC다.

예를 들어 회사 A와 회사 B가 모두 AWS를 사용하더라도, 각자 별도의 VPC를 사용하면 서로 네트워크가 분리된다.

즉 VPC는 다음 역할을 한다.

* 네트워크 주소 범위 정의

* 리소스 배치 공간 제공

* 네트워크 격리

* 트래픽 흐름 제어

* 보안 정책 적용 기반 제공

구조를 단순화하면 다음과 같다.

```
AWS Cloud
 └ VPC
    ├ EC2
    ├ RDS
    ├ Load Balancer
    └ Other resources
```

```
VPC는 AWS 안에서 내가 직접 설계하는 내 전용 네트워크다.
```

---

## 3.3 왜 VPC가 필요한가

```
어차피 AWS에 서버 만들면 되는 것 아닌가?
```

그런데 실제 서비스 운영에서는 그냥 서버만 띄우면 안 됨.

다음 같은 요구가 항상 존재함.

* 어떤 서버는 인터넷에 공개해야 함

* 어떤 서버는 외부에서 보이면 안 됨

* 데이터베이스는 내부에서만 접근 가능해야 함

* 서버끼리만 통신 가능한 영역이 필요함

* IP 대역을 직접 설계해야 함

이걸 가능하게 하는 것이 VPC다.

예를 들어 다음과 같은 설계를 할 수 있음.

```
VPC 10.0.0.0/16
 ├ Public Subnet   10.0.1.0/24
 ├ Private Subnet  10.0.2.0/24
 └ DB Subnet       10.0.3.0/24
```

즉 VPC는 단순한 네트워크가 아니라,

**서비스 구조를 설계할 수 있게 해주는 네트워크 틀**이다.

---

## 3.4 CIDR이란 무엇인가

VPC를 만들 때 가장 먼저 보게 되는 것이 CIDR이다.

예

```
10.0.0.0/16
172.16.0.0/16
192.168.0.0/16
```

CIDR은 **IP 주소 범위를 표현하는 방식**이다.

AWS에서 VPC나 Subnet을 만들 때는 반드시 이 CIDR을 사용해야 함.

예를 들어

```
10.0.0.0/16
```

은 큰 네트워크 범위를 의미하고, 그 안에서 여러 개의 작은 Subnet으로 나눌 수 있음.

첫째, VPC는 **하나의 큰 주소 공간**을 먼저 잡는다는 점.

둘째, Subnet은 그 안에서 **작게 나누어 사용하는 주소 공간**이라는 점.

예를 들면 이렇게 볼 수 있음.

```
VPC CIDR      : 10.0.0.0/16
Subnet CIDR   : 10.0.1.0/24
Subnet CIDR   : 10.0.2.0/24
Subnet CIDR   : 10.0.3.0/24
```

---

## 3.5 서브넷(Subnet)이란 무엇인가

Subnet은 VPC 내부를 더 작은 네트워크 단위로 나눈 것이다.

VPC가 하나의 큰 네트워크라면, Subnet은 그 안에 존재하는 **구역**이라고 생각하면 됨.

예

```
VPC 10.0.0.0/16
 ├ Subnet A 10.0.1.0/24
 ├ Subnet B 10.0.2.0/24
 └ Subnet C 10.0.3.0/24
```

Subnet을 나누는 이유는 단순히 IP를 나누기 위해서만은 아님.

실제 목적은 **역할 분리와 보안 분리**다.

예를 들어 다음처럼 설계할 수 있음.

```
Public Subnet  → ALB, Bastion
Private Subnet → App Server
DB Subnet      → Database
```

즉 Subnet을 분리하면

* 공개할 리소스

* 내부 전용 리소스

* 데이터 저장 리소스

를 분리할 수 있음.

이 부분이 AWS 아키텍처 설계의 핵심이다.

---

## 3.6 Public Subnet과 Private Subnet

### Public Subnet

Public Subnet은 **Internet Gateway로 나가는 경로가 있는 서브넷**이다.

즉 라우팅 테이블에 다음 경로가 있는 경우 보통 Public Subnet이라 부름.

```
0.0.0.0/0 → Internet Gateway
```

여기에 퍼블릭 IP를 가진 EC2가 있다면 외부와 직접 통신 가능함.

주로 배치하는 리소스

* Load Balancer

* Bastion Host

* NAT Gateway

* Public EC2

### Private Subnet

Private Subnet은 **Internet Gateway로 직접 나가는 경로가 없는 서브넷**이다.

즉 외부 인터넷과 직접 연결되지 않음.

보안이 더 필요한 리소스를 여기에 배치함.

주로 배치하는 리소스

* Application Server

* Internal Service

* Database

```
Public / Private를 결정하는 것은 이름이 아니라 라우팅 구조다.
```

이 말이 중요함.

Subnet 이름이 public이라고 적혀 있어도,

라우팅이 IGW로 가지 않으면 진짜 Public Subnet이 아님.

---

## 3.7 라우팅 테이블(Route Table)이란 무엇인가

라우팅 테이블은 **패킷이 어디로 가야 하는지 결정하는 경로정보**다.

쉽게 말하면 네트워크에서 길 안내판 역할을 함.

예를 들어 어떤 EC2가 외부 인터넷으로 나가려 할 때, 라우팅 테이블을 보고 다음 홉을 결정함.

예시:

```
Destination     Target
10.0.0.0/16     local
0.0.0.0/0       igw-xxxx
```

의미는 다음과 같다.

* `10.0.0.0/16`으로 가는 트래픽은 VPC 내부에서 처리

* 그 외 모든 트래픽 `0.0.0.0/0`은 Internet Gateway로 전송[![](3%EC%9E%A5%20AWS%20%EB%84%A4%ED%8A%B8%EC%9B%8C%ED%81%AC%20%EA%B8%B0%EC%B4%88/image.png)](3%EC%9E%A5%20AWS%20%EB%84%A4%ED%8A%B8%EC%9B%8C%ED%81%AC%20%EA%B8%B0%EC%B4%88/image.png)

즉 다음 두 가지를 구분해야 함.

* 리소스가 어느 서브넷에 있는가

* 그 서브넷이 어떤 라우팅 테이블을 사용하는가

---

## 3.8 Internet Gateway란 무엇인가

Internet Gateway(IGW)는 VPC와 인터넷을 연결하는 게이트웨이다.

구조를 단순화하면 다음과 같다.

```
Internet
 │
Internet Gateway
 │
VPC
```

IGW가 없으면 VPC는 외부 인터넷과 직접 통신할 수 없음.

IGW가 연결돼 있어도 실제로 인터넷이 되려면 다음 조건이 맞아야 함.

* 서브넷 라우팅 테이블에 IGW 경로 존재

* EC2에 퍼블릭 IP 존재

* 보안 그룹 허용

* 경우에 따라 NACL 허용

즉 IGW는 **인터넷 연결의 구성 요소 중 하나**일 뿐, 그 자체만으로 인터넷이 되는 것은 아님.

---

## 3.9 퍼블릭 IP와 프라이빗 IP

AWS의 EC2는 기본적으로 프라이빗 IP를 가짐.

같은 VPC 내부에서는 이 프라이빗 IP로 통신함.

예

```
10.0.1.10
10.0.2.15
10.0.3.20
```

그런데 외부 인터넷과 직접 통신하려면 퍼블릭 IP가 필요함.

즉

* 프라이빗 IP: VPC 내부 통신용

* 퍼블릭 IP: 인터넷 통신용

예를 들어 웹 서버를 외부에서 접속하려면

* Public Subnet

* IGW 경로

* Public IP

* Security Group 허용

이 네 가지가 조합되어야 함.

```
Public Subnet에 있어도 Public IP가 없으면 외부에서 직접 접근 불가
```

---

## 3.10 보안 그룹(Security Group)이란 무엇인가

Security Group은 AWS의 **가상 방화벽**이다.

EC2나 ENI 단위에 붙여서 인바운드/아웃바운드 트래픽을 제어함.

예

```
Inbound
- TCP 22 from 0.0.0.0/0
- TCP 80 from 0.0.0.0/0

Outbound
- All traffic
```

Security Group의 중요한 특징은 다음과 같다.

### 상태 저장(Stateful)

허용된 요청에 대한 응답 트래픽은 자동 허용됨.

예를 들어 SSH 22 인바운드를 허용했다면,

응답 패킷은 별도로 아웃바운드 규칙을 복잡하게 만들지 않아도 돌아갈 수 있음.

### 허용 규칙만 존재

Security Group은 기본적으로 **Allow only** 방식이다.

즉 차단 규칙을 명시하는 것이 아니라, 허용한 것만 통과시킴.

### 리소스 단위 적용

서브넷 전체가 아니라 EC2 같은 리소스에 직접 연결됨.

```
Security Group은 서버 앞에 붙는 개별 방화벽이다.
```

---

## 3.11 NACL과 Security Group의 차이

### NACL

* 서브넷 단위 적용

* Stateless

* Allow / Deny 가능

### Security Group

* 인스턴스 단위 적용

* Stateful

* Allow only

```
NACL은 서브넷 경계 방화벽
Security Group은 서버 단위 방화벽
```

---

## 3.12 AWS 네트워크 기본 구성 예시

가장 기본적인 구조는 다음과 같음.

```
VPC 10.0.0.0/16
 ├ Public Subnet  10.0.1.0/24
 │   └ EC2 Web Server
 │
 └ Private Subnet 10.0.2.0/24
     └ EC2 App Server
```

Public Subnet의 Route Table에 Internet Gateway를 붙이면

* Public Subnet의 웹 서버는 인터넷과 연결 가능

* Private Subnet의 앱 서버는 외부에서 직접 접근 불가

이런 구조를 만들 수 있음.

이게 AWS 3-Tier Architecture의 시작점이 됨.

---

## 3.13 왜 네트워크를 이렇게 복잡하게 나누는가

```
한 서브넷에 다 넣으면 안 되나?
```

예를 들어 웹 서버, 앱 서버, DB 서버를 모두 같은 네트워크에 두면

* 외부 노출 범위가 커짐

* 보안 정책 분리가 어려움

* 장애 영향 범위가 커짐

* 관리가 어려워짐

반대로 분리하면 다음 장점이 있음.

* 웹 서버만 공개 가능

* 앱 서버는 내부 통신만 허용 가능

* DB는 특정 서버만 접근 가능

* 계층별 보안 정책 설정 가능

즉 네트워크 분리는 단순한 기술이 아니라 **보안과 운영을 위한 아키텍처 설계 기법**이다.

---