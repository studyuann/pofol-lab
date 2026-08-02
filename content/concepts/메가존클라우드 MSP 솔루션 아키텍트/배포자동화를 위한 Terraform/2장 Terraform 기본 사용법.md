---
title: "2장 Terraform 기본 사용법"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "배포자동화를 위한 Terraform"]
is_public: true
draft: false
---

# 2장. Terraform 기본 사용법

## 1. 학습 목표

* Terraform 작업 디렉터리의 의미를 이해한다.

* Terraform 설정 파일의 기본 구조를 이해한다.

* `terraform init`, `fmt`, `validate`, `plan`, `apply`, `destroy` 명령의 역할을 이해한다.

* Terraform이 현재 상태와 원하는 상태를 비교하는 방식을 이해한다.

* 로컬 실습을 통해 Terraform의 기본 실행 흐름을 익힌다.

* state 파일의 의미와 역할을 이해한다.

---

## 2. Terraform 기본 사용법 개요

Terraform은 현재 작업 디렉터리에 있는 설정 파일을 읽고 동작한다.

즉, Terraform은 단순히 명령만 실행하는 도구가 아니라,

**현재 디렉터리에 어떤** `.tf` **파일이 있는지**,

그리고 그 파일에 **어떤 원하는 상태가 정의되어 있는지**를 기준으로 동작한다.

우선 **로컬 환경에서 Terraform의 기본 원리**를 먼저 익힌다.

이 방식의 장점은 다음과 같다.

* 클라우드 비용 걱정 없이 실습 가능

* 인증 문제 없이 Terraform 자체 흐름에 집중 가능

* `init → plan → apply → destroy` 흐름을 단순하게 이해 가능

* state 파일의 역할을 눈으로 확인 가능

---

## 3. 작업 디렉터리와 설정 파일

Terraform은 현재 디렉터리 안의 `.tf` 파일을 모두 읽는다.

즉, 예를 들어 `terraform-basic`이라는 폴더 안에 `main.tf` 파일이 있다면,

Terraform은 그 디렉터리를 하나의 작업 단위처럼 인식한다.

앞서 만든 실습용 디렉터리를 사용한다.

```
cd terraform-basic
mkdir ex1
```

이제 이 디렉터리 안에서 Terraform 설정 파일을 만들고 명령을 실행하게 된다.

### 3.1 `.tf` 파일

Terraform 설정 파일은 `.tf` 확장자를 사용한다.

예를 들면 다음과 같은 파일명을 자주 사용한다.

* `main.tf`

* `variables.tf`

* `outputs.tf`

* `provider.tf`

파일명은 관례일 뿐이며, 꼭 저 이름을 써야 하는 것은 아니다.

중요한 것은 **확장자가** `.tf`**여야 Terraform이 읽는다는 점**이다.

예를 들어 `main.tf.txt`처럼 저장하면 Terraform이 설정 파일로 인식하지 못한다.

### 3.2 여러 파일을 하나처럼 읽는 방식

Terraform은 현재 디렉터리 안의 `.tf` 파일을 모두 읽어서 하나의 구성처럼 처리한다.

예를 들어 다음처럼 나눌 수 있다.

`main.tf`

```
resource "local_file" "example" {
  filename = "hello.txt"
  content  = "Hello Terraform"
}
```

`outputs.tf`

```
output "file_name" {
  value = local_file.example.filename
}
```

이 두 파일은 Terraform 입장에서는 따로 노는 것이 아니라,

하나의 설정 묶음처럼 함께 처리된다.

즉, 파일을 나누는 목적은 실행 순서 때문이 아니라 **가독성과 관리 편의성** 때문이다.

---

## 4. 로컬 실습에 사용할 Provider

이번 장에서는 AWS Provider 대신 **local Provider**를 사용한다.

local Provider는 클라우드 자원을 만드는 것이 아니라,

현재 로컬 시스템에서 파일 같은 리소스를 Terraform으로 관리할 수 있게 해준다.

즉, Terraform이 다음과 같이 동작하는 것을 눈으로 바로 확인할 수 있다.

* 원하는 상태 정의

* 계획 확인

* 적용

* 결과 확인

* 삭제

---

## 5. 첫 번째 Terraform 설정 파일 작성

먼저 가장 단순한 로컬 파일 생성 예제를 작성한다.

파일명: `main.tf`

```
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

resource "local_file" "example" {
  filename = "hello.txt"
  content  = "Hello Terraform"
}
```

이 코드의 의미를 하나씩 보면 다음과 같다.

### 5.1 `terraform` 블록

`terraform` 블록은 Terraform 자체 동작과 관련된 설정을 정의한다.

```
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}
```

### `required_version`

```
required_version = ">= 1.5.0"
```

현재 설정이 Terraform 1.5.0 이상 버전에서 동작해야 한다는 의미다.

이 설정을 두는 이유는 버전 차이로 인한 예기치 않은 문제를 줄이기 위해서다.

실무나 팀 실습에서는 버전 불일치 때문에 문법이나 동작 차이가 생길 수 있으므로,

어느 정도의 버전 기준을 명시하는 것이 좋다.

### `required_providers`

```
required_providers {
  local = {
    source  = "hashicorp/local"
    version = "~> 2.5"
  }
}
```

이 블록은 현재 작업에서 어떤 Provider를 사용할지 정의한다.

* `local`

  사용할 Provider 이름이다.

* `source = "hashicorp/local"`

  HashiCorp가 제공하는 공식 local Provider를 사용한다는 뜻이다.

* `version = "~> 2.5"`

  2.5 계열 버전을 사용하겠다는 의미다.

  너무 큰 버전 변화로 인한 동작 차이를 줄이기 위해 버전 범위를 지정한다.

### 5.2 `resource` 블록

```
resource "local_file" "example" {
  filename = "hello.txt"
  content  = "Hello Terraform"
}
```

이 블록은 Terraform이 실제로 관리할 리소스를 정의한다.

### `resource`

Terraform이 관리할 실제 대상을 선언할 때 사용한다.

### `"local_file"`

local Provider가 제공하는 리소스 타입이다.

로컬 파일을 생성하고 관리하는 리소스라고 이해하면 된다.

### `"example"`

이 리소스의 로컬 이름이다.

Terraform 코드 안에서 이 이름으로 참조할 수 있다.

### `filename`

생성할 파일 이름이다.

현재 디렉터리에 `hello.txt` 파일이 생성된다.

### `content`

파일 안에 들어갈 내용이다.

즉, 이 코드는 다음 원하는 상태를 선언한 것이다.

* 현재 작업 디렉터리에 `hello.txt`라는 파일이 있어야 함

* 그 파일 안에는 `Hello Terraform` 문자열이 들어 있어야 함

---

## 6. `terraform init`

### 6.1 초기화

Terraform은 설정 파일을 작성했다고 바로 실행되는 것이 아니다.

먼저 작업 디렉터리를 초기화해야 한다.

```
terraform init
```

### 6.2 `init`이 하는 일

이 명령은 다음 작업을 수행한다.

* 현재 디렉터리의 Terraform 설정 파일을 읽는다.

* 어떤 Provider가 필요한지 분석한다.

* 필요한 Provider 플러그인을 다운로드한다.

* 작업 디렉터리를 Terraform 실행 가능 상태로 준비한다.

즉, `init`은 Terraform 작업의 시작점이다.

### 6.3 실행 결과에서 확인할 점

정상적으로 실행되면 다음과 같은 흐름을 볼 수 있다.

* local Provider를 찾음

* local Provider를 설치함

* Terraform이 초기화 완료 메시지를 보여줌

이 과정이 끝나면 `.terraform` 디렉터리와 lock 파일이 생성될 수 있다.

### 6.4 `.terraform` 디렉터리

`terraform init` 이후 `.terraform` 디렉터리가 생성된다.

이 디렉터리에는 Terraform이 사용하는 내부 데이터와 Provider 관련 파일이 저장된다.

즉, 이 디렉터리는 사용자가 직접 수정하는 용도가 아니라, Terraform이 관리하는 작업 디렉터리 내부 정보라고 이해하면 된다.

### 6.5 언제 다시 실행하는가

다음 경우에는 `init`을 다시 실행하는 것이 좋다.

* 처음 해당 디렉터리에서 Terraform을 사용할 때

* Provider 설정을 변경했을 때

* 모듈을 추가했을 때

백엔드 설정을 변경했을 때

### 백엔드 설정을 변경했을 때 `terraform init`을 다시 실행하는 이유

Terraform에서 **백엔드(backend)** 는 state 파일을 어디에 저장하고, 어떻게 관리할지를 결정하는 설정이다.

기본적으로 Terraform은 별도 설정이 없으면 현재 작업 디렉터리에 `terraform.tfstate` 파일을 생성하여 로컬에 state를 저장한다.

하지만 실무에서는 로컬 파일 대신 원격 저장소를 사용하는 경우가 많다.

예를 들면 다음과 같다.

* S3에 state 저장

* Terraform Cloud에 state 저장

* Azure Storage에 state 저장

* GCS에 state 저장

즉, 백엔드는 **Terraform 상태 정보를 보관하는 위치와 방식**을 정의하는 설정이다.

Terraform은 `init` 시점에 현재 디렉터리의 설정을 읽고,

어떤 Provider를 사용할지뿐 아니라 **어떤 백엔드를 사용할지도 함께 초기화**한다.

따라서 백엔드 설정이 바뀌면 Terraform 입장에서는 다음과 같은 중요한 변화가 생긴다.

* state 파일 저장 위치가 바뀜

* state 접근 방식이 바뀜

* 잠금(lock) 방식이 바뀔 수 있음

* 인증 방식이 바뀔 수 있음

* 기존 state를 새 백엔드로 옮겨야 할 수 있음

이런 이유로 백엔드 설정을 바꾼 뒤에는 `terraform init`을 다시 실행해야 한다.

---

### 예시 1. 로컬 state에서 S3 백엔드로 변경하는 경우

처음에는 백엔드 설정 없이 로컬에서 시작했다고 가정해보자.

```
resource "aws_instance" "web" {
  ami           = "ami-xxxxxxxxxxxxxxxxx"
  instance_type = "t3.micro"
}
```

이 상태에서는 기본적으로 `terraform.tfstate` 파일이 현재 디렉터리에 저장된다.

그런데 이후 팀 협업을 위해 S3 백엔드로 바꾸고 싶을 수 있다.

```
terraform {
  backend "s3" {
    bucket = "my-terraform-state-bucket"
    key    = "dev/ec2/terraform.tfstate"
    region = "ap-northeast-2"
  }
}
```

이렇게 되면 state 저장 방식이 완전히 달라진다.

* 이전: 로컬 파일에 저장

* 이후: S3 객체로 저장

이 상태에서 `terraform init`을 다시 실행하면 Terraform은

“백엔드 설정이 바뀌었음”을 감지하고 필요한 초기화 작업을 다시 수행한다.

이때 Terraform은 종종 기존 state를 새 백엔드로 옮길지 묻기도 한다.

즉, 단순히 설정 파일 한 줄이 바뀐 것이 아니라,

**Terraform이 상태를 관리하는 기반 자체가 달라진 것**이기 때문에 재초기화가 필요함.

---

### 예시 2. 같은 S3 백엔드라도 설정 값이 바뀌는 경우

이미 S3 백엔드를 쓰고 있더라도 다음 값이 바뀌면 다시 init이 필요할 수 있다.

* `bucket` 이름 변경

* `key` 경로 변경

* `region` 변경

* DynamoDB 잠금 테이블 관련 설정 변경

* 프로파일 또는 인증 관련 방식 변경

예를 들어 아래처럼 `key` 값을 바꾸면,

기존:

```
terraform {
  backend "s3" {
    bucket = "my-terraform-state-bucket"
    key    = "dev/app/terraform.tfstate"
    region = "ap-northeast-2"
  }
}
```

변경 후:

```
terraform {
  backend "s3" {
    bucket = "my-terraform-state-bucket"
    key    = "prod/app/terraform.tfstate"
    region = "ap-northeast-2"
  }
}
```

Terraform 입장에서는 state 파일 위치가 달라진다.

즉, 이전 상태 파일과 이후 상태 파일이 서로 다른 대상으로 취급될 수 있다.

이 경우에도 `terraform init`을 다시 실행해서

새로운 백엔드 설정 기준으로 작업 환경을 다시 맞춰야 한다.

---

## 7. `terraform fmt`

### 7.1 코드 정렬

Terraform 코드를 작성한 뒤에는 `terraform fmt`를 실행하는 습관이 좋다.

```
terraform fmt
```

### 7.2 역할

이 명령은 코드의 형식을 Terraform 표준 스타일에 맞게 자동 정렬한다.

예를 들면 다음을 정리한다.

* 들여쓰기

* 공백

* 블록 정렬

* 표현식 정렬

즉, 코드 의미를 바꾸는 것이 아니라 **형식을 정리하는 명령**이다.

### 7.3 왜 필요한가

Terraform 코드는 사람이 자주 읽고 검토한다.

따라서 코드 형식이 일정해야 다음 장점이 있다.

* 가독성이 좋아짐

* 협업 시 스타일이 통일됨

* 리뷰가 쉬워짐

* 불필요한 diff가 줄어듦

파일을 작성하거나 수정한 뒤에는 `terraform fmt`를 먼저 실행하는 습관이 좋다.

---

## 8. `terraform validate`

### 8.1 문법 검사

다음으로 현재 설정 파일이 문법적으로 올바른지 검사한다.

```
terraform validate
```

### 8.2 역할

이 명령은 다음을 확인한다.

* Terraform 문법이 맞는지

* 블록 구조가 올바른지

* 기본적인 참조 구문에 문제가 없는지

정상이라면 보통 다음과 비슷한 메시지가 출력된다.

```
Success! The configuration is valid.
```

### 8.3 주의할 점

`validate`가 성공했다고 해서 모든 것이 끝난 것은 아니다.

이 명령은 문법과 구조를 검사하는 것이지,

실제 원하는 결과가 정확히 만들어질지까지 보장하는 것은 아니다.

즉, `validate`는 **문법 점검 단계**라고 이해하면 된다.

---

## 9. `terraform plan`

### 9.1 변경 예정 사항 확인

이제 Terraform이 현재 상태와 코드 정의를 비교해서 어떤 작업을 할지 계산하도록 한다.

```
terraform plan
```

### 9.2 역할

`plan`은 실제로 리소스를 만들지 않는다.

대신 다음을 보여준다.

* 어떤 리소스를 생성할지

* 어떤 속성 값으로 생성할지

* 변경 또는 삭제 대상이 있는지

이 예제에서는 현재 아직 `hello.txt` 파일이 없으므로, Terraform은 새 파일을 생성해야 한다고 판단한다.

### 9.3 출력에서 볼 수 있는 기호

`plan` 결과에서는 다음 기호를 자주 본다.

* `+` : 새로 생성

* `~` : 수정

* : 삭제

이번 실습에서는 `local_file.example` 리소스가 생성될 예정이므로 `+` 기호가 보일 가능성이 크다.

### 9.4 왜 중요한가

`plan`은 Terraform의 핵심 명령 중 하나다.

실제 적용 전에 무엇이 바뀌는지 먼저 보여주기 때문이다.

즉, `plan`은 “지금 이 코드를 적용하면 어떤 일이 생기는가”를 사전에 검토하는 단계다.

---

## 10. `terraform apply`

### 10.1 실제 반영

이제 계획된 내용을 실제로 적용한다.

```
terraform apply
```

실행하면 Terraform은 변경 내용을 다시 보여주고,

정말 적용할지 확인을 요청한다.

확인을 위해 `yes`를 입력하면 적용이 진행된다.

### 10.2 실행 결과

정상적으로 완료되면 현재 디렉터리에 `hello.txt` 파일이 생성된다.

즉, 다음 원하는 상태가 실제로 반영된 것이다.

* `hello.txt` 파일 존재

* 파일 내용은 `Hello Terraform`

### 10.3 확인 방법

리눅스나 macOS에서는 다음처럼 확인할 수 있다.

```
ls
cat hello.txt
```

Windows PowerShell에서는 다음처럼 확인할 수 있다.

```
Get-ChildItem
Get-Content hello.txt
```

이 과정을 통해 Terraform이 단순히 코드를 읽는 것이 아니라,

실제로 정의된 상태를 만족하도록 리소스를 생성한다는 점을 확인할 수 있다.

---

## 11. state 파일 확인

### 11.1 `terraform.tfstate`

`apply`가 끝나면 `terraform.tfstate` 파일이 생성된다.

이 파일은 Terraform이 현재 관리 중인 상태를 저장하는 파일이다.

즉, Terraform은 다음 정보를 이 파일에 기록한다.

* 어떤 리소스를 만들었는지

* 그 리소스의 현재 속성이 무엇인지

* Terraform 코드와 실제 리소스를 어떻게 연결하고 있는지

### 11.2 state가 필요한 이유

Terraform은 다음 실행 때 단순히 코드를 다시 읽는 것만으로 동작하지 않는다.

**코드 + state + 실제 현재 상태**를 비교하여 변경사항을 계산한다.

예를 들어 현재 state에는 `hello.txt` 파일이 있다고 기록되어 있다.

그러면 다음 `plan` 실행 시 Terraform은 “이미 원하는 파일이 존재하는가”를 판단할 수 있다.

즉, state는 Terraform이 자신의 관리 대상을 기억하는 기준이다.

---

## 12. 변경 사항 반영 실습

이제 기존 파일 내용을 바꿔보자.

기존 코드:

```
resource "local_file" "example" {
  filename = "hello.txt"
  content  = "Hello Terraform"
}
```

다음과 같이 수정한다.

```
resource "local_file" "example" {
  filename = "hello.txt"
  content  = "Hello Terraform Updated"
}
```

이제 다시 다음 명령을 실행한다.

```
terraform fmt
terraform validate
terraform plan
```

### 12.1 무엇이 달라지는가

이번에는 파일이 새로 생성되는 것이 아니라,

기존 리소스의 내용이 바뀌는 방향으로 계획이 잡힌다.

Terraform은 다음처럼 판단한다.

* `hello.txt` 파일은 이미 존재함

* 하지만 원하는 내용이 달라졌음

* 따라서 현재 상태를 원하는 상태로 바꾸기 위해 수정이 필요함

즉, Terraform은 “현재 상태”와 “원하는 상태”의 차이를 계산해서 동작한다.

### 12.2 다시 적용

```
terraform apply
```

적용 후 파일 내용을 다시 확인하면 변경된 문자열이 들어가 있다.

이 실습은 Terraform의 핵심 개념을 잘 보여준다.

* 처음에는 생성

* 이후에는 변경

* 항상 원하는 상태를 기준으로 비교

---

## 13. `terraform destroy`

### 13.1 삭제

Terraform이 생성한 리소스를 삭제하려면 다음 명령을 사용한다.

```
terraform destroy
```

### 13.2 역할

이 명령은 현재 state를 기준으로 Terraform이 관리 중인 리소스를 찾아 삭제한다.

이번 실습에서는 `hello.txt` 파일이 삭제된다.

즉, Terraform은 단순히 생성만 하는 도구가 아니라,

자신이 관리하는 리소스의 수명주기 전체를 다룰 수 있다.

---

## 14. 정리

* Terraform은 현재 디렉터리의 `.tf` 파일을 기준으로 동작한다.

* `terraform init`은 작업 디렉터리를 초기화하고 Provider를 준비한다.

* `terraform fmt`는 코드 형식을 정리한다.

* `terraform validate`는 문법과 구조를 점검한다.

* `terraform plan`은 변경 예정 사항을 보여준다.

* `terraform apply`는 원하는 상태를 실제로 반영한다.

* `terraform.tfstate`는 Terraform이 관리 중인 상태를 기록하는 파일이다.

* `terraform destroy`는 Terraform이 생성한 리소스를 삭제한다.

즉, Terraform은 단순한 명령 실행 도구가 아니라,

**원하는 상태를 선언하고 현재 상태와 비교하여 맞춰가는 도구**라는 점이 가장 중요하다.