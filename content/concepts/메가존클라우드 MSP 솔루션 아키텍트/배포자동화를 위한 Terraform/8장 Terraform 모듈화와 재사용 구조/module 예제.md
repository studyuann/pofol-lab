---
title: "module 예제"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "배포자동화를 위한 Terraform", "8장 Terraform 모듈화와 재사용 구조"]
is_public: true
draft: false
---

# module 예제

* random 프로바이더

* resource

random\_pet : 이름을 자동으로 생성해 줌.

random\_password : 패스워드를 임의로 생성해 줌.

* 사용자와 패스워드를 여러 번 구성해야하는 경우 사용시 효과적임.

자식 모듈과 루트 모듈 디렉토리 구조

```
/
module-lab
|--modules                     # child module home
|    |-----random_pwgen
|             |-- main.tf 
|             |-- output.tf
|             |-- variable.tf
|--random-id-pw                # root module home
       |--main.tf
```

* random\_pwgen 모듈 작성

main.tf

```
 resource "random_pet" "name" {
    keepers = {
        ami_id = timestamp()    # keepers의 값이 동일하면 값을 새로 생성하지 않음.
    }                           # timestamp()를 이용해 매번 새로운 값을 생성하도록 함.
}

resource "random_password" "password" {
    length = var.isDB ? 16 : 10
    special = var.isDB ? true : false 
    override_special = "!@#$%^"
}
```

variable.tf

```
variable "isDB" {
  type = bool
  default = false
  description = "DB용 패스워드 여부"
}
```

output.tf

```
output "id" {
  value = random_pet.name.id
}

output "pw" {
    value = nonsensitive(random_password.password.result)
}
```

테스트를 위해 terraform init을 수행하고 terraform apply를 수행할 때 변수를 지정한다.

자식모듈 디렉토리인 random-id-pw에서 실행

```
random-id-pw$ terraform init
random-id-pw$ terraform apply -auto-approve -var=isDB=true
```

* 자식모듈 호출

* root module의 [main.tf](http://main.tf) 작성

```
module "mypw1" {
    source = "../modules/terraform-random-pwgen"
}

module "mypw2" {
    source = "../modules/terraform-random-pwgen"
    isDB = true
}
```

루트모듈 디렉토리(random\_pwgen)에서 실행

```
random_pwgen$ terraform init
random_pwgen$ terraform apply -auto-approve
```

DB용 ID/PW와 일반용 ID/PW가 랜덤하게 출력됨.

ID와 PW를 생성하는 자식모듈을 루트모듈에서 호출해서 사용하고 있음.

# 예제 1. S3 버킷 생성 모듈

---

# 1-1. 디렉터리 구조

```
terraform-s3-module/
├── main.tf
├── provider.tf
├── outputs.tf
└── modules/
    └── s3_bucket/
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

---

# 1-2. 루트 모듈 코드

## `provider.tf`

```
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.42.0"
    }
  }
}

provider "aws" {
  region = "ap-northeast-2"
}
```

## `main.tf`

```
module "my_s3_bucket" {
  source = "./modules/s3_bucket"

  bucket_name = "my-tf-module-demo-bucket-001"
  environment = "dev"
}
```

## `outputs.tf`

```
output "bucket_name" {
  value = module.my_s3_bucket.bucket_name
}

output "bucket_arn" {
  value = module.my_s3_bucket.bucket_arn
}
```

---

# 1-3. 모듈 코드

## `modules/s3_bucket/variables.tf`

```
variable "bucket_name" {
  description = "생성할 S3 버킷 이름"
  type        = string
}

variable "environment" {
  description = "태그에 사용할 환경 이름"
  type        = string
}
```

## `modules/s3_bucket/main.tf`

## `modules/s3_bucket/outputs.tf`

```
output "bucket_name" {
  value = aws_s3_bucket.this.bucket
}

output "bucket_arn" {
  value = aws_s3_bucket.this.arn
}
```

---

# 1-4. 코드 설명

## 루트의 `module` 블록

```
module "my_s3_bucket" {
  source = "./modules/s3_bucket"

  bucket_name = "my-tf-module-demo-bucket-001"
  environment = "dev"
}
```

여기서 핵심은 다음과 같음.

### `module "my_s3_bucket"`

모듈을 호출하는 이름임.

이 이름으로 나중에 output 참조 가능함.

예:

```
module.my_s3_bucket.bucket_name
```

### `source = "./modules/s3_bucket"`

실제로 사용할 모듈 코드가 있는 경로임.

* `./` : 현재 폴더 기준

* `modules/s3_bucket` : 모듈 폴더

즉, 현재 프로젝트 안에 있는 로컬 모듈을 사용한다는 뜻임.

### `bucket_name`, `environment`

모듈에 전달하는 입력값임.

모듈 내부에서는 `var.bucket_name`, `var.environment` 형태로 사용함.

---

## 모듈 내부의 변수 선언

```
variable "bucket_name" {
  description = "생성할 S3 버킷 이름"
  type        = string
}
```

이 코드는

"이 모듈은 `bucket_name`이라는 문자열 값을 입력받아야 함"

이라는 뜻임.

Terraform module은 함수처럼 생각하면 이해가 쉬움.

* 입력값 = variable

* 내부 처리 = resource

* 반환값 = output

---

## 리소스 선언

```
resource "aws_s3_bucket" "this" {
  bucket = var.bucket_name
```

### `resource`

실제 AWS 리소스를 만들겠다는 뜻임.

### `"aws_s3_bucket"`

AWS provider가 제공하는 S3 버킷 리소스 타입임.

### `"this"`

리소스의 로컬 이름임.

모듈 내부에서 이 이름으로 참조함.

예:

```
aws_s3_bucket.this.arn
```

### `bucket = var.bucket_name`

입력받은 버킷 이름을 실제 버킷 이름으로 사용함.

주의할 점도 있음.

S3 버킷 이름은 **전 세계에서 고유해야 함**.

그래서 이미 누가 쓰는 이름이면 생성 실패함.

---

## output 선언

```
output "bucket_arn" {
  value = aws_s3_bucket.this.arn
}
```

이 값은 모듈 밖으로 꺼내주는 값임.

즉, 루트 모듈에서 다음처럼 참조 가능함.

```
module.my_s3_bucket.bucket_arn
```

---

# 1-5. 실행 방법

프로젝트 루트에서 실행함.

```
terraform init
```

## 설명

초기화 명령임.

* provider 다운로드

* module 인식

* 실행 준비

그다음 실행 계획 확인:

```
terraform plan
```

## 설명

실제로 만들기 전에 어떤 리소스가 생성될지 미리 보여줌.

적용:

```
terraform apply
```

확인 메시지가 나오면:

```
yes
```

삭제:

```
terraform destroy
```

## 설명

실습 후 리소스 정리할 때 사용함.

AWS 과금 방지를 위해 꼭 정리하는 습관이 중요함.

---

# 1-6. 이 예제로 익히는 핵심

이 예제에서 익혀야 할 핵심은 다음임.

* module 호출 방법

* variable로 값 전달하는 방법

* output으로 값 반환하는 방법

* AWS provider 기반 리소스 생성 흐름