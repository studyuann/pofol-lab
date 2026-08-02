---
title: "VPC Interface Endpoint 기반 SSM Session Manager 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 클라우드 기술 기초(TESS)"]
is_public: true
draft: false
---

# VPC Interface Endpoint 기반 SSM Session Manager 실습

---

# 1. 실습 목표

[![](VPC%20Interface%20Endpoint%20%EA%B8%B0%EB%B0%98%20SSM%20Session%20Manager%20%EC%8B%A4%EC%8A%B5/image.png)](VPC%20Interface%20Endpoint%20%EA%B8%B0%EB%B0%98%20SSM%20Session%20Manager%20%EC%8B%A4%EC%8A%B5/image.png)

Private Subnet에 위치한 EC2 인스턴스를 **SSH 없이 Systems Manager(Session Manager)를 통해 접속**할 수 있도록 구성한다.

이를 위해 다음 기술을 활용한다.

```
Interface Endpoint (PrivateLink)
Systems Manager
Session Manager
```

즉 다음 구조를 구현한다.

```
관리자
   │
   │ AWS Console / CLI
   │
Systems Manager
   │
   │ WebSocket
   │
VPC Interface Endpoint
(ssm / ec2messages / ssmmessages)
   │
   │ HTTPS 443
   │
Private Subnet EC2
```

이 구조를 통해 다음이 가능해진다.

```
SSH 필요 없음
Bastion Host 필요 없음
Internet Gateway 필요 없음
NAT Gateway 필요 없음
```

---

# 2. Interface Endpoint 개념

Interface Endpoint는 **AWS PrivateLink 기반 서비스 연결 방식**이다.

VPC 내부에 **ENI(Elastic Network Interface)** 를 생성하여 AWS 서비스와 **사설 IP로 통신**하도록 한다.

즉 AWS 서비스 접근 방식이 다음과 같이 변경된다.

### 기존 방식

```
EC2
  │
Internet Gateway / NAT Gateway
  │
AWS Service
```

### Interface Endpoint 방식

```
EC2
  │
Interface Endpoint (ENI)
  │
PrivateLink
  │
AWS Service
```

즉 **AWS 서비스 접근이 Private Network 내부에서 처리된다.**

---

# 3. Interface Endpoint 구성 요소

Interface Endpoint 생성 시 다음 리소스가 함께 생성된다.

```
Endpoint 리소스
Elastic Network Interface (ENI)
Security Group
Private DNS
```

예시

```
Endpoint ENI IP

172.31.47.152
```

즉 VPC 내부에서는 AWS 서비스가 **사설 IP로 보이게 된다.**

---

# 4. Private DNS 동작

Interface Endpoint에서 **Private DNS 활성화**를 설정하면

AWS 서비스 도메인이 Endpoint IP로 변환된다.

예

```
ssm.ap-northeast-2.amazonaws.com
```

EC2에서 DNS 조회

```
dig ssm.ap-northeast-2.amazonaws.com
```

결과

```
172.31.x.x
```

즉 DNS 동작은 다음과 같다.

```
Public DNS
      ↓
VPC Private DNS Override
      ↓
Endpoint ENI IP
```

따라서 애플리케이션은 **도메인을 그대로 사용하면서 Private 통신이 가능하다.**

---

# 5. SSM Endpoint 구성

Systems Manager 사용 시 다음 **3개의 Endpoint가 필요하다.**

```
com.amazonaws.ap-northeast-2.ssm
com.amazonaws.ap-northeast-2.ec2messages
com.amazonaws.ap-northeast-2.ssmmessages
```

각 역할

| Endpoint | 역할 |
| --- | --- |
| ssm | SSM API |
| ec2messages | Agent 메시지 통신 |
| ssmmessages | Session Manager WebSocket |

---

# 6. SSM Session Manager 동작

Session Manager는 **WebSocket 기반 통신**을 사용한다.

통신 흐름

```
EC2 SSM Agent
      │
      │ HTTPS 443
      │
ssmmessages Endpoint
      │
      │ WebSocket
      │
Systems Manager
```

SSM Agent 로그에서 다음 메시지가 확인되면 정상 연결이다.

```
Successfully opened websocket connection
Set up control channel successfully
```

---

# 7. EC2 IAM Role 설정

EC2에는 다음 정책이 필요하다.

```
AmazonSSMManagedInstanceCore
```

이 정책은 SSM Agent가 AWS Systems Manager와 통신하도록 허용한다.

주요 권한

```
ssm:UpdateInstanceInformation
ssmmessages:CreateControlChannel
ssmmessages:OpenDataChannel
ec2messages:GetMessages
```

즉 **Agent 통신 권한이다.**

---

# 8. CLI 조회 권한

다음 명령 실행 시

```
aws ssm describe-instance-information
```

다음 권한이 필요하다.

```
ssm:DescribeInstanceInformation
```

따라서 다음 정책이 추가로 필요할 수 있다.

```
AmazonSSMReadOnlyAccess
```

중요한 개념

```
EC2 Role (Agent 권한)
≠
관리자 CLI 조회 권한
```

---

# 9. SSM 연결 확인 방법

### 1 DNS 확인

```
dig ssm.ap-northeast-2.amazonaws.com
```

결과

```
172.31.x.x
```

이면 Private DNS 정상.

---

### 2 Endpoint 네트워크 확인

```
nc -vz ssm.ap-northeast-2.amazonaws.com 443
```

성공하면 Endpoint 연결 정상.

---

### 3 IAM Role 확인

```
aws sts get-caller-identity
```

결과 예시

```
assumed-role/kyt-ssm-role
```

---

### 4 Agent 로그 확인

```
sudo tail -f /var/log/amazon/ssm/amazon-ssm-agent.log
```

정상 메시지

```
Successfully opened websocket connection
Set up control channel successfully
```

---

# 10. Fleet Manager 확인

다음 경로에서 EC2 등록 여부 확인

```
Systems Manager
→ Fleet Manager
```

또는

```
Systems Manager
→ Managed nodes
```

인스턴스가 표시되면 **SSM 등록 성공**이다.

---

# 11. Session Manager 접속 테스트

다음 메뉴에서 접속 테스트 수행

```
Systems Manager
→ Session Manager
→ Start session
```

정상 연결 시 **SSH 없이 EC2 터미널 접속 가능**하다.

---

# 12. 실습 핵심 개념

이번 실습의 핵심은 다음이다.

```
Private Subnet 서버 관리
```

즉 다음 구조를 구현한다.

```
Private Subnet EC2
       │
       │ VPC Endpoint
       │
Systems Manager
       │
Session Manager
```

이를 통해

```
SSH 접속 불필요
Bastion Host 불필요
```

구성이 가능하다.

---

# 13. 한 줄 정리

```
Interface Endpoint는 AWS 서비스를 VPC 내부 사설 IP로 접근하도록 만드는 PrivateLink 기반 네트워크 구성이며, SSM Session Manager는 이를 이용하여 Private Subnet EC2를 SSH 없이 관리할 수 있게 한다.
```