---
title: "boto3로 로그인 사용자 권한별 IAM Role 생성 및 AssumeRole 권한 차이"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "클라우드 자동화를 위한 파이썬 프로그래밍", "5장 AWS 운영 보안 점검 자동화"]
is_public: true
draft: false
---

# boto3로 로그인 사용자 권한별 IAM Role 생성 및 AssumeRole 권한 차이 확인

---

## 1. 실습 개요

**프론트엔드 로그인 사용자 기반 AWS 리소스 제어 실습**을 준비하기 위해, AWS IAM Role 기반 권한 분리 구조를 먼저 구성한다.

실습에서는 다음 3개의 IAM Role을 생성한다.

```
app-viewer-role
app-operator-role
app-admin-role
```

각 Role은 서로 다른 권한을 가진다.

| 애플리케이션 권한 | IAM Role | 권한 수준 |
| --- | --- | --- |
| `viewer` | `app-viewer-role` | EC2/S3 조회만 가능 |
| `operator` | `app-operator-role` | EC2 조회, 시작, 중지 가능 |
| `admin` | `app-admin-role` | EC2 운영 작업 + S3 객체 업로드 가능 |

아직 프론트엔드 로그인 기능은 만들지 않는다.

대신 로컬에서 AWS Profile로 인증한 IAM User가 각 Role을 `AssumeRole` 한 뒤, Role별 권한 차이를 확인한다.

---

## 2. 실습 목표

이번 실습의 목표는 다음과 같다.

```
1. 현재 로컬 AWS Profile의 IAM User 정보를 확인한다.
2. viewer, operator, admin Role을 생성한다.
3. 각 Role의 Trust Policy에 현재 IAM User를 Principal로 등록한다.
4. 각 Role에 서로 다른 Permission Policy를 연결한다.
5. 로컬 IAM User가 각 Role을 AssumeRole 한다.
6. AssumeRole 이후에는 IAM User 권한이 아니라 Role 권한으로 동작함을 확인한다.
7. 이후 FastAPI와 프론트엔드 로그인 사용자 권한 제어 구조로 확장할 준비를 한다.
```

---

## 3. 전체 구조

이번 실습 구조는 다음과 같다.

```
로컬 PC
  ↓
AWS Profile
  ↓
IAM User: instructor
  ↓ sts:AssumeRole
app-viewer-role
app-operator-role
app-admin-role
  ↓
각 Role 권한으로 AWS API 호출
```

이후 FastAPI와 프론트엔드 실습에서는 아래 구조로 확장된다.

```
프론트엔드 로그인 사용자
  ↓
FastAPI 백엔드
  ↓
로그인 사용자 권한 확인
  ↓
USER_ROLE_MAP에서 IAM Role ARN 선택
  ↓
sts:AssumeRole
  ↓
Role 권한으로 AWS 리소스 제어
```

---

# 4. 현재 실습 환경의 전제

현재 학생들이 사용하는 IAM User에는 `AdministratorAccess` 또는 이에 준하는 FullAccess 권한이 부여되어 있다고 가정한다.

예를 들어 현재 profile로 인증한 IAM User가 다음과 같다고 가정한다.

```
aws sts get-caller-identity --profile instructor
```

예상 출력:

```
{
    "UserId": "AIDAxxxxxxxxxxxxx",
    "Account": "471166314777",
    "Arn": "arn:aws:iam::471166314777:user/instructor"
}
```

현재 학생 IAM User는 관리자 권한이 있으므로 다음 작업을 수행할 수 있다.

```
iam:CreateRole
iam:PutRolePolicy
iam:UpdateAssumeRolePolicy
iam:DeleteRole
sts:AssumeRole
ec2:*
s3:*
```

따라서 이번 실습에서는 별도로 학생 IAM User에게 `sts:AssumeRole` 권한을 추가하지 않아도 된다.

하지만 이 점은 반드시 설명해야 한다.

---

## 4.1 일반 IAM User라면 AssumeRole 권한이 별도로 필요함

현재 학생 IAM User는 관리자 권한이 있기 때문에 `sts:AssumeRole`도 이미 가능하다.

하지만 일반 IAM User라면 상황이 다르다.

일반 IAM User가 특정 Role을 AssumeRole 하려면, 해당 IAM User에게 명시적으로 `sts:AssumeRole` 권한이 있어야 한다.

예를 들어 일반 IAM User가 아래 3개 Role을 AssumeRole 해야 한다면, 사용자에게 다음 정책이 필요하다.

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowAssumeApplicationRoles",
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": [
        "arn:aws:iam::471166314777:role/app-viewer-role",
        "arn:aws:iam::471166314777:role/app-operator-role",
        "arn:aws:iam::471166314777:role/app-admin-role"
      ]
    }
  ]
}
```

이 정책은 다음 의미를 가진다.

| 항목 | 의미 |
| --- | --- |
| `Effect: Allow` | 허용 정책 |
| `Action: sts:AssumeRole` | Role을 맡는 작업 허용 |
| `Resource` | AssumeRole 가능한 대상 Role 제한 |

즉, 일반 IAM User는 아무 Role이나 AssumeRole 할 수 있는 것이 아니다.

허용된 Role ARN에 대해서만 AssumeRole 할 수 있다.

---

## 4.2 AssumeRole 성공 조건

AssumeRole이 성공하려면 항상 두 조건이 모두 필요하다.

```
조건 1. 호출하는 주체에게 sts:AssumeRole 권한이 있어야 한다.

조건 2. 대상 Role의 Trust Policy가 호출 주체를 Principal로 신뢰해야 한다.
```

현재 실습 환경에서는 학생 IAM User가 관리자 권한이 있으므로 조건 1은 이미 충족되어 있다.

이번 실습 코드에서는 조건 2를 만족시키기 위해 Role의 Trust Policy에 현재 IAM User ARN을 넣는다.

예:

```
{
  "Effect": "Allow",
  "Principal": {
    "AWS": "arn:aws:iam::471166314777:user/instructor"
  },
  "Action": "sts:AssumeRole"
}
```

정리하면 다음과 같다.

| 항목 | 현재 실습 환경 |
| --- | --- |
| 학생 IAM User의 `sts:AssumeRole` 권한 | 관리자 권한에 포함되어 있음 |
| 대상 Role의 Trust Policy | 실습 코드에서 직접 설정 |
| 대상 Role의 Permission Policy | viewer/operator/admin별로 다르게 설정 |

---

# 5. 핵심 개념

## 5.1 IAM User

IAM User는 AWS 계정 안에서 사람 또는 애플리케이션을 식별하는 장기 자격 증명이다.

이번 실습에서는 로컬 AWS Profile이 IAM User의 자격 증명을 사용한다.

```
AWS Profile
  ↓
IAM User instructor
```

현재 학생 IAM User는 관리자 권한을 가지고 있으므로 직접 EC2, S3, IAM을 제어할 수 있다.

하지만 이번 실습의 목적은 관리자 권한을 직접 사용하는 것이 아니다.

핵심은 다음이다.

```
관리자 권한을 가진 IAM User가 Role을 AssumeRole 한 뒤,
Assume한 Role의 권한으로만 동작하는지 확인한다.
```

---

## 5.2 IAM Role

IAM Role은 특정 주체가 임시로 맡아서 사용할 수 있는 권한 묶음이다.

Role 자체는 Access Key를 직접 가지지 않는다.

대신 STS `AssumeRole`을 통해 임시 자격 증명을 발급받아 사용한다.

```
IAM User
  ↓ sts:AssumeRole
IAM Role
  ↓
임시 Access Key 발급
  ↓
Role 권한으로 AWS API 호출
```

---

## 5.3 Trust Policy

Trust Policy는 Role에 설정되는 정책이다.

“누가 이 Role을 AssumeRole 할 수 있는가?”를 정의한다.

예:

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "TrustLocalIamUser",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::471166314777:user/instructor"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

이 정책의 의미는 다음과 같다.

```
arn:aws:iam::471166314777:user/instructor 사용자는
이 Role을 AssumeRole 할 수 있다.
```

여기서 중요한 점은 `Principal`이다.

```
"Principal": {
  "AWS": "arn:aws:iam::471166314777:user/instructor"
}
```

`Principal`에는 AssumeRole API를 실제 호출하는 AWS 주체를 넣는다.

이번 실습에서는 로컬에서 실행하므로 IAM User가 Principal이 된다.

이후 EC2에서 FastAPI를 실행하면 Principal은 EC2에 연결된 Instance Profile Role이 된다.

---

## 5.4 Permission Policy

Permission Policy는 Role을 Assume한 뒤 어떤 AWS 작업을 할 수 있는지 정의한다.

예를 들어 viewer Role에는 조회 권한만 부여한다.

```
{
  "Effect": "Allow",
  "Action": [
    "ec2:DescribeInstances",
    "s3:ListAllMyBuckets"
  ],
  "Resource": "*"
}
```

이 정책은 다음 의미를 가진다.

```
이 Role을 Assume한 세션은 EC2 조회와 S3 버킷 목록 조회를 할 수 있다.
```

하지만 `ec2:StopInstances`, `s3:PutObject` 같은 권한은 없으므로 해당 작업은 실패한다.

---

# 6. Role별 권한 설계

## 6.1 viewer Role

`app-viewer-role`은 조회 전용 Role이다.

허용 작업:

```
ec2:DescribeInstances
ec2:DescribeInstanceStatus
ec2:DescribeTags
ec2:DescribeSecurityGroups
ec2:DescribeVolumes
s3:ListAllMyBuckets
s3:ListBucket
```

허용하지 않는 작업:

```
ec2:StartInstances
ec2:StopInstances
s3:PutObject
```

---

## 6.2 operator Role

`app-operator-role`은 운영 담당자 Role이다.

허용 작업:

```
ec2:DescribeInstances
ec2:DescribeInstanceStatus
ec2:DescribeTags
ec2:StartInstances
ec2:StopInstances
s3:ListAllMyBuckets
s3:ListBucket
```

허용하지 않는 작업:

```
s3:PutObject
iam:*
ec2:TerminateInstances
```

---

## 6.3 admin Role

`app-admin-role`은 실습용 관리자 Role이다.

허용 작업:

```
ec2:Describe*
ec2:StartInstances
ec2:StopInstances
ec2:RebootInstances
ec2:CreateTags
ec2:DeleteTags
s3:ListAllMyBuckets
s3:ListBucket
s3:GetObject
s3:PutObject
```

주의할 점은 `admin`이라고 해서 `AdministratorAccess`를 그대로 연결하지 않는다는 것이다.

이번 실습의 목적은 역할별 권한 차이를 확인하는 것이므로, 필요한 범위 안에서 권한을 넓힌다.

---

# 7. 실습 파일 구성

```
iam-role-login-prep-lab/
├── 01_create_roles.py
├── 02_assume_role_test.py
├── 03_cleanup_roles.py
└── README.md
```

---

# 8. 사전 준비

## 8.1 boto3 설치

```
pip install boto3
```

명령어 설명:

```
pip
  Python 패키지를 설치하는 명령어다.

install
  지정한 패키지를 현재 Python 환경에 설치한다.

boto3
  Python에서 AWS API를 호출하기 위한 AWS SDK다.
```

---

## 8.2 AWS Profile 확인

현재 학생들이 사용하는 profile 이름을 확인한다.

```
aws configure list-profiles
```

예상 출력:

```
default
instructor
```

`instructor` profile을 사용한다고 가정하고 현재 인증 주체를 확인한다.

```
aws sts get-caller-identity --profile instructor
```

명령어 설명:

```
aws
  AWS CLI 명령어 실행 프로그램이다.

sts
  AWS Security Token Service 관련 명령을 실행한다.

get-caller-identity
  현재 인증된 AWS 주체의 Account, UserId, Arn을 확인한다.

--profile instructor
  로컬 AWS 설정 중 instructor profile을 사용한다.
```

예상 출력:

```
{
    "UserId": "AIDAxxxxxxxxxxxxx",
    "Account": "471166314777",
    "Arn": "arn:aws:iam::471166314777:user/instructor"
}
```

이 ARN이 이번 실습에서 Trust Policy의 Principal로 들어간다.

---

# 9. 1단계: Role 생성 및 정책 연결

파일명: `01_create_roles.py`

```
import json
import boto3
from botocore.exceptions import ClientError


AWS_PROFILE = "instructor"
AWS_REGION = "ap-northeast-2"

ROLE_NAMES = {
    "viewer": "app-viewer-role",
    "operator": "app-operator-role",
    "admin": "app-admin-role"
}


def create_base_session():
    """
    로컬 AWS Profile을 사용하는 boto3 Session을 생성한다.

    boto3.Session은 AWS API 호출에 사용할 인증 정보와 리전 정보를 담는 객체다.

    profile_name:
        ~/.aws/config 또는 ~/.aws/credentials에 저장된 profile 이름이다.

    region_name:
        AWS API 호출 시 사용할 기본 리전이다.
    """

    return boto3.Session(
        profile_name=AWS_PROFILE,
        region_name=AWS_REGION
    )


def get_current_identity(session):
    """
    현재 boto3 Session이 어떤 AWS Principal로 인증되어 있는지 확인한다.

    sts.get_caller_identity()는 현재 인증 주체의 정보를 반환한다.

    이번 실습에서는 반환값 중 Arn을 Trust Policy의 Principal로 사용한다.
    """

    sts_client = session.client("sts")
    identity = sts_client.get_caller_identity()

    print("=== 현재 인증 주체 ===")
    print(f"Account: {identity['Account']}")
    print(f"Arn    : {identity['Arn']}")
    print(f"UserId : {identity['UserId']}")
    print()

    return identity


def build_trust_policy(principal_arn):
    """
    IAM Role의 Trust Policy를 생성한다.

    Trust Policy는 '누가 이 Role을 AssumeRole 할 수 있는가'를 정의한다.

    principal_arn:
        AssumeRole을 호출할 수 있는 AWS Principal ARN이다.
        이번 실습에서는 현재 로컬 AWS profile의 IAM User ARN을 사용한다.

    Action:
        sts:AssumeRole

    의미:
        지정한 Principal이 이 Role을 맡을 수 있도록 허용한다.
    """

    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "TrustLocalIamUser",
                "Effect": "Allow",
                "Principal": {
                    "AWS": principal_arn
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }

    return json.dumps(trust_policy)


def build_viewer_policy():
    """
    viewer Role에 연결할 Permission Policy를 생성한다.

    viewer는 조회 전용 사용자다.
    EC2와 S3의 조회 계열 작업만 허용한다.
    """

    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowEC2ReadOnly",
                "Effect": "Allow",
                "Action": [
                    "ec2:DescribeInstances",
                    "ec2:DescribeInstanceStatus",
                    "ec2:DescribeTags",
                    "ec2:DescribeSecurityGroups",
                    "ec2:DescribeVolumes"
                ],
                "Resource": "*"
            },
            {
                "Sid": "AllowS3ListOnly",
                "Effect": "Allow",
                "Action": [
                    "s3:ListAllMyBuckets",
                    "s3:ListBucket"
                ],
                "Resource": "*"
            }
        ]
    }

    return json.dumps(policy)


def build_operator_policy():
    """
    operator Role에 연결할 Permission Policy를 생성한다.

    operator는 운영 담당자 역할이다.
    EC2 조회, 시작, 중지를 허용한다.
    S3는 목록 조회만 허용한다.
    """

    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowEC2ReadAndOperate",
                "Effect": "Allow",
                "Action": [
                    "ec2:DescribeInstances",
                    "ec2:DescribeInstanceStatus",
                    "ec2:DescribeTags",
                    "ec2:StartInstances",
                    "ec2:StopInstances"
                ],
                "Resource": "*"
            },
            {
                "Sid": "AllowS3ListOnly",
                "Effect": "Allow",
                "Action": [
                    "s3:ListAllMyBuckets",
                    "s3:ListBucket"
                ],
                "Resource": "*"
            }
        ]
    }

    return json.dumps(policy)


def build_admin_policy():
    """
    admin Role에 연결할 Permission Policy를 생성한다.

    admin은 실습용 관리 역할이다.
    EC2 운영 작업과 S3 객체 업로드를 허용한다.

    실습용 admin이라고 해서 AdministratorAccess를 연결하지 않는다.
    최소 권한 원칙을 유지하면서 viewer/operator보다 넓은 권한을 부여한다.
    """

    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowEC2AdminOperations",
                "Effect": "Allow",
                "Action": [
                    "ec2:Describe*",
                    "ec2:StartInstances",
                    "ec2:StopInstances",
                    "ec2:RebootInstances",
                    "ec2:CreateTags",
                    "ec2:DeleteTags"
                ],
                "Resource": "*"
            },
            {
                "Sid": "AllowS3BasicOperations",
                "Effect": "Allow",
                "Action": [
                    "s3:ListAllMyBuckets",
                    "s3:ListBucket",
                    "s3:GetObject",
                    "s3:PutObject"
                ],
                "Resource": "*"
            }
        ]
    }

    return json.dumps(policy)


def get_permission_policy_by_role_type(role_type):
    """
    role_type에 맞는 Permission Policy 문서를 반환한다.

    role_type 값:
        viewer
        operator
        admin
    """

    if role_type == "viewer":
        return build_viewer_policy()

    if role_type == "operator":
        return build_operator_policy()

    if role_type == "admin":
        return build_admin_policy()

    raise ValueError(f"지원하지 않는 role_type임: {role_type}")


def create_or_update_role(iam_client, role_type, role_name, principal_arn):
    """
    IAM Role을 생성한다.

    Role이 이미 존재하면 새로 만들지 않고 Trust Policy만 업데이트한다.

    create_role():
        IAM Role을 새로 생성한다.

    update_assume_role_policy():
        기존 Role의 Trust Policy를 변경한다.
    """

    trust_policy = build_trust_policy(principal_arn)

    try:
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=trust_policy,
            Description=f"Application {role_type} role for login-based AWS control lab"
        )

        role = response["Role"]

        print(f"[생성 완료] {role_name}")
        print(f"RoleArn: {role['Arn']}")
        print()

        return role

    except ClientError as e:
        error_code = e.response["Error"]["Code"]

        if error_code == "EntityAlreadyExists":
            print(f"[안내] 이미 존재하는 Role임: {role_name}")
            print("[작업] Trust Policy를 현재 Principal 기준으로 업데이트함")

            iam_client.update_assume_role_policy(
                RoleName=role_name,
                PolicyDocument=trust_policy
            )

            role = iam_client.get_role(RoleName=role_name)["Role"]

            print(f"[업데이트 완료] {role_name}")
            print(f"RoleArn: {role['Arn']}")
            print()

            return role

        print(f"[오류] Role 생성 실패: {role_name}")
        print(e)
        raise


def attach_inline_permission_policy(iam_client, role_type, role_name):
    """
    Role에 Inline Permission Policy를 연결한다.

    put_role_policy():
        Role 내부에 Inline Policy를 추가하거나 덮어쓴다.

    이번 실습에서는 Role별 권한 차이를 명확히 보여주기 위해 Inline Policy를 사용한다.
    """

    policy_name = f"{role_type}-permission-policy"
    policy_document = get_permission_policy_by_role_type(role_type)

    iam_client.put_role_policy(
        RoleName=role_name,
        PolicyName=policy_name,
        PolicyDocument=policy_document
    )

    print(f"[정책 연결 완료] {role_name}")
    print(f"PolicyName: {policy_name}")
    print()


def print_role_map(account_id):
    """
    이후 FastAPI에서 사용할 USER_ROLE_MAP 예시를 출력한다.
    """

    print("=== 이후 FastAPI에서 사용할 USER_ROLE_MAP 예시 ===")
    print("USER_ROLE_MAP = {")
    print(f'    "viewer": "arn:aws:iam::{account_id}:role/app-viewer-role",')
    print(f'    "operator": "arn:aws:iam::{account_id}:role/app-operator-role",')
    print(f'    "admin": "arn:aws:iam::{account_id}:role/app-admin-role"')
    print("}")
    print()


def main():
    session = create_base_session()

    identity = get_current_identity(session)
    principal_arn = identity["Arn"]
    account_id = identity["Account"]

    iam_client = session.client("iam")

    for role_type, role_name in ROLE_NAMES.items():
        create_or_update_role(
            iam_client=iam_client,
            role_type=role_type,
            role_name=role_name,
            principal_arn=principal_arn
        )

        attach_inline_permission_policy(
            iam_client=iam_client,
            role_type=role_type,
            role_name=role_name
        )

    print_role_map(account_id)

    print("IAM Role 생성 및 정책 연결 완료")


if __name__ == "__main__":
    main()
```

---

## 9.1 실행

```
python 01_create_roles.py
```

예상 출력:

```
=== 현재 인증 주체 ===
Account: 471166314777
Arn    : arn:aws:iam::471166314777:user/instructor
UserId : AIDAxxxxxxxxxxxxx

[생성 완료] app-viewer-role
RoleArn: arn:aws:iam::471166314777:role/app-viewer-role

[정책 연결 완료] app-viewer-role
PolicyName: viewer-permission-policy

[생성 완료] app-operator-role
RoleArn: arn:aws:iam::471166314777:role/app-operator-role

[정책 연결 완료] app-operator-role
PolicyName: operator-permission-policy

[생성 완료] app-admin-role
RoleArn: arn:aws:iam::471166314777:role/app-admin-role

[정책 연결 완료] app-admin-role
PolicyName: admin-permission-policy

=== 이후 FastAPI에서 사용할 USER_ROLE_MAP 예시 ===
USER_ROLE_MAP = {
    "viewer": "arn:aws:iam::471166314777:role/app-viewer-role",
    "operator": "arn:aws:iam::471166314777:role/app-operator-role",
    "admin": "arn:aws:iam::471166314777:role/app-admin-role"
}

IAM Role 생성 및 정책 연결 완료
```

---

# 10. 2단계: Role별 AssumeRole 테스트

이번 단계에서는 로컬 IAM User가 각 Role을 AssumeRole 한 뒤, Role별 권한 차이를 확인한다.

중요한 점은 다음이다.

```
학생 IAM User는 관리자 권한을 가지고 있다.

하지만 AssumeRole 이후에 생성된 임시 자격 증명은
학생 IAM User의 관리자 권한이 아니라
Assume한 Role의 Permission Policy를 기준으로 동작한다.
```

즉, `app-viewer-role`을 AssumeRole 하면 관리자 IAM User로 시작했더라도 viewer 권한만 가진다.

---

## 10.1 테스트 항목

| 테스트 작업 | viewer | operator | admin |
| --- | --- | --- | --- |
| AssumeRole | 성공 | 성공 | 성공 |
| EC2 인스턴스 조회 | 성공 | 성공 | 성공 |
| S3 버킷 목록 조회 | 성공 | 성공 | 성공 |
| EC2 중지 DryRun | 실패 | 성공 | 성공 |
| S3 객체 업로드 | 실패 | 실패 | 성공 |

---

## 10.2 테스트 코드

파일명: `02_assume_role_test.py`

```
import boto3
from botocore.exceptions import ClientError


AWS_PROFILE = "instructor"
AWS_REGION = "ap-northeast-2"

ROLE_MAP = {
    "viewer": "app-viewer-role",
    "operator": "app-operator-role",
    "admin": "app-admin-role"
}


def create_base_session():
    """
    로컬 IAM User profile을 사용하는 기본 Session을 생성한다.

    이 Session은 sts:AssumeRole을 호출하기 위한 시작 세션이다.
    아직 viewer/operator/admin 권한이 아니다.
    """

    return boto3.Session(
        profile_name=AWS_PROFILE,
        region_name=AWS_REGION
    )


def get_account_id(session):
    """
    현재 profile의 Account ID를 조회한다.

    Role ARN을 자동으로 만들기 위해 사용한다.
    """

    sts_client = session.client("sts")
    identity = sts_client.get_caller_identity()

    print("=== AssumeRole 호출 전 인증 주체 ===")
    print(f"Arn: {identity['Arn']}")
    print()

    return identity["Account"]


def build_role_arn(account_id, role_name):
    """
    Role 이름을 Role ARN으로 변환한다.

    입력:
        account_id = 471166314777
        role_name = app-viewer-role

    출력:
        arn:aws:iam::471166314777:role/app-viewer-role
    """

    return f"arn:aws:iam::{account_id}:role/{role_name}"


def assume_role(base_session, role_arn, role_type):
    """
    지정한 Role을 AssumeRole 한다.

    sts.assume_role()은 대상 Role의 권한을 가진 임시 자격 증명을 반환한다.

    RoleArn:
        AssumeRole 대상 IAM Role ARN이다.

    RoleSessionName:
        Role 세션 이름이다.
        CloudTrail에서 누가 어떤 세션 이름으로 Role을 사용했는지 추적할 때 도움이 된다.
    """

    sts_client = base_session.client("sts")

    response = sts_client.assume_role(
        RoleArn=role_arn,
        RoleSessionName=f"local-{role_type}-test-session"
    )

    credentials = response["Credentials"]

    print(f"[성공] {role_type} Role AssumeRole 완료")
    print(f"RoleArn     : {role_arn}")
    print(f"AccessKeyId : {credentials['AccessKeyId']}")
    print(f"Expiration  : {credentials['Expiration']}")
    print()

    return credentials


def create_assumed_session(credentials):
    """
    AssumeRole로 받은 임시 자격 증명을 사용해 새로운 boto3 Session을 생성한다.

    주의:
        임시 자격 증명은 AccessKeyId, SecretAccessKey, SessionToken이 모두 필요하다.
        SessionToken이 없으면 STS 임시 자격 증명으로 인증할 수 없다.
    """

    return boto3.Session(
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
        region_name=AWS_REGION
    )


def check_assumed_identity(assumed_session):
    """
    AssumeRole 이후 현재 AWS 인증 주체를 확인한다.

    정상적으로 Role을 AssumeRole 했다면 ARN이 다음 형태로 나온다.

    arn:aws:sts::471166314777:assumed-role/app-viewer-role/local-viewer-test-session
    """

    sts_client = assumed_session.client("sts")
    identity = sts_client.get_caller_identity()

    print("=== AssumeRole 이후 인증 주체 ===")
    print(f"Account: {identity['Account']}")
    print(f"Arn    : {identity['Arn']}")
    print(f"UserId : {identity['UserId']}")
    print()


def test_ec2_describe_instances(assumed_session):
    """
    EC2 인스턴스 조회 권한을 테스트한다.

    필요한 권한:
        ec2:DescribeInstances

    viewer, operator, admin 모두 성공해야 한다.
    """

    ec2_client = assumed_session.client("ec2", region_name=AWS_REGION)

    try:
        response = ec2_client.describe_instances()

        instances = []

        for reservation in response["Reservations"]:
            for instance in reservation["Instances"]:
                instances.append({
                    "InstanceId": instance["InstanceId"],
                    "InstanceType": instance["InstanceType"],
                    "State": instance["State"]["Name"]
                })

        print("[성공] EC2 인스턴스 조회 가능")

        if not instances:
            print("조회된 EC2 인스턴스가 없음")
        else:
            for instance in instances:
                print(
                    f"- {instance['InstanceId']} "
                    f"{instance['InstanceType']} "
                    f"{instance['State']}"
                )

        print()

    except ClientError as e:
        print("[실패] EC2 인스턴스 조회 불가")
        print(f"ErrorCode: {e.response['Error']['Code']}")
        print()


def test_s3_list_buckets(assumed_session):
    """
    S3 버킷 목록 조회 권한을 테스트한다.

    필요한 권한:
        s3:ListAllMyBuckets

    viewer, operator, admin 모두 성공해야 한다.
    """

    s3_client = assumed_session.client("s3")

    try:
        response = s3_client.list_buckets()

        buckets = response.get("Buckets", [])

        print("[성공] S3 버킷 목록 조회 가능")

        if not buckets:
            print("조회된 S3 버킷이 없음")
        else:
            for bucket in buckets:
                print(f"- {bucket['Name']}")

        print()

    except ClientError as e:
        print("[실패] S3 버킷 목록 조회 불가")
        print(f"ErrorCode: {e.response['Error']['Code']}")
        print()


def get_first_instance_id(assumed_session):
    """
    테스트용 EC2 인스턴스 ID 하나를 조회한다.

    StopInstances DryRun 테스트에 사용할 인스턴스 ID를 찾는다.
    인스턴스가 없으면 None을 반환한다.
    """

    ec2_client = assumed_session.client("ec2", region_name=AWS_REGION)
    response = ec2_client.describe_instances()

    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            return instance["InstanceId"]

    return None


def test_ec2_stop_dry_run(assumed_session):
    """
    EC2 중지 권한을 DryRun으로 테스트한다.

    필요한 권한:
        ec2:StopInstances

    DryRun=True 의미:
        실제로 인스턴스를 중지하지 않는다.
        권한이 있으면 DryRunOperation 오류가 발생한다.
        권한이 없으면 UnauthorizedOperation 오류가 발생한다.

    결과 해석:
        DryRunOperation:
            권한 있음

        UnauthorizedOperation:
            권한 없음
    """

    instance_id = get_first_instance_id(assumed_session)

    if instance_id is None:
        print("[건너뜀] 테스트할 EC2 인스턴스가 없음")
        print("EC2 StopInstances 권한 테스트를 수행하지 않음")
        print()
        return

    ec2_client = assumed_session.client("ec2", region_name=AWS_REGION)

    try:
        ec2_client.stop_instances(
            InstanceIds=[instance_id],
            DryRun=True
        )

        print("[주의] DryRun=True인데 예외가 발생하지 않았음")
        print("일반적으로 DryRun 권한 확인에서는 예외가 발생함")
        print()

    except ClientError as e:
        error_code = e.response["Error"]["Code"]

        if error_code == "DryRunOperation":
            print("[권한 있음] EC2 StopInstances 가능")
            print(f"테스트 대상 InstanceId: {instance_id}")
            print("DryRun=True이므로 실제 중지는 수행되지 않음")
            print()
            return

        if error_code == "UnauthorizedOperation":
            print("[권한 없음] EC2 StopInstances 불가")
            print(f"테스트 대상 InstanceId: {instance_id}")
            print()
            return

        print("[오류] 예상하지 못한 EC2 StopInstances 테스트 오류")
        print(f"ErrorCode: {error_code}")
        print()


def get_first_bucket_name(assumed_session):
    """
    테스트용 S3 버킷 이름 하나를 조회한다.

    S3 PutObject 권한 테스트에 사용할 버킷을 찾는다.
    버킷이 없으면 None을 반환한다.
    """

    s3_client = assumed_session.client("s3")
    response = s3_client.list_buckets()

    buckets = response.get("Buckets", [])

    if not buckets:
        return None

    return buckets[0]["Name"]


def test_s3_put_object(assumed_session):
    """
    S3 PutObject 권한을 테스트한다.

    S3 PutObject에는 EC2처럼 DryRun 옵션이 없다.
    따라서 실제로 작은 테스트 객체를 업로드한다.

    viewer:
        실패해야 정상

    operator:
        실패해야 정상

    admin:
        성공할 수 있음

    주의:
        이 테스트는 실제 S3 버킷에 객체를 생성한다.
        실습용 버킷을 사용하는 것이 좋다.
    """

    bucket_name = get_first_bucket_name(assumed_session)

    if bucket_name is None:
        print("[건너뜀] 테스트할 S3 버킷이 없음")
        print("S3 PutObject 권한 테스트를 수행하지 않음")
        print()
        return

    s3_client = assumed_session.client("s3")

    object_key = "iam-role-lab/put-object-test.txt"
    body = b"test object for iam role lab"

    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=body
        )

        print("[권한 있음] S3 PutObject 가능")
        print(f"Bucket: {bucket_name}")
        print(f"Key   : {object_key}")
        print()

    except ClientError as e:
        error_code = e.response["Error"]["Code"]

        print("[권한 없음 또는 실패] S3 PutObject 불가")
        print(f"Bucket   : {bucket_name}")
        print(f"ErrorCode: {error_code}")
        print()


def run_test_for_role(role_type, role_name, account_id, base_session):
    """
    특정 Role에 대해 AssumeRole 후 권한 테스트를 수행한다.
    """

    print("=" * 80)
    print(f"권한 테스트 시작: {role_type}")
    print("=" * 80)

    role_arn = build_role_arn(account_id, role_name)

    try:
        credentials = assume_role(
            base_session=base_session,
            role_arn=role_arn,
            role_type=role_type
        )

        assumed_session = create_assumed_session(credentials)

        check_assumed_identity(assumed_session)
        test_ec2_describe_instances(assumed_session)
        test_s3_list_buckets(assumed_session)
        test_ec2_stop_dry_run(assumed_session)
        test_s3_put_object(assumed_session)

    except ClientError as e:
        print(f"[오류] {role_type} Role 테스트 실패")
        print(f"ErrorCode: {e.response['Error']['Code']}")
        print(f"Message  : {e.response['Error']['Message']}")
        print()


def main():
    base_session = create_base_session()
    account_id = get_account_id(base_session)

    for role_type, role_name in ROLE_MAP.items():
        run_test_for_role(
            role_type=role_type,
            role_name=role_name,
            account_id=account_id,
            base_session=base_session
        )


if __name__ == "__main__":
    main()
```

---

## 10.3 실행

```
python 02_assume_role_test.py
```

---

# 11. 예상 결과

## 11.1 viewer Role 결과

```
================================================================================
권한 테스트 시작: viewer
================================================================================
[성공] viewer Role AssumeRole 완료
RoleArn     : arn:aws:iam::471166314777:role/app-viewer-role
AccessKeyId : ASIAxxxxxxxxxxxxxxxx
Expiration  : 2026-04-29 09:30:00+00:00

=== AssumeRole 이후 인증 주체 ===
Account: 471166314777
Arn    : arn:aws:sts::471166314777:assumed-role/app-viewer-role/local-viewer-test-session
UserId : AROAxxxxxxxxxxxx:local-viewer-test-session

[성공] EC2 인스턴스 조회 가능
- i-0123456789abcdef0 t3.micro running

[성공] S3 버킷 목록 조회 가능
- my-lab-bucket

[권한 없음] EC2 StopInstances 불가
테스트 대상 InstanceId: i-0123456789abcdef0

[권한 없음 또는 실패] S3 PutObject 불가
Bucket   : my-lab-bucket
ErrorCode: AccessDenied
```

해석:

```
viewer는 조회 전용 Role이다.
EC2 조회와 S3 목록 조회는 가능하다.
EC2 중지와 S3 업로드는 실패해야 정상이다.
```

---

## 11.2 operator Role 결과

```
================================================================================
권한 테스트 시작: operator
================================================================================
[성공] operator Role AssumeRole 완료
RoleArn     : arn:aws:iam::471166314777:role/app-operator-role
AccessKeyId : ASIAxxxxxxxxxxxxxxxx
Expiration  : 2026-04-29 09:30:00+00:00

=== AssumeRole 이후 인증 주체 ===
Account: 471166314777
Arn    : arn:aws:sts::471166314777:assumed-role/app-operator-role/local-operator-test-session
UserId : AROAxxxxxxxxxxxx:local-operator-test-session

[성공] EC2 인스턴스 조회 가능
- i-0123456789abcdef0 t3.micro running

[성공] S3 버킷 목록 조회 가능
- my-lab-bucket

[권한 있음] EC2 StopInstances 가능
테스트 대상 InstanceId: i-0123456789abcdef0
DryRun=True이므로 실제 중지는 수행되지 않음

[권한 없음 또는 실패] S3 PutObject 불가
Bucket   : my-lab-bucket
ErrorCode: AccessDenied
```

해석:

```
operator는 EC2 운영 권한을 가진다.
EC2 StopInstances DryRun 테스트는 성공해야 한다.
하지만 S3 PutObject 권한은 없으므로 업로드는 실패해야 정상이다.
```

---

## 11.3 admin Role 결과

```
================================================================================
권한 테스트 시작: admin
================================================================================
[성공] admin Role AssumeRole 완료
RoleArn     : arn:aws:iam::471166314777:role/app-admin-role
AccessKeyId : ASIAxxxxxxxxxxxxxxxx
Expiration  : 2026-04-29 09:30:00+00:00

=== AssumeRole 이후 인증 주체 ===
Account: 471166314777
Arn    : arn:aws:sts::471166314777:assumed-role/app-admin-role/local-admin-test-session
UserId : AROAxxxxxxxxxxxx:local-admin-test-session

[성공] EC2 인스턴스 조회 가능
- i-0123456789abcdef0 t3.micro running

[성공] S3 버킷 목록 조회 가능
- my-lab-bucket

[권한 있음] EC2 StopInstances 가능
테스트 대상 InstanceId: i-0123456789abcdef0
DryRun=True이므로 실제 중지는 수행되지 않음

[권한 있음] S3 PutObject 가능
Bucket: my-lab-bucket
Key   : iam-role-lab/put-object-test.txt
```

해석:

```
admin은 EC2 운영 권한과 S3 PutObject 권한을 가진다.
따라서 EC2 StopInstances DryRun과 S3 PutObject가 가능하다.
```

---

# 12. 결과 정리

| 작업 | viewer | operator | admin |
| --- | --- | --- | --- |
| AssumeRole | 가능 | 가능 | 가능 |
| EC2 인스턴스 조회 | 가능 | 가능 | 가능 |
| S3 버킷 목록 조회 | 가능 | 가능 | 가능 |
| EC2 중지 DryRun | 불가 | 가능 | 가능 |
| S3 객체 업로드 | 불가 | 불가 | 가능 |

---

# 13. 중요한 해석: IAM User가 관리자 권한이어도 Role 권한으로 제한됨

이번 실습에서 학생 IAM User는 관리자 권한을 가지고 있다.

그런데도 `app-viewer-role`을 AssumeRole한 뒤에는 `ec2:StopInstances`가 실패한다.

이유는 다음과 같다.

```
AssumeRole 이전:
  IAM User instructor 권한으로 동작
  관리자 권한 보유

AssumeRole 이후:
  app-viewer-role 권한으로 동작
  viewer Role의 Permission Policy만 적용
```

즉, AssumeRole 이후에는 원래 IAM User의 관리자 권한을 그대로 사용하는 것이 아니다.

이 점이 이번 실습의 핵심이다.

---

# 14. 이후 FastAPI 로그인 실습과 연결

이번 실습에서 생성한 Role은 이후 FastAPI 코드에서 그대로 사용할 수 있다.

## 14.1 USER\_ROLE\_MAP 예시

```
USER_ROLE_MAP = {
    "viewer": "arn:aws:iam::471166314777:role/app-viewer-role",
    "operator": "arn:aws:iam::471166314777:role/app-operator-role",
    "admin": "arn:aws:iam::471166314777:role/app-admin-role"
}
```

이 매핑은 다음 의미를 가진다.

```
프론트엔드 로그인 사용자 role 값
  ↓
FastAPI 내부 USER_ROLE_MAP
  ↓
해당 IAM Role ARN 선택
  ↓
sts:AssumeRole
```

예를 들어 로그인 사용자가 viewer라면:

```
current_user = {
    "username": "kim",
    "role": "viewer"
}

role_arn = USER_ROLE_MAP[current_user["role"]]
```

선택되는 Role은 다음이다.

```
arn:aws:iam::471166314777:role/app-viewer-role
```

---

## 14.2 로컬 실행과 EC2 실행의 Principal 차이

이번 실습에서는 로컬에서 실행하므로 Trust Policy Principal이 IAM User다.

```
arn:aws:iam::471166314777:user/instructor
```

하지만 이후 FastAPI를 EC2에서 실행하면 AssumeRole을 호출하는 주체가 바뀐다.

EC2에서 FastAPI가 실행될 경우 구조는 다음과 같다.

```
EC2 Instance
  ↓
Instance Profile Role
  ↓
fastapi-backend-base-role
  ↓ sts:AssumeRole
app-viewer-role / app-operator-role / app-admin-role
```

이때 대상 Role의 Trust Policy Principal은 아래처럼 바꿔야 한다.

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "TrustFastAPIBackendBaseRole",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::471166314777:role/fastapi-backend-base-role"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

로컬과 EC2를 둘 다 허용하려면 배열로 설정할 수 있다.

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "TrustLocalUserAndBackendRole",
      "Effect": "Allow",
      "Principal": {
        "AWS": [
          "arn:aws:iam::471166314777:user/instructor",
          "arn:aws:iam::471166314777:role/fastapi-backend-base-role"
        ]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

---

# 15. 실습 리소스 정리

이 Role들은 이후 프론트엔드/FastAPI 실습에서 계속 사용할 예정이라면 삭제하지 않는다.

실습만 하고 정리하려면 아래 코드를 사용한다.

파일명: `03_cleanup_roles.py`

```
import boto3
from botocore.exceptions import ClientError


AWS_PROFILE = "instructor"
AWS_REGION = "ap-northeast-2"

ROLE_POLICY_MAP = {
    "app-viewer-role": "viewer-permission-policy",
    "app-operator-role": "operator-permission-policy",
    "app-admin-role": "admin-permission-policy"
}


def create_base_session():
    return boto3.Session(
        profile_name=AWS_PROFILE,
        region_name=AWS_REGION
    )


def delete_inline_policy(iam_client, role_name, policy_name):
    """
    Role에 연결된 Inline Policy를 삭제한다.

    IAM Role을 삭제하기 전에 Inline Policy를 먼저 삭제한다.
    """

    try:
        iam_client.delete_role_policy(
            RoleName=role_name,
            PolicyName=policy_name
        )

        print(f"[삭제 완료] Inline Policy 삭제: {role_name} / {policy_name}")

    except ClientError as e:
        error_code = e.response["Error"]["Code"]

        if error_code == "NoSuchEntity":
            print(f"[안내] Inline Policy가 없음: {role_name} / {policy_name}")
            return

        print(f"[오류] Inline Policy 삭제 실패: {role_name}")
        print(e)
        raise


def delete_role(iam_client, role_name):
    """
    IAM Role을 삭제한다.
    """

    try:
        iam_client.delete_role(RoleName=role_name)
        print(f"[삭제 완료] IAM Role 삭제: {role_name}")

    except ClientError as e:
        error_code = e.response["Error"]["Code"]

        if error_code == "NoSuchEntity":
            print(f"[안내] Role이 없음: {role_name}")
            return

        print(f"[오류] Role 삭제 실패: {role_name}")
        print(e)
        raise


def main():
    session = create_base_session()
    iam_client = session.client("iam")

    for role_name, policy_name in ROLE_POLICY_MAP.items():
        delete_inline_policy(iam_client, role_name, policy_name)
        delete_role(iam_client, role_name)

    print("실습 Role 정리 완료")


if __name__ == "__main__":
    main()
```

실행:

```
python 03_cleanup_roles.py
```

---

# 16. 수업 진행 순서 추천

```
1. 현재 학생 IAM User가 관리자 권한을 가지고 있음을 설명한다.
2. 하지만 일반 IAM User는 sts:AssumeRole 권한이 별도로 필요함을 설명한다.
3. Trust Policy와 Permission Policy 차이를 설명한다.
4. aws sts get-caller-identity로 현재 Principal을 확인한다.
5. boto3로 viewer/operator/admin Role을 생성한다.
6. 각 Role의 Trust Policy에 현재 IAM User ARN을 넣는다.
7. 각 Role에 서로 다른 Permission Policy를 연결한다.
8. Role별로 AssumeRole 한다.
9. AssumeRole 이후 get_caller_identity 결과를 확인한다.
10. viewer/operator/admin 권한 차이를 테스트한다.
11. 이후 FastAPI USER_ROLE_MAP 구조와 연결한다.
12. EC2 배포 시 Principal이 IAM User에서 EC2 Role로 바뀐다는 점을 설명한다.
```

---

# 17. 학생 과제

## 과제 1. Role별 권한 차이 확인

다음 Role을 생성하고 권한 테스트 결과를 제출한다.

```
app-viewer-role
app-operator-role
app-admin-role
```

제출물:

```
1. 01_create_roles.py
2. 02_assume_role_test.py
3. 실행 결과 캡처
4. viewer/operator/admin 권한 차이 표
5. Trust Policy와 Permission Policy 차이 설명
```

---

## 과제 2. 일반 IAM User라면 필요한 정책 설명

현재 실습 환경에서는 학생 IAM User가 관리자 권한을 가지고 있다.

하지만 일반 IAM User라면 어떤 정책이 추가로 필요한지 설명한다.

포함해야 할 내용:

```
1. 일반 IAM User에게 sts:AssumeRole 권한이 필요한 이유
2. 대상 Role의 Trust Policy가 필요한 이유
3. 두 조건 중 하나라도 빠지면 AssumeRole이 실패하는 이유
4. Resource를 "*"로 열지 않고 특정 Role ARN으로 제한해야 하는 이유
```

예시 정책:

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowAssumeApplicationRoles",
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": [
        "arn:aws:iam::471166314777:role/app-viewer-role",
        "arn:aws:iam::471166314777:role/app-operator-role",
        "arn:aws:iam::471166314777:role/app-admin-role"
      ]
    }
  ]
}
```

---

# 18. 핵심 정리

이번 실습의 핵심은 다음이다.

```
1. 학생 IAM User는 현재 관리자 권한을 가지고 있으므로 AssumeRole 호출 권한이 이미 있음
2. 하지만 일반 IAM User라면 sts:AssumeRole 권한을 별도로 부여해야 함
3. Role의 Trust Policy에는 AssumeRole을 실제 호출하는 AWS Principal을 넣음
4. 로컬 실행에서는 IAM User가 Principal이 됨
5. EC2 실행에서는 EC2 Instance Profile Role이 Principal이 됨
6. viewer/operator/admin Role은 서로 다른 Permission Policy를 가짐
7. AssumeRole 이후에는 원래 IAM User의 권한이 아니라 Role 권한으로 동작함
8. 이 구조를 이후 FastAPI 로그인 사용자별 Role 매핑 구조로 확장함
```

최종적으로 이번 실습은 다음 질문에 답하기 위한 준비 과정이다.

```
로그인 사용자가 viewer이면 왜 조회만 가능해야 하는가?
로그인 사용자가 operator이면 왜 EC2 시작/중지는 가능하지만 S3 업로드는 불가능해야 하는가?
로그인 사용자가 admin이면 왜 더 넓은 운영 작업이 가능해야 하는가?
```

그리고 그 답은 다음 구조에 있다.

```
로그인 사용자 권한
  ↓
FastAPI USER_ROLE_MAP
  ↓
IAM Role 선택
  ↓
sts:AssumeRole
  ↓
Role Permission Policy 기준으로 AWS API 호출
```