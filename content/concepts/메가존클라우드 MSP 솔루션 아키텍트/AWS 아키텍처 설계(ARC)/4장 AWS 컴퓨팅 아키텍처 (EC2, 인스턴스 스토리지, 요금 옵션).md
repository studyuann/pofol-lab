---
title: "4장 AWS 컴퓨팅 아키텍처 (EC2, 인스턴스 스토리지, 요금 옵션)"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 아키텍처 설계(ARC)"]
is_public: true
draft: false
---

# 4장 AWS 컴퓨팅 아키텍처 (EC2, 인스턴스 스토리지, 요금 옵션)

---

# 4.1 컴퓨팅 서비스 개요

AWS에서 컴퓨팅 서비스는 애플리케이션을 실제로 실행하는 역할을 담당함.

사용자가 웹 브라우저로 접속하거나, API를 호출하거나, 데이터 처리를 요청하면 결국 어딘가에서 연산이 수행되어야 하는데, 그 연산을 담당하는 계층이 컴퓨팅 계층임.

AWS의 대표적인 컴퓨팅 서비스

| 서비스 | 설명 |
| --- | --- |
| EC2 | 가상 서버 |
| Lambda | 서버리스 함수 실행 |
| ECS | 컨테이너 오케스트레이션 |
| EKS | Kubernetes 관리형 서비스 |
| Elastic Beanstalk | 애플리케이션 배포 자동화 |

이 장에서는 그중 가장 기본이 되는 **Amazon EC2**를 중심으로 학습함.

---

# 4.2 Amazon EC2 개요

Amazon EC2는 **Elastic Compute Cloud**의 약자이며, AWS에서 제공하는 가상 서버 서비스임.

온프레미스에서 서버를 운영할 때는 다음과 같은 과정이 필요했음.

* 서버 장비 구매

* 랙 설치

* 전원 연결

* 네트워크 연결

* 운영체제 설치

* 보안 설정

* 장애 대응

AWS에서는 이러한 물리적 작업 없이 몇 번의 클릭 또는 명령어만으로 서버를 생성할 수 있음.

즉, EC2는 **필요한 만큼 빠르게 생성하고 제거할 수 있는 가상 컴퓨팅 자원**임.

EC2의 핵심 특징

* 몇 분 안에 서버 생성 가능

* 필요할 때만 사용 가능

* 다양한 CPU / 메모리 사양 선택 가능

* 보안 그룹, VPC와 연동 가능

* Auto Scaling 및 Load Balancer와 결합 가능

---

# 4.3 EC2의 주요 구성 요소

EC2 인스턴스를 생성할 때는 단순히 서버 이름만 정하는 것이 아니라 여러 요소를 함께 결정해야 함.

EC2 주요 구성 요소

* AMI

* Instance Type

* Key Pair

* VPC / Subnet

* Security Group

* Storage

* IAM Role

* User Data

---

## 4.3.1 AMI

AMI는 **Amazon Machine Image**의 약자임.

쉽게 말하면 EC2 인스턴스를 만들기 위한 **운영체제 템플릿**임.

예

* Amazon Linux

* Ubuntu

* Red Hat Enterprise Linux

* Windows Server

AMI에는 다음 정보가 포함될 수 있음.

* 운영체제

* 기본 패키지

* 초기 설정

* 애플리케이션 환경

즉, AMI는 “빈 서버를 어떤 모습으로 시작할 것인가”를 결정하는 이미지 파일이라고 보면 됨.

예를 들어

* Amazon Linux AMI 선택 → 리눅스 서버 생성

* Windows Server AMI 선택 → 윈도우 서버 생성

---

## 4.3.2 Instance Type

Instance Type은 EC2 인스턴스의 **하드웨어 사양**을 의미함.

여기에는 CPU, 메모리, 네트워크 성능 등이 포함됨.

예

* t3.micro

* t3.small

* m5.large

* c6i.large

* r6i.large

이 이름은 아무 의미 없이 붙은 것이 아니라 일정한 규칙이 있음.

예를 들어 `t3.micro`를 보면

* `t` : 인스턴스 패밀리

* `3` : 세대

* `micro` : 크기

즉, 인스턴스 타입은 “어떤 계열의 서버를 어느 정도 크기로 쓸 것인가”를 정하는 값임.

---

## 4.3.3 Key Pair

Key Pair는 Linux 인스턴스에 SSH로 접속할 때 사용하는 공개키 / 개인키 쌍임.

구성

* Public Key : AWS가 EC2 내부에 저장

* Private Key : 사용자가 보관

접속 예

```
ssh-i mykey.pem ec2-user@<Public-IP>
```

중요한 점

* `.pem` 파일은 재다운로드 불가능한 경우가 많음

* 분실하면 접속 복구가 번거로움

* 실습 환경에서는 학생별로 별도 키를 관리하는 것이 좋음

---

## 4.3.4 Security Group

Security Group은 인스턴스 수준의 가상 방화벽임.

예

* SSH 허용

* HTTP 허용

* HTTPS 허용

예시 규칙

| 방향 | 프로토콜 | 포트 | 소스 |
| --- | --- | --- | --- |
| Inbound | TCP | 22 | 내 IP |
| Inbound | TCP | 80 | 0.0.0.0/0 |
| Inbound | TCP | 443 | 0.0.0.0/0 |

Security Group은 **Stateful** 특성을 가짐.

즉, 들어오는 요청을 허용하면 그에 대한 응답은 별도 규칙 없이 허용됨.

---

## 4.3.5 User Data

User Data는 인스턴스가 **최초 부팅될 때 자동으로 실행할 스크립트**임.

예를 들어 웹 서버를 생성하면서 Apache를 자동 설치할 수 있음.

예시

```
#!/bin/bash
yum update-y
yum install-y httpd
systemctl enable httpd
systemctlstart httpd
echo"<h1>Hello EC2</h1>" > /var/www/html/index
```

이 스크립트를 넣고 EC2를 생성하면, 인스턴스가 부팅되면서 자동으로 웹 서버를 설치하고 시작함.

즉, User Data는 서버 초기 설정을 자동화하는 매우 중요한 기능임.

---

# 4.4 EC2 인스턴스 타입 분류

EC2 인스턴스는 용도에 따라 여러 패밀리로 나뉨.

---

## 4.4.1 범용 인스턴스 (General Purpose)

범용 인스턴스는 CPU와 메모리가 비교적 균형 있게 제공되는 타입임.

대표 예

* t3

* t4g

* m5

* m6i

주요 용도

* 일반 웹 서버

* 개발 서버

* 테스트 서버

* 중소 규모 애플리케이션 서버

특징

* 가장 많이 사용됨

* 실습 환경에서 적합함

* 성능과 비용의 균형이 좋음

---

## 4.4.2 컴퓨팅 최적화 인스턴스 (Compute Optimized)

CPU 성능이 중요한 워크로드에 적합함.

대표 예

* c5

* c6i

주요 용도

* 대규모 연산

* 게임 서버

* 배치 처리

* 고성능 웹 계층

---

## 4.4.3 메모리 최적화 인스턴스 (Memory Optimized)

메모리가 중요한 워크로드에 적합함.

대표 예

* r5

* r6i

주요 용도

* 대용량 캐시

* 인메모리 DB

* 분석 시스템

---

## 4.4.4 스토리지 최적화 인스턴스 (Storage Optimized)

디스크 I/O 성능이 중요한 환경에서 사용함.

대표 예

* i3

* i4i

주요 용도

* 고성능 데이터 처리

* 로컬 NVMe 저장이 중요한 경우

---

# 4.5 버스트 가능한 인스턴스

`t` 계열 인스턴스는 **버스트 가능한 인스턴스**임.

예

* t2.micro

* t3.micro

* t3.small

이 타입은 평소에는 낮은 CPU를 사용하다가, 필요할 때 일시적으로 CPU 성능을 높일 수 있음.

즉, 항상 높은 CPU가 필요한 서버가 아니라

* 실습용 서버

* 개발용 서버

* 소규모 웹 서버

같은 환경에 적합함.

교육 과정에서는 주로 `t3.micro` 또는 `t3.small`을 많이 사용함.

---

# 4.6 EC2 스토리지 개요

EC2는 서버 자체만으로 끝나지 않고, 스토리지와 함께 동작함.

AWS에서 EC2와 연결되는 대표적인 스토리지는 다음과 같음.

| 스토리지 | 설명 |
| --- | --- |
| EBS | 네트워크 기반 블록 스토리지 |
| Instance Store | 물리 서버에 직접 연결된 임시 스토리지 |
| EFS | 여러 인스턴스가 공유 가능한 파일 스토리지 |
| S3 | 객체 스토리지, EC2 외부 저장소 |

이 장에서는 EC2와 직접 관련이 깊은 **EBS와 Instance Store**를 중심으로 설명함.

---

# 4.7 EBS 개요

EBS는 **Elastic Block Store**의 약자임.

EC2에 연결해서 사용하는 블록 스토리지임.

온프레미스에서 말하면 서버에 연결된 디스크와 비슷한 개념이지만, 실제로는 AWS 내부 네트워크를 통해 연결되는 독립된 스토리지 서비스임.

EBS 특징

* EC2와 분리된 저장소

* 인스턴스를 종료해도 볼륨 유지 가능

* 스냅샷 생성 가능

* 성능 옵션 선택 가능

* 운영체제 디스크로 주로 사용

즉, EC2가 “컴퓨터 본체”라면 EBS는 “하드디스크” 역할을 함.

---

## 4.7.1 EBS 볼륨 유형

대표적인 EBS 유형

| 유형 | 설명 |
| --- | --- |
| gp3 | 범용 SSD, 가장 많이 사용 |
| gp2 | 이전 세대 범용 SSD |
| io1 / io2 | 고성능 IOPS 필요 시 |
| st1 | 처리량 중심 HDD |
| sc1 | 저비용 HDD |

실습용 / 일반 서버에서는 보통 `gp3`를 사용하면 됨.

---

## 4.7.2 EBS의 장점

* 인스턴스 중지 후 다시 시작해도 데이터 유지됨

* 스냅샷 생성으로 백업 가능

* 운영체제 루트 디스크로 사용 가능

---

# 4.8 Instance Store 개요

* 용량 증설 가능

Instance Store는 EC2가 실행되는 물리 호스트에 직접 연결된 로컬 디스크임.

특징

* 매우 빠름

* 임시 데이터 저장에 적합

* 인스턴스 중지 / 종료 시 데이터 유실 가능

* 영구 저장소로 부적합

즉, Instance Store는 빠르지만 **휘발성 저장소**라는 점이 핵심임.

주요 용도

* 캐시

* 임시 파일

* 버퍼 데이터

* 일시적 처리 데이터

---

## 4.8.1 EBS와 Instance Store 비교

| 항목 | EBS | Instance Store |
| --- | --- | --- |
| 저장 위치 | 네트워크 기반 | 물리 호스트 로컬 |
| 영속성 | 유지 가능 | 인스턴스 종료/중지 시 유실 가능 |
| 백업 | 스냅샷 가능 | 별도 백업 필요 |
| 용도 | 운영체제, 데이터 저장 | 캐시, 임시 데이터 |

---

# 4.9 EC2 네트워크와 IP 주소

EC2 인스턴스는 VPC 내부에서 실행되므로 네트워크 정보가 함께 부여됨.

주요 개념

* Private IP

* Public IP

* Elastic IP

---

## 4.9.1 Private IP

VPC 내부 통신용 IP 주소임.

같은 VPC 내 다른 인스턴스나 RDS와 통신할 때 사용함.

예

```
10.0.1.25
```

---

## 4.9.2 Public IP

인터넷과 통신하기 위한 IP 주소임.

Public Subnet에 인스턴스를 배치하고 Public IP를 할당하면 외부에서 접속 가능함.

주의

* 인스턴스 중지 후 시작 시 Public IP가 바뀔 수 있음

---

## 4.9.3 Elastic IP

고정 공인 IP 주소임.

AWS 계정에 할당해 두고 특정 인스턴스에 연결함.

용도

* 고정 IP 필요 시

* 외부 시스템에서 화이트리스트 등록이 필요한 경우

---

# 4.10 EC2 상태 변화

EC2는 여러 상태를 가짐.

| 상태 | 설명 |
| --- | --- |
| pending | 생성 중 |
| running | 실행 중 |
| stopping | 중지 중 |
| stopped | 중지됨 |
| shutting-down | 종료 중 |
| terminated | 종료됨 |

중요한 점

* `stopped` 상태는 디스크(EBS)는 유지되지만 서버는 꺼져 있음

* `terminated` 상태는 인스턴스가 삭제된 상태임

* 종료 시 EBS 삭제 옵션이 켜져 있으면 루트 볼륨도 함께 삭제될 수 있음

---

# 4.11 EC2 요금 옵션

EC2는 사양뿐 아니라 **구매 방식**도 중요함.

같은 인스턴스 타입이라도 어떤 요금 옵션을 선택하느냐에 따라 비용 구조가 달라짐.

대표적인 요금 옵션

* On-Demand

* Reserved Instances

* Savings Plans

* Spot Instances

* Dedicated Hosts / Dedicated Instances

---

## 4.11.1 On-Demand

가장 기본적인 과금 방식임.

필요할 때 생성하고 사용한 만큼 비용을 지불함.

특징

* 약정 없음

* 가장 유연함

* 단기 실습 및 테스트에 적합

* 장기 사용 시 상대적으로 비쌈

교육 환경에서는 가장 많이 사용하는 방식임.

---

## 4.11.2 Reserved Instances

1년 또는 3년 약정을 통해 비용을 절감하는 방식임.

특징

* 장기 운영에 적합

* 사용량이 일정한 서버에 유리

* On-Demand 대비 할인 가능

적합한 예

* 24시간 항상 실행되는 운영 웹 서버

* 고정적인 DB 서버

---

## 4.11.3 Savings Plans

일정 금액 또는 사용량을 약정해서 할인받는 방식임.

특징

* RI보다 유연한 경우가 많음

* EC2 외 일부 컴퓨팅 서비스까지 적용 가능

* 장기 운영에서 비용 절감 효과가 큼

---

## 4.11.4 Spot Instances

AWS의 남는 자원을 매우 저렴하게 사용하는 방식임.

특징

* 매우 저렴함

* AWS 사정에 따라 언제든 회수될 수 있음

* 중단 허용 가능한 작업에 적합

적합한 예

* 배치 처리

* 테스트 환경

* 렌더링 작업

* 비핵심 워크로드

부적합한 예

* 중요한 운영 DB

* 세션 유지가 중요한 단일 서버

---

## 4.11.5 요금 옵션 비교

| 옵션 | 장점 | 단점 | 적합한 환경 |
| --- | --- | --- | --- |
| On-Demand | 유연함 | 비용 높음 | 실습, 테스트 |
| Reserved | 할인 큼 | 약정 필요 | 장기 운영 |
| Savings Plans | 유연한 할인 | 약정 필요 | 장기 컴퓨팅 |
| Spot | 매우 저렴 | 중단 가능 | 배치, 일시 작업 |

---

# 4.12 EC2 운영 시 고려사항

EC2는 단순히 만들고 끝나는 서비스가 아님.

실제 운영에서는 다음 항목을 반드시 고려해야 함.

---

## 4.12.1 단일 EC2의 한계

한 대의 EC2만 운영하면 다음 문제가 있음.

* 장애 시 서비스 중단

* 확장 한계

* 수동 운영 필요

* 패치 관리 부담

따라서 실제 운영 환경에서는 보통 다음과 같이 구성함.

* 앞단에 ALB 배치

* Auto Scaling Group 구성

* 다중 AZ 배치

* RDS / ElastiCache 연계

즉, EC2는 독립적으로 보기보다 **아키텍처의 일부로 이해해야 함.**

---

## 4.12.2 보안 고려사항

* SSH는 필요한 IP만 허용

* 0.0.0.0/0으로 22번 포트 전면 개방 지양

* IAM Role 사용

* Access Key를 인스턴스에 직접 저장하지 않음

* OS 패치 수행

* CloudWatch / SSM 연계 고려

---

## 4.12.3 비용 고려사항

* 필요 없는 인스턴스는 중지 또는 종료

* EBS 미사용 볼륨 정리

* Elastic IP 미사용 자원 정리

* 과도한 인스턴스 타입 사용 지양

---

# 4.13 실습 : EC2 웹 서버 생성

실습 목표

* EC2 인스턴스를 생성함

* 보안 그룹을 구성함

* User Data로 웹 서버를 자동 설치함

* 브라우저에서 웹 페이지 접속을 확인함

---

## 4.13.1 사전 준비

필요 자원

* 3장에서 생성한 VPC

* Public Subnet

* Internet Gateway

* Public Route Table

---

## 4.13.2 보안 그룹 생성

EC2 콘솔 또는 VPC 콘솔에서 생성함.

이름

```
이니셜-sg-web
```

Inbound Rules

| 타입 | 프로토콜 | 포트 | 소스 |
| --- | --- | --- | --- |
| SSH | TCP | 22 | 내 IP |
| HTTP | TCP | 80 | 0.0.0.0/0 |

설명

* SSH는 관리자 접속용

* HTTP는 웹 접속 테스트용

* 실습에서는 HTTPS보다 HTTP부터 확인하는 것이 편함

---

## 4.13.3 Key Pair 생성

EC2 콘솔에서 Key Pair를 생성함.

이름

```
이니셜-key
```

형식

```
.pem
```

주의

* 다운로드한 개인키는 안전한 위치에 보관

* 리눅스/macOS에서는 권한 조정 필요

```
chmod400 이니셜-key.pem
```

이 명령은 개인키 파일의 권한을 소유자 읽기 전용으로 제한하는 명령임.

SSH는 개인키 파일의 권한이 너무 넓으면 보안상 위험하다고 판단하여 접속을 거부할 수 있음.

따라서 `.pem` 파일을 사용할 때는 보통 먼저 `chmod 400`으로 권한을 제한함.

---

## 4.13.4 EC2 인스턴스 생성

EC2 콘솔 → Instances → Launch instances

설정 예

| 항목 | 값 |
| --- | --- |
| Name | 이니셜-ec2-web |
| AMI | Amazon Linux 2023 |
| Instance Type | t3.micro |
| Key Pair | 이니셜-key |
| VPC | 이니셜-vpc-main |
| Subnet | 이니셜-subnet-public-a |
| Auto-assign Public IP | Enable |
| Security Group | 이니셜-sg-web |

---

## 4.13.5 User Data 입력

Advanced details에서 User Data에 아래 스크립트를 입력함.

```
#!/bin/bash
dnf update -y
dnf install -y httpd
systemctl enable httpd
systemctlstart httpd
echo"<h1>Welcome to EC2 Web Server</h1>" > /var/www/html/index
```

### 명령어 설명

### `#!/bin/bash`

이 스크립트를 bash 셸로 실행하라는 의미임.

리눅스 스크립트의 첫 줄에 자주 들어가는 선언문임.

### `dnf update -y`

설치된 패키지 목록과 패키지를 최신 상태로 업데이트함.

* `y` 옵션은 중간에 확인 질문이 나왔을 때 자동으로 yes를 입력하는 역할을 함.

### `dnf install -y httpd`

Apache 웹 서버 패키지인 `httpd`를 설치함.

Amazon Linux 2023 계열에서는 패키지 관리 도구로 `dnf`를 사용함.

### `systemctl enable httpd`

부팅할 때 Apache가 자동 실행되도록 설정함.

즉, 서버를 재부팅해도 웹 서버가 다시 올라오게 만듦.

### `systemctl start httpd`

지금 즉시 Apache 서비스를 실행함.

### `echo "<h1>Welcome to EC2 Web Server</h1>" > /var/www/html/index`

웹 서버의 기본 문서 경로에 HTML 파일을 생성함.

브라우저에서 해당 EC2의 IP로 접속하면 이 문장이 표시됨.

---

## 4.13.6 접속 확인

인스턴스가 Running 상태가 된 뒤, Public IPv4 주소를 복사해 브라우저에서 접속함.

예

```
http://43.x.x.x
```

정상 동작 시 아래와 비슷한 문구가 표시됨.

```
Welcome to EC2 Web Server
```

---

# 4.14 실습 : SSH 접속

Linux / macOS / WSL 환경에서 실행

```
ssh -i 이니셜-key.pem ec2-user@<EC2-Public-IP>
```

예

```
ssh -i kyt-key.pem ec2-user@43.201.10.10
```

### 명령어 설명

### `ssh`

원격 서버에 안전하게 접속하기 위한 Secure Shell 명령어임.

### `-i 이니셜-key.pem`

접속 시 사용할 개인키 파일을 지정함.

AWS EC2는 비밀번호 방식보다 키 기반 인증을 많이 사용함.

### `ec2-user`

Amazon Linux 계열의 기본 로그인 계정임.

Ubuntu AMI를 썼다면 기본 계정은 보통 `ubuntu`임.

### `@<EC2-Public-IP>`

접속 대상 서버의 공인 IP 주소를 지정함.

---

## 4.14.1 웹 서버 동작 확인 명령

SSH 접속 후 아래 명령으로 상태를 확인함.

```
systemctl status httpd
```

이 명령은 Apache 서비스 상태를 확인하는 명령임.

확인 포인트

* active (running) 상태인지 확인

* 비정상 종료되었는지 확인

* 에러 메시지가 있는지 확인

추가 확인

```
curl localhost
```

이 명령은 자기 자신 서버의 웹 서버에 HTTP 요청을 보내는 명령임.

브라우저 없이도 웹 페이지 응답을 텍스트로 확인할 수 있음.

정상 동작 시

```
<h1>Welcome to EC2 Web Server</h1>
```

가 출력됨.

---

# 4.15 AWS CLI로 EC2 조회 실습

CLI로 인스턴스 정보를 조회할 수 있음.

---

## 4.15.1 인스턴스 목록 조회

```
aws ec2 describe-instances
```

이 명령은 계정 내 EC2 인스턴스의 상세 정보를 JSON 형식으로 반환함.

출력 내용이 매우 많기 때문에 처음 보면 복잡할 수 있음.

포함되는 정보 예

* InstanceId

* InstanceType

* PrivateIpAddress

* PublicIpAddress

* State

* SecurityGroups

* SubnetId

* VpcId

---

## 4.15.2 실행 중인 인스턴스만 조회

```
aws ec2 describe-instances \
--filters"Name=instance-state-name,Values=running"
```

### 명령어 설명

### `--filters`

조건을 걸어 필요한 결과만 조회하는 옵션임.

### `"Name=instance-state-name,Values=running"`

인스턴스 상태가 `running`인 것만 조회하겠다는 의미임.

즉, 이 명령은 전체 인스턴스 중 현재 실행 중인 서버만 필터링해서 보여줌.

---

## 4.15.3 특정 항목만 간단히 조회

```
aws ec2 describe-instances \
--query "Reservations[*].Instances[*].[InstanceId,InstanceType,PrivateIpAddress,PublicIpAddress,State.Name]" \
--output table
```

### 명령어 설명

### `--query`

JMESPath 문법을 사용해서 원하는 필드만 추출함.

### `Reservations[*].Instances[*]`

AWS EC2 응답 JSON 구조에서 인스턴스 목록이 위치한 경로임.

### `[InstanceId,InstanceType,PrivateIpAddress,PublicIpAddress,State.Name]`

표시할 항목만 선택함.

### `--output table`

결과를 JSON 대신 표 형식으로 출력함.

이 명령은 실습 중 인스턴스 상태를 빠르게 확인할 때 매우 유용함.

---

# 4.16 EC2 구매 옵션 설계 관점 정리

실무에서 인스턴스 선택은 단순히 “싸면 좋다”가 아니라 워크로드 특성을 보고 결정해야 함.

---

## 4.16.1 교육용 / 실습용 환경

추천 방식

* On-Demand

* t3.micro 또는 t3.small

이유

* 유연하게 생성 / 삭제 가능

* 약정이 필요 없음

* 학생별 실습 환경에 적합

---

## 4.16.2 운영 웹 서버

추천 방식

* Reserved Instances 또는 Savings Plans

* m 계열 또는 적절한 범용 인스턴스

이유

* 항상 켜져 있는 서버라 할인 효과 큼

* 장기 예측 가능한 사용량에 적합

---

## 4.16.3 배치 처리 / 일시 작업

추천 방식

* Spot Instance

이유

* 비용 절감 효과 큼

* 중단되어도 다시 실행 가능한 작업에 적합

---

# 4.17 EC2 아키텍처 관점 핵심 정리

EC2를 아키텍처 관점에서 보면 다음이 중요함.

### 1. EC2 한 대는 아키텍처가 아님

단일 서버는 장애에 취약함.

운영 환경에서는 Load Balancer, Auto Scaling, Multi AZ와 결합해야 함.

### 2. 스토리지를 구분해서 봐야 함

* OS 디스크와 데이터 디스크

* 영구 저장소와 임시 저장소

* EBS와 Instance Store 차이

### 3. 비용과 성능을 함께 고려해야 함

* 무조건 큰 인스턴스가 좋은 것이 아님

* 워크로드에 맞는 타입을 선택해야 함

### 4. 네트워크와 보안이 같이 따라와야 함

* Public / Private Subnet 구분

* 보안 그룹 최소 허용

* IAM Role 활용

---