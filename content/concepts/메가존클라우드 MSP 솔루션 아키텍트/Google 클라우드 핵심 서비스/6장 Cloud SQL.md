---
title: "6장 Cloud SQL"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Google 클라우드 핵심 서비스"]
is_public: true
draft: false
---

# 6장. Cloud SQL

## 1. 장 개요

앞 장에서 Compute Engine과 Cloud Storage를 다뤘다면, 이제 웹 애플리케이션의 데이터 계층에 해당하는 **RDBMS 계층**을 이해하는 단계다.

AWS를 먼저 학습한 상태라면 Cloud SQL은 자연스럽게 **Amazon RDS**와 비교해서 이해할 수 있다.

익숙한 감각은 아래와 같다.

* 데이터베이스 엔진을 선택한다

* 인스턴스 크기를 정한다

* 스토리지와 백업을 설정한다

* 애플리케이션에서 DB로 접속한다

* 운영 편의를 위해 관리형 서비스를 사용한다

하지만 GCP에서는 아래 포인트를 같이 봐야 한다.

* Cloud SQL은 **MySQL, PostgreSQL, SQL Server**를 지원하는 완전관리형 서비스다.

* 연결 방식은 **Public IP**, **Private IP**, 또는 둘 다 사용할 수 있다.

* Public IP를 쓸 때는 **authorized networks** 같은 접근 제어를 반드시 고려해야 한다.

* Private IP를 쓰려면 VPC와의 사설 연결 구성을 이해해야 한다.

* 연결 방식은 직접 연결뿐 아니라 **Cloud SQL Auth Proxy** 또는 언어 커넥터를 사용할 수 있고, 공식 문서는 Auth Proxy를 권장 방식으로 설명한다.

* 고가용성은 생성 시 또는 이후에 활성화할 수 있다.

* 자동 백업과 백업 전략을 같이 봐야 한다.

---

## 2. 학습 목표

이 장을 마치면 다음이 가능해야 한다.

* Cloud SQL의 기본 개념을 설명할 수 있음

* Cloud SQL과 Amazon RDS의 공통점과 차이를 설명할 수 있음

* Cloud SQL이 지원하는 주요 엔진을 설명할 수 있음

* Public IP와 Private IP 연결 방식의 차이를 설명할 수 있음

* Cloud SQL Auth Proxy의 역할을 설명할 수 있음

* 고가용성과 자동 백업의 목적을 설명할 수 있음

* Compute Engine 또는 애플리케이션과 Cloud SQL의 연결 구조를 설명할 수 있음

* 콘솔 또는 CLI로 기본 Cloud SQL 생성 흐름을 설명할 수 있음

---

## 3. 핵심 키워드

* Cloud SQL

* Managed RDBMS

* MySQL

* PostgreSQL

* SQL Server

* Public IP

* Private IP

* Authorized Networks

* Cloud SQL Auth Proxy

* IAM Database Authentication

* Automated Backups

* High Availability

* Primary / Standby

* Connection Architecture

---

# 4. Cloud SQL이란 무엇인가

Cloud SQL은 Google Cloud의 **완전관리형 관계형 데이터베이스 서비스**다.

Google 공식 문서는 Cloud SQL이 MySQL, PostgreSQL, SQL Server용 완전관리형 관계형 데이터베이스 서비스라고 설명한다.

## 쉽게 이해하면

* AWS의 RDS와 가장 직접적으로 비교할 수 있는 서비스

* DB 엔진 설치, 패치, 기본 운영 부담을 줄여줌

* 애플리케이션은 일반적인 RDBMS처럼 접속해서 사용 가능

## 언제 사용하는가

* 웹 애플리케이션의 관계형 DB가 필요할 때

* 운영 부담을 줄이고 싶을 때

* 직접 DB 서버를 관리하고 싶지 않을 때

* 백업, 고가용성, 모니터링을 관리형으로 가져가고 싶을 때

---

# 5. Cloud SQL과 RDS 비교

## 5.1 공통점

* 관리형 관계형 데이터베이스 서비스

* MySQL, PostgreSQL 같은 엔진 지원

* 백업, 복구, 고가용성 기능 제공

* 애플리케이션과 네트워크 경로를 설계해야 함

## 5.2 차이점

* GCP에서는 연결 설계에서 **Public IP / Private IP / Auth Proxy** 조합을 더 명시적으로 설명하는 흐름이 강하다.

* Public IP를 사용하는 경우 허용 네트워크를 별도로 관리해야 한다.

* Private IP는 VPC 사설 연결 설계와 함께 봐야 한다.

* Cloud SQL은 관리형이므로 일부 고급 DB 권한이나 OS 수준 제어는 제한된다. 예를 들어 Cloud SQL for MySQL 문서는 `SUPER` 권한이 허용되지 않는다고 설명한다.

**Cloud SQL은 RDS와 매우 유사하지만, GCP에서는 DB 연결 방식을 네트워크와 프록시 관점에서 더 명확하게 설계해서 보는 감각이 중요함**

---

# 6. 지원 엔진

Cloud SQL은 다음 주요 엔진을 지원한다.

* MySQL

* PostgreSQL

* SQL Server

---

# 7. Cloud SQL 인스턴스의 기본 구성 요소

Cloud SQL 인스턴스를 생성할 때 보통 아래 요소를 함께 결정한다.

* DB 엔진

* 버전

* 인스턴스 이름

* 리전

* 머신/컴퓨팅 크기

* 스토리지 크기

* 백업 설정

* 고가용성 여부

* Public IP / Private IP

* 인증 및 연결 정책

이 항목들은 단순 생성 옵션이 아니라, 운영 구조 전체에 영향을 준다.

---

# 8. Public IP와 Private IP

Cloud SQL 연결에서 가장 먼저 이해해야 하는 것이 **연결 경로**다.

Cloud SQL은 public IP, private IP, 또는 둘 다 사용할 수 있다.

---

## 8.1 Public IP

Public IP 방식은 Cloud SQL 인스턴스가 공인 주소를 통해 접근 가능한 형태다.

공식 문서는 public IPv4 주소를 구성할 수 있고, 특정 IP 또는 IP 범위를 **authorized networks** 로 추가해 접속을 허용할 수 있다고 설명한다. 사설 대역은 authorized network로 지정할 수 없다.

### 장점

* 초기 테스트와 개념 이해가 쉬움

* 로컬 PC나 외부 환경에서 접속 테스트가 편함

### 단점

* 네트워크 노출 면이 커짐

* 허용 IP 관리가 필요함

* 운영 환경에서는 더 신중해야 함

---

## 8.2 Private IP

Private IP 방식은 Cloud SQL 인스턴스를 사설 네트워크 경로로 연결하는 방식이다.

공식 문서는 생성 과정에서 VPC 네트워크를 선택해 private IP를 구성할 수 있다고 설명한다.

### 장점

* 인터넷에 직접 노출하지 않음

* 애플리케이션과 DB를 내부망으로 연결 가능

* 운영 관점에서 더 안전한 구조를 만들기 쉬움

### 단점

* VPC 및 사설 연결 구성을 이해해야 함

* 로컬 PC에서 바로 접속하기는 더 복잡함

---

# 9. Cloud SQL Auth Proxy

Cloud SQL 연결 방식에서 매우 중요한 개념이다.

공식 문서는 Cloud SQL Auth Proxy가 public/private IP 모두에서 동작하며, 사용자 또는 서비스 계정 자격증명으로 연결을 검증하고, Cloud SQL 인스턴스로의 보안 연결을 제공한다고 설명한다. 또한 **권장 연결 방식**으로 소개한다.

## 9.1 왜 필요한가

애플리케이션이 DB에 연결할 때 인증과 네트워크 처리를 더 안전하고 단순하게 할 수 있다.

## 9.2 역할

* Cloud SQL 인증 처리 보조

* 보안 연결 구성

* 애플리케이션에서는 로컬 포트처럼 DB에 접근하는 형태 제공

---

# 10. 인증 방식

Cloud SQL 연결 시 데이터베이스 사용자로 인증해야 하며, **built-in authentication** 과 **IAM database authentication** 을 선택할 수 있다.

## 10.1 Built-in Authentication

전통적인 DB 사용자 계정 방식이다.

예시

* MySQL 사용자/비밀번호

* PostgreSQL 사용자/비밀번호

## 10.2 IAM Database Authentication

일부 시나리오에서는 IAM 기반 데이터베이스 인증을 사용할 수 있다.

---

# 11. 백업

Cloud SQL는 백업 옵션을 제공하며, 자동 백업 운영이 중요하다. 백업 옵션 문서는 인스턴스에 맞는 백업 구성을 선택하도록 설명한다. 또한 백업 관리 문서는 자동 백업 시간 창을 설정할 수 있다고 안내한다.

## 왜 중요한가

* 장애 시 복구 가능성 확보

* 실수로 삭제/손상된 데이터 복원 대비

* 운영 안정성 확보

---

# 12. 고가용성(HA)

Cloud SQL은 고가용성 구성을 생성 시 또는 기존 인스턴스에서 활성화할 수 있다.

## 왜 필요한가

* 단일 장애 지점 완화

* 장애 발생 시 서비스 지속성 향상

* 운영 환경 신뢰성 강화

---

# 13. Cloud SQL 연결 아키텍처 예시

이번 장은 실습보다 연결 구조 이해가 더 중요하므로, 아래 3가지 아키텍처를 비교 설명하면 좋다.

---

## 13.1 구조 A. 로컬 PC → Public IP → Cloud SQL

### 용도

* 초기 테스트

* 관리자 점검

* 간단한 데모

### 특징

* 쉬움

* 빠름

* 운영용으로는 노출 면이 커질 수 있음

---

## 13.2 구조 B. Compute Engine → Private IP → Cloud SQL

### 용도

* 전형적인 내부망 애플리케이션 구조

* 웹/앱 서버와 DB 분리 구조

### 특징

* 운영에 적합

* 보안적으로 유리

* VPC 구조 이해가 필요함

---

## 13.3 구조 C. 애플리케이션 → Auth Proxy → Cloud SQL

### 용도

* 인증과 보안 연결을 더 일관되게 가져가고 싶을 때

* 서비스 계정과 함께 안전한 연결을 구성할 때

### 특징

* 실무 친화적

* 권장 패턴에 가깝다.

---

# 15. 실습 1: Cloud SQL 생성 화면에서 핵심 설정 확인

## 콘솔 흐름

1. Google Cloud Console 접속

2. **Cloud SQL** 메뉴 이동

3. **인스턴스 만들기(Create instance)** 클릭

4. 엔진 선택
   * MySQL
   * PostgreSQL
   * SQL Server

5. 인스턴스 이름, 비밀번호, 리전, 구성 옵션 확인

## 확인 포인트

* 엔진 선택

* 리전 선택

* 연결 옵션

* 백업 옵션

* HA 옵션

* Public IP / Private IP 설정 위치

---

# 16. 실습 2: Public IP / Private IP 설정 위치 확인

## 콘솔에서 확인할 항목

* Connections 섹션

* Public IP 활성화 여부

* Private IP 활성화 여부

* Authorized networks 입력 영역

* VPC 선택 영역

---

# 17. 실습 3: Cloud SQL 인스턴스 생성 예시 CLI 확인

## 예시 명령

```
gcloud sql instances create mysql-lab-01 \
--database-version=MYSQL_8_0 \
--cpu=2 \
--memory=4GB \
--region=asia-northeast3 \
--root-password='MySecurePass123!'
```

### 명령 설명

* `gcloud sql instances create`

  Cloud SQL 인스턴스를 생성하는 명령이다.

* `mysql-lab-01`

  인스턴스 이름이다.

* `--database-version=MYSQL_8_0`

  사용할 DB 엔진과 버전을 지정한다.

* `--cpu=2` / `--memory=4GB`

  인스턴스 크기를 지정한다.

* `--region=asia-northeast3`

  리전을 지정한다.

* `--root-password=...`

  초기 관리자 비밀번호를 설정한다.

---

# 18. 실습 4: 인스턴스 정보 조회 예시

## 예시 명령

```
gcloud sql instances describe mysql-lab-01
```

### 확인 포인트

* 엔진 종류

* 리전

* IP 구성

* 백업 설정

* HA 여부

* 상태

---

# 19. 실습 5: DB 연결 구조 설명용 예시

이번 과정에서는 실제 DB 접속 대신 연결 구조를 설명하는 형태가 더 적절하다.

## 예시 시나리오

* 웹 서버 VM: `web-vm-01`

* DB: `mysql-lab-01`

* 연결 방식: Private IP 또는 Auth Proxy

## 설명 포인트

1. 사용자는 웹 서버의 Public IP로 접속

2. 웹 서버는 애플리케이션을 실행

3. 애플리케이션은 내부망 또는 Proxy를 통해 Cloud SQL에 접속

4. DB는 외부 사용자에게 직접 공개되지 않아도 됨

이 구조가 전형적인 2-tier 또는 3-tier 아키텍처의 기본 형태다.

---

# 20. 실습 6: Auth Proxy 개념 설명

public/private IP 모두에서 동작하며, 사용자 또는 서비스 계정 자격증명을 사용한다.

* 애플리케이션이 직접 DB 공인 IP에 붙는 것보다 안전하고 관리가 쉬움

* 서비스 계정 권한과 연결해 설명하기 좋음

* 이후 Cloud Run, GKE와 연결할 때도 중요한 개념이 됨

---

# 21. 장 요약

핵심은 다음과 같다.

* Cloud SQL은 MySQL, PostgreSQL, SQL Server를 지원하는 완전관리형 관계형 데이터베이스 서비스다.

* Cloud SQL은 Public IP, Private IP, 또는 둘 다를 통해 연결할 수 있다.

* Public IP를 사용할 때는 authorized networks 등 접근 제어가 중요하다.

* Private IP는 VPC 기반 내부망 연결 구조를 만드는 데 적합하다.

* Cloud SQL Auth Proxy는 권장 연결 방식으로 설명되며, 인증과 보안 연결을 단순화한다.

* 자동 백업과 고가용성은 운영 환경에서 중요한 기본 설계 요소다.