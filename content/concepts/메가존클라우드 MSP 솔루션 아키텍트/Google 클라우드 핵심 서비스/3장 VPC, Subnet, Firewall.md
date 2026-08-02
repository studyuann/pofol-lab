---
title: "3장 VPC, Subnet, Firewall"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Google 클라우드 핵심 서비스"]
is_public: true
draft: false
---

# 3장. VPC, Subnet, Firewall

## 1. 장 개요

이 장에서는 Google Cloud 네트워크의 기본이 되는 VPC, Subnet, Route, Firewall Rule을 학습한다.

앞 장에서 Project와 IAM을 다뤘다면, 이제는 그 프로젝트 안에서 실제 워크로드가 연결될 **네트워크 기반**을 이해하는 단계다.

AWS를 먼저 학습한 상태에서는 보통 다음 감각이 익숙하다.

* VPC는 리전 단위 네트워크임

* 서브넷은 AZ 단위로 나뉨

* Security Group이 인스턴스 단위 방화벽 역할을 함

* Route Table을 서브넷과 연결해 경로를 제어함

하지만 GCP는 이 지점에서 운영 감각이 다르게 들어온다.

* **VPC는 글로벌 리소스**임

* **서브넷은 리전 리소스**임

* **방화벽 제어는 VPC Firewall Rule 중심**으로 봄

* 인스턴스 대상 지정에 **네트워크 태그**나 **서비스 계정**을 활용할 수 있음

* 모든 VPC에는 기본적으로 **암시적(implied) 방화벽 규칙**이 존재함 ([Google Cloud Documentation](https://docs.cloud.google.com/vpc/docs/overview?utm_source=chatgpt.com))

즉, 이 장은 단순히 네트워크를 만드는 법을 배우는 장이 아니라,

**GCP 네트워크를 어떤 사고방식으로 다뤄야 하는지**를 익히는 장이라고 보면 된다.

---

## 2. 학습 목표

이 장을 마치면 다음이 가능해야 한다.

* GCP VPC가 글로벌 리소스라는 의미를 설명할 수 있음

* Subnet이 리전 리소스라는 점을 설명할 수 있음

* Auto mode VPC와 Custom mode VPC의 차이를 설명할 수 있음

* Firewall Rule의 구성 요소와 동작 방식을 설명할 수 있음

* 네트워크 태그와 서비스 계정을 대상 지정에 활용하는 방법을 설명할 수 있음

* GCP Firewall Rule과 AWS Security Group의 차이를 비교할 수 있음

* CLI와 콘솔을 사용해 VPC, Subnet, Firewall Rule을 생성할 수 있음

* 기본적인 VM 통신을 위한 네트워크를 구성할 수 있음 ([Google Cloud Documentation](https://docs.cloud.google.com/vpc/docs/overview?utm_source=chatgpt.com))

---

## 3. 핵심 키워드

* VPC

* Global Resource

* Subnet

* Regional Resource

* Firewall Rule

* Implied Rules

* Ingress

* Egress

* Route

* Network Tag

* Target Service Account

* Auto mode

* Custom mode

---

# 4. GCP VPC란 무엇인가

GCP에서 VPC는 가상 네트워크를 의미한다.

Compute Engine VM, 로드밸런서 백엔드, 내부 서비스 연결 등 대부분의 인프라 통신이 이 VPC 위에서 이루어진다.

여기서 가장 중요한 특징은 다음이다.

## 핵심 특징

* **VPC 네트워크는 글로벌 리소스**다

* 하나의 VPC 안에 **여러 리전의 서브넷**을 둘 수 있다

* 라우트와 방화벽 규칙도 VPC와 함께 네트워크 차원에서 관리된다

즉, AWS처럼 “서울 리전에 VPC 하나, 도쿄 리전에 다른 VPC 하나”라는 감각으로 먼저 생각하기보다,

GCP에서는 **하나의 VPC가 여러 리전 자원을 포괄하는 구조**를 먼저 떠올리는 것이 더 자연스럽다.

---

# 5. AWS VPC와 GCP VPC의 차이

## 5.1 AWS에서 익숙한 구조

* VPC는 리전 단위

* 서브넷은 AZ 단위로 나뉨

* Security Group이 인스턴스 방화벽 역할을 수행

* Route Table을 서브넷과 연결하는 감각이 강함

## 5.2 GCP에서의 구조

* VPC는 글로벌 리소스

* 서브넷은 리전 리소스

* 방화벽은 VPC 차원에서 정의

* 대상 인스턴스 선택 시 네트워크 태그나 서비스 계정을 사용 가능

---

# 6. VPC 네트워크의 종류

GCP에서 VPC를 만들 때 대표적으로 두 가지 모드를 볼 수 있다.

* Auto mode VPC

* Custom mode VPC

---

## 6.1 Auto mode VPC

Auto mode VPC는 Google Cloud가 미리 서브넷을 자동 생성해주는 방식이다.

여러 리전에 대해 기본 대역의 서브넷이 자동으로 준비된다.

### 장점

* 빠르게 시작 가능

* 실습 초반에는 구조를 빨리 확인하기 쉬움

### 단점

* 네트워크 대역을 세밀하게 설계하기 어려움

* 실무 환경에서는 주소 체계 충돌 가능성이 있음

* 향후 확장이나 하이브리드 연결 시 불편할 수 있음

---

## 6.2 Custom mode VPC

Custom mode VPC는 서브넷을 직접 설계하고 생성하는 방식이다.

리전별로 필요한 서브넷과 CIDR 대역을 직접 정한다.

### 장점

* 주소 체계를 명확히 설계 가능

* 멀티리전, VPN, 하이브리드 연결 시 유리

* 교육에서도 네트워크 구조를 의도적으로 설명하기 좋음

### 단점

* 직접 설계해야 하므로 초기 설정이 약간 더 필요함

---

# 7. Subnet이란 무엇인가

서브넷은 VPC 안에서 IP 주소 범위를 실제로 나누어 사용하는 네트워크 세그먼트다.

중요한 점은 GCP에서 **서브넷은 리전 리소스**라는 것이다. 즉, 같은 VPC 안에도 서울 리전 서브넷, 도쿄 리전 서브넷을 각각 둘 수 있다.

예를 들어 아래처럼 설계할 수 있다.

* VPC: `camp-vpc`
  + Seoul subnet: `10.10.1.0/24`
  + Tokyo subnet: `10.20.1.0/24`

이 둘은 하나의 글로벌 VPC 안에 속하지만, 각각 다른 리전에 존재한다.

## 왜 중요한가

이 구조 덕분에 GCP에서는 멀티리전 네트워크를 상대적으로 일관되게 설계할 수 있다.

반면 주소 체계를 처음부터 잘 잡지 않으면 이후 VPN이나 Shared VPC 연결 시 복잡해질 수 있다.

---

# 8. Route란 무엇인가

Route는 패킷이 어디로 나가야 하는지를 결정하는 경로 정보다.

## 8.1 GCP 라우트의 기본 감각

* VPC 네트워크에는 기본 라우트가 존재함

* 같은 VPC 안의 서브넷 간 통신을 위한 경로가 자동으로 처리됨

* 필요 시 정적 라우트를 추가할 수 있음

## 8.2 AWS와의 차이 체감

AWS에서는 Route Table을 서브넷과 연관시키는 개념을 자주 다룬다.

GCP도 라우팅 개념은 동일하게 중요하지만, 방화벽과 VPC 구조 쪽에서 더 크게 나타난다.

* 같은 VPC 내부 통신은 기본 라우팅이 상당 부분 처리함

* 인터넷 방향 통신도 기본 경로가 관여함

* VPN, 하이브리드, 특수 목적 경로는 이후 별도 설계가 필요함

---

# 9. GCP Firewall Rule이란 무엇인가

GCP의 VPC는 분산형 가상 방화벽을 구현하며, Firewall Rule로 어떤 트래픽을 허용하거나 차단할지 제어한다.

## 9.1 핵심 개념

방화벽 규칙은 다음을 기준으로 트래픽을 제어한다.

* 어떤 VPC 네트워크에 적용할지

* 인바운드(INGRESS)인지 아웃바운드(EGRESS)인지

* 허용(allow)인지 거부(deny)인지

* 어떤 프로토콜과 포트인지

* 어떤 소스 또는 목적지 범위인지

* 어떤 대상 인스턴스에 적용할지

## 9.2 중요한 특징

* Firewall Rule은 **네트워크 차원에서 정의**된다

* 대상 인스턴스를 **태그**나 **서비스 계정**으로 지정할 수 있다

* 규칙마다 **우선순위(priority)** 가 있다

* 기본적으로 모든 VPC에는 **암시적 인바운드 거부 / 아웃바운드 허용 규칙**이 존재한다

---

# 10. 암시적 방화벽 규칙(Implied Rules)

이 부분은 꼭 짚어야 한다.

Google Cloud는 모든 VPC 네트워크에 대해 기본적으로 다음 두 가지 암시적 규칙을 둔다.

* 모든 **인바운드 연결 차단**

* 모든 **아웃바운드 연결 허용**

즉, VM을 만들었다고 해서 외부에서 바로 SSH나 HTTP 접속이 가능한 것이 아니다.

접속하려면 명시적으로 인바운드 허용 규칙을 만들어야 한다.

---

# 11. Firewall Rule의 주요 구성 요소

## 11.1 Direction

트래픽 방향을 의미한다.

* `INGRESS`: 외부 또는 다른 소스에서 VM으로 들어오는 트래픽

* `EGRESS`: VM에서 외부 또는 다른 대상으로 나가는 트래픽

## 11.2 Action

규칙이 일치할 때 수행할 동작이다.

* `allow`

* `deny`

## 11.3 Protocol / Port

허용 또는 차단할 프로토콜과 포트를 지정한다.

예시

* `tcp:22`

* `tcp:80`

* `tcp:443`

## 11.4 Source / Destination

어디서 오는 트래픽인지, 어디로 가는 트래픽인지 지정한다.

예시

* `0.0.0.0/0`

* `10.10.1.0/24`

## 11.5 Target

규칙이 적용될 대상을 의미한다.

Google Cloud에서는 모든 규칙이 네트워크 안의 모든 인스턴스에 적용될 수도 있고, 특정 **타깃 태그** 또는 **타깃 서비스 계정**을 기준으로 제한할 수도 있다.

---

# 12. 네트워크 태그(Network Tag)

네트워크 태그는 VM 인스턴스를 논리적으로 분류하는 데 사용하는 문자열이다.

Firewall Rule에서 `target-tags` 로 지정하면, 해당 태그를 가진 VM에만 규칙이 적용된다.

예를 들어

* 웹 서버 VM: `web`

* 관리 서버 VM: `bastion`

* 애플리케이션 서버 VM: `app`

처럼 태그를 줄 수 있다.

그리고 방화벽 규칙에서

* `target-tags=web`

* `allow tcp:80`

로 설정하면, `web` 태그가 붙은 인스턴스만 HTTP를 받을 수 있다.

## 왜 유용한가

인스턴스 이름으로 일일이 관리하지 않고, 역할 기반으로 네트워크 제어가 가능해진다.

---

# 13. 서비스 계정을 대상 지정에 활용

방화벽 규칙 대상은 태그뿐 아니라 **서비스 계정**으로도 지정할 수 있다.

즉, 특정 서비스 계정이 연결된 VM 인스턴스 집합에만 규칙을 적용할 수 있다.

초반 실습은 태그 기반이 더 직관적이므로 태그 중심으로 진행하면 된다.

하지만 실무에서는 서비스 계정 기반 제어가 더 정교하고 관리 친화적인 경우가 많다.

예를 들어

* `web-sa` 서비스 계정을 가진 인스턴스만 특정 백엔드 포트에 접근 가능하게 설계

---

# 14. GCP Firewall Rule과 AWS Security Group 비교

## AWS Security Group

* 인스턴스나 ENI에 연결되는 감각이 강함

* 상태 저장(stateful) 방화벽

* 리소스 부착형 보안 제어라는 인상이 강함

## GCP Firewall Rule

* VPC 차원에서 정의

* 대상은 태그 또는 서비스 계정 등으로 지정

* 네트워크 중심 제어라는 인상이 강함

**AWS는 인스턴스에 보안그룹을 붙이는 감각이 강하고, GCP는 네트워크 위에 방화벽 규칙을 정의한 뒤 대상 VM을 지정하는 감각이 강함**

---

# 15. 기본 네트워크 설계 예시

## 예시 구조

* VPC: `initial-vpc`

* Region: `asia-northeast3`

* Subnet: `initial-subnet-web`

* CIDR: `10.10.1.0/24`

## 방화벽 규칙

* `allow-ssh`: TCP 22 허용

* `allow-http`: TCP 80 허용

## 태그

* 웹 서버 VM: `web`

이 구조면 이후 Compute Engine 장에서 웹 서버 VM을 올리고 접속 테스트하기 좋다.

---

# 16. 실습 1: Custom VPC 생성

## 16.1 실습 목표

* Custom mode VPC를 직접 생성함

* 자동 생성 방식이 아닌 직접 설계 방식으로 네트워크를 준비함

## 16.2 콘솔 실습

1. Google Cloud Console 접속

2. **VPC 네트워크** 메뉴 이동

3. **VPC 네트워크 만들기** 클릭

4. 이름: `initial-vpc`

5. 서브넷 생성 모드: **Custom**

6. 저장

## 16.3 CLI 실습

```
gcloud compute networks create initial-vpc \
  --subnet-mode=custom
```

### 명령 설명

* `gcloud compute networks create`

  새 VPC 네트워크를 생성하는 명령이다.

* `initial-vpc`

  생성할 VPC 이름이다.

* `-subnet-mode=custom`

  자동 생성이 아니라 커스텀 모드로 만들겠다는 의미다.

### 확인 명령

```
gcloud compute networks list
```

### 설명

생성된 VPC 네트워크 목록을 조회한다.

---

# 17. 실습 2: 서브넷 생성

## 17.1 실습 목표

* 특정 리전에 서브넷을 직접 생성함

* 서브넷이 리전 리소스라는 점을 확인함

## 17.2 CLI 실습

```
gcloud compute networks subnets create initial-subnet-web \
  --network=initial-vpc \
  --region=asia-northeast3 \
  --range=10.10.1.0/24
```

### 명령 설명

* `gcloud compute networks subnets create`

  새 서브넷을 생성하는 명령이다.

* `initial-subnet-web`

  서브넷 이름이다.

* `-network=initial-vpc`

  어느 VPC에 속할지 지정한다.

* `-region=asia-northeast3`

  서브넷이 위치할 리전을 지정한다.

* `-range=10.10.1.0/24`

  사용할 IP 주소 범위를 CIDR 형식으로 지정한다.

### 확인 명령

```
gcloud compute networks subnets list
```

---

# 18. 실습 3: SSH 허용 방화벽 규칙 생성

## 18.1 실습 목표

* 인바운드 SSH 접속을 허용하는 규칙을 만든다

* 태그를 이용해 특정 역할의 인스턴스에만 적용하는 방식을 익힌다

## 18.2 CLI 실습

```
gcloud compute firewall-rules create allow-ssh-web \
  --network=initial-vpc \
  --direction=INGRESS \
  --priority=1000 \
  --action=ALLOW \
  --rules=tcp:22 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=web
```

### 명령 설명

* `gcloud compute firewall-rules create`

  새 방화벽 규칙을 생성한다.

* `allow-ssh-web`

  규칙 이름이다.

* `--network=initial-vpc`

  어느 VPC에 적용할 규칙인지 지정한다.

* `--direction=INGRESS`

  외부에서 들어오는 트래픽에 대한 규칙이다.

* `--priority=1000`

  우선순위다. 숫자가 작을수록 우선순위가 높다. ([Google Cloud Documentation](https://docs.cloud.google.com/firewall/docs/using-firewalls?hl=ko&utm_source=chatgpt.com))

* `--action=ALLOW`

  일치하는 트래픽을 허용한다.

* `--rules=tcp:22`

  SSH 포트인 TCP 22를 허용한다.

* `--source-ranges=0.0.0.0/0`

  모든 IP에서 오는 트래픽을 허용한다.

* `--target-tags=web`

  `web` 태그가 붙은 인스턴스에만 적용한다.

### 보안 설명

실습에서는 `0.0.0.0/0` 을 자주 쓰지만, 운영 환경에서는 관리망 IP 대역으로 제한하는 것이 바람직하다.

---

# 19. 실습 4: HTTP 허용 방화벽 규칙 생성

## 19.1 실습 목표

* 웹 서버 포트 80을 허용하는 규칙을 만든다

## 19.2 CLI 실습

```
gcloud compute firewall-rules create allow-http-web \
  --network=initial-vpc \
  --direction=INGRESS \
  --priority=1000 \
  --action=ALLOW \
  --rules=tcp:80 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=web
```

### 확인 명령

```
gcloud compute firewall-rules list
```

또는 특정 네트워크 기준으로 필터링해서 볼 수 있다.

```
gcloud compute firewall-rules list --filter="network:initial-vpc"
```

---

# 20. 실습 5: VPC와 방화벽 규칙 확인

## 20.1 VPC 상세 확인

```
gcloud compute networks describe initial-vpc
```

## 20.2 서브넷 상세 확인

```
gcloud compute networks subnets describe initial-subnet-web \
  --region=asia-northeast3
```

## 20.3 방화벽 규칙 상세 확인

```
gcloud compute firewall-rules describe allow-http-web
```

---

# 21. 실습 6: VM 생성 준비 관점에서 네트워크 정리

## 현재 준비된 것

* `initial-vpc`

* `initial-subnet-web`

* `allow-ssh-web`

* `allow-http-web`

## 추가할 것

* 태그 `web` 을 가진 VM 생성

* Startup Script로 nginx 설치

* 외부 IP로 접속 테스트

---

# 22. 장 요약

* GCP의 VPC는 **글로벌 리소스**다.

* 서브넷은 **리전 리소스**이며, 하나의 VPC 안에 여러 리전 서브넷을 둘 수 있다.

* 방화벽 제어는 **VPC Firewall Rule 중심**으로 이루어진다.

* 모든 VPC에는 기본적으로 **인바운드 거부 / 아웃바운드 허용**의 암시적 규칙이 있다.

* 방화벽 규칙 대상은 네트워크 태그 또는 서비스 계정으로 지정할 수 있다.

* AWS와 비교하면, GCP는 **네트워크 중심 방화벽 모델**이라는 감각이 더 강하다.

---