---
title: "CloudFront + 일반 S3 Origin 배포 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 아키텍처 설계(ARC)"]
is_public: true
draft: false
---

# CloudFront + 일반 S3 Origin 배포 실습

# 1. 실습 목표

이 실습에서는 S3에 정적 웹 콘텐츠를 업로드하고, CloudFront를 통해 사용자에게 콘텐츠를 배포하는 구조를 구성한다.

이 실습의 핵심 목표는 다음과 같다.

* S3를 정적 콘텐츠 저장소로 사용

* CloudFront를 통해 전 세계 엣지 로케이션에서 콘텐츠 제공

* S3 버킷은 비공개로 유지

* CloudFront만 S3 버킷에 접근 가능하도록 OAC 구성

* HTTPS 기반으로 정적 사이트 제공

* S3 website endpoint 방식과 OAC 방식의 차이 이해

정적 사이트를 안전하게 운영하는 관점에서 보면, **일반 S3 오리진 + OAC** 방식이 보안상 더 적절하다.

---

# 2. 전체 아키텍처

이번 실습에서 구성할 아키텍처는 다음과 같다.

```
사용자
  │
  │ HTTPS 요청
  ▼
CloudFront
  │
  │ OAC
  ▼
Private S3 Bucket
```

이 구조에서 중요한 점은 다음과 같다.

* 사용자는 CloudFront 도메인으로 접속

* CloudFront가 S3 버킷에서 객체를 가져옴

* S3 버킷은 외부에 직접 공개하지 않음

* CloudFront만 버킷 접근 가능

이 구조는 정적 파일을 공개 서비스로 제공하되, **오리진 저장소 자체는 비공개로 보호**하는 형태다.

---

# 3. 먼저 구분해야 하는 두 가지 방식

CloudFront와 S3를 함께 사용할 때는 아래 두 가지 구성을 구분해야 한다.

## 3.1 방식 A: S3 website endpoint 사용

이 방식은 S3의 **Static Website Hosting** 기능을 켜고, 생성된 **website endpoint**를 CloudFront 오리진으로 연결하는 구성이다.

예

```
bucket-name.s3-website-ap-northeast-2.amazonaws.com
```

이 방식의 특징은 다음과 같다.

* S3 website endpoint 사용

* CloudFront에서는 custom origin으로 동작

* 오리진 연결은 HTTP only

* OAC 사용 불가

* 공개 읽기 가능한 객체 구성이 필요

**website endpoint는 HTTPS를 지원하지 않으며**, 이 엔드포인트를 CloudFront 오리진으로 사용할 경우 **custom origin**이 되어 **OAC 또는 OAI를 사용할 수 없다**. 또한 website endpoint는 **공개적으로 읽을 수 있는 콘텐츠만 지원**한다.

## 3.2 방식 B: 일반 S3 버킷 오리진 + OAC 사용

이 방식은 S3의 website endpoint가 아니라, **일반 S3 버킷 자체**를 CloudFront 오리진으로 사용하는 구성이다.

예

```
bucket-name.s3.ap-northeast-2.amazonaws.com
```

이 방식의 특징은 다음과 같다.

* 일반 S3 bucket origin 사용

* OAC 적용 가능

* 버킷 비공개 유지 가능

* CloudFront를 통해서만 접근 가능

* 현재 보안상 권장되는 방식

---

# 4. **일반 S3 버킷 오리진 + OAC 사용**

이 방식을 선택하는 이유는 다음과 같다.

* S3 버킷을 공개하지 않아도 됨

* CloudFront만 오리진 접근 가능

* HTTPS 배포 구조를 자연스럽게 구성 가능

* 실무 운영에 더 적합함

**“정적 파일은 공개 서비스지만, S3 버킷 자체는 공개하지 않는다”**는 점이 핵심이다.

---

# 5. 실습 준비

실습 전에 아래 항목을 준비한다.

* AWS 계정

* 정적 웹 파일
  + `index.html`
  + 필요 시 `style.css`, `app.js`, 이미지 파일

* S3 버킷 생성 권한

* CloudFront 배포 생성 권한

실습에 사용할 기본 파일 예시는 다음과 같다.

## index.html

```
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CloudFront + S3 Test</title>
</head>
<body>
  <h1>Hello CloudFront + S3</h1>
  <p>정적 웹사이트 배포 테스트 페이지</p>
</body>
</html>
```

이 파일은 브라우저에서 정적 페이지가 정상적으로 출력되는지 확인하는 가장 단순한 테스트용 파일이다.

---

# 6. Step 1. S3 버킷 생성

AWS 콘솔에서 S3 버킷을 생성한다.

경로

```
S3 → Create bucket
```

예시 설정

```
Bucket name
이니셜-cf-static-site-001

Region
ap-northeast-2
```

이 실습에서는 S3를 **CloudFront의 오리진 저장소**로 사용할 것이므로, 버킷 이름은 전역적으로 고유해야 한다.

## 주의사항

이번 방식에서는 S3 Static Website Hosting을 반드시 활성화하지 않아도 된다.

오히려 핵심은 **일반 S3 오리진**으로 사용하는 것이다.

즉 이 단계에서는 단순히 정적 파일을 저장할 S3 버킷을 만든다고 이해하면 된다.

---

# 7. Step 2. 퍼블릭 액세스 차단 유지

버킷 생성 시 또는 생성 후 **퍼블릭 액세스 차단(Block Public Access)** 은 유지한다.

확인 항목

```
Block all public access
체크 유지
```

즉 다음 네 가지도 함께 차단 상태로 유지한다.

* Block public ACLs

* Ignore public ACLs

* Block public bucket policies

* Restrict public bucket policies

이번 실습의 핵심은 **S3를 직접 공개하지 않는 것**이다. S3 website hosting 문서에서는 website endpoint 방식으로 공개 사이트를 만들려면 퍼블릭 읽기 구성이 필요하지만, OAC 방식은 그와 다르게 버킷을 비공개로 유지할 수 있다.

---

# 8. Step 3. 정적 파일 업로드

생성한 버킷에 `index.html` 파일을 업로드한다.

경로

```
S3 → 대상 버킷 선택 → Upload
```

업로드 후 버킷 내부에 최소한 다음 파일이 있어야 한다.

```
index.html
```

이 시점에서는 S3 URL로 직접 열리지 않아도 정상이다.

왜냐하면 버킷은 아직 비공개 상태이기 때문이다.

즉 지금은 저장소만 준비한 단계다.

---

# 9. Step 4. CloudFront 배포 생성

이제 CloudFront 배포를 생성한다.

경로

```
CloudFront → Create distribution
```

## 9.1 Origin domain 선택

여기서 가장 중요하다.

**S3 website endpoint를 선택하는 것이 아니라 일반 S3 bucket origin을 선택해야 한다.**

예시

```
Origin domain
이니셜-cf-static-site-001.s3.ap-northeast-2.amazonaws.com
```

만약 `s3-website-...amazonaws.com` 형태를 선택하면 이번 실습 구조와 달라진다.

## 9.2 Origin access 설정

설정값

```
Origin access
Origin access control settings (recommended)
```

새 OAC를 생성하거나 기존 OAC를 선택한다.

이 설정이 바로 CloudFront만 S3 오리진에 접근할 수 있도록 제한하는 핵심이다. AWS CloudFront 시작 가이드에서도 S3 origin에 대해 OAC를 사용하는 배포 생성 절차를 제공한다. ([AWS Docs](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/GettingStarted.SimpleDistribution.html?utm_source=chatgpt.com))

## 9.3 Viewer protocol policy 설정

설정값

```
Viewer protocol policy
Redirect HTTP to HTTPS
```

또는

```
HTTPS only
```

정적 사이트를 배포할 때는 일반적으로 HTTPS 사용을 강제하는 것이 좋다. CloudFront 문서에서도 Viewer Protocol Policy를 통해 HTTPS 강제를 설정할 수 있다고 설명한다. ([AWS Docs](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/using-https-cloudfront-to-s3-origin.html?utm_source=chatgpt.com))

## 9.4 Default root object 설정

설정값

```
Default root object
index.html
```

이 값을 설정하면 CloudFront 도메인 루트(`/`) 접속 시 `index.html` 을 기본 문서로 반환한다.

예를 들어 사용자가 다음 주소로 접속했을 때

```
https://배포도메인/
```

실제로는 `index.html` 이 응답된다.

## 9.5 Cache settings

일반적인 정적 파일 배포 실습이라면 기본 권장 캐시 정책을 사용하면 충분하다.

예

```
Use a recommended cache policy
```

정적 콘텐츠는 변경 빈도가 낮고 캐시 효율이 높기 때문에 기본 권장 정책으로 시작해도 무리가 없다.

---

# 10. Step 5. 버킷 정책 반영

CloudFront에서 OAC를 사용하면 콘솔이 자동으로 버킷 정책 적용을 제안하는 경우가 많다.

자동 적용이 되지 않았다면 수동으로 추가한다.

예시 정책은 다음과 같다.

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCloudFrontServicePrincipalReadOnly",
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudfront.amazonaws.com"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::이니셜-cf-static-site-001/*",
      "Condition": {
        "StringEquals": {
          "AWS:SourceArn": "arn:aws:cloudfront::123456789012:distribution/배포ID"
        }
      }
    }
  ]
}
```

## 정책 설명

### `Principal`

CloudFront 서비스 자체를 의미한다.

```
"Service": "cloudfront.amazonaws.com"
```

즉 모든 사용자가 아니라 CloudFront 서비스만 이 버킷에 접근 가능하게 하는 것이다.

### `Action`

허용할 작업은 `s3:GetObject` 이다.

즉 객체 읽기만 허용한다.

### `Resource`

버킷 내부 모든 객체를 의미한다.

```
arn:aws:s3:::버킷이름/*
```

### `Condition`

특정 CloudFront 배포에서 오는 요청만 허용하기 위한 조건이다.

```
"AWS:SourceArn": "arn:aws:cloudfront::계정ID:distribution/배포ID"
```

이 조건 덕분에 다른 CloudFront 배포나 다른 주체는 접근할 수 없다.

---

# 11. Step 6. CloudFront 배포 완료 후 테스트

배포 생성 후 CloudFront가 배포를 완료하면 도메인 이름이 발급된다.

예

```
d123exampleabcd.cloudfront.net
```

브라우저에서 다음 주소로 접속한다.

```
https://d123exampleabcd.cloudfront.net
```

정상이라면 `index.html` 내용이 표시된다.

## 확인 포인트

* S3 객체는 비공개 상태

* CloudFront 주소로는 정상 접속

* 사용자는 HTTPS로 접속

* 실제 오리진 저장소는 CloudFront만 접근 가능

이 구조가 이번 실습의 핵심 결과다.

---

# 12. Step 7. 직접 S3 접근 차단 확인

이제 CloudFront를 거치지 않고 직접 S3에 접근이 되는지 확인한다.

예를 들어 S3 객체 URL을 직접 열어본다.

```
https://이니셜-cf-static-site-001.s3.ap-northeast-2.amazonaws.com/index.html
```

또는 브라우저/CLI에서 직접 접근을 시도해본다.

정상적인 OAC 구성이라면 **직접 접근은 실패하거나 AccessDenied가 나와야 한다.**

이 테스트를 통해 다음을 확인할 수 있다.

* 버킷이 공개되지 않았음

* CloudFront만 오리진 접근 가능함

* CloudFront가 보안 경계 역할을 수행함

---

# 13. Step 8. 파일 변경 후 캐시 동작 확인

정적 웹사이트에서는 캐시 동작도 함께 이해하는 것이 좋다.

예를 들어 `index.html` 의 내용을 수정해 다시 업로드한다.

수정 예시

```
<h1>Hello CloudFront + S3 - Version 2</h1>
```

업로드 후 즉시 CloudFront URL로 접속했는데 이전 페이지가 보일 수 있다.

이유는 CloudFront 엣지에 기존 객체가 캐시되어 있을 수 있기 때문이다.

이 경우 두 가지 방법이 있다.

## 방법 1. 캐시 만료 대기

캐시 정책 TTL에 따라 일정 시간이 지나면 새 객체가 반영된다.

## 방법 2. Invalidation 실행

CloudFront에서 캐시 무효화를 수행한다.

경로

```
CloudFront → Distribution → Invalidations → Create invalidation
```

입력값

```
/*
```

또는 특정 파일만 지정

```
/index.html
```

이 작업은 캐시된 객체를 강제로 무효화해서 새 콘텐츠를 더 빨리 반영하는 데 사용한다.

---

# 14. 자주 발생하는 문제

# 14.1 Access Denied 발생

원인 후보는 다음과 같다.

* 버킷 정책이 누락됨

* SourceArn이 잘못됨

* CloudFront OAC가 제대로 연결되지 않음

* 오리진을 website endpoint로 잘못 선택함

특히 가장 많이 하는 실수는 다음이다.

* CloudFront 오리진을 `s3-website-...` 로 선택함

* 그런데 OAC를 적용하려고 함

이 조합은 맞지 않는다.

# 14.2 HTTPS는 되는데 파일이 안 보임

확인 항목

* Default root object가 `index.html` 로 설정되어 있는지

* 실제 버킷에 `index.html` 이 업로드되어 있는지

* 대소문자가 일치하는지

# 14.3 콘텐츠 수정 후 반영이 늦음

원인

* CloudFront 캐시 유지 중

해결

* Invalidation 수행

* 객체 버전 관리 방식 사용
  + 예: `app.v2.js`

---

# 15. 비교용: website endpoint 방식은 어떻게 다른가

이번 실습은 OAC 방식이지만, 비교를 위해 website endpoint 방식도 정리해둘 필요가 있다.

## 15.1 website endpoint 방식의 특징

* S3 Static Website Hosting 사용

* S3 website endpoint 사용

* 오리진은 custom origin

* HTTP only

* OAC 불가

* 공개 읽기 정책 필요

## 15.2 언제 사용할 수 있는가

다음과 같은 경우에만 제한적으로 사용할 수 있다.

* 공개용 정적 사이트

* 보안보다 간단한 웹 호스팅 동작이 우선인 경우

* S3의 website redirect 기능이 꼭 필요한 경우

* index / error document 기능을 S3 website hosting 자체에 의존하는 경우

---

# 16. 최종 정리

이번 실습에서 기억해야 할 핵심은 다음과 같다.

* CloudFront + S3 정적 배포에는 두 가지 방식이 있음

* **S3 website endpoint 방식**
  + 공개 읽기 필요
  + HTTP only
  + OAC 불가

* **일반 S3 origin + OAC 방식**
  + S3 비공개 유지 가능
  + CloudFront만 오리진 접근 가능
  + 실무 권장 방식

즉 정적 웹사이트를 안전하게 배포하려면

**S3는 비공개로 두고, CloudFront에 OAC를 적용해 배포하는 방식**으로 이해하면 된다.

---

# 17. 실습 체크리스트

실습 완료 후 아래 항목을 확인한다.

* S3 버킷 생성 완료

* 퍼블릭 액세스 차단 유지

* `index.html` 업로드 완료

* CloudFront 배포 생성 완료

* 일반 S3 오리진 선택 완료

* OAC 적용 완료

* 버킷 정책 반영 완료

* CloudFront 도메인으로 HTTPS 접속 성공

* 직접 S3 접근 차단 확인 완료

* 파일 수정 후 Invalidation 동작 확인 완료

---