---
title: "6장 Terraform으로 AWS 인프라 구성하기"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "배포자동화를 위한 Terraform"]
is_public: true
draft: false
---

# 6장. Terraform으로 AWS 인프라 구성하기

## 장 목표

이 장에서는 Terraform 기본 요소를 사용해서 실제 AWS 인프라를 구성하는 흐름을 학습한다.

이 장을 학습한 뒤에는 다음이 가능해야 한다.

* VPC, Subnet, Internet Gateway, Route Table, Route Table Association의 역할을 설명할 수 있음

* Security Group의 역할을 설명할 수 있음

* Terraform으로 EC2를 포함한 기본 퍼블릭 인프라 구성을 이해할 수 있음

* 리소스 간 참조 방식이 실제 의존 관계를 어떻게 만드는지 설명할 수 있음

* `depends_on`의 의미와 사용 시점을 설명할 수 있음

* `terraform plan` 결과를 읽고 어떤 리소스가 어떤 순서로 만들어질지 해석할 수 있음

* 퍼블릭 서브넷 기반의 기본 네트워크 구성 흐름을 설명할 수 있음

---

## 1. 기본 구성 흐름

이번 장에서 다룰 가장 기본적인 퍼블릭 인프라 구성 흐름은 다음과 같다.

1. VPC 생성

2. Subnet 생성

3. Internet Gateway 생성 후 VPC 연결

4. Route Table 생성

5. 기본 경로 `0.0.0.0/0` 를 Internet Gateway로 연결

6. Route Table을 Subnet에 연결

7. Security Group 생성

8. EC2 생성

이 흐름은 AWS 네트워크 실습의 가장 기본적인 형태다.

즉, “인터넷에 나갈 수 있는 퍼블릭 서브넷에 EC2를 배치하는 구조”다.

---

## 2. VPC

### 2.1 VPC의 역할

VPC는 AWS에서 네트워크의 가장 큰 논리적 경계다.

쉽게 말하면 내가 사용할 사설 네트워크 공간을 정의하는 것이다.

예를 들어 다음처럼 생성할 수 있다.

```
resource "aws_vpc" "main" {
  cidr_block = "10.10.0.0/16"

  tags = {
    Name = "main-vpc"
  }
}
```

이 코드는 `10.10.0.0/16` 대역을 사용하는 VPC를 생성한다.

---

### 2.2 CIDR 블록 의미

`cidr_block = "10.10.0.0/16"` 은 이 VPC가 사용할 전체 IP 범위를 뜻한다.

즉, 이후 생성할 Subnet은 이 범위 안에서 잘라서 사용해야 한다.

예를 들어 다음 같은 서브넷을 만들 수 있다.

* `10.10.1.0/24`

* `10.10.2.0/24`

즉, VPC는 전체 네트워크 범위를 정하고,

Subnet은 그 범위를 더 작게 나눠 사용하는 구조다.

---

## 3. Subnet

### 3.1 Subnet의 역할

Subnet은 VPC 내부를 더 작은 네트워크 단위로 나눈 것이다.

EC2 같은 리소스는 실제로 Subnet 안에 배치된다.

예시:

```
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.10.1.0/24"
  availability_zone       = "ap-northeast-2a"
  map_public_ip_on_launch = true

  tags = {
    Name = "public-subnet-a"
  }
}
```

---

### 3.2 중요한 인자 설명

### `vpc_id`

이 Subnet이 어느 VPC에 속하는지 지정한다.

```
vpc_id = aws_vpc.main.id
```

즉, 앞에서 생성한 `aws_vpc.main` 리소스의 ID를 참조한다.

---

### `cidr_block`

이 Subnet이 사용할 IP 범위다.

```
cidr_block = "10.10.1.0/24"
```

이 값은 반드시 VPC CIDR 범위 안에 있어야 한다.

---

### `availability_zone`

어느 가용 영역에 만들지 지정한다.

```
availability_zone = "ap-northeast-2a"
```

---

### `map_public_ip_on_launch`

이 값이 `true`이면 이 Subnet에 생성되는 인스턴스가 퍼블릭 IP를 자동으로 받을 수 있다.

```
map_public_ip_on_launch = true
```

이 설정이 있다고 해서 바로 인터넷 통신이 되는 것은 아니다.

Internet Gateway와 Route Table 설정도 함께 필요하다.

---

## 4. Internet Gateway

### 4.1 역할

Internet Gateway는 VPC가 인터넷과 통신할 수 있도록 연결해주는 구성 요소다.

예시:

```
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "main-igw"
  }
}
```

이 리소스는 생성과 동시에 특정 VPC에 연결된다.

---

### 4.2 왜 필요한가

퍼블릭 서브넷이라고 해서 자동으로 인터넷 연결이 되는 것은 아니다.

Subnet은 단지 네트워크 구간일 뿐이고,

외부 인터넷으로 나가려면 VPC 자체가 Internet Gateway와 연결되어 있어야 한다.

즉,

* 퍼블릭 IP만 있어도 부족함

* Internet Gateway만 있어도 부족함

* 라우팅까지 연결되어야 실제 인터넷 통신 가능함

---

## 5. Route Table

### 5.1 역할

Route Table은 네트워크 트래픽이 어디로 가야 하는지 규칙을 정의한다.

예시:

```
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "public-rt"
  }
}
```

이 자체로는 단지 라우팅 테이블만 만든 것이다.

실제 인터넷 경로는 별도 route 리소스로 추가한다.

---

### 5.2 기본 인터넷 경로 추가

퍼블릭 서브넷에서 인터넷으로 나가려면

기본 경로 `0.0.0.0/0` 를 Internet Gateway로 보내야 한다.

예시:

```
resource "aws_route" "public_internet_access" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.igw.id
}
```

---

### 5.3 각 인자 설명

### `route_table_id`

어느 Route Table에 경로를 추가할지 지정한다.

### `destination_cidr_block`

목적지 대역이다. `0.0.0.0/0` 는 모든 외부 대역을 의미한다.

### `gateway_id`

그 목적지로 갈 때 어느 게이트웨이를 사용할지 지정한다.

여기서는 Internet Gateway를 사용한다.

---

## 6. Route Table Association

### 6.1 역할

Route Table을 만들고 route까지 넣었다고 끝이 아니다.

그 Route Table이 어떤 Subnet에 적용되는지도 연결해야 한다.

예시:

```
resource "aws_route_table_association" "public_assoc" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}
```

---

### 6.2 왜 필요한가

AWS에서는 Route Table이 존재한다고 해서 모든 Subnet에 자동 적용되지 않는다.

특정 Subnet과 명시적으로 연결되어야 한다.

즉, 퍼블릭 서브넷이 되려면 보통 다음 세 가지가 함께 맞아야 한다.

1. 퍼블릭 IP 할당 가능

2. Internet Gateway 연결 존재

3. 해당 Subnet에 연결된 Route Table에 `0.0.0.0/0 -> IGW` 경로 존재

이 세 가지가 맞아야 실제로 퍼블릭 통신이 가능해진다.

---

## 7. Security Group

### 7.1 역할

Security Group은 인스턴스 수준의 가상 방화벽이다.

인바운드와 아웃바운드 트래픽을 제어한다.

예시:

인라인 방식

```
resource "aws_security_group" "web_sg" {
  name        = "web-sg"
  description = "Allow SSH and HTTP"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "web-sg"
  }
}
```

독립형 방식

```
# 1. 보안 그룹 본체 (껍데기)
resource "aws_security_group" "web_sg" {
  name        = "web-sg"
  description = "Allow SSH and HTTP"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "web-sg"
  }
}

# 2. 인바운드 규칙: SSH (22)
resource "aws_vpc_security_group_ingress_rule" "allow_ssh" {
  security_group_id = aws_security_group.web_sg.id
  description       = "SSH"
  from_port         = 22
  to_port           = 22
  ip_protocol       = "tcp"
  cidr_ipv4         = "0.0.0.0/0"
}

# 3. 인바운드 규칙: HTTP (80)
resource "aws_vpc_security_group_ingress_rule" "allow_http" {
  security_group_id = aws_security_group.web_sg.id
  description       = "HTTP"
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"
  cidr_ipv4         = "0.0.0.0/0"
}

# 4. 아웃바운드 규칙: All Traffic
resource "aws_vpc_security_group_egress_rule" "allow_all_outbound" {
  security_group_id = aws_security_group.web_sg.id
  description       = "All outbound"
  ip_protocol       = "-1" # 모든 프로토콜 및 포트 허용
  cidr_ipv4         = "0.0.0.0/0"
}
```

---

### 7.2 ingress와 egress

### ingress

외부에서 인스턴스로 들어오는 트래픽 규칙이다.

### egress

인스턴스에서 외부로 나가는 트래픽 규칙이다.

초기 실습에서는 다음처럼 이해하면 된다.

* SSH 접속용 22 포트 허용

* 웹 확인용 80 포트 허용

* 외부로 나가는 트래픽은 전체 허용

---

## 8. EC2

### 8.1 역할

EC2는 실제 서버 인스턴스다.

이전까지 만든 네트워크 구성 요소 위에 실제 컴퓨팅 리소스를 배치하는 단계다.

예시:

```
resource "aws_instance" "web" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web_sg.id]
  key_name               = var.key_name

  tags = merge(local.common_tags, {
    Name = var.instance_name
  })
}
```

---

### 8.2 주요 인자 설명

### `ami`

어떤 OS 이미지로 인스턴스를 생성할지 지정한다.

### `instance_type`

인스턴스 사양이다.

### `subnet_id`

어느 Subnet에 배치할지 지정한다.

### `vpc_security_group_ids`

어떤 Security Group을 적용할지 지정한다.

### `key_name`

SSH 접속용 키페어 이름이다.

---

## 9. 리소스 참조

Terraform의 강점 중 하나는 리소스를 문자열로 연결하지 않고

참조로 연결한다는 점이다.

예를 들어 다음 코드를 보자.

```
vpc_id = aws_vpc.main.id
```

이 표현은 단순히 값을 끼워 넣는 것이 아니다.

Terraform에게 다음을 알려준다.

* `aws_subnet.public` 은 `aws_vpc.main` 이 먼저 필요함

* 따라서 생성 순서상 VPC가 먼저 만들어져야 함

즉, 참조는 단순한 값 전달이 아니라 **의존 관계 선언**이기도 하다.

## 10. 참조 기반 의존성

Terraform은 리소스 간 참조를 분석해서 어떤 리소스를 먼저 만들고 나중에 만들어야 하는지를 계산한다.

예를 들어 다음 관계가 있다고 하자.

* Subnet은 VPC ID가 필요함

* Internet Gateway는 VPC ID가 필요함

* Route는 Route Table ID와 IGW ID가 필요함

* EC2는 Subnet ID와 Security Group ID가 필요함

이 경우 Terraform은 자동으로 대략 다음 순서를 계산한다.

1. VPC

2. Subnet / IGW / Route Table / Security Group

3. Route Table Association / Route

4. EC2

즉, Terraform이 대부분의 생성 순서를 자동으로 계산한다.

---

## 11. depends\_on

### 11.1 의미

`depends_on`은 Terraform에게

“이 리소스는 저 리소스가 끝난 뒤에 처리해야 한다”고 명시적으로 알려주는 설정이다.

예시:

```
resource "aws_instance" "web" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web_sg.id]
  key_name               = var.key_name

  depends_on = [
    aws_route.public_internet_access
  ]
}
```

---

### 11.2 언제 쓰는가

보통은 참조만으로 충분하다.

하지만 다음처럼 **직접 참조는 없는데 논리적으로 먼저 준비되어야 하는 경우**에 쓴다.

**EIP**와 **인터넷 게이트웨이(IGW)** 사이의 관계를 코드로 작성할 때

```
# 인터넷 게이트웨이
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
}

# 탄력적 IP (EIP)
resource "aws_eip" "nat_eip" {
  domain = "vpc"
  # 여기에 IGW의 ID를 참조하는 코드가 없음!
}

# NAT 게이트웨이
resource "aws_nat_gateway" "nat_gw" {
  allocation_id = aws_eip.nat_eip.id
  subnet_id     = aws_subnet.public.id
}
```

EIP가 VPC 내부에서 정상적으로 동작하려면(특히 NAT 게이트웨이용으로 쓰이려면), 해당 VPC에 IGW가 붙어 있는 상태여야 API 호출이 성공함.

순서가 꼬이면 다음과 같은 일이 발생함.

1. 테라폼이 IGW와 EIP 생성을 동시에 요청함.

2. AWS가 IGW를 붙이는 동안, EIP 생성이 먼저 끝나거나 혹은 IGW가 채 붙기도 전에 EIP 관련 설정이 진행됨.

3. 결과적으로 "VPC에 인터넷 경로가 없어서 설정을 완료할 수 없다"는 식의 에러를 뱉으며 멈춰버림.

따라서, 다음 코드처럼 IGW 생성 후에 EIP가 할당되도록 할 수 있음.

```
resource "aws_eip" "nat_eip" {
  domain     = "vpc"
  depends_on = [aws_internet_gateway.igw] # "IGW가 다 만들어질 때까지 기다려!"
}
```

---

### 11.3 주의점

`depends_on`은 필요할 때만 써야 한다.

Terraform은 원래 참조 기반으로 의존성을 잘 계산하므로,

무조건 많이 넣는 방식은 오히려 코드 가독성을 해칠 수 있다.

즉,

* 참조로 표현 가능하면 참조를 우선 사용

* 참조로 드러나지 않는 논리적 선후관계가 있을 때만 `depends_on` 사용

이 원칙이 좋다.

---

## 12. plan 결과 해석

### 12.1 왜 plan 해석이 중요한가

Terraform은 선언형 도구이기 때문에

코드를 썼다고 바로 apply부터 하는 습관은 좋지 않다.

항상 `terraform plan` 결과를 보고 다음을 확인해야 한다.

* 어떤 리소스가 생성되는가

* 어떤 값이 들어가는가

* 변경인지 생성인지 삭제인지

* 예상한 구조와 맞는가

---

### 12.2 plan에서 확인할 것

예를 들어 이번 장의 구성을 plan하면 다음 같은 리소스들이 보일 것이다.

* `aws_vpc.main`

* `aws_subnet.public`

* `aws_internet_gateway.igw`

* `aws_route_table.public`

* `aws_route.public_internet_access`

* `aws_route_table_association.public_assoc`

* `aws_security_group.web_sg`

* `aws_instance.web`

즉, plan 결과를 보면

Terraform이 지금 어떤 인프라 구조를 이해하고 있는지 확인할 수 있다.

---

### 12.3 plan은 설계 검토 단계다

`terraform plan`은 단순 미리보기가 아니라

실제 설계 검토 단계라고 보는 것이 더 맞다.

즉, 다음을 확인해야 한다.

* CIDR 범위가 맞는가

* 리전과 AZ가 맞는가

* Security Group 포트가 맞는가

* Key pair 이름이 맞는가

* EC2가 원하는 Subnet에 배치되는가

이 확인 없이 apply하면 불필요한 비용이나 잘못된 구성이 생길 수 있다.

---

## 13. 퍼블릭 인프라 조합 흐름 정리

이번 장에서 구성하는 기본 퍼블릭 인프라 흐름은 아래처럼 정리할 수 있다.

### 네트워크 계층

* VPC 생성

* 퍼블릭 Subnet 생성

### 인터넷 연결 계층

* Internet Gateway 생성 및 연결

* Route Table 생성

* 기본 경로를 IGW로 연결

* Route Table을 Subnet에 연결

### 보안 계층

* Security Group 생성

* 필요한 포트만 허용

### 컴퓨팅 계층

* AMI 조회

* EC2 생성

* Subnet과 Security Group 연결

즉, AWS 인프라는 개별 리소스를 따로따로 만드는 것이 아니라

**네트워크, 라우팅, 보안, 컴퓨팅을 조합해서 하나의 구조로 만드는 것**이다.

Terraform은 이 구조를 코드로 선언하는 도구다.

---

## 15. 장 정리

이 장에서는 Terraform을 이용해 AWS의 기본 퍼블릭 인프라를 구성하는 흐름을 정리했다.

핵심은 다음과 같다.

* VPC는 전체 네트워크 범위다.

* Subnet은 VPC를 나눈 실제 배치 구간이다.

* Internet Gateway는 VPC의 인터넷 연결 지점이다.

* Route Table과 Route는 트래픽 경로를 정의한다.

* Route Table Association은 특정 Subnet에 라우팅 규칙을 적용한다.

* Security Group은 인스턴스 수준의 방화벽이다.

* EC2는 이 모든 구성 위에 배치되는 실제 서버다.

* 리소스 참조는 값 전달이면서 동시에 의존 관계 선언이다.

* Terraform은 참조를 바탕으로 생성 순서를 계산한다.

* 필요할 때는 `depends_on`으로 명시적 의존성을 줄 수 있다.

즉, Terraform은 단일 리소스 생성 도구가 아니라 **여러 AWS 리소스를 구조적으로 연결하는 도구다.**

---

# 실습 6. Terraform으로 AWS 퍼블릭 인프라 구성하기

## 실습 목표

이 실습에서는 다음을 확인한다.

* Terraform으로 VPC, Subnet, Internet Gateway, Route Table, Route Table Association 생성

* Security Group 생성

* 최신 AMI 조회 후 EC2 생성

* 리소스 참조를 통한 의존 관계 이해

* `terraform plan`과 `terraform apply` 결과 확인

---

## 실습 구성 개요

이번 실습은 서울 리전에서 다음 구성을 만든다.

* VPC 1개

* 퍼블릭 Subnet 1개

* Internet Gateway 1개

* Route Table 1개

* 기본 인터넷 경로 1개

* Route Table Association 1개

* Security Group 1개

* EC2 1개

즉, 인터넷 접속이 가능한 가장 기본적인 퍼블릭 EC2 실습이다.

---

## 실습 1. 프로젝트 파일 구성

### 디렉터리 구조 예시

```
terraform-aws-network-lab/
├── main.tf
├── variables.tf
├── locals.tf
├── outputs.tf
├── terraform.tfvars
├── .terraform.lock.hcl
└── .terraform/
```

---

## 실습 2. 변수 정의

### `variables.tf`

```
variable "region" {
  type        = string
  description = "AWS region"
  default     = "ap-northeast-2"
}

variable "vpc_cidr" {
  type        = string
  description = "VPC CIDR block"
  default     = "10.10.0.0/16"
}

variable "public_subnet_cidr" {
  type        = string
  description = "Public subnet CIDR block"
  default     = "10.10.1.0/24"
}

variable "availability_zone" {
  type        = string
  description = "Availability Zone for public subnet"
  default     = "ap-northeast-2a"
}

variable "instance_type" {
  type        = string
  description = "EC2 instance type"
  default     = "t3.micro"
}

variable "instance_name" {
  type        = string
  description = "EC2 Name tag"
  default     = "tf-web-01"
}

variable "key_name" {
  type        = string
  description = "Existing AWS key pair name for SSH access"
}
```

---

## 실습 3. 로컬값 정의

### `locals.tf`

```
locals {
  common_tags = {
    Environment = "lab"
    Project     = "terraform-network"
    ManagedBy   = "terraform"
  }
}
```

---

## 실습 4. 실제 인프라 코드 작성

### `main.tf`

```
terraform {
  required_version = ">= 1.5.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

data "aws_ami" "amazon_linux" {
  most_recent = true

  owners = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
}

resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidr

  tags = merge(local.common_tags, {
    Name = "main-vpc"
  })
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidr
  availability_zone       = var.availability_zone
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, {
    Name = "public-subnet-a"
  })
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id

  tags = merge(local.common_tags, {
    Name = "main-igw"
  })
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  tags = merge(local.common_tags, {
    Name = "public-rt"
  })
}

resource "aws_route" "public_internet_access" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.igw.id
}

resource "aws_route_table_association" "public_assoc" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "web_sg" {
  name        = "web-sg"
  description = "Allow SSH and HTTP"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "web-sg"
  })
}

resource "aws_instance" "web" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web_sg.id]
  key_name               = var.key_name

  depends_on = [
    aws_route.public_internet_access
  ]

  tags = merge(local.common_tags, {
    Name = var.instance_name
  })
}
```

---

## 실습 5. 출력값 정의

### `outputs.tf`

```
output "vpc_id" {
  description = "Created VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_id" {
  description = "Created public subnet ID"
  value       = aws_subnet.public.id
}

output "security_group_id" {
  description = "Created security group ID"
  value       = aws_security_group.web_sg.id
}

output "instance_id" {
  description = "Created EC2 instance ID"
  value       = aws_instance.web.id
}

output "instance_public_ip" {
  description = "Created EC2 public IP"
  value       = aws_instance.web.public_ip
}
```

---

## 실습 6. 변수값 입력

### `terraform.tfvars`

```
key_name = "my-keypair"
```

---

### 설명

여기서 `key_name`은 반드시 AWS 계정에 이미 존재하는 키페어 이름이어야 한다.

존재하지 않는 키 이름을 넣으면 EC2 생성 단계에서 오류가 발생한다.

AWS 콘솔에서 미리 키페어를 생성해두거나,

CLI로 다음 명령을 사용해 확인할 수 있다.

```
aws ec2 describe-key-pairs --region ap-northeast-2
```

---

## 실습 7. 실행 순서

```
terraform init
terraform fmt
terraform validate
terraform plan
terraform apply -auto-approve
terraform output
```

---

## 실습 8. plan 결과에서 확인할 포인트

`terraform plan` 결과를 볼 때 다음을 확인한다.

* VPC가 새로 생성되는지

* 퍼블릭 Subnet이 올바른 CIDR과 AZ로 생성되는지

* Internet Gateway와 Route Table이 생성되는지

* `0.0.0.0/0` 경로가 Internet Gateway로 향하는지

* Security Group에 22, 80 포트가 열리는지

* EC2가 올바른 Subnet과 Security Group에 연결되는지

즉, plan은 단순히 “몇 개 만든다”가 아니라

**내가 설계한 인프라 구조가 코드대로 표현되고 있는지 확인하는 단계**다.

---

## 실습 9. 접속 및 확인

EC2가 생성된 뒤 퍼블릭 IP를 확인한다.

```
terraform output instance_public_ip
```

SSH 접속 예시:

```
ssh -i /path/to/my-keypair.pem ec2-user@<PUBLIC_IP>
```

Amazon Linux 2023 계열에서는 기본 사용자 이름으로 `ec2-user`를 사용한다.

---

## 실습 11. 리소스 정리

실습이 끝났으면 반드시 삭제한다.

```
terraform destroy -auto-approve
```

이 명령은 Terraform state에 기록된 리소스를 기준으로 생성한 인프라를 삭제한다.

즉, 이번 실습에서 생성한 다음 리소스가 삭제 대상이 된다.

* VPC

* Subnet

* Internet Gateway

* Route Table

* Route Table Association

* Security Group

* EC2