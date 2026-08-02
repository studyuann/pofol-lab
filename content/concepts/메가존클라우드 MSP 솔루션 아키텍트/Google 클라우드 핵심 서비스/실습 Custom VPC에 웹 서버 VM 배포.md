---
title: "실습 Custom VPC에 웹 서버 VM 배포"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Google 클라우드 핵심 서비스"]
is_public: true
draft: false
---

# 실습. Custom VPC에 웹 서버 VM 배포

---

## 1. 실습 개요

먼저 Custom VPC와 서브넷을 만들고, 외부에서 접속할 수 있도록 SSH와 HTTP 방화벽 규칙을 생성한다.

그 다음 Compute Engine VM을 생성하고, Startup Script를 이용해 nginx를 자동 설치한 뒤, 브라우저를 통해 웹 서버 접속을 확인한다.

이 실습은 AWS 경험자 기준으로 보면 다음 흐름과 거의 대응된다.

### AWS 기준 대응 흐름

* VPC 생성

* Subnet 생성

* Security Group 생성

* EC2 생성

* User Data로 nginx 설치

* Public IP로 접속 확인

### GCP 기준 실습 흐름

* VPC 생성

* Subnet 생성

* Firewall Rule 생성

* Compute Engine 생성

* Startup Script로 nginx 설치

* External IP로 접속 확인

---

## 2. 실습 목표

* GCP 프로젝트를 기준으로 작업하는 흐름을 이해할 수 있음

* Custom VPC와 Regional Subnet을 직접 생성할 수 있음

* Firewall Rule을 이용해 SSH/HTTP 트래픽을 허용할 수 있음

* Compute Engine VM을 생성할 수 있음

* Startup Script를 이용해 초기 설정을 자동화할 수 있음

* External IP를 통해 웹 서버 접속을 확인할 수 있음

* 네트워크 태그와 방화벽 규칙의 관계를 설명할 수 있음

---

## 3. 실습 시나리오

> 신규 웹 서버를 GCP에 배포하려고 한다.
>
> 아직 네트워크가 준비되어 있지 않으므로 Custom VPC를 직접 만들고, 웹 서버가 들어갈 서브넷을 생성해야 한다.
>
> 외부 관리자는 SSH로 접속해야 하고, 사용자는 HTTP로 웹 서버에 접근해야 한다.
>
> VM 생성 후 수동 설정을 줄이기 위해 Startup Script를 사용해 nginx를 자동 설치한다.

---

## 4. 전체 아키텍처

### 아키텍처 구성 요소

* Project: 현재 선택된 GCP 프로젝트

* VPC: `initial-vpc`

* Subnet: `initial-subnet-web`

* CIDR: `10.10.1.0/24`

* Firewall Rule
  + `allow-ssh-web`
  + `allow-http-web`

* VM
  + 이름: `web-vm-01`
  + Zone: `asia-northeast3-a`
  + Machine Type: `e2-micro`
  + Tag: `web`
  + Startup Script: nginx 설치

* 접속 경로
  + 관리자: SSH
  + 사용자: HTTP

---

## 5. 사전 준비

실습 전에 아래 항목을 확인한다.

* GCP 로그인 완료

* 실습용 Project 선택 완료

* Compute Engine API 사용 가능 상태

* 권한: VPC, Firewall, VM 생성 가능 권한 보유

* Cloud Shell 사용 가능

### 권장 리전/존

* Region: `asia-northeast3`

* Zone: `asia-northeast3-a`

---

## 6. 실습 흐름

이번 실습은 아래 순서로 진행한다.

1. 현재 프로젝트 확인

2. VPC 생성

3. 서브넷 생성

4. SSH 허용 방화벽 규칙 생성

5. HTTP 허용 방화벽 규칙 생성

6. Startup Script 작성

7. Compute Engine VM 생성

8. VM 상태 확인

9. SSH 접속 확인

10. HTTP 웹 접속 확인

11. 결과 점검 및 정리

---

# 7. 단계별 실습

---

## 단계 1. 현재 프로젝트 확인

GCP에서는 현재 어떤 Project를 기준으로 작업하는지가 매우 중요하다.

같은 계정으로 여러 프로젝트를 운영할 수 있기 때문에, 지금 어떤 프로젝트에 리소스를 생성하는지 먼저 확인해야 한다.

### 명령어

```
gcloud config get-value project
```

### 설명

* `gcloud config get-value project` 는 현재 gcloud CLI가 기본으로 참조하는 프로젝트를 출력한다.

* 이 값이 예상한 프로젝트가 아니라면 이후 생성되는 VPC, 서브넷, VM이 전부 다른 프로젝트에 만들어질 수 있다.

* 실습에서는 이 확인 과정을 습관처럼 반복하는 것이 좋다.

### 프로젝트 변경이 필요한 경우

```
gcloud config set project [PROJECT_ID]
```

### 설명

* `[PROJECT_ID]` 부분에 실제 프로젝트 ID를 입력한다.

* 프로젝트 이름이 아니라 프로젝트 ID를 사용하는 것이 일반적이다.

* 변경 후 다시 `gcloud config get-value project` 로 확인한다.

---

## 단계 2. 기존 네트워크 확인

실습 전에 현재 프로젝트에 어떤 네트워크가 이미 있는지 확인한다.

### 명령어

```
gcloud compute networks list
```

### 설명

* 현재 프로젝트에 존재하는 VPC 네트워크 목록을 보여준다.

* 기본 네트워크(default)가 있을 수도 있고, 아무 것도 없을 수도 있다.

* 이번 실습에서는 직접 설계한 Custom VPC를 새로 만드는 것이 목적이므로, 기존 네트워크와 별도로 새 VPC를 생성한다.

---

## 단계 3. Custom VPC 생성

이번 실습에서는 자동 생성 방식이 아닌 Custom VPC를 직접 만든다.

이 방식이 실무 구조와 더 가깝고, 서브넷을 명시적으로 설계할 수 있다.

### 명령어

```
gcloud compute networks create initial-vpc \
  --subnet-mode=custom
```

### 설명

* `gcloud compute networks create` 는 새 VPC 네트워크를 생성하는 명령이다.

* `initial-vpc` 는 생성할 VPC 이름이다.

* `-subnet-mode=custom` 은 자동 서브넷 생성이 아니라, 서브넷을 사용자가 직접 만들겠다는 의미다.

### 생성 확인

```
gcloud compute networks list
```

### 기대 결과

* `initial-vpc` 가 목록에 보여야 한다.

### 실습 포인트

* GCP의 VPC는 글로벌 리소스다.

* 지금은 단일 리전만 사용할 것이지만, 같은 VPC 안에 이후 다른 리전 서브넷도 추가할 수 있다.

---

## 단계 4. 웹 서버용 서브넷 생성

이제 서울 리전에 웹 서버가 배치될 서브넷을 생성한다.

### 명령어

```
gcloud compute networks subnets create initial-subnet-web \
  --network=initial-vpc \
  --region=asia-northeast3 \
  --range=10.10.1.0/24
```

### 설명

* `gcloud compute networks subnets create` 는 새 서브넷을 생성하는 명령이다.

* `initial-subnet-web` 은 서브넷 이름이다.

* `-network=initial-vpc` 는 이 서브넷이 어느 VPC에 속하는지 지정한다.

* `-region=asia-northeast3` 는 서브넷이 서울 리전에 속함을 의미한다.

* `-range=10.10.1.0/24` 는 서브넷에서 사용할 사설 IP 대역이다.

### 확인 명령어

```
gcloud compute networks subnets list
```

### 기대 결과

* `initial-subnet-web`

* Region: `asia-northeast3`

* Range: `10.10.1.0/24`

### 실습 포인트

* VPC는 글로벌이지만 서브넷은 리전 단위라는 점을 다시 확인한다.

* VM은 이후 존(Zone) 단위로 생성되지만, 네트워크는 리전 서브넷을 기준으로 연결된다.

---

## 단계 5. SSH 허용 방화벽 규칙 생성

웹 서버를 관리하기 위해 관리자 SSH 접속을 허용한다.

실습에서는 모든 IP에서 접근 가능하게 열지만, 운영에서는 반드시 관리망 대역으로 제한하는 것이 좋다.

### 명령어

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

### 설명

* `allow-ssh-web` 이라는 이름의 인바운드 규칙을 생성한다.

* `-network=initial-vpc` 는 이 규칙이 적용될 VPC를 지정한다.

* `-direction=INGRESS` 는 외부에서 VM으로 들어오는 트래픽에 대한 규칙임을 의미한다.

* `-priority=1000` 은 우선순위다. 숫자가 작을수록 우선순위가 높다.

* `-action=ALLOW` 는 조건에 맞는 트래픽을 허용한다.

* `-rules=tcp:22` 는 SSH 포트인 22번 포트를 허용한다.

* `-source-ranges=0.0.0.0/0` 는 모든 출발지 IP를 의미한다.

* `-target-tags=web` 은 `web` 태그가 붙은 VM에만 이 규칙이 적용된다는 뜻이다.

### 확인 명령어

```
gcloud compute firewall-rules describe allow-ssh-web
```

### 실습 포인트

* 규칙은 만들어졌지만, 아직 `web` 태그를 가진 VM이 없으므로 실제 적용 대상은 없다.

* 나중에 VM 생성 시 반드시 `web` 태그를 넣어야 한다.

---

## 단계 6. HTTP 허용 방화벽 규칙 생성

이제 웹 사용자가 브라우저로 접근할 수 있도록 80번 포트를 허용한다.

### 명령어

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

### 설명

* 구조는 SSH 규칙과 동일하다.

* 차이는 허용 포트가 `tcp:80` 이라는 점이다.

* 역시 `web` 태그가 붙은 VM에만 적용된다.

### 확인 명령어

```
gcloud compute firewall-rules list --filter="network:initial-vpc"
```

### 기대 결과

다음 규칙이 보여야 한다.

* `allow-ssh-web`

* `allow-http-web`

---

## 단계 7. Startup Script 작성

이제 VM이 부팅될 때 자동으로 nginx를 설치하도록 Startup Script를 만든다.

이 스크립트는 AWS의 User Data와 매우 비슷한 역할을 한다.

### 명령어

```
cat > startup-web.sh <<'EOF'
#!/bin/bash
apt-get update -y
apt-get install -y nginx
systemctl enable nginx
systemctl start nginx
echo "<h1>GCP Compute Engine Web Server</h1>" > /var/www/html/index
EOF
```

### 스크립트 설명

* `#!/bin/bash`

  bash 셸로 실행하겠다는 의미다.

* `apt-get update -y`

  패키지 목록을 최신 상태로 갱신한다.

* `apt-get install -y nginx`

  nginx 패키지를 자동 설치한다.

* `systemctl enable nginx`

  VM 재부팅 후에도 nginx가 자동 시작되도록 설정한다.

* `systemctl start nginx`

  현재 부팅 세션에서 nginx를 바로 실행한다.

* `echo "<h1>GCP Compute Engine Web Server</h1>" > /var/www/html/index`

  웹 브라우저로 접속했을 때 확인할 수 있는 인덱스 페이지를 생성한다.

### 파일 확인

```
cat startup-web.sh
```

### 실습 포인트

* Startup Script는 인스턴스 생성 후 수동 작업을 줄이는 가장 기본적인 자동화 기법이다.

* 실무에서는 여기서 웹 애플리케이션 설치, 환경 변수 설정, 에이전트 설치 등으로 확장할 수 있다.

---

## 단계 8. Compute Engine VM 생성

이제 앞에서 만든 네트워크 위에 실제 VM을 생성한다.

### 명령어

```
gcloud compute instances create web-vm-01 \
  --zone=asia-northeast3-a \
  --machine-type=e2-micro \
  --subnet=initial-subnet-web \
  --tags=web \
  --image-family=debian-12 \
  --image-project=debian-cloud \
  --metadata-from-file=startup-script=startup-web.sh
```

### 명령 상세 설명

* `gcloud compute instances create web-vm-01`

  `web-vm-01` 이라는 이름의 VM을 생성한다.

* `--zone=asia-northeast3-a`

  서울 리전의 a 존에 VM을 배치한다.

* `--machine-type=e2-micro`

  실습용으로 가벼운 머신 타입을 사용한다.

* `--subnet=initial-subnet-web`

  앞에서 생성한 웹 서버용 서브넷에 VM을 연결한다.

* `--tags=web`

  이 VM에 `web` 태그를 부여한다.

  이 태그가 있어야 `allow-ssh-web`, `allow-http-web` 방화벽 규칙이 적용된다.

* `--image-family=debian-12`

  Debian 12 계열 최신 공개 이미지를 사용한다.

* `--image-project=debian-cloud`

  Debian 이미지를 제공하는 공개 프로젝트를 지정한다.

* `--metadata-from-file=startup-script=startup-web.sh`

  로컬에 만든 스크립트 파일을 VM 메타데이터의 startup-script 항목으로 전달한다.

### 실습 포인트

이 명령 하나 안에 사실상 VM 운영의 핵심 요소가 다 들어 있다.

* 어디에 배치할 것인가

* 어떤 크기로 만들 것인가

* 어떤 네트워크에 연결할 것인가

* 어떤 태그를 부여할 것인가

* 어떤 운영체제를 쓸 것인가

* 처음 부팅 시 무엇을 자동 실행할 것인가

---

## 단계 9. VM 생성 결과 확인

### 인스턴스 목록 조회

```
gcloud compute instances list
```

### 확인 포인트

* NAME: `web-vm-01`

* ZONE: `asia-northeast3-a`

* INTERNAL\_IP: `10.10.1.x` 대역인지 확인

* EXTERNAL\_IP: 공인 IP가 할당되었는지 확인

* STATUS: `RUNNING`

### 특정 인스턴스 상세 조회

```
gcloud compute instances describe web-vm-01 \
  --zone=asia-northeast3-a
```

### 상세 조회에서 확인할 항목

* 태그에 `web` 이 들어갔는지

* 네트워크 인터페이스가 `initial-subnet-web` 인지

* 외부 IP가 있는지

* 메타데이터에 startup-script가 있는지

---

## 단계 10. SSH 접속 확인

이제 VM이 SSH로 접속 가능한지 확인한다.

### 명령어

```
gcloud compute ssh web-vm-01 --zone=asia-northeast3-a
```

### 설명

* `gcloud compute ssh` 는 Compute Engine VM에 SSH 접속하는 명령이다.

* gcloud가 키 관리와 접속 설정을 도와준다.

* 접속이 되지 않으면 방화벽, 태그, 외부 IP, 권한을 차례대로 점검한다.

### 접속 후 확인 명령어

```
hostname
ip addr
systemctl status nginx
curl localhost
```

### 각 명령 설명

* `hostname`

  현재 접속한 서버 이름을 확인한다.

* `ip addr`

  네트워크 인터페이스와 내부 IP 주소를 확인한다.

* `systemctl status nginx`

  nginx 서비스가 정상 실행 중인지 확인한다.

* `curl localhost`

  로컬에서 웹 서버 응답을 확인한다.

  `<h1>GCP Compute Engine Web Server</h1>` 가 보이면 성공이다.

---

## 단계 11. 브라우저 HTTP 접속 확인

이제 외부에서 웹 브라우저로 접속해본다.

### 외부 IP 확인

```
gcloud compute instances list
```

### 브라우저 접속

```
http://[EXTERNAL_IP]
```

### 기대 결과

브라우저에 아래 메시지가 보이면 성공이다.

```
<h1>GCP Compute Engine Web Server</h1>
```

### 실습 포인트

이 단계는 단순히 웹이 뜨는 것을 보는 것이 아니라, 아래 요소가 모두 제대로 연결되었음을 의미한다.

* VPC 생성 완료

* Subnet 생성 완료

* Firewall Rule 생성 완료

* VM 태그 적용 완료

* External IP 할당 완료

* Startup Script 정상 실행 완료

* nginx 정상 실행 완료

---

# 8. 실습 결과 정리

실습이 성공적으로 끝났다면 현재 환경은 아래와 같아야 한다.

## 생성된 리소스

* VPC: `initial-vpc`

* Subnet: `initial-subnet-web`

* Firewall Rule:
  + `allow-ssh-web`
  + `allow-http-web`

* VM: `web-vm-01`

## 동작 상태

* SSH 접속 가능

* HTTP 접속 가능

* nginx 자동 설치 완료

* 웹 페이지 확인 가능

---

# 10. AWS와 비교 정리

이번 종합실습은 AWS 경험자 기준으로 아래처럼 대응해서 설명하면 좋다.

| AWS | GCP |
| --- | --- |
| VPC | VPC |
| Subnet | Subnet |
| Security Group | Firewall Rule |
| EC2 | Compute Engine |
| User Data | Startup Script |
| Public IP / Elastic IP | External IP / Static External IP |

### 핵심 차이

* AWS는 Security Group을 인스턴스에 붙이는 감각이 강함

* GCP는 VPC 차원 방화벽 규칙을 만들고, 태그로 대상 VM을 연결하는 감각이 강함

* AWS는 VPC가 리전 단위

* GCP는 VPC가 글로벌, 서브넷이 리전 단위

---

# 12. 장 요약

이번 종합실습에서는 GCP의 핵심 인프라 요소를 하나의 흐름으로 연결했다.

핵심은 다음과 같다.

* GCP 작업은 항상 Project 확인부터 시작해야 한다.

* VPC는 글로벌 리소스이며, 서브넷은 리전 단위로 생성한다.

* Firewall Rule은 VPC 차원에서 만들고, 태그를 통해 대상 VM에 적용한다.

* Compute Engine은 GCP의 대표적인 VM 서비스다.

* Startup Script를 통해 초기 설정을 자동화할 수 있다.

* 외부 IP, 방화벽 규칙, 태그, 서비스 상태가 모두 맞아야 웹 접속이 가능하다.

---