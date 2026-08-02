---
title: "3장 Terraform 블록과 Provider"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "배포자동화를 위한 Terraform"]
is_public: true
draft: false
---

# 3장. Terraform 블록과 Provider

## 장 목표

Terraform 코드를 구성하는 가장 기본적인 틀인 **블록(block)** 과 **Provider**를 이해한다.

* HCL의 기본 문법을 설명할 수 있음

* 블록과 인자의 차이를 구분할 수 있음

* `terraform` 블록의 역할을 설명할 수 있음

* `required_version`과 `required_providers`를 설정할 수 있음

* `provider` 블록의 역할을 설명할 수 있음

* AWS Provider를 기본 형태로 구성할 수 있음

* `terraform init`이 왜 필요한지 이해할 수 있음

* Terraform 코드와 Provider 다운로드의 관계를 설명할 수 있음

---

# 1. Terraform 코드를 이루는 기본 단위

Terraform 코드는 사람이 읽기 쉬운 선언형 언어인 **HCL(HashiCorp Configuration Language)** 로 작성한다.

HCL은 JSON처럼 기계적으로만 보이는 형식이 아니라, 사람이 인프라 구성을 읽고 수정하기 쉽게 설계된 문법이다.

Terraform 파일을 열어보면 다음과 같은 형태를 자주 보게 된다.

```
terraform {
  required_version = ">= 1.5.0"
}

provider "aws" {
  region = "ap-northeast-2"
}
```

겉보기에는 단순해 보이지만, 여기에는 Terraform 코드의 핵심 구조가 들어 있다.

* `terraform { ... }` → Terraform 자체에 대한 설정

* `provider "aws" { ... }` → AWS와 연결하기 위한 설정

즉, Terraform 코드는 단순히 “무엇을 만들겠다”만 적는 것이 아니라,

**어떤 도구 버전으로**, **어떤 플러그인을 이용해서**, **어느 대상 시스템에 작업할지**까지 함께 선언한다.

---

# 2. HCL 기본 구조

## 2.1 HCL은 어떻게 생겼는가

Terraform의 HCL은 기본적으로 다음 구조를 가진다.

```
블록종류 "라벨1" "라벨2" {
  인자이름 = 값
  인자이름 = 값
}
```

예를 들어 다음 코드를 보자.

```
provider "aws" {
  region = "ap-northeast-2"
}
```

여기서 구성 요소를 나누면 다음과 같다.

* `provider` → 블록 종류

* `"aws"` → 블록 라벨

* `{ ... }` → 블록 본문

* `region = "ap-northeast-2"` → 인자(argument)

즉, HCL은 **블록**을 중심으로 구성되고, 블록 안에 **인자**가 들어가는 방식이다.

---

## 2.2 블록과 인자

### 블록(block)

블록은 특정한 설정의 범위를 나타낸다.

쉽게 말하면 “어떤 종류의 설정 묶음”이라고 보면 된다.

예를 들면 다음과 같은 것들이 모두 블록이다.

* `terraform`

* `provider`

* `resource`

* `data`

* `variable`

* `output`

* `locals`

블록은 보통 다음처럼 중괄호로 감싼다.

```
terraform {
  ...
}
```

---

### 인자(argument)

인자는 블록 내부에서 실제 값을 지정하는 항목이다.

쉽게 말하면 “설정값”이다.

```
region = "ap-northeast-2"
```

여기서

* `region` → 인자 이름

* `"ap-northeast-2"` → 인자 값

이다.

---

## 2.3 블록과 인자 구분

* **블록**은 설정의 큰 틀

* **인자**는 그 틀 안에 들어가는 구체적인 값

예를 들어 다음 코드를 보자.

```
provider "aws" {
  region  = "ap-northeast-2"
  profile = "default"
}
```

여기서

* `provider "aws"` 는 블록

* `region`, `profile` 은 인자

이다.

---

# 3. terraform 블록

## 3.1 terraform 블록이란

`terraform` 블록은 **Terraform 자체의 동작 조건을 정의하는 블록**이다.

즉, 어떤 인프라를 만들지 설명하는 블록이 아니라, **이 코드를 어떤 규칙으로 실행할 것인지**를 지정하는 블록이다.

대표적으로 다음을 설정한다.

* Terraform 버전 조건

* 필요한 Provider 정보

* Backend 설정

* 실험적 기능 또는 기타 동작 옵션

가장 기본적인 예시는 다음과 같다.

```
terraform {
  required_version = ">= 1.5.0"
}
```

이 코드는 “이 Terraform 구성은 1.5.0 이상 버전에서 실행해야 한다”는 의미다.

---

## 3.2 왜 terraform 블록이 필요한가

Terraform은 버전에 따라 문법이나 동작이 조금씩 달라질 수 있다.

실무에서는 한 사람이 아니라 여러 사람이 같은 코드를 다루기 때문에, 누군가는 1.3 버전, 다른 사람은 1.8 버전을 사용하면 예상하지 못한 문제가 생길 수 있다.

예를 들어

* 어떤 문법은 최신 버전에서만 동작할 수 있음

* 어떤 Provider 버전은 특정 Terraform 버전과 호환되지 않을 수 있음

* 협업 환경에서 실행 결과가 달라질 수 있음

이런 문제를 줄이기 위해 `terraform` 블록에서 최소한의 실행 조건을 명시한다.

---

# 4. required\_version

## 4.1 required\_version의 의미

`required_version`은 현재 Terraform 코드가 **어떤 Terraform CLI 버전에서 실행 가능한지**를 제한하는 설정이다.

예시:

```
terraform {
  required_version = ">= 1.5.0"
}
```

의미:

* Terraform CLI 버전이 1.5.0 이상이어야 실행 가능함

---

## 4.2 버전 조건 표현 방식

Terraform에서는 비교 연산자를 사용해서 버전 범위를 지정할 수 있다.

### 예시 1. 특정 버전 이상

```
required_version = ">= 1.5.0"
```

1.5.0 이상이면 가능하다.

---

### 예시 2. 특정 버전만 허용

```
required_version = "= 1.5.7"
```

정확히 1.5.7일 때만 허용한다.

실무에서는 너무 딱 고정하면 관리가 불편할 수 있어서 자주 쓰지는 않지만, 재현성이 아주 중요할 때는 의미가 있다.

---

### 예시 3. 범위 지정

```
required_version = ">= 1.5.0, < 2.0.0"
```

1.5.0 이상이면서 2.0.0 미만 버전만 허용한다.

이 방식이 실무에서 비교적 많이 쓰인다.

너무 낮은 버전은 막고, 너무 큰 메이저 버전 변경도 막을 수 있기 때문이다.

---

## 4.3 왜 버전 상한도 고려하는가

인프라 자동화 도구는 **안정성**이 중요하다.

예를 들어 2.0.0에서 큰 변화가 생겼다면 기존 코드가 예상과 다르게 동작할 수도 있다.

그래서 아래처럼 범위를 두는 방식이 안전하다.

```
required_version = ">= 1.5.0, < 2.0.0"
```

이렇게 하면 검증한 큰 버전 범위 안에서만 실행되도록 통제할 수 있다.

---

# 5. required\_providers

## 5.1 Provider란 무엇인가

Terraform은 혼자서 AWS, GCP, Azure, GitHub, Kubernetes 같은 외부 시스템을 직접 제어하지 않는다.

실제로는 각 대상 시스템과 통신할 수 있는 **Provider 플러그인**을 통해 작업한다.

즉, Provider는 Terraform과 외부 API 사이를 연결하는 **중간 계층**이다.

예를 들어

* AWS 리소스를 만들려면 AWS Provider 필요

* GCP 리소스를 만들려면 Google Provider 필요

* Kubernetes 오브젝트를 다루려면 Kubernetes Provider 필요

---

## 5.2 required\_providers의 역할

`required_providers`는 이 Terraform 코드가 **어떤 Provider를 필요로 하는지**, 그리고 **어느 소스에서 어떤 버전 범위를 사용할지**를 선언하는 설정이다.

예시:

```
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

의미는 다음과 같다.

* `aws`라는 이름의 Provider를 사용함

* Provider 소스는 `hashicorp/aws`

* 버전은 5.x 계열에서 호환 범위 내 사용

---

## 5.3 source의 의미

```
source = "hashicorp/aws"
```

이 값은 Provider를 어디서 가져올지 지정한다.

* `hashicorp` → 제공자 네임스페이스

* `aws` → Provider 이름

즉, `hashicorp/aws`는 HashiCorp가 제공하는 AWS Provider라는 뜻이다.

Terraform은 `init` 시점에 이 정보를 보고 적절한 Provider 플러그인을 다운로드한다.

---

## 5.4 version의 의미

```
version = "~> 5.0"
```

이 설정은 Provider 버전 제약 조건이다.

`~> 5.0`은 보통 다음처럼 이해하면 된다.

* 5.x 대의 호환 가능한 최신 버전을 허용

* 6.0 이상은 허용하지 않음

버전을 아예 지정하지 않을 수도 있지만, 실무에서는 권장되지 않음.

이유는 다음과 같다.

* 새로운 Provider 버전에서 동작이 바뀔 수 있음

* 팀원마다 설치 시점이 달라 다른 버전을 받을 수 있음

* 예제 코드의 재현성이 떨어짐

그래서 최소한 대략적인 버전 범위는 고정하는 편이 좋다.

---

## 5.5 예제: terraform 블록 완성 형태

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
```

이 코드는 다음을 의미한다.

1. Terraform CLI는 1.5.0 이상 2.0.0 미만이어야 함

2. AWS Provider가 필요함

3. AWS Provider는 HashiCorp 공식 소스에서 가져옴

4. 버전은 5.x 계열을 사용함

이 블록은 이후의 `provider "aws"` 블록과 연결된다.

---

# 6. provider 블록

## 6.1 provider 블록의 역할

`required_providers`가 “무슨 Provider가 필요한가”를 선언하는 영역이라면,

`provider` 블록은 “그 Provider를 어떤 방식으로 사용할 것인가”를 설정하는 영역이다.

즉,

* `required_providers` → 설치 대상 선언

* `provider` → 실제 사용 설정

이라고 이해하면 된다.

---

## 6.2 가장 기본적인 AWS Provider 설정

```
provider "aws" {
  region = "ap-northeast-2"
}
```

이 코드는 AWS Provider를 사용하며, 기본 리전은 서울(`ap-northeast-2`)로 하겠다는 의미다.

이제부터 이 Terraform 코드에서 AWS 리소스를 생성하면 특별히 다른 설정이 없는 한 이 리전을 기준으로 동작한다.

---

## 6.3 provider 블록에서 자주 보는 항목

AWS Provider에서는 다음 항목을 자주 사용한다.

* `region`

* `profile`

* `access_key`

* `secret_key`

하지만 가능한 한 **액세스 키를 코드에 직접 적지 않는 방식**으로 진행하는 것이 좋다.

실습 환경에서는 보통 다음 중 하나를 사용한다.

1. AWS CLI로 미리 인증 설정

2. 환경 변수 사용

3. EC2 IAM Role 사용

초반 예제에서는 가장 단순하게 리전만 적고, 인증은 AWS CLI 기본 프로필을 사용하는 방식이 무난하다.

예시:

```
provider "aws" {
  region = "ap-northeast-2"
  profile = "default"
}
```

---

## 6.4 왜 Provider 설정이 필요한가

Terraform은 AWS에 리소스를 만들어야 해도, 기본적으로는 다음 정보를 알아야 한다.

* 어느 클라우드에 연결할지

* 어느 리전에 만들지

* 어떤 자격 증명으로 API를 호출할지

이 정보가 없으면 Terraform은 리소스를 선언해도 실제 작업 대상을 알 수 없다.

즉, `resource`는 “무엇을 만들지”를 쓰는 곳이고,

`provider`는 “어디에 만들지”를 쓰는 곳이다.

---

# 7. AWS Provider 기본 설정

## 7.1 실습용 최소 코드

다음은 AWS Provider를 사용하는 최소한의 예시 코드다.

파일명: `main.tf`

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
  region = "ap-northeast-2"
}
```

이 상태에서는 아직 아무 리소스도 만들지 않는다.

하지만 Terraform은 이미 다음을 이해한 상태가 된다.

* 어떤 버전으로 동작해야 하는지

* 어떤 Provider가 필요한지

* AWS Provider를 어떤 리전으로 사용할지

즉, **인프라를 만들 준비 단계**까지는 완료된 셈이다.

---

## 7.2 인증은 어떻게 처리되는가

이 코드에는 액세스 키가 없다.

그렇다면 Terraform은 어떻게 AWS에 인증할까?

AWS Provider는 일반적으로 AWS SDK의 인증 체인을 따른다.

실습에서는 보통 아래 순서 중 하나로 인증된다.

* 환경 변수

* `~/.aws/credentials`

* `~/.aws/config`

* IAM Role

예를 들어 AWS CLI에서 다음 명령으로 인증을 설정했다고 가정하자.

```
aws configure
```

그러면 입력한 자격 증명이 로컬 파일에 저장되고, Terraform의 AWS Provider가 이를 참조해 인증할 수 있다.

즉, Terraform이 AWS에 접속할 때 꼭 코드 안에 키를 적어야 하는 것은 아님.

---

# 8. init과 Provider 다운로드 연결

## 8.1 terraform init은 무엇을 하는가

Provider를 사용하려면 먼저 **필요한 플러그인을 다운로드하고 작업 디렉터리를 초기화**해야 한다.

이 작업을 수행하는 명령이 `terraform init`이다.

---

## 8.2 init이 수행하는 핵심 작업

`terraform init`은 보통 다음 작업을 수행한다.

### 1) 작업 디렉터리 초기화

현재 디렉터리를 Terraform 작업 디렉터리로 준비한다.

### 2) Provider 다운로드

`terraform` 블록 안의 `required_providers`를 보고 필요한 Provider를 다운로드한다.

### 3) 내부 메타데이터 생성

`.terraform` 디렉터리와 잠금 파일 등을 생성해 이후 명령이 동작할 수 있게 준비한다.

---

## 8.3 실제 실행 예시

작업 디렉터리에서 다음 명령을 실행한다.

```
terraform init
```

실행 후에는 보통 다음과 같은 변화가 생긴다.

* `.terraform/` 디렉터리 생성

* `.terraform.lock.hcl` 파일 생성

---

## 8.4 .terraform 디렉터리

이 디렉터리에는 다운로드된 Provider 플러그인과 내부 메타데이터가 저장된다.

즉, Terraform이 AWS Provider를 실제로 사용할 수 있게 만드는 준비물이 들어 있는 디렉터리다.

보통 사용자가 직접 수정하지 않음.

---

## 8.5 .terraform.lock.hcl 파일

이 파일은 Provider 잠금 파일이다.

실제로 어떤 Provider 버전이 선택되었는지를 기록한다.

예를 들어 코드에 이렇게 적었다고 해보자.

```
version = "~> 5.0"
```

이 조건은 5.x 범위 내에서 여러 버전이 가능하다.

그중 실제로 설치된 버전이 무엇인지 기록해 두는 것이 `.terraform.lock.hcl` 파일이다.

이 파일이 중요한 이유는 협업 시 재현성을 높여주기 때문이다.

* 내 PC에서 설치된 Provider 버전

* 팀원의 PC에서 설치되는 Provider 버전

이 달라지지 않도록 도와준다.

---

# 9. 실습: terraform 블록과 AWS Provider 구성

---

## 9.1 실습 목표

* `terraform` 블록 작성

* `required_version` 설정

* `required_providers` 설정

* `provider "aws"` 블록 작성

* `terraform init`으로 Provider 다운로드 확인

---

## 9.2 실습 디렉터리 생성

```
mkdir tf-provider-lab
cd tf-provider-lab
```

---

## 9.3 main.tf 작성

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
  region = "ap-northeast-2"
}
```

---

## 9.4 코드 형식 정리

```
terraform fmt
```

### 설명

`terraform fmt`는 Terraform 코드의 들여쓰기와 정렬을 자동으로 맞춰준다.

실행하지 않아도 코드는 동작할 수 있지만, 협업과 가독성을 위해 습관적으로 실행하는 것이 좋다.

---

## 9.5 초기화 실행

```
terraform init
```

### 기대 결과

출력 메시지에 다음과 같은 흐름이 보이면 정상이다.

* Terraform has been successfully initialized

* Installing hashicorp/aws ...

* Terraform has created a lock file ...

즉,

* AWS Provider가 다운로드되었고

* 현재 디렉터리가 Terraform 실행 준비 상태가 되었음

을 의미한다.

---

## 9.6 생성 파일 확인

* `main.tf`

* `.terraform/`

* `.terraform.lock.hcl`

# 10. init과 Provider의 관계 이해하기

## 10.1

```
provider "aws" {
  region = "ap-northeast-2"
}
```

실제로 해당 Provider 플러그인을 가져와야 하며, 그 작업을 `terraform init`이 수행한다.

즉,

* 코드 작성 → 설정 선언

* `terraform init` → 필요한 Provider 실제 다운로드

---

## 10.2 왜 init을 먼저 해야 하는가

Terraform이 `plan`, `apply`, `validate` 같은 작업을 하려면

해당 Provider가 제공하는 스키마와 동작 방식을 알아야 한다.

예를 들어 AWS의 EC2 리소스를 쓰려면 Terraform은 AWS Provider를 통해 다음을 알아야 한다.

* 이 리소스 이름이 유효한지

* 어떤 인자들이 필요한지

* 어떤 API를 호출해야 하는지

따라서 Provider가 준비되지 않으면 정상적인 해석이 어렵다.

---

# 11. 자주 발생하는 오류와 원인

## 11.1 `terraform init` 전에 다른 명령 실행

예를 들어 `terraform plan`을 먼저 실행하면 초기화가 필요하다는 메시지가 나올 수 있다.

원인:

* Provider가 아직 다운로드되지 않았음

* 작업 디렉터리가 아직 초기화되지 않았음

해결:

```
terraform init
```

---

## 11.2 잘못된 Provider 소스 지정

예를 들어 다음처럼 오타가 있으면 다운로드에 실패할 수 있다.

```
source = "hashcorp/aws"
```

`hashicorp`를 `hashcorp`로 잘못 적은 경우다.

해결:

* Provider source 경로 확인

* 공식 문서 기준으로 수정

---

## 11.3 지원되지 않는 Terraform 버전

```
required_version = ">= 1.8.0"
```

이렇게 적었는데 실제 설치 버전이 1.6.0이면 실행되지 않는다.

해결:

* Terraform CLI 버전 업그레이드

* 또는 코드의 버전 조건 재검토

---

## 11.4 AWS 인증 관련 오류

Provider 설정은 맞아도 인증 정보가 없으면 AWS API 호출 시 실패한다.

예시 원인:

* `aws configure` 미실행

* 잘못된 프로필 사용

* 액세스 키 오류

* 권한 부족

해결 흐름:

```
aws sts get-caller-identity
```

이 명령이 정상 응답하는지 먼저 확인하면 좋다.

이 명령이 실패하면 Terraform도 AWS 인증 단계에서 실패할 가능성이 높다.

---

# 12. 실습 확장: profile 지정해보기

AWS CLI에 여러 프로필이 있는 경우 `provider` 블록에서 특정 프로필을 명시할 수 있다.

```
provider "aws" {
  region  = "ap-northeast-2"
  profile = "default"
}
```

또는 예를 들어 학습용 프로필이 `terraform-lab`이라면 다음처럼 설정할 수 있다.

```
provider "aws" {
  region  = "ap-northeast-2"
  profile = "terraform-lab"
}
```

이 경우 Terraform은 해당 프로필의 인증 정보를 사용해 AWS API를 호출한다.

---

# 13. 장 마무리

이 장에서는 Terraform 코드의 기반이 되는 두 축을 다뤘다.

* `terraform` 블록은 Terraform 실행 규칙을 정의하는 영역

* `provider` 블록은 외부 플랫폼과 연결하는 설정 영역

특히 다음 구분이 중요하다.

* `required_providers`는 **무슨 Provider가 필요한지 선언**

* `provider` 블록은 **그 Provider를 어떻게 사용할지 설정**

또한 `terraform init`은 단순한 시작 명령이 아니라,

**Provider 다운로드와 작업 디렉터리 초기화**를 수행하는 필수 단계이다.