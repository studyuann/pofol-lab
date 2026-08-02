---
title: "Bastion Host를 이용한 Private Web Server 접속 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 클라우드 기술 기초(TESS)"]
is_public: true
draft: false
---

# Bastion Host를 이용한 Private Web Server 접속 실습

---

# 실습 목표

이번 실습에서는 AWS 네트워크 환경에서 **Public Subnet과 Private Subnet을 활용한 보안 아키텍처**를 구축한다.

다음 환경을 구성한다.

1. Public Subnet에 **Bastion Host 구축**

2. Private Subnet에 **Web Server 구축**

3. Bastion Host를 통해 Private Web Server SSH 접속

4. Bastion Host를 **Reverse Proxy 서버로 구성**

5. Bastion Public IP를 통해 Web 서비스 접속

이 실습을 통해 다음 개념을 이해한다.

* Bastion Host 역할

* Private Subnet 보안 구조

* SSH Jump Host

* Reverse Proxy 구조

* AWS CLI를 이용한 EC2 정보 조회

---

# 실습 아키텍처

```
Internet
   │
   │
Public Subnet
   │
   │
이니셜-ec2-bastion
   │
   │ SSH
   │
Private Subnet
   │
   │
이니셜-ec2-web
```

Reverse Proxy 적용 후

```
Internet
   │
   │ HTTP
   │
이니셜-ec2-bastion (Nginx)
   │
   │ Reverse Proxy
   │
이니셜-ec2-web
```

[![](Bastion%20Host%EB%A5%BC%20%EC%9D%B4%EC%9A%A9%ED%95%9C%20Private%20Web%20Server%20%EC%A0%91%EC%86%8D%20%EC%8B%A4%EC%8A%B5/image.png)](Bastion%20Host%EB%A5%BC%20%EC%9D%B4%EC%9A%A9%ED%95%9C%20Private%20Web%20Server%20%EC%A0%91%EC%86%8D%20%EC%8B%A4%EC%8A%B5/image.png)

---

# 1 Bastion Server 생성

## EC2 콘솔 이동

```
EC2
 → 인스턴스
 → 인스턴스 시작
```

---

## Bastion 인스턴스 설정

| 항목 | 값 |
| --- | --- |
| 이름 | 이니셜-ec2-bastion |
| AMI | Amazon Linux 2023 |
| Instance Type | t3.micro |
| Key Pair | 이니셜-key-ec2 |

---

## 네트워크 설정

| 항목 | 값 |
| --- | --- |
| VPC | 이니셜-vpc-01 |
| Subnet | 이니셜-sub-pub-01 |
| Public IP | 활성화 |

---

## 보안 그룹

| Type | Source |
| --- | --- |
| SSH | 내 IP |
| HTTP | 내 IP |

---

# Bastion 서버 접속

```
ssh -i 이니셜-key-ec2.pem ec2-user@BASTION_PUBLIC_IP
```

* aws cli 설치 : Amazon Linux 2023에는 설치되어 있음.

```
# Install AWS CLI
curl -fsSL https://awscli.amazonaws.com/awscli-exe-linux-$(uname -m).zip -o /tmp/aws-cli.zip
unzip -q -d /tmp /tmp/aws-cli.zip
sudo /tmp/aws/install
rm -rf /tmp/aws
aws --version
```

* aws configure : access key와 secret key 저장.

---

# 2 Web Server 생성 (Private Subnet)

## EC2 생성

| 항목 | 값 |
| --- | --- |
| 이름 | 이니셜-ec2-web |
| AMI | Amazon Linux 2023 |
| Instance Type | t3.micro |
| Key Pair | 이니셜-key-ec2 |

---

## 네트워크 설정

| 항목 | 값 |
| --- | --- |
| VPC | 이니셜-vpc-01 |
| Subnet | 이니셜-sub-pri-01 |
| Public IP | 비활성 |

---

## 보안 그룹

| Type | Source |
| --- | --- |
| SSH | VPC CIDR |
| HTTP | VPC CIDR |

즉

```
VPC 내부에서만 접근 가능
```

---

# 3 Web Server 자동 설치

EC2 생성 시 **User Data에 아래 스크립트 입력**

### install\_python.sh

```
#!/bin/bash

# 1. Python 3.12 및 필수 개발 도구 설치
echo "#####################"
echo "Python 3.12 설치 시작"
echo "#####################"
sudo dnf install python3.12 python3.12-pip python3.12-devel -y

# 2. Alternatives 설정 (기존 3.9와 새 3.12 관리)
echo "##############################"
echo "Python Default Version Setting"
echo "##############################"
# 기존 시스템 파이썬(3.9)을 1순위, 3.12를 2순위로 등록
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 2

# 자동 선택 (2번: python3.12)
sudo update-alternatives --set python3 /usr/bin/python3.12

# 3. Symbolic link 설정 (python 명령어가 3.12를 가리키도록)
echo "##############################"
echo "Python3 → Python Symbolic link"
echo "##############################"
sudo ln -fs /usr/bin/python3.12 /usr/bin/python

# 4. 시스템 도구(dnf/yum) 하드코딩 보호
# dnf/yum은 시스템 파이썬(3.9)에 의존하므로, 첫 줄(Shebang)을 명시적으로 고정합니다.
echo "#####################################"
echo "dnf/yum 안정성 확보 (Python 3.9 고정)"
echo "#####################################"
sudo sed -i '1s|#!/usr/bin/python3|#!/usr/bin/python3.9|' /usr/bin/dnf
sudo sed -i '1s|#!/usr/bin/python3|#!/usr/bin/python3.9|' /usr/bin/yum

# 5. PIP 업그레이드
echo "################"
echo "PIP Upgrade 설치"
echo "################"
python3 -m pip install --upgrade pip

# 6. 기타 도구 및 소스코드 클론
echo "#######################"
echo "Stress, Git & Code Install"
echo "#######################"
sudo dnf install stress git -y
cd /root/
# 기존 디렉토리가 있다면 삭제 후 다시 클론 (재실행 대비)
sudo rm -rf streamlit-project
sudo git clone https://github.com/sunnykid7/streamlit-project.git
cd streamlit-project

# 7. Python 패키지 설치
echo "######################"
echo "Python Package Install"
echo "######################"
# 3.12에서는 일부 패키지 설치 시 --user를 권장하거나 venv를 권장할 수 있음
pip install --no-cache-dir -r requirements.txt

# 8. AWS CLI 업그레이드
echo "##############"
echo "Upgrade AWSCLI"
echo "##############"
if [ -f "scripts/upgrade_aws_cli_v2.sh" ]; then
    sudo sh scripts/upgrade_aws_cli_v2.sh
fi

# 9. 애플리케이션 실행 (80포트 사용 시 sudo 권한 필요할 수 있음)
echo "#################"
echo "Application Start"
echo "#################"
# Streamlit을 백그라운드에서 실행하려면 앞에 'nohup'과 끝에 '&'를 붙이는 것이 좋습니다.
# 포트 80은 Well-known 포트이므로 일반 사용자는 권한이 없을 수 있습니다.
python3 -m streamlit run main.py --server.port 8501 --server.enableCORS false --server.enableXsrfProtection false
```

스크립트 동작

1. Python 3.11 설치

2. Python 기본 버전 변경

3. pip 업그레이드

4. Git 프로젝트 다운로드

5. Streamlit 웹 서버 실행

---

# 4 Bastion → Web Server 접속

먼저 Bastion 서버에 접속한다.

```
ssh -i 이니셜-key-ec2.pem ec2-user@BASTION_PUBLIC_IP
```

---

## Bastion 서버에 Key 저장

```
vim 이니셜-key-ec2.pem
```

권한 설정

```
chmod 600 이니셜-key-ec2.pem
```

---

## Web Server 접속

Web Server Private IP 확인

```
10.x.x.x
```

접속

```
ssh -i 이니셜-key-ec2.pem ec2-user@WEB_PRIVATE_IP
```

접속 흐름

```
Internet
 → Bastion
 → Private Web Server
```

* MobaXterm의 Jumphost 기능을 이용해 접속할 수 있다.

---

# 5 Bastion Reverse Proxy 구성

Private Web Server는 외부에서 직접 접근할 수 없다.

따라서 Bastion 서버에 **Nginx Reverse Proxy**를 구성한다.

---

# Proxy 설정 스크립트 생성

```
vim setting_bastion.sh
```

---

# setting\_bastion.sh

* **이니셜-ec2-web을 실제 서버의 Tag이름으로 변경한다.**

```
#!/bin/bash

echo "WEB EC2 Private IP 주소를 조회 중입니다..."
WEB_PRIVATE_IP=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=이니셜-ec2-web" \
  --query "Reservations[*].Instances[*].PrivateIpAddress" \
  --output text)

if [ $? -ne 0 ]; then
    echo "[Error] 인스턴스 정보를 가져오는데 실패했습니다."
    exit 1
fi

if [ -z "$WEB_PRIVATE_IP" ]; then
    echo "WEB EC2 인스턴스 IP 정보를 가져오는데 실패했습니다."
    exit 1
fi

echo "WEB EC2 Private IP 주소 조회 완료: $WEB_PRIVATE_IP"

sudo yum install nginx -y

echo "user nginx;
worker_processes auto;

events {
    worker_connections 1024;
}

http {
    server {
        listen 80;
        server_name _;

        location / {
            proxy_pass http://$WEB_PRIVATE_IP:8501/;
            proxy_http_version 1.1;

            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";

            proxy_read_timeout 86400;
            proxy_send_timeout 86400;
            proxy_buffering off;
        }
    }
}" | sudo tee /etc/nginx/nginx.conf > /dev/null

sudo nginx -t

sudo systemctl start nginx
sudo systemctl enable nginx
```

---

# 스크립트 실행

```
chmod +x setting_bastion.sh
```

```
./setting_bastion.sh
```

---

# Web 접속 테스트

브라우저 접속

```
http://BASTION_PUBLIC_IP
```

접속 흐름

```
Client
 → Bastion Host
 → Reverse Proxy
 → Private Web Server
```

---

# 최종 아키텍처

```
Internet
   │
   │
이니셜-ec2-bastion
   │
   │ Reverse Proxy
   │
이니셜-ec2-web
```

---

# 실습 핵심 개념

| 구성 | 역할 |
| --- | --- |
| Bastion Host | 관리용 서버 |
| Private Subnet | 내부 서버 보호 |
| Reverse Proxy | 외부 접근 제어 |
| Security Group | 네트워크 접근 제어 |
| AWS CLI | EC2 정보 조회 |

---

# 6 Instance Profile(IAM Role)을 이용한 EC2 권한 할당

현재 Web Server는 AWS API를 호출할 수 있는 권한이 없다.

따라서 Web 애플리케이션에서 **EC2 정보를 조회하려고 하면 오류가 발생한다.**

이를 해결하기 위해 **EC2 인스턴스에 IAM Role을 할당**한다.

이 방식은 **Instance Profile**이라고 한다.

즉

```
EC2 → IAM Role → AWS API 접근
```

구조로 동작한다.

---

# 6.1 IAM Role 생성

IAM 콘솔로 이동

```
IAM
 → 역할
 → 역할 생성
```

---

## 역할 생성 설정

| 항목 | 값 |
| --- | --- |
| 신뢰할 수 있는 엔터티 유형 | AWS 서비스 |
| 사용 사례 | EC2 |

다음 클릭

---

## 권한 정책 추가

검색창에서 다음 정책 검색

```
AmazonEC2ReadOnlyAccess
```

체크 후

```
다음
```

---

## 역할 생성

| 항목 | 값 |
| --- | --- |
| 역할 이름 | ec2-describe-role |

```
역할 생성
```

---

# 6.2 EC2 Instance Profile 할당

EC2 콘솔 이동

```
EC2
 → 인스턴스
```

---

## Web Server 선택

```
이니셜-ec2-web
```

선택 후

```
작업
 → 보안
 → IAM 역할 수정
```

---

## IAM Role 설정

| 항목 | 값 |
| --- | --- |
| IAM 역할 | ec2-describe-role |

```
IAM 역할 업데이트
```

---

# 7 Web 서비스 접속 테스트

브라우저에서 접속

```
http://BASTION_PUBLIC_IP
```

접속 흐름

```
Client
 → Bastion Host
 → Nginx Reverse Proxy
 → Private Web Server
```

---

# 정상 동작 확인

IAM Role이 정상적으로 적용되면

웹 페이지에서 **EC2 인스턴스 정보가 정상적으로 조회된다.**

예

```
Instance ID
Instance Type
Region
Availability Zone
```

---

# 최종 아키텍처

```
Internet
   │
   │
Public Subnet
   │
   │
Bastion Host
(Nginx Reverse Proxy)
   │
   │
Private Subnet
   │
   │
Web Server
(Streamlit Application)
   │
   │
IAM Role
   │
   │
AWS API
```

---

# 실습 핵심 개념

| 구성 | 역할 |
| --- | --- |
| Bastion Host | 관리 서버 |
| Private Subnet | 내부 서버 보호 |
| Reverse Proxy | 외부 접근 제어 |
| Instance Profile | EC2 권한 관리 |
| IAM Role | AWS API 접근 권한 |
| Security Group | 네트워크 접근 제어 |