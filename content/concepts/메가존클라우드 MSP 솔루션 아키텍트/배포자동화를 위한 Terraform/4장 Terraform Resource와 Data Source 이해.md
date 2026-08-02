---
title: "4장 Terraform Resource와 Data Source 이해"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "배포자동화를 위한 Terraform"]
is_public: true
draft: false
---

# 4장. Terraform Resource와 Data Source 이해

## 장 목표

이 장에서는 Terraform에서 실제 인프라를 다룰 때 가장 자주 만나게 되는 두 가지 개념인 **Resource**와 **Data Source**를 학습한다.

이 장을 학습한 뒤에는 다음이 가능해진다.

* `resource`의 의미와 구조를 설명할 수 있음

* `data source`의 의미와 구조를 설명할 수 있음

* 생성과 조회의 차이를 구분할 수 있음

* Resource와 state의 관계를 설명할 수 있음

* Data Source와 state의 관계를 설명할 수 있음

* `aws_ami`, `aws_vpc`, `aws_subnets`를 이용한 조회 예제를 이해할 수 있음

* 조회 결과를 다른 리소스에서 참조할 수 있음

* `most_recent = true`의 의미를 설명할 수 있음

* 자동 조회 / 실행 시 선택 / 직접 지정 방식의 차이를 설명할 수 있음

* 실무에서 Resource와 Data Source를 어떻게 조합하는지 이해할 수 있음

---

# 1. 왜 Resource와 Data Source를 구분해야 하는가

실무에서는 다음과 같은 상황이 매우 자주 나온다.

* 이미 존재하는 VPC 안에 Subnet과 EC2를 만들어야 함

* 기존에 만들어둔 보안 기준용 AMI를 찾아서 EC2를 띄워야 함

* 네트워크팀이 미리 만든 VPC를 조회해서 애플리케이션 리소스를 배치해야 함

* 공통 인프라는 기존 것을 쓰고, 애플리케이션 리소스만 새로 만들어야 함

즉, Terraform은 단순히 **새로 생성만 하는 도구**가 아니라

**이미 존재하는 값을 조회해서 재사용하는 도구**이기도 하다.

이때 역할이 나뉜다.

* **Resource** → 새로 생성하거나 관리 대상으로 선언하는 것

* **Data Source** → 이미 존재하는 것을 조회해서 가져오는 것

이 차이를 정확히 이해해야 Terraform 코드를 제대로 읽고 설계할 수 있다.

---

# 2. Resource의 의미와 구조

## 2.1 Resource란 무엇인가

`resource`는 Terraform이 **생성, 변경, 삭제를 관리하는 대상**을 의미한다.

쉽게 말하면 다음과 같다.

* VPC를 새로 만든다

* EC2 인스턴스를 새로 만든다

* Security Group을 새로 만든다

* Subnet을 새로 만든다

즉, Terraform이 직접 **desired state**를 선언하고, 그 상태에 맞게 실제 인프라를 맞춰가는 대상이 Resource다.

---

## 2.2 기본 구조

`resource` 블록의 기본 구조는 다음과 같다.

```
resource "리소스타입" "이름" {
  인자 = 값
}
```

예를 들어 AWS에서 VPC를 생성하는 코드는 다음과 같다.

```
resource "aws_vpc" "main" {
  cidr_block = "10.10.0.0/16"
}
```

이 코드를 구성 요소별로 나누면 다음과 같다.

* `resource` → 블록 종류

* `"aws_vpc"` → 리소스 타입

* `"main"` → 로컬 이름

* `cidr_block = "10.10.0.0/16"` → 설정 인자

---

## 2.3 리소스 타입과 이름의 의미

### 리소스 타입

`aws_vpc`는 AWS Provider가 제공하는 리소스 타입이다.

즉, AWS의 VPC를 만들겠다는 의미다.

다른 예시는 다음과 같다.

* `aws_subnet`

* `aws_instance`

* `aws_security_group`

* `aws_internet_gateway`

---

### 로컬 이름

`main`은 Terraform 코드 내부에서 이 리소스를 식별하기 위한 이름이다.

AWS 콘솔의 리소스 이름과는 다르다.

즉, 다음 코드에서

```
resource "aws_vpc" "main" {
  cidr_block = "10.10.0.0/16"
}
```

`main`은 Terraform 내부 참조용 이름이다.

이 이름을 이용해서 다른 곳에서 다음처럼 참조할 수 있다.

```
aws_vpc.main.id
```

즉, `aws_vpc.main.id`는

“Terraform 코드 안에서 `aws_vpc` 타입의 `main`이라는 리소스의 id 값”이라는 뜻이다.

---

# 3. Data Source의 의미와 구조

## 3.1 Data Source란 무엇인가

`data source`는 Terraform이 **이미 존재하는 외부 정보를 조회해서 가져오는 대상**이다.

쉽게 말하면 다음과 같다.

* 이미 존재하는 VPC를 찾는다

* 특정 조건에 맞는 AMI를 찾는다

* 기존 Subnet 목록을 가져온다

* 현재 계정 정보나 리전 정보를 조회한다

즉, Terraform이 직접 생성하지 않고 **읽기(read)** 용도로 사용하는 정보가 Data Source다.

---

## 3.2 기본 구조

`data` 블록의 기본 구조는 다음과 같다.

```
data "데이터타입" "이름" {
  조건 = 값
}
```

예를 들어 특정 VPC를 조회하는 코드는 다음과 같다.

```
data "aws_vpc" "selected" {
  id = "vpc-1234567890abcdef0"
}
```

구성 요소는 다음과 같다.

* `data` → 블록 종류

* `"aws_vpc"` → 데이터 타입

* `"selected"` → 로컬 이름

* `id = "vpc-1234567890abcdef0"` → 조회 조건

---

## 3.3 Resource와 Data Source는 문법도 닮아 있다

Terraform 초보자가 헷갈리는 이유 중 하나는 두 문법이 매우 비슷하기 때문이다.

예를 들어:

### Resource

```
resource "aws_vpc" "main" {
  cidr_block = "10.10.0.0/16"
}
```

### Data Source

```
data "aws_vpc" "selected" {
  id = "vpc-1234567890abcdef0"
}
```

둘 다 VPC와 관련되어 있고, 블록 구조도 비슷하다.

하지만 의미는 완전히 다르다.

* `resource "aws_vpc"` → VPC를 **생성/관리**

* `data "aws_vpc"` → 기존 VPC를 **조회**

---

# 4. 생성과 조회의 차이

## 4.1 Resource는 만든다

Resource는 Terraform이 원하는 상태를 선언하고, 실제 클라우드에 그 상태를 맞추는 역할을 한다.

예를 들어

```
resource "aws_instance" "web" {
  ami           = "ami-xxxxxxxx"
  instance_type = "t3.micro"
}
```

이 코드는 EC2 인스턴스를 새로 만들겠다는 뜻이다.

Terraform은 이 코드를 보고 다음과 같은 작업을 한다.

* 아직 없으면 생성함

* 설정이 바뀌면 변경함

* 코드에서 제거되면 삭제 대상으로 판단할 수 있음

즉, 수명주기를 관리한다.

---

## 4.2 Data Source는 찾는다

반면 Data Source는 조회만 한다.

```
data "aws_ami" "amazon_linux" {
  most_recent = true
}
```

이 코드는 “조건에 맞는 AMI를 조회한다”는 뜻이지, AMI를 새로 만드는 뜻이 아니다.

Terraform은 Data Source를 통해 값을 읽어오고, 그 값을 다른 리소스에 전달하는 데 사용한다.

즉, Data Source는 **생성 도구가 아니라 입력값 공급 도구**에 가깝다.

---

# 5. State와의 관계

## 5.1 Resource와 state의 관계

Terraform에서 `state`는 매우 중요하다.

Terraform은 자신이 관리하는 리소스의 현재 상태를 state 파일에 기록한다.

예를 들어 다음 리소스를 만들었다고 해보자.

```
resource "aws_vpc" "main" {
  cidr_block = "10.10.0.0/16"
}
```

`terraform apply`를 수행해서 실제 VPC가 생성되면, Terraform은 그 결과를 state에 기록한다.

예를 들어 state에는 다음과 같은 정보가 연결된다.

* 이 리소스의 실제 AWS 리소스 ID

* 현재 속성값

* Terraform 코드상의 주소

* 의존 관계

즉, Resource는 Terraform이 **지속적으로 추적하는 관리 대상**이다.

---

## 5.2 Data Source와 state의 관계

Data Source도 실행 시 조회 결과가 state에 반영될 수는 있다.

하지만 Resource처럼 “내가 관리하는 대상”으로 저장되는 것은 아니다.

이 차이가 중요하다.

* Resource → Terraform이 생성/변경/삭제까지 관리하는 대상

* Data Source → 조회 결과를 계산 과정에서 사용하기 위한 대상

즉, Data Source는 state에 값이 반영되더라도, 그것이 곧 Terraform 관리 리소스라는 뜻은 아님.

간단히 말하면

* Resource는 **관리 대상**

* Data Source는 **참조 정보**

라고 보면 된다.

---

Terraform은 그 VPC를 조회해서 값을 읽어온 것뿐이다.

생성, 변경, 삭제를 관리하겠다고 선언한 것이 아니다.

즉, `data "aws_vpc"`는 기존 VPC를 **참조**하는 것이고,

`resource "aws_vpc"`는 Terraform이 그 VPC를 **관리**하는 것이다.

---

# 6. Resource 예제: VPC 생성

먼저 생성부터 보자.

```
resource "aws_vpc" "main" {
  cidr_block = "10.10.0.0/16"

  tags = {
    Name = "terraform-main-vpc"
  }
}
```

이 코드는 다음 의미를 가진다.

* AWS에 VPC를 새로 만든다

* CIDR은 `10.10.0.0/16`

* 태그 Name은 `terraform-main-vpc`

생성 후에는 다른 리소스가 이 VPC를 참조할 수 있다.

예를 들면

```
aws_vpc.main.id
```

이 값은 생성된 VPC의 실제 ID를 의미한다.

---

# 7. Data Source 예제: aws\_ami

## 7.1 왜 AMI를 Data Source로 자주 조회하는가

EC2를 만들 때 반드시 필요한 것 중 하나가 AMI다.

그런데 AMI ID는 고정값처럼 보이지만 실제로는 자주 달라질 수 있다.

예를 들어 Amazon Linux 2, Amazon Linux 2023, Ubuntu 이미지 등은

리전별로 ID가 다를 수 있고, 업데이트 버전이 계속 새로 나올 수 있다.

그래서 실무에서는 하드코딩보다 **조건으로 조회**하는 방식을 많이 쓴다.

---

## 7.2 기본 예제

```
data "aws_ami" "amazon_linux" {
  most_recent = true

  owners = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
}
```

이 코드는 대략 다음 의미다.

* Amazon이 제공한 AMI 중에서

* 이름 패턴이 `al2023-ami-2023.*-x86_64`에 맞는 것들을 찾고

* 그중 가장 최신 이미지를 선택한다

---

## 7.3 owners의 의미

```
owners = ["amazon"]
```

이 설정은 AMI 소유자를 제한한다.

즉, Amazon이 제공한 이미지 중에서만 찾겠다는 뜻이다.

왜 필요한가?

AMI는 같은 이름 패턴을 가진 이미지가 다른 계정에도 있을 수 있기 때문이다.

소유자를 제한하지 않으면 의도치 않은 이미지를 잡을 위험이 있다.

---

## 7.4 filter 블록의 의미

```
filter {
  name   = "name"
  values = ["al2023-ami-2023.*-x86_64"]
}
```

이 블록은 조회 조건을 걸어준다.

* `name = "name"` → AMI의 이름 속성을 기준으로 검색

* `values = [...]` → 해당 패턴과 일치하는 값을 찾음

즉, AMI 목록 전체를 가져오는 것이 아니라 조건을 걸어 원하는 후보군만 추린다.

---

## 7.5 most\_recent = true

```
most_recent = true
```

이 옵션은 여러 결과가 나왔을 때 **가장 최신 것 하나를 선택**하겠다는 뜻이다.

예를 들어 AMI가 여러 개 존재할 수 있다.

* al2023-ami-2023.0.x

* al2023-ami-2023.1.x

* al2023-ami-2023.2.x

이 중 최신 이미지를 자동으로 선택하려면 `most_recent = true`를 사용한다.

이 옵션은 실습과 운영 모두에서 매우 자주 사용된다.

---

# 8. Data Source 예제: aws\_vpc

## 8.1 특정 VPC를 ID로 조회

이미 존재하는 VPC를 조회하는 가장 단순한 예시는 다음과 같다.

```
data "aws_vpc" "selected" {
  id = "vpc-1234567890abcdef0"
}
```

의미는 매우 단순하다.

* ID가 `vpc-1234567890abcdef0`인 기존 VPC를 찾아라

그리고 나서 다음처럼 참조할 수 있다.

```
data.aws_vpc.selected.id
```

또는 CIDR을 가져올 수도 있다.

```
data.aws_vpc.selected.cidr_block
```

---

## 8.2 태그 기반으로 조회하는 방식

실무에서는 VPC ID를 직접 입력하지 않고 태그를 조건으로 찾는 경우도 많다.

예시:

```
data "aws_vpc" "selected" {
  filter {
    name   = "tag:Name"
    values = ["shared-vpc"]
  }
}
```

이 코드는 Name 태그가 `shared-vpc`인 VPC를 조회한다.

이 방식은 ID를 직접 쓰지 않아도 되기 때문에 코드 이식성이 좋아질 수 있다.

다만 조건에 맞는 VPC가 여러 개일 경우 의도와 다를 수 있으므로 태그 체계가 명확해야 한다.

---

# 9. Data Source 예제: aws\_subnets

## 9.1 Subnet 목록 조회가 왜 필요한가

실무에서는 특정 VPC 안의 Subnet 목록을 가져와서 다음 작업에 연결하는 경우가 많다.

예를 들면

* ALB를 여러 Subnet에 배치

* EC2를 특정 Subnet 집합 중 하나에 배치

* EKS, RDS, NAT Gateway 구성 시 Subnet 목록 활용

* 기존 네트워크 안에서만 애플리케이션 구성

이럴 때 `aws_subnets`를 사용한다.

---

## 9.2 기본 예제

```
data "aws_subnets" "selected" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.selected.id]
  }
}
```

의미는 다음과 같다.

* 앞에서 조회한 VPC의 ID를 기준으로

* 그 VPC에 속한 Subnet들을 모두 조회한다

즉, VPC를 먼저 찾고, 그 VPC에 연결된 Subnet 목록을 가져오는 흐름이다.

---

## 9.3 조회 결과 참조

`aws_subnets`는 여러 개의 Subnet ID를 리스트 형태로 반환할 수 있다.

예를 들어 다음처럼 사용할 수 있다.

```
data.aws_subnets.selected.ids
```

이 값은 Subnet ID들의 목록이다.

예를 들면 내부적으로 다음 같은 형태라고 이해하면 된다.

```
[
  "subnet-aaaa1111",
  "subnet-bbbb2222",
  "subnet-cccc3333"
]
```

이 값을 다른 리소스에 그대로 전달할 수 있다.

---

# 10. 조회 결과 참조 방식

Terraform에서는 Resource와 Data Source 모두 속성 참조가 가능하다.

다만 주소 형식이 다르다.

---

## 10.1 Resource 참조 방식

형식:

```
리소스타입.이름.속성
```

예시:

```
aws_vpc.main.id
```

의미:

* `aws_vpc` 타입의

* `main`이라는 이름을 가진 리소스의

* `id` 속성

---

## 10.2 Data Source 참조 방식

형식:

```
data.데이터타입.이름.속성
```

예시:

```
data.aws_vpc.selected.id
```

의미:

* `data` 블록 중에서

* `aws_vpc` 타입의

* `selected`라는 이름을 가진 데이터의

* `id` 속성

---

## 10.3 왜 data 접두사가 붙는가

Resource와 Data Source는 타입 이름이 겹칠 수 있다.

예를 들어 둘 다 `aws_vpc`를 사용할 수 있다.

그래서 Terraform은 Data Source일 때 앞에 `data.`를 붙여 구분한다.

예를 들어

* `aws_vpc.main.id` → 내가 관리하는 VPC

* `data.aws_vpc.selected.id` → 조회한 기존 VPC

이렇게 구분된다.

# 11. Resource와 Data Source를 함께 쓰는 예제

이제 두 개념을 연결해보자.

목표는 다음과 같다.

* 기존에 있는 최신 Amazon Linux AMI를 조회한다

* 조회한 AMI를 사용해서 EC2를 새로 생성한다

```
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
  instance_type = "t3.micro"

  tags = {
    Name = "tf-web-instance"
  }
}
```

이 코드는 아주 중요한 흐름을 보여준다.

1. `data.aws_ami.amazon_linux` 가 먼저 실행되어 AMI를 찾음

2. 그 결과의 `id` 값을

3. `aws_instance.web`의 `ami` 인자에 전달함

4. Terraform은 조회된 최신 AMI를 사용해 EC2를 생성함

즉, Data Source는 Resource의 입력값을 공급하는 역할을 한다.

---

# 12. 자동 조회 / 실행 시 선택 / 직접 지정

AMI나 VPC 같은 값을 Terraform 코드에 넣는 방식은 크게 세 가지로 볼 수 있다.

---

## 12.1 직접 지정

예시:

```
resource "aws_instance" "web" {
  ami           = "ami-0abc123456789def0"
  instance_type = "t3.micro"
}
```

이 방식은 가장 단순하다.

하지만 단점도 분명하다.

* 리전이 바뀌면 ID가 달라질 수 있음

* 이미지 업데이트가 반영되지 않음

* 코드 이식성이 떨어질 수 있음

실습 초기에는 이해하기 쉽지만, 운영 코드에서는 주의가 필요하다.

---

## 12.2 Data Source로 자동 조회

예시:

```
ami = data.aws_ami.amazon_linux.id
```

이 방식은 Terraform 실행 시 조건에 맞는 값을 자동으로 찾는다.

장점:

* 최신 이미지 자동 반영 가능

* 리전별 차이를 코드가 흡수할 수 있음

* 하드코딩을 줄일 수 있음

단점:

* 필터 조건이 불명확하면 예상과 다른 결과가 나올 수 있음

* 조회 결과가 변동되면 재현성이 낮아질 수 있음

---

## 12.3 변수로 직접 선택

예시:

```
variable "ami_id" {
  type = string
}

resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = "t3.micro"
}
```

이 방식은 AMI 값을 외부에서 입력받는다.

장점:

* 환경별로 값 제어가 쉬움

* 운영에서 승인된 값만 주입 가능

* 재현성이 높음

단점:

* 사용자가 값을 관리해야 함

* 자동화 수준은 다소 낮아질 수 있음

---

## 12.4 세 가지 방식을 비교하면

### 직접 지정

* 가장 단순함

* 고정값

* 실습 초반에 이해하기 쉬움

### 자동 조회

* 유연함

* 최신값 활용 가능

* 실무에서 자주 사용됨

### 변수 입력

* 통제력이 높음

* 운영에서 많이 사용됨

* 환경별 관리에 유리함

실무에서는 세 방식을 상황에 따라 섞어서 쓴다.

---

# 13. 실무에서의 활용 방식

## 13.1 공통 인프라는 조회, 애플리케이션은 생성

실무에서 매우 흔한 패턴은 다음과 같다.

* 네트워크팀이 VPC, Subnet, 라우팅 등 공통 인프라를 미리 생성

* 애플리케이션 팀은 그 인프라를 Data Source로 조회

* 그 안에 EC2, ALB, Auto Scaling, EKS 등을 Resource로 생성

즉,

* 공통 기반 → Data Source

* 내가 배포하는 대상 → Resource

이런 구조가 많다.

---

## 13.2 승인된 골든 이미지 조회

운영 환경에서는 아무 AMI나 쓰지 않고, 보안팀이나 플랫폼팀이 검증한 이미지 집합만 사용하기도 한다.

이 경우 다음처럼 한다.

* 특정 소유자만 허용

* 특정 태그나 이름 패턴으로 필터링

* `most_recent = true`로 최신 승인 이미지 선택

즉, Data Source는 단순 조회를 넘어 **운영 정책을 코드화하는 수단**이 되기도 한다.

---

## 13.3 환경 분리와 결합

예를 들어 dev / stage / prod 환경이 있다고 해보자.

* VPC는 환경별로 다름

* Subnet도 환경별로 다름

* 하지만 EC2 생성 방식은 동일함

이때 VPC와 Subnet은 환경별 Data Source 또는 변수로 바꾸고,

리소스 구조는 공통으로 유지할 수 있다.

이런 설계가 가능해지는 이유가 바로 Resource와 Data Source의 분리 덕분이다.

---

# 14. 실습 1: 최신 AMI 조회하기

## 14.1 실습 목표

* `aws_ami` Data Source를 사용해 최신 Amazon Linux AMI 조회

* 조회 결과를 output으로 확인

---

## 14.2 예제 코드

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

data "aws_ami" "amazon_linux" {
  most_recent = true

  owners = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
}

output "selected_ami_id" {
  value = data.aws_ami.amazon_linux.id
}

output "selected_ami_name" {
  value = data.aws_ami.amazon_linux.name
}
```

---

## 14.3 실행 순서

```
terraform init
terraform plan
```

또는 실제 조회 결과를 더 명확히 확인하려면:

```
terraform apply -auto-approve
```

---

## 14.4 확인 포인트

* AMI가 생성되는 것은 아님

* Terraform이 조회한 AMI ID와 이름이 출력됨

* Data Source는 값을 읽어오는 용도라는 점을 확인할 수 있음

---

# 15. 실습 2: 조회한 AMI로 EC2 생성하기

## 15.1 실습 목표

* `aws_ami` Data Source로 AMI 조회

* 해당 결과를 `aws_instance` Resource에 연결

* 조회와 생성이 연결되는 흐름 이해

---

## 15.2 예제 코드

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
  instance_type = "t3.micro"

  tags = {
    Name = "tf-data-source-web"
  }
}

output "instance_id" {
  value = aws_instance.web.id
}

output "ami_id_used" {
  value = data.aws_ami.amazon_linux.id
}
```

---

## 15.3 실행 명령

```
terraform init
terraform plan
terraform apply-auto-approve
```

---

## 15.4 명령어 설명

### `terraform init`

현재 디렉터리를 초기화하고 AWS Provider를 준비한다.

### `terraform plan`

Terraform이 실제로 어떤 작업을 하려는지 미리 계산한다.

이 단계에서 Data Source도 함께 평가되어 어떤 AMI가 선택될지 확인 흐름에 반영된다.

### `terraform apply`

실제 AWS에 EC2를 생성한다.

이때 `ami` 값은 하드코딩된 값이 아니라 Data Source 조회 결과로 채워진다.

---

## 15.5 정리 명령

실습 후에는 반드시 리소스를 정리한다.

```
terraform destroy-auto-approve
```

이 명령은 Terraform이 관리하는 Resource를 삭제한다.

중요한 점은 다음이다.

* `aws_instance.web`는 삭제 대상임

* `data.aws_ami.amazon_linux`는 삭제 대상이 아님

왜냐하면 Data Source는 원래 생성한 것이 아니라 조회한 정보이기 때문이다.

---

# 16. 실습 3: 기존 VPC와 Subnet 조회하기

## 16.1 실습 목표

* 기존 VPC를 조회

* 해당 VPC의 Subnet 목록을 조회

* 조회 결과를 output으로 확인

---

## 16.2 예제 코드

아래 예제는 특정 Name 태그를 가진 VPC를 찾는 방식이다.

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

data "aws_vpc" "selected" {
  filter {
    name   = "tag:Name"
    values = ["shared-vpc"]
  }
}

data "aws_subnets" "selected" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.selected.id]
  }
}

output "vpc_id" {
  value = data.aws_vpc.selected.id
}

output "subnet_ids" {
  value = data.aws_subnets.selected.ids
}
```

---

## 16.3 실행 전 주의

이 실습은 실제로 `Name=shared-vpc` 태그를 가진 VPC가 있어야 한다.

없다면 조회 실패가 발생할 수 있다.

그래서 교육 환경에서는 다음 둘 중 하나로 진행하면 된다.

* 미리 생성된 VPC 이름을 알려주고 조회하게 하기

* VPC ID를 직접 입력하는 형태로 바꾸기

예를 들어 ID 직접 지정 방식은 다음과 같다.

```
data "aws_vpc" "selected" {
  id = "vpc-1234567890abcdef0"
}
```

---

# 18. Resource와 Data Source를 보는 관점 정리

Terraform 코드를 볼 때 다음 질문을 던지면 구조가 빠르게 읽힌다.

## 18.1 이 블록은 새로 만드는가, 기존 것을 찾는가

* 새로 만든다 → `resource`

* 기존 것을 찾는다 → `data`

---

## 18.2 이 대상은 Terraform이 수명주기를 관리하는가

* 관리한다 → `resource`

* 관리하지 않고 읽기만 한다 → `data`

---

## 18.3 다른 블록의 입력값 역할을 하는가

* Data Source는 자주 입력값 공급 역할을 함

* Resource도 다른 Resource의 입력값이 될 수 있음

즉, Terraform 코드는 하나의 블록만 보는 것이 아니라

**생성 흐름과 참조 흐름**을 같이 읽어야 한다.

---

# 19. 장 마무리

이 장에서는 Terraform의 핵심 개념인 Resource와 Data Source를 구분했다.

핵심은 다음이다.

* `resource`는 Terraform이 생성/변경/삭제를 관리하는 대상이다

* `data`는 이미 존재하는 값을 조회해서 가져오는 대상이다

* Resource는 관리 대상이므로 state와 강하게 연결된다

* Data Source는 조회 결과를 참조용으로 사용한다

* 실무에서는 둘 중 하나만 쓰는 경우보다 둘을 함께 쓰는 경우가 훨씬 많다

특히 다음 예시는 반드시 익숙해져야 한다.

* `data "aws_ami"`로 최신 이미지 조회

* `data "aws_vpc"`로 기존 네트워크 조회

* `data "aws_subnets"`로 Subnet 목록 조회

* 조회 결과를 `resource`의 인자로 참조

즉, Terraform 실전 코드는 보통 이렇게 읽으면 된다.

> 필요한 기존 정보를 먼저 조회하고,
>
> 그 값을 이용해서 새 리소스를 생성한다.