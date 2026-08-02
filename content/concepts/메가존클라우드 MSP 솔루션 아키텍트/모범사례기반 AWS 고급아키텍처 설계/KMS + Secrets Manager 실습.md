---
title: "KMS + Secrets Manager 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "모범사례기반 AWS 고급아키텍처 설계"]
is_public: true
draft: false
---

# KMS + Secrets Manager 실습

## 1. 실습 목표

이번 실습에서 수행할 내용은 다음과 같다.

1. KMS 고객 관리형 키 생성

2. KMS로 문자열 암호화

3. KMS로 문자열 복호화

4. Secrets Manager에 비밀값 저장

5. Secrets Manager에서 비밀값 조회

6. Python 코드에서 secret 조회

7. KMS와 Secrets Manager 역할 차이 확인

---

## 2. 실습 구성

이번 실습은 아래 순서로 진행한다.

```
실습 1. KMS 키 생성
실습 2. KMS로 문자열 암호화/복호화
실습 3. Secrets Manager에 secret 저장
실습 4. Secrets Manager에서 secret 조회
실습 5. Python 코드에서 secret 사용
실습 6. KMS와 Secrets Manager 차이 정리
```

---

## 3. 실습 전 준비

필요한 준비물은 다음과 같다.

* AWS 계정

* IAM 사용자 또는 Role

* AWS CLI 설치

* AWS CLI 인증 구성 완료

* 실습 리전 예시: `ap-northeast-2`

CLI 확인

```
aws configure list
```

리전 확인

```
aws configure get region
```

---

# 4. 실습 1. KMS 키 생성

## 4.1 실습 목표

직접 **고객 관리형 KMS 키(Customer managed key)** 를 생성한다.

일반적인 데이터 암호화 실습에서는 **대칭키(Symmetric)** 를 사용하는 것이 기본이다.

## 4.2 콘솔에서 생성

경로

```
AWS Console → KMS → Customer managed keys → Create key
```

설정

* Key type: `Symmetric`

* Key usage: `Encrypt and decrypt`

* Alias: `lab-kms-key`

다음 단계에서

* Key administrators: 현재 사용자

* Key usage permissions: 현재 사용자 또는 실습용 Role

생성 완료 후 키 별칭(alias)을 확인한다.

## 4.3 확인 포인트

확인할 항목

* 키 ID

* Key ARN

* Alias

* Key state = Enabled

---

# 5. 실습 2. KMS로 문자열 암호화 / 복호화

## 5.1 실습 목표

CLI를 이용해 간단한 문자열 파일을 암호화하고, 다시 복호화한다.

## 5.2 평문 파일 만들기

```
echo -n "This is my KMS secret" > plain.txt
```

설명

* `echo -n`
  + 줄바꿈 없이 문자열만 파일에 저장

* `> plain.txt`
  + 출력 결과를 `plain.txt` 파일로 저장

파일 내용 확인

```
cat plain.txt
```

예상 결과

```
This is my KMS secret
```

## 5.3 KMS로 암호화

```
aws kms encrypt \
  --key-id alias/lab-kms-key \
  --plaintext fileb://plain.txt \
  --output text \
  --query CiphertextBlob > cipher.txt
```

### 명령어 설명

* `aws kms encrypt`
  + KMS를 사용해 암호화 수행

* `--key-id alias/lab-kms-key`
  + 사용할 KMS 키 지정

* `--plaintext fileb://plain.txt`
  + 암호화할 원본 파일 지정
  + `fileb://` 는 바이너리 안전 방식으로 파일을 읽는 의미

* `--output text`
  + 결과를 텍스트로 출력

* `--query CiphertextBlob`
  + 반환 결과 중 `CiphertextBlob` 값만 추출

* `> cipher.txt`
  + 추출한 암호문을 `cipher.txt` 에 저장

암호문 확인

```
cat cipher.txt
```

예상 결과

* 긴 Base64 문자열이 보이면 정상

## 5.4 복호화 준비

암호문은 Base64 상태이므로 먼저 바이너리 파일로 변환한다.

```
cat cipher.txt | base64 -d > cipher.bin
```

base64: invalid input 출력시 -i 옵션 추

설명

* `cat cipher.txt`
  + 암호문 파일 읽기

* `| base64 -d`
  + Base64 디코딩

* `> cipher.bin`
  + 바이너리 암호문 파일 생성

## 5.5 복호화

```
aws kms decrypt \
  --ciphertext-blob fileb://cipher.bin \
  --output text \
  --query Plaintext | base64 -d
```

예상 결과

```
This is my KMS secret
```

### 명령어 설명

* `aws kms decrypt`
  + KMS를 사용해 복호화 수행

* `--ciphertext-blob fileb://cipher.bin`
  + 복호화할 암호문 지정

* `-query Plaintext`
  + 결과 중 복호화된 원문 부분만 추출

* `| base64 -d`
  + 원문이 Base64 형태로 반환되므로 다시 디코딩

## 5.6 확인 포인트

확인할 항목

* 평문 파일 생성 여부

* 암호문 파일 생성 여부

* 복호화 결과가 원문과 동일한지

---

# 6. 실습 3. Secrets Manager에 secret 저장

## 6.1 실습 목표

DB 접속 정보처럼 민감한 값을 Secrets Manager에 저장한다.

## 6.2 저장할 예시 데이터

이번 실습에서는 아래 JSON을 secret 값으로 사용한다.

```
{
  "username": "admin",
  "password": "P@ssw0rd1234!",
  "host": "db.example.com",
  "port": "3306",
  "dbname": "appdb"
}
```

## 6.3 JSON 파일 작성

```
cat > secret.json <<'EOF'
{
  "username": "admin",
  "password": "P@ssw0rd1234!",
  "host": "db.example.com",
  "port": "3306",
  "dbname": "appdb"
}
EOF
```

파일 확인

```
cat secret.json
```

## 6.4 Secrets Manager에 저장

```
aws secretsmanager create-secret \
  --name prod/app/db \
  --description "Database credential for app" \
  --secret-string file://secret.json
```

### 명령어 설명

* `aws secretsmanager create-secret`
  + 새로운 secret 생성

* `--name prod/app/db`
  + secret 이름

* `--description`
  + 설명

* `--secret-string file://secret.json`
  + 파일 내용을 secret 값으로 저장

## 6.5 확인 포인트

확인할 항목

* Secret name

* ARN

* Secret value 정상 저장 여부

---

# 7. 실습 4. Secrets Manager에서 secret 조회

## 7.1 전체 secret 조회

```
aws secretsmanager get-secret-value \
  --secret-id prod/app/db
```

예상 결과

```
{
  "ARN": "...",
  "Name": "prod/app/db",
  "SecretString": "{\"username\":\"admin\",\"password\":\"P@ssw0rd1234!\",\"host\":\"db.example.com\",\"port\":\"3306\",\"dbname\":\"appdb\"}"
}
```

## 7.2 SecretString만 추출

```
aws secretsmanager get-secret-value \
  --secret-id prod/app/db \
  --query SecretString \
  --output text
```

## 7.3 password 값만 보기

jq가 설치되어 있으면 아래처럼 추출할 수 있다.

```
aws secretsmanager get-secret-value \
  --secret-id prod/app/db \
  --query SecretString \
  --output text | jq -r '.password'
```

예상 결과

```
P@ssw0rd1234!
```

## 7.4 확인 포인트

확인할 항목

* SecretString 값이 보이는지

* JSON 구조가 유지되는지

* password 키만 추출 가능한지

---

# 8. 실습 5. Python 애플리케이션에서 secret 조회

## 8.1 실습 목표

애플리케이션 코드 안에 비밀번호를 직접 쓰지 않고, 실행 시 Secrets Manager에서 가져오게 한다.

## 8.2 boto3 설치

```
pip install boto3 "botocore[crt]"
```

## 8.3 예제 코드 작성

```
import json
import boto3

SECRET_NAME = "prod/app/db"
REGION = "ap-northeast-2"

def get_secret():
    client = boto3.client("secretsmanager", region_name=REGION)
    response = client.get_secret_value(SecretId=SECRET_NAME)
    return json.loads(response["SecretString"])

if __name__ == "__main__":
    secret = get_secret()
    print("username:", secret["username"])
    print("password:", secret["password"])
    print("host:", secret["host"])
    print("port:", secret["port"])
    print("dbname:", secret["dbname"])
```

## 8.4 실행

```
python app.py
```

예상 결과

```
username: admin
password: P@ssw0rd1234!
host: db.example.com
port: 3306
dbname: appdb
```

## 8.5 설명

이 방식의 핵심은 다음이다.

* 코드 안에 비밀번호를 하드코딩하지 않음

* secret 값을 필요할 때만 조회함

* 비밀번호 변경 시 코드 수정이 줄어듦

---

# 9. 실습 6. 고객 관리형 KMS 키를 사용해 secret 저장

## 9.1 실습 목표

이번에는 Secrets Manager가 기본 키가 아니라 **직접 만든 KMS 키**를 사용하도록 설정한다.

## 9.2 새 secret 생성

```
aws secretsmanager create-secret \
  --name 이니셜/prod/app/db-custom-kms \
  --description "Database credential protected by customer managed KMS key" \
  --kms-key-id alias/이니셜-kms-key \
  --secret-string file://secret.json
```

## 9.3 조회 확인

```
aws secretsmanager get-secret-value \
  --secret-id prod/app/db-custom-kms \
  --query SecretString \
  --output text
```

## 9.4 확인 포인트

* customer managed KMS key로 저장되었는지

* 조회가 정상 동작하는지

* KMS 권한 부족 시 어떤 에러가 나는지

---

# 10. 실습 7. KMS와 Secrets Manager 차이 확인

## 10.1 KMS는 무엇인가

KMS는 **암호화 키를 관리하는 서비스**다.

* 키 생성

* CLI로 암호화

* CLI로 복호화

즉, KMS는 **키 관리와 암호화 작업** 중심이다.

## 10.2 Secrets Manager는 무엇인가

Secrets Manager는 **비밀번호, 토큰, API Key, DB 자격 증명 같은 secret 값을 저장하고 조회하는 서비스**다.

* secret 생성

* secret 조회

* Python등 코드에서 secret 사용

즉, Secrets Manager는 **비밀값 관리** 중심이다.

## 10.3 두 서비스의 관계

* KMS는 키를 관리

* Secrets Manager는 비밀값을 관리

* Secrets Manager는 내부적으로 KMS를 사용해 secret를 보호

---

# 11. 실습 8. 선택 실습 - Secret 값 변경

## 11.1 새 값 파일 작성

```
cat > secret-v2.json <<'EOF'
{
  "username": "admin",
  "password": "NewP@ssw0rd5678!",
  "host": "db.example.com",
  "port": "3306",
  "dbname": "appdb"
}
EOF
```

## 11.2 Secret 값 업데이트

```
aws secretsmanager update-secret \
  --secret-id prod/app/db \
  --secret-string file://secret-v2.json
```

## 11.3 다시 조회

```
aws secretsmanager get-secret-value \
  --secret-id prod/app/db \
  --query SecretString \
  --output text
```

---

# 12. 트러블슈팅

## 12.1 `AccessDeniedException` 발생

원인

* KMS 사용 권한 부족

* Secrets Manager 조회 권한 부족

확인할 것

* `secretsmanager:GetSecretValue`

* KMS key policy 또는 IAM policy

## 12.2 `ResourceNotFoundException`

원인

* secret 이름 오타

* 리전 다름

* 삭제 예약 상태

확인

```
aws configure get region
```

## 12.3 KMS 복호화가 안 됨

원인

* 잘못된 key-id 사용

* ciphertext 파일 손상

* Base64 디코딩 누락

확인 절차

1. `cipher.txt` 생성 여부

2. `cipher.bin` 생성 여부

3. 복호화 명령에서 `fileb://cipher.bin` 사용 여부

---

# 14. 정리

* **KMS는 키를 관리하고 암호화/복호화를 수행하는 서비스**

* **Secrets Manager는 비밀번호와 토큰 같은 secret 값을 저장하고 조회하는 서비스**

* **Secrets Manager는 내부적으로 KMS를 사용해 secret를 보호한다**

즉,

* **KMS = 키 관리**

* **Secrets Manager = 비밀값 관리**