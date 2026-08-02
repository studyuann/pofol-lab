---
title: "9장 Terraform State, Backend, 협업 방식"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "배포자동화를 위한 Terraform"]
is_public: true
draft: false
---

# 9장. Terraform State, Backend, 협업 방식

## 장 목표

이 장에서는 Terraform 운영에서 매우 중요한 **state**, **backend**, **workspace**, 그리고 **협업 시 주의사항**을 학습한다.

앞 장까지는 Terraform 코드를 작성하고 리소스를 생성하는 흐름에 집중했다. 하지만 실제 운영 환경에서는 코드 자체만큼이나 **Terraform이 현재 인프라 상태를 어떻게 기억하고 있는가**가 중요하다.

Terraform은 단순히 선언만 읽고 리소스를 만드는 도구가 아니다.

Terraform은 자신이 관리하는 리소스와 실제 클라우드 자원 사이의 연결 정보를 **state**에 기록하고, 그 정보를 바탕으로 다음 변경 작업을 계산한다.

이 장을 학습한 뒤에는 다음이 가능해야 한다.

* Terraform state의 역할을 설명할 수 있음

* state 파일이 왜 중요한지 설명할 수 있음

* drift의 의미를 설명할 수 있음

* `terraform state` 명령의 기초를 이해할 수 있음

* backend의 의미를 설명할 수 있음

* S3 backend를 사용하는 이유를 설명할 수 있음

* `terraform init -reconfigure`, `terraform init -migrate-state`의 차이를 설명할 수 있음

* workspace를 이용한 환경 분리 개념을 설명할 수 있음

* 협업 시 state 관리 주의사항을 설명할 수 있음

---

## 1. 왜 state가 중요한가

Terraform을 처음 배울 때는 보통 다음처럼 이해한다.

* 코드를 작성한다

* `terraform plan`을 실행한다

* `terraform apply`를 실행한다

* 리소스가 생성된다

예를 들어 다음을 생각해보자.

* Terraform은 내가 만든 VPC를 어떻게 다시 찾는가

* 다음 실행 때는 왜 같은 VPC를 또 만들지 않는가

* EC2 이름만 바꿨을 때 무엇을 수정해야 하는지 어떻게 아는가

* 이미 존재하는 리소스와 코드가 연결되어 있다는 사실을 Terraform은 어디에 기록하는가

이 질문의 답이 바로 **state**다.

Terraform은 자신이 관리하는 리소스의 정보를 state에 기록한다.

즉, state는 Terraform이 인프라를 기억하는 저장소다.

---

## 2. state란 무엇인가

Terraform state는 Terraform이 **관리 중인 리소스와 실제 인프라의 연결 상태를 기록한 데이터**다.

보통 로컬 작업에서는 `terraform.tfstate` 파일 형태로 존재한다.

즉, state에는 다음과 같은 정보가 담긴다.

* Terraform 코드의 리소스 주소

* 실제 클라우드 리소스 ID

* 각 리소스의 현재 속성 정보 일부

* 의존 관계 추적에 필요한 정보

* output 값 정보

쉽게 말하면 다음과 같다.

* 코드에는 “무엇을 원하는가”가 적혀 있음

* state에는 “무엇이 실제로 존재하는가”와 “그것이 코드의 어떤 리소스와 연결되는가”가 기록됨

이 두 가지가 함께 있어야 Terraform이 제대로 동작한다.

---

## 3. state 파일은 언제 생기는가

처음 `terraform init`만 했을 때는 state가 아직 없다.

왜냐하면 아직 Terraform이 실제로 관리하는 리소스가 없기 때문이다.

보통 state 파일은 다음 시점에 생긴다.

* `terraform apply`로 실제 리소스를 생성한 후

* 또는 state를 생성/갱신하는 작업을 수행한 후

즉, Terraform이 실제 인프라와 연결되는 순간부터 state가 중요해진다.

---

## 4. state가 하는 역할

Terraform state의 역할은 단순 기록이 아니다.

실제로 다음과 같은 핵심 기능을 담당한다.

### 4.1 리소스 추적

예를 들어 코드에 다음이 있다고 하자.

```
resource "aws_vpc" "main" {
  cidr_block = "10.10.0.0/16"
}
```

Terraform이 apply를 실행한 뒤에는

이 `aws_vpc.main` 이 실제 AWS의 어떤 VPC ID와 연결되는지 state에 기록한다.

즉, 다음 실행부터 Terraform은

“내가 관리하는 `aws_vpc.main` 은 이미 존재하고, 그 실제 ID는 무엇이다”라고 판단할 수 있다.

---

### 4.2 변경 계산

Terraform은 코드와 state를 비교해서 변경 작업을 계산한다.

예를 들어 VPC 태그를 바꿨다고 하자.

Terraform은 state를 기준으로 현재 관리 중인 리소스와 코드의 차이를 계산하고,

“새로 만들 것인지”, “수정할 것인지”, “아무것도 하지 않을 것인지”를 판단한다.

즉, `terraform plan`은 단순히 코드만 보고 계산하는 것이 아니라

**코드 + state**를 함께 보고 계산한다.

---

### 4.3 output 관리

Terraform의 output 값도 state에 반영된다.

예를 들어 다음 output이 있다고 하자.

```
output "vpc_id" {
  value = aws_vpc.main.id
}
```

이 값도 state를 통해 기록되고 다시 조회될 수 있다.

그래서 `terraform output` 명령으로 나중에 다시 확인할 수 있다.

---

## 5. local state

## 5.1 local state란

가장 기본적인 상태는 로컬 파일 기반 state다.

즉, 현재 디렉터리에 `terraform.tfstate` 파일이 생성되는 방식이다.

예를 들어 디렉터리 구조가 다음과 같을 수 있다.

```
terraform-lab/
├── main.tf
├── variables.tf
├── outputs.tf
├── terraform.tfstate
├── terraform.tfstate.backup
└── .terraform/
```

여기서 `terraform.tfstate`가 local state 파일이다.

---

## 5.2 local state의 장점

local state는 단순하고 이해하기 쉽다.

* 별도 backend 설정이 필요 없음

* 바로 실습 가능

* 구조를 이해하기 쉬움

---

## 5.3 local state의 한계

하지만 실제 협업과 운영에서는 local state만 사용하면 문제가 많다.

### 문제 1. 내 PC에만 있음

다른 팀원은 내 state 파일을 볼 수 없다.

### 문제 2. 동기화가 어려움

같은 코드를 여러 사람이 실행하면 각자 다른 state를 가질 수 있다.

### 문제 3. 충돌 위험

동시에 apply하면 서로 다른 상태를 기준으로 작업할 수 있다.

### 문제 4. 유실 위험

파일 삭제, PC 변경, 경로 이동 등으로 state를 잃을 수 있다.

즉, local state는 **개인 실습에는 편하지만 협업에는 취약하다**.

---

## 6. drift

## 6.1 drift란 무엇인가

drift는 Terraform 코드와 state, 그리고 실제 인프라 상태 사이에 차이가 생긴 상태를 말한다.

보통은 특히 **Terraform 외부에서 실제 인프라가 변경되었을 때** 자주 문제가 된다.

예를 들어 다음 상황을 생각해보자.

* Terraform으로 Security Group 생성

* 이후 누군가 AWS 콘솔에서 규칙을 직접 수정

* Terraform 코드는 그대로

* state는 이전 상태를 기준으로 존재

이 경우 실제 AWS 상태와 Terraform이 기대하는 상태가 달라질 수 있다.

이것이 drift다.

---

## 6.2 drift가 왜 문제인가

Terraform은 일관된 상태를 전제로 변경 계획을 계산한다.

그런데 실제 상태가 몰래 바뀌어 있으면 다음 문제가 생길 수 있다.

* plan 결과가 예상과 다르게 나옴

* Terraform이 변경을 되돌리려 함

* 운영 중인 설정이 의도치 않게 덮어써질 수 있음

* 원인을 파악하기 어려움

즉, drift는 단순한 차이가 아니라

운영 안정성을 해칠 수 있는 상태 불일치다.

---

## 6.3 drift는 어떻게 발견하는가

가장 기본적인 방법은 `terraform plan`이다.

Terraform은 provider를 통해 실제 상태를 조회하고, 코드와 state를 비교해 차이를 계산한다.

즉, 주기적으로 plan을 확인하는 습관은 drift 탐지에도 중요하다.

---

## 7. terraform state 명령 기초

Terraform은 state를 다루기 위한 `terraform state` 명령군을 제공한다.

---

## 7.1 state list

현재 state에 어떤 리소스가 기록되어 있는지 확인하는 명령이다.

```
terraform state list
```

예상 결과 예시:

```
aws_vpc.main
aws_subnet.public
aws_internet_gateway.igw
aws_instance.web
```

즉, Terraform이 현재 관리 중인 리소스 주소 목록을 보여준다.

---

## 7.2 state show

특정 리소스의 state 정보를 확인하는 명령이다.

```
terraform state show aws_vpc.main
```

이 명령은 해당 리소스에 대해 state에 저장된 속성 정보를 보여준다.

즉, 현재 Terraform이 그 리소스를 어떤 값으로 알고 있는지 확인할 수 있다.

---

## 7.3 왜 state 명령을 알아야 하는가

* 현재 Terraform이 어떤 리소스를 관리 중인지 확인

* 리소스 주소를 확인

* state와 코드 매핑을 추적

* 문제 상황 분석

즉, `terraform state` 명령은

직접 수정을 위한 도구라기보다 **운영 중 상태를 진단하는 도구**다.

---

## 8. backend란 무엇인가

## 8.1 backend의 의미

Terraform backend는 **state 파일을 어디에 저장하고 어떻게 관리할 것인지**를 정의하는 구성이다.

즉, backend는 Terraform의 state 저장소 설정이다.

local state에서는 파일이 현재 디렉터리에 저장되지만,

backend를 사용하면 state를 외부 저장소로 옮길 수 있다.

예를 들어 다음과 같은 저장 위치를 생각할 수 있다.

* 로컬 파일

* S3

* Terraform Cloud

* 기타 원격 저장소

---

## 8.2 왜 backend가 필요한가

backend가 필요한 이유는 다음과 같다.

* 여러 사람이 같은 state를 공유해야 함

* state를 중앙에서 관리해야 함

* 로컬 파일 유실 위험을 줄여야 함

* 협업 시 기준 상태를 하나로 맞춰야 함

즉, backend는 협업과 운영을 위한 state 중앙화 장치다.

---

## 9. terraform 블록에서 backend 설정

backend는 `terraform` 블록 안에서 설정한다.

예시:

```
terraform {
  backend "s3" {
    bucket = "my-terraform-state-bucket"
    key    = "network/dev/terraform.tfstate"
    region = "ap-northeast-2"
  }
}
```

이 설정의 의미는 다음과 같다.

* state 파일을 S3 버킷에 저장

* 해당 state 파일의 경로는 `network/dev/terraform.tfstate`

* S3 버킷이 있는 리전은 `ap-northeast-2`

즉, 이제 state는 로컬 파일이 아니라 S3에 저장된다.

---

## 10. S3 backend

## 10.1 왜 S3 backend를 많이 사용하는가

AWS 기반 Terraform 운영에서 S3 backend는 매우 흔한 선택이다.

그 이유는 다음과 같다.

* AWS 계정 안에서 관리 가능

* 중앙 저장소 역할 수행 가능

* 버킷 단위 접근 제어 가능

* 환경별 key 분리 가능

* 기존 AWS 인프라와 잘 통합됨

즉, AWS 환경에서는 S3가 state 저장소 역할을 자연스럽게 수행한다.

---

## 10.2 bucket, key, region의 의미

### `bucket`

state를 저장할 S3 버킷 이름

### `key`

버킷 안에서 state 파일이 저장될 경로

예:

* `network/dev/terraform.tfstate`

* `app/prod/terraform.tfstate`

### `region`

S3 버킷이 위치한 리전

즉, `key`를 잘 설계하면 환경별 state 파일을 분리할 수 있다.

---

## 10.3 local state와 S3 backend 비교

### local state

* 개인 실습에 적합

* 파일이 로컬에 존재

* 협업에 취약

### S3 backend

* 중앙 저장 가능

* 여러 사람이 같은 state 기준 사용 가능

* 협업과 운영에 적합

즉, 실무 운영은 원격 backend가 거의 필수에 가깝다.

---

## 11. init -reconfigure 와 -migrate-state

backend 설정을 바꾸면 Terraform은 다시 초기화가 필요하다.

이때 자주 보게 되는 옵션이 `-reconfigure`, `-migrate-state`다.

---

## 11.1 `terraform init -reconfigure`

이 옵션은 Terraform에게

“기존 backend 설정을 무시하고, 현재 코드 기준으로 backend를 다시 구성하라”는 의미다.

예시:

```
terraform init -reconfigure
```

주로 다음 상황에서 사용한다.

* backend 설정이 바뀌었음

* 기존 초기화 정보와 다르게 새 backend를 다시 잡고 싶음

* 이전 backend 연결 정보를 새로 해석하고 싶음

즉, `-reconfigure`는 backend 연결 정보를 다시 맞추는 데 사용한다.

---

## 11.2 `terraform init -migrate-state`

이 옵션은 backend 구성을 바꾸는 과정에서

기존 state를 새 backend로 옮기겠다는 의미다.

예시:

```
terraform init -migrate-state
```

주로 다음 상황에서 사용한다.

* local state를 S3 backend로 옮길 때

* 기존 backend에서 다른 backend로 이전할 때

즉, `-migrate-state`는 단순 재설정이 아니라

**기존 state 이동까지 포함**하는 옵션이다.

---

## 11.3 차이점

### `-reconfigure`

* backend 설정 재초기화

* state 이전이 핵심은 아님

* 연결 정보를 다시 잡는 목적

### `-migrate-state`

* state를 기존 위치에서 새 backend로 이동

* backend 이전 시 사용

즉, 다음처럼 기억하면 좋다.

* 설정 다시 잡기 → `-reconfigure`

* state까지 옮기기 → `-migrate-state`

---

## 12. workspace와 환경 분리

## 12.1 workspace란 무엇인가

workspace는 같은 Terraform 구성에서 **state를 논리적으로 분리하는 기능**이다.

즉, 같은 코드지만 서로 다른 state를 가지도록 할 수 있다.

예를 들어 다음 workspace를 생각할 수 있다.

* `default`

* `dev`

* `stage`

* `prod`

이 경우 같은 코드라도 workspace별로 다른 state를 가진다.

---

## 12.2 왜 필요한가

같은 코드 구조를 여러 환경에 적용하고 싶을 때가 많다.

예:

* 개발 환경

* 테스트 환경

* 운영 환경

이때 workspace를 사용하면 state를 구분할 수 있다.

즉, 같은 코드라도

* dev workspace에서는 dev 리소스 관리

* prod workspace에서는 prod 리소스 관리

가 가능하다.

---

## 12.3 기본 명령

현재 workspace 확인:

```
terraform workspace show
```

workspace 목록 확인:

```
terraform workspace list
```

새 workspace 생성:

```
terraform workspace new dev
```

workspace 전환:

```
terraform workspace select prod
```

---

## 12.4 workspace 사용 시 주의

workspace는 편리하지만 무조건 만능은 아니다.

특히 큰 규모의 운영에서는 다음 점을 주의해야 한다.

* 환경 차이가 너무 크면 같은 코드만으로 관리하기 어려울 수 있음

* 변수값과 naming 규칙 분리가 함께 필요함

* state만 분리된다고 해서 리소스 이름 충돌이 자동 해결되는 것은 아님

즉, workspace는 환경 분리의 한 방법이지

모든 환경 전략을 자동으로 해결해주는 기능은 아니다.

---

## 13. 협업 시 주의사항

Terraform 협업에서는 코드보다 state 관리가 더 위험한 지점이 되는 경우가 많다.

즉, 협업 시 핵심은 “누가 어떤 코드를 썼는가”뿐 아니라

“누가 어떤 state를 기준으로 작업했는가”다.

---

## 13.1 local state로 협업하지 않는 것이 좋다

각자 로컬에 state를 두면 같은 코드라도 서로 다른 기준으로 작업하게 된다.

이 경우 plan/apply 결과가 엇갈릴 수 있다.

즉, 협업에서는 중앙 backend를 사용해야 한다.

---

## 13.2 콘솔 수동 변경을 최소화해야 한다

누군가 AWS 콘솔에서 직접 리소스를 수정하면 drift가 생길 수 있다.

이런 변경이 누적되면 Terraform 코드가 실제 상태를 설명하지 못하게 된다.

즉, 가능한 한 인프라 변경은 Terraform을 통해 수행해야 한다.

---

## 13.3 state 파일을 임의 수정하지 않는 것이 좋다

state는 매우 중요한 운영 데이터다.

수동 편집은 위험하며, 잘못 수정하면 Terraform이 리소스 매핑을 잃을 수 있다.

입문 단계에서는 state 파일을 열어 구조를 보는 정도는 가능하지만,

직접 수정하는 방식은 권장하지 않는다.

---

## 13.4 backend 경로 설계를 명확히 해야 한다

S3 backend를 사용할 때 `key` 설계를 대충 하면

환경 간 state 충돌이 생길 수 있다.

예:

* dev와 prod가 같은 state 경로 사용

* 프로젝트별 경로 구분이 없음

즉, `key`는 환경/프로젝트/구성 단위별로 명확히 나눠야 한다.

---

## 13.5 workspace를 써도 naming 충돌은 따로 관리해야 한다

workspace가 다르다고 해서 AWS 리소스 이름이 자동으로 구분되는 것은 아니다.

예를 들어 S3 버킷 이름, IAM 역할 이름 등은 별도 naming 전략이 필요할 수 있다.

즉, state 분리와 리소스 naming 전략은 별개로 봐야 한다.

---

## 14. 운영 관점에서 정리

실무에서 Terraform을 안정적으로 운영하려면 다음 원칙이 중요하다.

* state는 매우 중요한 운영 자산으로 봐야 함

* 개인 실습 외에는 local state 의존을 줄이는 것이 좋음

* 중앙 backend를 사용해야 함

* drift를 줄이기 위해 콘솔 수동 변경을 최소화해야 함

* plan 결과를 자주 확인해야 함

* workspace나 backend key로 환경을 분리할 수 있어야 함

즉, Terraform 운영의 핵심은 코드 작성뿐 아니라

**state를 안전하게 관리하는 체계**를 갖추는 것이다.

---

## 15. 정리

* state는 Terraform이 관리 중인 리소스와 실제 인프라의 연결 정보를 저장하는 데이터다.

* local state는 개인 실습에는 적합하지만 협업에는 취약하다.

* drift는 코드/state/실제 인프라 사이에 불일치가 생긴 상태다.

* `terraform state list`, `terraform state show`로 현재 관리 중인 state를 확인할 수 있다.

* backend는 state를 어디에 저장하고 어떻게 관리할지 정하는 설정이다.

* S3 backend는 AWS 환경에서 대표적인 원격 state 저장 방식이다.

* `terraform init -reconfigure`는 backend 설정 재초기화, `migrate-state`는 state 이전에 사용한다.

* workspace는 같은 코드에서 서로 다른 state를 분리하는 기능이다.

* 협업에서는 중앙 backend, drift 최소화, 명확한 경로 설계와 naming 전략이 중요하다.

# 실습. Terraform State, Backend, 협업 방식 실습

## 실습 목표

이 실습에서는 다음을 확인한다.

* local state 파일 생성과 확인

* `terraform state list`, `terraform state show` 사용

* drift 개념 체감

* S3 backend 설정 구조 이해

* `init -reconfigure`, `init -migrate-state` 사용 흐름 이해

* workspace 생성 및 전환 실습

---

## 실습 1. local state 생성 확인

### 실습 목적

Terraform apply 이후 local state 파일이 생성되고, Terraform이 리소스를 추적한다는 점을 확인한다.

---

### 예제 코드

`main.tf`

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

resource "aws_vpc" "main" {
  cidr_block = "10.20.0.0/16"

  tags = {
    Name = "state-lab-vpc"
  }
}
```

---

### 실행 순서

```
terraform init
terraform apply -auto-approve
```

---

### 확인 포인트

적용이 끝난 뒤 현재 디렉터리에 다음 파일이 생겼는지 확인한다.

* `terraform.tfstate`

* `terraform.tfstate.backup`

### 설명

이 시점부터 Terraform은 `aws_vpc.main` 이 실제 어떤 VPC와 연결되는지 state에 기록한다.

즉, 다음 실행부터는 같은 코드를 다시 적용해도 무조건 새 VPC를 만드는 것이 아니라 state를 기준으로 현재 상태를 판단한다.

---

## 실습 2. terraform state list 사용

### 실습 목적

Terraform이 현재 어떤 리소스를 관리 중인지 확인한다.

---

### 실행 명령

```
terraform state list
```

---

### 기대 결과 예시

```
aws_vpc.main
```

---

### 설명

이 결과는 Terraform state 안에 현재 `aws_vpc.main` 리소스가 기록되어 있다는 뜻이다.

즉, Terraform은 이 리소스를 자신이 관리하는 대상으로 인식하고 있다.

---

## 실습 3. terraform state show 사용

### 실습 목적

특정 리소스의 state 정보를 확인한다.

---

### 실행 명령

```
terraform state show aws_vpc.main
```

---

### 확인 포인트

다음 같은 속성을 확인할 수 있다.

* VPC ID

* CIDR 블록

* 태그 정보

* 기타 리소스 속성

즉, Terraform이 이 리소스를 어떤 값으로 알고 있는지 확인할 수 있다.

---

## 실습 4. drift 개념 체감하기

### 실습 목적

Terraform 외부에서 실제 리소스를 수정했을 때 drift가 어떤 의미인지 이해한다.

---

### 실습 방법

1. Terraform으로 VPC를 생성한다.

2. AWS 콘솔에서 해당 VPC의 Name 태그를 직접 변경한다.

3. 다시 `terraform plan`을 실행한다.

---

### 실행 명령

```
terraform plan
```

---

### 확인 포인트

Terraform은 코드 기준 Name 태그와 실제 AWS의 태그가 다르다는 점을 감지하고,

이를 다시 맞추려는 변경 계획을 보여줄 수 있다.

즉, drift는 다음 흐름으로 이해하면 된다.

* 코드 기준 상태

* state 기준 관리 정보

* 실제 AWS 상태

* 이 셋이 어긋남

---

## 실습 5. S3 backend 설정 작성

### 실습 목적

local state 대신 S3 backend를 사용하는 구성을 이해한다.

---

### 예제 코드

`main.tf`의 `terraform` 블록 예시:

```
terraform {

  backend "s3" {
    bucket = "my-terraform-state-bucket"
    key    = "state-lab/dev/terraform.tfstate"
    region = "ap-northeast-2"
  }
  
	required_providers {
		aws = {
			source  = "hashicorp/aws"
			version = "6.41.0"
		}
	}
}
```

---

### 설명

이 설정은 state를 로컬이 아니라 S3에 저장하도록 한다.

단, 실제로는 해당 S3 버킷이 미리 존재해야 한다.

즉, backend는 Terraform이 자동으로 만드는 인프라가 아니라

Terraform이 state를 저장할 위치를 알려주는 설정이다.

---

## 실습 6. backend 재초기화

### 실습 목적

backend 설정 변경 후 재초기화하는 방법을 이해한다.

---

### 실행 명령

```
terraform init -reconfigure
```

---

### 설명

이 명령은 현재 코드의 backend 설정을 기준으로

Terraform의 backend 연결 정보를 다시 초기화한다.

즉, backend를 새로 잡거나 변경한 뒤에는 자주 사용하는 흐름이다.

---

## 실습 7. local state를 S3로 마이그레이션하는 흐름 이해

### 실습 목적

기존 local state를 원격 backend로 옮기는 개념을 이해한다.

---

### 실행 명령 예시

```
terraform init -migrate-state
```

---

### 설명

이 명령은 기존 local state를 새 backend로 이동하는 흐름에서 사용한다.

즉, 단순히 backend 설정만 다시 읽는 것이 아니라

기존 state를 실제로 옮기는 작업까지 포함한다.

---

## 실습 8. workspace 생성과 전환

### 실습 목적

같은 코드에서 state를 분리하는 workspace 기능을 이해한다.

---

### 현재 workspace 확인

```
terraform workspace show
```

---

### workspace 목록 확인

```
terraform workspace list
```

---

### 새 workspace 생성

```
terraform workspace new dev
terraform workspace new prod
```

---

### workspace 전환

```
terraform workspace select dev
terraform workspace select prod
```

---

### 확인 포인트

workspace가 달라지면 같은 코드라도 서로 다른 state를 가진다.

즉, dev workspace와 prod workspace는 서로 독립적인 state 기준으로 동작한다.

---

## 실습 9. workspace와 naming 전략 함께 보기

### 실습 목적

workspace가 state를 분리하지만 리소스 이름 충돌은 별도로 고려해야 한다는 점을 이해한다.

---

### 예제 코드

```
resource "aws_vpc" "main" {
  cidr_block = terraform.workspace == "prod" ? "10.30.0.0/16" : "10.40.0.0/16"

  tags = {
    Name = "vpc-${terraform.workspace}"
  }
}
```

---

### 설명

이 코드에서는 workspace 이름을 태그에 반영한다.

즉, dev workspace에서는 `vpc-dev`, prod workspace에서는 `vpc-prod` 태그가 붙는다.

이런 방식은 workspace 분리와 naming 전략을 함께 사용하는 간단한 예다.

---

## 실습 10. 전체 흐름 정리

1. local state 생성

2. state list/show로 현재 관리 리소스 확인

3. 콘솔 수동 변경으로 drift 개념 체감

4. backend 설정으로 원격 state 개념 이해

5. `reconfigure`, `migrate-state` 차이 이해

6. workspace 생성과 전환으로 state 분리 확인

즉, Terraform 운영에서 중요한 것은 단순 apply가 아니라

**state를 어디에 두고, 어떻게 공유하고, 어떻게 분리하며, 어떻게 일관성을 유지할 것인가**라는 점이다.