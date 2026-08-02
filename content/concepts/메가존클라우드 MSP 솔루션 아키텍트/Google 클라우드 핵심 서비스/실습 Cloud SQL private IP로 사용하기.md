---
title: "실습 Cloud SQL private IP로 사용하기"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Google 클라우드 핵심 서비스"]
is_public: true
draft: false
---

# 실습. Cloud SQL : private IP로 사용하기

---

# 1. 학습 목표

* Cloud SQL 인스턴스를 생성하고 관리형 데이터베이스 서비스의 특징을 이해한다.

* **Private Service Access**를 구성하여 Cloud SQL에 **비공개 IP**를 할당하는 방법을 익힌다.

* **Cloud SQL Auth Proxy**의 역할과 동작 방식을 이해한다.

* Cloud SQL이 **비공개 IP만 사용하는 경우**, 어떤 환경에서 Proxy 접속이 가능한지 이해한다.

---

# 2. 실습 환경 구성도

이 실습은 다음과 같은 구조를 전제로 한다.

* 사용자 VPC

* Private Service Access로 Google 관리형 서비스 네트워크와 연결

* 비공개 IP만 가진 Cloud SQL 인스턴스

* 같은 VPC 내부의 VM 또는 해당 VPC에 연결된 환경에서 Cloud SQL Auth Proxy 실행

**중요**

Cloud SQL 인스턴스를 **비공개 IP 전용**으로 만들었다면, **Cloud SQL Auth Proxy도 해당 VPC에 접근 가능한 환경에서 실행해야 한다.**

예를 들어 다음 환경에서는 가능하다.

* 같은 VPC 안의 Compute Engine VM

* 해당 VPC와 VPN 또는 Interconnect로 연결된 온프레미스 환경

* PSC 등 별도 네트워크 구성이 완료된 환경

반대로, **일반 로컬 PC에서 단순 인터넷 연결만으로는 비공개 IP 전용 Cloud SQL에 직접 Proxy 연결할 수 없음**.

---

# 3. 주요 실습 단계

## [Step 1] Private Service Access 설정

Cloud SQL을 **비공개 IP**로 사용하려면, 먼저 내 VPC와 Google 관리형 서비스 네트워크 사이에 **Private Service Access** 연결을 만들어야 한다.

이 과정은 내부적으로 **예약 IP 범위 할당 + private connection 생성**으로 이루어진다.

### 1-1. 내부 IP 범위 예약

1. **VPC 네트워크** 메뉴로 이동한다.

2. VPC네트워크 선택

3. **비공개 서비스 액세스** 탭으로 이동한다.

4. **IP 범위 할당**을 생성한다.

예시 값

* 이름: `google-managed-services-<vpc-name>`

* IP 범위: `10.10.0.0/24` 또는 실습 환경에서 겹치지 않는 대역

### 1-2. Private connection 생성

1. **서비스에 대한 비공개 연결** 탭으로 이동한다.

2. 연결만들기를 선택한다.

3. 방금 예약한 내부 IP 범위를 선택한다.

4. 연결을 클릭한다.

**설명**

이 단계는 **Google 관리형 서비스 전용 연결을 구성하는 절차**라고 이해하는 것이 정확하다. Cloud SQL의 private IP는 이 연결을 기반으로 할당된다.

---

## [Step 2] Cloud SQL for MySQL 인스턴스 생성

이제 Cloud SQL 인스턴스를 생성한다.

1. **SQL** 메뉴로 이동한다.

2. **[인스턴스 만들기]** 클릭

3. 데이터베이스 엔진으로 **MySQL** 선택

### 2-1. 기본 설정

예시

* 인스턴스 ID: `my-db-instance`

* root 비밀번호: 직접 설정

* 데이터베이스 버전: `MySQL 8.0`

### 2-2. 연결 설정

가장 중요한 단계다.

* **공개 IP 할당 해제**

* **비공개 IP 사용 체크**

* 연결할 **VPC 네트워크 선택**

Cloud SQL에서 private IP를 사용하려면, 앞 단계의 **Private Service Access가 이미 준비되어 있어야 한다.**

### 2-3. 머신 및 스토리지 설정

실습용으로는 비용을 줄이기 위해 작은 사양을 선택한다.

예시 방향

* 에디션: `Enterprise`

* 머신 유형: **shared core 계열의 최소 사양**

* 스토리지: `HDD`

* 용량: `10GB`

**주의**

---

## [Step 3] 서비스 계정 및 IAM 권한 설정

Cloud SQL Auth Proxy는 접속 시 **Cloud SQL 인스턴스에 대한 IAM 권한**을 검사한다.

따라서 Proxy 실행 주체에는 최소한 **Cloud SQL Client** 권한이 필요하다.

### 3-1. 서비스 계정 생성

1. **IAM 및 관리 > 서비스 계정** 메뉴로 이동한다.

2. 서비스 계정 생성
   * 이름 예시: `sql-proxy-sa`

### 3-2. 역할 부여

다음 역할을 부여한다.

* `Cloud SQL Client`

  (`roles/cloudsql.client`)

### 3-3. 인증 방식

실습 환경에 따라 인증 방식이 달라진다.

### 방법 A. GCE VM에서 실행

* VM에 이 서비스 계정을 연결

* 별도 JSON 키 없이 **ADC(Application Default Credentials)** 방식 사용 가능

### 방법 B. 로컬 또는 별도 환경에서 실행

* 서비스 계정 키(JSON)를 발급해서 사용

**주의**

실무에서는 가능하면 **서비스 계정 키 파일 남발을 피하는 것**이 좋다.

하지만 교육용 로컬 실습에서는 JSON 키를 이용하면 동작 원리를 보여주기 쉽다.

---

## [Step 4] Cloud SQL Auth Proxy 실행

여기서 가장 중요한 점은 다음이다.

### 핵심 조건

* Cloud SQL 인스턴스가 **공개 IP**를 쓰면, 로컬 PC에서도 Proxy 사용이 비교적 단순하다.

* Cloud SQL 인스턴스가 **비공개 IP만** 쓰면, Proxy가 실행되는 장비도 **그 VPC에 네트워크적으로 접근 가능해야 한다.**

즉, 이번 실습처럼 **비공개 IP 기반 보안 구성을 강조**하려면, Proxy는 보통 다음 중 하나에서 실행한다.

* 같은 VPC 안의 Compute Engine VM

* VPN으로 해당 VPC에 접속된 PC

* 하이브리드 연결이 구성된 내부망 서버

---

## [Step 5] Proxy 실행 예시

### 5-1. 인스턴스 연결 이름 확인

형식은 다음과 같다.

```
PROJECT_ID:REGION:INSTANCE_ID
```

예시

```
my-project:asia-northeast3:my-db-instance
```

### 5-2. Proxy 실행 명령

### VM의 서비스 계정 권한을 사용하는 경우

이 경우 VM에 연결된 서비스 계정이 `Cloud SQL Client` 권한을 가지고 있어야 한다.

vm에서 browser를 띄울 수 없으므로 아래 명령으로 생성된 url을 로컬PC의 브라우저에 붙여넣고 google cloud에 로그인하여 인증한다. 인증 후 생성된 키값을 vm에 붙여 넣는다.

```
gcloud auth application-default login --no-launch-browser
```

```
./cloud-sql-proxy \
  --private-ip \
  my-project:asia-northeast3:my-db-instance
```

또는 포트를 명시하려면

```
./cloud-sql-proxy \
  --private-ip \
  --port=3306 \
  my-project:asia-northeast3:my-db-instance
```

**설명**

* `--private-ip`

  Proxy가 Cloud SQL의 **비공개 IP**로 연결하도록 지시한다. 기본적으로는 public IP를 시도할 수 있으므로, private IP 인스턴스 실습에서는 이 옵션을 명시하는 편이 명확하다.

* `--port=3306`

  로컬에서 열어둘 포트다. MySQL 기본 포트이므로 생략 가능하지만 명시하면 이해하기 쉽다.

---

## [Step 6] DB 클라이언트로 접속

Proxy가 정상 실행되면, 로컬 또는 실행 중인 장비에서는 다음 정보로 접속한다.

* Host: `127.0.0.1`

* Port: `3306`

* Username: MySQL 사용자 계정

* Password: MySQL 비밀번호

예시

```
mysql -h 127.0.0.1 -P 3306 -u root -p
```

**중요**

Cloud SQL Auth Proxy는 **네트워크 경로와 인증을 안전하게 중개**해 주는 도구다.

하지만 실제 데이터베이스 로그인은 여전히 **MySQL 계정**으로 수행한다. 즉, Proxy 권한과 DB 계정은 서로 다른 개념이다.

---

# 6. 정리

* **Private Service Access**는 Cloud SQL private IP 사용을 위한 선행 작업이다.

* **Cloud SQL Auth Proxy**는 IAM 기반 인증과 TLS 보호를 제공하는 접속 도구다.

* 하지만 **Cloud SQL이 private IP 전용이면, Proxy도 그 VPC에 접근 가능한 위치에서 실행해야 한다.** 이 부분이 가장 중요하다.