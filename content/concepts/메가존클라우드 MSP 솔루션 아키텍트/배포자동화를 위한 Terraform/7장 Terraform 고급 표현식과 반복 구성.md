---
title: "7장 Terraform 고급 표현식과 반복 구성"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "배포자동화를 위한 Terraform"]
is_public: true
draft: false
---

# 7장. Terraform 고급 표현식과 반복 구성

## 장 목표

이 장에서는 Terraform 코드에서 반복과 조건을 다루는 핵심 기능을 학습한다.

앞 장까지는 리소스를 하나씩 직접 선언하는 방식으로 인프라를 구성했다. 이 방식은 개념 학습에는 좋지만, 실제 환경에서는 리소스 수가 늘어나면 코드가 빠르게 길어지고 중복도 많아진다.

예를 들어 다음과 같은 상황을 생각해볼 수 있다.

* 같은 형식의 EC2를 3대 생성해야 함

* 여러 개의 Subnet을 반복적으로 생성해야 함

* 환경에 따라 특정 리소스는 만들고, 특정 리소스는 만들지 않아야 함

* 보안 그룹 규칙을 여러 개 반복 생성해야 함

* 여러 속성을 가진 복잡한 입력값을 기반으로 리소스를 구성해야 함

이런 상황에서 Terraform은 다음 기능을 제공한다.

* `count`

* `for_each`

* 조건식

* 리스트, 맵, 객체 같은 컬렉션 타입

* `dynamic` 블록

이 장을 학습한 뒤에는 다음이 가능해야 한다.

* `count`의 의미와 사용 방식을 설명할 수 있음

* `for_each`의 의미와 사용 방식을 설명할 수 있음

* `count`와 `for_each`의 차이를 설명할 수 있음

* 조건식을 사용해 값이나 리소스 생성을 제어할 수 있음

* 리스트, 맵, 객체의 기본 구조를 이해할 수 있음

* `dynamic` 블록의 역할을 설명할 수 있음

* 반복 구성을 설계할 때 어떤 방식을 선택할지 판단할 수 있음

---

## 1. 왜 반복 구성이 필요한가

Terraform 초반에는 보통 리소스를 하나씩 직접 작성한다.

예를 들어 다음처럼 EC2를 하나 생성할 수 있다.

```
resource "aws_instance" "web" {
  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"
}
```

이 방식은 한두 개 리소스를 만들 때는 문제없다.

하지만 같은 리소스를 여러 개 만들기 시작하면 중복이 급격히 늘어난다.

예를 들어 EC2를 세 대 만들기 위해 다음처럼 작성할 수도 있다.

```
resource "aws_instance" "web1" {
  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"
}

resource "aws_instance" "web2" {
  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"
}

resource "aws_instance" "web3" {
  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"
}
```

동작은 가능하지만 코드 품질은 좋지 않다.

* 중복이 많음

* 수정 시 여러 곳을 함께 고쳐야 함

* 개수가 바뀌면 블록을 직접 늘리거나 줄여야 함

* 이름 관리가 불편함

Terraform의 반복 구성 기능은 이런 문제를 해결하기 위해 존재한다.

즉, 반복 구성은 단순히 코드를 짧게 만드는 기능이 아니라 **중복을 줄이고, 인프라를 데이터 중심으로 정의하게 해주는 기능**이다.

---

## 2. count

## 2.1 count란 무엇인가

`count`는 같은 리소스를 **정수 개수만큼 반복 생성**하는 기능이다.

예를 들어 다음처럼 사용할 수 있다.

```
resource "aws_instance" "web" {
  count         = 3
  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"
}
```

이 코드는 `aws_instance.web`를 3개 생성한다.

즉, `count = 3` 이라는 것은

“이 리소스 블록을 3번 반복해서 만들겠다”는 뜻이다.

---

## 2.2 count 인덱스

`count`를 사용하면 Terraform은 각 리소스를 인덱스로 구분한다.

예를 들어 위 코드는 내부적으로 다음처럼 구분된다.

* `aws_instance.web[0]`

* `aws_instance.web[1]`

* `aws_instance.web[2]`

이때 현재 반복 순서를 나타내는 특수 값으로 `count.index`를 사용할 수 있다.

예시:

```
resource "aws_instance" "web" {
  count         = 3
  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"

  tags = {
    Name = "web-${count.index}"
  }
}
```

이 코드에서는 Name 태그가 다음처럼 붙는다.

* `web-0`

* `web-1`

* `web-2`

---

## 2.3 count의 장점

`count`는 다음 상황에 적합하다.

* 동일한 리소스를 단순 개수만큼 만들 때

* 각 리소스가 거의 같은 설정을 사용할 때

* 숫자 기반 인덱스로 충분할 때

예를 들어 다음과 같은 경우다.

* 동일한 테스트용 EC2 2대 생성

* 동일한 규칙의 EBS 볼륨 여러 개 생성

* 학습용으로 간단히 반복 생성

즉, 구조가 단순하고 개수 중심일 때 `count`가 편하다.

---

## 2.4 count의 한계

`count`는 단순하지만, 다음과 같은 한계가 있다.

* 리소스를 숫자 인덱스로 식별함

* 중간 항목이 사라지거나 순서가 바뀌면 인덱스가 밀릴 수 있음

* 각 리소스가 서로 다른 속성을 가져야 할 때 관리가 불편함

예를 들어 리스트의 두 번째 항목을 삭제하면

그 뒤 인덱스가 모두 당겨질 수 있다.

이 경우 Terraform은 기존 리소스를 바꾸거나 재생성해야 하는 상황으로 판단할 수 있다.

즉, `count`는 **순서 기반 반복**이라는 점을 항상 염두에 둬야 한다.

---

## 3. for\_each

## 3.1 for\_each란 무엇인가

`for_each`는 컬렉션의 각 항목을 기준으로 리소스를 반복 생성하는 기능이다.

`count`가 숫자 개수 중심이라면, `for_each`는 **항목 자체를 기준으로 반복**한다.

예를 들어 다음처럼 사용할 수 있다.

```
resource "aws_instance" "web" {
  for_each = toset(["web-a", "web-b", "web-c"])

  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"

  tags = {
    Name = each.value
  }
}
```

이 코드는 문자열 집합의 각 값을 기준으로 EC2를 생성한다.

즉, 리소스는 다음처럼 식별된다.

* `aws_instance.web["web-a"]`

* `aws_instance.web["web-b"]`

* `aws_instance.web["web-c"]`

이 점이 `count`와 가장 큰 차이다.

---

## 3.2 each.key와 each.value

`for_each`를 사용하면 반복 대상에 접근하기 위해 `each.key`, `each.value`를 사용한다.

### 집합(set)을 사용할 때

집합은 key와 value가 사실상 같은 개념으로 동작한다.

예:

```
for_each = toset(["web-a", "web-b"])
```

이 경우 `each.key`와 `each.value`는 모두 `"web-a"`, `"web-b"` 같은 값이 된다.

---

### 맵(map)을 사용할 때

맵을 사용하면 key와 value가 명확히 구분된다.

예:

```
for_each = {
  web-a = "t3.micro"
  web-b = "t3.small"
}
```

이 경우

* `each.key` → `web-a`, `web-b`

* `each.value` → `t3.micro`, `t3.small`

이 된다.

예시 코드:

```
resource "aws_instance" "web" {
  for_each = {
    web-a = "t3.micro"
    web-b = "t3.small"
  }

  ami           = data.aws_ami.amazon_linux.id
  instance_type = each.value

  tags = {
    Name = each.key
  }
}
```

---

## 3.3 for\_each의 장점

`for_each`는 다음 상황에서 강력하다.

* 리소스를 이름 기준으로 식별하고 싶을 때

* 각 항목이 서로 다른 속성을 가져야 할 때

* 순서보다 항목의 식별자가 중요할 때

* 리스트 변경으로 인한 인덱스 밀림을 피하고 싶을 때

즉, 실무에서는 `count`보다 `for_each`가 더 자주 선호되는 경우가 많다.

특히 리소스 식별 안정성 측면에서 강점이 있다.

---

## 3.4 count와 for\_each 차이

두 기능은 비슷해 보이지만 기준이 다르다.

### count

* 기준: 개수

* 식별 방식: 숫자 인덱스

* 참조 예: `aws_instance.web[0]`

### for\_each

* 기준: 항목

* 식별 방식: key 또는 값

* 참조 예: `aws_instance.web["web-a"]`

즉, 다음처럼 이해하면 좋다.

* `count` → “3개 만들어라”

* `for_each` → “이 목록의 각 항목별로 만들어라”

---

## 4. 조건식

## 4.1 조건식이란 무엇인가

Terraform에서도 조건에 따라 값을 다르게 줄 수 있다.

가장 기본적인 형태는 삼항 연산자 형태다.

```
조건 ? 참일때값 : 거짓일때값
```

예시:

```
instance_type = var.environment == "prod" ? "t3.small" : "t3.micro"
```

이 코드는 환경이 `prod`이면 `t3.small`, 아니면 `t3.micro`를 사용한다.

---

## 4.2 값 제어에 사용하는 경우

조건식은 리소스 전체를 제어하기 전에,

먼저 속성값을 유연하게 정하는 데 많이 쓴다.

예를 들어 다음과 같이 쓸 수 있다.

```
resource "aws_instance" "web" {
  ami           = data.aws_ami.amazon_linux.id
  instance_type = var.is_production ? "t3.small" : "t3.micro"
}
```

이 방식은 같은 리소스 구조를 유지하면서도

환경에 따라 값만 바꿀 수 있게 해준다.

---

## 4.3 count와 함께 사용하는 조건부 생성

조건식은 리소스 생성 여부 자체를 제어하는 데도 자주 사용한다.

가장 대표적인 방식이 `count = 조건 ? 1 : 0` 패턴이다.

예시:

```
resource "aws_instance" "bastion" {
  count         = var.enable_bastion ? 1 : 0
  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"
}
```

이 코드는 `enable_bastion`이 `true`이면 1개 생성하고,

`false`이면 0개 생성한다.

즉, 조건부 생성이 가능하다.

---

## 4.4 주의점

조건부 생성에서 `count`를 사용하면 생성 여부가 바뀔 때

리소스 주소가 배열 형태로 바뀐다.

예를 들면 다음처럼 된다.

* 생성 시 → `aws_instance.bastion[0]`

* 미생성 시 → 없음

즉, 나중에 참조할 때도 이 구조를 이해해야 한다.

---

## 5. 리스트, 맵, 객체

반복 구성을 잘 하려면 Terraform의 컬렉션 타입을 이해해야 한다.

반복은 결국 **데이터 구조를 기반으로 리소스를 생성하는 방식**이기 때문이다.

---

## 5.1 리스트(list)

리스트는 순서가 있는 값의 모음이다.

예시:

```
["subnet-a", "subnet-b", "subnet-c"]
```

또는 변수로 선언할 수 있다.

```
variable "subnet_cidrs" {
  type = list(string)
}
```

예시 값:

```
subnet_cidrs = ["10.10.1.0/24", "10.10.2.0/24"]
```

리스트는 순서가 중요할 때 유용하다.

하지만 순서 변경의 영향을 받을 수 있다는 점도 함께 고려해야 한다.

---

## 5.2 맵(map)

맵은 key-value 구조다.

예시:

```
{
  web-a = "t3.micro"
  web-b = "t3.small"
}
```

변수 선언 예시:

```
variable "instance_types" {
  type = map(string)
}
```

맵은 이름 기반으로 값을 관리하기 좋다.

그래서 `for_each`와 매우 잘 어울린다.

---

## 5.3 객체(object)

객체는 여러 속성을 묶은 구조다.

리스트나 맵보다 더 구조화된 데이터를 표현할 수 있다.

예를 들어 하나의 서브넷 정보를 객체로 표현할 수 있다.

```
{
  name = "public-a"
  cidr = "10.10.1.0/24"
  az   = "ap-northeast-2a"
}
```

변수 선언 예시:

```
variable "subnets" {
  type = map(object({
    cidr = string
    az   = string
  }))
}
```

예시 값:

```
subnets = {
  public-a = {
    cidr = "10.10.1.0/24"
    az   = "ap-northeast-2a"
  }
  public-c = {
    cidr = "10.10.2.0/24"
    az   = "ap-northeast-2c"
  }
}
```

이 구조를 사용하면 리소스 반복 시 더 풍부한 설정을 함께 전달할 수 있다.

---

## 6. for\_each와 객체 조합

실무에서는 `for_each + map(object(...))` 조합이 매우 자주 사용된다.

이유는 각 리소스가 이름과 여러 속성을 함께 가지는 경우가 많기 때문이다.

예시:

```
resource "aws_subnet" "public" {
  for_each = var.subnets

  vpc_id            = aws_vpc.main.id
  cidr_block        = each.value.cidr
  availability_zone = each.value.az

  tags = {
    Name = each.key
  }
}
```

이 코드는 `var.subnets`의 각 항목을 기준으로 Subnet을 생성한다.

예를 들어

* key → `public-a`

* value.cidr → `10.10.1.0/24`

* value.az → `ap-northeast-2a`

이런 식으로 해석된다.

즉, 반복 구성은 단순히 개수만 늘리는 것이 아니라

**데이터 구조를 기반으로 인프라를 선언하는 방식**으로 발전한다.

## 7 for

`for` 표현식은 주로 **리스트(List)나 맵(Map)의 데이터를 가공하여 새로운 형태의 리스트나 맵을 만들 때** 사용함. 앞서 설명한 `for_each`가 리소스를 생성하는 '반복문'이라면, `for`는 데이터를 변환하는 '필터'나 '매퍼'라고 이해하면 됨.

### 7.1. `for` 표현식의 기본 원리

기본적인 문법 구조는 다음과 같음.

* **리스트 생성:** `[for item in list : item.value]`

* **맵 생성:** `{for key, value in map : key => value.upper()}`

---

### 7.2. 주요 활용 예제

### ① 리스트 변환 (소문자를 대문자로)

사용자가 입력한 서브넷 이름 리스트를 모두 대문자로 바꿔서 태그에 넣고 싶을 때 사용함.

```
variable "names" {
  default = ["web", "db", "app"]
}

locals {
  # 결과: ["WEB", "DB", "APP"]
  upper_names = [for n in var.names : upper(n)]
}
```

### ② 조건문(if)과 함께 사용 (필터링)

특정 조건에 맞는 데이터만 골라내서 새로운 리스트를 만들 때 아주 강력함.

```
variable "users" {
  default = [
    { name = "alice", is_admin = true },
    { name = "bob",   is_admin = false },
    { name = "charlie", is_admin = true }
  ]
}

locals {
  # 관리자(is_admin이 true)인 사용자의 이름만 추출
  # 결과: ["alice", "charlie"]
  admin_names = [for u in var.users : u.name if u.is_admin]
}
```

### ③ 맵(Map) 가공 (가장 실무적인 케이스)

객체 형태의 데이터를 가공해서 특정 리소스의 입력값으로 넘길 때 자주 사용함.

```
variable "subnets" {
  default = {
    "public_a" = { az = "ap-northeast-2a", cidr = "10.0.1.0/24" }
    "public_b" = { az = "ap-northeast-2b", cidr = "10.0.2.0/24" }
  }
}

locals {
  # CIDR 블록만 따로 모은 맵 생성
  # 결과: { "public_a" = "10.0.1.0/24", "public_b" = "10.0.2.0/24" }
  subnet_cidrs = { for k, v in var.subnets : k => v.cidr }
}
```

---

### 7.3. `for_each`와 `for`의 조합

실무에서는 `for`로 데이터를 먼저 예쁘게 가공한 뒤, 그 결과물을 `for_each`에 집어넣어 리소스를 생성하는 식으로 많이 사용함.

```
resource "aws_subnet" "example" {
  # locals에서 필터링하거나 가공한 데이터를 for_each에 전달
  for_each = { for k, v in var.subnets : k => v if v.az == "ap-northeast-2a" }

  vpc_id     = aws_vpc.main.id
  cidr_block = each.value.cidr
  availability_zone = each.value.az
}
```

---

## 8. dynamic 블록

## 8.1 왜 dynamic이 필요한가

Terraform에서는 어떤 리소스 내부에 중첩 블록이 반복적으로 들어가야 하는 경우가 있다.

대표적인 예가 Security Group의 `ingress` 규칙이다.

예를 들어 아래처럼 직접 여러 블록을 쓸 수 있다.

```
resource "aws_security_group" "web_sg" {
  name   = "web-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

이 방식은 규칙이 많아지면 반복이 늘어난다.

이럴 때 `dynamic` 블록을 사용할 수 있다.

---

## 8.2 기본 구조

```
dynamic "블록이름" {
  for_each = 반복대상
  content {
    ...
  }
}
```

즉, 중첩 블록을 반복적으로 생성하는 방식이다.

---

## 8.3 Security Group ingress 예제

```
variable "ingress_rules" {
  type = list(object({
    port        = number
    description = string
  }))
}
```

예시 값:

```
ingress_rules = [
  {
    port        = 22
    description = "SSH"
  },
  {
    port        = 80
    description = "HTTP"
  }
]
```

리소스 예시:

```
resource "aws_security_group" "web_sg" {
  name   = "web-sg"
  vpc_id = aws_vpc.main.id

  dynamic "ingress" {
    for_each = var.ingress_rules
    content {
      description = ingress.value.description
      from_port   = ingress.value.port
      to_port     = ingress.value.port
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }
}
```

이 코드는 `ingress_rules` 리스트의 각 항목을 기준으로 ingress 블록을 반복 생성한다.

---

## 8.4 dynamic 블록의 의미

`dynamic`은 리소스 자체를 반복 생성하는 것이 아니라,

**리소스 내부의 중첩 블록을 반복 생성**하는 기능이다.

즉, 다음처럼 구분해야 한다.

* `count`, `for_each` → 리소스 반복

* `dynamic` → 리소스 내부 블록 반복

이 차이가 중요하다.

## 9. 반복 구성 설계 방식

Terraform에서 반복을 설계할 때는 단순히 “반복문을 쓰자”가 아니라

**무엇을 기준으로 반복할 것인지**를 먼저 결정해야 한다.

---

## 9.1 count가 적합한 경우

다음 같은 상황에서는 `count`가 적합하다.

* 동일한 리소스를 개수만큼 만들면 됨

* 각 항목의 차이가 거의 없음

* 숫자 인덱스로 충분함

* 학습이나 간단한 테스트용 구성

예:

* 동일 사양 EC2 2대

* 동일한 퍼블릭 IP 3개

* 동일한 테스트 볼륨 여러 개

---

## 9.2 for\_each가 적합한 경우

다음 같은 상황에서는 `for_each`가 더 적합하다.

* 각 리소스의 이름이 중요함

* 항목별 속성이 다름

* 순서보다 식별자가 중요함

* 변경 안정성이 중요함

예:

* 이름이 있는 여러 Subnet 생성

* 역할별 서로 다른 Security Group 생성

* 서버 이름별 인스턴스 구성

---

## 9.3 dynamic이 적합한 경우

다음 같은 상황에서는 `dynamic`이 적합하다.

* 리소스 안에 중첩 블록이 반복되어야 함

* ingress, egress, 태그 규칙, 설정 블록 등을 반복 생성해야 함

예:

* Security Group ingress 규칙 여러 개

* EBS 블록 설정 반복

* 특정 리소스의 nested configuration 반복

---

## 9.4 선택 기준 요약

다음처럼 기억하면 좋다.

* 같은 리소스를 단순 개수로 반복 → `count`

* 항목 기반으로 안정적으로 반복 → `for_each`

* 리소스 내부 블록 반복 → `dynamic`

---

## 10. 장 정리

이 장의 핵심은 다음과 같다.

* `count`는 개수 기반 반복이다.

* `for_each`는 항목 기반 반복이다.

* 조건식은 값이나 생성 여부를 제어하는 데 사용한다.

* 리스트, 맵, 객체는 반복 구성을 위한 데이터 구조다.

* `dynamic` 블록은 리소스 내부의 중첩 블록을 반복 생성한다.

* 단순 반복은 `count`, 안정적 식별 기반 반복은 `for_each`, 중첩 블록 반복은 `dynamic`이 적합하다.

즉, Terraform 고급 표현식과 반복 구성의 핵심은

**코드를 많이 쓰는 것이 아니라, 데이터를 기준으로 인프라를 선언하는 방식으로 전환하는 것**이다.

---

# 실습. Terraform 고급 표현식과 반복 구성 실습

## 실습 목표

이 실습에서는 다음을 확인한다.

* `count`로 동일 리소스를 여러 개 생성하는 방법

* `for_each`로 이름 기반 반복 구성을 만드는 방법

* 조건식으로 값과 생성 여부를 제어하는 방법

* 리스트, 맵, 객체를 반복 구성에 연결하는 방법

* `dynamic` 블록으로 Security Group ingress 규칙을 반복 생성하는 방법

---

## 실습 1. count로 동일한 EC2 여러 대 생성하기

### 실습 목적

동일한 EC2를 개수 기반으로 반복 생성하는 방법을 익힌다.

---

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
  count         = 2
  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"

  tags = {
    Name = "count-web-${count.index}"
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

* EC2가 2개 생성될 계획인지 확인

* 리소스 주소가 `aws_instance.web[0]`, `aws_instance.web[1]` 형태인지 이해

* `count.index` 값이 태그 이름에 반영되는지 확인

---

## 실습 2. for\_each로 이름 기반 EC2 생성하기

### 실습 목적

이름을 기준으로 각 인스턴스를 구분하는 `for_each` 방식을 익힌다.

---

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
  for_each = toset(["web-a", "web-b"])

  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"

  tags = {
    Name = each.value
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

* 리소스 주소가 `aws_instance.web["web-a"]`, `aws_instance.web["web-b"]` 형태인지 이해

* 숫자 인덱스가 아니라 이름으로 구분된다는 점 확인

* 항목 기반 반복이라는 점 이해

---

## 실습 3. 맵을 이용해 서로 다른 인스턴스 타입 적용하기

### 실습 목적

`for_each`와 맵을 결합해서 각 인스턴스마다 다른 속성을 적용하는 방식을 익힌다.

---

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

locals {
  instance_config = {
    web-a = "t3.micro"
    web-b = "t3.small"
  }
}

resource "aws_instance" "web" {
  for_each = local.instance_config

  ami           = data.aws_ami.amazon_linux.id
  instance_type = each.value

  tags = {
    Name = each.key
  }
}
```

---

### 확인 포인트

* `each.key`는 인스턴스 이름

* `each.value`는 인스턴스 타입

* 항목별로 서로 다른 사양을 줄 수 있다는 점 확인

---

## 실습 4. 조건식으로 인스턴스 타입 제어하기

### 실습 목적

환경 변수에 따라 다른 값을 선택하는 조건식을 익힌다.

---

### `variables.tf`

```
variable "environment" {
  type        = string
  description = "Deployment environment"
  default     = "dev"
}
```

---

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
  instance_type = var.environment == "prod" ? "t3.small" : "t3.micro"

  tags = {
    Name = "conditional-web"
  }
}
```

---

### 실행 예시

```
terraform plan-var="environment=dev"
terraform plan-var="environment=prod"
```

---

### 확인 포인트

* `dev`일 때와 `prod`일 때 인스턴스 타입이 다르게 계산되는지 확인

* 조건식이 속성값을 제어하는 데 사용된다는 점 이해

---

## 실습 5. count를 이용한 조건부 생성

### 실습 목적

특정 조건에서만 리소스를 생성하는 패턴을 익힌다.

---

### `variables.tf`

```
variable "enable_bastion" {
  type        = bool
  description = "Whether to create bastion instance"
  default     = false
}
```

---

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

resource "aws_instance" "bastion" {
  count         = var.enable_bastion ? 1 : 0
  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"

  tags = {
    Name = "bastion"
  }
}
```

---

### 실행 예시

```
terraform plan-var="enable_bastion=false"
terraform plan-var="enable_bastion=true"
```

---

### 확인 포인트

* `false`일 때는 생성 계획이 없음

* `true`일 때는 1개 생성 계획이 나타남

* 조건부 생성이 `count`와 함께 자주 사용된다는 점 이해

---

## 실습 6. 객체 기반으로 Subnet 반복 생성하기

### 실습 목적

`map(object(...))` 구조를 이용해 여러 속성을 가진 리소스를 반복 생성하는 방식을 익힌다.

---

### `variables.tf`

```
variable "subnets" {
  type = map(object({
    cidr = string
    az   = string
  }))
}
```

---

### `terraform.tfvars`

```
subnets = {
  public-a = {
    cidr = "10.10.1.0/24"
    az   = "ap-northeast-2a"
  }
  public-c = {
    cidr = "10.10.2.0/24"
    az   = "ap-northeast-2c"
  }
}
```

---

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

resource "aws_vpc" "main" {
  cidr_block = "10.10.0.0/16"
}

resource "aws_subnet" "public" {
  for_each = var.subnets

  vpc_id            = aws_vpc.main.id
  cidr_block        = each.value.cidr
  availability_zone = each.value.az

  tags = {
    Name = each.key
  }
}
```

---

### 확인 포인트

* 각 Subnet이 key 이름으로 식별됨

* 각 Subnet이 서로 다른 CIDR, AZ를 가질 수 있음

* 객체 구조를 통해 복합 속성을 전달한다는 점 이해

---

## 실습 7. dynamic 블록으로 Security Group ingress 반복 생성하기

### 실습 목적

리소스 내부 중첩 블록을 반복 생성하는 `dynamic` 사용법을 익힌다.

---

### `variables.tf`

```
variable "ingress_rules" {
  type = list(object({
    port        = number
    description = string
  }))
}
```

---

### `terraform.tfvars`

```
ingress_rules = [
  {
    port        = 22
    description = "SSH"
  },
  {
    port        = 80
    description = "HTTP"
  }
]
```

---

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

resource "aws_vpc" "main" {
  cidr_block = "10.10.0.0/16"
}

resource "aws_security_group" "web_sg" {
  name   = "web-sg"
  vpc_id = aws_vpc.main.id

  dynamic "ingress" {
    for_each = var.ingress_rules
    content {
      description = ingress.value.description
      from_port   = ingress.value.port
      to_port     = ingress.value.port
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

---

### 확인 포인트

* Security Group은 1개만 생성됨

* 하지만 ingress 블록은 여러 개 반복 생성됨

* `dynamic`은 리소스 내부 블록 반복이라는 점 확인