---
title: "AWS WAF Logging 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "모범사례기반 AWS 고급아키텍처 설계"]
is_public: true
draft: false
---

# AWS WAF Logging 실습

## Kinesis Data Firehose를 이용해 S3에 저장하기

---

# 1. 실습 개요

AWS WAF에서 발생한 웹 요청 로그를 Amazon Data Firehose로 전달하고,

최종적으로 Amazon S3 버킷에 저장하는 과정을 실습한다.

실습 흐름은 다음과 같다.

```
Client Request
   │
   ▼
AWS WAF
   │
   ▼
Amazon Data Firehose
   │
   ▼
Amazon S3
```

이 구조를 사용하면 WAF 로그를 장기 보관하거나, 이후 Athena, Glue, OpenSearch 같은 서비스와 연계해서 분석할 수 있다.

---

# 2. 실습 목표

이 실습에서 수행할 내용은 다음과 같다.

```
1. WAF 로그 저장용 S3 버킷 생성
2. Amazon Data Firehose 전달 스트림 생성
3. WAF Web ACL Logging 대상에 Firehose 연결
4. 웹 요청 발생 후 S3에 로그 파일이 저장되는지 확인
5. 저장된 로그 JSON 구조를 확인
```

---

# 3. 사전 이해

## 3.1 왜 Firehose를 사용하는가

CloudWatch Logs로 보내면 실시간 조회는 편하지만,

장기 저장과 대용량 분석은 S3가 더 유리한 경우가 많다.

Firehose를 사용하면 다음이 가능하다.

* WAF 로그를 자동으로 S3에 적재

* 버퍼링 후 파일 단위로 저장

* 이후 Athena로 쿼리 가능

* 중앙 로그 저장소 구성 가능

즉, 운영 환경에서는 **보안 로그 보관 및 분석 파이프라인**의 시작점으로 많이 사용한다.

---

## 3.2 AWS WAF와 Firehose 연동 시 중요한 점

AWS 공식 문서 기준으로 WAF 로그를 Amazon Data Firehose로 보내려면 다음 조건을 지켜야 한다.

* Firehose 전달 스트림 이름은 `aws-waf-logs-` 로 시작하는 것이 권장됨

* WAF와 같은 리전에서 Firehose를 생성해야 함

* 단, CloudFront용 WAF 로그를 수집할 때는 `us-east-1` 에 생성해야 함

* Firehose는 `Direct PUT` 방식으로 생성해야 함

이번 실습은 **Regional WAF + ALB 기준**으로 작성하므로,

서울 리전이라면 서울 리전에 Firehose를 생성하면 된다.

---

# 4. 실습 환경

예시 환경은 다음과 같다.

```
Internet
   │
   ▼
Application Load Balancer
   │
   ▼
EC2 Web Server
```

여기에 WAF를 연결한 뒤, 로그 저장 경로를 아래처럼 구성한다.

```
AWS WAF
   │
   ▼
Amazon Data Firehose Delivery Stream
   │
   ▼
Amazon S3 Bucket
```

---

# 5. 실습 1. S3 버킷 생성

---

## 5.1 S3 콘솔 이동

다음 메뉴로 이동한다.

```
AWS Console → S3 → Create bucket
```

---

## 5.2 버킷 생성

다음과 같이 입력한다.

### Bucket name

```
my-waf-log-bucket-고유이름
```

예

```
my-waf-log-bucket-seoul-001
```

### Region

```
Asia Pacific (Seoul)
```

### 나머지 옵션

기본값 사용

버킷을 생성한다.

---

## 5.3 설명 포인트

이 S3 버킷은 WAF 로그가 직접 저장되는 것이 아니라,

정확히는 **Firehose가 전달한 로그 파일을 저장하는 최종 목적지**다.

즉 역할을 구분하면 다음과 같다.

```
WAF = 로그 생성
Firehose = 로그 전달/버퍼링
S3 = 로그 저장소
```

---

# 6. 실습 2. Firehose 전달 스트림 생성

---

## 6.1 Firehose 콘솔 이동

다음 메뉴로 이동한다.

```
AWS Console → Amazon Data Firehose
```

화면에서 다음을 선택한다.

```
Create Firehose stream
```

---

## 6.2 소스 설정

WAF는 Firehose에 직접 로그를 푸시하는 형태로 전달하므로 소스는 **Direct PUT** 방식으로 생성해야 한다.

설정값은 다음과 같이 한다.

### Source

```
Direct PUT
```

### Destination

```
Amazon S3
```

---

## 6.3 전달 스트림 이름 지정

여기서 매우 중요하다.

전달 스트림 이름은 다음처럼 `aws-waf-logs-` 접두사로 시작해야 한다.

예

```
aws-waf-logs-seoul-lab
```

이름 예시를 정리하면 다음과 같다.

```
aws-waf-logs-seoul-lab
aws-waf-logs-alb-prod
aws-waf-logs-demo
```

---

## 6.4 목적지 S3 설정

다음 항목에서 앞에서 만든 버킷을 선택한다.

### S3 bucket

```
my-waf-log-bucket-고유이름
```

### S3 prefix

원하면 다음처럼 폴더 경로를 지정할 수 있다.

```
waf-logs/
```

그러면 S3에는 다음 경로 형태로 저장될 수 있다.

```
s3://my-waf-log-bucket-고유이름/waf-logs/
```

---

## 6.5 버퍼 설정

Firehose는 요청이 들어올 때마다 바로 파일 하나씩 저장하지 않고

일정량을 모아서 S3에 적재한다.

예를 들어 다음과 같이 설정할 수 있다.

### Buffer size

```
5 MiB
```

### Buffer interval

```
300 seconds
```

의미는 다음과 같다.

* 5MiB 이상 쌓이면 저장

* 또는 300초가 지나면 저장

* 둘 중 먼저 만족하는 조건으로 S3에 전달

실습에서는 기본값을 써도 무방하다.

---

## 6.6 IAM Role 설정

Firehose가 S3에 파일을 저장하려면 S3에 쓸 수 있는 권한이 필요하다.

콘솔에서 보통 다음 방식 중 하나를 선택하게 된다.

* 새 IAM Role 자동 생성

* 기존 IAM Role 사용

실습에서는 **자동 생성**을 선택하는 것이 가장 쉽다.

---

## 6.7 Firehose 생성 완료

설정을 검토한 뒤 전달 스트림을 생성한다.

생성 후 상태가 다음처럼 바뀌어야 한다.

```
ACTIVE
```

Firehose는 생성 직후 `CREATING` 상태였다가, 완료되면 `ACTIVE` 상태로 바뀌며 데이터를 받을 수 있게 된다.

---

# 7. 실습 3. WAF Logging 대상에 Firehose 연결

---

## 7.1 WAF 콘솔 이동

다음 메뉴로 이동한다.

```
AWS Console → WAF & Shield → Web ACLs
```

실습에 사용 중인 Web ACL을 선택한다.

예

```
my-waf-lab
```

---

## 7.2 Logging 설정 메뉴 이동

Web ACL 상세 화면에서 다음 메뉴로 이동한다.

```
Logging and metrics
```

이후 다음을 선택한다.

```
Enable logging
```

---

## 7.3 Logging destination 선택

로그 저장 대상을 선택하는 화면에서 다음을 선택한다.

```
Amazon Data Firehose delivery stream
```

그리고 아까 생성한 Firehose 전달 스트림을 선택한다.

예

```
aws-waf-logs-seoul-lab
```

AWS WAF는 로깅을 활성화할 때 대상에 맞는 추가 권한 구성을 자동으로 생성할 수 있다.

---

## 7.4 설명 포인트

이 단계에서 실제 데이터 흐름은 다음처럼 된다.

```
사용자 요청
   ▼
WAF가 요청 검사
   ▼
WAF 로그 생성
   ▼
Firehose Delivery Stream으로 전송
   ▼
Firehose가 버퍼링 후 S3에 파일 저장
```

즉, WAF가 직접 S3에 쓰는 구조가 아니라

**중간 전달 계층으로 Firehose를 사용하는 구조**다.

---

# 8. 실습 4. 트래픽 발생시키기

WAF 로그가 실제로 생성되려면 웹 요청이 발생해야 한다.

---

## 8.1 정상 요청 보내기

ALB DNS 이름을 사용해 요청을 보낸다.

```
curl http://ALB-DNS-이름/
```

예

```
curl http://my-alb-123456.ap-northeast-2.elb.amazonaws.com/
```

이 명령어는 루트 경로 `/` 에 GET 요청을 전송한다.

### 명령어 설명

* `curl`
  + HTTP 요청을 보내는 CLI 도구다.
  + 브라우저 없이 웹 요청을 테스트할 때 사용한다.

* `http://ALB-DNS-이름/`
  + ALB 리스너로 HTTP 요청을 보낸다.
  + ALB 앞단에 WAF가 연결되어 있으면 이 요청은 먼저 WAF를 통과한다.

---

## 8.2 차단 요청도 테스트

예를 들어 SQL Injection 테스트 룰이 이미 설정되어 있다면 다음처럼 요청해볼 수 있다.

```
curl "http://ALB-DNS-이름/search?id=1%27%20OR%20%271%27%3D%271"
```

이 요청이 차단되더라도 로그는 남는다.

---

# 9. 실습 5. S3에 로그 파일 저장 확인

---

## 9.1 S3 버킷 열기

다음 메뉴로 이동한다.

```
AWS Console → S3 → my-waf-log-bucket-고유이름
```

앞에서 지정한 prefix가 있다면 해당 경로를 연다.

예

```
waf-logs/
```

---

## 9.2 로그 파일 확인

Firehose는 로그를 일정 시간 또는 용량만큼 버퍼링한 뒤 저장하므로,

요청 직후 즉시 파일이 보이지 않을 수도 있다.

버퍼 조건이 충족되면 다음과 비슷한 파일 경로가 생성된다.

```
waf-logs/YYYY/MM/DD/HH/파일명
```

실제 파일 이름은 자동 생성된다.

---

## 9.3 파일 다운로드 후 내용 확인

저장된 로그 파일을 다운로드한 뒤 열어보면 JSON 형식의 로그를 확인할 수 있다.

예시 형태는 다음과 비슷하다.

```
{
  "timestamp": 1710000000000,
  "formatVersion": 1,
  "webaclId": "example-web-acl-id",
  "terminatingRuleId": "Default_Action",
  "action": "ALLOW",
  "httpSourceName": "ALB",
  "httpSourceId": "app/my-alb/123456789",
  "httpRequest": {
    "clientIp": "203.0.113.10",
    "country": "KR",
    "uri": "/",
    "args": "",
    "httpMethod": "GET",
    "httpVersion": "HTTP/1.1"
  }
}
```

---

# 10. 로그 필드 해설

실습에서 꼭 읽어봐야 하는 주요 필드는 다음과 같다.

## 10.1 action

요청 처리 결과다.

예

```
ALLOW
BLOCK
COUNT
```

이 값으로 요청이 허용되었는지 차단되었는지 확인할 수 있다.

---

## 10.2 terminatingRuleId

최종적으로 요청 처리를 결정한 규칙 ID다.

예

```
block-specific-ip
block-country
AWS-AWSManagedRulesSQLiRuleSet
Default_Action
```

즉, 어떤 규칙이 요청을 차단했는지 파악할 때 중요하다.

---

## 10.3 clientIp

클라이언트 요청 IP다.

예

```
203.0.113.10
```

이 값을 통해 공격 원점 추적이나, 특정 IP 반복 요청 분석을 할 수 있다.

---

## 10.4 country

IP 기반 국가 코드다.

예

```
KR
US
JP
CN
```

Geolocation 차단 룰을 실습한 경우 특히 중요하게 본다.

---

## 10.5 uri / args

요청 URI와 파라미터다.

예

```
uri = /search
args = id=1' OR '1'='1
```

SQL Injection 같은 공격 패턴 분석 시 이 필드를 본다.

---

# 11. 실습 흐름

```
1. S3 버킷 생성
2. Amazon Data Firehose 전달 스트림 생성
   - Source: Direct PUT
   - Destination: S3
   - Stream name: aws-waf-logs-로 시작
3. WAF Web ACL에서 Logging 활성화
4. Logging 대상에 Firehose 연결
5. 웹 요청 발생
6. Firehose가 로그를 S3에 저장
7. 저장된 JSON 로그 확인
```