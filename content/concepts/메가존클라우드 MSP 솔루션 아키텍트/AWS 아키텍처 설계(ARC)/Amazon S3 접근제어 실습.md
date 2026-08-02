---
title: "Amazon S3 접근제어 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 아키텍처 설계(ARC)"]
is_public: true
draft: false
---

# Amazon S3 접근제어 실습

# 1. 실습 목표

이 실습에서는 Amazon S3에서 제공하는 여러 가지 접근제어 방식을 직접 구성하고 비교한다.

S3는 단순히 파일을 저장하는 서비스처럼 보이지만, 실제 운영에서는 **누가**, **어떤 방식으로**, **얼마 동안**, **어디서** 접근할 수 있는지를 정교하게 제어해야 한다.

이 실습은 그 제어 방식을 단계별로 이해하는 데 목적이 있다.

실습을 통해 다음 내용을 익힌다.

* S3 Bucket 생성

* S3 객체 업로드

* 기본 Private 동작 확인

* ACL 기반 접근제어

* Bucket Policy 기반 접근제어

* IAM Role 기반 접근제어

* Pre-Signed URL 기반 임시 접근

* Static Website Hosting 구성

---

# 2. S3 기본 구조 이해

S3는 **Object Storage** 서비스이다.

즉, 운영체제의 디렉터리와 파일 시스템처럼 동작하는 것이 아니라,

버킷 안에 객체를 저장하는 구조로 동작한다.

구조는 다음과 같다.

```
S3
 └ Bucket
     └ Object
          ├ image.jpg
          ├ log.txt
          └ index.html
```

S3의 핵심 구성요소는 다음과 같다.

| 구성요소 | 설명 |
| --- | --- |
| Bucket | 객체를 저장하는 논리적 컨테이너 |
| Object | 실제 저장되는 파일 데이터 |
| Key | 객체의 이름. 경로처럼 보이지만 실제로는 문자열 키 |
| Metadata | 객체에 대한 부가 정보 |
| Version | 버전 관리 사용 시 객체 변경 이력 |
| Policy | 접근제어를 위한 정책 |

## 2.1 S3에서 알아둘 점

### 1) Bucket 이름은 전역적으로 유일해야 한다

S3 버킷 이름은 AWS 전체에서 고유해야 한다.

다른 계정이 이미 사용 중인 이름은 사용할 수 없다.

예를 들어 다음 이름은 누군가가 먼저 만들었다면 사용할 수 없다.

```
my-bucket
test-bucket
s3-demo
```

따라서 실습에서는 보통 계정 ID나 이니셜을 포함해서 이름을 만든다.

예

```
abc-s3-bucket-123456789012
```

---

### 2) S3는 기본적으로 Private이다

버킷을 만들고 객체를 올렸다고 해서 바로 외부 공개되지 않는다.

기본적으로는 버킷도 객체도 외부에서 접근할 수 없도록 막혀 있다.

즉, 다음 URL 형식이 존재하더라도 바로 열리는 것이 아니다.

```
https://버킷명.s3.리전.amazonaws.com/객체명
```

권한이 없으면 다음과 같은 결과가 나온다.

```
AccessDenied
```

---

### 3) S3의 폴더는 실제 폴더가 아니다

S3 콘솔에서는 폴더처럼 보이지만, 실제로는 폴더 구조가 저장되는 것이 아니다.

객체의 Key 값에 `/` 문자가 들어가 있어서 폴더처럼 보이는 것이다.

예를 들어 다음 객체는

```
images/photo.jpg
```

실제로는 `images` 폴더와 `photo.jpg` 파일이 따로 존재하는 것이 아니라,

`images/photo.jpg` 라는 하나의 Key를 가진 객체이다.

---

# 3. 실습 아키텍처

이번 실습에서 다루는 접근 방식은 다음과 같다.

```
[사용자 브라우저]
      │
      ├─(공개 접근)──────────────→ [S3 Bucket]
      │
      ├─(Pre-Signed URL)────────→ [S3 Object]
      │
      └─(Website Endpoint)──────→ [S3 Static Website]

[EC2 Instance + IAM Role]
      │
      └─(AWS API 호출)──────────→ [S3 Bucket]
```

각 방식의 의미는 다음과 같다.

* 사용자 브라우저가 직접 S3 객체에 접근할 수 있음

* EC2는 IAM Role을 사용해 S3 API를 호출할 수 있음

* Pre-Signed URL은 제한된 시간 동안만 객체 접근을 허용함

* Static Website Hosting은 S3를 정적 웹사이트 서버처럼 사용할 수 있게 함

---

# 4. S3 버킷 생성 실습

## 4.1 S3 콘솔 접속

AWS Management Console에 로그인한 뒤 S3 서비스로 이동한다.

```
AWS Console → S3
```

이후 다음 버튼을 클릭한다.

```
버킷 만들기
```

---

## 4.2 버킷 생성 설정

다음과 같이 입력한다.

```
버킷 이름
이니셜-s3-bucket-{ACCOUNT_ID}
```

예시

```
kyt-s3-bucket-123456789012
```

리전은 다음과 같이 선택한다.

```
ap-northeast-2
```

즉, 서울 리전에 생성한다.

---

## 4.3 주요 설정 설명

버킷 생성 화면에는 다양한 옵션이 보이는데, 이번 실습에서는 아래 개념을 이해하는 것이 중요하다.

### 객체 소유권(Object Ownership)

기본적으로는 ACL을 비활성화하는 방향이 권장된다.

AWS는 최근 운영 방식에서 ACL보다 **Bucket Policy + IAM Policy** 중심의 제어를 더 권장한다.

하지만 이번 실습에서는 ACL 동작도 확인해야 하므로,

초반에는 기본 상태로 버킷을 만들고, 이후 ACL 실습 단계에서 관련 설정을 변경한다.

---

### 퍼블릭 액세스 차단(Block Public Access)

이 옵션은 S3 버킷이 실수로 외부에 공개되는 것을 막기 위한 안전장치이다.

기본적으로 활성화되어 있으며,

이 상태에서는 ACL이나 Bucket Policy로 공개 설정을 넣어도 실제 공개가 차단될 수 있다.

즉, 다음 구조로 이해하면 된다.

```
ACL / Bucket Policy 로 공개를 허용하려고 해도
Block Public Access 가 막고 있으면 외부 공개되지 않음
```

---

## 4.4 버킷 생성 완료

설정을 확인한 뒤 버킷을 생성한다.

```
버킷 만들기
```

생성이 완료되면 S3 버킷 목록에서 생성한 버킷을 확인한다.

---

# 5. 테스트 파일 업로드

## 5.1 버킷 선택

생성한 버킷을 클릭한다.

```
이니셜-s3-bucket-{ACCOUNT_ID}
```

---

## 5.2 업로드 메뉴 진입

다음 메뉴를 선택한다.

```
업로드
 → 파일 추가
```

---

## 5.3 테스트 HTML 파일 생성

실습용으로 간단한 HTML 파일을 하나 만든다.

파일명

```
index.html
```

내용

```
<html>
<body>
<h1>S3 Access Control Test</h1>
<p>This file is stored in Amazon S3.</p>
</body>
</html>
```

이 파일은 브라우저에서 열렸을 때 간단한 텍스트가 보이도록 만든 것이다.

---

## 5.4 업로드 완료

파일을 선택한 뒤 업로드를 진행한다.

업로드가 끝나면 버킷 내부에 `index.html` 객체가 생성된다.

---

# 6. 객체 접근 테스트

## 6.1 객체 URL 확인

업로드한 객체를 클릭한다.

```
index.html
```

객체 상세 화면에서 URL을 확인한다.

예시 형식

```
https://이니셜-s3-bucket-ACCOUNT_ID.s3.ap-northeast-2.amazonaws.com/index.html
```

---

## 6.2 브라우저에서 접근

복사한 URL을 브라우저에서 열어본다.

결과는 보통 다음과 같다.

```
AccessDenied
```

---

## 6.3 왜 AccessDenied가 발생하는가

이 단계에서 중요한 개념은 다음과 같다.

* 객체는 업로드되었음

* URL도 존재함

* 하지만 외부 사용자에게 읽기 권한이 없음

즉, **S3 객체가 존재하는 것**과 **외부에서 접근 가능한 것**은 전혀 다른 문제이다.

이 단계는 앞으로 ACL, Bucket Policy, Pre-Signed URL을 적용했을 때

무엇이 달라지는지를 비교하기 위한 기준점 역할을 한다.

---

# 7. ACL 기반 접근제어 실습

ACL은 Access Control List의 약자이다.

객체 또는 버킷 단위에서 읽기/쓰기 권한을 부여하는 오래된 방식이다.

현재 AWS에서는 ACL보다 Bucket Policy와 IAM 방식을 더 권장하지만,

기존 환경이나 구조를 이해하려면 ACL의 동작도 알아둘 필요가 있다.

---

## 7.1 ACL 방식의 특징

ACL은 다음과 같은 특징을 가진다.

* 객체 단위 제어가 가능함

* 퍼블릭 읽기 같은 단순 공개에 사용할 수 있음

* 관리가 복잡해질 수 있음

* 최근 운영 방식에서는 권장도가 낮아졌음

즉, 실습 목적상 이해는 필요하지만

실무에서는 Bucket Policy와 IAM 중심으로 설계하는 경우가 많다.

---

## 7.2 ACL 활성화

버킷의 권한 탭으로 이동한다.

```
권한 탭
```

객체 소유권 항목을 찾는다.

```
객체 소유권
 → 편집
```

여기서 ACL을 사용할 수 있도록 설정한다.

```
ACL 활성화
```

저장한다.

---

## 7.3 Public Access Block 비활성화

다음 항목으로 이동한다.

```
권한 탭
 → 퍼블릭 액세스 차단
 → 편집
```

다음 설정을 해제한다.

```
모든 퍼블릭 액세스 차단
```

저장한다.

### 왜 이 작업이 필요한가

ACL로 퍼블릭 공개를 허용하더라도

Block Public Access가 켜져 있으면 실제 공개가 차단될 수 있다.

즉, 다음 순서가 필요하다.

1. ACL 사용 가능하도록 설정

2. 퍼블릭 차단 기능 해제

3. 객체에 퍼블릭 읽기 부여

---

## 7.4 객체 Public 설정

버킷 안의 객체 목록에서 `index.html`을 선택한다.

다음 메뉴를 선택한다.

```
작업
 → ACL을 사용하여 퍼블릭으로 설정
```

설정은 다음과 같이 한다.

```
퍼블릭 읽기 허용
```

이제 이 객체는 외부 사용자가 읽을 수 있도록 설정된 상태가 된다.

---

## 7.5 접근 테스트

다시 객체 URL을 브라우저에서 연다.

```
https://이니셜-s3-bucket-ACCOUNT_ID.s3.ap-northeast-2.amazonaws.com/index.html
```

결과

```
파일 정상 출력
```

즉, HTML 내용이 브라우저에 표시된다.

---

## 7.6 ACL 실습 정리

이 단계에서 확인한 내용은 다음과 같다.

* 기본 상태에서는 외부 접근이 차단됨

* ACL을 사용하려면 객체 소유권 설정을 조정해야 함

* Block Public Access가 켜져 있으면 퍼블릭 공개가 막힘

* 객체에 퍼블릭 읽기를 주면 URL로 직접 접근 가능해짐

---

# 8. Bucket Policy 기반 접근제어

ACL은 객체 중심 제어 방식이고,

Bucket Policy는 버킷에 연결되는 JSON 정책 기반 접근제어 방식이다.

Bucket Policy는 다음과 같은 상황에서 많이 사용한다.

* 버킷 전체 또는 특정 경로에 대한 공개 정책

* 특정 계정 또는 특정 역할 허용

* 특정 조건(IP, VPC Endpoint 등)에 따라 제어

* 웹 정적 호스팅 공개

---

## 8.1 Bucket Policy 개념

Bucket Policy는 버킷 리소스에 직접 붙는 정책이다.

구조는 IAM Policy와 비슷하며,

주로 다음 요소로 구성된다.

| 항목 | 의미 |
| --- | --- |
| Effect | Allow 또는 Deny |
| Principal | 누구에게 적용할 것인지 |
| Action | 어떤 API 동작을 허용/거부할지 |
| Resource | 어떤 리소스에 적용할지 |

---

## 8.2 전체 객체 공개 정책 설정

버킷의 권한 탭으로 이동한다.

```
버킷
 → 권한
 → 버킷 정책
 → 편집
```

다음 정책을 입력한다.

```
{
  "Version":"2012-10-17",
  "Statement": [
    {
      "Sid":"AllowPublicReadAllObjects",
      "Effect":"Allow",
      "Principal":"*",
      "Action":"s3:GetObject",
      "Resource":"arn:aws:s3:::이니셜-s3-bucket-ACCOUNT_ID/*"
    }
  ]
}
```

저장한다.

---

## 8.3 정책 설명

위 정책의 의미는 다음과 같다.

* `Principal: "*"`  
  모든 사용자를 의미한다.

* `Action: "s3:GetObject"`  
  객체 읽기 권한을 의미한다.

* `Resource: "arn:aws:s3:::버킷명/*"`  
  해당 버킷 내부 모든 객체에 대해 적용함을 의미한다.

즉, 이 정책은 다음 의미를 가진다.

```
이 버킷 안의 모든 객체를
누구나 읽을 수 있도록 허용한다
```

---

## 8.4 접근 테스트

브라우저에서 다시 객체 URL을 연다.

결과

```
파일 정상 접근
```

---

## 8.5 특정 객체만 공개하는 정책

전체 객체 공개가 아니라, 특정 파일만 공개할 수도 있다.

예를 들어 `index.html`만 공개하려면 다음처럼 작성한다.

```
{
  "Version":"2012-10-17",
  "Statement": [
    {
      "Sid":"AllowPublicReadOnlyIndex",
      "Effect":"Allow",
      "Principal":"*",
      "Action":"s3:GetObject",
      "Resource":"arn:aws:s3:::이니셜-s3-bucket-ACCOUNT_ID/index.html"
    }
  ]
}
```

이 정책을 사용하면 `index.html`만 외부 접근 가능하고,

다른 객체는 여전히 접근이 거부된다.

---

## 8.6 ACL과 Bucket Policy 비교

| 항목 | ACL | Bucket Policy |
| --- | --- | --- |
| 적용 범위 | 객체/버킷 단위 | 버킷 정책 단위 |
| 표현력 | 단순함 | 훨씬 풍부함 |
| 관리 편의성 | 낮음 | 높음 |
| 권장도 | 낮아지는 추세 | 높음 |

실무에서는 보통 Bucket Policy를 더 많이 사용한다.

---

# 9. IAM Role 기반 접근제어

이번 단계에서는 외부 공개가 아니라

**AWS 내부 리소스가 권한을 가지고 S3에 접근하는 방식**을 확인한다.

대표적인 예가 EC2가 IAM Role을 통해 S3에 접근하는 구조이다.

이 방식은 매우 중요하다.

왜냐하면 서버 안에 Access Key를 직접 저장하지 않고도 AWS 리소스 접근이 가능하기 때문이다.

---

## 9.1 IAM Role이 필요한 이유

EC2에서 AWS CLI를 사용해 S3를 조회하려면 인증이 필요하다.

가장 위험한 방법은 서버 안에 다음을 직접 넣는 것이다.

```
Access Key ID
Secret Access Key
```

이 방식은 키 유출 위험이 크기 때문에 권장되지 않는다.

대신 EC2에 IAM Role을 연결하면,

EC2는 임시 자격 증명을 자동으로 받아 AWS API를 호출할 수 있다.

즉, 다음처럼 이해하면 된다.

```
EC2 인스턴스 자체가 권한을 가진다
```

---

## 9.2 IAM Role 생성

AWS 콘솔에서 이동한다.

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

권한은 실습 편의를 위해 다음을 선택한다.

```
AmazonS3FullAccess
```

역할 이름

```
이니셜-role-s3
```

생성한다.

### 참고

실무에서는 `AmazonS3FullAccess`처럼 너무 넓은 권한 대신

특정 버킷만 허용하는 최소 권한 정책을 직접 만들어 사용하는 것이 더 적절하다.

---

## 9.3 EC2에 IAM Role 연결

EC2 콘솔로 이동한다.

인스턴스를 선택한다.

```
이니셜-ec2-web
```

다음 메뉴를 선택한다.

```
작업
 → 보안
 → IAM 역할 수정
```

다음 역할을 선택한다.

```
이니셜-role-s3
```

업데이트한다.

---

## 9.4 EC2에서 S3 접근 테스트

EC2에 접속한다.

```
ssh ec2-user@EC2-IP
```

현재 자격 증명이 정상적으로 연결되었는지 확인하려면 다음 명령도 유용하다.

```
aws sts get-caller-identity
```

이 명령은 현재 어떤 IAM 주체로 동작 중인지 확인할 수 있게 해준다.

이후 S3 버킷 목록을 조회한다.

```
aws s3ls
```

특정 버킷 내부를 조회한다.

```
aws s3ls s3://이니셜-s3-bucket-ACCOUNT_ID
```

예상 결과

```
2026-03-21 12:00:00         92 index.html
```

---

## 9.5 객체 다운로드 테스트

다음 명령으로 객체를 EC2로 내려받을 수 있다.

```
aws s3 cp s3://이니셜-s3-bucket-ACCOUNT_ID/index.html .
```

파일 확인

```
cat index.html
```

결과

```
<html>
<body>
<h1>S3 Access Control Test</h1>
<p>This file is stored in Amazon S3.</p>
</body>
</html>
```

---

# 10. Pre-Signed URL 실습

Pre-Signed URL은

권한이 없는 사용자에게도 **정해진 시간 동안만** 객체 접근을 허용하는 방법이다.

이 방식은 매우 자주 사용된다.

예를 들면 다음과 같은 경우이다.

* 다운로드 링크를 일정 시간만 열어주고 싶을 때

* 업로드 가능한 임시 URL을 발급하고 싶을 때

* 객체를 퍼블릭 공개하지 않고도 외부 전달이 필요할 때

---

## 10.1 Pre-Signed URL의 의미

일반 S3 객체 URL은 권한이 없으면 접근할 수 없다.

하지만 Pre-Signed URL은 URL 안에 인증 정보와 만료 시간이 포함되어 있어

해당 시간이 지나기 전까지는 객체 접근이 가능하다.

즉, 다음과 같은 특징을 가진다.

* 버킷을 퍼블릭 공개하지 않아도 됨

* 특정 객체만 공유 가능

* 짧은 시간만 허용 가능

* 만료 후 자동 차단됨

---

## 10.2 Pre-Signed URL 생성

AWS CLI에서 다음 명령을 실행한다.

```
aws s3 presign s3://이니셜-s3-bucket-ACCOUNT_ID/index.html--expires-in60
```

설명

* `presign` : 서명된 URL 생성

* `s3://버킷명/객체명` : 대상 객체 지정

* `-expires-in 60` : 60초 동안 유효

실행 결과로 긴 URL이 출력된다.

예시 형식

```
https://이니셜-s3-bucket-ACCOUNT_ID.s3.amazonaws.com/index.html?X-Amz-Algorithm=...
```

---

## 10.3 접근 테스트

출력된 URL을 브라우저에 붙여넣고 접속한다.

결과

```
파일 접근 가능
```

약 1분이 지난 후 다시 같은 URL에 접근하면

다음과 같이 만료되어 접근이 거부된다.

```
AccessDenied
```

또는 서명 만료 관련 오류 메시지가 표시될 수 있다.

---

## 10.4 30초짜리 URL 생성 예시

문제 실습과 연결해서 30초 URL도 만들 수 있다.

```
aws s3 presign s3://이니셜-s3-bucket-ACCOUNT_ID/index.html--expires-in30
```

# 11. Static Website Hosting 실습

S3는 정적 웹사이트를 호스팅하는 기능을 제공한다.

여기서 정적 웹사이트란 다음과 같은 파일로 구성된 사이트를 말한다.

* HTML

* CSS

* JavaScript

* 이미지 파일

즉, 서버 측 애플리케이션 실행 없이

정적인 파일만 제공하는 웹사이트를 의미한다.

---

## 11.1 일반 객체 URL과 Website Endpoint의 차이

S3에는 두 가지 접근 관점이 있다.

### 1) 일반 S3 객체 URL

예

```
https://버킷명.s3.ap-northeast-2.amazonaws.com/index.html
```

이 방식은 S3 API 기반 객체 접근이다.

---

### 2) Website Endpoint

예

```
http://버킷명.s3-website-ap-northeast-2.amazonaws.com
```

이 방식은 S3를 웹사이트처럼 동작시키는 엔드포인트이다.

특징은 다음과 같다.

* 기본 문서(index document) 지정 가능

* 오류 문서(error document) 지정 가능

* 웹사이트처럼 URL 접속 가능

* HTTPS가 아니라 HTTP 엔드포인트임

---

## 11.2 Static Website Hosting 활성화

버킷으로 이동한다.

```
속성
 → Static website hosting
```

다음과 같이 설정한다.

```
Enable
```

Index document

```
index.html
```

필요하다면 Error document도 지정할 수 있다.

예

```
error.html
```

저장한다.

---

## 11.3 Bucket Policy 설정

정적 웹사이트가 외부에서 열리려면 객체 읽기 권한이 필요하다.

다음 정책을 적용한다.

```
{
  "Version":"2012-10-17",
  "Statement": [
    {
      "Sid":"PublicReadForWebsite",
      "Effect":"Allow",
      "Principal":"*",
      "Action":"s3:GetObject",
      "Resource":"arn:aws:s3:::이니셜-s3-bucket-ACCOUNT_ID/*"
    }
  ]
}
```

---

## 11.4 웹사이트 URL 접속

Static Website Hosting 설정 후 제공되는 웹사이트 엔드포인트를 확인한다.

형식은 다음과 같다.

```
http://이니셜-s3-bucket-ACCOUNT_ID.s3-website-ap-northeast-2.amazonaws.com
```

브라우저에서 접속하면 `index.html`이 기본 페이지로 표시된다.

예상 결과

```
S3 Access Control Test
This file is stored in Amazon S3.
```

---

## 11.5 실습 포인트

이 단계에서 중요한 점은 다음과 같다.

* 일반 객체 URL과 Website Endpoint는 다름

* S3가 정적 콘텐츠를 제공할 수 있음

* 동적 처리(PHP, JSP, Python 실행 등)는 하지 않음

* 정적 파일 제공 전용 웹 호스팅 방식임

---

# 12. S3 접근제어 방식 비교

| 방식 | 특징 | 사용 목적 |
| --- | --- | --- |
| ACL | 객체 단위 권한 부여 | 단순 공개, 기존 구조 이해 |
| Bucket Policy | 버킷 정책 기반 제어 | 공개/비공개 정책, 조건부 허용 |
| IAM Policy / Role | 사용자·역할 기반 제어 | AWS 리소스 간 안전한 접근 |
| Pre-Signed URL | 시간 제한 임시 접근 | 제한된 공유 |
| Static Website Hosting | 웹사이트 공개 | 정적 사이트 운영 |

---

# 13. 실습 문제

## 문제 1

다음 이름으로 버킷을 생성한다.

```
이니셜-s3-lab
```

조건

* `index.html` 업로드

* ACL 방식으로 Public Read 허용

* 브라우저에서 객체 URL 접속 확인

---

## 문제 2

Bucket Policy를 사용해서 다음 조건을 구현한다.

```
특정 객체만 Public 접근 허용
```

예시

* `index.html` 은 공개

* `private.txt` 는 비공개 유지

### 예시 정책

```
{
  "Version":"2012-10-17",
  "Statement": [
    {
      "Sid":"PublicReadOnlyIndex",
      "Effect":"Allow",
      "Principal":"*",
      "Action":"s3:GetObject",
      "Resource":"arn:aws:s3:::이니셜-s3-lab/index.html"
    }
  ]
}
```

---

## 문제 3

Pre-Signed URL을 생성한다.

조건

```
30초 동안만 접근 가능
```

명령 예시

```
aws s3 presign s3://이니셜-s3-lab/index.html--expires-in30
```

확인 사항

* 생성 직후 브라우저에서 접근 가능해야 함

* 30초 이후 다시 접속하면 만료되어야 함

---

# 14. 정리

* S3는 기본적으로 Private이다

* 공개가 필요하면 ACL 또는 Bucket Policy를 사용할 수 있다

* AWS 리소스 간 접근은 IAM Role 기반으로 구성하는 것이 안전하다

* Pre-Signed URL은 임시 공유에 적합하다

* Static Website Hosting은 정적 웹사이트 제공에 적합하다