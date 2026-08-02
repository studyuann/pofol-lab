---
title: "4장 AWS 네트워크 흐름"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 클라우드 기술 기초(TESS)"]
is_public: true
draft: false
---

# 4장 AWS 네트워크 흐름

## 4.1 AWS 네트워크 흐름을 이해해야 하는 이유

AWS에서 네트워크 문제의 대부분은 **구성요소가 없어서 발생하는 것이 아니라 흐름을 이해하지 못해서 발생**한다.

예를 들어 다음 질문이 자주 나온다.

```
EC2에 접속이 안됩니다
Public Subnet인데 인터넷이 안됩니다
apt update가 안 됩니다
```

이 문제들은 대부분 다음 중 하나 때문이다.

* Route Table 설정 오류

* Internet Gateway 연결 문제

* Security Group 설정 문제

* Public IP 문제

즉 AWS 네트워크를 이해하려면 단순히 구성요소 이름을 아는 것이 아니라

```
패킷이 어떤 경로를 통해 이동하는지
```

를 이해해야 한다.

---

# 4.2 외부 사용자 → EC2 접속 흐름

가장 기본적인 네트워크 흐름은 **외부 사용자가 EC2에 접속하는 경우**이다.

예를 들어 웹 서버에 접속하는 상황을 생각해보자.

구조

```
User
 │
Internet
 │
Internet Gateway
 │
VPC
 │
Public Subnet
 │
EC2
```

실제 패킷 흐름은 다음과 같다.

```
User
 │
Internet
 │
Public IP
 │
Internet Gateway
 │
Route Table
 │
Public Subnet
 │
EC2
```

즉 외부에서 EC2로 접속하려면 다음 조건이 필요하다.

---

### 조건 1 : Public IP

EC2는 기본적으로 Private IP를 가진다.

예

```
10.0.1.10
```

하지만 외부 인터넷에서 접속하려면 Public IP가 필요하다.

예

```
3.34.120.10
```

즉 외부 사용자는 Public IP를 통해 EC2에 접속한다.

---

### 조건 2 : Internet Gateway

VPC는 기본적으로 외부 인터넷과 연결되어 있지 않다.

따라서 Internet Gateway가 있어야 한다.

구조

```
Internet
 │
Internet Gateway
 │
VPC
```

Internet Gateway는 VPC와 인터넷 사이의 **출입구 역할**을 한다.

---

### 조건 3 : Route Table

Route Table에는 다음 경로가 있어야 한다.

```
0.0.0.0/0 → Internet Gateway
```

의미

```
모든 외부 트래픽은 IGW로 전달
```

이 경로가 있어야 Public Subnet이 된다.

---

### 조건 4 : Security Group

Security Group이 해당 포트를 허용해야 한다.

예

```
Inbound
TCP 22  SSH
TCP 80  HTTP
TCP 443 HTTPS
```

허용되지 않은 포트는 접속할 수 없다.

---

# 4.3 EC2 → Internet 흐름

이번에는 EC2가 외부 인터넷으로 접속하는 경우를 보자.

예

```
apt update
yum update
wget
```

이 경우 패킷 흐름은 다음과 같다.

```
EC2
 │
Subnet
 │
Route Table
 │
Internet Gateway
 │
Internet
```

하지만 여기에도 조건이 있다.

---

### Public IP 필요

EC2가 Internet Gateway를 통해 외부로 나가려면 Public IP가 필요하다.

즉 다음 구조가 되어야 한다.

```
Public Subnet
 │
EC2 (Public IP)
 │
IGW
 │
Internet
```

Public IP가 없다면 외부 인터넷으로 직접 나갈 수 없다.

---

# 4.4 Private Subnet 구조

AWS 아키텍처에서 대부분의 서버는 **Private Subnet에 배치된다**.

예

```
Application Server
Database
Internal Service
```

구조

```
VPC
 ├ Public Subnet
 │   └ Load Balancer
 │
 └ Private Subnet
     └ Application Server
```

Private Subnet의 특징

```
Internet Gateway로 직접 나가지 않음
외부에서 직접 접근 불가
```

즉 보안이 필요한 서버는 Private Subnet에 배치한다.

---

# 4.5 Private EC2 → Internet

문제는 Private EC2도 인터넷에 나가야 하는 경우가 많다는 것이다.

예

```
패키지 업데이트
API 호출
외부 서비스 접근
```

하지만 Private Subnet에는 IGW 경로가 없다.

그래서 사용하는 것이 **NAT Gateway**이다.

---

# 4.6 NAT Gateway 역할

NAT Gateway는 Private 서버 대신 인터넷에 접속해주는 장비이다.

구조

```
Private EC2
 │
Private Subnet
 │
Route Table
 │
NAT Gateway
 │
Internet Gateway
 │
Internet
```

패킷 흐름

```
EC2
 │
NAT Gateway
 │
Internet
```

응답 흐름

```
Internet
 │
NAT Gateway
 │
EC2
```

즉 NAT Gateway는 **Private 서버의 IP를 대신 변환하여 인터넷과 통신한다**.

---

# 4.7 NAT Gateway 특징

NAT Gateway는 다음 특징을 가진다.

### Outbound Only

인터넷에서 Private EC2로 직접 접속할 수 없다.

```
Internet → NAT → EC2
```

이 흐름은 불가능하다.

즉 NAT Gateway는 **외부로 나가는 통신만 가능**하다.

---

### Public Subnet에 배치

NAT Gateway는 반드시 Public Subnet에 생성해야 한다.

구조

```
Public Subnet
 └ NAT Gateway
```

---

### Private Subnet에서 사용

Private Subnet의 Route Table에 다음 경로를 추가한다.

```
0.0.0.0/0 → NAT Gateway
```

이렇게 하면 Private EC2도 인터넷에 나갈 수 있다.

---

# 4.8 내부 서버 통신

같은 VPC 내부에서는 Private IP로 통신한다.

예

```
Web Server
10.0.1.10
```

```
DB Server
10.0.2.20
```

통신 흐름

```
Web Server
 │
VPC Network
 │
DB Server
```

이 통신은 Internet Gateway나 NAT Gateway를 거치지 않는다.

즉 VPC 내부 통신은 **AWS 내부 네트워크를 통해 직접 연결된다**.

---

# 4.9 AWS 기본 네트워크 구조

지금까지 설명한 내용을 합치면 다음 구조가 된다.

```
Internet
 │
Internet Gateway
 │
Public Subnet
 │
Load Balancer
 │
Private Subnet
 │
Application Server
 │
Database
```

그리고 Private Subnet에는 NAT Gateway 경로가 존재한다.

```
Private Subnet
 │
NAT Gateway
 │
Internet
```

이 구조가 **AWS 웹 서비스 아키텍처의 기본 형태**이다.

---

# 요약

AWS 네트워크 흐름을 이해하려면 다음 세 가지를 기억하면 된다.

---

### 외부 → Public EC2

```
User
 → Internet
 → Internet Gateway
 → Route Table
 → Subnet
 → EC2
```

---

### Public EC2 → Internet

```
EC2
 → Route Table
 → Internet Gateway
 → Internet
```

---

### Private EC2 → Internet

```
EC2
 → NAT Gateway
 → Internet Gateway
 → Internet
```

---