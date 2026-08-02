---
title: "5장 AWS 컴퓨팅 서비스"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 클라우드 기술 기초(TESS)"]
is_public: true
draft: false
---

# 5장 AWS 컴퓨팅 서비스

## 5.1 컴퓨팅 서비스란 무엇인가

컴퓨팅 서비스는 **애플리케이션을 실행하기 위한 서버 자원을 제공하는 서비스**이다.

온프레미스 환경에서는 기업이 직접 서버를 구매하고 설치해야 했음.

예

```
물리 서버 구매
→ 데이터센터 설치
→ OS 설치
→ 애플리케이션 설치
```

이 과정은 많은 시간과 비용이 필요했음.

AWS에서는 이러한 서버를 **가상 서버 형태로 제공**한다.

즉 AWS에서는 다음과 같이 서버를 생성할 수 있다.

```
AWS Console
 → EC2 생성
 → 몇 분 후 서버 사용 가능
```

이처럼 클라우드는 **컴퓨팅 자원을 빠르게 제공하는 것이 특징**이다.

---

# 5.2 Amazon EC2

EC2는 **Elastic Compute Cloud**의 약자이다.

EC2는 AWS에서 제공하는 **가상 서버 서비스**이다.

즉 물리 서버를 직접 구매하지 않고도 AWS에서 서버를 사용할 수 있음.

예

```
Linux Server
Windows Server
Application Server
```

모두 EC2로 생성할 수 있다.

EC2의 주요 특징

```
가상 서버 제공
다양한 인스턴스 타입 제공
빠른 생성
Auto Scaling 가능
```

---

# 5.3 EC2 동작 원리

EC2는 AWS 데이터센터의 **물리 서버 위에서 가상화 기술을 통해 실행된다**.

구조

```
Physical Server
   │
Hypervisor
   │
EC2 Instance
```

하이퍼바이저(Hypervisor)는 하나의 물리 서버를 여러 가상 서버로 나누는 역할을 한다.

즉 하나의 물리 서버 위에서 여러 EC2 인스턴스가 실행될 수 있음.

이 구조 덕분에 AWS는 다음 특징을 제공할 수 있다.

```
빠른 서버 생성
유연한 확장
자원 효율성
```

---

# 5.4 EC2 구성 요소

EC2를 생성할 때 다음 요소를 설정한다.

```
AMI
Instance Type
Storage
Key Pair
Security Group
Network
```

각 구성 요소는 EC2 서버의 동작에 중요한 역할을 한다.

---

# 5.5 AMI (Amazon Machine Image)

AMI는 EC2 인스턴스를 생성할 때 사용하는 **서버 이미지**이다.

쉽게 말하면 AMI는 **서버 템플릿**이다.

AMI에는 다음 정보가 포함된다.

```
운영체제
기본 소프트웨어
시스템 설정
```

예

```
Amazon Linux
Ubuntu
RedHat
Windows Server
```

EC2를 생성하면 AWS는 해당 AMI를 기반으로 서버를 시작한다.

즉

```
AMI → EC2 생성
```

구조이다.

---

# 5.6 Instance Type

Instance Type은 **EC2의 CPU, Memory 성능을 결정하는 요소**이다.

AWS는 다양한 종류의 인스턴스를 제공한다.

예

```
t3.micro
t3.small
m5.large
c5.xlarge
```

각 인스턴스는 다음 기준으로 구분된다.

```
CPU 성능
Memory 크기
Network 성능
Storage 성능
```

예를 들어

```
t3.micro
```

는 작은 테스트 서버에 적합하고

```
m5.large
```

는 중간 규모 애플리케이션 서버에 적합하다.

<https://docs.aws.amazon.com/ko_kr/ec2/latest/instancetypes/instance-type-names>

---

# 5.7 Key Pair

Key Pair는 **EC2 서버에 접속하기 위한 인증 키**이다.

Linux 서버는 보통 다음 방식으로 접속한다.

```
SSH
```

EC2는 비밀번호 대신 **SSH Key 기반 인증**을 사용한다.

구성

```
Public Key
Private Key
```

Public Key는 EC2 서버에 저장되고

Private Key는 사용자가 보관한다.

접속 예

```
ssh -i mykey.pem ubuntu@EC2_IP
```

---

# 5.8 Security Group

Security Group은 EC2 인스턴스를 보호하는 **가상 방화벽**이다.

Security Group은 다음 트래픽을 제어한다.

```
Inbound Traffic
Outbound Traffic
```

예

```
Inbound
22   SSH
80   HTTP
443  HTTPS
```

만약 HTTP 포트를 허용하지 않으면

```
웹 서버 접속 불가
```

즉 Security Group은 **서버 접근을 제어하는 중요한 보안 요소**이다.

---

# 5.9 EC2 Storage

EC2는 데이터를 저장하기 위해 **EBS 스토리지**를 사용한다.

EBS는 **Elastic Block Store**의 약자이다. EBS는 EC2에 연결되는 **가상 디스크**이다.

구조

```
EC2 Instance
 │
EBS Volume
```

특징

```
Persistent Storage
High Performance
Snapshot 지원
```

즉 EC2 인스턴스가 종료되더라도 EBS 데이터는 유지될 수 있다.

---

# 5.10 EC2 Life Cycle

EC2 인스턴스는 다음 상태를 가진다.

```
Pending
Running
Stopping
Stopped
Terminated
```

각 상태 의미

```
Pending     → 서버 생성 중
Running     → 서버 실행 중
Stopped     → 서버 중지
Terminated  → 서버 삭제
```

중요한 특징

```
Stopped 상태에서는 컴퓨팅 비용 없음
```

즉 필요하지 않을 때 서버를 중지하면 비용을 절약할 수 있다.

---

# 5.11 Auto Scaling

Auto Scaling은 **트래픽에 따라 EC2 인스턴스를 자동으로 확장하거나 축소하는 기능**이다.

예

```
평소 트래픽
→ EC2 2대
```

사용자가 증가하면

```
EC2 10대
```

로 자동 확장할 수 있다.

구조

```
Load Balancer
   │
Auto Scaling Group
   │
EC2 Instances
```

Auto Scaling의 장점

```
자동 확장
자동 복구
비용 절감
```

---

# 요약

AWS에서 가장 기본적인 컴퓨팅 서비스는 **EC2**이다.

EC2는 **가상 서버 서비스**이다.

EC2 구성 요소

```
AMI
Instance Type
Key Pair
Security Group
Storage
Network
```

확장 기능

```
Auto Scaling
Load Balancer
```