---
title: "3장 boto3와 AWS API 자동화 입문"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "클라우드 자동화를 위한 파이썬 프로그래밍"]
is_public: true
draft: false
---

# 3장. boto3와 AWS API 자동화 입문

## 장 개요

이 장에서는 Python에서 AWS 서비스를 제어할 때 사용하는 AWS SDK인 **boto3**의 기본 구조를 학습한다.

AWS CLI 프로필 기반 인증과 `boto3.Session()` 사용 방식, `client`와 `resource`의 개념, AWS API 응답 구조를 읽는 방법을 익히고, 생성형 AI를 활용해 기본적인 boto3 코드 초안을 만드는 실습까지 진행한다.

이 장의 목표는 단순히 boto3 문법을 외우는 것이 아니라, **AWS 콘솔에서 하던 작업을 Python 코드로 어떻게 옮기는지 이해하는 것**이다.

---

## 학습 목표

이 장을 마치면 다음을 할 수 있어야 한다.

* boto3가 무엇인지 설명할 수 있다.

* AWS SDK와 AWS API의 관계를 설명할 수 있다.

* `boto3.Session()`을 사용해 프로필 기반 세션을 만들 수 있다.

* `client` 방식과 `resource` 방식의 차이를 설명할 수 있다.

* boto3로 EC2, S3 같은 AWS 서비스 클라이언트를 생성할 수 있다.

* AWS API 응답이 딕셔너리와 리스트 구조로 반환된다는 점을 이해할 수 있다.

* 응답 구조에서 필요한 값을 추출할 수 있다.

* 생성형 AI에게 boto3 코드 생성을 요청하고, 결과를 검토할 수 있다.

---

# 4.1 AWS SDK와 boto3 이해

## 1. SDK와 API란 무엇인가

AWS는 다양한 클라우드 서비스를 제공한다.

예를 들면 다음과 같은 서비스가 있다.

* EC2

* S3

* IAM

* CloudWatch

* Bedrock

이 서비스들은 콘솔 화면에서 클릭으로도 사용할 수 있지만, 내부적으로는 모두 **API(Application Programming Interface)** 를 통해 동작한다.

즉, 콘솔에서 버튼을 눌러 인스턴스를 조회하거나 버킷 목록을 보는 것도 결국은 AWS API를 호출하는 것이다.

이 API를 Python 코드에서 편하게 사용할 수 있도록 만들어 놓은 라이브러리가 **AWS SDK**이다.

Python에서 AWS SDK 역할을 하는 대표 라이브러리가 바로 **boto3**이다.

---

## 2. boto3란 무엇인가

boto3는 Python에서 AWS 서비스를 제어하기 위한 공식 SDK이다.

즉, Python 코드로 AWS API를 호출할 수 있게 해주는 도구이다.

예를 들어 boto3를 사용하면 다음과 같은 작업을 할 수 있다.

* EC2 인스턴스 목록 조회

* S3 버킷 목록 조회

* 객체 업로드 및 다운로드

* IAM 사용자 조회

* CloudWatch 지표 조회

* Bedrock 모델 호출

즉, AWS 콘솔에서 하던 작업을 Python 코드로 자동화할 수 있게 만든다.

---

## 3. 왜 boto3를 배우는가

콘솔 사용과 boto3 사용은 완전히 같은 경험은 아니다.

콘솔은 사람이 직접 클릭하고 확인하는 방식이고,

boto3는 코드를 통해 **반복 가능하고 재사용 가능한 자동화 흐름**을 만드는 방식이다.

예를 들어 콘솔에서는 여러 인스턴스를 하나씩 확인해야 할 수도 있지만,

boto3를 사용하면 한 번의 API 호출과 반복문으로 전체 상태를 바로 확인할 수 있다.

즉, boto3는 AWS 서비스를 “사용하는 것”에서 나아가 **자동화 가능한 코드로 바꾸는 단계**라고 볼 수 있다.

---

# 4.2 boto3 설치와 기본 준비

## 1. boto3 설치 - 이미 1장에서 설치 했음.

가상환경이 활성화된 상태에서 다음 명령으로 설치한다.

```
pip install boto3[crt]
```

설치 여부는 아래처럼 확인할 수 있다.

```
pip show boto3
```

---

## 2. boto3 import

Python 코드에서는 아래처럼 불러온다.

```
import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError, ProfileNotFound
```

이제 Python 코드 안에서 AWS SDK를 사용할 수 있다.

---

# 4.3 Session과 프로필 기반 인증

## 1. 왜 Session을 사용하는가

이번 과정에서는 AWS CLI 프로필 기반 인증을 사용한다.

따라서 boto3 코드도 같은 인증 흐름을 따르는 것이 좋다.

이때 사용하는 구조가 `boto3.Session()`이다.

기본 예제는 다음과 같다.

```
import boto3

session = boto3.Session(profile_name="lab")
print(session)
```

여기서 `profile_name="lab"`은 AWS CLI에 로그인한 프로필 이름을 의미한다.

즉, 이 코드는 “lab 프로필로 AWS 세션을 만든다”는 뜻이다.

---

## 2. Session이 필요한 이유

`Session`을 사용하면 다음과 같은 장점이 있다.

* 어떤 프로필을 쓸지 명확하게 지정할 수 있다.

* 이후 여러 서비스 클라이언트를 같은 세션에서 만들 수 있다.

* 실습 환경에서 인증 흐름을 통일하기 쉽다.

예를 들어 한 세션으로 EC2와 S3 클라이언트를 모두 만들 수 있다.

```
import boto3

session = boto3.Session(profile_name="lab")

ec2 = session.client("ec2", region_name="ap-northeast-2")
s3 = session.client("s3", region_name="ap-northeast-2")

print(ec2)
print(s3)
```

---

## 3. region\_name 지정

일부 AWS 서비스는 리전이 중요하다.

따라서 클라이언트를 만들 때 `region_name`을 명시하는 습관이 좋다.

```
import boto3

session = boto3.Session(profile_name="lab")
ec2 = session.client("ec2", region_name="ap-northeast-2")
```

이 구조는 이후 장에서도 계속 사용된다.

---

## 실습 1. 세션 만들기

파일명: `session_test.py`

```
import boto3

session = boto3.Session(profile_name="lab")
print("session created")
print(session)
```

### 확인할 내용

* `profile_name`이 포함된 세션이 만들어지는지 확인한다.

* 세션 생성 자체는 AWS API 호출이 아니므로 기본 구조 확인용으로 적절하다.

---

# 4.4 client와 resource

## 1. client 방식

boto3에는 크게 두 가지 접근 방식이 있다.

* `client`

* `resource`

`client`는 서비스의 API와 거의 1:1로 매핑되는 **저수준(Low-level)** 인터페이스이다.

예를 들어 EC2 client 생성은 다음과 같다.

```
import boto3

session = boto3.Session(profile_name="lab")
ec2 = session.client("ec2", region_name="ap-northeast-2")

print(ec2)
```

이 `ec2` 객체를 사용해 `describe_instances()` 같은 API를 호출할 수 있다.

---

## 2. resource 방식

`resource`는 객체 지향적으로 설계된 **고수준(High-level)** 인터페이스이다.

예:

```
import boto3

session = boto3.Session(profile_name="lab")
s3_resource = session.resource("s3", region_name="ap-northeast-2")

print(s3_resource)
```

이 방식은 특정 서비스에서 편리한 경우도 있지만, 실습과 응답 구조 학습 관점에서는 `client`가 더 명확할 때가 많다.

---

## 3. 이 과정에서는 client를 중심으로 다룬다.

이유는 다음과 같다.

* AWS API 응답 구조를 그대로 보기 좋다.

* 딕셔너리/리스트 구조 학습과 연결된다.

* 생성형 AI가 `client` 예제를 자주 생성한다.

* EC2, IAM, Bedrock 등에서 일관된 패턴으로 다루기 좋다.

따라서 이후 장에서는 주로 아래 구조를 사용한다.

```
session = boto3.Session(profile_name="lab")
ec2 = session.client("ec2", region_name="ap-northeast-2")
```

---

## 실습 2. client와 resource 생성

파일명: `client_resource_test.py`

```
import boto3

session = boto3.Session(profile_name="lab")

ec2_client = session.client("ec2", region_name="ap-northeast-2")
s3_resource = session.resource("s3", region_name="ap-northeast-2")

print("ec2 client created")
print(ec2_client)

print("s3 resource created")
print(s3_resource)
```

### 확인할 내용

* `client`와 `resource` 모두 생성할 수 있는지 확인한다.

* 두 객체가 각각 다른 방식의 접근이라는 점을 이해한다.

---

# 4.5 첫 번째 AWS API 호출

## 1. EC2 리전 목록 조회 예제

API 호출 구조를 처음 익힐 때는 간단한 예제를 보는 것이 좋다.

```
import boto3

session = boto3.Session(profile_name="lab")
ec2 = session.client("ec2", region_name="ap-northeast-2")

response = ec2.describe_regions()
print(response)
```

이 코드에서 중요한 부분은 다음과 같다.

* `ec2.describe_regions()`가 AWS API 호출이다.

* 결과는 `response` 변수에 저장된다.

* `response`는 딕셔너리 구조이다.

즉, boto3는 대부분 이런 흐름이다.

1. 세션 생성

2. client 생성

3. API 호출

4. 응답값 저장

5. 응답 구조에서 필요한 값 추출

---

## 2. 응답값 전체를 바로 출력하는 이유

처음에는 응답값 전체를 한 번 출력해보는 것이 중요하다.

그래야 어떤 키가 들어 있는지, 리스트가 어디에 있는지 구조를 볼 수 있다.

예를 들어 `describe_regions()` 결과는 대략 아래와 비슷한 구조를 가진다.

```
{
    "Regions": [
        {"RegionName": "ap-northeast-2", ...},
        {"RegionName": "us-east-1", ...}
    ],
    "ResponseMetadata": {...}
}
```

즉,

* 바깥쪽은 딕셔너리

* `"Regions"` 값은 리스트

* 리스트 안 각 항목은 딕셔너리

구조이다.

---

## 실습 3. EC2 리전 목록 조회

파일명: `describe_regions.py`

```
import boto3

session = boto3.Session(profile_name="lab")
ec2 = session.client("ec2", region_name="ap-northeast-2")

response = ec2.describe_regions()

print("전체 응답 출력")
print(response)
```

### 확인할 내용

* 응답이 딕셔너리 구조로 보이는지 확인한다.

* `"Regions"` 키가 있는지 확인한다.

* 그 안에 리스트가 들어 있는지 확인한다.

---

# 4.6 AWS API 응답 구조 읽기

## 1. 응답은 왜 복잡해 보이는가

AWS API 응답은 단순 문자열 하나만 주지 않는다.

보통 아래 정보가 함께 들어 있다.

* 실제 데이터

* 메타데이터

* 상태 정보

* 페이지 관련 정보

* 추가 속성들

그래서 응답은 종종 길고 복잡해 보인다.

하지만 중요한 것은 **필요한 부분만 찾아서 읽는 것**이다.

---

## 2. 응답 구조 해석 순서

AWS API 응답을 읽을 때는 보통 아래 순서로 본다.

### 1) 가장 바깥쪽 키 확인

예:

* `Regions`

* `Reservations`

* `Buckets`

### 2) 그 값이 리스트인지 딕셔너리인지 확인

리스트면 반복문이 필요하고, 딕셔너리면 키로 들어간다.

### 3) 리스트 안 항목 구조 확인

각 항목이 딕셔너리인 경우가 많다.

### 4) 필요한 필드만 골라서 출력

예:

* `RegionName`

* `InstanceId`

* `State`

* `Name`

---

## 3. Regions 응답에서 값 꺼내기

```
import boto3

session = boto3.Session(profile_name="lab")
ec2 = session.client("ec2", region_name="ap-northeast-2")

response = ec2.describe_regions()

for region in response["Regions"]:
    print(region["RegionName"])
```

이 코드는 다음 구조를 따른다.

* `response`는 딕셔너리

* `response["Regions"]`는 리스트

* 리스트 안 `region`은 딕셔너리

* `region["RegionName"]`은 문자열

즉, 앞에서 배운 리스트/딕셔너리/반복문 구조가 그대로 연결된다.

---

## 실습 4. 리전 이름만 출력하기

파일명: `region_names.py`

```
import boto3

session = boto3.Session(profile_name="lab")
ec2 = session.client("ec2", region_name="ap-northeast-2")

response = ec2.describe_regions()

print("리전 이름 목록")
for region in response["Regions"]:
    print(region["RegionName"])
```

### 확인할 내용

* 응답 전체를 보지 않고 필요한 값만 꺼내는 방식을 확인한다.

* 리스트 반복과 딕셔너리 키 접근이 함께 사용되는지 확인한다.

---

# 4.7 EC2 인스턴스 조회 구조 미리 보기

이제 실제 자동화에서 자주 쓰는 EC2 조회 구조를 간단히 보자.

```
import boto3

session = boto3.Session(profile_name="lab")
ec2 = session.client("ec2", region_name="ap-northeast-2")

response = ec2.describe_instances()
print(response)
```

이 응답은 보통 다음과 비슷한 구조를 가진다.

```
{
    "Reservations": [
        {
            "Instances": [
                {
                    "InstanceId": "i-1234...",
                    "State": {"Name": "running"},
                    ...
                }
            ]
        }
    ],
    "ResponseMetadata": {...}
}
```

즉, 구조가 한 단계 더 깊다.

* `response` → 딕셔너리

* `response["Reservations"]` → 리스트

* 각 `reservation` → 딕셔너리

* `reservation["Instances"]` → 리스트

* 각 `instance` → 딕셔너리

그래서 반복문이 두 번 필요하다.

---

## 1. 인스턴스 ID와 상태 출력

```
import boto3

session = boto3.Session(profile_name="lab")
ec2 = session.client("ec2", region_name="ap-northeast-2")

response = ec2.describe_instances()

for reservation in response["Reservations"]:
    for instance in reservation["Instances"]:
        print(instance["InstanceId"], instance["State"]["Name"])
```

이 코드가 어렵게 느껴진다면 구조를 단계적으로 보면 된다.

### 첫 번째 반복문

`Reservations` 리스트를 돈다.

### 두 번째 반복문

각 reservation 안의 `Instances` 리스트를 돈다.

### 출력 부분

각 instance 딕셔너리에서 `InstanceId`와 `State -> Name` 값을 꺼낸다.

---

## 실습 5. EC2 인스턴스 ID와 상태 출력

파일명: `ec2_basic_list.py`

```
import boto3

session = boto3.Session(profile_name="lab")
ec2 = session.client("ec2", region_name="ap-northeast-2")

response = ec2.describe_instances()

for reservation in response["Reservations"]:
    for instance in reservation["Instances"]:
        print(
            f"id={instance['InstanceId']}, "
            f"state={instance['State']['Name']}"
        )
```

### 확인할 내용

* 반복문이 두 번 사용되는 이유를 이해한다.

* `State`가 중첩 딕셔너리라는 점을 확인한다.

---

# 4.8 이름 태그를 다루는 방식

## 1. 이름이 바로 있는 것이 아님

처음 boto3를 배울 때 많이 헷갈리는 부분이 이름 태그이다.

이름이 `instance["Name"]`처럼 바로 있는 것이 아니라, 보통 `Tags` 안에 들어 있다.

예를 들어 구조는 다음과 비슷하다.

```
"Tags": [
    {"Key": "Name", "Value": "web-1"},
    {"Key": "Env", "Value": "dev"}
]
```

즉, 이름을 바로 꺼낼 수 없고, `Tags` 리스트를 돌면서 `Key == "Name"`인 항목을 찾아야 한다.

---

## 2. 이름 태그 찾기 예제

```
def get_name_tag(instance):
    tags = instance.get("Tags", [])

    for tag in tags:
        if tag["Key"] == "Name":
            return tag["Value"]

    return "NoName"
```

이 함수의 의미는 다음과 같다.

* `Tags`가 없으면 빈 리스트 사용

* 태그를 하나씩 반복

* `Key`가 `"Name"`이면 그 값을 반환

* 끝까지 없으면 `"NoName"` 반환

이 구조는 이후 EC2 실습에서 매우 중요하다.

---

## 실습 6. 이름 태그 찾기 함수 구조 읽기

파일명: `name_tag_test.py`

```
def get_name_tag(instance):
    tags = instance.get("Tags", [])

    for tag in tags:
        if tag["Key"] == "Name":
            return tag["Value"]

    return "NoName"

sample_instance = {
    "InstanceId": "i-1111",
    "State": {"Name": "running"},
    "Tags": [
        {"Key": "Name", "Value": "web-1"},
        {"Key": "Env", "Value": "dev"}
    ]
}

print(get_name_tag(sample_instance))
```

### 확인할 내용

* `Tags`가 리스트라는 점을 확인한다.

* 반복문과 조건문으로 원하는 태그를 찾는 구조를 이해한다.

* 태그가 없을 때 기본값을 반환하는 방식을 이해한다.

---

# 4.9 boto3 코드에 예외 처리 넣기

AWS API 호출은 네트워크, 인증, 권한, 리전 설정 등의 이유로 오류가 날 수 있다.

그래서 기본적인 예외 처리를 함께 넣는 것이 좋다.

```
import boto3

try:
    session = boto3.Session(profile_name="lab")
    ec2 = session.client("ec2", region_name="ap-northeast-2")
    response = ec2.describe_regions()

    for region in response["Regions"]:
        print(region["RegionName"])

except Exception as e:
    print("AWS API 호출 중 오류 발생")
    print(f"오류 내용: {e}")
```

이 구조는 이후 장에서도 계속 사용된다.

---

## 실습 7. 예외 처리 포함 리전 조회

파일명: `describe_regions_safe.py`

```
import boto3

try:
    session = boto3.Session(profile_name="lab")
    ec2 = session.client("ec2", region_name="ap-northeast-2")

    response = ec2.describe_regions()

    for region in response["Regions"]:
        print(region["RegionName"])

except Exception as e:
    print("리전 조회 실패")
    print(f"오류 내용: {e}")
```

### 확인할 내용

* API 호출 전체를 `try/except`로 감싸는 구조를 확인한다.

* 오류가 발생했을 때 메시지가 출력되도록 준비하는 방식을 이해한다.

---

# 4.10 생성형 AI로 boto3 코드 생성 요청하기

이제 생성형 AI에게 boto3 코드 생성을 요청하는 흐름을 보자.

## 1. 좋지 않은 요청

```
EC2 코드 짜줘
```

이 요청은 정보가 부족하다.

---

## 2. 개선된 요청

```
Python boto3 코드를 작성해줘.
AWS 프로필 이름은 lab, 리전은 ap-northeast-2로 사용해줘.
EC2 인스턴스 목록을 조회하고, 인스턴스 ID와 상태를 출력해줘.
예외 처리도 포함해줘.
```

이 요청은 구체적이다.

---

## 3. 더 나은 요청

```
Python boto3 코드를 작성해줘.
AWS CLI 프로필 기반 인증을 사용하고, profile_name은 lab으로 해줘.
region_name은 ap-northeast-2로 지정해줘.
EC2 인스턴스 목록을 조회해서 인스턴스 ID, 이름 태그, 상태를 출력해줘.
이름 태그가 없으면 NoName으로 표시해줘.
함수로 분리하고, try/except 예외 처리도 포함해줘.
```

이 요청은 필요한 정보를 모두 포함하고 있다.

```
import boto3
from botocore.exceptions import ProfileNotFound, ClientError

def list_lab_ec2_instances():
    try:
        # 1. 'lab' 프로필과 지정된 리전을 사용하여 세션을 생성으로 한다.
        session = boto3.Session(
            profile_name='lab',
            region_name='ap-northeast-2'
        )
        
        # 2. EC2 클라이언트 생성으로 한다.
        ec2 = session.client('ec2')
        
        # 3. 인스턴스 정보 호출로 한다.
        response = ec2.describe_instances()
        
        # 결과 출력 헤더 설정으로 한다.
        print(f"{'Instance ID':<20} | {'Status':<15}")
        print("-" * 40)
        
        # 4. 응답 데이터를 파싱하여 ID와 상태 출력으로 한다.
        found = False
        for reservation in response.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                instance_id = instance['InstanceId']
                state = instance['State']['Name']
                print(f"{instance_id:<20} | {state:<15}")
                found = True
        
        if not found:
            print("해당 리전에 활성화된 인스턴스가 존재하지 않는다.")

    except ProfileNotFound:
        print("에러: 'lab' 프로필을 찾을 수 없음. 'aws login --profile lab' 설정을 확인하시오.")
    except ClientError as e:
        print(f"AWS 서비스 오류: {e.response['Error']['Message']}")
    except Exception as e:
        print(f"기타 오류 발생: {str(e)}")

if __name__ == "__main__":
    list_lab_ec2_instances()
```

---

# 4.11 생성된 boto3 코드를 검토하는 기준

AI가 boto3 코드를 생성했다면 아래 항목을 먼저 확인한다.

## 1. import가 맞는가

```
import boto3
```

## 2. 세션과 프로필이 맞는가

```
session = boto3.Session(profile_name="lab")
```

## 3. 리전이 명시되었는가

```
ec2 = session.client("ec2", region_name="ap-northeast-2")
```

## 4. 응답 구조를 올바르게 처리하는가

* 리스트인지

* 딕셔너리인지

* 반복문이 필요한지

## 5. 없는 값 처리 방식이 안전한가

* 태그가 없을 때 기본값 처리

* `get()` 사용 여부

## 6. 예외 처리가 있는가

* `try/except` 포함 여부

## 7. 요청한 작업만 하는가

* 조회 요청인데 삭제나 중지가 들어 있지 않은지 확인

---

# 4.12 자동화 스타일 종합 예제

이제 지금까지 배운 구조를 모은 예제를 보자.

파일명: `boto3_summary.py`

```
import boto3

def get_name_tag(instance):
    tags = instance.get("Tags", [])

    for tag in tags:
        if tag["Key"] == "Name":
            return tag["Value"]

    return "NoName"

def print_instances():
    session = boto3.Session(profile_name="lab")
    ec2 = session.client("ec2", region_name="ap-northeast-2")

    response = ec2.describe_instances()

    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            instance_id = instance["InstanceId"]
            state = instance["State"]["Name"]
            name = get_name_tag(instance)

            print(f"id={instance_id}, name={name}, state={state}")

try:
    print_instances()
except Exception as e:
    print("EC2 조회 중 오류 발생")
    print(f"오류 내용: {e}")
```

### 학습 포인트

이 예제에는 다음 내용이 모두 포함되어 있다.

* `boto3` import

* 프로필 기반 세션 생성

* EC2 client 생성

* API 호출

* 중첩 응답 구조 반복 처리

* 태그 조회 함수

* f-string 출력

* 예외 처리

즉, 이후 EC2 자동화 장으로 가기 전 준비 단계로 매우 적절한 예제이다.

---

# 4.13 자주 하는 실수

## 1. boto3 import를 빼먹는 경우

```
# ec2 = boto3.client("ec2")
```

이렇게 쓰면 `boto3`가 정의되지 않았다는 오류가 날 수 있다.

---

## 2. 세션 없이 인증을 모호하게 처리하는 경우

이번 과정에서는 프로필 기반 인증을 사용하므로, 가능하면 아래 구조를 유지하는 것이 좋다.

```
session = boto3.Session(profile_name="lab")
```

---

## 3. 리전을 빼먹는 경우

서비스에 따라 리전 지정이 없으면 원하는 결과가 나오지 않거나 오류가 날 수 있다.

---

## 4. 응답 구조를 잘못 이해하는 경우

예를 들어 `describe_instances()` 결과에서 바로 아래처럼 접근하면 안 될 수 있다.

```
# print(response["Instances"])
```

실제로는 보통 `Reservations -> Instances` 구조를 따라가야 한다.

---

## 5. 이름 태그를 바로 `instance["Name"]`으로 찾는 경우

이름 태그는 보통 `Tags` 리스트 안에 있으므로 별도 조회 로직이 필요하다.

---

# 4.14 정리

* boto3는 Python에서 AWS 서비스를 제어하는 공식 SDK이다.

* 콘솔 사용과 달리 boto3는 AWS 작업을 코드로 자동화할 수 있게 해준다.

* 이번 과정에서는 `boto3.Session(profile_name="lab")` 방식으로 프로필 기반 인증을 사용한다.

* `client` 방식은 AWS API 응답 구조를 그대로 다루기 좋다.

* AWS API 응답은 보통 딕셔너리와 리스트가 중첩된 구조이다.

* 응답을 읽을 때는 바깥 키, 리스트 여부, 반복문 필요 여부를 순서대로 보면 이해하기 쉽다.

* EC2 응답에서는 `Reservations -> Instances` 구조를 자주 보게 된다.

* 이름 태그는 보통 `Tags` 리스트 안에서 찾아야 한다.

* 생성형 AI에게 boto3 코드 생성을 요청할 때는 인증 방식, 리전, 출력 형식, 예외 처리 요구를 함께 적는 것이 좋다.

* 생성된 코드는 반드시 인증, 리전, 응답 구조, 예외 처리 기준으로 검토해야 한다.