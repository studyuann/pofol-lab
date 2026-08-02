---
title: "5장 AWS 운영 보안 점검 자동화"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "클라우드 자동화를 위한 파이썬 프로그래밍"]
is_public: true
draft: false
---

# 5장. AWS 운영/보안 점검 자동화

## 장 개요

이 장에서는 `boto3`를 사용해 IAM 사용자 목록과 정책 정보를 조회하고, 운영 점검에 활용할 수 있는 기본 자동화 코드를 작성한다.

IAM은 AWS에서 인증과 권한을 다루는 핵심 서비스이므로, 단순한 목록 조회도 운영 확인과 보안 점검의 기초가 된다.

또한 조회 결과를 보기 좋게 정리하고, 필요한 항목만 추출해 출력하는 방법도 함께 다룬다.

이 장의 목표는 **Python 코드로 IAM 정보를 조회하고 점검용 출력으로 정리하는 흐름**을 익히는 것이다.

---

## 학습 목표

* IAM의 역할을 설명할 수 있다.

* `boto3`로 IAM 사용자 목록을 조회할 수 있다.

* `boto3`로 정책 목록을 조회할 수 있다.

* 조회 결과에서 필요한 항목만 추출해 출력할 수 있다.

* 운영 점검 관점에서 어떤 IAM 정보를 확인할 수 있는지 설명할 수 있다.

* 함수 분리와 예외 처리를 통해 IAM 조회 코드를 정리할 수 있다.

---

## 주요 키워드

* IAM

* User

* Policy

* list\_users

* list\_policies

* 조회 자동화

* 운영 점검

* boto3

* 권한

* 계정 정보

---

# 7.1 IAM 기본 이해

## 1. IAM이란 무엇인가

IAM은 AWS에서 **인증(Authentication)** 과 **권한 부여(Authorization)** 를 담당하는 서비스이다.

쉽게 말하면 “누가 AWS를 사용할 수 있는가”와 “무엇을 할 수 있는가”를 관리하는 영역이다.

IAM에서 자주 보는 대상은 다음과 같다.

* 사용자(User)

* 그룹(Group)

* 역할(Role)

* 정책(Policy)

이번 장에서는 이 중에서도 **사용자와 정책 조회**를 중심으로 다룬다.

---

## 2. 왜 IAM 조회가 중요한가

운영 환경에서는 리소스만 중요한 것이 아니다.

어떤 계정이 존재하는지, 어떤 정책이 있는지, 어떤 이름 규칙으로 관리되는지 확인하는 것도 매우 중요하다.

예를 들면 다음과 같은 상황에서 IAM 조회가 필요하다.

* 현재 계정에 어떤 사용자가 있는지 확인

* 이름 규칙이 맞게 적용되었는지 확인

* 특정 정책이 존재하는지 확인

* 운영 계정과 실습 계정을 구분해 확인

* 보고용 목록을 정리

즉, IAM 조회 자동화는 **운영 점검의 기초 단계**라고 볼 수 있다.

---

# 7.2 IAM client 생성

## 1. IAM client 기본 구조

IAM도 `boto3` client로 접근할 수 있다.

```
import boto3

session = boto3.Session(profile_name="lab")
iam = session.client("iam")

print(iam)
```

IAM은 글로벌 서비스 성격이 강하므로 EC2, S3처럼 항상 `region_name`을 강조하지는 않지만, 세션 구조 자체는 동일하다.

---

## 2. 함수로 분리한 기본 구조

```
import boto3

def get_iam_client():
    session = boto3.Session(profile_name="lab")
    return session.client("iam")

iam = get_iam_client()
print(iam)
```

이 방식은 이후 사용자 조회, 정책 조회에서도 그대로 사용된다.

---

## 실습 1. IAM client 생성

파일명: `iam_client_test.py`

```
import boto3

def get_iam_client():
    session = boto3.Session(profile_name="lab")
    return session.client("iam")

iam = get_iam_client()

print("iam client created")
print(iam)
```

* IAM도 다른 AWS 서비스처럼 `boto3` client로 다룰 수 있음을 확인한다.

* 세션 생성 구조가 EC2, S3와 동일하다는 점을 확인한다.

---

# 7.3 IAM 사용자 목록 조회

## 1. 사용자 목록 조회 API

IAM 사용자 목록을 조회할 때는 `list_users()`를 사용한다.

기본 예제는 다음과 같다.

```
import boto3

session = boto3.Session(profile_name="lab")
iam = session.client("iam")

response = iam.list_users()
print(response)
```

이 응답은 보통 `Users` 리스트를 포함한다.

즉, 구조는 대략 다음과 같다.

```
{
    "Users": [
        {
            "UserName": "alice",
            "UserId": "...",
            "Arn": "...",
            "CreateDate": "..."
        },
        ...
    ]
}
```

따라서 `Users`를 반복해서 필요한 값을 출력하면 된다.

---

## 2. 사용자 이름만 출력

```
import boto3

session = boto3.Session(profile_name="lab")
iam = session.client("iam")

response = iam.list_users()

for user in response["Users"]:
    print(user["UserName"])
```

---

## 3. 사용자 이름과 ARN 출력

```
import boto3

session = boto3.Session(profile_name="lab")
iam = session.client("iam")

response = iam.list_users()

for user in response["Users"]:
    print(
        f"user={user['UserName']}, "
        f"arn={user['Arn']}"
    )
```

이 방식은 사용자 이름만 보는 것보다 더 많은 정보를 제공한다.

---

## 실습 2. IAM 사용자 목록 출력

파일명: `iam_list_users.py`

```
import boto3

def get_iam_client():
    session = boto3.Session(profile_name="lab")
    return session.client("iam")

iam = get_iam_client()
response = iam.list_users()

print("IAM 사용자 목록")
for user in response["Users"]:
    print(
        f"user={user['UserName']}, "
        f"arn={user['Arn']}"
    )
```

* `Users`가 리스트라는 점을 확인한다.

* 각 사용자 항목이 딕셔너리라는 점을 확인한다.

* `UserName`, `Arn` 같은 키를 직접 읽는 방식을 익힌다.

---

# 7.4 IAM 사용자 생성일 확인

운영 점검 관점에서는 단순히 사용자 이름만 보는 것이 아니라, 언제 생성되었는지도 함께 보고 싶을 수 있다.

## 1. 생성일 포함 출력

```
import boto3

def get_iam_client():
    session = boto3.Session(profile_name="lab")
    return session.client("iam")

iam = get_iam_client()
response = iam.list_users()

for user in response["Users"]:
    print(
        f"user={user['UserName']}, "
        f"created={user['CreateDate']}"
    )
```

이 출력은 계정이 언제 생성되었는지 확인하는 데 도움이 된다.

* 조회 결과에서 필요한 필드를 하나씩 확장해 출력할 수 있음을 이해한다.

* 운영 점검 출력은 “전체 응답을 그대로 찍는 것”이 아니라 “필요한 정보만 정리해 보여주는 것”임을 이해한다.

---

# 7.5 IAM 정책 목록 조회

## 1. 정책 조회 API

IAM 정책 목록을 조회할 때는 `list_policies()`를 사용할 수 있다.

기본 예제는 다음과 같다.

```
import boto3

session = boto3.Session(profile_name="lab")
iam = session.client("iam")

response = iam.list_policies()
print(response)
```

응답에는 보통 `Policies` 리스트가 포함된다.

각 정책 항목에는 `PolicyName`, `Arn`, `DefaultVersionId` 같은 정보가 들어 있다.

---

## 2. 정책 이름만 출력

```
import boto3

session = boto3.Session(profile_name="lab")
iam = session.client("iam")

response = iam.list_policies()

for policy in response["Policies"]:
    print(policy["PolicyName"])
```

---

## 3. 정책 이름과 ARN 출력

```
import boto3

session = boto3.Session(profile_name="lab")
iam = session.client("iam")

response = iam.list_policies()

for policy in response["Policies"]:
    print(
        f"policy={policy['PolicyName']}, "
        f"arn={policy['Arn']}"
    )
```

---

## 실습 4. IAM 정책 목록 조회

파일명: `iam_list_policies.py`

```
import boto3

def get_iam_client():
    session = boto3.Session(profile_name="lab")
    return session.client("iam")

iam = get_iam_client()
response = iam.list_policies()

print("IAM 정책 목록")
for policy in response["Policies"]:
    print(
        f"policy={policy['PolicyName']}, "
        f"arn={policy['Arn']}"
    )
```

### 학습 포인트

* `Policies` 리스트 구조를 확인한다.

* 정책 이름과 ARN을 읽는 패턴을 익힌다.

* 사용자 조회와 정책 조회가 매우 비슷한 구조임을 이해한다.

---

# 7.6 AWS 관리형 정책과 사용자 정의 정책 구분

정책 목록은 매우 많을 수 있으며, AWS 관리형 정책과 사용자 정의 정책이 함께 섞여 있을 수 있다.

이때 운영 점검에서는 특정 유형만 보고 싶을 수 있다.

정책 항목에는 보통 `Arn`이 있으므로, 이름과 ARN을 기준으로 구분에 참고할 수 있다.

예를 들어 아래처럼 출력하면서 눈으로 구분할 수 있다.

```
import boto3

def get_iam_client():
    session = boto3.Session(profile_name="lab")
    return session.client("iam")

iam = get_iam_client()
response = iam.list_policies()

for policy in response["Policies"]:
    print(
        f"name={policy['PolicyName']}, "
        f"arn={policy['Arn']}"
    )
```

이후에는 특정 문자열 포함 여부를 기준으로 필터링하는 형태로 확장할 수 있다.

---

## 실습 5. 정책 이름 필터링 기초

파일명: `iam_policy_filter.py`

```
import boto3

def get_iam_client():
    session = boto3.Session(profile_name="lab")
    return session.client("iam")

iam = get_iam_client()
response = iam.list_policies()

print("ReadOnly가 포함된 정책")
for policy in response["Policies"]:
    if "ReadOnly" in policy["PolicyName"]:
        print(
            f"name={policy['PolicyName']}, "
            f"arn={policy['Arn']}"
        )
```

### 학습 포인트

* 문자열 포함 여부를 활용한 간단한 필터링을 익힌다.

* 운영 점검에서는 전체 출력보다 필요한 항목만 골라 보는 방식이 유용함을 이해한다.

---

# 7.7 운영 점검 자동화 관점에서의 IAM 조회

## 1. 운영 점검 자동화란 무엇인가

운영 점검 자동화는 리소스를 생성하거나 삭제하는 것이 아니라, **현재 상태를 확인하고 보기 좋게 정리하는 자동화**에 가깝다.

IAM 조회를 운영 점검 관점에서 보면 다음과 같은 질문을 던질 수 있다.

* 현재 어떤 사용자가 존재하는가

* 이름 규칙이 일정한가

* 특정 정책이 존재하는가

* 정책 목록을 정리해 보고할 수 있는가

* 실습용 계정만 따로 보거나 특정 패턴만 볼 수 있는가

즉, 운영 점검 자동화는 “수정”보다 “확인과 정리”에 더 가깝다.

---

## 2. 사용자 이름 규칙 점검 예제

예를 들어 사용자 이름에 `lab-` 접두사가 붙는 계정만 보고 싶다고 하자.

```
import boto3

def get_iam_client():
    session = boto3.Session(profile_name="lab")
    return session.client("iam")

iam = get_iam_client()
response = iam.list_users()

print("lab- 접두사 사용자")
for user in response["Users"]:
    if user["UserName"].startswith("lab-"):
        print(
            f"user={user['UserName']}, "
            f"arn={user['Arn']}"
        )
```

이 구조는 운영 기준 이름 규칙 점검에 응용할 수 있다.

---

## 실습 6. 사용자 이름 규칙 점검

파일명: `iam_user_prefix_check.py`

```
import boto3

def get_iam_client():
    session = boto3.Session(profile_name="lab")
    return session.client("iam")

iam = get_iam_client()
response = iam.list_users()

print("lab- 접두사 사용자")
for user in response["Users"]:
    if user["UserName"].startswith("lab-"):
        print(
            f"user={user['UserName']}, "
            f"arn={user['Arn']}"
        )
```

### 학습 포인트

* `startswith()`를 사용한 문자열 패턴 점검을 익힌다.

* 운영 점검은 복잡한 분석보다 이런 작은 규칙 확인부터 시작할 수 있음을 이해한다.

---

# 7.8 함수로 구조 정리하기

조회 코드도 점점 길어질 수 있으므로, 기능별로 함수 분리를 하는 것이 좋다.

예를 들면 아래처럼 나눌 수 있다.

* IAM client 생성 함수

* 사용자 목록 조회 함수

* 정책 목록 조회 함수

* 출력 전용 함수

---

## 1. 함수 분리 예제

```
import boto3

def get_iam_client():
    session = boto3.Session(profile_name="lab")
    return session.client("iam")

def list_users():
    iam = get_iam_client()
    response = iam.list_users()

    for user in response["Users"]:
        print(
            f"user={user['UserName']}, "
            f"arn={user['Arn']}"
        )

list_users()
```

이 구조를 만들면 이후 다른 출력 형식이나 필터 조건을 추가하기도 쉬워진다.

---

## 실습 7. 함수 분리 버전 작성

파일명: `iam_users_func.py`

```
import boto3

def get_iam_client():
    session = boto3.Session(profile_name="lab")
    return session.client("iam")

def list_users():
    iam = get_iam_client()
    response = iam.list_users()

    print("IAM 사용자 목록")
    for user in response["Users"]:
        print(
            f"user={user['UserName']}, "
            f"arn={user['Arn']}"
        )

list_users()
```

### 학습 포인트

* 클라이언트 생성과 실제 조회 기능을 분리한다.

* 코드 읽기가 더 쉬워지는지 확인한다.

---

# 7.9 예외 처리 추가하기

IAM 조회도 인증, 권한, 프로필 문제로 오류가 날 수 있으므로 기본적인 예외 처리를 넣는 것이 좋다.

```
import boto3

def get_iam_client():
    session = boto3.Session(profile_name="lab")
    return session.client("iam")

def list_users():
    iam = get_iam_client()
    response = iam.list_users()

    for user in response["Users"]:
        print(
            f"user={user['UserName']}, "
            f"arn={user['Arn']}"
        )

try:
    list_users()
except Exception as e:
    print("IAM 사용자 조회 실패")
    print(f"오류 내용: {e}")
```

---

## 실습 8. 예외 처리 포함 사용자 조회

파일명: `iam_users_safe.py`

```
import boto3

def get_iam_client():
    session = boto3.Session(profile_name="lab")
    return session.client("iam")

def list_users():
    iam = get_iam_client()
    response = iam.list_users()

    print("IAM 사용자 목록")
    for user in response["Users"]:
        print(
            f"user={user['UserName']}, "
            f"arn={user['Arn']}"
        )

try:
    list_users()
except Exception as e:
    print("IAM 사용자 조회 실패")
    print(f"오류 내용: {e}")
```

### 학습 포인트

* 조회 코드에도 기본적인 예외 처리가 필요함을 이해한다.

* 이후 EC2, S3, Bedrock 코드와 동일한 구조를 유지하는 것이 좋음을 확인한다.

---

# 7.10 생성형 AI로 IAM 조회 코드 요청하기

## 1. 요청 예시

```
Python boto3 코드를 작성해줘.
AWS CLI 프로필 기반 인증을 사용하고 profile_name은 lab으로 해줘.
IAM 사용자 목록을 조회해서 사용자 이름과 ARN을 출력해줘.
예외 처리도 포함해줘.
```

---

## 3. 향상된 요청 예시

```
Python boto3 코드를 작성해줘.
AWS CLI 프로필 기반 인증을 사용하고 profile_name은 lab으로 해줘.
IAM client 생성 함수와 사용자 목록 조회 함수를 분리해줘.
IAM 사용자 목록을 조회해서 UserName, Arn, CreateDate를 출력해줘.
출력은 f-string으로 정리하고, try/except 예외 처리도 포함해줘.
```

---

## 4. 정책 조회 코드 요청 예시

```
Python boto3 코드를 작성해줘.
AWS CLI 프로필 기반 인증을 사용하고 profile_name은 lab으로 해줘.
IAM 정책 목록을 조회해서 PolicyName과 Arn을 출력해줘.
ReadOnly가 포함된 정책만 출력하는 예제도 포함해줘.
함수로 분리하고 예외 처리도 넣어줘.
```

---

# 7.11 자동화 스타일 종합 예제

이제 이 장의 흐름을 모은 종합 예제를 보자.

파일명: `iam_summary.py`

```
import boto3

def get_iam_client():
    session = boto3.Session(profile_name="lab")
    return session.client("iam")

def list_users():
    iam = get_iam_client()
    response = iam.list_users()

    print("IAM 사용자 목록")
    for user in response["Users"]:
        print(
            f"user={user['UserName']}, "
            f"arn={user['Arn']}, "
            f"created={user['CreateDate']}"
        )

def list_readonly_policies():
    iam = get_iam_client()
    response = iam.list_policies()

    print("ReadOnly 정책 목록")
    for policy in response["Policies"]:
        if "ReadOnly" in policy["PolicyName"]:
            print(
                f"name={policy['PolicyName']}, "
                f"arn={policy['Arn']}"
            )

try:
    list_users()
    list_readonly_policies()

except Exception as e:
    print("IAM 조회 자동화 실패")
    print(f"오류 내용: {e}")
```

### 학습 포인트

이 예제에는 다음 흐름이 들어 있다.

* 프로필 기반 IAM client 생성

* 사용자 목록 조회

* 정책 목록 조회

* 문자열 조건 기반 필터링

* 출력 형식 정리

* 함수 분리

* 예외 처리

즉, 이 코드는 조회 중심 운영 점검 자동화의 기본형이라고 볼 수 있다.

---

# 7.12 정리

* IAM은 AWS에서 인증과 권한을 다루는 핵심 서비스이다.

* `boto3`로 IAM client를 생성해 사용자와 정책 정보를 조회할 수 있다.

* `list_users()` 응답에는 `Users` 리스트가 포함되며, `UserName`, `Arn`, `CreateDate` 같은 정보를 볼 수 있다.

* `list_policies()` 응답에는 `Policies` 리스트가 포함되며, `PolicyName`, `Arn` 같은 정보를 볼 수 있다.

* 운영 점검 자동화는 리소스를 바꾸는 것이 아니라 현재 상태를 확인하고 정리하는 데 초점이 있다.

* 사용자 이름 규칙이나 정책 이름 패턴처럼 간단한 조건 필터링도 운영 점검에 유용하다.

* 함수 분리와 예외 처리를 통해 IAM 조회 코드를 더 읽기 좋고 안정적으로 만들 수 있다.

* 생성형 AI에게 요청할 때는 인증 방식, 조회 대상, 출력할 필드, 필터링 조건, 예외 처리 요구를 함께 적는 것이 좋다.

 [[boto3로 로그인 사용자 권한별 IAM Role 생성 및 AssumeRole 권한 차이|boto3로 로그인 사용자 권한별 IAM Role 생성 및 AssumeRole 권한 차이 확인]]  [[프론트엔드, FastAPI, MariaDB, boto3를 이용한 로그인 기반 AWS 운영|프론트엔드, FastAPI, MariaDB, boto3를 이용한 로그인 기반 AWS 운영 자동화]]