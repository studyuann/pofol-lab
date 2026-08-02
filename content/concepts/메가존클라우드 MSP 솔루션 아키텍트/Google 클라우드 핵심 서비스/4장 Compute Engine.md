---
title: "4장 Compute Engine"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Google 클라우드 핵심 서비스"]
is_public: true
draft: false
---

# 4장. Compute Engine

## 1. 장 개요

이 장에서는 Google Cloud의 가상머신 서비스인 Compute Engine을 학습한다.

앞 장에서 VPC, Subnet, Firewall Rule을 준비했으므로, 이제 그 네트워크 위에 실제 워크로드를 배치하는 단계다.

AWS를 먼저 학습한 상태라면 Compute Engine은 가장 익숙하게 느껴질 수 있다.

* EC2처럼 VM을 만든다

* OS 이미지를 선택한다

* CPU/메모리 크기를 정한다

* 디스크를 붙인다

* 외부 IP를 연결한다

* 초기 설정 자동화를 위해 스크립트를 넣는다

하지만 GCP에도 분명한 차이가 있다.

* 인스턴스를 생성할 때 **머신 패밀리 / 머신 시리즈 / 머신 타입** 구조로 자원을 선택한다.

* 부팅 디스크와 추가 디스크를 함께 설계하고, Persistent Disk는 네트워크 블록 스토리지로 제공된다.

* Startup Script는 메타데이터를 통해 실행되며, 공개 이미지에는 게스트 환경이 기본 포함되어 있다.

* Service Account를 인스턴스에 연결해 워크로드 권한을 주는 방식이 중요하다.

* 네트워크 태그와 결합해 방화벽 제어를 연결해서 봐야 한다.

즉, 이 장은 VM 한 대를 띄우는 법만 배우는 장이 아니라,

**실제 클라우드 서버를 어떻게 배치하고 초기화하고 권한과 네트워크를 붙이는지**를 배우는 장이다.

---

## 2. 학습 목표

* Compute Engine 인스턴스의 기본 개념을 설명할 수 있음

* 머신 패밀리, 시리즈, 머신 타입의 의미를 설명할 수 있음

* 이미지와 부팅 디스크의 관계를 설명할 수 있음

* Persistent Disk의 역할과 특징을 설명할 수 있음

* 외부 IP와 내부 IP의 역할을 설명할 수 있음

* Startup Script를 이용한 초기 설정 자동화를 설명할 수 있음

* Service Account를 VM에 연결하는 이유를 설명할 수 있음

* 웹 서버 VM을 생성하고 접속 테스트를 수행할 수 있음

* AWS EC2와 GCP Compute Engine의 공통점과 차이점을 비교할 수 있음

---

## 3. 핵심 키워드

* Compute Engine

* VM Instance

* Machine Family

* Machine Series

* Machine Type

* Image

* Boot Disk

* Persistent Disk

* External IP

* Internal IP

* Startup Script

* Metadata

* Service Account

* Network Tag

---

# 4. Compute Engine이란 무엇인가

Compute Engine은 Google Cloud에서 가상머신을 실행하는 서비스다.

## 쉽게 이해하면

* AWS의 EC2와 가장 유사한 서비스

* 사용자가 OS 수준까지 제어할 수 있는 IaaS 컴퓨팅 서비스

* 직접 패키지 설치, 웹 서버 구성, 애플리케이션 배포 가능

## 언제 사용하는가

* 서버를 직접 운영해야 할 때

* 기존 VM 기반 애플리케이션을 옮길 때

* 세밀한 OS 제어가 필요할 때

* 네트워크와 디스크 구조를 직접 설계해야 할 때

---

# 5. AWS EC2와의 비교

## 5.1 공통점

* 가상머신을 생성해서 사용함

* Linux / Windows 이미지 선택 가능

* CPU, 메모리, 디스크, 네트워크를 함께 설계함

* SSH 또는 RDP로 접속 가능

* 초기 설정 자동화 기능이 있음

## 5.2 차이점

* AWS는 인스턴스 타입 개념이 익숙하고, GCP는 머신 패밀리/시리즈/타입 구조가 더 드러남.

* AWS EBS와 유사한 GCP의 Persistent Disk는 네트워크 블록 디바이스로 제공되며, 인스턴스와 분리된 지속 스토리지 개념이 강하다.

* AWS User Data와 유사한 기능이 GCP Startup Script인데, GCP는 인스턴스 메타데이터를 기반으로 게스트 에이전트가 이를 실행한다.

* IAM Role for EC2에 대응되는 개념으로 Service Account를 자주 사용한다.

**Compute Engine은 EC2와 비슷하지만, GCP 방식으로는 네트워크·권한·초기화 자동화를 더 일관되게 묶어서 보는 감각이 중요함**

---

# 6. 인스턴스의 기본 구성 요소

Compute Engine 인스턴스를 만들 때는 대체로 아래 요소를 함께 결정한다.

* 이름

* Region / Zone

* 머신 타입

* OS 이미지

* 부팅 디스크

* 네트워크와 서브넷

* 외부 IP 여부

* 방화벽 대상 태그

* Service Account

* Startup Script

이 항목들은 단순히 생성 화면 옵션이 아니라, 실제 운영 설계의 핵심 요소다.

---

# 7. 머신 패밀리, 시리즈, 머신 타입

Google Cloud는 인스턴스 크기를 고를 때 **머신 패밀리 → 머신 시리즈 → 머신 타입** 구조를 사용한다. 예를 들어 N2 시리즈 안에 `n2-standard-4` 같은 머신 타입이 있다.

## 7.1 머신 패밀리

큰 범주의 용도 구분이다.

예시 개념

* 범용(General-purpose)

* 컴퓨팅 최적화

* 메모리 최적화

## 7.2 머신 시리즈

같은 패밀리 안에서 세대나 특성을 나눈다.

예시

* E2

* N2

* C 계열

## 7.3 머신 타입

실제로 선택하는 VM 크기다.

예시

* `e2-micro`

* `e2-medium`

* `n2-standard-2`

* **작은 실습용**: `e2-micro`, `e2-small`

* **일반적인 테스트**: `e2-medium`, `e2-standard-*`

* **더 많은 CPU/메모리 필요 시**: N2 계열 등

### AWS 비교

AWS의 `t3.micro`, `t3.small`, `m5.large` 같은 인스턴스 타입과 유사하게 생각하면 된다.

다만 GCP는 CPU/메모리 성격을 시리즈 수준에서 설명하는 구조가 더 눈에 띈다.

---

# 8. 이미지(Image)와 부팅 디스크(Boot Disk)

## 8.1 이미지란 무엇인가

이미지는 운영체제와 기본 소프트웨어 구성이 담긴 템플릿이다.

Compute Engine은 공개 Linux/Windows 이미지와 사용자 정의 이미지를 지원한다.

예시

* Debian

* Ubuntu

* Rocky Linux

* Windows Server

## 8.2 부팅 디스크란 무엇인가

부팅 디스크는 실제 인스턴스가 부팅할 때 사용하는 디스크다.

이미지를 기반으로 생성되며 OS 파일 시스템이 들어 있다.

### AWS 비교

* AWS AMI ↔ GCP Image

* AWS 루트 볼륨(EBS 기반) ↔ GCP Boot Disk

이미지는 “설치 원본 템플릿”, 부팅 디스크는 “실제 인스턴스에 연결된 운영체제 디스크”.

---

# 9. Persistent Disk

Persistent Disk는 내구성을 갖는 블록 스토리지다. Google 문서는 Persistent Disk가 네트워크 블록 디바이스이며, 물리 호스트와 분리되어 있고, 인스턴스를 삭제해도 데이터를 유지하도록 분리/이동할 수 있다고 설명한다. 또한 성능은 디스크 크기, 머신 타입, vCPU 수 등의 영향을 받는다.

## 9.1 핵심 특징

* 네트워크 기반 블록 스토리지

* 부팅 디스크 또는 데이터 디스크로 사용 가능

* 인스턴스와 분리된 지속성 제공

* 필요 시 크기 조정 가능

* 추가 디스크를 붙여 데이터 분리 가능

## 9.2 왜 중요한가

VM 자체와 데이터를 분리해서 운영할 수 있다.

예를 들어 웹 서버를 다시 만들더라도 데이터 디스크를 재연결해 사용할 수 있다.

## AWS 비교

* EBS와 매우 유사한 개념

* 다만 GCP 에서는 “네트워크 블록 디바이스”라는 점이 더 직접적으로 설명된다.

초기 실습에서는 Boot Disk만으로 충분하지만,

운영 관점에서는

* OS와 데이터를 분리하면 관리가 쉬워짐

* 로그, 업로드 파일, DB 파일 등을 별도 디스크에 둘 수 있음

* 성능과 용량 요구가 커지면 디스크 설계가 중요해짐

---

# 10. 외부 IP와 내부 IP

## 10.1 내부 IP

같은 VPC 또는 연결된 네트워크 안에서 사용하는 사설 IP다.

인스턴스 간 내부 통신에 사용한다.

## 10.2 외부 IP

인터넷 또는 외부 네트워크에서 인스턴스에 접근할 때 사용하는 공인 IP다.

외부 IP가 있다고 해서 바로 접속되는 것은 아니다.

다음 조건이 모두 맞아야 한다.

* 인스턴스에 외부 IP가 있음

* 인바운드 방화벽 규칙이 있음

* OS 수준 접속 조건이 맞음

---

# 11. 정적 외부 IP(Static External IP)

외부 IP는 동적으로 할당할 수도 있고, 정적으로 예약할 수도 있다.

서비스 주소가 바뀌면 안 되는 경우에는 정적 외부 IP가 중요하다.

## 언제 쓰는가

* DNS를 특정 서버에 고정 연결할 때

* 운영 서버의 외부 주소를 고정할 때

* 방화벽 화이트리스트에 등록해야 할 때

### AWS 비교

* Elastic IP와 유사한 감각으로 이해하면 된다.

---

# 12. Startup Script

Startup Script는 VM이 부팅할 때 실행되는 스크립트다. Google 문서에 따르면 스크립트는 메타데이터에서 읽혀 실행되고, 공개 이미지에는 게스트 환경이 기본 포함되어 있으며, VM 수준 메타데이터 스크립트는 프로젝트 수준 스크립트보다 우선한다. Linux 스크립트는 네트워크가 준비된 뒤 실행된다.

## 12.1 왜 중요한가

반복적으로 해야 하는 초기 설정을 자동화할 수 있다.

예시

* 패키지 업데이트

* nginx 설치

* 인덱스 페이지 생성

* 애플리케이션 배포

* 에이전트 설치

## 12.2 AWS 비교

* AWS User Data와 매우 비슷한 목적

* 다만 GCP는 메타데이터와 게스트 에이전트 실행 구조로 설명하면 이해가 명확함

---

# 13. 메타데이터(Metadata)

GCP 인스턴스는 메타데이터를 통해 설정값을 전달받을 수 있다.

Startup Script 역시 메타데이터의 한 형태로 생각할 수 있다.

## 활용 예시

* startup-script

* 환경설정 값

* 애플리케이션 시작 파라미터

* 관리용 정보

---

# 14. Service Account와 VM

앞 장에서 배운 Service Account는 Compute Engine에서도 매우 중요하다.

## 왜 필요한가

VM 안의 애플리케이션이 GCP API에 접근해야 할 수 있기 때문이다.

예시

* 웹 서버가 Cloud Storage 파일을 읽음

* 배치 프로그램이 Pub/Sub에 메시지를 발행함

* 애플리케이션이 Secret Manager를 읽음

## 운영 원칙

* 사람 계정 자격증명을 VM 안에 두지 않음

* VM에 Service Account를 연결함

* 필요한 Role만 최소 권한으로 부여함

### AWS 비교

* EC2 인스턴스 프로파일과 IAM Role을 연결하는 감각과 유사

---

# 15. 네트워크 태그와 VM

앞 장에서 만든 방화벽 규칙이 `target-tags=web` 이었다면,

이번 장에서 만드는 VM에도 `web` 태그를 넣어야 한다.

## 왜 중요한가

방화벽 규칙은 이미 만들어져 있어도,

VM이 해당 대상 조건을 만족하지 않으면 실제로 적용되지 않는다.

---

# 16. 기본 실습 아키텍처

이번 장에서 사용할 구조는 아래와 같다.

* VPC: `initial-vpc`

* Subnet: `initial-subnet-web`

* Region/Zone: `asia-northeast3-a` 예시

* Firewall Rule:
  + `allow-ssh-web`
  + `allow-http-web`

* VM:
  + 이름: `web-vm-01`
  + 태그: `web`
  + OS: Debian 또는 Ubuntu
  + Startup Script: nginx 설치
  + 외부 IP: 임시 또는 정적

---

# 17. 실습 1: 현재 프로젝트와 네트워크 확인

## 17.1 프로젝트 확인

```
gcloud config get-value project
```

### 설명

현재 어떤 프로젝트에 VM을 만들지 확인한다.

프로젝트가 다르면 VPC도 다르고, 권한도 다르고, 비용 집계도 달라진다.

## 17.2 네트워크 확인

```
gcloud compute networks list
```

## 17.3 서브넷 확인

```
gcloud compute networks subnets list
```

## 17.4 방화벽 규칙 확인

```
gcloud compute firewall-rules list--filter="network:initial-vpc"
```

### 설명

이전 장에서 만든 VPC, 서브넷, 방화벽 규칙이 준비되어 있는지 확인한다.

---

# 18. 실습 2: Startup Script 파일 준비

## 18.1 예시 스크립트

```
cat > startup-web.sh<<'EOF'
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

  bash 인터프리터로 실행하겠다는 의미다.

* `apt-get update -y`

  패키지 목록을 최신 상태로 갱신한다.

* `apt-get install -y nginx`

  nginx 웹 서버를 자동 설치한다.

* `systemctl enable nginx`

  부팅 시 nginx가 자동 시작되도록 등록한다.

* `systemctl start nginx`

  현재 세션에서 nginx를 바로 실행한다.

* `echo ... > /var/www/html/index`

  웹 루트 디렉터리에 간단한 인덱스 페이지를 생성한다.

### 교육 포인트

Startup Script는 보통 인스턴스가 처음 뜰 때 반복적으로 해야 하는 설정을 자동화하는 데 쓴다.

실습에서는 nginx 설치가 가장 직관적이다.

---

# 19. 실습 3: VM 생성

## 19.1 CLI 명령

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

## 19.2 명령 상세 설명

### `gcloud compute instances create web-vm-01`

* 새 VM 인스턴스를 생성한다.

* `web-vm-01` 은 인스턴스 이름이다.

### `--zone=asia-northeast3-a`

* 인스턴스를 배치할 Zone을 지정한다.

* 서브넷은 리전 단위이고, VM은 존 단위로 배치된다.

### `--machine-type=e2-micro`

* 인스턴스 크기를 지정한다.

* 실습용으로는 비용이 비교적 낮고 가벼운 타입을 선택한다.

### `--subnet=initial-subnet-web`

* 인스턴스가 연결될 서브넷을 지정한다.

* 해당 서브넷의 내부 IP 대역을 사용하게 된다.

### `--tags=web`

* 인스턴스에 `web` 태그를 부여한다.

* 앞 장의 `allow-ssh-web`, `allow-http-web` 규칙이 이 태그를 기준으로 적용된다.

### `--image-family=debian-12`

* Debian 12 계열 최신 이미지 패밀리를 사용한다.

* 같은 패밀리 안에서 최신 이미지를 자동 선택한다.

### `--image-project=debian-cloud`

* Debian 공개 이미지를 제공하는 프로젝트를 지정한다.

### `--metadata-from-file=startup-script=startup-web.sh`

* 로컬 파일 내용을 인스턴스 메타데이터의 `startup-script` 키로 전달한다.

* 부팅 시 해당 스크립트가 자동 실행된다.

---

# 20. 실습 4: VM 상태 확인

## 20.1 인스턴스 목록 조회

```
gcloud compute instances list
```

### 확인 포인트

* 인스턴스 이름

* Zone

* INTERNAL\_IP

* EXTERNAL\_IP

* STATUS

## 20.2 특정 인스턴스 상세 확인

```
gcloud compute instances describe web-vm-01 \
--zone=asia-northeast3-a
```

### 확인 포인트

* 태그가 `web` 로 들어갔는지

* 연결된 네트워크와 서브넷

* 외부 IP가 할당됐는지

* 서비스 계정 정보

* 메타데이터에 startup-script가 들어갔는지

---

# 21. 실습 5: SSH 접속

## 21.1 gcloud를 이용한 SSH 접속

```
gcloud compute ssh web-vm-01 --zone=asia-northeast3-a
```

### 설명

* `gcloud compute ssh` 는 Compute Engine VM에 SSH 접속하는 명령이다.

* 필요한 SSH 키 관리와 접속 정보를 gcloud가 도와준다.

### 접속 후 확인 명령

```
hostname
ip addr
systemctl status nginx
curl localhost
```

### 각 명령 설명

* `hostname`

  현재 서버 이름 확인

* `ip addr`

  네트워크 인터페이스 및 내부 IP 확인

* `systemctl status nginx`

  nginx 서비스 실행 상태 확인

* `curl localhost`

  로컬에서 웹 서버 응답 확인

---

# 22. 실습 6: 웹 접속 테스트

## 22.1 외부 IP 확인

```
gcloud compute instances list
```

## 22.2 브라우저 접속

* `http://[EXTERNAL_IP]`

### 기대 결과

브라우저에서 아래와 비슷한 페이지가 떠야 한다.

```
<h1>GCP Compute Engine Web Server</h1>
```

### 접속이 안 될 때 점검 순서

1. VM이 Running 상태인가

2. 외부 IP가 있는가

3. `allow-http-web` 규칙이 있는가

4. VM 태그가 `web` 인가

5. nginx가 실행 중인가

---

# 23. 실습 7: 정적 외부 IP 예약 및 연결

## 23.1 정적 외부 IP 예약

```
gcloud compute addresses create web-ip-01 \
--region=asia-northeast3
```

### 설명

* `gcloud compute addresses create` 는 정적 IP를 예약한다.

* 외부 IP는 보통 리전 단위 주소로 예약한다.

## 23.2 예약된 주소 확인

```
gcloud compute addresses list
```

## 23.3 인스턴스에 정적 IP 연결

```
gcloud compute instances delete-access-config web-vm-01 \
--zone=asia-northeast3-a \
--access-config-name="external-nat"

gcloud compute instances add-access-config web-vm-01 \
--zone=asia-northeast3-a \
--access-config-name="external-nat" \
--address=web-ip-01
```

### 설명

* 기존 임시 외부 IP 구성을 제거한 뒤

* 예약해 둔 정적 외부 IP를 연결한다.

### AWS 비교

Elastic IP를 연결하는 것으로 이해하면 된다.

---

# 24. 실습 8: 추가 데이터 디스크 생성 및 연결 개념

## 24.1 디스크 생성

```
gcloud compute disks create web-data-disk-01 \
--zone=asia-northeast3-a \
--size=20GB \
--type=pd-balanced
```

### 설명

* `gcloud compute disks create` 는 별도 Persistent Disk를 만든다.

* `pd-balanced` 는 일반적인 균형형 디스크 타입 예시다.

* 추가 후 OS에서 해당 디스크를 사용할 수 있도록 설정을 해야한다.

## 24.2 인스턴스에 연결

```
gcloud compute instances attach-disk web-vm-01 \
--zone=asia-northeast3-a \
--disk=web-data-disk-01
```

---

# 25. 실습 9: Service Account 확인

인스턴스 상세 정보에서 어떤 Service Account가 연결되어 있는지 확인한다.

```
gcloud compute instances describe web-vm-01 \
--zone=asia-northeast3-a \
--format="get(serviceAccounts)"
```

---

# 26. Startup Script 동작 확인 포인트

Startup Script가 기대대로 실행되지 않았을 때는 아래를 점검한다.

* 스크립트 문법 오류가 없는가

* OS 이미지가 Debian/Ubuntu 계열인지, 명령이 맞는가

* 패키지 저장소 접근이 가능한가

* VM가 완전히 부팅되었는가

* 메타데이터가 제대로 전달됐는가

Linux에서는 메타데이터 기반 스크립트가 네트워크가 준비된 뒤 실행되므로, 아주 직후에는 설치가 아직 진행 중일 수도 있다.

---

# 27. 장 요약

이 장에서는 GCP의 가상머신 서비스인 Compute Engine을 학습했다.

핵심은 다음과 같다.

* Compute Engine은 Google Cloud의 VM 서비스다.

* 인스턴스 생성 시 머신 패밀리/시리즈/타입 구조로 자원을 선택한다.

* 이미지와 부팅 디스크를 구분해서 이해해야 한다.

* Persistent Disk는 인스턴스와 분리된 네트워크 블록 스토리지다.

* Startup Script는 메타데이터를 통해 전달되고 부팅 시 자동 실행된다.

* 외부 IP, 방화벽 규칙, 네트워크 태그는 함께 봐야 한다.

* Service Account는 VM 워크로드 권한 제어에 중요하다.

* AWS EC2와 유사하지만, GCP 방식으로는 네트워크, 초기화 자동화, 권한 연결을 한 번에 보는 것이 중요하다.