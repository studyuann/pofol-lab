---
title: "1장 IaC와 Terraform 이해 및 실습 환경 준비"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "배포자동화를 위한 Terraform"]
is_public: true
draft: false
---

# 1장. IaC와 Terraform 이해 및 실습 환경 준비

## 1. 학습 목표

* IaC(Infrastructure as Code)의 개념을 이해한다.

* 수작업 인프라 구성 방식의 한계를 이해한다.

* Terraform의 역할과 기본 구조를 이해한다.

* Terraform의 주요 구성 요소와 실행 흐름을 이해한다.

* AWS 환경에서 Terraform을 사용하는 이유를 이해한다.

* CloudFormation과 Terraform의 차이를 개괄적으로 이해한다.

* Terraform 설치와 기본 실행 준비를 완료한다.

---

## 2. 인프라 관리 방식의 변화

클라우드 환경에서는 단순히 서버 한 대만 생성한다고 끝나지 않는다.

실제 환경에서는 VPC, 서브넷, 인터넷 게이트웨이, NAT 게이트웨이, 라우팅 테이블, 보안 그룹, EC2, EBS, IAM, 로드밸런서, 데이터베이스 같은 다양한 자원을 함께 구성해야 한다.

초기 학습 단계에서는 AWS Management Console을 사용해 직접 클릭하면서 자원을 생성하는 방식이 직관적이다.

어떤 메뉴에서 어떤 리소스를 만드는지 눈으로 확인할 수 있기 때문이다.

하지만 환경 규모가 커지거나 반복 작업이 많아지면 수작업 방식은 여러 한계를 드러낸다.

예를 들어 다음과 같은 상황이 자주 발생한다.

* 같은 구성을 개발 환경, 테스트 환경, 운영 환경에 반복 적용해야 함

* 누가 어떤 설정으로 자원을 만들었는지 추적하기 어려움

* 콘솔에서 클릭하다가 옵션 하나를 빠뜨릴 수 있음

* 환경마다 설정이 조금씩 달라질 수 있음

* 동일한 구조를 다시 만들어야 할 때 재현이 어려움

예를 들어 운영 환경에서는 특정 보안 그룹 규칙을 엄격하게 설정했는데,

개발 환경에서는 실수로 전체 IP에 SSH를 열어둘 수 있다.

또는 운영 환경에서는 태그를 체계적으로 붙였지만, 개발 환경에서는 태그를 누락할 수도 있다.

이처럼 수작업 기반 인프라 운영은 다음 문제가 생기기 쉽다.

* 일관성 부족

* 반복 작업 증가

* 변경 이력 추적 어려움

* 자동화 어려움

* 운영 실수 가능성 증가

이 문제를 해결하기 위한 대표 방식이 **IaC**다.

---

## 3. IaC 개념

IaC는 **Infrastructure as Code**의 약자다.

인프라 구성을 사람이 콘솔에서 직접 만들기보다, **코드로 정의하고 코드 기준으로 관리하는 방식**이다.

즉, 다음과 같은 흐름으로 생각하면 된다.

1. 원하는 인프라 상태를 코드로 작성한다.

2. IaC 도구가 코드를 읽는다.

3. 실제 클라우드 환경과 비교한다.

4. 필요한 자원을 생성, 변경, 삭제한다.

IaC의 핵심은 단순 자동 실행이 아니라 **원하는 상태를 코드로 선언**한다는 점이다.

### 3.1 선언형 관리

IaC 도구는 보통 선언형 방식으로 동작한다.

선언형 방식은 “어떻게 만들 것인가”보다 “어떤 상태가 되어야 하는가”를 정의하는 방식이다.

예를 들어 사용자는 다음처럼 원하는 상태를 코드로 적는다.

* 서울 리전에 VPC 1개가 있어야 함

* 퍼블릭 서브넷 2개가 있어야 함

* EC2 인스턴스 1대가 있어야 함

* 80 포트는 전체 허용이어야 함

* 22 포트는 특정 IP만 허용이어야 함

그러면 IaC 도구가 현재 상태와 비교하여 필요한 작업을 계산한다.

### 3.2 재현성

IaC의 가장 큰 장점 중 하나는 같은 코드를 사용하면 같은 인프라를 반복적으로 만들 수 있다는 점이다.

예를 들어 동일한 코드로 다음 환경을 만들 수 있다.

* 개인 실습 환경

* 개발 환경

* 테스트 환경

* 운영 환경

환경마다 값은 일부 다를 수 있다.

예를 들어 운영 환경은 더 큰 인스턴스를 쓰고, 개발 환경은 더 작은 인스턴스를 쓸 수 있다.

하지만 구조 자체는 같은 코드 기반으로 유지할 수 있다.

### 3.3 버전 관리

인프라 코드도 애플리케이션 코드처럼 Git으로 관리할 수 있다.

이렇게 하면 다음이 가능하다.

* 누가 언제 어떤 변경을 했는지 기록 가능

* 변경 전후 비교 가능

* 코드 리뷰 가능

* 이전 버전으로 되돌리기 쉬움

즉, 인프라 변경도 개발 프로세스 안으로 들어오게 된다.

### 3.4 표준화

조직에서는 자원 이름 규칙, 태그 규칙, 네트워크 구성 방식, 보안 정책 같은 표준이 중요하다.

IaC를 사용하면 이러한 규칙을 코드 수준에서 반복 적용할 수 있다.

예를 들어 모든 EC2 인스턴스에 공통 태그를 붙이거나,

기본 보안 그룹 정책을 동일하게 적용하거나,

표준 VPC 구조를 모듈 형태로 재사용할 수 있다.

### 3.5 자동화

IaC는 CI/CD 파이프라인과 결합하기 좋다.

예를 들어 GitHub Actions, Jenkins, GitLab CI와 연결하면 인프라 코드 변경 시 검증, 계획 확인, 배포 자동화를 구성할 수 있다.

---

## 4. Terraform 개요

Terraform은 HashiCorp가 만든 대표적인 IaC 도구다.

Terraform의 가장 큰 특징은 **특정 클라우드 하나에만 종속되지 않고 다양한 플랫폼을 공통 방식으로 관리할 수 있다는 점**이다.

Terraform은 AWS뿐 아니라 다음과 같은 플랫폼도 다룰 수 있다.

* Microsoft Azure

* Google Cloud

* Kubernetes

* GitHub

* Cloudflare

* Datadog

* VMware

* 다양한 SaaS 및 인프라 플랫폼

즉, Terraform은 AWS 자동화 도구라기보다 **범용 인프라 관리 도구**에 가깝다.

이번 과정에서는 AWS를 대상으로 실습하지만, Terraform의 범용성은 여전히 중요하다.

왜냐하면 AWS 안에서도 여러 계정, 여러 환경, 여러 리전을 일관된 방식으로 관리하는 데 유리하고,

향후 다른 플랫폼과의 연계 가능성도 확보할 수 있기 때문이다.

Terraform은 기본적으로 **HCL(HashiCorp Configuration Language)** 이라는 전용 언어를 사용한다.

HCL은 사람이 읽기 쉽게 설계된 선언형 구성 언어다.

JSON보다 가독성이 좋고, 인프라 코드 작성에 적합하게 설계되어 있다.

---

## 5. Terraform의 주요 구성 요소

Terraform 코드를 읽고 작성하려면 몇 가지 핵심 구성 요소를 먼저 이해해야 한다.

### 5.1 Provider

Provider는 Terraform이 어떤 플랫폼과 통신할지 정의하는 구성 요소다.

AWS를 관리하려면 AWS Provider가 필요하다.

예시는 다음과 같다.

```
provider "aws" {
  region = "ap-northeast-2"
}
```

이 설정은 Terraform이 AWS 서울 리전과 통신하도록 지정한다.

여기서 `region = "ap-northeast-2"`는 매우 중요하다.

같은 코드라도 어느 리전에 배포하느냐에 따라 생성되는 리소스 위치가 달라지기 때문이다.

### 5.2 Resource

Resource는 실제로 생성하거나 관리할 인프라 자원을 의미한다.

예를 들어 EC2, VPC, Subnet, Security Group, EBS, IAM Role 등이 모두 Resource가 될 수 있다.

예시는 다음과 같다.

```
resource "aws_instance" "web" {
  ami           = "ami-0123456789abcdef0"
  instance_type = "t3.micro"

  tags = {
    Name = "terraform-web"
  }
}
```

이 코드의 각 요소는 다음 의미를 가진다.

* `resource`  
  Terraform이 관리할 실제 자원을 선언한다는 의미다.

* `"aws_instance"`  
  AWS Provider가 제공하는 EC2 인스턴스 리소스 타입이다.

* `"web"`  
  해당 리소스의 로컬 이름이다.  
  Terraform 코드 내부에서 이 이름으로 참조한다.

* `ami`  
  인스턴스를 생성할 때 사용할 머신 이미지다.  
  운영체제와 기본 구성이 들어있는 템플릿이라고 이해하면 된다.

* `instance_type`  
  인스턴스의 CPU, 메모리 사양을 지정한다.

* `tags`  
  AWS 자원에 붙일 메타데이터다.  
  운영 식별, 비용 분석, 자원 분류에 자주 사용한다.

### 5.3 Variable

Variable은 값을 외부로 분리하여 코드 재사용성을 높일 때 사용한다.

예를 들어 환경마다 인스턴스 타입만 다르게 쓰고 싶다면 변수를 사용할 수 있다.

```
variable "instance_type" {
  default = "t3.micro"
}
```

이 변수는 다음처럼 참조할 수 있다.

```
resource "aws_instance" "web" {
  ami           = "ami-0123456789abcdef0"
  instance_type = var.instance_type
}
```

변수를 사용하는 이유는 다음과 같다.

* 하드코딩 감소

* 환경별 값 분리

* 코드 재사용성 향상

* 협업 편의성 증가

### 5.4 Output

Output은 Terraform 실행 결과 중 중요한 값을 출력할 때 사용한다.

예를 들어 생성된 EC2 인스턴스의 퍼블릭 IP, 인스턴스 ID, VPC ID 등을 출력할 수 있다.

```
output "instance_id" {
  value = aws_instance.web.id
}
```

이렇게 하면 `terraform apply` 실행 후 결과 화면에서 해당 값을 확인할 수 있다.

### 5.5 Data Source

Data Source는 이미 존재하는 정보를 조회할 때 사용한다.

예를 들어 기존에 존재하는 AMI를 검색하거나, 이미 만들어진 VPC 정보를 읽어올 때 사용할 수 있다.

즉, 다음처럼 구분하면 된다.

* Resource: 새로 만들거나 관리할 대상

* Data Source: 이미 존재하는 정보를 조회할 대상

### 5.6 State

Terraform은 자신이 관리하는 인프라 상태를 별도의 state 파일에 저장한다.

기본적으로는 `terraform.tfstate` 파일이 생성된다.

State에는 다음 정보가 들어간다.

* Terraform이 어떤 자원을 만들었는지

* 각 자원의 실제 ID가 무엇인지

* 코드와 실제 인프라 사이 연결 정보

* 다음 실행 시 비교에 필요한 현재 상태 정보

Terraform은 코드만 보고 동작하지 않는다.

**코드 + state + 실제 인프라 상태**를 함께 비교하여 변경 내용을 계산한다.

---

## 6. Terraform의 동작 방식

Terraform은 기본적으로 다음 순서로 동작한다.

1. 코드를 작성한다.

2. 필요한 Provider를 초기화한다.

3. 현재 상태와 코드 정의를 비교한다.

4. 변경 예정 사항을 계산한다.

5. 실제 인프라에 적용한다.

이 흐름을 제대로 이해하려면 Terraform의 대표 명령어를 알아야 한다.

### 6.1 `terraform init`

Terraform 작업 디렉터리를 초기화하는 명령이다.

처음 작업을 시작할 때 가장 먼저 실행한다.

```
terraform init
```

이 명령이 하는 일은 다음과 같다.

* 현재 디렉터리의 Terraform 설정 파일을 확인함

* 필요한 Provider 정보를 분석함

* 필요한 Provider 플러그인을 다운로드함

* 작업 디렉터리를 Terraform 실행 가능 상태로 준비함

즉, `init`은 “이 디렉터리에서 Terraform 작업을 시작할 준비를 한다”는 의미다.

### 6.2 `terraform plan`

코드 기준으로 어떤 변경이 발생할지 미리 계산하여 보여주는 명령이다.

실제 인프라를 바로 변경하지는 않는다.

```
terraform plan
```

이 명령이 중요한 이유는 다음과 같다.

* 실수로 삭제되거나 변경되는 자원이 없는지 확인 가능

* 코드가 의도대로 동작하는지 검토 가능

* 팀 단위 리뷰가 가능

* 운영 환경 적용 전 안전장치 역할 수행

`plan` 결과에서는 보통 다음을 확인한다.

* 새로 생성될 자원

* 변경될 자원

* 삭제될 자원

즉, `plan`은 실제 적용 전에 보는 검토 보고서라고 이해하면 된다.

### 6.3 `terraform apply`

`plan` 결과를 실제 인프라에 반영하는 명령이다.

```
terraform apply
```

실행하면 Terraform은 어떤 변경이 이루어질지 다시 보여주고,

사용자 확인을 받은 뒤 실제 AWS 자원을 생성, 변경, 삭제한다.

자동 승인 옵션을 사용하면 확인 과정 없이 바로 반영할 수도 있다.

```
terraform apply -auto-approve
```

실습에서는 빠르게 진행하기 위해 이 옵션을 쓰는 경우도 있다.

하지만 학습 초기나 운영 환경에서는 변경 내용을 확인하는 습관이 중요하다.

### 6.4 `terraform destroy`

Terraform이 만든 자원을 삭제하는 명령이다.

```
terraform destroy
```

AWS 실습에서는 매우 중요하다.

실습이 끝난 뒤 리소스를 정리하지 않으면 과금이 발생할 수 있기 때문이다.

자동 승인 옵션도 사용할 수 있다.

```
terraform destroy -auto-approve
```

---

## 7. Terraform 코드 예제

가장 단순한 수준의 예제를 먼저 살펴보자.

```
provider "aws" {
  region = "ap-northeast-2"
}

resource "aws_instance" "web" {
  ami           = "ami-0123456789abcdef0"
  instance_type = "t3.micro"

  tags = {
    Name = "tf-web-01"
  }
}

output "instance_id" {
  value = aws_instance.web.id
}
```

이 코드의 의미를 순서대로 정리하면 다음과 같다.

1. AWS 서울 리전을 사용한다.

2. EC2 인스턴스 1대를 생성한다.

3. 사용할 AMI를 지정한다.

4. 인스턴스 타입은 `t3.micro`다.

5. 태그 이름은 `tf-web-01`이다.

6. 생성이 끝나면 인스턴스 ID를 출력한다.

여기서 중요한 점은 Terraform이 단순 스크립트가 아니라는 점이다.

이 코드는 “이런 자원이 존재해야 한다”는 원하는 상태를 선언한 것이다.

Terraform은 이를 기준으로 현재 상태와 비교해 필요한 작업을 수행한다.

---

## 8. Terraform을 사용하는 이유

Terraform을 사용하는 이유는 다음과 같이 정리할 수 있다.

### 8.1 가독성

Terraform은 HCL을 사용한다.

HCL은 인프라 구성을 표현하기 쉽게 설계되어 있어, 많은 사용자가 YAML이나 JSON 기반 템플릿보다 읽기 쉽다고 느낀다.

### 8.2 모듈화와 재사용

Terraform은 반복되는 구성을 모듈화하기 쉽다.

예를 들어 VPC 구성, 보안 그룹 구성, EC2 생성 구성을 각각 모듈로 만들어 여러 환경에서 재사용할 수 있다.

### 8.3 변경 계획 확인

`terraform plan`을 통해 실제 반영 전에 무엇이 바뀌는지 명확히 확인할 수 있다.

이 기능은 실수 방지와 리뷰 측면에서 매우 중요하다.

### 8.4 멀티 환경 관리

실무에서는 개발, 테스트, 운영 환경이 분리되어 있는 경우가 많다.

Terraform은 동일한 구조를 여러 환경에 반복 적용하기 좋다.

### 8.5 다양한 Provider 지원

Terraform은 다양한 Provider를 지원한다.

즉, AWS뿐 아니라 Azure, Google Cloud, Kubernetes, GitHub, Cloudflare, Datadog 같은 여러 플랫폼을 같은 방식으로 관리할 수 있다.

---

## 9. CloudFormation과의 관계

CloudFormation은 AWS가 제공하는 공식 IaC 서비스다.

AWS 자원을 YAML 또는 JSON 템플릿으로 정의하고, 스택(Stack) 단위로 관리한다.

### 9.1 CloudFormation의 특징

* AWS 네이티브 IaC 도구다.

* AWS 서비스와 통합이 자연스럽다.

* YAML 또는 JSON 형식 템플릿을 사용한다.

* 스택 단위로 리소스를 관리한다.

### 9.2 Terraform과 CloudFormation 비교

| 항목 | Terraform | CloudFormation |
| --- | --- | --- |
| 개발 주체 | HashiCorp | AWS |
| 지원 범위 | 멀티 클라우드 및 다양한 플랫폼 | AWS 중심 |
| 구성 언어 | HCL | YAML / JSON |
| 상태 관리 | 별도 state 파일 사용 | AWS 스택 상태 기반 |
| 확장성 | 높음 | AWS 내부 운영에 최적화 |
| 학습 방향 | 범용 IaC 개념 확장 가능 | AWS 네이티브 방식 이해에 적합 |

## 10. Terraform 설치

Terraform 실습을 진행하려면 먼저 로컬 PC에 Terraform CLI를 설치해야 한다.

Terraform은 대부분의 작업을 명령줄에서 수행하므로, 설치 후 버전 확인까지 완료해야 한다.

운영체제별 설치 방법은 다음과 같다.

* 테라폼 공식 사이트

<https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli>

### 10.1 Windows 설치

Windows에서는 공식 다운로드 페이지에서 압축 파일을 내려받아 설치하는 방식이 일반적이다.

설치 절차는 다음과 같다.

1. Terraform 공식 다운로드 페이지에 접속한다.

2. Windows AMD64 버전을 다운로드한다.

3. 압축 파일을 해제한다.

4. `terraform.exe` 파일을 원하는 폴더에 저장한다.  
   예: `C:\terraform`

5. 해당 폴더 경로를 시스템 환경 변수 `Path`에 추가한다.

6. 새 명령 프롬프트 또는 PowerShell 창을 연다.

7. 버전 확인 명령을 실행한다.

```
terraform version
```

정상 설치되었다면 다음과 같은 형식으로 버전이 출력된다.

```
Terraform v1.x.x
on windows_amd64
```

### Path 등록 의미

환경 변수 `Path`에 Terraform 실행 파일 경로를 등록하는 이유는,

어느 디렉터리에서든 `terraform` 명령을 실행할 수 있게 하기 위해서다.

만약 Path 등록이 되어 있지 않으면 다음과 같은 문제가 발생할 수 있다.

* `terraform` 명령을 찾지 못함

* PowerShell 또는 CMD에서 실행 실패

* 특정 폴더에서만 실행 가능

즉, Windows에서는 설치 파일을 받는 것만으로 끝나지 않고, **Path 등록까지 해야 설치가 완료된 것**으로 봐야 한다.

---

### 10.2 macOS 설치

macOS에서는 Homebrew를 사용하는 방식이 가장 일반적이다.

```
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
```

설치가 끝나면 다음 명령으로 확인한다.

```
terraform version
```

정상 설치되었다면 버전 정보가 출력된다.

Homebrew를 사용하면 장점이 있다.

* 설치가 간단함

* 업그레이드가 쉬움

* 다른 패키지 관리와 일관성 있음

---

### 10.3 Linux 설치

Ubuntu 계열 리눅스에서는 HashiCorp 공식 저장소를 등록한 후 설치할 수 있다.

```
sudo apt-get update && sudo apt-get install -y gnupg software-properties-common
wget -O- https://apt.releases.hashicorp.com/gpg | \
gpg --dearmor | \
sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg > /dev/null
gpg --no-default-keyring \
--keyring /usr/share/keyrings/hashicorp-archive-keyring.gpg \
--fingerprint
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(grep -oP '(?<=UBUNTU_CODENAME=).*' /etc/os-release || lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update
sudo apt-get install terraform
```

설치 후 다음 명령으로 확인한다.

```
terraform version
```

정상 설치되면 리눅스 플랫폼 기준 버전 정보가 출력된다.

---

## 11. 기본 동작 테스트용 디렉터리 준비

Terraform 설치가 끝났다면 기본 동작 테스트를 위한 작업 디렉터리를 하나 준비한다.

```
mkdir terraform-basic
cd terraform-basic
```

이 디렉터리는 앞으로 Terraform 설정 파일을 저장하고 실행하는 작업 공간 역할을 한다.

Terraform은 보통 현재 디렉터리 안에 있는 `.tf` 파일들을 읽어서 동작한다.

즉, 어느 폴더에서 Terraform 명령을 실행하느냐가 중요하다.

예를 들어 `terraform-basic` 디렉터리 안에서 `main.tf` 파일을 만들고 실행하면,

Terraform은 해당 디렉터리를 하나의 작업 단위처럼 취급한다.

---

## 12. 최소 구성 예제 파일 작성

기본 동작만 확인할 목적이라면 다음과 같이 최소 구성 파일을 만들 수 있다.

파일명: `main.tf`

```
terraform {
  required_version = ">= 1.5.0"

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

이 코드의 의미는 다음과 같다.

### 12.1 `terraform` 블록

이 블록은 Terraform 자체 설정을 정의한다.

* `required_version = ">= 1.5.0"`  
  이 코드는 Terraform 1.5.0 이상 버전에서 동작해야 한다는 의미다.  
  너무 오래된 버전을 사용하는 경우 예기치 않은 문제를 줄이는 데 도움이 된다.

* `required_providers`  
  이 작업에서 사용할 Provider 정보를 정의한다.

### 12.2 `source = "hashicorp/aws"`

사용할 Provider의 출처를 의미한다.

여기서는 HashiCorp가 제공하는 공식 AWS Provider를 사용한다.

### 12.3 `version = "~> 5.0"`

Provider 버전 범위를 지정한다.

이 표기는 5.x 대 버전을 허용하되, 큰 버전 변화로 인한 예기치 않은 동작 차이를 줄이기 위해 사용한다.

### 12.4 `provider "aws"`

Terraform이 AWS와 통신할 때 사용할 기본 설정이다.

* `region = "ap-northeast-2"`  
  AWS 서울 리전을 사용하겠다는 의미다.

이 최소 구성 예제는 아직 실제 리소스를 만들지는 않는다.

하지만 Provider 초기화와 설정 파일 해석이 가능한지 확인하는 데 유용하다.

---

## 13. Terraform 기본 실행 흐름

이제 이 디렉터리에서 Terraform의 기본 흐름을 확인할 수 있다.

### 13.1 초기화

```
terraform init
```

이 명령을 실행하면 Terraform은 현재 디렉터리의 설정 파일을 읽고,

필요한 AWS Provider를 다운로드하여 작업을 초기화한다.

정상적으로 완료되면 다음과 같은 의미를 가진다.

* 설정 파일 문법이 크게 문제없음

* Provider 다운로드가 가능함

* Terraform 작업 디렉터리가 준비되었음

### 13.2 계획 확인

```
terraform plan
```

현재 예제는 실제 리소스를 정의하지 않았으므로,

큰 변경 사항 없이 설정을 검토하는 수준으로 동작한다.

하지만 이후 EC2, VPC, 보안 그룹 같은 리소스를 추가하면 이 명령이 매우 중요해진다.

실제 적용 전에 어떤 자원이 생성, 변경, 삭제될지 미리 보여주기 때문이다.

### 13.3 적용

리소스를 정의한 뒤에는 다음 명령으로 실제 AWS에 반영할 수 있다.

```
terraform apply
```

이 장에서는 아직 실제 리소스 생성하지 않으므로,

여기서는 기본 명령 흐름 이해에 중점을 둔다.

### 13.4 삭제

Terraform이 만든 자원은 다음 명령으로 삭제할 수 있다.

```
terraform destroy
```

---

## 14. 정리

* IaC는 인프라를 코드로 관리하는 방식이다.

* 수작업 인프라 관리의 한계를 줄이고 재현성과 일관성을 높일 수 있다.

* Terraform은 범용 IaC 도구이며 AWS 환경에서도 널리 사용된다.

* Terraform은 Provider, Resource, Variable, Output, Data Source, State 개념으로 동작한다.

* Terraform 설치 후 `init`, `plan`, `apply`, `destroy` 흐름을 이해하는 것이 중요하다.