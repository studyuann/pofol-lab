---
title: "Cloudfront + S3 Website Endpoint 방식 정적 웹사이트 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 아키텍처 설계(ARC)"]
is_public: true
draft: false
---

# Cloudfront + S3 Website Endpoint 방식 정적 웹사이트 실습

# 1. 실습 목표

이번 실습에서는 S3 버킷을 **정적 웹사이트 호스팅 모드**로 설정하고, S3가 제공하는 **website endpoint**로 직접 웹페이지를 제공하는 구조를 구성한다.

이 실습을 통해 다음을 확인한다.

* S3 Static Website Hosting 활성화

* `index` 과 `error` 설정

* 버킷 퍼블릭 접근 허용

* S3 website endpoint로 직접 접속

* 필요 시 CloudFront를 website endpoint 앞단에 연결

* website endpoint 방식과 OAC 방식의 차이 이해

S3 static website hosting은 버킷을 웹사이트처럼 동작하게 만들 수 있고, 루트 요청 시 index document를 반환하며, 4XX 오류에 대해 custom error document를 지정할 수 있다. 하지만 이 방식은 **공개 콘텐츠 전용**이며 website endpoint는 **HTTPS를 지원하지 않는다**.

---

# 2. 전체 아키텍처

가장 단순한 구조는 다음과 같다.

```
사용자
  │
  │ HTTP 요청
  ▼
S3 Website Endpoint
```

CloudFront를 앞단에 붙이는 경우는 다음과 같다.

```
사용자
  │
  │ HTTPS 요청
  ▼
CloudFront
  │
  │ HTTP only
  ▼
S3 Website Endpoint
```

여기서 중요한 점은 CloudFront를 붙이더라도 오리진은 **S3 website endpoint** 이고, 이 엔드포인트는 HTTPS를 지원하지 않으므로 CloudFront와 오리진 간 통신은 HTTP 기반으로 동작한다. 또한 website endpoint는 custom origin으로 다뤄지므로 OAC/OAI를 사용할 수 없다.

---

# 3. 이 방식의 특징

이 방식은 S3를 웹서버처럼 사용하는 가장 단순한 형태다.

주요 특징은 다음과 같다.

* S3 bucket을 정적 웹 호스팅 용도로 사용

* index document 설정 가능

* error document 설정 가능

* redirect rule 설정 가능

* website endpoint 주소로 직접 접속 가능

* 콘텐츠가 공개 읽기 가능해야 함

* Cloudfront와 S3버킷간에 HTTPS 통신 불가

---

# 4. 실습 준비

이번 실습에서는 최소한 다음 파일을 준비한다.

## index

```
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>S3 Website Endpoint Test</title>
</head>
<body>
  <h1>Hello S3 Website Endpoint</h1>
  <p>정적 웹사이트 테스트 페이지</p>
</body>
</html>
```

## error

```
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Error Page</title>
</head>
<body>
  <h1>오류 페이지</h1>
  <p>요청한 페이지를 찾을 수 없음</p>
</body>
</html>
```

이 파일들은 각각 기본 문서와 오류 문서 테스트용이다.

S3 static website hosting에서는 **index document 지정이 필수**이고, error document는 선택적으로 지정할 수 있다. 파일명은 **대소문자를 정확히 일치**시켜야 한다.

---

# 5. Step 1. S3 버킷 생성

AWS 콘솔에서 S3 버킷을 생성한다.

경로

```
S3 → Create bucket
```

예시 설정

```
Bucket name
이니셜-s3-website-lab-001

Region
ap-northeast-2
```

버킷 이름은 전역적으로 고유해야 한다.

---

# 6. Step 2. 정적 웹사이트 호스팅 활성화

버킷 생성 후 해당 버킷으로 들어간다.

경로

```
S3 → 버킷 선택 → Properties
```

아래로 내려가서 **Static website hosting** 항목을 설정한다.

설정값

```
Static website hosting
Enable

Hosting type
Host a static website

Index document
index

Error document
error
```

설정 후 저장한다.

이 설정을 완료하면 버킷 하단에 **Website endpoint** 가 표시된다.

---

# 7. Step 3. 퍼블릭 액세스 차단 해제

이 방식에서 가장 중요한 부분이다.

S3 website endpoint로 콘텐츠를 제공하려면 객체가 **공개적으로 읽을 수 있어야 한다**.

경로

```
S3 → 버킷 선택 → Permissions
```

**Block public access (bucket settings)** 에서 Edit를 선택하고 다음처럼 변경한다.

```
Block all public access
체크 해제
```

저장할 때 확인 문구를 입력하고 저장한다.

## 이 단계의 의미

이 설정은 “이 버킷을 인터넷에서 누구나 읽을 수 있는 구조로 바꿀 수 있는 상태”를 만든다.

---

# 8. Step 4. 버킷 정책 추가

이제 공개 읽기 정책을 버킷에 추가한다.

경로

```
S3 → 버킷 선택 → Permissions → Bucket policy → Edit
```

예시 정책

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadForWebsite",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::이니셜-s3-website-lab-001/*"
    }
  ]
}
```

## 정책 설명

### `Principal: "*"`

누구나 접근 가능하다는 의미다.

### `Action: "s3:GetObject"`

객체 읽기만 허용한다.

### `Resource`

버킷 내부 모든 객체를 의미한다.

```
arn:aws:s3:::버킷이름/*
```

S3 website endpoint로 정적 사이트를 공개하려면 콘텐츠가 publicly readable 해야 하며, AWS tutorial도 bucket policy를 사용해 공개 읽기 권한을 부여하는 절차를 제공한다.

---

# 9. Step 5. 파일 업로드

버킷에 `index` 과 `error` 파일을 업로드한다.

경로

```
S3 → 버킷 선택 → Upload
```

업로드 후 최소한 다음 두 파일이 존재해야 한다.

```
index
error
```

이제 버킷은 웹사이트처럼 응답할 준비가 된 상태다.

---

# 10. Step 6. Website endpoint 확인

Properties 화면 하단의 Static website hosting 항목에서 **Website endpoint** 주소를 확인한다.

예시 형식

```
http://이니셜-s3-website-lab-001.s3-website.ap-northeast-2.amazonaws.com
```

또는 리전에 따라 다음 형식일 수도 있다.

```
http://bucket-name.s3-website-Region.amazonaws.com
```

---

# 11. Step 7. 브라우저 접속 테스트

브라우저에서 website endpoint 주소로 접속한다.

예

```
http://이니셜-s3-website-lab-001.s3-website.ap-northeast-2.amazonaws.com
```

정상이라면 `index` 내용이 표시된다.

## 확인 포인트

* `Hello S3 Website Endpoint` 문구가 보이는지

* 주소가 `http://` 인지

* `https://` 가 아니라는 점을 확인했는지

S3 website endpoint는 HTTPS를 지원하지 않기 때문에 **반드시 HTTP로 접속**해야 한다. ([AWS Docs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteEndpoints))

---

# 12. Step 8. 오류 페이지 테스트

없는 파일 경로로 접속해서 error document 동작을 확인한다.

예

```
http://이니셜-s3-website-lab-001.s3-website.ap-northeast-2.amazonaws.com/notfound
```

정상이라면 `error` 이 표시된다.

S3 static website hosting은 4XX 오류에 대해 custom error document를 지정할 수 있고, 지정하지 않으면 기본 HTML 오류 문서를 반환한다.

---

# 13. Step 9. CloudFront를 website endpoint 앞단에 연결하는 실습

이제 비교 목적으로 CloudFront를 앞단에 붙여본다.

이 단계의 목적은 “CloudFront를 붙이면 사용자 입장에서는 HTTPS 접속이 가능하지만, 오리진은 여전히 공개 website endpoint”라는 점을 확인하는 것이다. ([AWS Docs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteEndpoints))

경로

```
CloudFront → Create distribution
```

## 13.1 Origin domain 설정

여기서는 일반 S3 bucket origin이 아니라 **website endpoint 주소**를 넣어야 한다.

예

```
이니셜-s3-website-lab-001.s3-website.ap-northeast-2.amazonaws.com
```

## 13.2 Origin type 해석

이 구성은 일반 S3 origin이 아니라 **custom origin**으로 동작한다.

즉 다음이 성립한다.

* OAC 사용 불가

* OAI 사용 불가

* website endpoint가 공개 상태여야 함

## 13.3 Origin protocol policy

설정값

```
HTTP only
```

이유는 S3 website endpoint가 HTTPS를 지원하지 않기 때문이다. ([AWS Docs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteEndpoints))

## 13.4 Default root object

설정값

```
index
```

## 13.5 Viewer protocol policy

설정값

```
Redirect HTTP to HTTPS
```

또는

```
HTTPS only
```

이 설정을 통해 사용자와 CloudFront 사이 구간은 HTTPS로 만들 수 있다.

하지만 CloudFront와 S3 website endpoint 사이 구간은 여전히 HTTP다.

---

# 14. Step 10. CloudFront 접속 테스트

배포 완료 후 CloudFront 도메인으로 접속한다.

예

```
https://d123exampleabcd.cloudfront.net
```

정상이라면 앞서 만든 정적 페이지가 출력된다.

## 이 단계에서 꼭 이해해야 할 점

사용자는 HTTPS로 접속할 수 있지만, 오리진은 여전히 공개 S3 website endpoint다.

즉 CloudFront가 앞단에 있어도 **S3 website endpoint를 직접 아는 사람은 여전히 그 주소로 접근 가능**하다. 이것이 OAC 방식과 가장 큰 차이다.

---

# 15. Route 53 사용자 도메인 연결도 가능한가

가능하다.

다만 여기서도 HTTPS 종단은 CloudFront가 담당하고, S3 website endpoint는 여전히 HTTP 기반 오리진이다.

구조는 다음과 같다.

```
사용자
  │
  │ https://www.example.com
  ▼
Route 53
  │
  ▼
CloudFront
  │
  │ HTTP only
  ▼
S3 Website Endpoint
```

즉 사용자 도메인과 HTTPS를 붙일 수는 있지만, **오리진 비공개화는 되지 않는다**.

website endpoint는 public content만 지원하고 HTTPS도 지원하지 않기 때문이다.

---

# 16. 이 방식의 장점

다음과 같은 경우에는 여전히 이해할 가치가 있다.

* 정적 웹사이트 호스팅 구조를 가장 단순하게 이해할 때

* index / error document 동작을 확인할 때

* redirect rule 기능을 실습할 때

* 공개용 테스트 페이지를 빠르게 배포할 때

S3 website endpoint는 browser-oriented endpoint이고, index document, error document, redirection rule 같은 웹사이트 호스팅 기능을 직접 제공한다.

---

# 17. 이 방식의 한계

* 공개 읽기 구성이 필요함

* Block Public Access 해제가 필요함

* website endpoint 자체는 HTTPS 미지원

* CloudFront를 붙여도 오리진 비공개화 불가

* OAC/OAI 사용 불가

* 보안상 권장되는 표준 구성은 아님

이 방식은 public access가 필요하며, 보다 안전한 정적 사이트 구성을 원하면 **CloudFront OAC 방식**을 사용하라고 권장된다.

---

# 18. OAC 방식과의 비교

| 항목 | S3 Website Endpoint 방식 | 일반 S3 Origin + OAC 방식 |
| --- | --- | --- |
| S3 공개 여부 | 공개 필요 | 비공개 가능 |
| HTTPS 직접 지원 | 불가 | 가능 |
| CloudFront OAC | 불가 | 가능 |
| CloudFront OAI | 불가 | 가능(레거시) |
| Index / Error 문서 | S3에서 직접 처리 | CloudFront 또는 앱 로직으로 처리 |
| 오리진 보안성 | 낮음 | 높음 |
| 권장 여부 | 비교 실습용 | 실무 권장 |

website endpoint는 public content만 지원하고 SSL을 지원하지 않는 반면, regular S3 bucket origin은 OAC로 제한할 수 있다.

---

# 19. 실습 체크리스트

* S3 버킷 생성 완료

* Static website hosting 활성화 완료

* `index` 설정 완료

* `error` 설정 완료

* Block Public Access 해제 완료

* public read bucket policy 적용 완료

* 파일 업로드 완료

* website endpoint HTTP 접속 성공

* 오류 페이지 동작 확인 완료

* 필요 시 CloudFront 연동 완료

* CloudFront HTTPS 접속 성공

* website endpoint 직접 접근 가능 여부 확인 완료

---

# 20. 최종 정리

이번 실습은 **S3 website endpoint 방식이 어떻게 동작하는지 직접 확인하는 실습**이다.

핵심은 다음과 같다.

* S3를 웹사이트처럼 동작하게 할 수 있음

* index / error document 기능을 직접 제공함

* website endpoint는 HTTP만 지원함

* 콘텐츠는 공개 읽기 가능해야 함

* CloudFront를 붙여도 오리진은 비공개가 되지 않음

* 보안상 권장 구조는 **일반 S3 origin + OAC 방식**임

즉 이 방식은 **기능 이해용, 비교용, 공개 정적 페이지 테스트용**으로는 의미가 있지만,

운영 표준 구조로는 앞에서 정리한 **S3 비공개 + CloudFront OAC 방식**을 선택하는 편이 더 적절하다.