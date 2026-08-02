---
title: "AWS WAF 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "모범사례기반 AWS 고급아키텍처 설계"]
is_public: true
draft: false
---

# AWS WAF 실습

---

# 1. 실습 개요

이 실습에서는 AWS WAF를 생성하고, 웹 애플리케이션에 연결한 뒤 다양한 차단 규칙을 적용해 본다.

또한 SQL Injection 공격 패턴을 탐지하는 관리형 규칙을 적용하고, WAF Logging을 통해 차단 로그를 확인한다.

이 실습을 통해 다음 내용을 확인할 수 있다.

* AWS WAF Web ACL 생성

* WAF를 Application Load Balancer 또는 CloudFront에 연결

* 특정 IP 차단

* 특정 국가(Geolocation) 차단

* SQL Injection 공격 탐지 및 차단

* WAF Logging 구성 및 로그 확인

---

# 2. 실습 목표

실습 목표는 다음과 같다.

```
1. AWS WAF Web ACL을 생성할 수 있다.
2. WAF Rule을 이용해 특정 IP를 차단할 수 있다.
3. Geolocation Match를 이용해 특정 국가를 차단할 수 있다.
4. AWS Managed Rules를 이용해 SQL Injection 공격을 탐지 및 차단할 수 있다.
5. WAF Logging을 통해 요청 로그와 차단 로그를 분석할 수 있다.
```

---

# 3. 실습 환경

실습 환경 예시는 다음과 같다.

```
사용자 브라우저
   │
   ▼
Application Load Balancer
   │
   ▼
EC2 Web Server
```

또는 다음 구조도 가능하다.

```
사용자 브라우저
   │
   ▼
CloudFront
   │
   ▼
ALB 또는 S3 Origin
```

이번 실습에서는 보통 **ALB 앞단에 WAF를 연결하는 방식**으로 진행하면 이해하기 쉽다.

---

# 4. WAF 기본 이해

## 4.1 AWS WAF란

AWS WAF는 웹 애플리케이션으로 들어오는 HTTP/HTTPS 요청을 검사해서

허용하거나 차단하는 보안 서비스다.

WAF는 다음과 같은 공격에 대응할 때 많이 사용한다.

* SQL Injection

* Cross Site Scripting(XSS)

* 악성 IP 접근

* 특정 국가에서의 접근

* 비정상적인 패턴의 웹 요청

즉, 네트워크 방화벽처럼 포트 단위로 제어하는 것이 아니라

**웹 요청 자체를 분석해서 제어하는 보안 계층**이다.

---

## 4.2 WAF의 핵심 구성요소

AWS WAF에서 중요한 구성요소는 다음과 같다.

### Web ACL

여러 개의 Rule을 묶어서 보호 대상(ALB, CloudFront 등)에 연결하는 단위다.

```
Web ACL = Rule들의 집합
```

### Rule

트래픽을 검사하는 개별 조건이다.

예

* 특정 IP 차단

* 특정 국가 차단

* SQL Injection 탐지

* 요청 횟수 제한

### Rule Action

Rule에 매칭되었을 때 수행할 동작이다.

* Allow

* Block

* Count

* CAPTCHA

* Challenge

실습에서는 주로 **Block**과 **Count**를 사용한다.

---

# 5. 실습 사전 준비

다음 리소스가 준비되어 있어야 한다.

```
1. VPC
2. Public Subnet
3. EC2 Web Server
4. Application Load Balancer
5. ALB Target Group
6. 테스트 가능한 웹 페이지
```

테스트용 웹 서버는 매우 단순해도 된다.

예

```
<html>
<head><title>WAF Test</title></head>
<body>
<h1>AWS WAF Test Page</h1>
<p>This is a test page.</p>
</body>
</html>
```

EC2에 Apache 또는 Nginx를 올려두고 ALB 뒤에 연결해두면 된다.

---

# 6. 실습 1. AWS WAF Web ACL 생성

---

## 6.1 WAF 콘솔 이동

AWS 콘솔에서 다음으로 이동한다.

```
AWS Console → WAF & Shield
```

왼쪽 메뉴에서 다음을 선택한다.

```
Web ACLs
```

그리고 다음 버튼을 클릭한다.

```
Create web ACL
```

---

## 6.2 Web ACL 기본 설정

다음 값을 입력한다.

### 이름

```
my-waf-lab
```

### 리전

ALB에 연결하는 경우에는 **ALB가 있는 동일 리전**을 선택해야 한다.

예

```
Asia Pacific (Seoul)
```

CloudFront에 연결하는 경우에는 전역 서비스이므로 별도 범위 개념이 다르다.

이번 실습은 ALB 기준으로 진행한다.

### 리소스 유형

```
Regional resources
```

### 연결 대상 리소스

보호할 ALB를 선택한다.

예

```
my-alb
```

---

## 6.3 기본 동작(Default action) 설정

기본 동작은 특별한 Rule에 걸리지 않은 요청을 어떻게 처리할 것인지 정하는 값이다.

보통 다음처럼 설정한다.

```
Default action: Allow
```

의미는 다음과 같다.

* 특별히 차단 룰에 걸리지 않으면 허용

* 필요한 보안 조건에 해당하는 요청만 선별적으로 차단

실무에서도 대부분 이 구조를 많이 사용한다.

---

# 7. 실습 2. 특정 IP 차단

---

## 7.1 IP 차단 방식 이해

특정 IP 또는 IP 대역에서 오는 요청을 차단하려면

먼저 **IP set**을 만든 뒤 Rule에서 참조하는 방식으로 구성한다.

즉 구조는 다음과 같다.

```
IP Set 생성
   ▼
Rule에서 IP Set 참조
   ▼
매칭되면 Block
```

---

## 7.2 IP Set 생성

WAF 콘솔에서 다음으로 이동한다.

```
IP sets → Create IP set
```

다음 값을 설정한다.

### 이름

```
blocked-ip-set
```

### Region

Web ACL과 동일한 리전 선택

### IP version

```
IPv4
```

### IP addresses

예를 들어 차단할 IP가 다음과 같다고 가정한다.

```
203.0.113.10/32
```

단일 IP를 차단할 때 `/32`를 사용한다.

* `/32` = 정확히 1개의 IP

* `/24` = 대역 차단

예시

```
203.0.113.0/24
```

이 경우 `203.0.113.0 ~ 203.0.113.255` 전체 대역을 차단하게 된다.

생성 후 저장한다.

---

## 7.3 Web ACL에 IP 차단 Rule 추가

이제 다시 Web ACL로 이동해서 Rule을 추가한다.

```
Web ACLs → my-waf-lab → Add rules → Add my own rules and rule groups
```

Rule 설정은 다음과 같이 한다.

### Rule name

```
block-specific-ip
```

### Type

```
IP set
```

### IP set 선택

```
blocked-ip-set
```

### Action

```
Block
```

저장 후 Web ACL에 추가한다.

---

## 7.4 동작 확인

차단 대상 IP에서 ALB URL로 접속하면

정상 페이지 대신 차단 응답이 발생해야 한다.

브라우저 또는 curl로 테스트할 수 있다.

예

```
curl http://ALB-DNS-이름
```

차단되면 일반적으로 다음과 유사한 응답이 나타난다.

```
403 Forbidden
```

---

## 7.5 설명 포인트

이 부분에서 반드시 짚어야 할 내용은 다음과 같다.

* Security Group은 IP 차단이 가능하지만 웹 요청 내용은 분석하지 않음

* WAF는 HTTP/HTTPS 레이어에서 동작함

* 특정 악성 IP, 스캐너 IP, 알려진 공격자 IP 차단에 유용함

---

# 8. 실습 3. 특정 국가 차단(Geolocation)

---

## 8.1 Geolocation Match 개념

Geolocation Match는 요청이 들어온 **클라이언트 IP의 국가 정보**를 기준으로 매칭한다.

즉 다음처럼 동작한다.

```
클라이언트 요청
   ▼
IP 기반 국가 판별
   ▼
지정 국가이면 Block
```

예를 들어 한국만 서비스하고 싶다면

특정 국가를 차단하거나 반대로 허용 정책을 세울 수도 있다.

이번 실습에서는 **특정 국가 차단**을 진행한다.

---

## 8.2 Geolocation Rule 생성

Web ACL로 이동해서 Rule을 추가한다.

```
Web ACLs → my-waf-lab → Add rules → Add my own rules and rule groups
```

다음과 같이 설정한다.

### Rule name

```
block-country
```

### Inspect

```
Originates from a country in
```

### Country codes

예시

```
CN
RU
```

또는 콘솔에서 국가명을 직접 선택할 수 있다.

### Action

```
Block
```

추가 후 저장한다.

---

## 8.3 동작 설명

이 Rule은 선택한 국가에서 들어오는 요청을 차단한다.

예

```
중국에서 들어오는 요청 → Block
러시아에서 들어오는 요청 → Block
그 외 국가 요청 → 다른 룰 검사 또는 기본 허용
```

---

## 8.4 설명 포인트

국가 차단은 다음 상황에서 자주 사용된다.

* 서비스 대상 국가가 제한된 경우

* 특정 지역에서의 공격 비율이 매우 높은 경우

* 해외 접근 자체를 최소화하고 싶은 경우

다만 반드시 설명해야 할 점이 있다.

### 주의사항

* VPN, Proxy, CDN 등을 통해 우회 가능할 수 있음

* 국가 차단만으로 완전한 보안이 되지 않음

* 다른 룰과 조합해서 다층 방어를 구성해야 함

---

# 9. 실습 4. SQL Injection 공격 방어

---

## 9.1 SQL Injection이란

SQL Injection은 입력값에 SQL 구문을 삽입해서

데이터베이스 질의를 변조하려는 공격 방식이다.

예를 들어 로그인 입력창, 검색창, URL 파라미터 등에

악의적인 SQL 문장을 넣어 인증 우회나 데이터 조회를 시도할 수 있다.

대표적인 예시는 다음과 같다.

```
' OR '1'='1
```

또는

```
?id=1' OR '1'='1
```

이런 문자열은 입력 검증이 부족한 애플리케이션에서 문제를 일으킬 수 있다.

---

## 9.2 WAF에서 SQL Injection 방어하는 방법

AWS WAF에서는 두 가지 방식이 있다.

```
1. 직접 SQLi Match Rule 작성
2. AWS Managed Rules 사용
```

실습에서는 관리가 쉬운 **AWS Managed Rules**를 사용한다.

특히 다음 Rule Group이 많이 사용된다.

```
AWSManagedRulesCommonRuleSet
```

또는 SQL Injection 관련 Rule이 포함된 관리형 세트를 사용한다.

추가로 좀 더 직접적으로 실습하려면 **SQL database rule statement**를 직접 생성할 수도 있다.

하지만 교육용 실습에서는 관리형 Rule Group을 먼저 쓰는 쪽이 이해하기 쉽다.

---

## 9.3 AWS Managed Rules 추가

Web ACL에서 다음으로 이동한다.

```
Add rules → Add managed rule groups
```

다음 항목을 선택한다.

```
AWS managed rule groups
```

여기서 다음 Rule Group을 추가한다.

예

```
Core rule set
Known bad inputs
SQL database
```

실습 환경에 따라 콘솔에 보이는 이름은 약간 다를 수 있다.

핵심은 **SQL Injection 탐지와 악성 입력 탐지 Rule Group**을 추가하는 것이다.

권장 예시는 다음과 같다.

```
AWSManagedRulesKnownBadInputsRuleSet
AWSManagedRulesSQLiRuleSet
```

각 Rule Group의 Action은 일반적으로 다음처럼 둔다.

```
Use rule actions defined in the rule group
```

대부분 차단(Block) 동작을 포함한다.

---

## 9.4 SQL Injection 테스트용 요청 보내기

테스트는 브라우저 주소창이나 curl로 할 수 있다.

예를 들어 ALB 뒤에 다음과 같은 URL이 있다고 가정한다.

```
http://ALB-DNS-이름/search?id=1
```

이제 다음과 같이 악성 패턴을 넣어본다.

```
curl"http://ALB-DNS-이름/search?id=1' OR '1'='1"
```

또는 URL 인코딩해서 다음처럼 보낼 수 있다.

```
curl"http://ALB-DNS-이름/search?id=1%27%20OR%20%271%27%3D%271"
```

### 명령어 설명

```
curl"http://ALB-DNS-이름/search?id=1%27%20OR%20%271%27%3D%271"
```

* `curl`
  + HTTP 요청을 보내는 명령어다.
  + 웹 브라우저 없이도 GET/POST 요청을 테스트할 때 매우 자주 사용한다.

* `http://ALB-DNS-이름/search?...`
  + ALB로 요청을 보내는 URL이다.
  + `/search`는 예시 경로다.
  + 실제 실습 환경에 맞게 수정해야 한다.

* `%27`
  + 작은따옴표 `'` 의 URL 인코딩 값이다.

* `%20`
  + 공백(space)의 URL 인코딩 값이다.

* `%3D`
  + `=` 문자의 URL 인코딩 값이다.

즉 아래 문자열을 브라우저에서 안전하게 보내기 위해 인코딩한 것이다.

```
1' OR '1'='1
```

---

## 9.5 예상 결과

정상적으로 WAF 규칙이 동작하면 요청은 차단된다.

예상 결과는 다음과 같다.

```
403 Forbidden
```

또는 ALB/WAF 차단 페이지가 나타날 수 있다.

---

## 9.6 실습 포인트

이 실습에서 중요한 점은 다음이다.

* WAF는 애플리케이션 코드 수정 없이도 1차 방어가 가능함

* 하지만 WAF만으로 보안이 끝나는 것은 아님

* 애플리케이션 자체의 입력 검증, Prepared Statement, ORM 보안 설정이 반드시 병행되어야 함

즉 WAF는 **보조적 보호막이 아니라 매우 중요한 전방 방어 계층**이지만,

애플리케이션 보안 대책을 완전히 대체하지는 않는다.

---

# 10. 실습 5. WAF Logging 구성

---

## 10.1 WAF Logging이 필요한 이유

WAF는 차단만 하는 것으로 끝나면 안 된다.

무엇이 차단되었는지, 어느 IP에서 어떤 요청이 들어왔는지, 어떤 Rule에 걸렸는지를 확인해야 한다.

Logging을 구성하면 다음이 가능해진다.

* 차단 이벤트 분석

* 오탐(False Positive) 확인

* 공격 패턴 파악

* 특정 Rule 튜닝

* 보안 감사 자료 확보

---

## 10.2 WAF Logging 대상

AWS WAF Logging은 보통 다음으로 보낼 수 있다.

* CloudWatch Logs

* S3

* Kinesis Data Firehose

실습에서는 **CloudWatch Logs**가 가장 확인하기 쉽다.

---

## 10.3 CloudWatch Logs 로그 그룹 준비

먼저 CloudWatch에서 로그 그룹을 생성한다.

```
AWS Console → CloudWatch → Logs → Log groups → Create log group
```

이름 예시

```
aws-waf-logs-lab
```

저장한다.

---

## 10.4 WAF Logging 활성화

다시 WAF 콘솔로 이동한다.

```
WAF → Web ACLs → my-waf-lab
```

다음 메뉴를 선택한다.

```
Logging and metrics
```

그 다음

```
Enable logging
```

로그 대상에서 CloudWatch Logs를 선택하고

앞에서 만든 로그 그룹을 지정한다.

예

```
aws-waf-logs-lab
```

저장한다.

---

## 10.5 로그 필드 이해

WAF 로그에는 다양한 정보가 기록된다.

대표적으로 다음 항목을 확인할 수 있다.

* 요청 시각

* 클라이언트 IP

* URI

* HTTP Method

* Country

* 적용된 Rule

* Allow / Block 여부

로그 예시는 대략 다음과 같은 JSON 형태다.

```
{
  "timestamp":1710000000000,
  "formatVersion":1,
  "webaclId":"example-web-acl-id",
  "terminatingRuleId":"block-specific-ip",
  "action":"BLOCK",
  "httpSourceName":"ALB",
  "httpSourceId":"app/my-alb/123456789",
  "ruleGroupList": [],
  "httpRequest": {
    "clientIp":"203.0.113.10",
    "country":"KR",
    "uri":"/search",
    "args":"id=1' OR '1'='1",
    "httpVersion":"HTTP/1.1",
    "httpMethod":"GET",
    "requestId":"example-request-id"
  }
}
```

---

## 10.6 로그 확인

CloudWatch Logs에서 해당 로그 그룹으로 이동한 뒤

Log stream을 열어 요청 로그를 확인한다.

확인 포인트는 다음과 같다.

```
action = BLOCK
terminatingRuleId = 어떤 룰이 차단했는가
clientIp = 어느 IP에서 요청했는가
country = 어느 국가에서 들어왔는가
uri / args = 어떤 요청이 들어왔는가
```

---

## 10.7 SQL Injection 차단 로그 확인 포인트

SQL Injection 테스트 후에는 다음을 중점적으로 본다.

* 요청 파라미터에 SQLi 패턴이 들어갔는가

* 어떤 Managed Rule이 탐지했는가

* 최종 action이 BLOCK인가

이 확인 과정이 매우 중요하다.

왜냐하면 실제 운영에서는 단순히 “막았다”보다

**무엇을 근거로 막았는지**를 알아야 Rule 조정이 가능하기 때문이다.

---

# 11. 실습 흐름

```
1. ALB 뒤에 웹 서버 준비
2. WAF Web ACL 생성
3. ALB에 Web ACL 연결
4. 특정 IP 차단 Rule 추가
5. 특정 국가 차단 Rule 추가
6. SQL Injection 방어용 Managed Rule 추가
7. WAF Logging 활성화
8. curl 또는 브라우저로 정상/공격 요청 테스트
9. CloudWatch Logs에서 차단 로그 확인
```

---

# 12. 테스트 시나리오

---

## 시나리오 1. 정상 요청

```
curl http://ALB-DNS-이름/
```

예상 결과

```
정상 페이지 응답
```

---

## 시나리오 2. 특정 IP 차단

차단 대상 IP에서 다음 요청 수행

```
curl http://ALB-DNS-이름/
```

예상 결과

```
403 Forbidden
```

로그 확인 포인트

```
terminatingRuleId = block-specific-ip
action = BLOCK
```

---

## 시나리오 3. 특정 국가 차단

해당 국가 IP 환경에서 접속 시도

예상 결과

```
403 Forbidden
```

로그 확인 포인트

```
country = 차단 대상 국가
terminatingRuleId = block-country
```

---

## 시나리오 4. SQL Injection 테스트

```
curl"http://ALB-DNS-이름/search?id=1%27%20OR%20%271%27%3D%271"
```

예상 결과

```
403 Forbidden
```

로그 확인 포인트

```
Managed Rule Group이 탐지
action = BLOCK
args = 공격 문자열 포함
```

---

# 13. 핵심 내용

## 13.1 WAF와 Security Group 차이

Security Group은 인스턴스 수준의 네트워크 접근 제어를 한다.

주로 포트와 IP 중심이다.

WAF는 HTTP/HTTPS 요청 내용을 검사한다.

즉 웹 애플리케이션 계층 보안에 더 가깝다.

정리하면 다음과 같다.

```
Security Group = L3/L4 중심
WAF = L7 중심
```

---

## 13.2 IP 차단과 Geolocation 차이

* IP 차단은 특정 주소 또는 대역을 직접 차단

* Geolocation은 IP 기반 국가 정보로 차단

둘은 목적이 다르다.

* IP 차단 = 특정 공격자 대응

* 국가 차단 = 지역 기반 접근 통제

---

## 13.3 SQL Injection 방어의 의미

WAF가 SQL Injection 패턴을 차단해 줄 수는 있지만

애플리케이션 코드 자체가 안전해야 진짜 보안이 완성된다.

즉 다음이 함께 필요하다.

* 입력값 검증

* Prepared Statement 사용

* ORM 보안 설정

* 최소 권한 DB 계정 사용

* WAF 적용

---

## 13.4 Logging의 중요성

운영 환경에서는 차단 자체보다 **로그 분석**이 더 중요할 때가 많다.

왜냐하면 다음을 판단해야 하기 때문이다.

* 실제 공격인지

* 정상 사용자가 오탐으로 차단된 것인지

* 어느 Rule이 너무 과하게 동작하는지

* 차단 추세가 증가하는지

따라서 WAF는 반드시 Logging과 함께 운영하는 것이 좋다.

---