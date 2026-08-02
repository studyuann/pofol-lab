---
title: "13장 RBAC ServiceAccount"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "쿠버네티스"]
is_public: true
draft: false
---

# 13장. RBAC / ServiceAccount

---

# 1. Kubernetes 접근 제어 전체 구조

쿠버네티스에서 API 요청은 항상 다음 순서로 처리된다.

```
 Authentication (인증)
 Authorization (인가)
 Admission Control
```

---

## 1.1 Authentication (인증)

목적:

> "누구인가?" 식별한다.

인증 방식:

* Client Certificate

* Bearer Token

* ServiceAccount Token

* OIDC

* Webhook

API Server는 요청자가 누구인지 확인하고,

그 사용자 이름을 내부적으로 다음과 같이 표현한다:

```
system:serviceaccount:<namespace>:<sa-name>
```

예:

```
system:serviceaccount:dev:cicd-sa
```

---

## 1.2 Authorization (인가)

목적:

> "이 사용자가 이 작업을 할 수 있는가?"

인가 모듈 종류:

* RBAC (가장 일반적)

* ABAC

* Webhook

* Node Authorizer

실무에서는 대부분 RBAC 사용한다.

---

# 2. RBAC(Role Based Access Control) 구성요소

RBAC는 4가지 객체로 구성된다.

```
Role
ClusterRole
RoleBinding
ClusterRoleBinding
```

이 구조를 이해해야 설계 가능하다.

---

**RBAC 테스트**

* kubectl 명령을 사용할 수 있는 파드 생성

* kubernetes는 파드 생성시 기본 sa로 default를 사용함.

```
kubectl run k8s-tool --image=alpine/k8s:1.29.2 --restart=Never -- sleep 3600
```

* default sa에는 어떤 권한도 없음. 따라서 kubectl get pods 실행시 권한없음이 출력됨.

* 따라서 다음과 같이 관리자 권한부여 후 테스트

```
kubectl create rolebinding default-admin --clusterrole=admin \
  --serviceaccount=resource-lab:default --namespace=resource-lab
  
kubectl exec -it k8s-tool -- bash
k8s-tool:/apps# kubectl get pods
NAME                   READY   STATUS    RESTARTS       AGE
k8s-tool               1/1     Running   0              16m
web-7bf79b8449-dk9vq   1/1     Running   1 (125m ago)   143m
```

# 3. Role (네임스페이스 단위 권한 정의)

## 3.1 개념

Role은:

> 특정 네임스페이스 안에서 어떤 리소스에 어떤 작업을 허용할지 정의하는 객체

중요 특징:

* namespace 범위

* 권한 "정의"만 한다

* 계정과 직접 연결되지 않는다

---

## 3.2 Role 내부 구조

```
rules:
- apiGroups:
  resources:
  verbs:
```

### apiGroups

리소스가 속한 API 그룹

| 리소스 | apiGroup |
| --- | --- |
| pods | "" (core) |
| services | "" |
| deployments | "apps" |
| ingresses | "networking.k8s.io" |

core 그룹은 반드시 `""`로 작성한다.

---

### resources

접근할 리소스 이름

예:

```
resources: ["pods", "services"]
```

---

### verbs

수행 가능한 동작

| verb | 의미 |
| --- | --- |
| get | 단일 조회 |
| list | 목록 조회 |
| watch | 변경 감시 |
| create | 생성 |
| update | 수정 |
| patch | 일부 수정 |
| delete | 삭제 |

---

## 3.3 Role은 권한 “정의서”

Role은 계정이 아니다. Role은 단순히 권한 집합이다.

즉:

> Role만 생성하면 아무 일도 일어나지 않는다.

Binding이 있어야 한다.

---

# 4. ClusterRole (클러스터 범위 권한 정의)

## 4.1 개념

ClusterRole은:

> 네임스페이스를 초월하는 권한 정의

사용 경우:

* nodes 접근

* cluster-wide 조회

* CRD 접근

* 여러 namespace 공통 권한

---

## 4.2 중요한 특징

ClusterRole은 두 가지 방식으로 사용된다.

### 1. ClusterRoleBinding으로 클러스터 전체 적용

```
모든 namespace에 권한 적용
```

### 2. RoleBinding으로 특정 namespace에만 적용

ClusterRole을 namespace에 제한해서 사용할 수 있다.

이게 실무에서 매우 중요하다. 즉, 모든 namespace에 공통으로 적용할 ClusterRole을 RoleBinding과 연결함.

---

# 5. RoleBinding (권한 연결 객체)

## 5.1 개념

RoleBinding은:

> Role 또는 ClusterRole을 특정 계정(User/Group/ServiceAccount)에 연결하는 객체

Binding이 없으면 권한은 적용되지 않는다.

---

## 5.2 내부 구조

```
subjects:
- kind:
  name:
roleRef:
  kind:
  name:
```

---

### subjects

권한을 부여할 대상

| kind | 설명 |
| --- | --- |
| User | 외부 사용자 |
| Group | 사용자 그룹 |
| ServiceAccount | Pod용 계정 |

---

### roleRef

연결할 권한 정의 객체

* Role

* ClusterRole

---

# 6. ClusterRoleBinding

ClusterRoleBinding은:

> ClusterRole을 클러스터 전체 범위로 연결하는 객체

예:

```
kind: ClusterRoleBinding
```

이 객체는 namespace 필드가 없다.

즉:

> 전체 클러스터에 적용된다.

---

# 7. ServiceAccount

## 7.1 ServiceAccount란?

* Pod가 Kubernetes API에 접근할 때 사용하는 계정

* Namespace 단위로 존재

확인:

```
kubectl get sa -n dev
```

---

## 7.2 동작 메커니즘

Pod가 생성되면:

1. ServiceAccount 지정

2. API Server가 토큰 생성

3. 토큰이 Pod 내부에 자동 마운트됨

경로:

```
/var/run/secrets/kubernetes.io/serviceaccount/
```

포함 파일:

* token

* ca.crt

* namespace

---

## 7.3 automountServiceAccountToken

필요 없으면 차단 가능:

```
automountServiceAccountToken: false
```

보안 설계에서 중요하다.

### 1. ServiceAccount 레벨 (기본값 설정)

```
apiVersion: v1
kind: ServiceAccount
metadata:
  name: build-robot
  namespace: resource-lab
automountServiceAccountToken: false  # 이 SA를 쓰는 Pod는 기본적으로 토큰 마운트 안 함
```

### 2. Pod 레벨 (개별 설정)

특정 Pod 하나에만 적용하거나, ServiceAccount의 설정을 무시하고 개별적으로 강제하고 싶을 때 사용한다. `spec` **바로 아래**에 위치한다.

```
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
  namespace: resource-lab
spec:
  automountServiceAccountToken: false  # 이 Pod 내부에 토큰 파일을 생성하지 않음
  containers:
  - name: my-container
    image: nginx
```

---

# 8. Kubernetes RBAC 실습

RBAC은 **"누가(Subject) + 어디서(Namespace) + 무엇을(Verb/Resource)"** 할 수 있는지 결정하는 핵심 보안 설정이다.

---

## 1. Role & RoleBinding (네임스페이스 단위)

특정 네임스페이스(`resource-lab`) 안에서만 유효한 권한을 부여합니다.

### A. YAML 정의

**Role**: 어떤 권한이 있는지 정의한다.

```
# pod-reader-role.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: resource-lab
  name: pod-reader
rules:
- apiGroups: [""] # 코어 API 그룹
  resources: ["pods", "pods/log"]
  verbs: ["get", "list", "watch"]
```

**RoleBinding**: 사용자(dev)와 Role을 연결한다.

```
# pod-reader-binding.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods-dev
  namespace: resource-lab
subjects:
- kind: User
  name: dev
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

### B. kubectl 명령형 방식

```
# Role 생성
kubectl create role pod-reader --verb=get,list,watch --resource=pods --namespace=resource-lab

# RoleBinding 생성
kubectl create rolebinding read-pods-dev --role=pod-reader --user=dev --namespace=resource-lab
```

---

## 2. ClusterRole & ClusterRoleBinding (클러스터 단위)

네임스페이스와 상관없이 **클러스터 전체 자원**(Nodes, PV 등)이나 **모든 네임스페이스**에 걸친 권한을 부여합니다.

### A. YAML 정의

**ClusterRole**: 클러스터 전체에 적용될 권한을 정의한다.

```
# node-reader-clusterrole.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: node-reader
rules:
- apiGroups: [""]
  resources: ["nodes"]
  verbs: ["get", "list"]
```

**ClusterRoleBinding**: 사용자(dev)와 ClusterRole을 클러스터 전체 수준에서 연결한다.

```
# node-reader-binding.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: read-nodes-dev
subjects:
- kind: User
  name: dev
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: node-reader
  apiGroup: rbac.authorization.k8s.io
```

### B. kubectl 명령형 방식

```
# ClusterRole 생성
kubectl create clusterrole node-reader --verb=get,list --resource=nodes

# ClusterRoleBinding 생성
kubectl create clusterrolebinding read-nodes-dev --clusterrole=node-reader --user=dev
```

---

## 3. 혼합 케이스: ClusterRole을 특정 네임스페이스에 Binding

가장 많이 쓰이는 실무 패턴. 공용 권한(`view`, `admin` 등)을 정의해두고 특정 네임스페이스에만 할당할 때 사용한다.

```
# 이미 만들어진 'view' ClusterRole을 dev 사용자에게 'resource-lab' 네임스페이스에서만 적용
kubectl create rolebinding dev-view-binding --clusterrole=view --user=dev --namespace=resource-lab
```

---

## 4. 권한 검증 및 삭제 실습

### Kubernetes 권한 확인

### 1. `kubectl auth can-i` (가장 많이 사용)

관리자가 특정 사용자나 그룹의 권한을 **가상으로 테스트**해볼 수 있는 가장 강력한 도구.

* **특정 사용자의 권한 확인 (**`--as`**)**

  ```
  # dev 사용자가 resource-lab 네임스페이스에서 Pod를 생성할 수 있는가?
  kubectl auth can-i create pods --as dev -n resource-lab

  # dev 사용자가 클러스터의 노드 목록을 볼 수 있는가?
  kubectl auth can-i list nodes --as dev
  ```

* **특정 그룹의 권한 확인 (**`--as-group`**)**Bash

  ```
  # developer 그룹에 속한 사용자가 Pod 로그를 볼 수 있는가?
  kubectl auth can-i get pods/log --as-group developer -n resource-lab
  ```

* **전체 권한 목록 확인 (**`--list`**)**Bash

  해당 사용자가 가진 모든 권한을 표 형태로 한눈에 보여준다.

  ```
  kubectl auth can-i --list --as dev -n resource-lab
  ```

---

### 2. 생성된 RBAC 자원 조회 및 상세 확인

클러스터에 어떤 Role과 Binding이 생성되어 있는지 직접 확인한다.

* **Role / RoleBinding 목록 조회**

  ```
  # 특정 네임스페이스의 권한 설정 확인
  kubectl get role,rolebinding -n resource-lab

  # 클러스터 전체 권한 설정 확인
  kubectl get clusterrole,clusterrolebinding | grep dev
  ```

* **상세 규칙(Rules) 확인 (**`-o yaml`**)**

  Role이 어떤 API 그룹과 리소스를 허용하는지 상세히 yaml형태로 출력한다.

  ```
  kubectl get role pod-reader -n resource-lab -o yaml
  ```

* **연결 상태 확인 (**`describe`**)**

  RoleBinding이 어떤 사용자(Subject)와 **어떤 Role**을 묶고 있는지 확인한다.

  ```
  kubectl describe rolebinding read-pods-dev -n resource-lab
  ```

---

### 3. Kubeconfig 파일을 이용한 직접 테스트

실제로 만든 `dev.config` 파일을 사용하여 명령을 날려보는 실무적인 방법이다.

```
# 1. 정상 작동 케이스 (resource-lab의 Pod 조회)
kubectl get pods --kubeconfig=dev.config

# 2. 거부 케이스 (다른 네임스페이스 조회)
kubectl get pods -n default --kubeconfig=dev.config

# 3. 거부 케이스 (권한 없는 자원 조회)
kubectl get services --kubeconfig=dev.config
```

---

|  |  |  |
| --- | --- | --- |
| **명령어** | **용도** | **권장 상황** |
| `can-i --as` | 특정 액션 가능 여부 즉시 확인 | 설정 직후 빠른 검증 시 |
| `can-i --list` | 사용자의 전체 권한 범위 확인 | 권한 누락이나 과다 부여 확인 시 |
| `describe` | Role과 User의 연결 관계 확인 | 설정값이 꼬였을 때 디버깅용 |
| `--kubeconfig` | 실제 환경과 동일한 테스트 | 최종 배포 전 사용자 경험 확인 시 |

### 리소스 삭제

실습이 끝난 후 생성한 자원을 정리한다.

```
# 네임스페이스 자원 삭제
kubectl delete rolebinding read-pods-dev -n resource-lab
kubectl delete role pod-reader -n resource-lab

# 클러스터 자원 삭제
kubectl delete clusterrolebinding read-nodes-dev
kubectl delete clusterrole node-reader
```

---

### 요약

|  |  |  |  |
| --- | --- | --- | --- |
| **구분** | **범위 (Scope)** | **대상 자원** | **주요 용도** |
| **Role** | Namespace | Pod, Service 등 NS 내 자원 | 팀별/프로젝트별 권한 격리 |
| **RoleBinding** | Namespace | Role/ClusterRole을 특정 NS에 연결 | 특정 방 안에서만 놀 수 있게 허용 |
| **ClusterRole** | Cluster | Node, PV, 모든 NS의 Pod 등 | 관리자 권한, 인프라 자원 관리 |
| **ClusterRoleBinding** | Cluster | ClusterRole을 클러스터 전체에 연결 | 클러스터 전체 통행증 발급 |

---

# 9. USER/GROUP에 RBAC 적용하기

### Step 1: 인증서 생성 (Control Plane 노드) : Control Plane이 CA역할을 함.

```
# 키 생성
openssl genrsa -out dev.key 2048
# CSR(인증서 요청) 생성
openssl req -new -key dev.key -out dev.csr -subj "/CN=dev/O=developer"
# CRT(인증서) 생성
sudo openssl x509 -req -in dev.csr -CA /etc/kubernetes/pki/ca.crt -CAkey /etc/kubernetes/pki/ca.key -CAcreateserial -out dev.crt -days 365
```

### Step 2: RBAC 적용

```
# Role & RoleBinding을 하나의 파일(rbac.yaml)로 만들어 적용
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: resource-lab
  name: pod-manager-role
rules:
- apiGroups: [""]
  resources: ["pods", "pods/log"]
  verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  namespace: resource-lab
  name: dev-group-pod-binding
subjects:
- kind: Group
  name: developer
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: pod-manager-role
  apiGroup: rbac.authorization.k8s.io
```

* User에게 RoleBinding한다면 다음과 같이 작성한다.

```
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  namespace: resource-lab
  name: dev-pod-manager-binding
subjects:
- kind: User
  name: dev
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: pod-manager
  apiGroup: rbac.authorization.k8s.io
```

### Step 3: Kubeconfig 생성 (`--embed-certs` 포함)

```
CLUSTER_NAME=$(kubectl config view -o jsonpath='{.clusters[0].name}')
ENDPOINT=$(kubectl config view -o jsonpath='{.clusters[0].cluster.server}')

# 클러스터/사용자/컨텍스트 등록
kubectl config set-cluster $CLUSTER_NAME --certificate-authority=/etc/kubernetes/pki/ca.crt --embed-certs=true --server=$ENDPOINT --kubeconfig=dev.config
kubectl config set-credentials dev --client-certificate=dev.crt --client-key=dev.key --embed-certs=true --kubeconfig=dev.config
kubectl config set-context dev-context --cluster=$CLUSTER_NAME --user=dev --namespace=resource-lab --kubeconfig=dev.config
kubectl config use-context dev-context --kubeconfig=dev.config
```

### 1. 설정 파일 배치

생성된 `dev.config` 파일에는 클러스터 정보(CA)와 사용자 인증 정보(CRT/Key)가 모두 내장되어 있다. 이 파일을 접속하려는 사용자의 홈 디렉토리에 배치한다.

```
# 디렉토리 생성 및 파일 복사
mkdir -p ~/.kube
cp dev.config ~/.kube/config
```

### 2. 보안 권한 설정 (필수)

`config` 파일 내에는 사용자의 **개인키(Private Key)** 데이터가 들어있으므로, 다른 사용자가 읽을 수 없도록 권한을 제한해야 한다.

```
# 소유자만 읽고 쓸 수 있도록 권한 수정
chmod 600 ~/.kube/config
```

### 3. 작동 원리 확인

이제 `kubectl` 명령어를 입력하면 쿠버네티스는 자동으로 `~/.kube/config` 파일을 읽어 다음 정보를 확인한다.

* **인증(Who):** 나는 `dev` 사용자이며 `developer` 그룹 소속이다.

* **접속(Where):** `https://192.168.80.101:6443` 서버로 접속한다.

* **제한(What):** 기본적으로 `resource-lab` 네임스페이스를 바라본다.

---

# 9. 설계 원칙 정리

## 최소 권한 원칙

* "\*" 사용 금지

* cluster-admin 남발 금지

* namespace 분리 활용

---

## 권한 설계 순서

```
1. 계정 정의
2. 필요한 리소스 정의
3. 필요한 verbs 정의
4. namespace 범위 결정
5. Binding 연결
6. can-i 검증
```

---

# 10. 핵심 개념 요약

| 구성요소 | 역할 |
| --- | --- |
| Role | namespace 권한 정의 |
| ClusterRole | 클러스터 범위 권한 정의 |
| RoleBinding | namespace 내 권한 연결 |
| ClusterRoleBinding | 클러스터 전체 연결 |
| ServiceAccount | Pod 전용 계정 |

---

 [[실습문제 1]]