---
title: "8장 IAM"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 클라우드 기술 기초(TESS)"]
is_public: true
draft: false
---

# 8장 IAM

# 1. IAM 개요

## IAM (Identity and Access Management)

IAM은 AWS 리소스에 대한 인증과 권한 관리를 담당하는 서비스이다.

AWS 환경에서는 수많은 리소스가 존재한다.

```
EC2
S3
RDS
Lambda
VPC
DynamoDB
CloudWatch
```

이 리소스들은 아무나 접근할 수 있으면 안 된다.

누가 로그인할 수 있는지, 누가 어떤 서비스에 접근할 수 있는지, 어떤 작업까지 허용할 것인지를 제어해야 한다.

IAM은 바로 이 문제를 해결하기 위한 서비스이다.

AWS에서는 기본적으로 다음 질문에 답할 수 있어야 한다.

```
누가(Who)
어떤 방식으로 인증되었는가(Authentication)
무엇을 할 수 있는가(What Action)
어떤 리소스에 대해 가능한가(Which Resource)
```

예를 들면 다음과 같은 통제가 필요하다.

```
사용자 A는 S3 버킷 조회만 가능
사용자 B는 EC2 시작/중지만 가능
EC2 인스턴스는 특정 S3 버킷에만 접근 가능
Lambda 함수는 DynamoDB 테이블 읽기만 가능
```

즉 IAM은 단순히 “사용자 계정 생성” 서비스가 아니라,

**AWS 환경 전체의 접근 통제 체계**라고 이해해야 한다.

---

# 2. 인증과 권한의 차이

IAM을 이해할 때 먼저 구분해야 하는 개념이 있다.

```
Authentication
Authorization
```

---

## 2.1 Authentication

Authentication은 “누구인지 확인하는 과정”이다.

예를 들어 다음이 인증에 해당한다.

```
사용자 이름과 비밀번호로 콘솔 로그인
Access Key와 Secret Key로 CLI 호출
AssumeRole을 통해 임시 자격 증명 획득
```

즉 AWS는 먼저 요청을 보낸 주체가 누구인지 확인한다.

---

## 2.2 Authorization

Authorization은 “무엇을 할 수 있는지 판단하는 과정”이다.

예를 들면 다음과 같다.

```
이 사용자는 S3 ListBucket 가능
이 역할은 EC2 DescribeInstances 가능
이 Lambda 실행 역할은 DynamoDB PutItem 불가
```

즉 인증이 “누구인가”라면, 인가는 “무엇을 할 수 있는가”이다.

IAM은 이 두 과정을 모두 다루지만, 특히 **인가**, 즉 권한 제어가 핵심이다.

---

# 3. IAM의 핵심 구성 요소

IAM은 다음 요소를 중심으로 동작한다.

```
IAM User
IAM Group
IAM Role
IAM Policy
```

이 네 가지를 단순히 외우는 것이 아니라, 서로 어떤 관계인지 이해해야 한다.

* **User**: 사람이나 애플리케이션을 위한 개별 주체

* **Group**: 여러 User를 묶는 권한 관리 단위

* **Role**: 임시로 권한을 사용할 수 있게 만든 역할

* **Policy**: 실제 권한 내용을 정의한 문서

즉 권한은 보통 다음 구조로 연결된다.

```
Principal
  └ Policy
      └ AWS Resource
```

여기서 Principal은 User, Role, AWS Service 등이 될 수 있다.

---

# 4. IAM User

## IAM User란 무엇인가

IAM User는 AWS에 로그인하거나 API를 호출할 수 있는 개별 사용자 계정이다.

보통 사람 단위 계정으로 많이 설명하지만, 과거에는 애플리케이션용 고정 계정처럼 사용하기도 했음.

다만 현재 운영 기준에서는 애플리케이션에는 가능하면 User보다 Role 사용을 권장한다.

예를 들면 다음과 같다.

```
개발자 계정
운영자 계정
보안 관리자 계정
```

IAM User의 특징은 다음과 같다.

```
AWS Management Console 로그인 가능
Access Key 생성 가능
개별 Policy 부여 가능
Group에 소속될 수 있음
MFA 설정 가능
```

구조는 다음과 같이 볼 수 있다.

```
IAM User
   │
   ▼
IAM Policy
   │
   ▼
AWS Service / Resource
```

---

## 4.1 IAM User가 필요한 이유

조직에서 여러 명이 AWS를 사용한다면, 같은 계정을 공유해서는 안 된다.

예를 들어 모든 사람이 Root 계정을 같이 사용하면 다음 문제가 발생한다.

```
누가 어떤 작업을 했는지 추적 어려움
권한 분리 불가능
보안 사고 시 영향 범위 큼
비밀번호 노출 시 전체 계정 위험
```

따라서 사용자별로 IAM User를 분리하거나, 더 나아가 IAM Identity Center 같은 중앙 인증 체계를 사용해야 한다.

---

## 4.2 IAM User의 자격 증명

IAM User는 여러 방식으로 인증할 수 있다.

### 콘솔 로그인

AWS Management Console에 웹으로 로그인하는 방식이다.

필요 요소는 다음과 같다.

```
계정 ID 또는 별칭
사용자 이름
비밀번호
MFA 코드(선택 또는 권장)
```

### 프로그래밍 방식 접근

CLI, SDK, API 호출을 위해 Access Key / Secret Access Key를 사용할 수 있다.

```
Access Key ID
Secret Access Key
```

다만 장기 자격 증명은 유출 위험이 있기 때문에, 현재는 가능하면 임시 자격 증명 기반 방식을 더 권장한다.

---

# 5. IAM Group

IAM Group은 여러 사용자를 묶어서 공통 권한을 부여하기 위한 기능이다.

실제 운영에서는 사용자마다 같은 정책을 일일이 붙이면 관리가 매우 번거롭다.

그래서 역할이 비슷한 사용자들을 그룹으로 묶는다.

예를 들면 다음과 같다.

```
Developers
Operators
Admins
Auditors
```

구조는 다음과 같다.

```
User
 │
 ▼
Group
 │
 ▼
Policy
```

즉 권한을 User에 직접 붙이는 대신 Group에 붙이고, 사용자를 Group에 넣는 방식으로 관리할 수 있다.

---

## 5.1 Group의 장점

```
권한 관리 단순화
일관된 권한 부여 가능
사용자 추가/삭제 시 운영 편의성 향상
개별 User에 과도한 직접 정책 연결 감소
```

예를 들어 Developers 그룹에 EC2 조회 권한과 S3 읽기 권한을 부여해 두면, 새 개발자가 입사했을 때 해당 그룹에만 추가하면 된다.

---

## 5.2 Group 사용 시 주의점

Group은 **IAM User만 포함**할 수 있다.

Role은 Group에 넣을 수 없다.

또한 Group 자체는 로그인 주체가 아니다.

즉 Group은 권한을 묶는 단위이지, API를 호출하거나 콘솔 로그인하는 주체가 아니다.

---

# 6. IAM Policy

Policy는 AWS 서비스에 대한 권한을 정의하는 JSON 문서이다.

즉 “무엇을 할 수 있는가”를 기계적으로 표현한 규칙이다.

예를 들면 다음 권한을 정책으로 정의할 수 있다.

```
S3 객체 조회
EC2 인스턴스 시작
DynamoDB 테이블 조회
CloudWatch 로그 읽기
```

예시 정책은 다음과 같다.

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::example-bucket/*"
    }
  ]
}
```

---

## 6.1 Policy의 핵심 구성 요소

### Effect

요청을 허용할지 거부할지를 정의한다.

```
Allow
Deny
```

### Action

어떤 작업을 할 수 있는지를 정의한다.

예

```
s3:GetObject
ec2:StartInstances
dynamodb:PutItem
```

### Resource

어떤 리소스에 대해 권한이 적용되는지를 정의한다.

예

```
arn:aws:s3:::example-bucket/*
arn:aws:ec2:ap-northeast-2:123456789012:instance/*
```

---

## 6.2 Statement 구조

정책은 보통 Statement 배열 안에 여러 권한 규칙을 포함한다.

즉 하나의 정책 안에서 다음을 함께 정의할 수 있다.

```
S3 읽기 허용
특정 버킷만 허용
특정 작업은 거부
```

필요에 따라 `Condition`을 사용해 더 정교한 제어도 가능하다.

예를 들어 다음과 같은 조건이 가능하다.

```
특정 IP에서만 허용
MFA 사용 시만 허용
특정 리전에서만 허용
특정 태그를 가진 리소스만 허용
```

즉 Policy는 단순 Allow 목록이 아니라, **세밀한 권한 제어 규칙**을 정의하는 도구이다.

---

## 6.3 Managed Policy와 Inline Policy

IAM Policy는 크게 두 가지 방식으로 사용할 수 있다.

### Managed Policy

AWS가 제공하거나, 사용자가 별도로 만들어 여러 대상에 재사용할 수 있는 정책이다.

예

```
AmazonS3ReadOnlyAccess
AmazonEC2ReadOnlyAccess
```

장점

```
재사용 가능
중앙 관리 가능
운영 편의성 높음
```

### Inline Policy

특정 User, Group, Role에 직접 내장되는 정책이다.

장점도 있지만, 재사용성과 관리성이 떨어질 수 있다.

따라서 일반적으로는 Managed Policy 중심으로 운영하는 경우가 많다.

---

# 7. IAM Role

IAM Role은 권한을 담고 있지만, 고정 로그인 계정은 아닌 권한 단위이다.

즉 Role은 사용자가 직접 비밀번호로 로그인하는 계정이 아니라,

누군가가 필요할 때 **AssumeRole** 해서 임시로 사용하는 권한 집합이다.

Role은 다음 상황에서 주로 사용된다.

```
AWS 서비스가 다른 리소스에 접근할 때
다른 AWS 계정의 권한을 사용할 때
일시적으로 관리자 권한으로 승격할 때
애플리케이션에 장기 Access Key를 주지 않을 때
```

---

## 7.1 Role 구조

```
Principal
   │
   │ AssumeRole
   ▼
IAM Role
   │
   ▼
IAM Policy
   │
   ▼
AWS Resource
```

즉 Role은 “누가 이 역할을 맡을 수 있는가”와 “이 역할이 어떤 권한을 가지는가”라는 두 가지 요소로 구성된다.

* 누가 맡을 수 있는가 → Trust Policy

* 어떤 권한을 가지는가 → Permission Policy

이 구분이 매우 중요하다.

---

## 7.2 Trust Policy와 Permission Policy

Role을 이해할 때 가장 많이 헷갈리는 부분이다.

### Trust Policy

누가 이 Role을 사용할 수 있는지를 정의한다.

예

```
EC2 서비스가 이 Role을 사용할 수 있음
특정 AWS 계정의 사용자가 이 Role을 AssumeRole 할 수 있음
```

### Permission Policy

이 Role을 사용한 뒤 어떤 작업이 가능한지를 정의한다.

예

```
S3 버킷 읽기 가능
DynamoDB PutItem 가능
CloudWatch Logs 기록 가능
```

즉 Role은 다음 두 단계를 모두 만족해야 한다.

```
1. 이 Role을 맡을 수 있어야 함
2. 맡은 뒤 허용된 권한 범위 안에서만 작업 가능
```

---

# 8. AWS 서비스에서 Role 사용

AWS 서비스는 IAM User처럼 장기 계정을 두고 동작하지 않는다.

그래서 AWS 서비스가 다른 리소스에 접근해야 할 때는 Role을 사용한다.

예를 들면 다음과 같다.

```
EC2 → S3 접근
Lambda → DynamoDB 접근
ECS Task → SQS 접근
CodeBuild → ECR 접근
```

구조는 다음과 같다.

```
AWS Service
     │
     ▼
IAM Role
     │
     ▼
IAM Policy
     │
     ▼
AWS Resource
```

예를 들어 EC2가 S3에 접근해야 한다고 하자.

이때 EC2 인스턴스 안에 Access Key를 직접 저장하는 방식은 보안상 좋지 않다.

대신 EC2에 Role을 연결하면, EC2는 메타데이터 서비스를 통해 임시 자격 증명을 받아 S3에 접근한다.

즉 다음 구조가 권장된다.

```
EC2 Instance Profile
   └ IAM Role
       └ S3 접근 권한
```

이 방식의 장점은 다음과 같다.

```
장기 Access Key 불필요
자동 순환되는 임시 자격 증명 사용
권한 변경이 중앙에서 가능
보안성 향상
```

---

# 9. AssumeRole

AssumeRole은 Role의 권한을 임시로 획득하는 동작이다.

이 과정은 AWS STS(Security Token Service)를 통해 이루어진다.

STS는 일정 시간 동안만 유효한 임시 자격 증명을 발급한다.

특징은 다음과 같다.

```
Temporary Credential 생성
만료 시간 존재
장기 키보다 안전함
필요 시점에만 권한 획득 가능
```

구조는 다음과 같다.

```
Principal
   │
   │ AssumeRole
   ▼
IAM Role
   │
   ▼
Temporary Credential
```

이 임시 자격 증명은 보통 다음 요소로 구성된다.

```
Access Key ID
Secret Access Key
Session Token
Expiration
```

즉 일반 Access Key와 비슷해 보이지만, **세션 토큰과 만료 시간**이 있다는 점이 다르다.

---

# 10. 역할 전환 (Switch Role)

Switch Role은 콘솔에서 다른 Role의 권한으로 전환해서 작업하는 기능이다.

예를 들면 평소에는 읽기 권한만 가진 개발자가,

필요할 때만 운영 계정의 특정 Role로 전환해서 작업할 수 있다.

예

```
DeveloperUser → AdminRole 전환
```

구조는 다음과 같다.

```
IAM User
   │
   │ Switch Role
   ▼
IAM Role
   │
   ▼
추가 권한 사용
```

콘솔에서는 보통 계정 메뉴에서 역할 전환 기능을 통해 사용한다.

이 방식은 다음과 같은 운영 모델에 적합하다.

```
평상시 저권한 사용
필요 시 일시적 권한 상승
작업 후 원래 권한으로 복귀
```

즉 상시 관리자 권한을 주는 것보다 보안상 더 바람직한 구조를 만들 수 있다.

---

# 11. Policy 평가 개념

IAM은 단순히 정책 하나만 보고 권한을 결정하지 않는다.

여러 정책과 여러 계층의 제어를 함께 평가한다.

기본 개념은 다음과 같다.

### 기본은 거부

명시적으로 허용되지 않으면 기본적으로 거부된다.

```
Implicit Deny
```

### 명시적 허용

정책에 Allow가 있으면 해당 작업이 가능할 수 있다.

### 명시적 거부 우선

어딘가에 명시적 Deny가 있으면 Allow보다 우선한다.

```
Explicit Deny > Allow
```

이 원칙은 매우 중요하다.

즉 다음처럼 이해하면 된다.

```
기본값은 불가
허용 정책이 있어야 가능
거부 정책이 있으면 최종적으로 불가
```

실제 AWS에서는 IAM Policy 외에도 Resource Policy, SCP, Permission Boundary 등 여러 요소가 함께 작동할 수 있다.

초반에는 우선 **명시적 Deny가 최우선**이라는 점만 정확히 잡으면 된다.

---

# 12. Access Key와 CLI 인증

AWS CLI는 Access Key와 Secret Key 또는 임시 자격 증명을 이용해 AWS API를 호출한다.

가장 기본적인 설정 명령은 다음과 같다.

```
aws configure
```

입력 항목은 보통 다음과 같다.

```
Access Key ID
Secret Access Key
Default region
Output format
```

CLI 요청은 내부적으로 서명 과정을 거쳐 AWS에 전달된다.

즉 단순 평문 비밀번호 전송 방식이 아니라, 요청에 대한 인증 서명을 포함한다.

---

## 12.1 Access Key 사용 시 주의점

Access Key는 편리하지만 보안상 매우 민감한 정보이다.

주의점은 다음과 같다.

```
소스코드에 직접 저장하지 않음
GitHub에 업로드하지 않음
장기간 고정 사용하지 않음
주기적으로 회전 필요
가능하면 Role 기반 임시 자격 증명 사용
```

특히 EC2, Lambda, ECS 같은 AWS 서비스 내부에서는 Access Key를 직접 넣기보다 Role 사용이 권장된다.

---

## 12.2 콘솔 세션 기반 CLI 사용

최근에는 콘솔 로그인 또는 IAM Identity Center 기반 세션을 이용해 CLI 인증을 처리하는 방식도 사용한다.

이 방식은 장기 Access Key 사용을 줄일 수 있다는 장점이 있다.

즉 운영 환경에서는 가능한 한 **고정 키보다 세션 기반 인증**을 지향하는 것이 좋다.

---

# 13. IAM 보안 모범 사례

AWS IAM 사용 시 다음 원칙을 따르는 것이 좋다.

---

## 13.1 최소 권한 원칙

필요한 권한만 부여한다.

예를 들어 S3 읽기만 필요한 사용자에게 전체 관리자 권한을 주면 안 된다.

```
필요 최소한의 Action
필요 최소한의 Resource
필요 시에만 권한 부여
```

---

## 13.2 Root 계정 사용 제한

Root 계정은 AWS 계정 자체의 최고 권한 계정이다.

이 계정은 다음 특징이 있다.

```
모든 권한 보유
과금 및 계정 설정 변경 가능
복구 어려운 작업 가능
```

따라서 일상 운영에는 사용하지 않는 것이 원칙이다.

권장 방식은 다음과 같다.

```
Root 계정 MFA 활성화
일상 작업에 Root 계정 사용하지 않음
Root 자격 증명 안전하게 보관
```

---

## 13.3 가능하면 Role 사용

특히 AWS 서비스 간 권한 부여에서는 장기 Access Key보다 Role 사용이 바람직하다.

```
EC2에는 Role 부여
Lambda에는 Execution Role 부여
ECS Task에는 Task Role 부여
```

이렇게 하면 자격 증명을 코드나 서버에 고정 저장하지 않아도 된다.

---

## 13.4 MFA 사용

관리자급 계정과 중요한 계정은 MFA를 활성화하는 것이 좋다.

즉 비밀번호가 유출되더라도 추가 인증 요소가 있어야 로그인할 수 있게 해야 한다.

---

## 13.5 공용 정책과 과도한 와일드카드 사용 주의

다음과 같은 정책은 매우 위험할 수 있다.

```
{
  "Effect": "Allow",
  "Action": "*",
  "Resource": "*"
}
```

관리자 계정 외에는 이런 형태를 남발하지 않는 것이 좋다.

---

## 13.6 장기 키보다 임시 자격 증명 선호

가능하면 STS, Role, Identity Center 같은 방식을 사용해서 임시 자격 증명을 쓰는 것이 더 안전하다.

---

# 14. IAM 구조 정리

AWS IAM 권한 구조는 다음과 같이 정리할 수 있다.

```
Principal
(User / Role / AWS Service)
        │
        ▼
Authentication
        │
        ▼
Policy Evaluation
        │
        ▼
AWS Resource Access
```

좀 더 단순화하면 다음과 같다.

```
Principal
   └ Policy
       └ Resource
```

단, 실제로는 다음 질문을 함께 생각해야 한다.

```
누가 요청했는가
어떤 방식으로 인증되었는가
어떤 정책이 연결되어 있는가
명시적 Deny가 있는가
대상 리소스가 무엇인가
```

---

# 15. 핵심 정리

IAM의 핵심 개념은 다음과 같다.

```
User   → 사람 또는 개별 주체 계정
Group  → 여러 User를 묶는 권한 관리 단위
Policy → 권한을 정의하는 JSON 문서
Role   → 임시로 권한을 사용할 수 있는 역할
```

권한 흐름은 다음처럼 이해하면 된다.

```
Principal → Policy → Resource
```

운영 관점에서 특히 중요한 포인트는 다음과 같다.

```
기본은 거부
명시적 Deny가 우선
장기 Access Key보다 Role 권장
AWS 서비스에는 Role 사용
최소 권한 원칙 적용
Root 계정은 일상 운영에 사용하지 않음
```

즉 IAM은 단순 계정 관리 기능이 아니라,

AWS 전체 환경의 보안과 운영 통제를 책임지는 가장 기본적인 보안 체계이다.