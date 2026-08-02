---
title: "5장 Terraform 변수, 출력값, 로컬값과 코드 구조화"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "배포자동화를 위한 Terraform"]
is_public: true
draft: false
---

# 5장. Terraform 변수, 출력값, 로컬값과 코드 구조화

## 장 목표

이 장에서는 Terraform 코드를 더 유연하고 재사용 가능하게 만드는 핵심 요소인 **variable**, **output**, **locals**, 그리고 **파일 분리 구조**를 학습한다.

앞 장까지는 Terraform 코드 한 파일 안에 값을 직접 적어 넣는 방식으로 개념을 익혔다면, 이제부터는 값을 외부에서 전달하거나, 공통 값을 한곳에 정리하고, 필요한 값을 밖으로 노출하는 구조를 이해해야 한다.

이 장을 학습한 뒤에는 다음이 가능해야 한다.

* `variable`의 의미와 역할을 설명할 수 있음

* `terraform.tfvars` 파일의 역할을 설명할 수 있음

* CLI 변수 전달 방식을 설명할 수 있음

* `output`의 의미와 역할을 설명할 수 있음

* `locals`의 의미와 역할을 설명할 수 있음

* 하드코딩된 Terraform 코드를 변수 기반으로 바꿀 수 있음

* 여러 `.tf` 파일로 코드를 분리해도 하나의 구성으로 동작한다는 점을 이해할 수 있음

* VS Code 기준으로 Terraform 프로젝트 구조를 정리할 수 있음

---

## 1. 왜 변수와 출력값, 로컬값이 필요한가

다음은 값을 직접 적어 넣은 코드다.

```
resource "aws_instance" "web" {
  ami           = "ami-0123456789abcdef0"
  instance_type = "t3.micro"

  tags = {
    Name = "web-server"
  }
}
```

이 방식은 코드가 조금만 많아져도 곧바로 불편해진다.

예를 들어 다음 상황을 생각해보자.

* 개발 환경은 `t3.micro`, 운영 환경은 `t3.small`을 써야 함

* 리전마다 사용할 AMI가 달라질 수 있음

* 태그 이름 규칙을 여러 리소스에 공통으로 적용해야 함

* 생성된 인스턴스 ID나 퍼블릭 IP를 나중에 확인하고 싶음

* 팀원들이 같은 코드를 서로 다른 값으로 실행해야 함

이런 상황에서 모든 값을 코드 안에 직접 적어 넣으면 다음 문제가 생긴다.

* 재사용성이 떨어짐

* 환경별 변경이 어려움

* 중복 값이 많아짐

* 실수 가능성이 커짐

* 결과 확인이 불편해짐

이 문제를 해결하기 위해 Terraform은 다음 기능을 제공한다.

* **variable** → 외부에서 값을 입력받는 기능

* **output** → 생성 결과나 중요한 값을 밖으로 보여주는 기능

* **locals** → 코드 내부에서 공통 값을 정리하는 기능

즉, Terraform 코드를 위 값들을 사용하여  **재사용 가능한 구조로** 만들 수 있다.

---

## 2. variable

### 2.1 variable이란 무엇인가

`variable`은 Terraform 코드가 외부로부터 입력값을 받을 수 있도록 정의하는 블록이다.

즉, Terraform 코드에서 사용할 **입력 파라미터**를 선언하는 것이다.

예를 들어 다음과 같이 정의할 수 있다.

```
variable "instance_type" {
  type = string
}
```

이 코드는 `instance_type`이라는 이름의 문자열 입력값을 받겠다는 의미다.

이제 다른 블록에서는 이 값을 다음처럼 사용할 수 있다.

```
instance_type = var.instance_type
```

즉, `var.instance_type`은

“variable로 선언한 `instance_type` 값을 사용하겠다”는 뜻이다.

---

### 2.2 왜 variable이 필요한가

예를 들어 EC2 인스턴스 타입을 코드에 직접 적는 방식은 다음과 같다.

```
instance_type = "t3.micro"
```

이 방식은 단순하지만, 환경이 바뀔 때마다 코드를 직접 수정해야 한다.

반면 variable을 사용하면 코드 구조는 그대로 두고 값만 바꿀 수 있다.

예를 들어

* 개발 환경 → `t3.micro`

* 운영 환경 → `t3.small`

이렇게 같은 코드에 다른 값을 넣어 재사용할 수 있다.

즉, variable은 **코드와 값을 분리하는 도구**다.

---

### 2.3 기본 구조

```
variable "이름" {
  type = 자료형
}
```

가장 자주 사용하는 자료형은 다음과 같다.

* `string`

* `number`

* `bool`

* `list(string)`

* `map(string)`

* `object({...})`

---

### 2.4 default 값

variable에는 기본값을 줄 수 있다.

```
variable "instance_type" {
  type    = string
  default = "t3.micro"
}
```

이 경우 별도로 값을 전달하지 않으면 `t3.micro`를 사용한다.

즉,

* `default`가 있으면 값 전달을 생략할 수 있음

* `default`가 없으면 실행 시 값을 반드시 제공해야 함

---

### 2.5 description

실무에서는 `description`을 함께 쓰는 것이 좋다.

```
variable "instance_type" {
  type        = string
  description = "EC2 instance type"
  default     = "t3.micro"
}
```

`description`은 문서화 역할을 한다.

특히 변수가 많아질수록 이 설명이 매우 중요해진다.

---

## 3. terraform.tfvars

### 3.1 tfvars 파일이란 무엇인가

variable을 선언했다고 해서 값이 자동으로 들어오지는 않는다.

값을 전달하는 방법이 필요하다.

그 방법 중 가장 대표적인 것이 `terraform.tfvars` 파일이다.

예를 들어 다음과 같이 작성할 수 있다.

```
instance_type = "t3.micro"
instance_name = "web-server"
```

Terraform은 기본적으로 `terraform.tfvars` 파일을 자동으로 읽는다.

즉, 코드에는 변수 선언만 해두고, 실제 값은 이 파일에서 주입할 수 있다.

---

### 3.2 왜 tfvars를 쓰는가

`terraform.tfvars`를 사용하면 다음 장점이 있다.

* 코드와 값이 분리됨

* 환경별 값 관리가 쉬움

* 같은 코드로 dev/stage/prod를 다르게 실행할 수 있음

* 변수 전달을 반복 입력하지 않아도 됨

즉, `terraform.tfvars`는 **실행 시 주입할 값 모음 파일**이라고 보면 된다.

---

### 3.3 예제

### variables.tf

```
variable "instance_type" {
  type = string
}

variable "instance_name" {
  type = string
}
```

### terraform.tfvars

```
instance_type = "t3.micro"
instance_name = "web-server"
```

### main.tf

```
resource "aws_instance" "web" {
  ami           = "ami-0123456789abcdef0"
  instance_type = var.instance_type

  tags = {
    Name = var.instance_name
  }
}
```

이 구조에서는 값을 코드 안에 직접 입력하지 않고, 외부에서 가져온다.

---

## 4. CLI 변수 전달

### 4.1 개념

변수는 파일뿐 아니라 명령행에서도 직접 전달할 수 있다.

이 방식은 테스트나 일회성 실행에서 유용하다.

예를 들어 다음처럼 사용할 수 있다.

```
terraform plan -var="instance_type=t3.micro"
```

또는 여러 개를 함께 전달할 수도 있다.

```
terraform plan -var="instance_type=t3.micro" -var="instance_name=web-server"
```

---

### 4.2 언제 사용하는가

CLI 변수 전달은 다음 상황에서 유용하다.

* 빠르게 테스트할 때

* 잠깐 다른 값으로 실행해볼 때

* 자동화 파이프라인에서 값을 주입할 때

* tfvars 파일을 따로 두지 않고 실험할 때

다만 변수가 많아지면 명령어가 길어지고 관리가 불편해진다.

그래서 실무에서는 보통 tfvars 파일과 함께 사용하거나, 자동화 도구에서 주입한다.

---

### 4.3 tfvars와 CLI 중 무엇이 우선인가

기본적으로는 **명시적으로 전달한 값이 더 우선**한다고 이해하면 된다.

즉, CLI에서 직접 `-var`로 준 값은 사용자가 지금 실행에서 특별히 지정한 값이기 때문에 의미가 크다.

---

## 5. output

### 5.1 output이란 무엇인가

`output`은 Terraform이 생성하거나 조회한 값 중에서

사용자에게 보여주고 싶은 값을 밖으로 노출하는 기능이다.

예를 들어 다음과 같이 사용할 수 있다.

```
output "instance_id" {
  value = aws_instance.web.id
}
```

이 코드는 `aws_instance.web.id` 값을 `instance_id`라는 이름으로 출력하겠다는 뜻이다.

---

### 5.2 왜 output이 필요한가

Terraform은 리소스를 잘 만들었더라도, 생성된 값을 자동으로 눈에 잘 보이게 정리해서 보여주지는 않는다.

특히 다음 값들은 실습과 운영 모두에서 자주 확인한다.

* 인스턴스 ID

* 퍼블릭 IP

* VPC ID

* Subnet ID 목록

* 로드밸런서 DNS 이름

이럴 때 output을 사용하면 결과를 명확히 확인할 수 있다.

즉, output은 **Terraform 코드의 결과를 출력할 때** 사용한다..

---

### 5.3 기본 구조

```
output "이름" {
  value = 값
}
```

예시:

```
output "public_ip" {
  value = aws_instance.web.public_ip
}
```

---

### 5.4 description과 sensitive

실무에서는 output에도 설명을 붙일 수 있다.

```
output "instance_id" {
  description = "Created EC2 instance ID"
  value       = aws_instance.web.id
}
```

민감한 값은 `sensitive = true`로 표시할 수 있다.

```
output "db_password" {
  value     = "example-password"
  sensitive = true
}
```

이 설정의 목적은 해당 값을 다른 곳으로 전달할 때 사용하려고 할 때 화면이나 로그 등에 노출되지 않도록 하는 것이다. 즉, CICD환경에서 출력된 값을 이용해 다른 동작을 하려고 할 때 안전하게 전달할 수 있다.

---

## 6. locals

### 6.1 locals란 무엇인가

`locals`는 Terraform 코드 내부에서 **공통 값이나 계산 결과를 이름 붙여 재사용하는 기능**이다.

즉, 외부 입력을 받는 variable과 달리, locals는 **코드 안에서 사용하기 위한 값**으로 변경이 불가능하다.

예를 들어 다음과 같이 사용할 수 있다.

```
locals {
  common_tags = {
    Environment = "dev"
    Project     = "terraform-lab"
  }
}
```

그리고 다른 곳에서 다음처럼 쓸 수 있다.

```
tags = local.common_tags
```

---

### 6.2 왜 locals가 필요한가

코드가 커지면 같은 값이나 같은 표현식이 여러 번 반복된다.

예를 들어 다음 상황을 생각해보자.

* 모든 리소스에 공통 태그를 붙이고 싶음

* 이름 규칙을 공통으로 만들고 싶음

* 여러 곳에서 같은 문자열 조합을 사용해야 함

이런 값을 각 리소스마다 직접 적으면 중복이 생긴다.

예:

```
tags = {
  Environment = "dev"
  Project     = "terraform-lab"
}
```

이 코드가 여러 리소스에 반복되면 유지보수가 불편해진다.

반면 locals를 사용하면 한곳에서 관리할 수 있다.

---

### 6.3 기본 구조

```
locals {
  이름 = 값
}
```

예:

```
locals {
  instance_name = "dev-web-01"
}
```

사용할 때는 다음처럼 쓴다.

```
local.instance_name
```

즉,

* variable 참조 → `var.변수명`

* locals 참조 → `local.이름`

이 차이를 구분해야 한다.

---

### 6.4 locals와 variable의 차이

### variable

* 외부 입력값

* 사용자가 실행 시 바꿀 수 있음

* 코드 바깥에서 들어옴

### locals

* 내부 사용 값

* 코드 안에서 참조함.

* 외부 입력이 아니라 내부 재사용 목적

---

## 7. 파일 분리 구조

### 7.1 왜 파일을 분리하는가

Terraform은 한 파일에 모든 코드를 다 써도 동작한다.

예를 들어 `main.tf` 하나에 `provider`, `resource`, `variable`, `output`, `locals`를 모두 넣어도 된다.

하지만 코드가 커질수록 한 파일에 다 넣는 방식은 불편해진다.

* 찾기 어려움

* 수정하기 어려움

* 협업 시 충돌이 많아짐

* 변수와 출력, 리소스가 섞여 가독성이 떨어짐

그래서 실무에서는 역할별로 파일을 나누는 경우가 많다.

---

### 7.2 대표적인 분리 방식

가장 기본적인 구조는 다음과 같다.

* `main.tf` → 주요 resource, data, provider

* `variables.tf` → variable 정의

* `outputs.tf` → output 정의

* `locals.tf` → locals 정의

* `terraform.tfvars` → 변수 실제 값

이렇게 나눠두면 파일 역할이 명확해진다.

---

### 7.3 중요한 점

파일을 나눴다고 해서 Terraform이 각 파일을 독립 실행하는 것은 아니다.

같은 디렉터리 안의 `.tf` 파일들은 **하나의 구성(configuration)** 으로 함께 읽힌다.

즉,

* `main.tf`에서 `var.instance_type`을 써도

* `variables.tf`에 선언만 되어 있으면 정상적으로 연결된다.

초보자는 종종 “main.tf에서 정의해야 main.tf에서 쓸 수 있지 않나?”라고 생각하는데, 그렇지 않다.

Terraform은 디렉터리 단위로 `.tf` 파일들을 함께 읽는다.

---

## 8. VS Code 기준 프로젝트 구조화

입문 단계에서 가장 무난한 Terraform 프로젝트 구조는 다음과 같다.

```
terraform-aws-lab/
├── main.tf
├── variables.tf
├── outputs.tf
├── locals.tf
├── terraform.tfvars
├── .terraform.lock.hcl
└── .terraform/
```

각 파일의 역할은 다음과 같다.

### `main.tf`

실제 provider, resource, data source를 배치하는 중심 파일이다.

### `variables.tf`

입력 변수 선언을 모아두는 파일이다.

### `outputs.tf`

사용자에게 보여줄 출력값을 모아두는 파일이다.

### `locals.tf`

공통 태그, 공통 이름 규칙, 재사용 값 등을 모아두는 파일이다.

### `terraform.tfvars`

현재 실행 환경에서 사용할 실제 변수값을 적는 파일이다.

### `.terraform.lock.hcl`

초기화 시 설치된 provider 버전 정보를 고정하는 파일이다.

### `.terraform/`

초기화 과정에서 생성되는 내부 작업 디렉터리다.

---

## 9. 하드코딩 코드에서 구조화 코드로 바꾸는 흐름

다음처럼 하드코딩된 코드가 있다고 하자.

```
resource "aws_instance" "web" {
  ami           = "ami-0123456789abcdef0"
  instance_type = "t3.micro"

  tags = {
    Name = "dev-web-01"
  }
}
```

이 코드는 재사용성은 낮다.

이를 점진적으로 바꾸면 다음 흐름이 된다.

### 1단계. variable 적용

```
variable "instance_type" {
  type    = string
  default = "t3.micro"
}

variable "instance_name" {
  type    = string
  default = "dev-web-01"
}
```

```
resource "aws_instance" "web" {
  ami           = "ami-0123456789abcdef0"
  instance_type = var.instance_type

  tags = {
    Name = var.instance_name
  }
}
```

---

### 2단계. locals 적용

```
locals {
  common_tags = {
    Environment = "dev"
    Project     = "terraform-lab"
  }
}
```

```
resource "aws_instance" "web" {
  ami           = "ami-0123456789abcdef0"
  instance_type = var.instance_type

  tags = merge(local.common_tags, {
    Name = var.instance_name
  })
}
```

여기서 `merge()`는 여러 맵을 하나로 합치는 함수다.

즉, 공통 태그와 개별 태그를 합쳐서 사용한다.

---

### 3단계. output 적용

```
output "instance_id" {
  value = aws_instance.web.id
}
```

즉, 하드코딩 코드는 점차 다음과 같은 구조로 발전한다.

* 입력은 variable

* 공통 정리는 locals

* 결과 확인은 output

---

## 11. 자주 하는 실수

### 11.1 variable 선언 없이 `var.` 사용함

예를 들어 다음처럼 사용했는데

```
instance_type = var.instance_type
```

`variable "instance_type"` 선언이 없으면 오류가 발생한다.

즉, `var.`로 참조하려면 반드시 해당 variable이 먼저 선언되어 있어야 한다.

---

### 11.2 locals를 `var.`처럼 참조함

예를 들어 locals를 선언해놓고

```
locals {
  instance_name = "dev-web-01"
}
```

아래처럼 쓰면 틀린다.

```
Name = var.instance_name
```

locals는 반드시 `local.`로 참조해야 한다.

정답:

```
Name = local.instance_name
```

---

### 11.3 output을 리소스 생성용이 아님.

output은 어디까지나 결과를 보여주는 용도다.

다른 블록의 입력값을 정의하는 기능이 아니다.

즉,

* variable → 입력

* output → 출력

---

### 11.4 tfvars 파일에 선언까지 같이 적으려 함

`terraform.tfvars`에는 variable 블록을 적는 것이 아니라,

이미 선언된 변수에 대한 **값만** 적는다.

틀린 형태:

```
variable "instance_type" {
  default = "t3.micro"
}
```

올바른 형태:

```
instance_type = "t3.micro"
```

---

## 12. 장 정리

이 장의 핵심은 다음과 같다.

* `variable`은 외부에서 입력값을 받기 위한 기능이다.

* `terraform.tfvars`는 변수 실제 값을 파일로 전달하는 방식이다.

* CLI의 `var` 옵션으로도 값을 직접 전달할 수 있다.

* `output`은 생성 결과나 중요한 값을 밖으로 보여주는 기능이다.

* `locals`는 코드 내부에서 공통 값이나 계산 결과를 정리하는 기능이다.

* Terraform 코드는 여러 `.tf` 파일로 나누어도 같은 디렉터리 안에서는 하나의 구성으로 함께 동작한다.

* 실무에서는 `main.tf`, `variables.tf`, `outputs.tf`, `locals.tf`, `terraform.tfvars` 형태로 분리하는 경우가 많다.

---

# 실습. Terraform 변수, 출력값, 로컬값과 코드 구조화 실습

## 실습 1. variable과 tfvars로 EC2 설정값 분리하기

---

### 파일 1. `variables.tf`

```
variable "instance_type" {
  type        = string
  description = "EC2 instance type"
}

variable "instance_name" {
  type        = string
  description = "EC2 Name tag"
}
```

---

### 파일 2. `terraform.tfvars`

```
instance_type = "t3.micro"
instance_name = "dev-web-01"
```

---

### 파일 3. `main.tf`

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
  region = "ap-northeast-2"
}

data "aws_ami" "amazon_linux" {
  most_recent = true

  owners = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
}

resource "aws_instance" "web" {
  ami           = data.aws_ami.amazon_linux.id
  instance_type = var.instance_type

  tags = {
    Name = var.instance_name
  }
}
```

---

### 실행 명령

```
terraform init
terraform plan
```

---

### 확인 포인트

* `instance_type`과 `instance_name`은 코드에 직접 쓰지 않았음

* Terraform이 `terraform.tfvars` 파일 값을 자동으로 읽음

* 같은 코드 구조를 유지한 채 값만 바꿔 실행 가능함

---

## 실습 2. CLI `var` 옵션으로 값 직접 전달하기

### 실습 목적

변수값을 파일이 아니라 명령행에서 직접 전달하는 방식을 확인한다.

---

### `terraform.tfvars` 사용 없이 실행 예시

```
terraform plan -var="instance_type=t3.small" -var="instance_name=cli-web-01"
```

---

### 설명

이 명령은 현재 실행에서만 변수값을 직접 주입한다.

* `instance_type` → `t3.small`

* `instance_name` → `cli-web-01`

즉, tfvars 파일 없이도 variable 값을 전달할 수 있다.

---

### 확인 포인트

* 일회성 테스트에는 편리함

* 변수가 많아지면 명령이 길어짐

* 반복 실행이나 환경별 관리에는 tfvars 파일 방식이 더 편리할 수 있음

---

## 실습 3. locals로 공통 태그 정리하기

반복되는 값을 locals로 정리해서 코드 중복을 줄이는 방식을 이해한다.

---

### 파일 1. `locals.tf`

```
locals {
  common_tags = {
    Environment = "dev"
    Project     = "terraform-lab"
    Owner       = "student"
  }
}
```

---

### 파일 2. `main.tf` 수정

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
  region = "ap-northeast-2"
}

data "aws_ami" "amazon_linux" {
  most_recent = true

  owners = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
}

resource "aws_instance" "web" {
  ami           = data.aws_ami.amazon_linux.id
  instance_type = var.instance_type

  tags = merge(local.common_tags, {
    Name = var.instance_name
  })
}
```

---

`merge()` 함수는 여러 맵을 하나로 합친다.

즉,

* `local.common_tags` 에 있는 공통 태그

* `Name = var.instance_name` 개별 태그

를 합쳐서 최종 태그로 사용한다.

---

### 확인 포인트

* 공통 태그를 한곳에서 관리할 수 있음

* 여러 리소스에서 재사용하기 쉬움

* 값 변경 시 유지보수가 편해짐

---

## 실습 4. output으로 생성 결과 확인하기

### 실습 목적

생성된 리소스의 주요 값을 `output`으로 확인하는 방식을 익힌다.

---

### 파일 1. `outputs.tf`

```
output "instance_id" {
  description = "Created EC2 instance ID"
  value       = aws_instance.web.id
}

output "instance_public_ip" {
  description = "Created EC2 public IP"
  value       = aws_instance.web.public_ip
}

output "ami_id_used" {
  description = "AMI ID used for EC2"
  value       = data.aws_ami.amazon_linux.id
}
```

---

### 실행 명령

```
terraform apply -auto-approve
```

---

### 설명

`apply`가 끝나면 Terraform은 output 값을 화면에 보여준다.

어떤 값이 실제로 사용되었고 어떤 결과가 나왔는지를 바로 확인할 수 있다.

---

### apply 이후 다시 확인하는 방법

```
terraform output
```

특정 값만 보고 싶다면 다음처럼 사용할 수 있다.

```
terraform output instance_id
```

---

### 확인 포인트

* `output`은 결과 확인용이다

* 리소스의 중요한 속성을 쉽게 다시 볼 수 있다

* Data Source 값도 output으로 함께 확인할 수 있다

---

## 실습 5. 파일 분리 구조 확인하기

### 실습 목적

Terraform이 같은 디렉터리 안의 여러 `.tf` 파일을 하나의 구성으로 읽는다는 점을 체감한다.

---

### 예시 디렉터리 구조

```
terraform-aws-lab/
├── main.tf
├── variables.tf
├── outputs.tf
├── locals.tf
├── terraform.tfvars
├── .terraform.lock.hcl
└── .terraform/
```

---

### 확인 방법

다음과 같은 상태여야 한다.

* `main.tf` 에서 `var.instance_type` 사용

* `variables.tf` 에서 `instance_type` 선언

* `locals.tf` 에서 `common_tags` 선언

* `outputs.tf` 에서 `aws_instance.web.id` 출력

이렇게 파일이 나뉘어 있어도 Terraform은 전체를 하나의 구성으로 읽는다.

즉, 파일이 달라도 다음 참조는 모두 정상 동작한다.

* `var.instance_type`

* `local.common_tags`

* `aws_instance.web.id`

* `data.aws_ami.amazon_linux.id`

---

## 실습 6. 전체 예제 코드 정리본

### `main.tf`

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
  region = "ap-northeast-2"
}

data "aws_ami" "amazon_linux" {
  most_recent = true

  owners = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
}

resource "aws_instance" "web" {
  ami           = data.aws_ami.amazon_linux.id
  instance_type = var.instance_type

  tags = merge(local.common_tags, {
    Name = var.instance_name
  })
}
```

---

### `variables.tf`

```
variable "instance_type" {
  type        = string
  description = "EC2 instance type"
}

variable "instance_name" {
  type        = string
  description = "EC2 Name tag"
}
```

---

### `locals.tf`

```
locals {
  common_tags = {
    Environment = "dev"
    Project     = "terraform-lab"
    Owner       = "student"
  }
}
```

---

### `outputs.tf`

```
output "instance_id" {
  description = "Created EC2 instance ID"
  value       = aws_instance.web.id
}

output "instance_public_ip" {
  description = "Created EC2 public IP"
  value       = aws_instance.web.public_ip
}

output "ami_id_used" {
  description = "AMI ID used for EC2"
  value       = data.aws_ami.amazon_linux.id
}
```

---

### `terraform.tfvars`

```
instance_type = "t3.micro"
instance_name = "dev-web-01"
```

---

### 실행 순서

```
terraform init
terraform fmt
terraform validate
terraform plan
terraform apply -auto-approve
terraform output
terraform destroy -auto-approve
```

---