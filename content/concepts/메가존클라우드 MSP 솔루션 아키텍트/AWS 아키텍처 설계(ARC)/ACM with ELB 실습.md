---
title: "ACM with ELB 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 아키텍처 설계(ARC)"]
is_public: true
draft: false
---

# ACM with ELB 실습

## 실습 주제

AWS Certificate Manager(ACM)를 이용해 SSL/TLS 인증서를 발급하고, Elastic Load Balancer 중 Application Load Balancer(ALB)에 연결하여 HTTPS 서비스를 제공하는 실습

---

## 실습 목표

이 실습에서는 다음 내용을 수행한다.

* ACM의 역할을 이해한다

* 퍼블릭 인증서를 ACM에서 발급한다

* ALB에 HTTPS 리스너를 구성한다

* HTTP 요청을 HTTPS로 리다이렉트한다

* Route 53을 이용해 도메인을 ALB에 연결한다

* 브라우저에서 HTTPS 접속이 정상적으로 되는지 확인한다

---

## 실습 개요

웹 서비스에서 HTTPS를 사용하려면 인증서가 필요하다.

기존에는 웹 서버(Apache, Nginx)에 직접 인증서를 설치하고 관리하는 경우가 많았음.

하지만 AWS 환경에서는 ACM이 인증서를 관리하고, ALB가 HTTPS 연결을 처리하는 구조를 많이 사용한다.

이 방식에서는 다음과 같이 동작한다.

* 사용자는 HTTPS로 ALB에 접속한다

* ALB가 인증서를 사용자에게 제시한다

* ALB가 TLS 핸드셰이크를 처리한다

* ALB는 백엔드 EC2로 요청을 전달한다

즉, HTTPS 처리를 EC2가 아니라 ALB가 담당하는 구조다.

---

## 아키텍처

```
사용자 브라우저
      │
      │ HTTPS(443)
      ▼
Application Load Balancer
      │
      │ HTTP(80)
      ▼
EC2 Web Server 1
EC2 Web Server 2
```

도메인 연결 구조는 다음과 같다.

```
www.도메인명
    │
    ▼
Route 53 Alias Record
    │
    ▼
ALB DNS Name
    │
    ▼
Target Group
    │
    ▼
EC2 Instances
```

---

## 주요 개념 정리

### ACM이란

ACM(AWS Certificate Manager)은 AWS에서 SSL/TLS 인증서를 발급하고 관리하는 서비스다.

주요 특징은 다음과 같다.

* 퍼블릭 인증서를 무료로 발급 가능

* AWS 서비스와 쉽게 연동 가능

* 자동 갱신 지원

* 인증서를 EC2에 직접 복사하지 않아도 됨

* 인증서 만료 관리 부담이 줄어듦

즉, 운영자가 인증서를 직접 설치하고 갱신하는 수고를 줄여주는 서비스라고 이해하면 된다.

---

### ELB에 인증서를 연결한다는 의미

이번 실습에서는 ELB 중 ALB를 사용한다.

ALB에 인증서를 연결하면 다음이 가능하다.

* 사용자가 `https://도메인명` 으로 접속 가능

* ALB가 TLS 핸드셰이크를 수행함

* 백엔드 EC2는 인증서를 몰라도 됨

* 웹 서버 설정이 단순해짐

즉, 외부 사용자가 보는 HTTPS 종단점은 EC2가 아니라 ALB가 된다.

---

### SSL Termination이란

SSL Termination은 HTTPS 연결을 로드밸런서에서 종료하는 구조를 의미한다.

흐름은 다음과 같다.

1. 사용자가 HTTPS로 ALB에 접속한다

2. ALB가 인증서를 제시한다

3. ALB가 TLS 세션을 종료한다

4. ALB가 백엔드 EC2로 요청을 전달한다

이 구조의 장점은 다음과 같다.

* EC2마다 인증서를 설치할 필요가 없음

* 인증서 관리를 중앙화할 수 있음

* Auto Scaling 환경에서 매우 유리함

* 웹 서버 설정이 단순해짐

---

### 도메인이 필요한 이유

ACM 퍼블릭 인증서는 도메인 검증 과정을 거쳐 발급된다.

즉, 내가 `www.example.com` 인증서를 요청했다면, AWS는 정말 내가 그 도메인을 제어하는지 확인해야 한다.

검증 방식은 보통 다음 두 가지가 있다.

* DNS 검증

* 이메일 검증

실무에서는 대부분 DNS 검증을 사용한다.

자동화가 쉽고 인증서 갱신에도 유리하기 때문이다.

---

## 실습 환경

### 준비물

* AWS 계정

* 퍼블릭 도메인 1개

* Route 53 Hosted Zone 또는 외부 DNS

* EC2 인스턴스 2대

* ALB 1대

* 보안 그룹 설정 가능 상태

---

### 리전 주의사항

ACM 인증서는 ALB와 같은 리전에 있어야 한다.

예를 들어

* ALB가 서울 리전(ap-northeast-2)에 있으면

* ACM 인증서도 서울 리전에서 발급해야 한다

이 부분은 실습 중 자주 발생하는 실수다.

---

## 실습 시나리오

이번 실습은 다음 순서로 진행한다.

1. 웹 서버 2대를 준비한다

2. Target Group을 생성한다

3. ALB를 생성한다

4. ACM에서 인증서를 발급받는다

5. ALB에 HTTPS 리스너를 추가한다

6. HTTP 요청을 HTTPS로 리다이렉트한다

7. Route 53에서 도메인을 ALB에 연결한다

8. 브라우저에서 HTTPS 접속을 확인한다

---

# 1. EC2 웹 서버 준비

## 1-1. EC2 인스턴스 생성

다음과 같은 이름으로 EC2 인스턴스 2대를 생성한다.

* 이니셜-ec2-web-01

* 이니셜-ec2-web-02

Amazon Linux 2023 기준으로 진행한다.

---

## 1-2. Apache 설치 및 기본 페이지 생성

### Web Server 1

```
sudo dnf install-y httpd
sudo systemctl enable--now httpd
echo"<h1>Web Server 1</h1>" |sudotee /var/www/html/index.html
```

### Web Server 2

```
sudo dnf install-y httpd
sudo systemctl enable--now httpd
echo"<h1>Web Server 2</h1>" |sudotee /var/www/html/index.html
```

---

## 1-3. 명령어 설명

### `sudo dnf install -y httpd`

* Apache 웹 서버 패키지를 설치한다

* `y` 옵션은 설치 과정에서 묻는 질문에 자동으로 yes를 선택하게 해준다

### `sudo systemctl enable --now httpd`

* `enable` 은 부팅 시 자동 시작되도록 등록한다

* `-now` 는 지금 즉시 서비스를 시작한다

* 즉, 현재 실행도 하고 다음 부팅 후 자동 시작도 설정하는 명령이다

### `echo "<h1>Web Server 1</h1>" | sudo tee /var/www/html/index.html`

* Apache 기본 문서 루트 경로에 HTML 파일을 생성한다

* `tee` 를 사용하는 이유는 root 권한으로 파일에 쓰기 위해서다

---

## 1-4. 웹 서버 보안 그룹 설정

EC2 웹 서버용 보안 그룹 인바운드 규칙 예시는 다음과 같다.

* SSH(22): 관리자 공인 IP 허용

* HTTP(80): ALB 보안 그룹만 허용

실무에서는 EC2의 80 포트를 전체 인터넷에 직접 열지 않고, ALB를 통해서만 접근되도록 구성하는 것이 일반적이다.

---

# 2. Target Group 생성

## 2-1. Target Group의 역할

ALB는 요청을 직접 EC2에 보내지 않고 Target Group을 통해 전달한다.

Target Group은 다음 역할을 수행한다.

* 어떤 서버에게 요청을 전달할지 결정

* Health Check를 수행해 정상 서버를 판별

* 정상 상태의 서버에만 트래픽 전달

---

## 2-2. 생성 절차

EC2 콘솔 → Load Balancing → Target Groups → Create target group

다음과 같이 설정한다.

* Target type: Instances

* Name: 이니셜-tg-web

* Protocol: HTTP

* Port: 80

* VPC: 실습용 VPC 선택

* Health check path: `/`

생성 후 EC2 웹 서버 2대를 등록한다.

---

## 2-3. Health Check 설명

Health Check는 ALB가 백엔드 서버 상태를 점검하는 기능이다.

예를 들어 다음처럼 설정했다면

* Protocol: HTTP

* Port: 80

* Path: `/`

ALB는 각 EC2에 대해 `http://대상IP:80/` 요청을 주기적으로 보낸다.

정상 응답 코드(예: 200 OK)가 돌아오면 Healthy 상태로 판단한다.

웹 서버가 중지되었거나 응답이 비정상이면 Unhealthy 상태가 된다.

---

# 3. ALB 생성

## 3-1. ALB 생성

EC2 콘솔 → Load Balancers → Create Load Balancer → Application Load Balancer 선택

다음과 같이 설정한다.

* Name: 이니셜-alb-web

* Scheme: Internet-facing

* IP address type: IPv4

* VPC: 실습 VPC

* Subnets: 서로 다른 AZ의 퍼블릭 서브넷 2개 이상 선택

ALB는 고가용성을 위해 최소 2개의 AZ에 걸쳐 배치하는 것이 일반적이다.

---

## 3-2. ALB 보안 그룹 설정

ALB용 보안 그룹 인바운드 규칙은 다음처럼 설정한다.

* HTTP(80): 0.0.0.0/0

* HTTPS(443): 0.0.0.0/0

설명은 다음과 같다.

* 80 포트는 HTTP 접속을 받은 뒤 HTTPS로 리다이렉트하기 위해 사용

* 443 포트는 실제 HTTPS 통신을 위해 사용

---

## 3-3. 초기 리스너 설정

처음에는 다음처럼 생성해도 된다.

* Listener: HTTP 80

* Default action: Forward to 이니셜-tg-web

이후 ACM 인증서를 발급한 뒤 443 리스너를 추가한다.

---

# 4. ACM 인증서 발급

## 4-1. ACM 콘솔 이동

반드시 ALB와 같은 리전으로 이동한 뒤 ACM 콘솔을 연다.

---

## 4-2. 인증서 요청

ACM 콘솔 → Request a certificate → Request a public certificate 선택

예시 도메인 입력

* `www.example.com`

또는 필요 시 와일드카드 사용 가능

* `.example.com`

실습 초반에는 개별 FQDN으로 진행하는 것이 이해하기 쉽다.

---

## 4-3. 검증 방식 선택

Validation method는 **DNS validation** 을 선택한다.

DNS validation을 선택하는 이유는 다음과 같다.

* 실무에서 가장 많이 사용함

* 자동화에 유리함

* 갱신 시에도 편리함

---

## 4-4. DNS 검증 이해

인증서를 요청하면 ACM은 해당 도메인을 내가 실제로 제어하는지 확인하기 위해 DNS 레코드 추가를 요구한다.

예를 들면 다음과 같은 CNAME 레코드가 제시될 수 있다.

* Name: `_xxxx.www.example.com`

* Value: `_yyyy.acm-validations.aws`

이 레코드를 DNS에 등록하면 AWS가 이를 조회해 도메인 소유 여부를 검증한다.

---

## 4-5. Route 53 사용 시

도메인을 Route 53에서 관리하고 있다면 ACM 콘솔에서 **Create records in Route 53** 버튼으로 검증 레코드를 자동 생성할 수 있다.

즉, CNAME 값을 수동으로 복사하지 않아도 된다.

---

## 4-6. 외부 DNS 사용 시

도메인이 외부 DNS 서비스에 있다면 ACM에서 안내한 CNAME 레코드를 해당 DNS 관리 화면에 직접 등록해야 한다.

예시:

* 가비아

* 후이즈

* Cloudflare 등

이 경우 DNS 전파 시간이 다소 걸릴 수 있다.

---

## 4-7. 인증서 상태 확인

인증서 상태가 다음과 같이 바뀌는지 확인한다.

* Pending validation

* Issued

반드시 **Issued** 상태가 되어야 ALB에 연결할 수 있다.

---

# 5. ALB에 HTTPS 리스너 추가

## 5-1. 443 리스너 추가

EC2 콘솔 → Load Balancers → 생성한 ALB 선택 → Listeners and rules → Add listener

다음과 같이 설정한다.

* Protocol: HTTPS

* Port: 443

* Default action: Forward to 이니셜-tg-web

* Default SSL/TLS certificate: 발급받은 ACM 인증서 선택

저장한다.

---

## 5-2. Security Policy 설명

HTTPS 리스너에는 TLS 정책(Security Policy)이 존재한다.

이 정책은 다음을 결정한다.

* 어떤 TLS 버전을 허용할지

* 어떤 암호 스위트를 허용할지

교육용 실습에서는 기본값을 사용해도 충분하다.

운영 환경에서는 보안 정책에 맞는 TLS 정책을 선택해야 한다.

---

# 6. HTTP를 HTTPS로 리다이렉트

## 6-1. 리다이렉트 설정 목적

사용자가 `http://도메인명` 으로 접속하더라도 자동으로 `https://도메인명` 으로 이동하게 만들어야 한다.

그래야 사용자가 평문 HTTP를 계속 사용하지 않게 된다.

---

## 6-2. 설정 절차

ALB → Listeners and rules → HTTP:80 리스너 선택 → Edit rules

기존 Forward 동작 대신 Redirect 동작으로 변경한다.

설정 예시는 다음과 같다.

* Protocol: HTTPS

* Port: 443

* Host: `#{host}`

* Path: `/#{path}`

* Query: `#{query}`

* Status code: HTTP\_301

---

## 6-3. 각 항목 설명

### `#{host}`

원래 요청한 호스트명을 그대로 유지한다.

예:

* `www.example.com`

* `app.example.com`

### `/#{path}`

사용자가 요청한 경로를 그대로 유지한다.

예:

* `/`

* `/login`

* `/images/logo.png`

### `#{query}`

URL 뒤의 쿼리 문자열을 유지한다.

예:

* `?page=1`

* `?id=100&sort=desc`

### `HTTP_301`

영구 이동(Permanent Redirect)을 의미한다.

브라우저와 검색엔진에게 해당 리소스가 HTTPS로 영구 이동했음을 알리는 응답 코드다.

---

# 7. Route 53에서 도메인 연결

## 7-1. ALB DNS 이름 확인

ALB에는 AWS가 자동 생성한 DNS 이름이 있다.

예시:

```
이니셜-alb-web-123456789.ap-northeast-2.elb.amazonaws.com
```

사용자는 이 주소가 아니라 `www.example.com` 같은 도메인으로 접속하게 해야 한다.

---

## 7-2. Route 53 Alias 레코드 생성

Route 53 콘솔 → Hosted Zones → 해당 도메인 선택 → Create record

다음과 같이 설정한다.

* Record name: `www`

* Record type: A

* Alias: On

* Route traffic to: Alias to Application and Classic Load Balancer

* Region: ALB가 있는 리전 선택

* Load balancer: 생성한 ALB 선택

저장한다.

---

## 7-3. Alias 레코드 설명

Alias 레코드는 Route 53에서 AWS 리소스를 대상으로 연결할 때 사용하는 특별한 레코드다.

장점은 다음과 같다.

* ALB와 쉽게 연결 가능

* 루트 도메인에도 사용 가능

* AWS 리소스와 연동성이 좋음

---

# 8. 접속 확인

## 8-1. HTTPS 접속 확인

브라우저에서 다음 주소로 접속한다.

```
https://www.example.com
```

다음 항목을 확인한다.

* 자물쇠 표시가 보이는지

* 인증서 경고가 발생하지 않는지

* 웹 페이지가 정상 출력되는지

* 새로고침 시 Web Server 1, Web Server 2가 번갈아 표시되는지

---

## 8-2. HTTP 접속 후 리다이렉트 확인

브라우저에서 다음 주소로 접속한다.

```
http://www.example.com
```

다음 항목을 확인한다.

* 자동으로 `https://www.example.com` 으로 이동하는지

---

## 8-3. curl 명령으로 확인

### HTTP 확인

```
curl-I http://www.example.com
```

예상 결과

* `301 Moved Permanently`

* `Location: https://www.example.com/...`

### HTTPS 확인

```
curl-I https://www.example.com
```

예상 결과

* `HTTP/2 200`

  또는

* `HTTP/1.1 200 OK`

---

## 8-4. openssl로 인증서 확인

```
openssl s_client-connect www.example.com:443-servername www.example.com
```

### 명령어 설명

### `openssl s_client`

TLS/SSL 서버와 직접 연결해 인증서와 핸드셰이크 정보를 확인하는 도구다.

### `connect www.example.com:443`

대상 호스트의 443 포트로 연결한다.

### `servername www.example.com`

SNI(Server Name Indication) 값을 함께 전달한다.

하나의 ALB에 여러 도메인 인증서가 있을 때 매우 중요하다.

출력 결과에서 다음을 확인할 수 있다.

* 서버가 제시한 인증서

* 인증서 체인

* TLS 버전

* Cipher Suite

* 인증서 검증 결과

---

# 9. 전체 실습 흐름 정리

다음 순서로 실습이 진행된다.

1. EC2 웹 서버 2대 준비

2. Apache 설치 및 index.html 작성

3. Target Group 생성

4. ALB 생성

5. ACM 퍼블릭 인증서 요청

6. DNS validation 수행

7. 인증서가 Issued 상태가 되면 ALB에 443 리스너 추가

8. 80 리스너는 443으로 Redirect 설정

9. Route 53 Alias 레코드 생성

10. 브라우저와 CLI로 HTTPS 동작 확인