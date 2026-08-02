---
title: "7장 기본 AWS 아키텍처"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 클라우드 기술 기초(TESS)"]
is_public: true
draft: false
---

# 7장 기본 AWS 아키텍처

## 7.1 웹 서비스 아키텍처의 기본 개념

대부분의 웹 서비스는 사용자 요청을 처리하는 서버와 데이터를 저장하는 저장소로 구성된다.

가장 단순한 형태는 다음과 같다.

```
User
 │
Internet
 │
Web Server
 │
Database
```

이 구조에서 Web Server는 사용자의 요청을 받아 화면을 제공하거나 애플리케이션 로직을 수행한다.

Database는 회원 정보, 게시글, 주문 정보, 설정 정보와 같은 데이터를 저장한다.

이 구조는 웹 서비스의 기본 원리를 이해하기에는 적절하지만, 실제 운영 환경에서는 여러 한계가 존재한다.

대표적인 문제는 다음과 같다.

```
단일 서버 장애 시 전체 서비스 중단
사용자 증가 시 성능 저하
서버 역할 분리가 부족함
보안 구성이 단순함
확장 구조가 비효율적임
```

실제 서비스 환경에서는 트래픽 증가, 장애 대응, 데이터 보호, 운영 효율성을 고려해야 하므로

서버 역할을 분리하고 네트워크를 나누는 방식으로 아키텍처를 설계한다.

AWS에서는 이러한 요구를 반영하여

VPC, Subnet, Load Balancer, Auto Scaling, RDS, S3 등의 서비스를 조합해

확장 가능하고 안정적인 웹 서비스 구조를 만든다.

---

## 7.2 기본 AWS 웹 아키텍처

AWS에서 웹 서비스를 구성할 때의 기본 구조는 다음과 같다.

```
User
 │
Internet
 │
Internet Gateway
 │
Public Subnet
 │
Load Balancer / Web Tier
 │
Private Subnet
 │
Application Tier / Database Tier
```

이 구조의 핵심은 네트워크를 외부 공개 영역과 내부 보호 영역으로 나누는 데 있다.

중요한 구성 요소는 다음과 같다.

```
VPC
Internet Gateway
Public Subnet
Private Subnet
Load Balancer
EC2
Database
```

각 요소의 역할은 다음과 같다.

### VPC

VPC는 AWS 안에 만드는 논리적인 사설 네트워크이다.

웹 서버, 애플리케이션 서버, 데이터베이스를 원하는 네트워크 구조 안에 배치할 수 있다.

### Internet Gateway

Internet Gateway는 VPC가 인터넷과 통신할 수 있도록 해주는 구성 요소이다.

인터넷에서 접근해야 하는 리소스는 이 경로를 통해 외부와 연결된다.

### Public Subnet

Public Subnet은 인터넷과 연결 가능한 서브넷이다.

보통 외부 요청을 받는 Load Balancer, NAT Gateway, Bastion Host 등이 여기에 위치한다.

### Private Subnet

Private Subnet은 인터넷에서 직접 접근할 수 없는 서브넷이다.

애플리케이션 서버, 데이터베이스, 내부 API, 캐시 서버와 같은 자원을 배치한다.

AWS 아키텍처의 기본 방향은 다음과 같다.

```
외부에서 접근해야 하는 자원만 Public에 배치
내부 처리 자원은 Private에 배치
데이터 저장 계층은 외부에 직접 노출하지 않음
```

---

## 7.3 Public Tier

Public Tier는 인터넷과 직접 연결되는 계층이다.

외부 요청을 처음 받아들이는 진입 지점 역할을 한다.

이 계층에는 다음과 같은 리소스가 주로 위치한다.

```
Application Load Balancer
Network Load Balancer
Bastion Host
NAT Gateway
Public Web Server
```

구조는 다음과 같이 표현할 수 있다.

```
Internet
 │
Internet Gateway
 │
Public Subnet
 │
Public Tier Resources
```

Public Tier의 특징은 다음과 같다.

```
인터넷과 직접 통신 가능
외부 요청 수신
내부 계층으로 요청 전달
보안 그룹과 라우팅 설정 중요
최소한의 자원만 공개
```

예를 들어 Application Load Balancer는

외부 사용자로부터 HTTP 또는 HTTPS 요청을 받아 내부 서버로 전달하므로

일반적으로 Public Subnet에 배치한다.

반면 Database처럼 외부에 직접 공개할 필요가 없는 자원은 Public Tier에 두지 않는다.

---

## 7.4 Private Tier

Private Tier는 인터넷에서 직접 접근할 수 없는 계층이다.

서비스의 핵심 로직과 데이터 처리가 이루어지는 영역이다.

이 계층에는 다음과 같은 리소스가 위치한다.

```
Application Server
Database
Internal API
Backend Service
Cache
Message Processing Service
```

구조는 다음과 같다.

```
Public Tier
 │
Private Subnet
 │
Application Server
 │
Database
```

Private Tier의 특징은 다음과 같다.

```
외부 직접 접근 불가
내부 서비스 처리
민감한 데이터 저장 가능
보안 강화에 유리
접근 경로를 제한 가능
```

사용자의 요청은 먼저 Public Tier를 거친 뒤

필요에 따라 Private Tier의 애플리케이션 서버로 전달된다.

애플리케이션 서버는 비즈니스 로직을 수행한 뒤 데이터베이스에 접근한다.

이 구조를 사용하면 데이터베이스나 내부 서버가 인터넷에 직접 노출되지 않으므로

보안성이 크게 향상된다.

---

## 7.5 3-Tier Architecture

AWS에서 가장 대표적으로 사용하는 웹 서비스 구조는 3-Tier Architecture이다.

3-Tier Architecture는 시스템을 다음 세 계층으로 나누는 방식이다.

```
Presentation Tier
Application Tier
Database Tier
```

웹 서비스 구조로 표현하면 다음과 같다.

```
User
 │
Load Balancer
 │
Web Tier
 │
Application Tier
 │
Database Tier
```

각 계층의 역할은 다음과 같다.

### Web Tier

사용자 요청을 수신하고 화면을 제공하거나

요청을 애플리케이션 계층으로 전달하는 역할을 한다.

### Application Tier

비즈니스 로직을 수행한다.

회원가입, 로그인, 주문 처리, API 실행, 권한 검사와 같은 핵심 처리가 이 계층에서 수행된다.

### Database Tier

서비스 데이터를 저장한다.

관계형 데이터, 키-값 데이터, 캐시 데이터 등이 이 계층에 포함된다.

AWS에서 3-Tier 구조를 적용하면 다음과 같이 정리할 수 있다.

```
User
 │
Internet
 │
Application Load Balancer
 │
Public Subnet
 │
Web Tier
 │
Private Subnet
 │
Application Tier
 │
Database Tier
```

이 구조의 장점은 다음과 같다.

```
역할 분리 가능
계층별 보안 정책 적용 가능
필요한 계층만 개별 확장 가능
장애 영향 범위 축소
운영 구조 명확화
```

예를 들어 웹 요청이 많아지면 Web Tier를 늘릴 수 있고,

비즈니스 로직 처리량이 증가하면 Application Tier 중심으로 확장할 수 있다.

---

## 7.6 Load Balancer

Load Balancer는 여러 서버에 트래픽을 분산하는 구성 요소이다.

사용자는 하나의 접점으로 접속하고, Load Balancer가 요청을 여러 서버로 나누어 전달한다.

구조는 다음과 같다.

```
User
 │
Load Balancer
 │
 ├─ EC2
 ├─ EC2
 └─ EC2
```

Load Balancer의 주요 기능은 다음과 같다.

```
트래픽 분산
고가용성 향상
장애 서버 제외
확장 구조 단순화
하나의 진입점 제공
```

AWS에서는 Elastic Load Balancing 서비스를 사용하며, 대표적으로 다음 두 종류를 자주 사용한다.

```
Application Load Balancer
Network Load Balancer
```

### Application Load Balancer

ALB는 HTTP, HTTPS 기반 웹 서비스에 적합하다.

경로 기반 라우팅, 호스트 기반 라우팅, SSL 종료 같은 기능을 제공한다.

예를 들면 다음과 같이 요청을 분기할 수 있다.

```
/api      → API Server
/admin    → Admin Server
/images   → Static Service
```

### Network Load Balancer

NLB는 TCP, UDP 기반 고성능 네트워크 처리에 적합하다.

지연 시간이 낮고 대량의 네트워크 트래픽을 빠르게 처리할 수 있다.

웹 서비스 기초 학습 단계에서는 ALB를 먼저 이해하는 것이 일반적이다.

---

## 7.7 Auto Scaling

Auto Scaling은 서버 수를 자동으로 조절하는 기능이다.

트래픽이 증가하면 인스턴스를 자동으로 추가하고, 트래픽이 감소하면 인스턴스를 자동으로 줄인다.

구조는 다음과 같다.

```
Load Balancer
 │
Auto Scaling Group
 │
EC2 Instances
```

기본 개념은 다음과 같다.

### Auto Scaling Group

동일한 역할을 수행하는 EC2 집합을 관리한다.

최소 인스턴스 수, 최대 인스턴스 수, 원하는 인스턴스 수를 지정할 수 있다.

### Scaling Policy

언제 인스턴스를 늘리거나 줄일지 결정하는 정책이다.

예를 들어 CPU 사용률이 70%를 초과하면 인스턴스를 추가하도록 설정할 수 있다.

예시는 다음과 같다.

```
평상시
EC2 2대 운영

트래픽 증가
EC2 4대 또는 6대로 자동 확장
```

Auto Scaling의 장점은 다음과 같다.

```
자동 확장
자동 축소
장애 인스턴스 자동 교체
비용 최적화
운영 자동화
```

Auto Scaling은 단순히 서버 수를 늘리는 기능만이 아니라

비정상 인스턴스를 감지하고 새 인스턴스로 교체하여 서비스 상태를 유지하는 역할도 한다.

---

## 7.8 정적 콘텐츠 처리

웹 서비스에는 다양한 정적 파일이 존재한다.

```
이미지
CSS
JavaScript
동영상
폰트 파일
문서 파일
다운로드 파일
```

이러한 파일을 모두 웹 서버가 직접 제공하면

웹 서버는 동적 요청 처리와 파일 전송을 동시에 수행해야 하므로 부담이 커질 수 있다.

AWS에서는 정적 파일을 Amazon S3에 저장하고,

웹 서비스와 분리하여 제공하는 구조를 자주 사용한다.

구조는 다음과 같다.

```
           ┌────────────→ Web Server
User ──────┤
           └────────────→ S3 (Static Files)
```

동작 과정은 다음과 같다.

```
1. 사용자가 웹 서비스에 접속한다.
2. Web Server 또는 Application이 HTML 응답을 제공한다.
3. HTML 안에는 이미지, CSS, JavaScript 파일 경로가 포함된다.
4. 브라우저는 필요한 정적 파일을 S3에서 가져온다.
```

이 구조의 장점은 다음과 같다.

```
웹 서버 부하 감소
정적 파일 저장에 적합
대용량 파일 처리에 유리
높은 확장성 제공
비용 효율적
```

실무에서는 S3 앞단에 CloudFront를 두는 경우가 많다.

```
           ┌────────────→ Load Balancer → Web / App Server
User ──────┤
           └────────────→ CloudFront → S3
```

이 구조를 사용하면 정적 콘텐츠를 엣지 로케이션에 캐싱할 수 있으므로

응답 속도가 향상되고 원본 저장소에 대한 요청도 줄어든다.

---

## 7.9 기본 AWS 아키텍처 예시

지금까지의 내용을 종합하면 AWS의 기본 웹 서비스 아키텍처는 다음과 같이 정리할 수 있다.

```
User
 │
Internet
 │
Application Load Balancer
 │
Public Subnet
 │
Web Tier
 │
Private Subnet
 │
Application Tier
 │
Database Tier
```

정적 콘텐츠 처리까지 포함하면 다음과 같다.

```
           ┌────────────→ Application Load Balancer → Web Tier → Application Tier → Database Tier
User ──────┤
           └────────────→ S3 (Static Files)
```

CloudFront를 포함한 형태는 다음과 같다.

```
           ┌────────────→ Application Load Balancer → Web Tier → Application Tier → Database Tier
User ──────┤
           └────────────→ CloudFront → S3
```

각 구성 요소의 역할은 다음과 같다.

```
Application Load Balancer  : 사용자 요청 분산
Web Tier                   : 요청 수신, 화면 제공, 전달 처리
Application Tier           : 비즈니스 로직 수행
Database Tier              : 데이터 저장
S3                         : 정적 콘텐츠 저장
CloudFront                 : 정적 콘텐츠 캐싱 및 전송 최적화
Auto Scaling               : 서버 자동 확장 및 복구
```

이 구조를 통해 다음과 같은 목표를 달성할 수 있다.

```
확장성
고가용성
보안성
운영 효율성
비용 최적화
```

---

## 요약

AWS의 기본 웹 서비스 아키텍처는 일반적으로 다음과 같이 구성된다.

```
Internet
 │
Load Balancer
 │
Web Tier
 │
Application Tier
 │
Database Tier
```

정적 콘텐츠는 다음과 같은 별도 경로로 처리한다.

```
S3
또는
CloudFront + S3
```

이 구조를 사용하면 다음과 같은 효과를 얻을 수 있다.

```
확장성 향상
가용성 향상
보안 강화
운영 자동화
비용 효율화
```

웹 서비스 아키텍처를 설계할 때는

외부 공개 영역과 내부 보호 영역을 구분하고,

정적 요청과 동적 요청의 처리 경로를 분리하며,

확장과 장애 대응이 가능한 구조로 설계하는 것이 중요하다.

---