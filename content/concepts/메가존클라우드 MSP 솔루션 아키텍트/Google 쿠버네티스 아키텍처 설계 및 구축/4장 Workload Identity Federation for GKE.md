---
title: "4장 Workload Identity Federation for GKE"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Google 쿠버네티스 아키텍처 설계 및 구축"]
is_public: true
draft: false
---

# 4장. Workload Identity Federation for GKE

## 1. 장 개요

이 장에서는 GKE 워크로드가 Google Cloud API에 안전하게 접근하는 권장 방식인 **Workload Identity Federation for GKE**를 학습한다.

**클러스터 안에서 실행되는 애플리케이션이 Google Cloud 리소스에 어떤 자격으로 접근할 것인가**를 다룬다.

Kubernetes 환경에서는 보통 다음 요구가 있다.

* Pod가 Cloud Storage 버킷을 읽어야 함

* 애플리케이션이 Secret Manager에서 시크릿을 읽어야 함

* 배치 작업이 Pub/Sub에 메시지를 발행해야 함

* 컨테이너가 BigQuery나 Cloud SQL에 접근해야 함

나쁜 패턴 중 하나가 **서비스 계정 키 JSON 파일을 만들어 Pod 안에 넣는 방식**이다.Workload Identity Federation for GKE가 이런 **덜 안전한 방식**을 대체한다.

**GKE에서는 가능하면 서비스 계정 키 파일 대신 Workload Identity Federation for GKE를 사용해야 한다.**

---

## 2. 학습 목표

* Workload Identity Federation for GKE가 무엇인지 설명할 수 있음

* 왜 서비스 계정 키 파일 방식보다 안전한지 설명할 수 있음

* Kubernetes ServiceAccount와 Google Cloud IAM의 연결 구조를 설명할 수 있음

* 프로젝트의 workload identity pool 개념을 설명할 수 있음

* Standard 클러스터에서 Workload Identity Federation for GKE를 활성화하는 흐름을 설명할 수 있음

* Autopilot과 Standard에서의 차이를 설명할 수 있음

* EKS의 IRSA와 GKE의 Workload Identity Federation for GKE를 비교할 수 있음

* 샘플 워크로드에 Google Cloud 권한을 연결하는 실습 흐름을 따라갈 수 있음

---

## 3. 핵심 키워드

* Workload Identity Federation for GKE

* Kubernetes ServiceAccount

* IAM Service Account

* Workload Identity Pool

* Principal Identifier

* Direct Access

* Service Account Impersonation

* GKE Metadata Server

* IRSA Comparison

---

# 4. Workload Identity Federation for GKE란 무엇인가

Workload Identity Federation for GKE는 **GKE 워크로드에 IAM 정책 기반으로 Google Cloud API 접근 권한을 부여하는 방식**이다. 이 기능을 통해 Kubernetes 워크로드가 수동 설정이나 서비스 계정 키 파일 없이 특정 Google Cloud API에 접근할 수 있다. 또한 애플리케이션별로 **세분화된 개별 아이덴티티와 권한**을 줄 수 있다.

## 쉽게 이해하면

* Pod에 키 파일을 넣지 않음

* Kubernetes ServiceAccount를 기준으로 워크로드 아이덴티티를 만듦

* 그 아이덴티티에 IAM 권한을 연결함

* 워크로드는 짧은 수명 자격 증명에 가까운 방식으로 Google Cloud API를 사용함

## 왜 중요한가

이 기능을 사용하지 않을 경우의 문제점

* JSON 키 파일을 Secret으로 저장

* Pod에 마운트

* 유출 위험 증가

* 키 회전 부담 증가

* 권한 추적이 어려워짐

---

# 5. GKE에서 이 기능이 어떻게 동작하는가

Workload Identity Federation for GKE를 활성화하면 GKE가 해당 프로젝트에 고정 형식의 workload identity pool을 만든다. 형식은 다음과 같다.

`PROJECT_ID.svc.id.goog`

이 풀은 IAM이 Kubernetes 자격 증명을 신뢰하고 이해할 수 있도록 하는 이름 체계 역할을 한다. 또한 이 풀은 클러스터를 모두 삭제해도 프로젝트에서 제거되지 않는다.

## 핵심 흐름

1. 클러스터에서 Workload Identity Federation for GKE 활성화

2. Kubernetes ServiceAccount 생성

3. 해당 ServiceAccount를 기준으로 IAM 권한 부여

4. Pod가 그 ServiceAccount로 실행

5. Pod가 Google Cloud API 접근

---

# 6. Direct Access와 Service Account Impersonation

federated identity에 직접 IAM 역할을 주는 방식은 **direct access**, 서비스 계정에 대한 권한을 부여해 그 계정을 대신 사용하는 방식은 **service account impersonation이**다.

## 6.1 Direct Access

* Federated principal에 직접 리소스 권한 부여

* 중간 Google Cloud 서비스 계정 없이 바로 접근

## 6.2 Service Account Impersonation

* Kubernetes 워크로드가 특정 IAM Service Account를 대신 사용

* 조직 내 기존 서비스 계정 운영 체계와 연결하기 좋음

---

# 7. 왜 키 파일 방식보다 좋은가

Workload Identity Federation for GKE가 **서비스 계정 키 파일 같은 덜 안전한 방식**을 대체한다. 기존에 서비스 계정 private key JSON을 내려받아 쓰던 관행을 Workload Identity Federation for GKE로 대체할 수 있다.

## 키 파일 방식의 문제

* 장기 자격 증명 유출 위험

* Secret 저장과 배포 부담

* 회전 작업 복잡

* 누가 어떤 키를 쓰는지 추적 어려움

* 여러 워크로드에 같은 키를 재사용하기 쉬움

## WIF for GKE 방식의 장점

* 키 파일이 필요 없음

* 워크로드별 세분화된 권한 설계 가능

* IAM 기반 감사와 추적이 쉬움

* GKE와 Google Cloud가 기본 인프라를 관리함

---

# 8. Autopilot과 Standard에서의 차이

**Autopilot 클러스터는 Workload Identity Federation for GKE가 기본적으로 활성화**되어 있다. 반면 **Standard 클러스터는 클러스터 수준에서 먼저 활성화한 뒤, 노드풀에도 활성화**해야 한다. 기존 Standard 클러스터에 대해 활성화할 때는 기존 노드풀은 영향을 받지 않고, 새 노드풀부터 적용될 수 있다.

## Autopilot

* 기본 활성화

* 별도 활성화 절차 부담이 적음

* 보안 기본값 관점과 잘 맞음

## Standard

* 클러스터 수준 활성화 필요

* 이후 노드풀 수준 활성화 필요

* 기존 환경 마이그레이션 시 단계적 적용 고려 필요

---

# 9. EKS IRSA(IAM Roles for Service Accounts)와의 비교

## 공통점

* Kubernetes ServiceAccount를 기준으로 워크로드 권한을 연결

* 장기 키 파일 없이 클라우드 API 접근

* 워크로드별 최소 권한 원칙 적용 가능

* OIDC 기반 신뢰 구조 감각이 있음

## 차이점

* GKE에서는 프로젝트 수준의 workload identity pool을 GKE가 관리해준다

* 외부 IdP를 별도로 준비하지 않아도 된다

* GKE에서는 Google Cloud IAM과 더 직접적으로 연결되는 운영 흐름이 강하다

**EKS의 IRSA가 “AWS식 워크로드 권한 연결”이라면, GKE의 Workload Identity Federation for GKE는 “Google Cloud식 워크로드 권한 연결”이다. 목적은 비슷하지만 GKE는 플랫폼이 아이덴티티 풀과 연결 구조를 더 많이 관리해준다.**

---

# 10. 장 요약

* Workload Identity Federation for GKE는 Kubernetes 워크로드가 서비스 계정 키 파일 없이 Google Cloud API에 접근하도록 해준다.

* GKE는 프로젝트에 `PROJECT_ID.svc.id.goog` 형식의 workload identity pool을 사용한다.

* 이 방식은 애플리케이션별로 세분화된 권한 설계를 가능하게 한다.

* Google은 서비스 계정 키 파일 같은 덜 안전한 방식 대신 이 기능을 사용할 것을 권장한다.

* Autopilot은 기본 활성화이고, Standard는 클러스터 및 노드풀 수준 활성화가 필요할 수 있다.

* EKS의 IRSA와 유사한 문제를 해결하지만, GKE는 identity pool과 신뢰 구조를 플랫폼이 더 직접 관리해준다.

**GKE에서 워크로드가 Google Cloud 리소스에 접근해야 한다면, 기본 선택지는 서비스 계정 키 파일이 아니라 Workload Identity Federation for GKE여야 한다.**