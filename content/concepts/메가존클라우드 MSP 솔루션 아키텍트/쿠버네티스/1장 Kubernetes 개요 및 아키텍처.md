---
title: "1장 Kubernetes 개요 및 아키텍처"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "쿠버네티스"]
is_public: true
draft: false
---

# 1장. Kubernetes 개요 및 아키텍처

---

# 1-1. 왜 Kubernetes인가?

## 🔹 Docker의 한계 (운영 관점)

Docker는 컨테이너 실행에는 매우 강력하지만,

**대규모 운영 환경에서는 한계**가 존재합니다.

### 실습: Docker의 운영 문제 확인

```
# 3개의 nginx 컨테이너 실행
docker run -d -p 8081:80 --name web1 nginx
docker run -d -p 8082:80 --name web2 nginx
docker run -d -p 8083:80 --name web3 nginx

# 컨테이너 확인
docker ps
```

---

### ❗ 문제 1: 컨테이너가 죽으면?

```
docker stop web1
docker ps
```

→ 자동 복구되지 않음

→ 관리자가 직접 재시작해야 함

---

### ❗ 문제 2: 여러 서버에 배포하려면?

* 서버 A

* 서버 B

* 서버 C

각 서버에 직접 SSH 접속 후 실행 필요

---

### ❗ 문제 3: 로드밸런싱은?

* 포트 수동 관리

* 별도 nginx 또는 HAProxy 설정 필요

---

## 🔴 정리: Docker는 “컨테이너 실행 도구”

```
✗ 단일 호스트 중심
✗ 자동 복구 없음
✗ 클러스터 관리 불가
✗ 선언적 관리 불가
```

---

# 1-2. Kubernetes의 핵심 철학

## 🔹 선언적(Declarative) 모델

Kubernetes는 **원하는 상태(Desired State)** 를 선언합니다.

```
spec:
  replicas: 3
```

의미:

> “nginx는 항상 3개 유지”

Kubernetes는:

* 3개 실행

* 죽으면 자동 재생성

* 노드가 죽으면 다른 노드에 재배치

---

## 🔹 Docker vs Kubernetes 비교

| 구분 | Docker | Kubernetes |
| --- | --- | --- |
| 목적 | 컨테이너 실행 | 컨테이너 오케스트레이션 |
| 관리 단위 | 컨테이너 | Pod |
| 여러 개 관리 | 수동 | Deployment |
| 자동 복구 | 없음 | 있음 |
| 스케일링 | 수동 | 자동 |
| 로드밸런싱 | 별도 설정 | Service |

---

# 1-3. Kubernetes 아키텍처

Kubernetes는 크게 두 영역으로 구성됩니다.

```
Control Plane + Worker Node
```

---

## 🔵 전체 구조

```
                ┌────────────────────┐
                │   Control Plane    │
                │--------------------│
                │  API Server        │
                │  Scheduler         │
                │  Controller Mgr    │
                │  etcd              │
                └──────────┬─────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼───────┐     ┌────▼───────┐     ┌────▼───────┐
   │ Worker1    │     │ Worker2    │     │ Worker3    │
   │------------│     │------------│     │------------│
   │ kubelet    │     │ kubelet    │     │ kubelet    │
   │ kube-proxy │     │ kube-proxy │     │ kube-proxy │
   │ containerd │     │ containerd │     │ containerd │
   │ Pod        │     │ Pod        │     │ Pod        │
   └────────────┘     └────────────┘     └────────────┘
```

---

# 1-4. Control Plane 구성요소

---

## 1️⃣ API Server

* 모든 요청의 진입점

* kubectl 명령은 모두 API Server로 전달

* REST API 기반

실습:

```
kubectl cluster-info
```

---

## 2️⃣ etcd

* 분산 Key-Value 저장소

* 클러스터의 모든 상태 저장

* Pod, Service, ConfigMap 등 저장

👉 etcd = Kubernetes의 DB

---

## 3️⃣ Scheduler

* 새 Pod이 어느 노드에 배치될지 결정

* CPU, Memory 요청 고려

* 노드 상태 고려

---

## 4️⃣ Controller Manager

* “현재 상태”와 “원하는 상태”를 비교

* 다르면 수정

예:

```
replicas: 3
→ 현재 2개면?
→ 1개 생성
```

---

# 1-5. Worker Node 구성요소

---

## 1️⃣ kubelet

* 각 노드에서 실행

* API Server 지시 수신

* Pod 생성/상태 모니터링

---

## 2️⃣ kube-proxy

* Service 네트워크 구현

* Pod 간 통신 라우팅

---

## 3️⃣ Container Runtime

* 실제 컨테이너 실행

* containerd (현재 표준)

* Docker는 CRI 미지원으로 제외됨

---

# 1-6. Kubernetes의 핵심 오브젝트

---

# ✅ Pod

> 컨테이너가 실제로 실행되는 최소 단위

* 하나 이상의 컨테이너 포함

* 동일 IP 공유

* 쿠버네티스의 가장 기본 객체

👉 하지만 **직접 운영용으로 쓰는 경우는 거의 없음**

→ 보통 Deployment가 관리함

---

# ✅ Deployment

> Pod을 관리하는 오브젝트

* replicas 유지

* Rolling Update 지원

* 자동 재시작

* 롤백 가능

👉 **실무에서 가장 많이 사용하는 오브젝트**

---

# ✅ Service

> Pod에 접근하기 위한 네트워크 추상화

* Pod IP는 계속 바뀜

* Service는 고정된 접근점 제공

* ClusterIP / NodePort / LoadBalancer 제공

👉 Pod을 외부/내부에서 접근하려면 필수

---

# ✅ Namespace

> 리소스 논리적 격리 단위

* 팀 단위 분리

* 환경(dev/prod) 분리

* RBAC 적용 범위 구분

👉 운영 환경에서는 거의 필수

# 1-7. 동작 흐름 이해 (중요)

예: nginx 3개 생성 요청

```
1. kubectl apply
2. API Server가 요청처
3. etcd에 기록
4. Controller가 감지
5. Scheduler가 노드 선택
6. kubelet이 Pod 생성
7. containerd가 컨테이너 실행
```

# 1️⃣ kubectl apply

사용자가 다음과 같이 실행했음.

```
kubectl apply-f pod.yaml
```

이 순간 일어나는 일:

* kubectl은 YAML을 읽음

* kubeconfig에 있는 API Server 주소로 요청을 보냄

* HTTP REST 요청 형태로 전송됨 (POST / PATCH)

즉,

> “이런 상태가 되길 원함” 이라는 선언을 API Server에 전달한 것임.

---

# 2️⃣ API Server 저장

API Server는 쿠버네티스의 중앙 관문임.

역할:

* 인증 (Authentication)

* 권한 확인 (Authorization)

* 요청 유효성 검사

* 객체 구조 검증

YAML이 올바르면 내부 오브젝트로 변환함.

이때 중요한 점:

> 아직 Pod가 실행된 건 아님
>
> 단지 “원하는 상태”가 저장될 준비가 된 것뿐임

---

# 3️⃣ etcd에 기록

API Server는 최종적으로 상태를 **etcd**에 저장함.

etcd는:

* 분산 Key-Value 저장소

* 쿠버네티스의 “상태 데이터베이스”

* 클러스터의 모든 리소스 상태 저장

즉,

> etcd에 “이런 Pod가 존재해야 한다”라는 데이터가 기록됨.

이 시점에서도 아직 실행은 안 됨.

---

# 4️⃣ Controller가 감지

쿠버네티스에는 여러 Controller가 존재함.

예:

* Deployment Controller

* ReplicaSet Controller

* Node Controller 등

Controller의 역할은:

> 현재 상태와 원하는 상태를 비교하는 것

예를 들어:

* replicas=3인데 현재 Pod가 0개임

* 그러면 Controller가 3개 생성해야 한다고 판단함

이 과정을 **Reconciliation Loop**라고 함.

---

# 5️⃣ Scheduler가 노드 선택

Pod이 생성 대상이 되면,

Scheduler가 다음을 판단함:

* 어떤 노드가 적절한가?

* CPU, Memory 충분한가?

* taint/toleration 조건 만족하는가?

* affinity 조건 만족하는가?

그 후:

> 해당 Pod을 특정 Node에 바인딩함

이 과정을 “스케줄링”이라고 함.

---

# 6️⃣ kubelet이 Pod 생성

이제 해당 노드에 있는 kubelet이 동작함.

kubelet은:

* API Server를 지속적으로 감시함

* “이 노드에 Pod 배치됨”을 확인함

그 후:

* Pod 명세(spec) 확인

* 볼륨 준비

* 네트워크 설정 요청(CNI)

* 컨테이너 실행 준비

즉,

> kubelet이 실제 실행 담당자임.

---

# 7️⃣ containerd가 컨테이너 실행

kubelet은 직접 컨테이너를 실행하지 않음.

대신:

> Container Runtime에게 실행 요청함

보통:

* containerd : 범용 컨테이너 런타임. 쿠버네티스 기본 런타임

* CRI-O : 쿠버네티스 전용 런타임

containerd가 하는 일:

1. 이미지 pull

2. 컨테이너 생성

3. 네임스페이스 설정

4. cgroup 설정

5. 프로세스 시작

이제 컨테이너가 실제로 동작함.

---

# 1-8. 실습: 클러스터 상태 확인

```
# 노드 확인
kubectl get nodes -o wide

# 시스템 Pod 확인
kubectl get pods -n kube-system

# API 자원 목록
kubectl api-resources
```

---

# 1-9. 정리

```
1. Kubernetes는 "원하는 상태"를 선언한다.
2. Control Plane이 상태를 관리한다.
3. Pod가 최소 배포 단위다.
4. Service가 로드밸런싱을 제공한다.
5. 모든 상태는 etcd에 저장된다.
```

---