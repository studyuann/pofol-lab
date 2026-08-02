---
title: "2장 AWS 계정 보안 아키텍처"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 아키텍처 설계(ARC)"]
is_public: true
draft: false
---

# 2장 AWS 계정 보안 아키텍처

## 2.1 AWS 계정 보안 개요

AWS에서 가장 중요한 보안 요소는 **계정(Account)**임.

AWS의 모든 리소스는 **계정 단위로 소유됨.**

예

* EC2

* S3

* RDS

* IAM

모든 리소스는 **특정 AWS 계정에 속함.**

따라서 AWS 보안의 시작은 다음과 같음.

```
계정 보호 → 권한 관리 → 자격증명 보호
```

AWS에서는 이를 위해 **IAM (Identity and Access Management)** 서비스를 제공함.

---

# 2.2 AWS 보안 주체 (Security Principal)

보안 주체는 **AWS 리소스에 접근할 수 있는 대상**을 의미함.

AWS에서 대표적인 보안 주체

| 보안 주체 | 설명 |
| --- | --- |
| Root Account | AWS 계정 생성 시 생성되는 최고 권한 계정 |
| IAM User | 사람 또는 애플리케이션 사용자 |
| IAM Role | AWS 서비스 또는 사용자에게 임시 권한 제공 |
| Federated User | 외부 인증 시스템 사용자 |

---

# 2.3 Root 계정

AWS 계정을 생성하면 **Root 사용자**가 자동으로 생성됨.

특징

* 모든 권한 보유

* 제한 없음

* 삭제 불가능

Root 계정은 **일상적인 작업에 사용하면 안됨.**

Root 계정 사용이 필요한 경우

* AWS 계정 생성

* 결제 설정 변경

* Support Plan 변경

* IAM 권한 복구

---

## Root 계정 보안 권장사항

AWS Best Practice

1 Root 계정 MFA 활성화

2 Access Key 생성 금지

3 일상 작업에 사용하지 않음

4 Root 로그인 알림 설정

---

# 2.4 IAM 개념

IAM은 **AWS 리소스 접근 권한을 관리하는 서비스**임.

IAM 구성 요소

```
User
Group
Policy
Role
```

---

## IAM 구성요소 구조

```
IAM User
   │
IAM Group
   │
IAM Policy
```

또는

```
AWS Service
    │
 IAM Role
    │
 IAM Policy
```

---

# 2.5 IAM User

IAM User는 AWS 계정을 사용하는 **개별 사용자**임.

예

* 개발자

* 운영자

* 관리자

특징

* 고유한 로그인 정보

* Access Key 발급 가능

IAM User 인증 방식

| 인증 방식 | 설명 |
| --- | --- |
| Password | Console 로그인 |
| Access Key | CLI / API |

---

# 2.6 IAM Group

Group은 여러 IAM User를 묶는 기능임.

예

```
Developers
Admins
Operators
```

구조

```
Group
 ├ User1
 ├ User2
 └ User3
```

권한은 **User가 아니라 Group에 부여하는 것이 권장됨.**

---

# 2.7 IAM Policy

Policy는 **권한 정의 문서**임.

JSON 형식으로 작성됨.

예

```
{
 "Version": "2012-10-17",
 "Statement": [
   {
     "Effect": "Allow",
     "Action": "s3:*",
     "Resource": "*"
   }
 ]
}
```

Policy 구성 요소

| 요소 | 설명 |
| --- | --- |
| Effect | Allow / Deny |
| Action | 수행 가능한 API |
| Resource | 대상 리소스 |

---

# 2.8 IAM Role

Role은 **임시 권한을 제공하는 IAM 객체**임.

특징

* Access Key 없음

* 임시 자격증명 사용

* Assume Role 방식

주요 사용 사례

| 사용 사례 | 설명 |
| --- | --- |
| EC2 → S3 접근 | EC2 Role |
| Lambda → DynamoDB | Service Role |
| Cross Account Access | 다른 계정 접근 |

---

## EC2 Role 구조

```
EC2 Instance
     │
Assume Role
     │
IAM Role
     │
IAM Policy
     │
AWS Resource
```

---

# 2.9 IAM 권한 정책 종류

IAM Policy는 2가지 종류가 있음.

| 정책 | 설명 |
| --- | --- |
| Managed Policy | AWS 또는 사용자가 관리 |
| Inline Policy | 특정 User 또는 Role에 직접 연결 |

---

## AWS Managed Policy 예

* AmazonS3FullAccess

* AmazonEC2FullAccess

* AdministratorAccess

---

# 2.10 AWS 자격증명 (Credential)

AWS 인증에는 다음 정보가 사용됨.

```
Access Key ID
Secret Access Key
```

CLI / SDK 사용 시 필요함.

---

# 2.11 AWS CLI 인증 설정 실습

IAM 사용자 Access Key를 이용해 CLI 인증 설정을 수행함.

---

## Access Key 생성

IAM 콘솔

```
IAM → Users → 사용자 선택
```

Security credentials 탭 선택

```
Create access key
```

---

## CLI 인증 설정

터미널에서 실행

```
aws configure
```

입력 항목

```
AWS Access Key ID
AWS Secret Access Key
Region
Output format
```

예

```
AWS Access Key ID: AKIAxxxx
AWS Secret Access Key: xxxxxxxx
Default region name: ap-northeast-2
Default output format: json
```

---

# 2.12 CLI 인증 확인 실습

현재 로그인한 AWS 계정 확인

```
aws sts get-caller-identity
```

출력 예

```
{
 "UserId": "AIDA...",
 "Account": "123456789012",
 "Arn": "arn:aws:iam::123456789012:user/student"
}
```

설명

현재 CLI 인증이 정상적으로 설정되었는지 확인하는 명령임.

---

# 2.13 IAM 실습

## 실습 목표

IAM 사용자 생성 후 CLI로 AWS 접근.

---

## 1 IAM User 생성

AWS Console

```
IAM → Users → Create user
```

설정

```
User name: student1
Access type: Console + Programmatic
```

---

## 2 권한 부여

```
Attach policies directly
```

선택

```
AdministratorAccess
```

---

## 3 Access Key 생성

```
Security credentials → Create access key
```

---

## 4 CLI 인증 설정

```
aws configure
```

---

## 5 인증 테스트

```
aws s3 ls
```

설명

현재 계정의 S3 버킷 목록을 조회함.

---

# 2.14 IAM Best Practice

AWS 권장 보안 방식

1 Root 계정 사용 금지

2 MFA 사용

3 최소 권한 원칙

4 Role 사용

5 Access Key 주기적 변경

---