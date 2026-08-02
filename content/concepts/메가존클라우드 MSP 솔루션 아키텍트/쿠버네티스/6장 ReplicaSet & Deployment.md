---
title: "6장 ReplicaSet & Deployment"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "쿠버네티스"]
is_public: true
draft: false
---

# 6장. ReplicaSet & Deployment

---

# 1. Controller란 무엇인가?

**Controller = 원하는 상태(Desired State)를 실제 상태(Current State)와 일치시키는 자동 조정기**

쿠버네티스는 선언형(Declarative) 시스템임.

---

# 2. Controller 동작 원리

동작 구조는 다음과 같음.

1. 사용자가 `kubectl apply` 실행

2. API Server가 요청을 검증하고 etcd에 저장

3. Controller가 API Server를 Watch

4. Desired State와 Current State 비교

5. 차이가 있으면 수정 작업 수행

즉, Controller는:

* 계속 감시(Watch)

* 상태 비교(Reconcile)

* 수정(Action)

이 과정을 반복함.

이를 **Reconciliation Loop**라고 부름.

---

# 3. Control Loop 구조

간단히 표현하면:

```
while(true) {
  현재상태 = API 조회
  원하는상태 = Spec 확인
  차이점 계산
  수정 실행
}
```

이 루프가 계속 돈다고 보면 됨.

---

# 4. 주요 Controller 종류

쿠버네티스에는 여러 Controller가 있음.

[![](6%EC%9E%A5%20ReplicaSet%20&%20Deployment/image.png)](6%EC%9E%A5%20ReplicaSet%20&%20Deployment/image.png)

---

## 1) ReplicationController란?

**ReplicationController = 지정한 개수의 Pod를 유지하는 가장 초기 Controller**

ReplicaSet의 전신(구버전)임.

역할은 동일함.

> 항상 N개의 Pod를 유지한다.

## 2) ReplicaSet Controller

### 역할

* 지정한 개수만큼 Pod 유지

### 예시

```
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: nginx-rs
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx
```

Pod 하나 삭제해보면:

```
kubectl delete pod <pod이름>
```

→ 자동으로 새 Pod 생성됨.

왜?

ReplicaSet Controller가 감지했기 때문임.

---

## 3) Deployment Controller

ReplicaSet을 관리하는 상위 Controller임.

### 역할

* ReplicaSet 생성ㅊ

* Rolling Update 관리

* 롤백 지원

### 예시

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deploy
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.25
```

이미지 버전 변경:

```
kubectl set image deployment nginx-deploy nginx=nginx:1.26
```

→ 새로운 ReplicaSet 생성

→ 기존 ReplicaSet 점진적으로 감소

→ Rolling Update 수행

이 과정을 관리하는 것이 Deployment Controller임.

---

## 4) StatefulSet Controller

### 역할

* Pod 이름 고정

* 순차적 생성/삭제

* 영구 스토리지 연결

DB, Kafka, Redis 같은 Stateful 앱에서 사용함.

---

## 5) DaemonSet Controller

### 역할

* 모든 노드에 Pod 하나씩 배포

예:

* 로그 수집기

* 모니터링 에이전트

* CNI 플러그인

예시:

```
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-exporter
spec:
  selector:
    matchLabels:
      app: node-exporter
  template:
    metadata:
      labels:
        app: node-exporter
    spec:
      containers:
      - name: node-exporter
        image: prom/node-exporter
```

노드 추가하면 자동으로 Pod 생성됨.

---

## 6) Job Controller

### 역할

* 한 번 실행하고 종료되는 작업 관리

예:

* 배치 처리

* DB 마이그레이션

---

## 7) CronJob Controller

### 역할

* 스케줄 기반 실행

Linux cron과 동일 개념임.

---

# 1️⃣ Kubernetes 리소스 계층 구조

## 1.1 생성 관계도

```
Deployment (선언)
    ↓ 생성/관리
ReplicaSet (복제 관리)
    ↓ 생성/관리
Pod (실행 단위)
    ↓
Container (실행 프로세스)
```

👉 중요한 점

* 사용자는 **Deployment만 직접 관리**

* ReplicaSet은 대부분 직접 생성하지 않음

* Pod은 Deployment에 의해 생성됨

---

## 1.2 개념 정의

### 🔹 Pod

* 가장 작은 실행 단위

* 하나 이상의 컨테이너 포함

* 직접 운영용으로 사용하지 않음

* 삭제되면 사라짐 (관리 객체 필요)

---

### 🔹 ReplicaSet

역할:

> 지정된 수의 Pod을 항상 유지

특징:

* self-healing (자동 복구)

* 라벨 기반 Pod 관리

* 스케일링 가능

* 업그레이드 기능 없음

---

### 🔹 Deployment

역할:

> ReplicaSet을 관리하면서 배포 전략 제공

기능:

* Rolling Update

* Rollback

* 버전 관리

* 업그레이드 일시중지

* 자동 ReplicaSet 생성

👉 실무에서는 거의 항상 Deployment 사용

---

# 2️⃣ ReplicaSet

---

## 2.1 동작 원리

ReplicaSet의 컨트롤 루프:

```
1. desired replicas 확인
2. 현재 Pod 수 확인
3. 부족하면 생성
4. 초과하면 삭제
5. Pod 죽으면 다시 생성
```

핵심은:

> ReplicaSet은 "Pod 개수"만 관리한다.

---

## 2.2 YAML 구조 분석

```
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: nginx-rs
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.19
```

---

### 🔴 매우 중요

```
selector.matchLabels
=
template.metadata.labels
```

이 값이 반드시 동일해야 한다.

불일치하면:

* Pod이 관리되지 않음

* ReplicaSet이 계속 새 Pod 생성

---

## 2.3 자동 복구 실습

```
kubectl apply -f replicaset.yaml
kubectl get pods -w
```

다른 터미널:

```
kubectl delete pod <pod-name>
```

→ 즉시 새 Pod 생성

이것이 self-healing이다.

---

## 2.4 ReplicaSet의 한계

이미지를 수정해보자.

```
kubectl edit rs nginx-rs
```

image 변경

→ 기존 Pod은 그대로

→ 새 Pod만 변경된 이미지

즉,

> ReplicaSet은 무중단 업그레이드를 보장하지 않는다.

---

# 3️⃣ Deployment

---

## 3.1 Deployment의 핵심 역할

Deployment는 내부적으로:

```
새 ReplicaSet 생성
→ 기존 ReplicaSet 점진적 축소
→ 새 ReplicaSet 점진적 증가
```

즉,

> Deployment는 ReplicaSet을 교체하는 전략 관리자다.

---

## 3.2 Deployment YAML (보강 버전)

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
spec:
  replicas: 3
  revisionHistoryLimit: 5  # 이전 버전 보관 개수
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.19
        ports:
        - containerPort: 80
```

---

## 🔹 revisionHistoryLimit

이전 ReplicaSet을 몇 개까지 보관할지 지정.

기본값: 10

운영 환경에서는 관리 필요.

---

# 4️⃣ Rolling Update 내부 동작

예:

replicas: 3

maxSurge: 1

maxUnavailable: 1

의미:

* 최대 4개까지 생성 가능

* 최소 2개는 항상 유지

업데이트 흐름:

```
3 → 4 → 3 → 4 → 3
```

항상 최소 2개 유지 → 무중단

---

## 전략 비교

### RollingUpdate (기본)

* 하나씩 교체

* 무중단

### Recreate

```
strategy:
  type: Recreate
```

* 기존 Pod 모두 삭제

* 새 Pod 생성

* 다운타임 발생

DB처럼 단일 인스턴스 환경에서 사용

---

# 5️⃣ 실습: Deployment 업그레이드

---

## 5.1 이미지 변경

```
kubectl set image deployment/nginx-deployment nginx=nginx:1.20
```

---

## 5.2 실시간 관찰

```
kubectl get pods -w
```

관찰 포인트:

* 새 ReplicaSet 생성됨

* 기존 ReplicaSet 점진적 감소

확인:

```
kubectl get rs
```

→ 두 개의 ReplicaSet 존재

---

# 6️⃣ 롤백

---

## 히스토리 확인

```
kubectl rollout history deployment/nginx-deployment
```

---

## 특정 버전으로 롤백

```
kubectl rollout undo deployment/nginx-deployment --to-revision=1
```

Deployment는 내부적으로 이전 ReplicaSet을 다시 활성화한다.

---

# 7️⃣ Scale과 Rolling Update의 차이

스케일링:

```
kubectl scale deployment nginx-deployment --replicas=5
```

→ 동일 ReplicaSet 내부 Pod 수 변경

업그레이드:

```
kubectl set image ...
```

→ 새 ReplicaSet 생성

이 차이를 반드시 이해해야 한다.

---

# 8️⃣ Selector & Label

---

## 실습: 라벨 변경

```
kubectl get pods --show-labels
kubectl label pod <pod-name> app=other --overwrite
```

결과:

* Deployment가 해당 Pod을 관리하지 못함

* 새로운 Pod 생성

---

# 9️⃣ 트러블슈팅 보강

---

## Pod가 Pending 상태인 경우

```
kubectl describe pod <pod>
```

확인:

* Node 리소스 부족

* taints 문제

* 이미지 pull 실패

---

## 롤아웃이 멈춘 경우

```
kubectl rollout status deployment/<name>
kubectl describe deployment <name>
kubectl get events
```

---

## CrashLoopBackOff

```
kubectl logs <pod>
kubectl logs <pod> --previous
```

---

# 🔟 최종 정리

### ReplicaSet

* Pod 개수 유지

* 자동 복구

* 업그레이드 전략 없음

---

### Deployment

* ReplicaSet 관리

* 무중단 배포

* 롤백 가능

* 프로덕션 기본 단위

---

### 전체 생성 흐름

```
Deployment 생성
   ↓
ReplicaSet 자동 생성
   ↓
Pod 생성
   ↓
Container 실행
```

---