---
title: "Auto Scaling과 ALB를 이용한 Web Application 확장 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 클라우드 기술 기초(TESS)"]
is_public: true
draft: false
---

# Auto Scaling과 ALB를 이용한 Web Application 확장 실습

---

[![](Auto%20Scaling%EA%B3%BC%20ALB%EB%A5%BC%20%EC%9D%B4%EC%9A%A9%ED%95%9C%20Web%20Application%20%ED%99%95%EC%9E%A5%20%EC%8B%A4%EC%8A%B5/image.png)](Auto%20Scaling%EA%B3%BC%20ALB%EB%A5%BC%20%EC%9D%B4%EC%9A%A9%ED%95%9C%20Web%20Application%20%ED%99%95%EC%9E%A5%20%EC%8B%A4%EC%8A%B5/image.png)

## 실습 목표

본 실습에서는 EC2 인스턴스를 기반으로 **AMI를 생성하고 Launch Template을 만든 뒤 Auto Scaling Group을 구성하고 Application Load Balancer와 연동**하는 과정을 수행한다.

실습을 통해 다음 내용을 이해한다.

* Web Application 자동 실행 설정

* AMI 생성 방법

* Launch Template 구성 방법

* Auto Scaling Group 생성 방법

* Application Load Balancer와 Auto Scaling 연동

* CPU 사용률 기반 Scale Out 동작

* 퍼블릭 서브넷과 프라이빗 서브넷의 역할 구분

---

# 1. 전체 아키텍처 이해

이번 실습의 목표 구조는 다음과 같다.

```
Internet
  ↓
Application Load Balancer
(Public Subnet)
  ↓
EC2 Auto Scaling Group
(Private Subnet)
```

이 구조에서 중요한 점은 다음과 같다.

* 외부 사용자는 **Internet-facing ALB** 로 접속한다.

* ALB는 퍼블릭 서브넷에 배치해야 한다.

* 실제 웹 애플리케이션은 프라이빗 서브넷의 EC2 인스턴스에서 실행한다.

* Auto Scaling Group은 프라이빗 서브넷에 인스턴스를 자동 생성한다.

* ALB는 Target Group을 통해 프라이빗 서브넷의 EC2 인스턴스로 요청을 전달한다.

---

# 2. 사전 네트워크 구성 확인

실습 전에 반드시 네트워크 구성이 올바른지 확인해야 한다.

## 2.1 서브넷 구성 예시

예시 구성은 다음과 같다.

```
ap-northeast-2a
 ├ public subnet-a
 └ private subnet-a

ap-northeast-2c
 ├ public subnet-c
 └ private subnet-c
```

즉 같은 가용 영역 안에서도 퍼블릭 서브넷과 프라이빗 서브넷은 각각 따로 존재할 수 있다.

여기서 중요한 것은 **가용 영역 이름이 아니라 서브넷이 어떤 라우팅 테이블을 사용하는가**다.

---

## 2.2 퍼블릭 서브넷의 의미

퍼블릭 서브넷은 일반적으로 다음 라우팅을 가진다.

```
0.0.0.0/0 -> Internet Gateway
```

이런 서브넷에는 보통 다음 리소스를 둔다.

* Internet-facing ALB

* NAT Gateway

* Bastion Host

---

## 2.3 프라이빗 서브넷의 의미

프라이빗 서브넷은 일반적으로 Internet Gateway로 직접 나가는 기본 경로가 없다.

예를 들면 다음과 같다.

```
VPC CIDR -> local
```

또는 외부 아웃바운드가 필요한 경우 다음과 같이 NAT Gateway를 사용한다.

```
0.0.0.0/0 -> NAT Gateway
```

이런 서브넷에는 보통 다음 리소스를 둔다.

* Web Server

* App Server

* Auto Scaling EC2

* Database

---

## 2.4 이번 실습에서 반드시 기억할 점

이번 실습에서는 다음 구분이 반드시 필요하다.

* **ALB는 퍼블릭 서브넷**

* **ASG 인스턴스는 프라이빗 서브넷**

만약 ALB가 프라이빗 서브넷에 배치되어 있으면, Internet-facing 으로 생성했더라도 외부에서 접속되지 않을 수 있다.

이전에 겪은 현상처럼, ALB와 대상 서버가 같은 라우팅 테이블을 공유하는 상태에서 `0.0.0.0/0 -> IGW` 를 넣으면 접속되고 빼면 안 되는 현상이 나타날 수 있다.

이것은 **대상 서버가 원래 IGW가 필요해서가 아니라, ALB가 퍼블릭 서브넷에 있지 않았기 때문**이다.

---

# 3. Web Application 자동 실행 설정

Auto Scaling 환경에서는 새로운 EC2 인스턴스가 생성될 때마다 애플리케이션이 자동으로 실행되어야 한다.

이를 위해 systemd 서비스를 설정한다.

---

## 3.1 Web Server 접속

Bastion Host를 통해 초기 Web Server 인스턴스에 접속한다.

이 인스턴스는 이후 AMI 생성의 기준이 되는 인스턴스다.

---

## 3.2 자동 실행 스크립트 작성

다음 파일을 생성한다.

```
vi streamlit_service.sh
```

다음 내용을 입력한다.

```
#!/bin/bash

sudo bash -c 'cat << EOF > /etc/systemd/system/streamlit.service
[Unit]
Description=Streamlit Application Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/streamlit-project
ExecStart=/usr/local/bin/streamlit run main.py --server.port 80 --server.address 0.0.0.0
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF'

sudo systemctl daemon-reload
sudo systemctl enable streamlit.service
sudo systemctl start streamlit.service

echo "Streamlit 서비스가 등록 및 시작되었음"
```

---

## 3.3 스크립트 실행

다음 명령으로 실행한다.

```
sh ./streamlit_service.sh
```

이 스크립트가 수행하는 일은 다음과 같다.

1. `streamlit.service` 파일 생성

2. Streamlit 실행 명령 등록

3. systemd 서비스 등록

4. 부팅 시 자동 실행 설정

5. 현재 세션에서 서비스 즉시 시작

---

## 3.4 서비스 상태 확인

다음 명령으로 서비스 상태를 확인한다.

```
sudo systemctl status streamlit.service
```

정상 동작 여부를 확인하려면 다음 명령도 수행한다.

```
sudo ss -tulpn | grep :80
```

또는

```
curl http://localhost
```

### 설명

* `systemctl status` 는 서비스가 정상 실행 중인지 확인하는 명령이다.

* `ss -tulpn` 은 현재 어떤 프로세스가 어떤 포트를 열고 있는지 확인한다.

* `grep :80` 은 80번 포트를 사용하는 프로세스만 필터링해서 보여준다.

* `curl http://localhost` 는 로컬 서버에서 웹 응답이 정상적으로 오는지 확인한다.

이번 실습에서는 Streamlit이 80 포트에서 직접 서비스되므로, 이후 Target Group 포트와 보안 그룹 포트도 동일하게 맞춰야 한다.

---

# 4. Web Server AMI 생성

Auto Scaling은 동일한 설정을 가진 EC2 인스턴스를 반복적으로 생성해야 하므로 AMI가 필요하다.

AMI는 현재 설정된 인스턴스를 이미지로 저장한 것이다.

---

## 4.1 AMI 생성 대상 확인

다음 EC2 인스턴스를 선택한다.

```
이니셜-ec2-web
```

이 인스턴스에는 다음이 준비되어 있어야 한다.

* 애플리케이션 코드

* Python 및 Streamlit 설치

* `streamlit.service` 설정 완료

* 서비스 정상 실행 상태

---

## 4.2 AMI 생성 메뉴 이동

다음 메뉴로 이동한다.

```
작업
→ 이미지 및 템플릿
→ 이미지 생성
```

---

## 4.3 AMI 설정

이미지 이름 예시는 다음과 같다.

```
이니셜-ami-web-v1-YYMMDD
```

옵션은 다음처럼 설정할 수 있다.

```
재부팅 안 함
```

### 설명

이 옵션은 서비스 중단 없이 AMI를 만들기 위해 사용할 수 있다.

다만 운영 환경에서는 파일 시스템 일관성 측면에서 재부팅 후 생성하는 것이 더 안전한 경우가 있다.

실습 환경에서는 빠르게 진행하기 위해 재부팅 안 함 옵션을 사용할 수 있다.

AMI 생성 버튼을 클릭한다.

---

## 4.4 AMI 생성 상태 확인

다음 메뉴로 이동한다.

```
EC2 콘솔
→ AMI
```

다음 AMI의 상태를 확인한다.

```
이니셜-ami-web-v1-YYMMDD
```

상태가 **Available** 이 되면 사용 가능하다.

---

# 5. Launch Template 생성

Auto Scaling Group은 Launch Template을 기준으로 EC2 인스턴스를 생성한다.

즉 Launch Template에는 **어떤 이미지로 어떤 인스턴스를 어떤 설정으로 만들 것인가**가 정의된다.

---

## 5.1 Launch Template 생성 메뉴 이동

다음 메뉴로 이동한다.

```
EC2 콘솔
→ 시작 템플릿
→ 시작 템플릿 생성
```

---

## 5.2 기본 설정

시작 템플릿 이름

```
이니셜-template-autoscaling-web
```

옵션

```
Auto Scaling 지침 활성화
```

---

## 5.3 AMI 선택

다음 AMI를 선택한다.

```
이니셜-ami-web-v1-YYMMDD
```

---

## 5.4 인스턴스 설정

인스턴스 유형

```
t3.micro
```

키 페어

```
이니셜-keypair
```

---

## 5.5 네트워크 설정

서브넷은 다음처럼 설정한다.

```
시작 템플릿에 포함하지 않음
```

이유는 실제 서브넷 선택을 Auto Scaling Group 단계에서 하기 때문이다.

보안 그룹은 다음을 선택한다.

```
이니셜-sg-web
```

### 보안 그룹 주의사항

이 보안 그룹은 웹 서버용 보안 그룹이어야 하며, 일반적으로 다음 규칙을 가진다.

인바운드 예시

```
HTTP 80
Source: ALB 보안 그룹
```

즉 80 포트를 전체 인터넷에 열기보다 **ALB 보안 그룹만 허용하는 방식**이 더 적절하다.

---

## 5.6 태그 설정

Tag Key

```
Name
```

Tag Value

```
이니셜-ec2-web
```

---

## 5.7 고급 설정

IAM Instance Profile

```
이니셜-role-ec2
```

Hostname type

```
IP name
```

옵션 활성화

```
리소스 기반 IPv4(A레코드) DNS 요청
```

설정 완료 후 다음을 클릭한다.

```
시작 템플릿 생성
```

---

# 6. Auto Scaling Group 생성

이제 Launch Template을 기반으로 Auto Scaling Group을 생성한다.

---

## 6.1 생성 메뉴 이동

다음 메뉴로 이동한다.

```
EC2 콘솔
→ Auto Scaling Group
→ Auto Scaling Group 생성
```

---

## 6.2 기본 설정

Auto Scaling Group 이름

```
이니셜-asg-web
```

Launch Template

```
이니셜-template-autoscaling-web
```

---

## 6.3 네트워크 설정

VPC

```
이니셜-vpc-ap-01
```

서브넷

```
이니셜-sub-pri-01
이니셜-sub-pri-02
```

여기서 중요한 점은 다음과 같다.

* Auto Scaling 인스턴스는 **Private Subnet에서 실행됨**

* 이 서브넷은 **ALB용 퍼블릭 서브넷과 구분되어야 함**

* ALB와 ASG 인스턴스가 같은 라우팅 테이블을 공유하면 안 됨

---

## 6.4 Load Balancer 연결

옵션

```
기존 로드 밸런서 연결
```

대상 그룹

```
이니셜-tg-web
```

옵션 활성화

```
Elastic Load Balancer 상태 확인
```

### 설명

이 옵션을 활성화하면 Auto Scaling Group은 ELB 상태를 기준으로 인스턴스 상태를 판단할 수 있다.

즉 Target Group 헬스 체크에서 비정상으로 판단된 인스턴스는 교체 대상이 될 수 있다.

---

## 6.5 그룹 크기 설정

Desired Capacity

```
1
```

Minimum Capacity

```
1
```

Maximum Capacity

```
4
```

즉 최소 1개, 최대 4개의 EC2 인스턴스가 실행된다.

---

## 6.6 Auto Scaling 정책 설정

정책 유형

```
Target Tracking Scaling Policy
```

정책 이름

```
Target Tracking Policy
```

지표 유형

```
Average CPU Utilization
```

Target Value

```
30
```

### 설명

Target Tracking 정책은 특정 지표를 목표값 근처로 유지하려는 방식이다.

여기서는 평균 CPU 사용률 30%를 목표로 한다.

즉 CPU가 지속적으로 30%를 넘으면 인스턴스를 추가하는 방향으로 동작하고,

반대로 CPU가 낮아지면 인스턴스 수를 줄이는 방향으로 동작한다.

주의할 점은 **정확히 30%를 넘는 순간 즉시 Scale Out이 발생하는 것은 아님**이다.

CloudWatch 지표 수집 주기, 평가 기간, 쿨다운 시간 등에 따라 실제 반응 시점은 조금 다를 수 있다.

---

## 6.7 태그 설정

Tag Key

```
Name
```

Tag Value

```
이니셜-asg-web
```

생성 완료 후 Auto Scaling Group을 생성한다.

---

# 7. Application Load Balancer 확인

Auto Scaling Group과 연결되는 ALB가 올바르게 구성되어 있는지 확인한다.

---

## 7.1 ALB 확인 항목

다음 메뉴로 이동한다.

```
EC2 콘솔
→ Load Balancer
→ 이니셜-alb-web
```

다음 항목을 확인한다.

* Scheme: `internet-facing`

* 연결된 서브넷: 퍼블릭 서브넷 2개 이상

* 리스너: HTTP 80 또는 HTTPS 443

* 연결 대상 그룹: `이니셜-tg-web`

---

## 7.2 중요 확인 사항

Internet-facing ALB 는 반드시 퍼블릭 서브넷에 연결되어 있어야 한다.

즉 ALB가 연결된 서브넷의 라우팅 테이블에는 다음 경로가 있어야 한다.

```
0.0.0.0/0 -> Internet Gateway
```

이 조건이 없으면 ALB가 외부에서 접근되지 않을 수 있다.

---

# 8. Web Service 접속

ALB DNS 이름을 확인한다.

다음 메뉴 이동

```
EC2 콘솔
→ Load Balancer
→ 이니셜-alb-web
```

DNS 주소 예시

```
http://xxxx.ap-northeast-2.elb.amazonaws.com
```

브라우저로 접속한다.

### 주의

접속 확인은 반드시 **ALB DNS 주소** 기준으로 해야 한다.

대상 EC2가 프라이빗 서브넷에 있으므로 EC2 공인 IP 접속을 기준으로 판단하면 안 된다.

---

# 9. Scale Out 테스트

웹 페이지에서 부하 유발 기능을 실행한다.

예시

```
Stress Tool
```

이 기능은 CPU 사용률을 증가시키기 위한 것이다.

CPU 사용률이 증가하면 Auto Scaling 정책에 따라 새 인스턴스가 생성될 수 있다.

---

# 10. Auto Scaling 동작 확인

다음 메뉴로 이동한다.

```
EC2 콘솔
→ Auto Scaling Group
→ 이니셜-asg-web
```

확인 항목은 다음과 같다.

```
모니터링
활동(Activity)
인스턴스 관리
```

다음과 같은 결과를 확인할 수 있다.

* CPU 사용률 증가

* 새로운 EC2 인스턴스 생성

* Target Group 자동 등록

* 부하 감소 후 Scale In

---

# 11. Target Group 상태 확인

다음 메뉴로 이동한다.

```
EC2 콘솔
→ 대상 그룹
→ 이니셜-tg-web
```

확인 항목

* 등록된 대상 수

* Health 상태

* deregistration 중인 대상 존재 여부

### 설명

Scale In 이 발생하면 기존 인스턴스가 바로 사라지지 않고 잠시 남아 있을 수 있다.

이것은 ALB의 **deregistration delay** 때문이다.

즉 다음과 같은 상태가 잠시 보일 수 있다.

* 정상 1

* 제거 중 1

이것은 비정상이 아니라 연결 종료를 위한 정상 동작일 수 있다.

---

# 12. 정리

이번 실습에서 수행한 작업은 다음과 같다.

1. Web Application 자동 실행 설정

2. AMI 생성

3. Launch Template 생성

4. Auto Scaling Group 생성

5. ALB 및 Target Group 연동

6. CPU 기반 Scale Out 테스트

7. Scale In 및 대상 그룹 상태 확인

8. 퍼블릭 서브넷과 프라이빗 서브넷 역할 구분 확인

---