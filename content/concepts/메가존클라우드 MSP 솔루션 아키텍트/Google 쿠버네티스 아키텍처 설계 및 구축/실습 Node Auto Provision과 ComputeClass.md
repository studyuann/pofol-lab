---
title: "실습 Node Auto Provision과 ComputeClass"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Google 쿠버네티스 아키텍처 설계 및 구축"]
is_public: true
draft: false
---

# 실습. Node Auto Provision과 ComputeClass

# 1. 실습 목표

* GKE Standard 클러스터에서 **Node Auto Provisioning(NAP)** 을 활성화한다.

* 기존 노드로는 수용되지 않는 워크로드를 배포해서 **Pending 상태**를 만든다.

* GKE가 자동으로 **새 노드풀을 생성**하는지 확인한다.

* **ComputeClass** 를 생성해서 특정 머신 패밀리 또는 우선순위를 선언적으로 지정한다.

* ComputeClass를 사용하는 워크로드를 배포해서 **ComputeClass 기반 노드 생성** 흐름을 확인한다.

---

# 2. 실습 개요

## 2.1 1단계: 클러스터 수준 Node Auto Provisioning 확인

* 소형 기본 노드풀로 클러스터 생성

* NAP 활성화

* CPU/메모리 요청이 큰 Deployment 배포

* Pod가 Pending 상태가 되면 GKE가 새 노드풀 생성

* 노드풀 목록과 노드 목록 확인

## 2.2 2단계: ComputeClass 기반 자동 노드 생성 확인

* custom ComputeClass 생성

* ComputeClass에 우선순위 규칙 정의

* `nodePoolAutoCreation.enabled: true` 설정

* 워크로드에서 ComputeClass 선택

* 해당 ComputeClass 특성에 맞는 노드풀 생성 확인

---

# 3. 실습 환경

* Google Cloud 프로젝트 1개

* `gcloud`, `kubectl` 사용 가능

* 리전 예시: `asia-northeast3`

* 클러스터 이름 예시: `gke-nap-lab`

* GKE Standard 클러스터 사용

---

# 4. 사전 준비

## 4.1 프로젝트 설정

```
gcloud config set project 프로젝트ID
```

## 4.2 API 활성화

```
gcloud services enable container.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable monitoring.googleapis.com
gcloud services enable logging.googleapis.com
```

## 4.3 환경 변수 지정

```
export PROJECT_ID=$(gcloud config get-value project)
export REGION=asia-northeast3
export CLUSTER_NAME=gke-nap-lab
```

---

# 5. 클러스터 생성

일부러 **작은 기본 노드풀**로 시작한다. 그래야 큰 워크로드를 넣었을 때 기존 노드에 스케줄되지 못하고, NAP가 새 노드풀을 생성하는 장면을 재현하기 쉽다.

## 5.1 NAP 활성화 포함 클러스터 생성

```
gcloud container clusters create $CLUSTER_NAME \
  --region=$REGION \
  --release-channel=regular \
  --machine-type=e2-standard-2 \
  --num-nodes=1 \
  --enable-ip-alias \
  --enable-autoprovisioning \
  --min-cpu=2 \
  --min-memory=8 \
  --max-cpu=20 \
  --max-memory=80 \
  --autoprovisioning-scopes=https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring,https://www.googleapis.com/auth/devstorage.read_only
```

### 명령 설명

* `--machine-type=e2-standard-2`
  + 기본 노드를 작게 시작한다.
  + CPU 2 vCPU, 메모리 8GiB 수준이라 큰 요청을 가진 Pod가 바로 안 올라가게 만들기 좋다.

* `--num-nodes=1`
  + 기본 노드풀을 최소로 구성한다.
  + 기존 노드에 배치될 여지를 줄여서 Pending 재현이 쉬워진다.

* `--enable-autoprovisioning`
  + 클러스터 수준 node auto-provisioning 활성화다.
  + Pending workload를 보고 GKE가 새 노드풀을 만들 수 있게 한다.

* `--min-cpu`, `--min-memory`, `--max-cpu`, `--max-memory`
  + NAP 활성화 시 CPU와 memory 제한 설정이 필요하다.

## 5.2 클러스터 인증 정보 가져오기

```
gcloud container clusters get-credentials $CLUSTER_NAME --region $REGION
```

## 5.3 기본 상태 확인

```
kubectl get nodes
gcloud container node-pools list --cluster=$CLUSTER_NAME --region=$REGION
```

### 기대 결과

* 노드는 보통 1개 또는 리전 특성상 여러 존에 분산된 형태로 보일 수 있음

* node pool 목록은 기본 생성된 풀만 보임

---

# 6. 1단계 실습: Pending Pod로 NAP 동작 확인

## 6.1 실습용 네임스페이스 생성

```
kubectl create namespace nap-lab
```

## 6.2 큰 리소스를 요청하는 Deployment 작성

기존 기본 노드는 `e2-standard-2` 이므로 큰 CPU/메모리 요청을 가진 Pod는 바로 올라가기 어렵다. 이걸 이용해서 Pending을 유도한다.

```
cat <<'EOF' > big-workload.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: big-workload
  namespace: nap-lab
spec:
  replicas: 2
  selector:
    matchLabels:
      app: big-workload
  template:
    metadata:
      labels:
        app: big-workload
    spec:
      containers:
      - name: pause
        image: registry.k8s.io/pause:3.9
        resources:
          requests:
            cpu: "4"
            memory: "12Gi"
          limits:
            cpu: "4"
            memory: "12Gi"
EOF
```

### 왜 이렇게 설정하는가

* Pod 하나가 CPU 4, 메모리 12Gi를 요청한다.

* 기본 노드 `e2-standard-2` 로는 수용이 불가능하다.

* 결과적으로 스케줄러는 Pod를 Pending으로 두고, cluster autoscaler / NAP가 적절한 노드 구성을 찾게 된다.

## 6.3 워크로드 배포

```
kubectl apply -f big-workload.yaml
```

## 6.4 Pod 상태 확인

```
kubectl get pods -n nap-lab -o wide
kubectl describe pod -n nap-lab -l app=big-workload
```

### 확인 포인트

* `Pending`

* 이벤트에 `Insufficient cpu`

* 이벤트에 `Insufficient memory`

* 또는 적절한 노드가 없다는 메시지

이 상태가 정상이다. 바로 실패가 아니라, **“기존 노드에는 못 올리지만 새 노드가 생기면 올라갈 수 있음”** 상태다.

## 6.5 노드풀 자동 생성 확인

```
gcloud container node-pools list --cluster=$CLUSTER_NAME --region=$REGION
```

몇 분 지나면서 새 auto-created node pool이 보이면 정상이다.

## 6.6 노드 생성 확인

```
kubectl get nodes
kubectl get pods -n nap-lab -o wide
```

### 기대 결과

* 기존보다 더 큰 머신 타입의 노드가 생김

* Pending이던 Pod가 `ContainerCreating` 또는 `Running` 으로 바뀜

* Pod가 새 노드에 스케줄됨

이 실습은 “Pod autoscaling”이 아니라 “**노드풀 자체가 자동 생성**되는 것”을 확인하는 실습이다.

**현재 워크로드 요구사항에 맞는 새 종류의 노드풀을 만드는 것**이 핵심이다.

---

# 7. 1단계 결과 분석

## 7.1 어떤 일이 일어났는가

1. 기본 노드풀은 작았음

2. 큰 리소스를 요구하는 Pod가 들어왔음

3. 기존 노드에는 배치 불가능했음

4. GKE가 새로운 조건의 노드풀 생성 필요성을 판단했음

5. 새 노드풀과 노드를 만들었음

6. Pending Pod가 새 노드로 올라갔음

## 7.2 확인

* HPA는 Pod 수를 늘리는 기능

* Cluster Autoscaler는 기존 노드풀의 노드 수를 늘리거나 줄이는 기능

* Node Auto Provisioning은 **새 노드풀 자체를 만들 수 있는 기능**

---

# 8. 2단계 실습: ComputeClass로 노드 특성 제어

**특정 성격의 노드**를 우선 사용하도록 선언한다.

## 8.1 ComputeClass 생성

문서 예시에는 `machineFamily: n4`, `spot: true/false`, `nodePoolAutoCreation.enabled: true` 를 사용한다.

```
cat <<'EOF' > compute-class.yaml
apiVersion: cloud.google.com/v1
kind: ComputeClass
metadata:
  name: lab-n4-priority
spec:
  priorities:
  - machineFamily: n4
    spot: true
  - machineFamily: n4
    spot: false
  nodePoolAutoCreation:
    enabled: true
EOF
```

## 8.2 ComputeClass 적용

```
kubectl apply -f compute-class.yaml
```

## 8.3 ComputeClass 확인

```
kubectl get computeclass
kubectl get computeclass lab-n4-priority -o yaml
```

---

# 9. ComputeClass를 요청하는 워크로드 배포

workload manifest에서는 `nodeSelector` 에 `cloud.google.com/compute-class: COMPUTE_CLASS_NAME` 형식으로 ComputeClass를 선택한다.

## 9.1 새 워크로드 manifest 작성

```
cat <<'EOF' > cc-workload.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cc-workload
  namespace: nap-lab
spec:
  replicas: 2
  selector:
    matchLabels:
      app: cc-workload
  template:
    metadata:
      labels:
        app: cc-workload
    spec:
      nodeSelector:
        cloud.google.com/compute-class: lab-n4-priority
      containers:
      - name: pause
        image: registry.k8s.io/pause:3.9
        resources:
          requests:
            cpu: "1500m"
            memory: "4Gi"
          limits:
            cpu: "1500m"
            memory: "4Gi"
EOF
```

### manifest 설명

* `nodeSelector.cloud.google.com/compute-class`
  + 이 Pod는 `lab-n4-priority` ComputeClass를 사용하겠다는 뜻이다.
  + GKE autoscaler는 이 ComputeClass의 우선순위 규칙을 참고해서 노드 생성 방향을 잡는다.

* `requests`
  + 적당한 크기로 설정함.

## 9.2 배포

```
kubectl apply -f cc-workload.yaml
```

## 9.3 상태 확인

```
kubectl get pods -n nap-lab -o wide
kubectl describe pod -n nap-lab -l app=cc-workload
gcloud container node-pools list --cluster=$CLUSTER_NAME --region=$REGION
kubectl get nodes --show-labels
```

### 기대 결과

* 기존 노드에 맞지 않거나 ComputeClass 요구를 충족할 노드가 없으면 새 node pool 생성 시도가 일어남

* 새 노드풀 또는 노드가 생성됨

* Pod가 해당 노드에 올라감

---

# 10. ComputeClass 실습 해설

## 10.1 priorities의 의미

```
priorities:
- machineFamily: n4
  spot: true
- machineFamily: n4
  spot: false
```

이 설정은 아래 의미다.

1. 먼저 N4 계열 Spot VM으로 시도

2. Spot 자원이 없거나 조건이 안 맞으면

3. N4 계열 일반 VM으로 시도

즉, ComputeClass는 단순 라벨이 아니라 **“노드 생성 전략”** 에 가깝다.

## 10.2 nodePoolAutoCreation.enabled 의 의미

```
nodePoolAutoCreation:
  enabled: true
```

이 옵션은 해당 ComputeClass를 사용하는 Pod 때문에 필요할 경우 **새 node pool 생성까지 허용**한다는 뜻이다.

---

# 14. 정리

* **Node Auto Provisioning**
  + Pending workload를 보고
  + 기존 노드풀만 늘리는 것이 아니라
  + **새 node pool 자체를 만들 수 있음** ([Google Cloud Documentation](https://docs.cloud.google.com/kubernetes-engine/docs/how-to/node-auto-provisioning))

* **ComputeClass**
  + autoscaling 시 사용할 노드 속성을 선언적으로 정의하는 프로필임
  + workload에서 `cloud.google.com/compute-class` 로 요청함
  + priorities 순서대로 후보를 시도함

---

# 15. 실습 정리 명령

## 15.1 워크로드 삭제

```
kubectl delete -f cc-workload.yaml
kubectl delete -f big-workload.yaml
kubectl delete -f compute-class.yaml
kubectl delete namespace nap-lab
```

## 15.2 클러스터 삭제

```
gcloud container clusters delete $CLUSTER_NAME --region $REGION
```

---