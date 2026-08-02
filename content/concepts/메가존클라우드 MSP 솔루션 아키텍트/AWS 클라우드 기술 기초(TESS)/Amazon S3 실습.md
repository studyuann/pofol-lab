---
title: "Amazon S3 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 클라우드 기술 기초(TESS)"]
is_public: true
draft: false
---

# Amazon S3 실습

# 1. 실습 목표

이 실습에서는 Amazon S3에서 제공하는 다양한 접근제어 방식을 실습한다.

실습을 통해 다음 내용을 이해한다.

* S3 Bucket 생성

* S3 객체 업로드

* ACL 기반 접근제어

* Bucket Policy 기반 접근제어

* IAM Role 기반 접근제어

* Pre-Signed URL 생성

* Static Website Hosting 구성

---

# 2. S3 기본 구조 이해

S3는 **Object Storage** 서비스이다.

구조는 다음과 같다.

```
S3
 └ Bucket
     └ Object
          ├ image.jpg
          ├ log.txt
          └ index.html
```

구성 요소

| 구성요소 | 설명 |
| --- | --- |
| Bucket | 객체 저장 컨테이너 |
| Object | 실제 데이터 |
| Key | 객체 이름 |
| Metadata | 객체 정보 |

---

# 3. S3 버킷 생성 실습

## 3.1 S3 콘솔 접속

```
AWS Console → S3
```

버킷 생성

```
버킷 만들기
```

버킷 설정

```
버킷 이름
이니셜-s3-bucket-{ACCOUNT_ID}
```

리전

```
ap-northeast-2
```

버킷 생성 클릭

---

# 4. 테스트 파일 업로드

버킷 선택

```
이니셜-s3-bucket-{ACCOUNT_ID}
```

업로드

```
업로드
 → 파일 추가
```

테스트 HTML 생성

```
index.html
```

내용

```
<html>
<body>
<h1>S3 Access Control Test</h1>
</body>
</html>
```

업로드

---

# 5. 객체 접근 테스트

객체 클릭

```
index.html
```

객체 URL 확인

```
https://이니셜-s3-bucket-ACCOUNT_ID.s3.ap-northeast-2.amazonaws.com/index.html
```

브라우저 접속

결과

```
AccessDenied
```

S3 기본 권한은 **Private**이다.

---

# 6. ACL 기반 접근제어 실습

ACL은 객체 단위 접근제어 방식이다.

## 6.1aws ACL 활성화

버킷

```
권한 탭
```

객체 소유권

```
편집
```

설정

```
ACL 활성화
```

저장

---

## 6.2 Public Access Block 비활성화

권한 탭

```
퍼블릭 액세스 차단
```

편집

다음 체크 해제

```
모든 퍼블릭 액세스 차단
```

저장

---

## 6.3 객체 Public 설정

객체 선택

```
작업
 → ACL을 사용하여 퍼블릭으로 설정
```

설정

```
퍼블릭 읽기 허용
```

---

## 6.4 접근 테스트

객체 URL 접속

```
브라우저
```

결과

```
파일 정상 출력
```

---

# 7. Bucket Policy 기반 접근제어

ACL은 객체 단위 제어이다.

Bucket Policy는 **버킷 단위 정책 제어 방식**이다.

---

## 7.1 Bucket Policy 설정

S3 콘솔

```
버킷
 → 권한
 → 버킷 정책
 → 편집
```

정책 입력

```
{
 "Version":"2012-10-17",
 "Statement":[
  {
   "Effect":"Allow",
   "Principal":"*",
   "Action":"s3:GetObject",
   "Resource":"arn:aws:s3:::이니셜-s3-bucket-ACCOUNT_ID/*"
  }
 ]
}
```

저장

---

## 7.2 접근 테스트

객체 URL 접속

```
브라우저
```

결과

```
파일 정상 접근
```

---

# 8. IAM Role 기반 접근제어

이번 실습은 **EC2 → S3 접근 제어**이다.

---

# 8.1 IAM Role 생성

AWS 콘솔

```
IAM → 역할 → 역할 생성
```

설정

```
신뢰할 수 있는 엔터티
AWS 서비스
```

사용 사례

```
EC2
```

권한 추가

```
AmazonS3FullAccess
```

역할 이름

```
이니셜-role-s3
```

생성

---

# 8.2 EC2에 IAM Role 연결

EC2 콘솔

인스턴스 선택

```
이니셜-ec2-web
```

작업

```
보안
 → IAM 역할 수정
```

선택

```
이니셜-role-s3
```

업데이트

---

# 8.3 EC2에서 S3 접근 테스트

EC2 접속

```
ssh ec2-user@EC2-IP
```

S3 버킷 조회

```
aws s3 ls
```

특정 버킷 조회

```
aws s3 ls s3://이니셜-s3-bucket-ACCOUNT_ID
```

결과

```
index.html
```

---

# 9. Pre-Signed URL 실습

Pre-Signed URL은 **일시적으로 접근을 허용하는 URL**이다.

---

## 9.1 Pre-Signed URL 생성

CLI 실행

```
aws s3 presign s3://이니셜-s3-bucket-ACCOUNT_ID/index.html --expires-in 60
```

설명

```
60초 동안 접근 가능
```

---

## 9.2 접근 테스트

브라우저 접속

```
PreSigned URL
```

결과

```
파일 접근 가능
```

1분 후

```
AccessDenied
```

---

# 10. Static Website Hosting 실습

S3는 정적 웹사이트 서버로 사용할 수 있다.

---

# 10.1 Static Website 활성화

버킷

```
속성
 → Static website hosting
```

설정

```
Enable
```

Index document

```
index.html
```

---

# 10.2 Bucket Policy 설정

정적 웹사이트 접근 허용 정책

```
{
 "Version":"2012-10-17",
 "Statement":[
  {
   "Effect":"Allow",
   "Principal":"*",
   "Action":"s3:GetObject",
   "Resource":"arn:aws:s3:::이니셜-s3-bucket-ACCOUNT_ID/*"
  }
 ]
}
```

---

# 10.3 웹사이트 접속

웹사이트 URL

```
http://이니셜-s3-bucket-ACCOUNT_ID.s3-website-ap-northeast-2.amazonaws.com
```

접속 결과

```
S3 Access Control Test
```

---

# 11. S3 접근제어 방식 비교

| 방식 | 특징 |
| --- | --- |
| ACL | 객체 단위 권한 |
| Bucket Policy | 버킷 정책 기반 제어 |
| IAM Policy | 사용자 / 역할 기반 |
| PreSigned URL | 임시 접근 |
| Static Website | 웹사이트 공개 |

---

# 12. 실습 문제

### 문제 1

다음 버킷 생성

```
이니셜-s3-lab
```

조건

* index.html 업로드

* ACL로 Public 접근 허용

---

### 문제 2

Bucket Policy로 다음 조건 구현

```
특정 객체만 Public 접근
```

---

### 문제 3

PreSigned URL 생성

조건

```
30초 동안만 접근 가능
```