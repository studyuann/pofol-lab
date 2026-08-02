---
title: "AWS Route53 DNS 및 Routing Policy"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "모범사례기반 AWS 고급아키텍처 설계"]
is_public: true
draft: false
---

# AWS Route53 DNS 및 Routing Policy

---

# 1. DNS 개념

DNS는 **도메인 이름을 IP 주소로 변환하는 시스템**이다.

예

```
www.example.com → 54.180.10.20
```

사용자가 웹 브라우저에 도메인을 입력하면 다음 순서로 DNS 조회가 진행된다.

```
사용자 PC
   │
   ▼
Local DNS Resolver
   │
   ▼
Root DNS
   │
   ▼
TLD DNS (.com)
   │
   ▼
Authoritative DNS
(Route53)
   │
   ▼
IP 반환
```

Route53은 **Authoritative DNS 서버 역할**을 한다.

---

# 2. Route53 서비스 개념

Route53은 AWS에서 제공하는 **Managed DNS 서비스**이다.

주요 기능

| 기능 | 설명 |
| --- | --- |
| Domain Registration | 도메인 구매 |
| Hosted Zone | DNS 영역 관리 |
| Record | DNS 레코드 설정 |
| Health Check | 서비스 상태 확인 |
| Routing Policy | 트래픽 제어 |

이번 실습에서 사용할 기능

```
Hosted Zone
DNS Record
Routing Policy
```

---

# 3. 실습 전체 아키텍처

교육 환경 구조

```
                 Internet
                     │
                     │
               example.com
                     │
              Route53 Hosted Zone
                     │
       ┌─────────────┼─────────────┐
       │             │             │
student1.example.com
student2.example.com
student3.example.com
       │
       │
       EC2
```

**자신의 서브도메인을 생성하여 서버를 연결**한다.

---

# 4. 실습 준비

### 1. 외부 도메인 구매

예

```
cloudai.store
```

구매 가능 사이트

```
가비아
Namecheap
GoDaddy
Cloudflare
```

---

# 5. Route53 Hosted Zone 생성

## 5.1 Route53 접속

AWS Console

```
Route53
```

메뉴

```
Hosted zones
```

---

## 5.2 Hosted Zone 생성

클릭

```
Create hosted zone
```

설정

```
Domain name

cloudai.store
```

Type

```
Public Hosted Zone
```

생성

```
Create hosted zone
```

---

## 5.3 생성 결과

Route53이 자동으로 NS 레코드를 생성한다.

예

```
ns-123.awsdns-12.com
ns-234.awsdns-34.net
ns-345.awsdns-56.org
ns-456.awsdns-78.co.uk
```

이 값은 **외부 도메인 DNS 설정에 등록해야 한다.**

---

# 6. 외부 도메인 NS 변경

도메인 구매 사이트에서

```
cloudai.store
```

DNS 설정 변경

기존

```
ns1.provider.com
ns2.provider.com
```

삭제

Route53 NS 등록

```
ns-123.awsdns-12.com
ns-234.awsdns-34.net
ns-345.awsdns-56.org
ns-456.awsdns-78.co.uk
```

---

# 7. DNS 전파 확인

명령어

```
dig NS cloudai.store
```

또는

```
nslookup cloudai.store
```

DNS 전파 시간

```
5~30분
```

---

# 8. 서브도메인 생성

자신의 서브도메인을 생성한다.

예

```
이니셜.cloudai.store
st2.cloudai.store
st3.cloudai.store
```

서브도메인을 호스팅 영역에 등록하고, 생성된 NS 정보를 메인 도메인에 NS레코드로 생성한다.

---

# 9. EC2 웹서버 생성

EC2 생성

이름

```
이니셜-web
```

보안그룹

```
SSH 22
HTTP 80
```

---

# 10. 웹서버 설치

EC2 접속

```
ssh ec2-user@EC2-IP
```

웹서버 설치

```
sudo yum install httpd -y
```

서비스 시작

```
sudo systemctl start httpd
```

자동 시작

```
sudo systemctl enable httpd
```

---

# 11. 웹페이지 생성

```
sudo vi /var/www/html/index
```

내용

```
<h1>이니셜 web server</h1>
```

---

# 12. Route53 DNS 레코드 생성

Route53

```
Hosted zones
```

이동

```
example.com
```

---

## 레코드 생성

클릭

```
Create record
```

설정

```
Record name

student1
```

Type

```
A Record
```

Value

```
EC2 Public IP
```

예

```
54.180.20.10
```

---

# 13. DNS 테스트

```
nslookup 이니셜.cloudai.store
```

또는

```
dig 이니셜.cloudai.store
```

브라우저 접속

```
http://이니셜.cloudai.store
```

---

# 14. Route53 Routing Policy

Routing Policy는 **DNS 트래픽을 제어하는 방식**이다.

주요 정책

| Routing Policy | 설명 |
| --- | --- |
| Simple | 기본 DNS |
| Weighted | 트래픽 비율 분산 |
| Latency | 사용자 위치 기준 |
| Failover | 장애 시 서버 변경 |
| Geolocation | 국가 기준 라우팅 |
| Multi-value | 여러 IP 반환 |

---

# 15. Weighted Routing 실습

Weighted Routing은 **트래픽을 비율로 분산**한다.

예

```
www.이니셜.cloudai.store
     │
 ┌───┴────┐
 │        │
EC2-A   EC2-B
 80%     20%
```

---

## EC2 서버 2개 생성

```
web-a
web-b
```

웹페이지 생성

서버 A

```
<h1>server A</h1>
```

서버 B

```
<h1>server B</h1>
```

---

## Route53 레코드 생성

Record name

```
www.이니셜.cloudai.store
```

Routing Policy

```
Weighted
```

---

### 레코드1

```
Value

EC2-A-IP
```

Weight

```
80
```

---

### 레코드2

```
Value

EC2-B-IP
```

Weight

```
20
```

---

## 테스트

브라우저 새로고침 반복

```
http://www.이니셜.cloudai.store
```

서버 A가 더 많이 나타난다.

---

# 16. Failover Routing 실습

Failover는 **장애 발생 시 서버를 변경**한다.

구조

```
Primary Server
      │
      │ 장애 발생
      ▼
Secondary Server
```

---

## 서버 2개 준비

```
web-primary
web-backup
```

---

## Health Check 생성

Route53

```
Health Checks
```

생성

설정

```
Protocol

HTTP
```

Endpoint

```
Primary server IP
```

---

## DNS 설정

Record name

```
fail.example.com
```

Routing policy

```
Failover
```

---

Primary record

```
Primary server IP
```

Health Check 연결

레코드ID 입력 : Main

---

Secondary record

```
Backup server IP
```

Failover type

```
Secondary
```

레코드ID 입력 : Backup

---

## 테스트

Primary 서버 중지

```
sudo systemctl stop httpd
```

DNS 자동 변경 확인

```
fail.이니셜.cloudai.store
```

Backup 서버로 접속된다.

---

# 17. Latency Routing 실습

Latency Routing은 **사용자와 가장 가까운 리전에 연결**한다.

구조

```
User
 │
 │
 ├─ Asia → ap-northeast-2
 │
 └─ US → us-east-1
```

---

## 서버 생성

```
Seoul EC2
Virginia EC2
```

---

## Route53 설정

Record name

```
latency.이니셜.cloudai.store
```

Routing policy

```
Latency
```

Region 지정

```
ap-northeast-2
us-east-1
```

---

# 18. 다중값 응답 (Multivalue Answer) 실습

다중값 응답 라우팅은 단순 라운드로빈과 비슷해 보이지만, **Health Check와 연동 가능**하다는 점이 중요하다.

상태 확인이 정상인 레코드만 DNS 응답에 포함되며, 최대 8개의 정상 레코드를 무작위로 반환한다.

즉, 다음과 같은 상황에서 유용하다.

* 여러 서버에 트래픽을 분산하고 싶을 때

* 특정 서버 장애 시 DNS 응답에서 자동 제외시키고 싶을 때

* 로드밸런서 없이 간단한 가용성 분산 효과를 확인하고 싶을 때

## 실습 구성

1. 동일한 이름으로 A 레코드 2개를 생성한다.

2. 두 레코드 모두 라우팅 정책을 **다중값 응답**으로 설정한다.

3. 각 레코드에 서로 다른 IP를 입력한다.

4. 필요 시 각 레코드에 **Health Check**를 연결한다.

5. 한쪽 서버를 중지하거나 웹 서비스 응답을 끊어서 DNS 응답에서 해당 IP가 사라지는지 확인한다.

## 실습 절차

### 1) 레코드 생성

Route 53 Hosted Zone으로 이동한 뒤, 동일한 이름의 A 레코드를 2개 만든다.

예시

* 레코드 이름: `api.example.com`

* 레코드 유형: `A`

### 레코드 1

* 값: 서버 1의 공인 IP

* 라우팅 정책: `다중값 응답`

* 레코드 ID: `server-01`

### 레코드 2

* 값: 서버 2의 공인 IP

* 라우팅 정책: `다중값 응답`

* 레코드 ID: `server-02`

## Health Check 연결

각 레코드에 개별적으로 Health Check를 연결할 수 있다.

예를 들어 다음처럼 구성한다.

* `server-01` → EC2-1의 HTTP 상태 확인

* `server-02` → EC2-2의 HTTP 상태 확인

Health Check를 연결하면, 특정 서버가 비정상 상태가 되었을 때 해당 IP는 DNS 응답에서 제외된다.

## 검증 방법

### Linux / macOS

```
dig api.example.com
```

여러 번 반복 실행

```
for i in {1..10}; do dig +short api.example.com; done
```

### Windows

```
nslookup api.example.com
```

## 확인 포인트

* 두 서버가 모두 정상일 때는 두 IP가 번갈아 또는 함께 조회될 수 있음

* 한 서버를 중지하거나 Health Check 실패 상태로 만들면, 해당 IP가 응답에서 제외됨

* 일반 단순 라우팅보다 가용성 측면에서 더 유리함

# 19. IP 기반 (IP-based) 라우팅 실습

## 실습 목적

클라이언트의 **소스 IP 주소 대역(CIDR)** 에 따라 서로 다른 엔드포인트로 라우팅되는 동작을 확인한다.

## 핵심 개념

IP 기반 라우팅은 사용자가 어디에 있는지가 아니라, **어떤 IP 대역에서 접속했는가**를 기준으로 응답을 다르게 준다.

이 방식은 다음과 같은 경우에 적합하다.

* 특정 기업망 사용자만 내부 서비스로 연결하고 싶을 때

* 사무실 네트워크와 외부 사용자를 다르게 분기하고 싶을 때

* 특정 ISP 또는 특정 NAT 대역에 대해 별도 응답을 주고 싶을 때

## 실습 구성

1. Route 53에서 **CIDR 컬렉션(IP 집합)** 을 생성한다.

2. 특정 CIDR 대역에 대해 서버 A로 응답하도록 설정한다.

3. 나머지 요청은 기본값(Default)으로 서버 B에 연결되도록 설정한다.

4. 서로 다른 네트워크에서 질의하여 결과가 달라지는지 확인한다.

## 실습 절차

### 1) CIDR 컬렉션 생성

Route 53 메뉴에서 **IP 집합(CIDR Collections)** 을 생성한다.

예시

* 이름: `MyOfficeNetwork`

* CIDR 범위: `현재 사무실 공인 IP/32`

예

```
203.0.113.10/32
```

단일 공인 IP만 테스트할 경우 `/32`를 사용하면 된다.

여러 대역을 포함하려면 `/24`, `/16`처럼 더 넓은 범위를 사용할 수 있다.

### 2) 레코드 생성

동일한 도메인 이름으로 A 레코드를 생성한다.

예시

* 레코드 이름: `app.example.com`

* 레코드 유형: `A`

### 3) 라우팅 정책 선택

라우팅 정책을 **IP 기반**으로 설정한다.

### 4) 매핑 설정

예시 구성

* `MyOfficeNetwork`에 매칭되면 → 서버 A의 IP 반환

* 매칭되지 않으면(Default) → 서버 B의 IP 반환

예시 시나리오

* 사무실 네트워크 사용자 → `10.10.10.10`

* 외부 사용자 → `20.20.20.20`

## 검증 방법

서로 다른 네트워크에서 동일한 도메인에 대해 조회한다.

### Linux / macOS

```
dig app.example.com
```

### Windows

```
nslookup app.example.com
```

## 확인 포인트

* 사무실 IP 대역에서 조회하면 서버 A로 연결됨

* 다른 네트워크에서 조회하면 기본값인 서버 B로 연결됨

* 위치 기반 라우팅과 달리, 지리적 위치가 아니라 **소스 IP 대역** 자체가 기준임

## 정리

IP 기반 라우팅은 사용자 그룹을 네트워크 기준으로 구분할 때 매우 직관적이다.

기업망, 협력사망, 관리자망처럼 **명확한 CIDR 대역이 있는 환경**에서 특히 유용하다.

---

# 20. 지리 근접성 (Geoproximity) 라우팅 실습

## 실습 목적

리소스가 배치된 지리적 위치를 기준으로 사용자를 가장 가까운 엔드포인트로 유도하고, **Bias(편향값)** 설정에 따라 특정 리전의 커버리지를 넓히거나 줄이는 동작을 확인한다.

## 핵심 개념

지리 근접성 라우팅은 사용자의 위치와 리소스의 위치를 비교해 더 가까운 쪽으로 응답한다.

여기에 **Bias** 값을 적용하면 특정 리전이 담당하는 영역을 의도적으로 확장하거나 축소할 수 있다.

즉, 단순히 가까운 리전으로 보내는 것에서 끝나는 것이 아니라, 운영자가 정책적으로 트래픽 범위를 조정할 수 있다.

## 준비물

* 서로 다른 리전에 배치된 엔드포인트 2개
  + 예: 서울 리전 ALB
  + 예: 버지니아 리전 ALB

* Route 53 Hosted Zone

* 가능하다면 위치 변경 테스트를 위한 VPN 또는 해외 테스트 환경

## 실습 구성

1. 동일 도메인에 대해 지리 근접성 라우팅 레코드를 2개 만든다.

2. 서울 리전 엔드포인트와 버지니아 리전 엔드포인트를 각각 연결한다.

3. Bias 값을 조정해 서울 리전의 영향 범위를 확대하거나 축소한다.

4. 접속 위치에 따라 어느 리전으로 응답되는지 확인한다.

## 실습 절차

### 1) 레코드 생성

동일한 도메인 이름으로 2개의 레코드를 생성한다.

예시

* 레코드 이름: `service.example.com`

* 레코드 유형: `A` 또는 `Alias`

### 2) 라우팅 정책 선택

각 레코드의 라우팅 정책을 **지리 근접성**으로 설정한다.

### 3) 엔드포인트 설정

### 레코드 1

* 리전: `ap-northeast-2` (서울)

* 레코드 ID: `Seoul-Endpoint`

### 레코드 2

* 리전: `us-east-1` (버지니아)

* 레코드 ID: `US-Endpoint`

### 4) Bias 설정

서울 리전 레코드의 Bias 값을 `+25`로 설정해본다.

Bias를 양수로 높이면 서울 리전이 담당하는 범위가 넓어진다.

반대로 음수로 설정하면 서울 리전의 영향 범위가 줄어든다.

예를 들어 원래는 다른 리전이 더 가까운 사용자라도, Bias 값 때문에 서울 리전으로 유도될 수 있다.

## 검증 방법

* 한국 또는 일본에서 접속 시 어느 리전으로 연결되는지 확인

* VPN을 통해 미국 또는 동남아 위치로 테스트

* Bias 조정 전후 결과 비교

### 확인용 명령 예시

```
dig service.example.com
```

또는 실제 웹 요청 확인

```
curl http://service.example.com
```

서버별로 서로 다른 식별 문자열을 반환하도록 구성하면 확인이 쉽다.

예

* 서울 서버 응답: `Connected to Seoul`

* 버지니아 서버 응답: `Connected to Virginia`

## 확인 포인트

* 기본적으로 사용자는 더 가까운 리전으로 유도됨

* Bias 값 조정 시 특정 리전의 서비스 범위가 달라짐

* 지리 위치 기반 분산이지만, 운영 목적에 따라 인위적 조정이 가능함

## 정리

지리 근접성 라우팅은 단순 지연시간 최소화 목적뿐 아니라, 특정 리전에 트래픽을 더 많이 유도하거나 줄이기 위한 정책 제어에도 활용할 수 있다.

글로벌 서비스 운영 시 트래픽 분산 전략을 실험하기에 좋은 방식이다.

---