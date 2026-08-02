---
title: "Gateway Endpoint 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "모범사례기반 AWS 고급아키텍처 설계"]
is_public: true
draft: false
---

# Gateway Endpoint 실습

---

# 1. 실습 목표

* Private Subnet의 EC2에서 NAT Gateway 없이 S3 접근 확인

* S3 Gateway Endpoint 생성

* Route Table 연동 확인

* Endpoint Policy 적용 확인

---

# 2. 실습 환경

## 구성

* VPC 1개

* Public Subnet 1개

* Private Subnet 1개

* Public EC2 1대

* Private EC2 1대

* S3 Bucket 1개

* S3 Gateway Endpoint 1개

## 예시 네트워크

* VPC: `10.10.0.0/16`

* Public Subnet: `10.10.1.0/24`

* Private Subnet: `10.10.2.0/24`

---

# 3. 사전 준비

* 서울 리전 사용

* Public EC2 생성

* Private EC2 생성

* Private EC2에 IAM Role 연결
  + `AmazonS3ReadOnlyAccess` 또는 `AmazonS3FullAccess`

* S3 Bucket 생성

* Bucket 안에 테스트 파일 업로드

예시 파일명

```
sample.txt
```

예시 내용

```
gateway endpoint test
```

---

# 4. VPC 및 서브넷 구성

---

## 4.1 VPC 생성

VPC 생성

```
Name: lab-vpc
CIDR: 10.10.0.0/16
```

---

## 4.2 Public Subnet 생성

```
Name: lab-public-subnet
CIDR: 10.10.1.0/24
```

---

## 4.3 Private Subnet 생성

```
Name: lab-private-subnet
CIDR: 10.10.2.0/24
```

---

## 4.4 Internet Gateway 생성 및 연결

Internet Gateway 생성 후 `lab-vpc`에 연결

---

## 4.5 Route Table 생성

### Public Route Table

```
Name: lab-public-rt
```

라우트 추가

```
0.0.0.0/0 → Internet Gateway
```

Public Subnet 연결

---

### Private Route Table

```
Name: lab-private-rt
```

주의사항

* NAT Gateway 연결하지 않음

* `0.0.0.0/0` 경로 넣지 않음

Private Subnet 연결

---

# 5. EC2 생성

---

## 5.1 Public EC2 생성

설정 예시

```
Name: bastion-ec2
Subnet: lab-public-subnet
Public IP: Enable
```

보안 그룹

* SSH 22: 내 공인 IP 허용

---

## 5.2 Private EC2 생성

설정 예시

```
Name: private-ec2
Subnet: lab-private-subnet
Public IP: Disable
IAM Role: AmazonS3ReadOnlyAccess
```

보안 그룹

* SSH 22: Public EC2 보안 그룹 허용

---

# 6. S3 Bucket 생성

S3 Bucket 생성

예시 이름

```
이니셜-gateway-endpoint-lab
```

파일 업로드

```
sample.txt
```

---

# 7. Public EC2에서 Private EC2 접속

---

## 7.1 Public EC2 접속

```
ssh -i mykey.pem ec2-user@<Public-EC2-Public-IP>
```

---

## 7.2 Private EC2 접속

```
ssh -i mykey.pem ec2-user@<Private-EC2-Private-IP>
```

---

# 8. AWS CLI 확인

Private EC2에서 실행

```
aws --version
```

설치되지 않은 경우

### Amazon Linux 2023

```
sudo dnf install awscli -y
```

### Ubuntu

```
sudo apt update
sudo apt install awscli -y
```

버전 확인 다시 실행

```
aws --version
```

---

# 9. Endpoint 생성 전 S3 접근 확인

Private EC2에서 실행

```
aws s3 ls
```

또는

```
aws s3 ls s3://이니셜-gateway-endpoint-lab
```

예상

* 응답 지연

* 연결 실패

* timeout 발생 가능

이 상태를 먼저 확인해둠.

---

# 10. S3 Gateway Endpoint 생성

---

## 10.1 콘솔 이동

```
VPC → Endpoints → Create endpoint
```

---

## 10.2 Endpoint 설정

### Name tag

```
lab-s3-gateway-endpoint
```

### Service category

```
AWS services
```

### Service name 검색

```
s3
```

서울 리전 예시

```
com.amazonaws.ap-northeast-2.s3
```

### VPC 선택

```
lab-vpc
```

### Endpoint type

```
Gateway
```

---

## 10.3 Route Table 선택

반드시 Private Subnet이 연결된 Route Table 선택

```
lab-private-rt
```

---

## 10.4 Policy

처음에는 기본 정책 사용

```
Full Access
```

---

## 10.5 Endpoint 생성

생성 후 상태가 `Available`인지 확인

---

# 11. Route Table 확인

콘솔 경로

```
VPC → Route Tables → lab-private-rt → Routes
```

확인 항목

* local 경로 존재

* S3 관련 Prefix List 경로 자동 추가됨

* target이 VPC Endpoint로 표시됨

예시 형태

```
Destination: pl-xxxxxxxx
Target: vpce-xxxxxxxx
```

---

# 12. Endpoint 생성 후 S3 접근 테스트

Private EC2에서 다시 실행

---

## 12.1 버킷 목록 조회

```
aws s3 ls
```

---

## 12.2 특정 버킷 조회

```
aws s3 ls s3://이니셜-gateway-endpoint-lab
```

예상 출력 예시

```
2026-04-01 12:10:00         22 sample.txt
```

---

## 12.3 파일 다운로드

```
aws s3 cp s3://이니셜-gateway-endpoint-lab/sample.txt .
```

---

## 12.4 다운로드 확인

```
cat sample.txt
```

예상 출력

```
gateway endpoint test
```

---

# 13. Endpoint Policy 제한 실습

---

## 13.1 Endpoint 선택

```
VPC → Endpoints → lab-s3-gateway-endpoint
```

---

## 13.2 Policy 수정

기존 정책을 아래처럼 수정

```
{
  "Statement": [
    {
      "Principal": "*",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Effect": "Allow",
      "Resource": [
        "arn:aws:s3:::이니셜-gateway-endpoint-lab",
        "arn:aws:s3:::이니셜-gateway-endpoint-lab/*"
      ]
    }
  ]
}
```

저장

---

## 13.3 허용된 버킷 테스트

```
aws s3 ls s3://이니셜-gateway-endpoint-lab
```

```
aws s3 cp s3://이니셜-gateway-endpoint-lab/sample.txt .
```

---

## 13.4 다른 버킷 접근 테스트

```
aws s3 ls s3://다른-버킷명
```

예상

```
AccessDenied
```

또는 권한 거부 메시지 확인

---

# 14. CLI로 Endpoint 생성 실습

콘솔 실습 후 CLI로도 생성 가능함.

```
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-xxxxxxxx \
  --service-name com.amazonaws.ap-northeast-2.s3 \
  --vpc-endpoint-type Gateway \
  --route-table-ids rtb-xxxxxxxx
```

각 항목

* `--vpc-id` : Endpoint를 생성할 VPC ID

* `--service-name` : 연결할 서비스 이름

* `--vpc-endpoint-type Gateway` : Gateway Endpoint 지정

* `--route-table-ids` : 연결할 Route Table 지정

생성 후 조회

```
aws ec2 describe-vpc-endpoints
```

---

# 15. 확인용 명령어 정리

Private EC2에서 자주 사용하는 명령

```
aws sts get-caller-identity
```

현재 IAM Role 확인용

```
aws s3 ls
```

버킷 목록 조회

```
aws s3 ls s3://이니셜-gateway-endpoint-lab
```

특정 버킷 조회

```
aws s3 cp s3://이니셜-gateway-endpoint-lab/sample.txt .
```

파일 다운로드

```
cat sample.txt
```

파일 내용 확인

---

# 16. 트러블슈팅

---

## 16.1 S3 접근이 계속 안 되는 경우

확인 항목

* Private EC2에 IAM Role 연결했는지 확인

* IAM Role에 S3 권한 있는지 확인

* Private Subnet이 `lab-private-rt`를 사용 중인지 확인

* Gateway Endpoint가 `lab-private-rt`에 연결됐는지 확인

* Endpoint 상태가 `Available`인지 확인

* Endpoint Policy가 너무 제한적이지 않은지 확인

---

## 16.2 EC2에 Role이 붙었는지 확인

```
aws sts get-caller-identity
```

정상적으로 계정 정보가 나오면 Role 자격 증명 사용 중인 상태임.

---

## 16.3 Route Table 잘못 연결한 경우

자주 하는 실수

* Public Route Table만 선택함

* Private Subnet이 다른 Route Table을 사용 중임

반드시 Private EC2가 속한 Subnet의 Route Table 확인 필요

---

# 17. 실습 종료 후 삭제

삭제 순서

1. VPC Endpoint 삭제

2. S3 객체 삭제

3. S3 Bucket 삭제

4. EC2 인스턴스 종료

5. Route Table 정리

6. Subnet 삭제

7. Internet Gateway 분리 및 삭제

8. VPC 삭제

---