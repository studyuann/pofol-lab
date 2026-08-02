---
title: "11장 Terraform과 Ansible 연계"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "배포자동화를 위한 Terraform"]
is_public: true
draft: false
---

# 11장. Terraform과 Ansible 연계

## 1. 학습 목표

이 장에서는 Terraform과 Ansible을 함께 사용하는 이유와 연계 방식을 이해하고, 인프라 생성과 서버 구성 자동화를 하나의 흐름으로 연결하는 방법을 학습한다. 학습이 끝나면 다음이 가능해진다.

* Terraform과 Ansible의 역할 차이를 설명할 수 있음

* 두 도구를 왜 함께 사용하는지 설명할 수 있음

* Terraform으로 인프라를 생성한 뒤 Ansible로 서버를 구성할 수 있음

* Terraform 출력값을 Ansible 인벤토리와 연결할 수 있음

* 실무에서 자주 사용하는 Terraform + Ansible 자동화 흐름을 이해할 수 있음

---

## 2. 왜 Terraform과 Ansible을 함께 사용하는가

클라우드 자동화를 처음 접할 때는 하나의 도구로 모든 것을 처리하려는 생각을 하게 된다. 하지만 실무에서는 **인프라를 생성하는 작업**과 **생성된 서버 내부를 구성하는 작업**이 성격상 다르기 때문에, 이를 분리해서 다루는 경우가 많다.

Terraform은 **인프라 프로비저닝 도구**다.

즉, 클라우드 자원을 선언적으로 만들고 관리하는 데 강점이 있다.

예를 들어 Terraform은 다음 작업에 적합하다.

* VPC 생성

* 서브넷 생성

* 보안 그룹 생성

* EC2 인스턴스 생성

* 로드밸런서 생성

* 데이터베이스 생성

반면 Ansible은 **구성 관리 및 배포 자동화 도구**다.

즉, 만들어진 서버에 접속해서 내부 상태를 원하는 형태로 맞추는 데 강점이 있다.

예를 들어 Ansible은 다음 작업에 적합하다.

* Nginx 설치

* 패키지 업데이트

* 사용자 생성

* 설정 파일 배포

* 서비스 시작 및 활성화

* 애플리케이션 배포

즉, 두 도구의 역할은 다음처럼 구분할 수 있다.

* Terraform은 **무엇을 만들 것인가**를 담당한다.

* Ansible은 **만들어진 서버를 어떻게 사용할 수 있는 상태로 만들 것인가**를 담당한다.

실무 흐름으로 보면 다음과 같다.

1. Terraform으로 서버, 네트워크, 보안 설정을 생성한다.

2. Terraform이 생성한 서버의 IP, DNS, 접속 정보 등을 확보한다.

3. Ansible이 해당 서버에 SSH로 접속한다.

4. 필요한 패키지 설치, 설정 파일 배포, 서비스 시작을 수행한다.

이렇게 분리하면 각 도구가 가장 잘하는 역할에 집중할 수 있다.

---

## 3. Terraform만으로 서버 구성까지 다 하지 않는 이유

Terraform에도 `remote-exec`, `file`, `local-exec` 같은 provisioner 기능이 있다. 그래서 Terraform만으로도 어느 정도 서버 초기 설정을 수행할 수 있다. 하지만 실무에서는 Terraform으로 인프라를 만들고, 서버 내부 구성은 Ansible로 넘기는 방식을 더 선호하는 경우가 많다.

그 이유는 다음과 같다.

### 3.1 역할 분리가 명확해짐

Terraform은 상태 파일을 기준으로 인프라를 관리한다.

즉, VM이 존재하는지, 서브넷이 생성되었는지, 보안 그룹 규칙이 어떻게 되어 있는지를 추적하는 데 강하다.

반면 Ansible은 서버 안에서 다음과 같은 상태를 관리한다.

* 패키지가 설치되었는가

* 특정 파일이 존재하는가

* 서비스가 실행 중인가

* 설정 내용이 원하는 값인가

이 두 영역은 성격이 다르다.

Terraform 코드 안에 서버 구성 스크립트까지 길게 넣기 시작하면, 코드의 책임이 섞이고 유지보수가 어려워진다.

### 3.2 변경 관리가 쉬워짐

예를 들어 VM을 3대 생성한 뒤 Nginx 설정만 바꾸고 싶다고 하자.

이때 Terraform만 사용하면 다시 provisioner 구문이나 user data를 수정해야 하고, 적용 방식도 복잡해질 수 있다.

반면 Ansible을 사용하면 playbook만 수정해서 다시 실행하면 된다.

즉, **서버 구성 변경은 Ansible만 재실행하면 되는 구조**가 된다.

### 3.3 재사용성이 높아짐

Ansible playbook은 특정 클라우드에 종속되지 않고 재사용하기 쉽다.

예를 들어 Ubuntu 서버에 Nginx를 설치하는 playbook은 AWS EC2에도 사용할 수 있고, GCP VM에도 사용할 수 있으며, 온프레미스 VM에도 사용할 수 있다.

반면 Terraform 코드는 클라우드 provider에 따라 달라진다.

즉, 인프라 생성은 클라우드별로 달라질 수 있지만, 서버 구성은 공통화할 수 있는 경우가 많다.

### 3.4 운영 자동화로 확장하기 좋음

처음에는 단순히 서버 한 대에 웹 서버를 설치하는 정도로 시작할 수 있다.

하지만 실제 운영 환경에서는 다음과 같은 요구가 생긴다.

* 여러 서버에 동일 설정 적용

* 환경별 설정 분리

* 롤링 배포

* 서비스 재시작 자동화

* 설정 파일 템플릿 관리

* 태그 기반 서버 그룹별 작업

이런 작업은 Terraform보다 Ansible이 훨씬 자연스럽다.

---

## 4. Terraform과 Ansible의 역할 구분

수강생이 가장 먼저 명확히 잡아야 할 부분은 **무엇을 Terraform으로 하고, 무엇을 Ansible로 하는가**다.

### Terraform이 담당하는 영역

* 네트워크 생성

* 보안 그룹 / 방화벽 설정

* VM 생성

* 디스크 연결

* 퍼블릭 IP 할당

* 로드밸런서 생성

* 출력값 제공(IP, DNS, ID 등)

### Ansible이 담당하는 영역

* 패키지 설치

* 사용자 계정 생성

* 설정 파일 복사

* 템플릿 파일 배포

* 서비스 시작 / 재시작

* 애플리케이션 코드 배포

* 운영체제 수준 반복 작업 자동화

### 같이 쓰는 흐름

* Terraform이 서버를 만든다.

* Terraform이 접속 가능한 정보를 출력한다.

* Ansible이 출력값을 받아 접속 대상을 결정한다.

* Ansible이 서버 내부를 구성한다.

이 흐름은 매우 전형적이며, 실무 자동화 파이프라인의 기초가 된다.

---

## 5. 전체 실습 시나리오

이번 실습에서는 AWS 환경을 기준으로 다음 순서로 진행한다.

1. Terraform으로 EC2 인스턴스 1대를 생성한다.

2. 보안 그룹에서 SSH(22), HTTP(80)를 허용한다.

3. Terraform output으로 EC2의 공인 IP를 출력한다.

4. 출력된 IP를 기반으로 Ansible 인벤토리를 작성한다.

5. Ansible playbook으로 Nginx를 설치한다.

6. 브라우저에서 웹 서버가 동작하는지 확인한다.

즉, 이번 실습의 핵심은 다음 한 문장으로 정리할 수 있다.

**Terraform이 서버를 만들고, Ansible이 서버를 웹 서버 상태로 완성한다.**

---

## 6. 실습 환경

### 로컬 PC에 설치되어 있어야 할 도구

* Terraform

* Ansible

* AWS CLI

* SSH 클라이언트

### AWS 준비 사항

* AWS 계정

* 액세스 키 설정 완료

* 사용할 키 페어(.pem 파일) 보유

* 기본 VPC 사용 가능 또는 실습용 VPC 준비 완료

### 예시 환경

* Region: `ap-northeast-2`

* OS: Ubuntu 22.04

* Instance Type: `t2.micro` 또는 프리티어 가능 사양

* SSH 사용자: `ubuntu`

---

## 7. 디렉터리 구조

실습 디렉터리는 다음처럼 구성한다.

```
terraform-ansible-lab/
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── terraform.tfvars
└── ansible/
    ├── inventory.ini
    ├── playbook.yml
    └── ansible.cfg
```

구조를 나눈 이유는 명확하다.

* `terraform/` 디렉터리에는 인프라 생성 코드만 둔다.

* `ansible/` 디렉터리에는 서버 구성 자동화 코드만 둔다.

실무에서도 이처럼 역할별로 디렉터리를 분리하는 편이 관리하기 좋다.

---

## 8. Terraform 코드 작성

## 8.1 variables.tf

먼저 변수 파일을 작성한다.

```
variable "aws_region" {
  type    = string
  default = "ap-northeast-2"
}

variable "ami_id" {
  type = string
}

variable "instance_type" {
  type    = string
  default = "t2.micro"
}

variable "key_name" {
  type = string
}
```

### 설명

* `aws_region`  
  AWS 리전을 지정한다.

* `ami_id`  
  사용할 Ubuntu AMI ID를 지정한다.  
  리전마다 AMI ID가 다르므로 실습 전에 현재 리전에 맞는 값을 확인해야 한다.

* `instance_type`  
  EC2 인스턴스 크기를 지정한다.

* `key_name`  
  AWS에 등록된 키 페어 이름을 지정한다.  
  이 값은 SSH 접속 시 매우 중요하다.

---

## 8.2 main.tf

```
provider "aws" {
  region = var.aws_region
}

resource "aws_security_group" "web_sg" {
  name        = "tf-ansible-web-sg"
  description = "Security group for Terraform + Ansible lab"

  tags = {
    Name = "tf-ansible-web-sg"
  }
}

resource "aws_vpc_security_group_ingress_rule" "web_ssh" {
  security_group_id = aws_security_group.web_sg.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 22
  to_port           = 22
  ip_protocol       = "tcp"

  tags = {
    Name = "tf-ansible-web-sg-ssh"
  }
}

resource "aws_vpc_security_group_ingress_rule" "web_http" {
  security_group_id = aws_security_group.web_sg.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"

  tags = {
    Name = "tf-ansible-web-sg-http"
  }
}

resource "aws_vpc_security_group_egress_rule" "web_all_outbound" {
  security_group_id = aws_security_group.web_sg.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"

  tags = {
    Name = "tf-ansible-web-sg-egress"
  }
}

resource "aws_instance" "web" {
  ami                         = var.ami_id
  instance_type               = var.instance_type
  key_name                    = var.key_name
  vpc_security_group_ids      = [aws_security_group.web_sg.id]
  associate_public_ip_address = true

  tags = {
    Name = "tf-ansible-web"
  }
}
```

### 설명

### provider "aws"

```
provider "aws" {
  region = var.aws_region
}
```

Terraform이 AWS API와 통신할 수 있도록 provider를 설정한다.

여기서 지정한 region 값에 따라 리소스가 생성될 위치가 결정된다.

### aws\_security\_group

보안 그룹은 EC2에 들어오고 나가는 트래픽을 제어한다.

```
resource "aws_security_group" "web_sg" {
```

* 리소스 타입은 `aws_security_group`

* 로컬 이름은 `web_sg`

이 이름은 Terraform 코드 내부에서 참조할 때 사용한다.

### SSH 허용 규칙

```
ingress {
  description = "SSH"
  from_port   = 22
  to_port     = 22
  protocol    = "tcp"
  cidr_blocks = ["0.0.0.0/0"]
}
```

* `ingress`는 외부에서 들어오는 트래픽 허용 규칙이다.

* `from_port`, `to_port`는 허용할 포트 범위다.

* `22`는 SSH 포트다.

* `protocol = "tcp"`는 TCP 프로토콜을 의미한다.

* `cidr_blocks = ["0.0.0.0/0"]`는 모든 IP에서 접속 가능하다는 뜻이다.

실습에서는 편의상 전체 허용으로 두었지만, 운영 환경에서는 특정 관리 IP 대역만 허용하는 것이 일반적이다.

### HTTP 허용 규칙

```
ingress {
  description = "HTTP"
  from_port   = 80
  to_port     = 80
  protocol    = "tcp"
  cidr_blocks = ["0.0.0.0/0"]
}
```

웹 브라우저에서 Nginx 기본 페이지에 접속하기 위해 80번 포트를 열어둔다.

### 아웃바운드 허용 규칙

```
egress {
  description = "All outbound"
  from_port   = 0
  to_port     = 0
  protocol    = "-1"
  cidr_blocks = ["0.0.0.0/0"]
}
```

* `egress`는 서버가 외부로 나가는 트래픽 규칙이다.

* `protocol = "-1"`은 모든 프로토콜 허용이다.

* OS 패키지 설치나 업데이트 과정에서 외부 저장소 접근이 필요하므로 전체 허용으로 둔다.

### aws\_instance

```
resource "aws_instance" "web" {
```

EC2 인스턴스를 생성하는 리소스다.

```
ami                         = var.ami_id
instance_type               = var.instance_type
key_name                    = var.key_name
vpc_security_group_ids      = [aws_security_group.web_sg.id]
associate_public_ip_address = true
```

각 항목의 의미는 다음과 같다.

* `ami`  
  어떤 운영체제 이미지를 사용할지 지정한다.

* `instance_type`  
  인스턴스의 CPU/메모리 사양을 지정한다.

* `key_name`  
  접속에 사용할 AWS 키 페어 이름이다.

* `vpc_security_group_ids`  
  이 EC2에 어떤 보안 그룹을 붙일지 지정한다.  
  여기서는 앞에서 만든 `aws_security_group.web_sg.id`를 연결한다.

* `associate_public_ip_address = true`  
  공인 IP를 할당한다.  
  Ansible이 로컬 PC에서 바로 SSH 접속할 것이므로 필요하다.

---

## 8.3 outputs.tf

```
output "public_ip" {
  value = aws_instance.web.public_ip
}

output "public_dns" {
  value = aws_instance.web.public_dns
}
```

### 설명

`output`은 Terraform 실행 결과를 화면에 보여주거나 다른 자동화 단계에서 활용할 수 있도록 값을 외부로 꺼내는 기능이다.

* `public_ip`는 EC2의 공인 IP

* `public_dns`는 EC2의 공인 DNS 이름

이 값은 나중에 Ansible 인벤토리를 작성할 때 사용한다.

---

## 8.4 terraform.tfvars

```
aws_region    = "ap-northeast-2"
ami_id        = "ami-xxxxxxxxxxxxxxxxx"
instance_type = "t2.micro"
key_name      = "my-keypair"
```

### 설명

* `ami_id`는 실습 시점의 Ubuntu AMI로 바꿔야 한다.

* `key_name`은 본인 AWS 계정에 등록된 키 페어 이름으로 바꿔야 한다.

---

## 9. Terraform 실행

`terraform/` 디렉터리로 이동한다.

```
cd terraform
```

### 9.1 초기화

```
terraform init
```

### 설명

`terraform init`은 Terraform 작업 디렉터리를 초기화하는 명령이다.

이 명령을 실행하면 다음이 수행된다.

* provider plugin 다운로드

* `.terraform` 디렉터리 생성

* 작업 환경 초기화

처음 실행할 때 반드시 필요하다.

---

### 9.2 문법 및 구성 검증

```
terraform validate
```

### 설명

* 코드 문법이 올바른지 검사한다.

* 필수 인자가 빠졌는지 확인한다.

* 인프라를 실제로 생성하지는 않는다.

---

### 9.3 실행 계획 확인

```
terraform plan
```

### 설명

현재 코드 기준으로 어떤 리소스가 생성될지 미리 보여준다.

중요한 이유는 다음과 같다.

* 실수로 불필요한 자원이 생성되는지 확인 가능

* 포트 개방이나 태그 설정 등을 사전 점검 가능

* 실제 apply 전에 변경 내용을 검토 가능

---

### 9.4 리소스 생성

```
terraform apply -auto-approve
```

### 설명

* `apply`는 실제 리소스를 생성한다.

* `auto-approve`는 중간 승인 질문을 생략한다.

실습 중에는 편리하지만, 운영 환경에서는 승인 과정을 남겨두는 경우도 많다.

---

### 9.5 출력값 확인

```
terraform output
```

또는 특정 출력값만 확인할 수도 있다.

```
terraform output public_ip
```

### 예시 결과

```
public_ip="3.37.xxx.xxx"
public_dns="ec2-3-37-xxx-xxx.ap-northeast-2.compute.amazonaws.com"
```

이 `public_ip` 값을 Ansible 인벤토리에 넣을 것이다.

---

## 10. Ansible 설정

이제 생성된 EC2에 Ansible이 접속해서 Nginx를 설치하도록 구성한다.

`ansible/` 디렉터리로 이동한다.

```
cd ../ansible
```

---

## 10.1 inventory.ini

```
[web]
3.37.xxx.xxx ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/my-keypair.pem
```

### 설명

### [web]

```
[web]
```

Ansible 그룹 이름이다.

이 그룹 아래에 속한 서버들에 대해 playbook을 실행할 수 있다.

### 호스트 항목

```
3.37.xxx.xxx ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/my-keypair.pem
```

의미는 다음과 같다.

* `3.37.xxx.xxx`  
  Terraform이 생성한 EC2의 공인 IP

* `ansible_user=ubuntu`  
  SSH 접속 사용자  
  Ubuntu AMI에서는 일반적으로 `ubuntu` 계정을 사용한다.

* `ansible_ssh_private_key_file=~/.ssh/my-keypair.pem`  
  접속에 사용할 개인 키 파일 경로  
  AWS 키 페어 생성 시 다운로드 받은 `.pem` 파일을 지정한다.

### 왜 인벤토리가 필요한가

Ansible은 기본적으로 “어느 서버에 접속할 것인가”를 알아야 한다.

그 정보를 저장하는 파일이 인벤토리다.

즉, Terraform은 서버를 만들고, Ansible 인벤토리는 그 서버의 접속 정보를 담는다.

---

## 10.2 ansible.cfg

```
[defaults]
inventory = ./inventory.ini
host_key_checking = False
```

### 설명

* `inventory = ./inventory.ini`  
  기본 인벤토리 파일 위치를 지정한다.

* `host_key_checking = False`  
  SSH 최초 접속 시 known\_hosts 확인으로 인한 인터랙션을 줄인다.

실습에서는 편리하지만, 운영 환경에서는 SSH host key 검증을 켜두는 것이 더 안전하다.

---

## 10.3 playbook.yml

```
- name: Install and start Nginx
  hosts: web
  become: yes

  tasks:
    - name: Update apt cache
      apt:
        update_cache: yes

    - name: Install nginx
      apt:
        name: nginx
        state: present

    - name: Enable nginx service
      systemd:
        name: nginx
        enabled: yes

    - name: Start nginx service
      systemd:
        name: nginx
        state: started
```

### 설명

이 playbook은 `web` 그룹에 속한 서버를 대상으로 실행된다.

### hosts: web

```
hosts: web
```

인벤토리의 `[web]` 그룹에 정의된 서버를 대상으로 한다.

### become: yes

```
become: yes
```

관리자 권한으로 작업한다는 뜻이다.

패키지 설치나 서비스 제어는 보통 root 권한이 필요하므로 거의 필수다.

---

### task 1: apt 캐시 갱신

```
- name: Update apt cache
  apt:
    update_cache: yes
```

Ubuntu 계열 시스템에서 패키지 목록을 최신 상태로 갱신한다.

직접 명령으로 치면 다음과 비슷한 역할이다.

```
sudo apt update
```

Ansible의 `apt` 모듈을 사용하면 직접 셸 명령을 쓰지 않고도 패키지 관리 작업을 선언적으로 수행할 수 있다.

---

### task 2: Nginx 설치

```
- name: Install nginx
  apt:
    name: nginx
    state: present
```

* `name: nginx`는 설치할 패키지 이름

* `state: present`는 해당 패키지가 설치된 상태가 되도록 보장한다는 의미

이미 설치되어 있다면 다시 설치하지 않는다.

이 특성이 Ansible의 중요한 특징인 **멱등성**이다.

---

### task 3: 서비스 활성화

```
- name: Enable nginx service
  systemd:
    name: nginx
    enabled: yes
```

이 설정은 시스템 부팅 후에도 Nginx가 자동으로 시작되도록 만든다.

직접 명령으로 치면 다음과 유사하다.

```
sudo systemctl enable nginx
```

---

### task 4: 서비스 시작

```
- name: Start nginx service
  systemd:
    name: nginx
    state: started
```

Nginx 서비스를 즉시 시작한다.

직접 명령으로 치면 다음과 비슷하다.

```
sudo systemctl start nginx
```

## 11. Ansible 접속 확인

playbook 실행 전에 먼저 접속이 되는지 확인한다.

```
ansible all -m ping
```

### 설명

* `all`은 인벤토리의 모든 호스트 대상

* `m ping`은 Ansible ping 모듈 실행

이 명령은 일반적인 ICMP ping이 아니다.

실제로는 SSH 접속이 가능하고, 원격 Python 실행 환경이 정상인지 확인하는 테스트에 가깝다.

### 성공 예시

```
3.37.xxx.xxx | SUCCESS=> {
"changed":false,
"ping":"pong"
}
```

이 결과가 나오면 Ansible이 해당 서버에 정상 접속할 수 있다는 뜻이다.

---

## 12. Ansible Playbook 실행

```
ansible-playbook playbook.yml
```

### 설명

이 명령을 실행하면 playbook에 작성된 작업이 순서대로 실행된다.

실행 순서는 다음과 같다.

1. SSH로 서버 접속

2. sudo 권한 확보

3. apt 캐시 갱신

4. nginx 설치

5. 서비스 활성화

6. 서비스 시작

### 실행 후 확인

브라우저에서 다음 주소로 접속한다.

```
http://EC2_PUBLIC_IP
```

정상이라면 Nginx 기본 페이지가 보인다.

---

## 13. Terraform 출력값과 Ansible을 연결하는 방식

앞에서는 Terraform output을 보고 사람이 직접 인벤토리에 IP를 넣었다.

이 방식은 학습용으로는 매우 좋다. 흐름이 눈에 잘 보이기 때문이다.

하지만 실무에서는 수동 입력을 줄이기 위해 자동 연결을 많이 사용한다.

대표적인 방식은 다음과 같다.

### 방식 1. Terraform output을 보고 수동으로 inventory 작성

가장 단순하다.

교육용, 개념 이해용으로 적합하다.

장점:

* 흐름이 명확함

* 수강생이 Terraform output의 의미를 쉽게 이해함

단점:

* 서버 수가 많아지면 번거로움

* 자동화 수준이 낮음

### 방식 2. Terraform output 값을 파일로 저장한 뒤 인벤토리 자동 생성

예를 들어 `terraform output -raw public_ip` 값을 받아 inventory 파일을 자동 생성할 수 있다.

예시:

```
cd terraform
PUBLIC_IP=$(terraform output -raw public_ip)

cd ../ansible
cat > inventory.ini<<EOF
[web]
$PUBLIC_IP ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/my-keypair.pem
EOF
```

이 방식은 매우 자주 사용된다.

### 방식 3. Terraform에서 local-exec로 인벤토리 파일 생성

Terraform 실행 중 로컬에서 명령을 실행해 Ansible inventory 파일을 만들 수도 있다.

예시는 다음과 같다.

```
resource "local_file" "ansible_inventory" {
  content = <<EOT
[web]
${aws_instance.web.public_ip} ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/my-keypair.pem
EOT

  filename = "../ansible/inventory.ini"
}
```

이 방식은 Terraform 결과가 곧바로 Ansible 입력으로 이어진다는 점에서 편리하다.

다만 Terraform 코드 안에 다른 도구용 파일 생성 로직이 섞이므로, 프로젝트 규모가 커지면 별도 스크립트나 CI/CD 단계로 분리하는 경우도 많다.

---

## 14. 확장 실습: 웹 페이지 내용까지 변경하기

Nginx만 설치하면 기본 페이지가 보인다.

여기서 한 단계 더 나아가서 index.html 파일을 배포해보자.

## 14.1 playbook.yml 수정

```
- name: Install and configure Nginx
  hosts: web
  become: yes

  tasks:
    - name: Update apt cache
      apt:
        update_cache: yes

    - name: Install nginx
      apt:
        name: nginx
        state: present

    - name: Deploy custom index page
      copy:
        dest: /var/www/html/index.html
        content:|
          <html>
          <head><title>Terraform + Ansible</title></head>
          <body>
            <h1>Provisioned by Terraform</h1>
            <h2>Configured by Ansible</h2>
          </body>
          </html>

    - name: Enable nginx service
      systemd:
        name: nginx
        enabled: yes

    - name: Start nginx service
      systemd:
        name: nginx
        state: started
```

### 설명

여기서 새롭게 등장한 모듈은 `copy`다.

```
copy:
  dest: /var/www/html/index.html
  content:|
```

* `dest`는 원격 서버에 저장할 경로

* `content`는 파일 내용을 직접 문자열로 작성하는 방식

이 모듈을 사용하면 별도 파일 없이도 간단한 설정 파일이나 HTML 파일을 배포할 수 있다.

브라우저에서 다시 접속하면 사용자 정의 페이지가 보인다.

---

## 15. 실무에서는 어떤 형태로 발전하는가

이번 실습은 EC2 한 대에 Nginx를 설치하는 매우 단순한 구조다.

하지만 실무에서는 이 구조가 다음처럼 발전한다.

### 15.1 여러 서버 동시 구성

예를 들어 웹 서버 3대, 배치 서버 2대, DB 서버 1대를 만든다고 하자.

Terraform은 각 서버를 생성하고, Ansible은 그룹별로 다른 playbook을 적용한다.

예시 인벤토리:

```
[web]
10.0.1.10
10.0.1.11
10.0.1.12

[batch]
10.0.2.10
10.0.2.11

[db]
10.0.3.10
```

이렇게 되면 같은 인프라 생성 코드 위에서 역할별 구성을 분리할 수 있다.

### 15.2 환경별 분리

* dev

* staging

* prod

환경마다 Terraform 변수와 Ansible 변수 파일을 다르게 가져가면 된다.

예를 들어:

* Terraform은 인스턴스 수, 크기, 네트워크를 환경별로 다르게 생성

* Ansible은 환경별 설정 파일, API endpoint, 로그 수준 등을 다르게 배포

### 15.3 CI/CD 파이프라인 연결

실무에서는 사람이 로컬에서 수동 실행하는 대신 다음 흐름으로 연결한다.

1. Git 저장소에 Terraform 코드와 Ansible 코드 저장

2. CI/CD 도구가 Terraform apply 실행

3. 생성된 출력값을 기반으로 인벤토리 생성

4. Ansible playbook 자동 실행

5. 배포 결과 검증

즉, Terraform과 Ansible의 연계는 단순 실습용 조합이 아니라 실제 운영 자동화의 핵심 기반이 될 수 있다.

---

## 16. 수강생이 자주 헷갈리는 부분

### 16.1 Terraform이 서버 안으로 접속해서 설정하는 도구인가

아니다.

Terraform의 핵심은 서버 내부 구성보다 인프라 생성과 상태 관리에 있다.

### 16.2 Ansible이 VM도 만들 수 있는가

일부 클라우드 모듈을 통해 가능은 하다.

하지만 일반적으로 인프라 생성은 Terraform이 더 구조적이고 선언적이며 상태 관리에 유리하다.

### 16.3 user\_data와 Ansible의 차이는 무엇인가

`user_data`는 인스턴스 최초 부팅 시 실행되는 초기화 스크립트다.

빠르게 부트스트랩할 때 유용하다.

하지만 다음 한계가 있다.

* 최초 부팅 시점 중심

* 재실행 및 변경 관리가 불편할 수 있음

* 구조화된 구성 관리에는 한계가 있음

반면 Ansible은 다음에 강하다.

* 반복 실행 가능

* 상태 기반 관리 가능

* 역할(Role), 변수, 템플릿으로 구조화 가능

실무에서는 `user_data`로 최소한의 초기 준비를 하고, 본격적인 구성은 Ansible이 담당하는 경우도 많다.

---

## 17. 정리

이번 장의 핵심은 다음이다.

Terraform과 Ansible은 경쟁 관계가 아니라 **서로 다른 계층을 담당하는 협업 도구**다.

* Terraform은 인프라를 만든다.

* Ansible은 그 인프라를 운영 가능한 상태로 구성한다.

즉, 두 도구를 함께 사용하면 다음 자동화 흐름이 완성된다.

1. Terraform으로 서버 생성

2. Terraform output으로 접속 정보 확보

3. Ansible 인벤토리 구성

4. Ansible playbook 실행

5. 서버 구성 자동화 완료

이 구조를 이해하면 이후에는 다음 주제로 확장하기 쉽다.

* 여러 서버 동시 구성

* 환경별 분리

* 동적 인벤토리

* 애플리케이션 배포 자동화

* CI/CD 연계 자동화

---

## 18. 실습 후 정리 작업

리소스 삭제는 반드시 수행한다.

```
cd terraform
terraform destroy -auto-approve
```

### 설명

* EC2 인스턴스 삭제

* 보안 그룹 삭제

* 생성된 관련 리소스 정리

클라우드 실습에서는 비용 방지를 위해 마지막 정리 단계가 매우 중요하다.

---

## 19. 실습 과제

### 과제 1. Apache로 바꿔보기

현재 playbook은 Nginx를 설치한다.

이를 Apache 설치 playbook으로 바꿔서 웹 페이지가 정상 동작하도록 구성해보자.

수행 조건:

* Nginx 대신 Apache 설치

* 서비스 활성화 및 시작

* 사용자 정의 index.html 배포

### 과제 2. 서버 2대로 확장하기

Terraform 코드에서 EC2를 2대로 늘리고, Ansible inventory에 두 서버를 등록한 뒤 동일 playbook을 적용해보자.

수행 조건:

* EC2 2대 생성

* 두 서버 모두 SSH 접속 가능해야 함

* 두 서버 모두 웹 페이지 정상 동작해야 함

### 과제 3. Terraform output 자동 반영하기

Terraform output 값을 기반으로 inventory 파일을 자동 생성하는 스크립트를 작성해보자.

수행 조건:

* `terraform output -raw public_ip` 사용

* inventory.ini 자동 생성

* 이후 ansible-playbook 실행