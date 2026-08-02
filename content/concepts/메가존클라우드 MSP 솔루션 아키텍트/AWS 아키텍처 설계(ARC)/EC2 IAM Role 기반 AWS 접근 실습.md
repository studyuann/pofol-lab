---
title: "EC2 IAM Role 기반 AWS 접근 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 아키텍처 설계(ARC)"]
is_public: true
draft: false
---

# EC2 IAM Role 기반 AWS 접근 실습

# 1. 실습 목표

이 실습에서는 EC2 인스턴스에 IAM Role을 연결하고, 인스턴스 내부에서 별도의 Access Key 설정 없이 AWS CLI가 동작하는 과정을 확인한다.

실습을 통해 다음 내용을 확인한다.

* EC2에 IAM Role을 연결하는 방식

* Instance Profile의 역할

* STS 기반 임시 자격 증명 사용 구조

* IMDS를 통한 임시 Credential 확인

* AWS CLI / SDK가 자격 증명을 자동으로 사용하는 방식

* IMDSv2 토큰 기반 조회 방법

* `aws sts get-caller-identity` 결과 해석 방법

AWS는 장기 Access Key보다 IAM Role과 임시 자격 증명 사용을 권장한다. IAM Role을 EC2에 연결하면 애플리케이션은 인스턴스 메타데이터 서비스(IMDS)에서 임시 자격 증명을 받아 AWS API를 호출할 수 있다. ([AWS Docs](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_switch-role-ec2?utm_source=chatgpt.com))

---

# 2. 전체 동작 구조

EC2에서 IAM Role을 사용하는 흐름은 다음과 같다.

```
EC2 Instance
      │
      │  IAM Role 연결
      ▼
Instance Profile
      │
      ▼
IAM Role
      │
      │  Role 기반 임시 자격 증명 사용
      ▼
AWS STS
      │
      │  Temporary Credential 제공
      ▼
EC2 Instance Metadata Service (IMDS)
      │
      ▼
AWS CLI / AWS SDK
```

핵심은 EC2 내부에 Access Key를 직접 저장하지 않는다는 점이다.

대신 IAM Role을 기반으로 한 임시 자격 증명이 인스턴스 내부에서 자동으로 제공되고, AWS CLI와 SDK는 이를 자동으로 사용한다. AWS 문서에서도 EC2에서 애플리케이션에 장기 자격 증명을 배포하는 대신 IAM Role 사용을 권장한다. ([AWS Docs](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_switch-role-ec2?utm_source=chatgpt.com))

---

# 3. 실습 아키텍처

이번 실습 구조는 다음과 같다.

```
EC2
 └─ IAM Role 연결
     └─ S3 읽기 권한 정책 연결
         └─ EC2 내부에서 aws s3 ls 실행
```

실습에서는 S3 조회 권한이 있는 IAM Role을 하나 만들고, 이를 EC2에 연결한 뒤 인스턴스 내부에서 다음을 확인한다.

* EC2에 Role이 연결되었는지

* 메타데이터 서버에서 임시 자격 증명이 조회되는지

* AWS CLI가 해당 자격 증명을 사용해 S3를 조회하는지

---

# 4. 사전 준비

실습 전에 다음이 준비되어 있어야 한다.

* 실행 중인 EC2 인스턴스 1대

* EC2 접속 가능 환경
  + SSH 또는 SSM Session Manager

* IAM Role 생성 권한

* EC2에 IAM Role 연결 권한

* AWS CLI 설치된 EC2

* 조회 테스트용 S3 버킷 또는 S3 조회 권한

EC2에 AWS CLI가 없다면 Amazon Linux 계열에서 다음과 같이 설치할 수 있다.

```
sudo dnf install -y awscli
aws --version
```

설명

* `sudo` : 관리자 권한으로 실행

* `dnf install -y awscli` : AWS CLI 패키지 설치

* `aws --version` : 설치된 AWS CLI 버전 확인

---

# 5. IAM Role 생성

이번 실습에서는 EC2가 S3를 조회할 수 있도록 Role을 생성한다.

## 5.1 IAM Role 생성

AWS 콘솔에서 다음 경로로 이동한다.

```
IAM → Roles → Create role
```

설정

```
Trusted entity type
AWS service

Use case
EC2
```

다음 단계에서 정책을 연결한다.

예시 정책

```
AmazonS3ReadOnlyAccess
```

Role 이름 예시

```
이니셜-role-ec2-s3-readonly
```

## 5.2 왜 EC2용 Role로 생성하는가

EC2가 Role을 사용할 수 있으려면 신뢰 정책(Trust Policy)에 EC2 서비스가 포함되어야 한다.

즉 이 Role은 “누가 Assume 할 수 있는가”를 EC2로 지정한 Role이다. IAM Role은 임시 자격 증명을 제공하며, EC2 워크로드에는 인스턴스 프로파일을 통해 전달된다. ([AWS Docs](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles?utm_source=chatgpt.com))

---

# 6. Instance Profile 확인

EC2는 IAM Role을 직접 붙이는 방식으로 동작하는 것처럼 보이지만, 실제로는 **Instance Profile**이 중간에 사용된다.

구조는 다음과 같다.

```
EC2 Instance
    │
Instance Profile
    │
IAM Role
```

Instance Profile은 EC2에 Role 정보를 전달하기 위한 컨테이너다. 콘솔에서 EC2용 Role을 생성하면 같은 이름의 인스턴스 프로파일이 자동 생성될 수 있다.

즉 콘솔에서는 Role을 인스턴스에 연결하는 것처럼 보이지만, 내부적으로는 Instance Profile을 통해 연결되는 구조다.

---

# 7. EC2에 IAM Role 연결

실행 중인 EC2에 Role을 연결한다.

경로

```
EC2 → Instances → 대상 인스턴스 선택
→ Actions → Security → Modify IAM role
```

선택 항목

```
IAM role
이니셜-role-ec2-s3-readonly
```

적용 후 저장한다.

## 확인 포인트

이 작업이 완료되면 EC2는 연결된 Role에 따라 임시 자격 증명을 사용할 수 있게 된다.

일반적으로 별도의 Access Key 파일을 만들지 않아도 AWS CLI가 자동으로 자격 증명을 인식한다.

---

# 8. EC2 내부에서 Role 사용 여부 확인

EC2에 접속한 후 가장 먼저 현재 어떤 자격 증명으로 AWS API를 호출하는지 확인한다.

```
aws sts get-caller-identity
```

예상 결과 예시

```
{
  "UserId": "AROAEXAMPLE:i-0123456789abcdef0",
  "Account": "123456789012",
  "Arn": "arn:aws:sts::123456789012:assumed-role/이니셜-role-ec2-s3-readonly/i-0123456789abcdef0"
}
```

## 명령 설명

### `aws sts get-caller-identity`

이 명령은 현재 AWS CLI가 어떤 자격 증명으로 동작하고 있는지 확인하는 가장 기본적인 진단 명령이다.

* `aws` : AWS CLI 실행

* `sts` : Security Token Service 관련 API 호출

* `get-caller-identity` : 현재 호출 주체의 계정, ARN, 식별자 조회

## 결과 해석

출력의 `Arn` 부분이 다음 형태라면

```
arn:aws:sts::계정ID:assumed-role/Role이름/세션이름
```

현재 EC2는 IAM Role 기반 임시 자격 증명을 사용 중이라는 의미다.

즉 Access Key를 직접 설정한 것이 아니라 Role을 Assume 한 세션으로 동작하는 상태다.

이 결과는 Role 기반 임시 자격 증명이 사용되고 있음을 보여준다. ([AWS Docs](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp?utm_source=chatgpt.com))

---

# 9. S3 접근 테스트

이제 실제 권한이 동작하는지 테스트한다.

```
aws s3 ls
```

또는 특정 버킷 조회

```
aws s3 ls s3://버킷이름
```

## 명령 설명

### `aws s3 ls`

* S3 버킷 목록 또는 버킷 내부 객체 목록을 조회하는 명령

* 현재 연결된 자격 증명이 S3 조회 권한을 가지고 있어야 성공함

성공하면 Role 권한이 EC2에서 정상적으로 적용된 것이다.

권한이 부족하면 다음과 같은 오류가 나올 수 있다.

```
An error occurred (AccessDenied) when calling the ListBuckets operation
```

이 경우 확인할 항목은 다음과 같다.

* Role에 연결된 정책이 맞는지

* Role이 올바른 EC2에 연결되었는지

* 버킷 정책이 별도로 접근을 제한하고 있지 않은지

---

# 10. EC2 Metadata Server 확인

EC2는 메타데이터 서비스(IMDS)를 통해 인스턴스 관련 정보를 제공한다.

IAM Role을 연결한 경우, 임시 자격 증명도 여기서 확인할 수 있다.

메타데이터 주소는 다음과 같다.

```
http://169.254.169.254
```

이 주소는 link-local 주소이며 EC2 인스턴스 내부에서만 접근할 수 있다. AWS는 인스턴스 메타데이터를 인스턴스 내부에서 조회할 수 있도록 제공한다.

---

# 11. IMDSv2 토큰 발급

최근에는 IMDSv2 사용이 권장된다. IMDSv2는 토큰 기반 세션 지향 방식으로, 단순 GET 요청만으로 메타데이터를 조회하는 IMDSv1보다 SSRF 완화에 유리하다.

먼저 토큰을 발급한다.

```
TOKEN=$(curl -X PUT http://169.254.169.254/latest/api/token \
-H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
```

## 명령 설명

### `curl -X PUT`

HTTP PUT 메서드로 요청을 보낸다.

### `http://169.254.169.254/latest/api/token`

IMDSv2 토큰 발급 엔드포인트다.

### `X-aws-ec2-metadata-token-ttl-seconds: 21600`

토큰 TTL(Time To Live)을 초 단위로 지정한다.

`21600`초는 6시간이다.

### `TOKEN=$(...)`

명령 실행 결과를 `TOKEN` 변수에 저장한다.

정상 실행 후 토큰 값이 저장되었는지 확인한다.

```
echo $TOKEN
```

문자열이 출력되면 정상이다.

---

# 12. 메타데이터 기본 조회

발급한 토큰을 이용해 메타데이터 상위 목록을 조회한다.

```
curl -H "X-aws-ec2-metadata-token: $TOKEN" \
http://169.254.169.254/latest/meta-data/
```

이 명령은 인스턴스에서 조회 가능한 메타데이터 항목 목록을 보여준다.

예를 들어 다음과 같은 항목이 보일 수 있다.

```
ami-id
hostname
iam/
instance-id
local-ipv4
placement/
security-groups
```

---

# 13. IAM Role 이름 조회

이제 현재 인스턴스에 연결된 IAM Role 이름을 확인한다.

```
curl -H "X-aws-ec2-metadata-token: $TOKEN" \
http://169.254.169.254/latest/meta-data/iam/security-credentials/
```

예상 결과

```
이니셜-role-ec2-s3-readonly
```

## 의미

이 경로는 EC2에 연결된 IAM Role 이름을 반환한다.

즉 현재 인스턴스가 어떤 Role의 자격 증명을 사용할 수 있는지 보여준다. AWS 문서에서도 IAM 역할 자격 증명은 `iam/security-credentials/role-name` 경로에서 조회할 수 있다고 설명한다.

---

# 14. 임시 Credential 조회

이제 실제 임시 자격 증명 내용을 조회한다.

```
ROLE_NAME=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
http://169.254.169.254/latest/meta-data/iam/security-credentials/)

curl -H "X-aws-ec2-metadata-token: $TOKEN" \
http://169.254.169.254/latest/meta-data/iam/security-credentials/$ROLE_NAME
```

예상 결과 예시

```
{
  "Code" : "Success",
  "LastUpdated" : "2026-03-21T06:10:18Z",
  "Type" : "AWS-HMAC",
  "AccessKeyId" : "ASIA....",
  "SecretAccessKey" : "....",
  "Token" : "....",
  "Expiration" : "2026-03-21T12:21:45Z"
}
```

## 주요 필드 설명

### `AccessKeyId`

임시 Access Key ID다.

### `SecretAccessKey`

임시 Secret Key다.

### `Token`

세션 토큰이다.

임시 자격 증명은 Access Key / Secret Key만으로 끝나지 않고 Session Token까지 함께 사용한다.

### `Expiration`

이 자격 증명이 만료되는 시각이다.

### `LastUpdated`

메타데이터에 현재 자격 증명이 반영된 시각이다.

이 결과는 EC2가 장기 자격 증명이 아닌 **STS 기반 임시 자격 증명**을 사용하고 있음을 보여준다. AWS STS는 임시 보안 자격 증명을 제공하는 서비스다. ([AWS Docs](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp?utm_source=chatgpt.com))

---

# 15. Credential 유효시간 확인

조회 결과의 `Expiration` 값을 보고 유효시간을 확인할 수 있다.

예

```
"Expiration" : "2026-03-21T12:21:45Z"
```

이 값은 현재 자격 증명이 언제 만료되는지 나타낸다.

실무적으로는 이 값을 기준으로 “자격 증명이 임시라는 점”을 확인하면 된다.

일반적으로 EC2 Role 자격 증명은 일정 시간이 지나면 자동으로 갱신되며, 애플리케이션은 보통 이 과정을 직접 구현하지 않아도 SDK와 CLI가 처리한다. AWS는 임시 자격 증명 사용과 자동 갱신 가능한 SDK 사용을 권장한다.

※ 유효시간은 항상 고정된 하나의 숫자로 이해하기보다, 실제로는 `Expiration` 값으로 확인하는 방식이 가장 정확하다.

---

# 16. 자동 갱신 동작 이해

EC2 IAM Role 자격 증명은 영구 자격 증명이 아니다.

만료 시점이 있으며, AWS CLI와 SDK는 만료 전에 새 자격 증명을 다시 받아 사용한다.

동작 흐름은 다음과 같다.

```
IAM Role 연결
   │
임시 Credential 생성
   │
IMDS에 제공
   │
AWS CLI / SDK 사용
   │
만료 시점 도래
   │
새 임시 Credential 갱신
   │
계속 사용
```

이 구조 덕분에 애플리케이션 코드나 운영자가 Access Key를 직접 교체하지 않아도 된다.

---

# 17. AWS CLI가 Credential을 자동으로 사용하는 이유

AWS CLI와 SDK는 기본 자격 증명 공급자 체인(credential provider chain)을 사용한다.

EC2 환경에서는 로컬 설정 파일에 자격 증명이 없더라도, 인스턴스 메타데이터 서비스에서 Role 자격 증명을 조회해 자동으로 사용한다. AWS SDK 최신 버전은 IMDSv2도 지원한다.

즉 다음과 같은 명령이 별도의 Access Key 설정 없이 동작할 수 있다.

```
aws s3 ls
aws dynamodb list-tables
aws sts get-caller-identity
```

단, 전제 조건은 다음과 같다.

* EC2에 IAM Role이 연결되어 있어야 함

* 해당 Role에 필요한 권한이 있어야 함

* IMDS 접근이 가능해야 함

---

# 18. 추가 확인 실습

## 18.1 현재 인스턴스 ID 확인

```
curl -H "X-aws-ec2-metadata-token: $TOKEN" \
http://169.254.169.254/latest/meta-data/instance-id
```

이 명령은 현재 접속 중인 EC2 인스턴스 ID를 보여준다.

## 18.2 현재 리전 확인

```
curl -H "X-aws-ec2-metadata-token: $TOKEN" \
http://169.254.169.254/latest/dynamic/instance-identity/document
```

출력 예시에는 다음 정보가 포함될 수 있다.

* accountId

* region

* availabilityZone

* instanceId

이 정보는 현재 인스턴스가 어느 리전에 속하는지 확인할 때 유용하다.

## 18.3 환경 변수 자격 증명 여부 확인

```
env | grep AWS
```

아무 값이 없거나 최소한의 설정만 보인다면, 현재 CLI가 환경 변수 Access Key가 아니라 Role 기반 자격 증명을 사용할 가능성이 높다.

## 18.4 로컬 CLI 설정 파일 확인

```
cat ~/.aws/credentials
cat ~/.aws/config
```

별도 자격 증명이 없는데도 `aws sts get-caller-identity` 가 성공한다면, Role 기반 자격 증명이 자동 사용되고 있다고 볼 수 있다.

---

# 19. 문제 발생 시 점검 항목

## 19.1 `aws sts get-caller-identity` 실패

확인 항목

* EC2에 IAM Role이 연결되었는지

* Role 연결 후 충분히 반영되었는지

* AWS CLI가 설치되어 있는지

* 네트워크 또는 프록시 문제는 없는지

## 19.2 메타데이터 조회 실패

확인 항목

* IMDS가 비활성화되지 않았는지

* IMDSv2 필수인데 토큰 없이 조회하고 있지 않은지

* OS 방화벽 또는 프록시 설정이 169.254.169.254 접근을 막고 있지 않은지

## 19.3 S3 조회 실패

확인 항목

* Role 정책에 S3 읽기 권한이 있는지

* 버킷 정책이 별도로 거부하고 있지 않은지

* 명령 대상 리전 또는 버킷 이름이 맞는지

---

# 20. 보안 관점 정리

EC2에서 Access Key를 직접 저장하지 않는 이유는 다음과 같다.

* 장기 자격 증명 유출 위험 감소

* 키 교체 운영 부담 감소

* 권한 회수 및 변경이 쉬움

* 인스턴스별 또는 역할별 최소 권한 적용 가능

* 자동 갱신되는 임시 자격 증명 사용 가능

AWS는 장기 Access Key보다 임시 자격 증명과 IAM Role 사용을 권장한다.

또한 IMDS는 민감한 정보에 접근하는 경로이므로, IMDSv2 사용과 애플리케이션의 SSRF(Server-Side Request Forgery;서버측 요청 위조) 방어가 중요하다.

---

# 21. 최종 실습 요약

이번 실습에서 확인한 흐름은 다음과 같다.

```
1. IAM Role 생성
2. EC2에 Role 연결
3. EC2 내부에서 aws sts get-caller-identity 실행
4. assumed-role ARN 확인
5. IMDSv2 토큰 발급
6. 메타데이터에서 Role 이름 조회
7. 메타데이터에서 임시 Credential 조회
8. aws s3 ls 실행
9. Access Key 없이 AWS 접근 가능함을 확인
```