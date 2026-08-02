---
title: "8장 Terraform 모듈화와 재사용 구조"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "배포자동화를 위한 Terraform"]
is_public: true
draft: false
---

# 8장. Terraform 모듈화와 재사용 구조

## 장 목표

이 장에서는 Terraform 코드의 재사용성과 유지보수성을 높이기 위한 핵심 개념인 **모듈(module)** 을 학습한다.

앞 장까지는 하나의 디렉터리 안에서 `main.tf`, `variables.tf`, `outputs.tf`, `locals.tf` 같은 파일을 나눠 관리하는 수준까지 왔다. 이 정도만으로도 소규모 실습은 충분히 가능하다. 하지만 실제 인프라 코드가 커지면 파일 분리만으로는 한계가 생긴다.

예를 들어 다음과 같은 상황을 생각해볼 수 있다.

* 같은 형태의 VPC 구성을 여러 프로젝트에서 반복 사용해야 함

* 같은 방식의 EC2 구성을 여러 환경에서 재사용해야 함

* 개발, 스테이징, 운영 환경에서 구조는 같고 값만 달라야 함

* 팀 내 공통 네트워크 모듈을 여러 서비스 팀이 함께 사용해야 함

* `main.tf` 파일이 너무 커져서 읽기 어려워짐

이런 문제를 해결하기 위해 Terraform은 **모듈화** 기능을 제공한다.

* 모듈의 의미와 역할을 설명할 수 있음

* root module과 child module의 차이를 설명할 수 있음

* module 블록의 기본 구조를 설명할 수 있음

* 모듈 입력값과 출력값의 흐름을 설명할 수 있음

* 모듈 디렉터리 구조를 설계할 수 있음

* 모듈화 전후 코드 차이를 설명할 수 있음

* 재사용 가능한 Terraform 코드 구조를 이해할 수 있음

---

## 1. 왜 모듈화가 필요한가

Terraform 입문 단계에서는 보통 리소스를 직접 작성한다.

예를 들어 다음처럼 VPC를 만들고, Subnet을 만들고, Security Group과 EC2를 하나의 디렉터리 안에서 모두 관리할 수 있다.

```
resource "aws_vpc" "main" {
  cidr_block = "10.10.0.0/16"
}

resource "aws_subnet" "public" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.10.1.0/24"
}

resource "aws_security_group" "web_sg" {
  vpc_id = aws_vpc.main.id
}

resource "aws_instance" "web" {
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web_sg.id]
}
```

소규모 실습에서는 이 방식이 단순하고 이해하기 쉽다.

하지만 실제 환경에서는 다음 문제가 생긴다.

* 같은 코드를 복사해서 다른 프로젝트에 붙여넣게 됨

* 값만 다르고 구조는 같은 코드가 여러 군데 생김

* 수정이 필요할 때 모든 파일을 각각 수정해야 함

* 코드 중복이 증가함

* 공통 구조를 표준화하기 어려움

즉, 코드가 커질수록 중요한 것은 **어떻게 같은 구조를 반복 사용하고 관리할 것인가**가 된다.

이때 모듈이 필요하다.

---

## 2. 모듈이란 무엇인가

[![](8%EC%9E%A5%20Terraform%20%EB%AA%A8%EB%93%88%ED%99%94%EC%99%80%20%EC%9E%AC%EC%82%AC%EC%9A%A9%20%EA%B5%AC%EC%A1%B0/image.png)](8%EC%9E%A5%20Terraform%20%EB%AA%A8%EB%93%88%ED%99%94%EC%99%80%20%EC%9E%AC%EC%82%AC%EC%9A%A9%20%EA%B5%AC%EC%A1%B0/image.png)

Terraform 모듈은 단일 디렉터리에 있는 Terraform 설정 파일들의 집합이다. 하나 이상의 `.tf`파일이 있는 단일 디렉터리로 구성된 간단한 설정이라도 모듈에 해당한다. 이러한 디렉터리에서 Terraform 명령을 직접 실행하면 해당 디렉터리가 **루트 모듈** 로 간주된다 . 따라서 모든 Terraform 설정은 모듈의 일부라고 할 수 있다.

예를 들어 다음을 하나의 모듈로 만들 수 있다.

* VPC + Subnet + Route Table + Internet Gateway

* EC2 + Security Group

* ALB + Target Group + Listener

* S3 버킷 + 정책 + 버전 관리 설정

즉, Terraform에서 모듈은 **관련된 리소스들을 하나의 묶음으로 캡슐화한 재사용 가능한 구성 단위**다.

---

## 3. root module과 child module

## 3.1 root module

사용자가 현재 실행하는 Terraform 디렉터리 자체를 root module이라고 한다.

예를 들어 현재 디렉터리에 다음 파일들이 있다고 하자.

```
project-a/
├── main.tf
├── variables.tf
├── outputs.tf
└── terraform.tfvars
```

여기서 `terraform init`, `terraform plan`, `terraform apply`를 실행하는 이 디렉터리 전체가 root module이다.

즉, Terraform CLI가 직접 실행되는 대상이 root module이다.

---

## 3.2 child module

root module 안에서 `module` 블록을 사용해 불러오는 별도 디렉터리의 Terraform 구성을 child module이라고 한다.

예를 들어 다음 구조가 있다고 하자.

```
project-a/
├── main.tf
└── modules/
    └── network/
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

이때 `modules/network` 디렉터리는 child module이 된다. modules 디렉토리는 고정된 디렉토리명이 아니지만 모듈을 모아둔 디렉토리임을 명시하기 위해 일반적으로 사용됨.

즉, root module이 child module을 호출해서 사용하는 구조다.

---

## 3.3 쉽게 비유하면

* root module → 메인 작업 공간

* child module → 재사용 가능한 부품

즉, root module은 전체 인프라를 만드는 역할을 하고,

child module은 재사용 가능한 부품을 제공한다.

---

## 4. module 블록 기본 구조

Terraform에서 모듈을 사용할 때는 `module` 블록을 쓴다.

기본 구조는 다음과 같다.

```
module "이름" {
  source = "모듈경로"

  입력변수1 = 값
  입력변수2 = 값
}
```

예시:

```
module "network" {
  source = "./modules/network"

  vpc_cidr           = "10.10.0.0/16"
  public_subnet_cidr = "10.10.1.0/24"
  availability_zone  = "ap-northeast-2a"
}
```

이 코드는 `./modules/network` 디렉터리에 있는 Terraform 구성을 불러와 사용한다는 뜻이다.

---

## 5. source의 의미

`source`는 모듈 코드를 어디서 가져올지 지정하는 값이다.

가장 기본적인 예시는 로컬 경로다.

```
source = "./modules/network"
```

즉, 현재 root module 기준으로 `modules/network` 디렉터리에 있는 모듈을 사용하겠다는 뜻이다.

실무에서는 로컬 경로 외에도 다음 같은 source를 사용할 수 있다.

* 다른 Git 저장소

* Terraform Registry

* 사내 표준 모듈 저장소

하지만 입문 단계에서는 로컬 경로 기반 child module부터 이해하는 것이 가장 좋다.

---

## 6. 모듈 입력값과 출력값

모듈은 함수처럼 생각하면 이해가 빠르다.

* variable → 모듈 입력값

* output → 모듈 출력값

즉, root module은 child module에 값을 넘기고,

child module은 필요한 값을 다시 root module에 반환할 수 있다.

---

## 6.1 입력값

child module 안에 다음처럼 변수가 선언되어 있다고 하자.

```
variable "vpc_cidr" {
  type = string
}
```

그러면 root module에서는 module 블록에서 이 값을 넘길 수 있다.

```
module "network" {
  source   = "./modules/network"
  vpc_cidr = "10.10.0.0/16"
}
```

즉, module 블록 안의 인자는 child module의 variable에 대응된다.

---

## 6.2 출력값

child module 안에 다음 output이 있다고 하자.

```
output "vpc_id" {
  value = aws_vpc.main.id
}
```

그러면 root module에서는 이 값을 다음처럼 참조할 수 있다.

```
module.network.vpc_id
```

즉, module 출력값은 `module.모듈이름.출력명` 형식으로 접근한다.

---

## 6.3 흐름 요약

모듈의 데이터 흐름은 다음과 같다.

1. root module이 child module에 입력값 전달

2. child module 내부에서 리소스 생성

3. child module이 output으로 결과 노출

4. root module이 그 값을 참조

이 흐름을 이해하면 모듈은 훨씬 단순하게 보인다.

---

## 7. 모듈 디렉터리 구조

입문 단계에서 가장 많이 사용하는 child module 구조는 다음과 같다.

```
modules/
└── network/
    ├── main.tf
    ├── variables.tf
    └── outputs.tf
```

각 파일의 역할은 root module과 동일하다.

### `main.tf`

실제 리소스 정의

### `variables.tf`

모듈 입력 변수 선언

### `outputs.tf`

모듈이 밖으로 노출할 값 정의

즉, child module도 하나의 독립된 Terraform 구성처럼 동작한다.

---

## 8. 모듈화 전후 비교

## 8.1 모듈화 전

모든 코드를 root module에 직접 작성하는 구조다.

```
resource "aws_vpc" "main" {
  cidr_block = "10.10.0.0/16"
}

resource "aws_subnet" "public" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.10.1.0/24"
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
}
```

이 구조는 작을 때는 괜찮지만,

리소스가 많아질수록 코드가 길어지고 역할 구분이 어려워진다.

---

## 8.2 모듈화 후

네트워크 구성을 child module로 분리한 구조다.

### root module

```
module "network" {
  source = "./modules/network"

  vpc_cidr           = "10.10.0.0/16"
  public_subnet_cidr = "10.10.1.0/24"
  availability_zone  = "ap-northeast-2a"
}
```

### child module 내부

VPC, Subnet, IGW, Route Table 등을 모두 포함

이렇게 되면 root module은 전체 인프라 조립에 집중하고,

세부 구현은 child module이 담당하게 된다.

즉, 모듈화는 코드를 줄이는 것보다 **책임을 분리하는 것**에 더 가깝다.

---

## 9. 모듈의 장점

모듈화는 다음 장점을 가진다.

### 9.1 재사용성

같은 네트워크 모듈을 여러 프로젝트에서 재사용할 수 있다.

예:

* 프로젝트 A에서 사용

* 프로젝트 B에서 사용

* 환경만 다르게 적용

---

### 9.2 일관성

모든 팀이 같은 표준 모듈을 사용하면 구조가 일관된다.

예:

* VPC naming 규칙 통일

* 공통 태그 정책 적용

* 공통 Security Group 패턴 재사용

---

### 9.3 유지보수성

네트워크 정책이 바뀌면 모듈 수정만으로 여러 구성에 반영할 수 있다.

물론 적용 범위와 버전 관리는 신중해야 하지만, 기본적으로 중복 수정이 줄어든다.

---

### 9.4 가독성

root module에서는 전체 아키텍처 흐름이 더 잘 보인다.

예:

```
module "network" { ... }
module "compute" { ... }
module "database" { ... }
```

이렇게 되면 “무엇을 조립하는가”가 명확해진다.

---

## 10. 모듈 입력값 설계

입력값 설계를 잘못하면 오히려 사용하기 어려운 모듈이 된다.

좋은 입력값 설계의 기본은 다음과 같다.

* 너무 많은 세부값을 강제로 노출하지 않음

* 사용자 입장에서 바꿔야 할 값만 변수로 뺌

* 공통으로 고정 가능한 값은 모듈 내부에 둠

* description을 잘 적음

* 타입을 명확히 지정함

예를 들어 network 모듈이라면 보통 다음 정도는 입력으로 받을 수 있다.

* `vpc_cidr`

* `public_subnet_cidr`

* `availability_zone`

즉, 모듈 입력값은 많다고 좋은 것이 아니라

**사용자가 조정해야 할 핵심만 적절히 노출하는 것**이 중요하다.

---

## 11. 모듈 출력값 설계

출력값도 마찬가지다.

모듈 내부의 모든 값을 다 output으로 내보낼 필요는 없다.

보통 다음처럼 **다음 단계에서 실제로 필요한 값**만 output으로 내보낸다.

예:

* `vpc_id`

* `public_subnet_id`

* `security_group_id`

* `instance_id`

* `instance_public_ip`

즉, output은 **다른 모듈이나 root module이 실제로 사용할 값** 위주로 설계하는 것이 좋다.

## 12. 모듈 간 연결

Terraform에서는 한 모듈의 output을 다른 모듈의 입력값으로 연결할 수 있다.

예를 들어 다음처럼 가능하다.

```
module "network" {
  source = "./modules/network"

  vpc_cidr           = "10.10.0.0/16"
  public_subnet_cidr = "10.10.1.0/24"
  availability_zone  = "ap-northeast-2a"
}

module "compute" {
  source = "./modules/compute"

  subnet_id = module.network.public_subnet_id
  vpc_id    = module.network.vpc_id
}
```

즉,

* `network` 모듈이 VPC와 Subnet 생성

* `compute` 모듈이 그 결과를 받아 EC2 생성

이런 식으로 역할을 나눌 수 있다.

이 구조가 바로 모듈화의 핵심이다.

즉, 인프라를 **기능 단위로 분리하고, 필요한 값만 연결해서 조립**하는 방식이다.

---

## 13. 재사용 가능한 코드 구조

```
project-a/
├── main.tf
├── variables.tf
├── outputs.tf
├── terraform.tfvars
└── modules/
    ├── network/
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    └── compute/
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

이 구조의 의미는 다음과 같다.

* root module → 전체 서비스 조립

* `modules/network` → 네트워크 담당

* `modules/compute` → 서버 담당

즉, root module이 child module들을 조립하는 구조다.

---

## 14. 모듈 설계 기준

### 14.1 이 리소스들은 항상 함께 쓰이는가

항상 함께 배포된다면 하나의 모듈로 묶을 수 있다.

### 14.2 다른 프로젝트에서도 같은 구조를 쓸 가능성이 있는가

그렇다면 모듈화 가치가 높다.

### 14.3 입력과 출력 인터페이스를 명확히 만들 수 있는가

그렇다면 모듈화하기 좋은 후보다.

### 14.4 root module에서 전체 흐름이 더 잘 보이는가

모듈화 후 root가 더 읽기 쉬워진다면 잘 나눈 것이다.

---

## 15. 정리

* 모듈은 관련된 Terraform 리소스를 묶은 재사용 가능한 구성 단위다.

* root module이 불러와 사용하는 하위 구성은 child module이다.

* child module은 variable로 입력을 받고 output으로 값을 반환한다.

* root module은 `module` 블록을 사용해 child module을 호출한다.

* 한 모듈의 output을 다른 모듈의 입력으로 연결할 수 있다.

* 모듈화의 핵심은 코드 길이 단축보다 재사용성, 책임 분리, 가독성, 유지보수성 향상에 있다.

* 좋은 모듈은 입력과 출력이 명확하고, 과도하게 복잡하지 않아야 한다.

---

 [[module 예제]] 

# 실습. Terraform 모듈화와 재사용 구조 실습

## 실습 목표

이 실습에서는 다음을 확인한다.

* child module 생성

* root module에서 child module 호출

* 모듈 입력값 전달

* 모듈 output 참조

* 네트워크와 컴퓨트를 분리한 기본 모듈 구조 이해

* 모듈화 전후 코드 차이 체감

---

## 실습 구성 개요

이번 실습에서는 다음 구조를 만든다.

* `network` 모듈
  + VPC
  + 퍼블릭 Subnet
  + Internet Gateway
  + Route Table
  + Route Table Association

* `compute` 모듈
  + Security Group
  + EC2

* root module
  + 두 모듈을 조립
  + network 출력값을 compute 입력값으로 전달

---

## 실습 1. 디렉터리 구조 만들기

```
terraform-modules-lab/
├── main.tf
├── variables.tf
├── terraform.tfvars
├── outputs.tf
└── modules/
    ├── network/
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    └── compute/
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

이 구조에서 바깥쪽이 root module이고,

`modules/network`, `modules/compute`가 child module이다.

---

## 실습 2. network 모듈 작성

## 2.1 `modules/network/variables.tf`

```
variable "vpc_cidr" {
  type        = string
  description = "VPC CIDR block"
}

variable "public_subnet_cidr" {
  type        = string
  description = "Public subnet CIDR block"
}

variable "availability_zone" {
  type        = string
  description = "Availability Zone for public subnet"
}
```

---

## 2.2 `modules/network/main.tf`

```
resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidr

  tags = {
    Name = "module-main-vpc"
  }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidr
  availability_zone       = var.availability_zone
  map_public_ip_on_launch = true

  tags = {
    Name = "module-public-subnet"
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "module-main-igw"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "module-public-rt"
  }
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
```

---

## 2.3 `modules/network/outputs.tf`

```
output "vpc_id" {
  description = "Created VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_id" {
  description = "Created public subnet ID"
  value       = aws_subnet.public.id
}
```

---

## 실습 3. compute 모듈 작성

## 3.1 `modules/compute/variables.tf`

```
variable "subnet_id" {
  type        = string
  description = "Subnet ID for EC2"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID for Security Group"
}

variable "instance_type" {
  type        = string
  description = "EC2 instance type"
}

variable "instance_name" {
  type        = string
  description = "EC2 Name tag"
}

variable "key_name" {
  type        = string
  description = "Existing AWS key pair name"
}
```

---

## 3.2 `modules/compute/main.tf`

```
data "aws_ami" "amazon_linux" {
  most_recent = true

  owners = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
}

resource "aws_security_group" "web_sg" {
  name        = "module-web-sg"
  description = "Allow SSH and HTTP"
  vpc_id      = var.vpc_id

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
    Name = "module-web-sg"
  }
}

resource "aws_instance" "web" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.web_sg.id]
  key_name               = var.key_name

  tags = {
    Name = var.instance_name
  }
}
```

---

## 3.3 `modules/compute/outputs.tf`

```
output "instance_id" {
  description = "Created EC2 instance ID"
  value       = aws_instance.web.id
}

output "instance_public_ip" {
  description = "Created EC2 public IP"
  value       = aws_instance.web.public_ip
}

output "security_group_id" {
  description = "Created security group ID"
  value       = aws_security_group.web_sg.id
}
```

---

## 실습 4. root module 작성

## 4.1 `variables.tf`

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
  default     = "module-web-01"
}

variable "key_name" {
  type        = string
  description = "Existing AWS key pair name"
}
```

---

## 4.2 `main.tf`

```
terraform {
	required_providers {
		aws = {
			source  = "hashicorp/aws"
			version = "6.41.0"
		}
	}
}

provider "aws" {
  region = var.region
}

module "network" {
  source = "./modules/network"

  vpc_cidr           = var.vpc_cidr
  public_subnet_cidr = var.public_subnet_cidr
  availability_zone  = var.availability_zone
}

module "compute" {
  source = "./modules/compute"

  subnet_id     = module.network.public_subnet_id
  vpc_id        = module.network.vpc_id
  instance_type = var.instance_type
  instance_name = var.instance_name
  key_name      = var.key_name
}
```

---

## 4.3 `outputs.tf`

```
output "vpc_id" {
  value = module.network.vpc_id
}

output "public_subnet_id" {
  value = module.network.public_subnet_id
}

output "instance_id" {
  value = module.compute.instance_id
}

output "instance_public_ip" {
  value = module.compute.instance_public_ip
}

output "security_group_id" {
  value = module.compute.security_group_id
}
```

---

## 4.4 `terraform.tfvars`

```
key_name = "my-keypair"
instance_type = "t3.micro"
instance_name = "이니셜-tf-demo-svr"
vpc_cidr = "10.X.0.0/16"
public_subnet_cidr = "10.X.0.0/24"
```

---

## 실습 5. 실행 순서

```
terraform init
terraform fmt
terraform validate
terraform plan
terraform apply -auto-approve
terraform output
```

---

## 실습 6. plan 결과에서 확인할 포인트

`terraform plan` 결과를 볼 때 다음을 확인한다.

* root module 안에 직접 리소스가 많지 않다는 점

* `module.network` 와 `module.compute`가 각각 어떤 리소스를 포함하는지 보이는 점

* `compute` 모듈이 `network` 모듈의 output 값을 입력으로 사용한다는 점

* 최종적으로는 VPC, Subnet, IGW, Route Table, Security Group, EC2가 모두 생성된다는 점

즉, root module은 세부 구현보다

**어떤 모듈을 어떤 값으로 조립하는가**에 집중하게 된다.

---

## 실습 8. 모듈화 전후 비교

실습 후 다음 차이를 비교해보면 좋다.

### 모듈화 전

* 모든 리소스가 한 디렉터리의 `main.tf` 또는 몇 개 파일에 직접 존재

* 리소스 수가 많아질수록 root가 복잡해짐

* 재사용이 어려움

### 모듈화 후

* 역할별로 코드가 나뉨

* root module은 전체 구조 조립에 집중

* child module은 세부 구현 담당

* 같은 network 모듈, compute 모듈을 다른 프로젝트에서도 재사용 가능

---

## 실습 9. 리소스 정리

실습이 끝났으면 반드시 삭제한다.

```
terraform destroy -auto-approve
```

이 명령은 root module 기준으로 실행하지만,

실제로는 child module 안에서 생성한 리소스까지 함께 삭제된다.