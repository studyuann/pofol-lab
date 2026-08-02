---
title: "3장 Namespace"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "쿠버네티스"]
is_public: true
draft: false
---

# 3장. Namespace

---

# 3-1. Namespace란 무엇인가?

## 🔹 개념

Namespace는 **클러스터 내부의 논리적 분리 공간**입니다.

> 하나의 Kubernetes 클러스터를 여러 팀, 여러 프로젝트가 함께 사용할 수 있도록 구분하는 기능

---

## 🔹 왜 필요한가?

### 예시 상황

* 개발팀(dev)

* 운영팀(prod)

* 테스트팀(test)

모두 같은 클러스터를 사용한다면?

```
my-app
my-app
my-app
```

이름 충돌 발생 ❗

---

Namespace를 사용하면:

```
dev/my-app
prod/my-app
test/my-app
```

→ 동일한 이름 사용 가능

→ 리소스 격리 가능

→ 접근 제어 가능

---

# 3-2. 기본 Namespace 확인

Kubernetes에는 기본 Namespace가 존재합니다.

```
kubectl get namespaces
```

출력 예:

```
NAME              STATUS   AGE
default           Active   30d
kube-system       Active   30d
kube-public       Active   30d
kube-node-lease   Active   30d
```

---

## 🔹 기본 Namespace 설명

| Namespace | 역할 |
| --- | --- |
| default | 기본 작업 공간 |
| kube-system | 시스템 Pod 실행 |
| kube-public | 공개 리소스 |
| kube-node-lease | 노드 상태 관리 |

---

# 3-3. Namespace 생성 실습

---

## 1️⃣ 명령어로 생성

```
kubectl create namespace dev
kubectl create namespace prod
```

확인:

```
kubectl get ns
```

---

## 2️⃣ YAML로 생성

```
# dev-ns.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: dev
```

적용:

```
kubectl apply -f dev-ns.yaml
```

---

# 3-4. Namespace 안에 리소스 생성

Namespace를 지정하지 않으면 기본값은 `default`입니다.

---

## 1️⃣ 특정 Namespace에 Pod 생성

```
kubectl run nginx-dev --image=nginx -n dev
```

확인:

```
kubectl get pods -n dev
```

---

## 2️⃣ YAML로 Namespace 지정

```
apiVersion: v1
kind: Pod
metadata:
  name: nginx-prod
  namespace: prod
spec:
  containers:
  - name: nginx
    image: nginx
```

```
kubectl apply -f pod-prod.yaml
```

---

# 3-5. Namespace별 리소스 격리 확인

```
kubectl get pods -n dev
kubectl get pods -n prod
kubectl get pods -n default
```

→ 서로 보이지 않음

---

# 3-6. 현재 기본 Namespace 변경

매번 `-n` 옵션 쓰는 건 번거롭습니다.

현재 context의 기본 Namespace 변경:

```
kubectl config set-context --current --namespace=dev
```

확인:

```
kubectl config view --minify | grep namespace:
```

이제:

```
kubectl get pods
```

→ dev namespace 기준으로 조회됨

namespace용 유틸리티 kubens 설치

```
sudo snap install kubectx --classic
```

네임스페이스 목록 확인 및 현재 위치 확인:

```
kubens
```

네임스페이스 전환 (예: kube-system으로 변경):

```
kubens kube-system
```

---

# 3-7. Namespace 삭제

```
kubectl delete namespace dev
```

⚠️ 주의:

Namespace 삭제 시

→ 내부 모든 리소스 자동 삭제

---

# 3-8. Namespace와 리소스 범위

모든 리소스가 Namespace에 속하는 것은 아닙니다.

---

## 🔹 Namespace에 속하는 리소스

* Pod

* Deployment

* Service

* ConfigMap

* Secret

* PVC

---

## 🔹 Cluster 범위 리소스

* Node

* Namespace

* PersistentVolume

* StorageClass

* ClusterRole

* CRD

확인:

```
kubectl api-resources --namespaced=true
kubectl api-resources --namespaced=false
```

---

# 3-9. 실무에서 Namespace 활용

---

## 🔹 환경 분리

```
dev
staging
prod
```

---

## 🔹 팀별 분리

```
frontend
backend
data
```

---

## 🔹 리소스 제한

* ResourceQuota

* LimitRange

예:

```
dev namespace는 CPU 4core 제한
```

---

# 3-10. 실습 과제

---

### ✔ 과제 1

* namespace test 생성

* nginx Pod 생성

* test namespace에서만 조회

---

### ✔ 과제 2

* dev namespace에 2개의 Pod 생성

* prod namespace에 1개 생성

* 각각 확인

---

### ✔ 과제 3

* 기본 namespace를 prod로 변경

* Pod 생성

* 실제 생성 위치 확인

---

# 3-11. 핵심 정리

```
1. Namespace는 논리적 분리 공간
2. 이름 충돌 방지
3. 리소스 격리
4. 접근 제어 가능
5. 모든 리소스가 Namespace에 속하는 것은 아니다
```

---