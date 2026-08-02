---
title: "AWS Backup 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "모범사례기반 AWS 고급아키텍처 설계"]
is_public: true
draft: false
---

# AWS Backup 실습

# 1. 실습 개요

## 1.1 실습 목표

이 실습에서는 AWS Backup을 이용해 EC2 리소스를 보호하는 전체 흐름을 학습한다.

실습을 통해 다음 내용을 확인한다.

* AWS Backup 서비스 구조 이해

* Backup Vault 생성

* Backup Plan 생성

* 리소스 할당(Resource Assignment)

* On-demand Backup 수행

* Recovery Point 확인

* 백업 데이터 복구

* 백업/복구 작업 상태 점검

---

## 1.2 실습 대상

이번 실습은 다음 리소스를 기준으로 진행한다.

* EC2 인스턴스 1대

* 해당 EC2에 연결된 EBS 볼륨

* AWS Backup 기본 서비스 역할 또는 자동 생성 역할

---

# 2. AWS Backup 기본 개념

## 2.1 Backup Vault

Backup Vault는 백업 데이터를 저장하는 논리적 보관소다.

쉽게 말하면 다음과 같이 이해하면 된다.

```
실제 서버/DB/볼륨 → 백업 수행 → Backup Vault 안에 Recovery Point 생성
```

즉, 백업 결과물이 들어가는 장소가 Backup Vault다.

특징

* Recovery Point 저장 위치

* KMS 키를 통한 암호화 가능

* 여러 백업 계획이 같은 Vault를 사용할 수 있음

---

## 2.2 Backup Plan

Backup Plan은 **언제**, **어떻게**, **얼마나 오래** 백업할지를 정의하는 정책이다.

예를 들어 다음과 같은 정책을 만들 수 있다.

```
매일 새벽 2시 백업
보관 기간 7일
백업 대상은 태그가 Backup=Yes 인 리소스
```

---

## 2.3 Resource Assignment

Backup Plan만 만든다고 바로 백업이 수행되지는 않음.

어떤 리소스를 그 계획에 포함할지 지정해야 한다.

이 과정을 Resource Assignment라고 한다.

지정 방식은 주로 다음 두 가지다.

* 리소스를 직접 선택

* 태그 기반으로 자동 선택

실습에서는 이해가 쉬운 **직접 선택 방식** 또는 **명확한 태그 기반 방식**을 사용한다.

---

## 2.4 On-demand Backup

정기 백업 계획과 별개로, 필요할 때 즉시 한 번 백업하는 기능이다.

예를 들어 다음과 같은 상황에서 사용한다.

* 운영 변경 전 임시 백업

* 패치 전 백업

* 실습 중 즉시 백업 테스트

AWS Backup은 자동 백업 계획 외에도 수동으로 On-demand Backup을 생성할 수 있음. ([AWS 문서](https://docs.aws.amazon.com/aws-backup/latest/devguide/recov-point-create-on-demand-backup?utm_source=chatgpt.com))

---

## 2.5 Recovery Point

Recovery Point는 실제 백업 결과물이다.

즉,

```
백업 1회 실행 = Recovery Point 1개 생성
```

이 Recovery Point를 이용해서 나중에 복구를 수행한다.

---

# 3. 실습 아키텍처

이번 실습 구조는 다음과 같다.

```
EC2 Instance
   │
   └─ EBS Volume
         │
         ▼
AWS Backup
   ├─ Backup Plan
   ├─ Backup Vault
   └─ Recovery Point
         │
         ▼
Restore
   ▼
New EC2 / New EBS Resource
```

---

# 4. 실습 사전 준비

## 4.1 준비 사항

다음 리소스가 미리 준비되어 있어야 한다.

* 실행 중인 EC2 인스턴스 1대

* 해당 인스턴스가 정상 동작 중일 것

* AWS 콘솔 접속 권한

* AWS Backup 사용 권한

* EC2 조회 및 복구 권한

---

## 4.2 권장 태그 설정

실습 편의를 위해 EC2 인스턴스에 다음 태그를 추가한다.

| Key | Value |
| --- | --- |
| Name | backup-lab-ec2 |
| Backup | Yes |

이 태그는 나중에 Backup Plan에서 리소스를 자동 선택할 때 사용 가능하다.

---

# 5. 실습 1 Backup Vault 생성

## 5.1 AWS Backup 콘솔 이동

AWS Management Console에서 다음으로 이동한다.

```
Services → AWS Backup
```

왼쪽 메뉴에서 다음 항목을 선택한다.

```
Backup vaults
```

---

## 5.2 Backup Vault 생성

다음 버튼을 선택한다.

```
Create backup vault
```

설정 예시는 다음과 같다.

```
Backup vault name: lab-backup-vault
Encryption key: aws/backup (기본 키 사용)
```

설명

* Vault 이름은 백업 보관소 이름이다.

* 기본 실습에서는 AWS 관리형 KMS 키를 사용해도 충분하다.

* 운영 환경에서는 고객 관리형 KMS 키를 별도로 설계하는 경우가 많다.

생성이 완료되면 Vault 목록에서 확인한다.

---

# 6. 실습 2 Backup Plan 생성

## 6.1 Backup Plan 메뉴 이동

왼쪽 메뉴에서 다음 항목을 선택한다.

```
Backup plans
```

다음 버튼을 선택한다.

```
Create backup plan
```

---

## 6.2 새 계획 생성

옵션에서 다음을 선택한다.

```
Build a new plan
```

예시 설정

```
Backup plan name: lab-backup-plan
Rule name: daily-backup-rule
Backup vault: lab-backup-vault
Backup frequency: Daily
Backup window: 기본값 사용
Lifecycle: Delete after 7 days
```

설명

### Backup plan name

백업 계획 전체 이름이다.

### Rule name

이 계획 안에서 실제 백업 규칙 이름이다.

하나의 Plan 안에 여러 Rule을 넣을 수도 있다.

### Backup frequency

백업 주기다.

예를 들어 매일 1회, 주기적으로 자동 수행되게 설정한다.

### Backup window

백업 작업이 시작될 수 있는 시간 범위다.

스케줄이 되더라도 이 윈도우 조건 내에서 실행된다.

### Lifecycle

생성된 Recovery Point를 얼마 동안 보관할지 정하는 설정이다.

보관 기간이 지나면 자동 삭제된다.

---

# 7. 실습 3 리소스 할당

## 7.1 Assign resources

Backup Plan 생성 후 다음 단계에서 리소스를 할당한다.

버튼

```
Assign resources
```

---

## 7.2 리소스 선택 방식

실습에서는 두 가지 방식 중 하나를 사용할 수 있다.

### 방식 1 직접 리소스 선택

* 특정 EC2 인스턴스를 직접 선택

### 방식 2 태그 기반 선택

* 예: `Backup=Yes`

태그 기반 방식 예시

```
IAM role: Default role
Resource selection:
  Include specific resource types: EC2
Tag key: Backup
Tag value: Yes
```

설명

* 태그 기반 방식은 운영 환경에서 매우 자주 사용한다.

* 새 서버를 추가할 때 태그만 붙이면 자동으로 백업 대상이 된다.

* 실습에서는 구조 이해를 위해 태그 방식이 더 교육 효과가 좋다.

---

## 7.3 IAM Role 설명

AWS Backup이 실제 백업 작업을 수행하려면 서비스 역할이 필요하다.

일반적으로 콘솔에서 기본 역할을 자동 생성하거나 기존 역할을 선택할 수 있다.

설명 포인트

* 사용자가 직접 백업 데이터를 복사하는 것이 아님

* AWS Backup 서비스가 권한을 위임받아 작업함

* 따라서 적절한 IAM Role이 필요함

---

# 8. 실습 4 On-demand Backup 수행

자동 계획과 별도로 즉시 백업을 수행해본다.

## 8.1 메뉴 이동

왼쪽 메뉴 또는 대시보드에서 다음을 선택한다.

```
Create on-demand backup
```

---

## 8.2 설정 입력

예시

```
Resource type: EC2
Instance ID: 실습용 EC2 선택
Backup window: 기본값
Transition to cold storage: 사용 안 함
Expire: 7 days
Backup vault: lab-backup-vault
IAM role: Default role
```

설명

### Resource type

무엇을 백업할지 선택한다.

여기서는 EC2를 선택한다.

### Backup window

백업 작업 허용 시간 범위다.

### Expire

백업 만료일이다.

지정한 기간이 지나면 자동 삭제된다.

### Backup vault

생성된 백업을 어느 Vault에 저장할지 선택한다.

### IAM role

AWS Backup이 작업할 때 사용할 권한이다.

---

## 8.3 작업 시작

다음 버튼을 선택한다.

```
Create on-demand backup
```

이후 Backup jobs 메뉴에서 작업 상태를 확인할 수 있다.

상태 예시

* CREATED

* PENDING

* RUNNING

* COMPLETED

* FAILED

백업 작업 상태는 리소스 유형별 백업 생성 문서에서도 확인 가능하며, 완료 후에는 Recovery Point가 생성된다.

---

# 9. 실습 5 Recovery Point 확인

## 9.1 Backup Vault에서 확인

왼쪽 메뉴에서 다음으로 이동한다.

```
Backup vaults → lab-backup-vault
```

Vault 상세 화면에서 Recovery Points를 확인한다.

확인 항목

* 리소스 유형

* 리소스 ARN

* 생성 시각

* 만료 시각

* 상태

---

## 9.2 핵심 설명

Recovery Point는 실제 백업 결과물이다.

즉,

```
백업 계획 = 정책
백업 작업 = 실행
Recovery Point = 결과물
```

이 관계를 반드시 구분해서 이해해야 한다.

---

# 10. 실습 6 백업 복구

이번에는 생성된 Recovery Point를 이용해 복구를 수행한다.

## 10.1 Recovery Point 선택

Vault 안에서 원하는 Recovery Point를 선택한다.

버튼

```
Restore
```

---

## 10.2 복구 설정

EC2 복구 시 입력 가능한 항목은 화면에 따라 다소 다를 수 있지만 일반적으로 다음과 같은 값을 지정한다.

예시

```
Resource name: restored-backup-lab-ec2
IAM role: 기본 복구 역할
Instance type: 기존과 동일 또는 소형 타입
Subnet: 실습용 Subnet
Security Group: 실습용 SG
```

설명

### Resource name

복구된 새 리소스 이름이다.

### Instance type

기존과 동일한 유형으로 복구할 수도 있고, 실습 목적상 더 작은 타입으로 선택할 수도 있다.

### Subnet / Security Group

복구 후 인스턴스가 어느 네트워크에서 동작할지 지정한다.

---

## 10.3 복구 실행

다음 버튼을 선택한다.

```
Start restore job
```

이후 Restore jobs 메뉴에서 상태를 확인한다.

상태 예시

* PENDING

* RUNNING

* COMPLETED

* FAILED

* ABORTED

---

# 11. 실습 7 복구 결과 검증

복구가 완료되면 EC2 콘솔로 이동하여 새 인스턴스가 생성되었는지 확인한다.

확인 항목

* 새로운 EC2 인스턴스 생성 여부

* 인스턴스 상태

* 연결된 볼륨 상태

* Name 태그 반영 여부

* 보안 그룹/Subnet 설정 정상 여부

검증 방법 예시

```
EC2 → Instances → restored-backup-lab-ec2 확인
```

필요하면 다음도 확인한다.

* SSH 접속 가능 여부

* 웹 서버라면 HTTP 응답 여부

* 원본 인스턴스와 설정 비교

---

# 12. 실습 8 작업 이력 확인

AWS Backup 콘솔에서 다음 메뉴를 확인한다.

```
Backup jobs
Restore jobs
Protected resources
```

각 메뉴 설명

### Backup jobs

백업 작업 실행 이력 확인

### Restore jobs

복구 작업 실행 이력 확인

### Protected resources

현재 AWS Backup으로 보호 중인 리소스 목록 확인

이 메뉴를 통해 단순히 백업을 생성하는 것뿐 아니라, 운영 관점에서 **무엇이 보호되고 있는지**, **어떤 작업이 실패했는지** 추적할 수 있다.

---

# 13. 실습 중 설명할 핵심 개념

## 13.1 백업과 스냅샷의 차이

학습 포인트는 다음과 같다.

* EBS 자체 스냅샷 기능도 존재함

* 하지만 AWS Backup은 여러 서비스의 백업을 중앙에서 통합 관리할 수 있음

* 즉, 서비스별 개별 백업 대신 정책 기반 관리가 가능해짐

---

## 13.2 자동 백업과 수동 백업의 차이

### 자동 백업

* Backup Plan 기반

* 정기 수행

* 운영 표준화에 적합

### 수동 백업

* 필요 시 즉시 수행

* 변경 작업 직전 백업에 적합

AWS Backup은 자동 및 수동 방식을 모두 지원한다.

---

## 13.3 복구의 의미

중요한 포인트는 다음이다.

```
백업이 있다는 것 ≠ 복구 가능성이 검증되었다는 것
```

즉, 실제 운영에서는 **Restore Test**가 매우 중요하다.

AWS Backup에는 복구 테스트 계획 기능이 있으며, 일정 기반으로 복구 테스트를 수행하고 복구 대상 리소스 및 Recovery Point 선택 기준을 정의할 수 있다. 복구 테스트 계획은 주기와 대상 시작 시간 등을 포함해 설정한다.

---

# 14. 확장 실습 아이디어

기본 실습이 끝나면 아래 내용을 추가로 확장할 수 있다.

## 14.1 태그 기반 자동 보호

새 EC2를 만들고 `Backup=Yes` 태그를 붙인 뒤 자동 포함되는지 확인

## 14.2 보관 주기 변경

7일 보관 대신 더 짧거나 긴 보관 기간 설정 후 차이 비교

## 14.3 여러 리소스 유형 실습

다음 리소스로 확장 가능

* EBS

* RDS

* DynamoDB

* EFS

## 14.4 복구 테스트 계획

Restore testing plan 생성 후 주기적 복구 검증 구조 이해

AWS Backup은 복구 테스트 기능을 제공하며, 계획 생성 후 선택 대상을 연결해 특정 또는 임의의 Recovery Point 기준으로 테스트를 수행할 수 있다. ([AWS 문서](https://docs.aws.amazon.com/aws-backup/latest/devguide/restore-testing?utm_source=chatgpt.com))

---

# 15. 실습 정리

이번 실습에서 수행한 흐름은 다음과 같다.

```
1. Backup Vault 생성
2. Backup Plan 생성
3. 리소스 할당
4. On-demand Backup 수행
5. Recovery Point 확인
6. Restore 수행
7. 복구 결과 검증
```