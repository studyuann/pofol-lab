---
title: "15장 Resource 관리(Requests Limits HPA)"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "쿠버네티스"]
is_public: true
draft: false
---

# 15장. Resource 관리(Requests / Limits / HPA)

## 0. 학습 목표

* requests/limits 개념과 동작 원리 이해한다

* Pod QoS 클래스(Guaranteed/Burstable/BestEffort) 구분한다

* requests/limits로 **스케줄링/자원 격리**를 제어한다

* metrics-server 기반으로 HPA 동작시킨다

* HPA v2로 CPU/메모리 기준 자동 확장 실습한다

---

## 1. 핵심 개념 정리

### 1.1 requests vs limits

* **requests**
  + 스케줄러가 “이 파드가 최소로 필요로 하는 자원”으로 간주한다
  + 노드에 파드를 배치할 때, 노드의 allocatable에서 requests 합을 보고 배치한다
  + 즉 **배치(스케줄링)의 기준**이 된다

* **limits**
  + 컨테이너가 “최대로 쓸 수 있는 자원 상한”이다
  + CPU는 CFS quota로 제한한다
  + Memory는 초과하면 OOMKilled 날 수 있다
  + 즉 **실행 중 자원 사용 상한(격리)의 기준**이 된다

### 1.2 CPU 단위

* `500m` = 0.5 코어를 의미한다

* `1` = 1 코어를 의미한다

* CPU는 **압박 시 throttling**(느려짐)으로 나타나는 경우가 많다

### 1.3 Memory 단위

* `Mi`, `Gi` 같은 이진 단위 쓴다

* Memory는 limits 초과 시 **OOMKilled**로 종료되는 형태가 흔하다

### 1.4 QoS 클래스

* **Guaranteed**
  + `requests == limits`로 CPU/Memory를 모두 지정한 경우

* **Burstable**
  + `requests < limits`인 경우

* **BestEffort**
  + requests/limits 둘 다 미지정인 경우

* 노드 메모리 부족 같은 상황에서 퇴출(eviction) 우선순위: `BestEffort → Burstable → Guaranteed`

---

## 2. 실습 준비

### 2.1 네임스페이스 생성

```
kubectl create ns resource-lab
```

* `create ns`는 namespace 오브젝트를 생성한다

* 분리된 실습 공간을 만들어 리소스쿼터/리밋레인지 적용을 안전하게 실습한다

### 2.2 현재 클러스터 자원 확인

```
kubectl get nodes
kubectl describe node <노드이름> | egrep -n "Allocatable|Capacity|cpu|memory|Pods"
```

[![](15%EC%9E%A5%20Resource%20%EA%B4%80%EB%A6%AC(Requests%20Limits%20HPA)/image.png)](15%EC%9E%A5%20Resource%20%EA%B4%80%EB%A6%AC(Requests%20Limits%20HPA)/image.png)

* `Capacity`는 노드 물리/가상 머신의 전체 자원이다

* `Allocatable`은 쿠버네티스가 파드에 할당 가능한 자원이다(시스템/쿠버네티스 예약분 제외)

* **Non-terminated Pods**

현재 이 노드에서 실행 중인 16개 Pod가 자원을 얼마나 점유하고 있는지 보여주는 가장 중요한 부분.

* **CPU (440m, 22%):**
  + 현재 실행 중인 Pod들이 요청(Requests)한 CPU 총합이 **440m**(0.44코어)이다.
  + 이는 전체 가용 CPU(2코어)의 22%를 차지하고 있다는 의미.

* **Memory (120Mi, 3% / 170Mi, 4%):**
  + **앞의 숫자(120Mi, 3%):** Pod들이 최소한 이만큼은 보장해달라고 요청한 **Requests** 합계.
  + **뒤의 숫자(170Mi, 4%):** Pod들이 최대 이만큼까지 쓸 수 있도록 설정된 **Limits** 합계.

---

## 3. Requests/Limits 기본 실습

### 3.1 requests/limits 미지정 파드(BestEffort) 생성

`besteffort.yaml`

```
apiVersion: v1
kind: Pod
metadata:
  name: besteffort-pod
  namespace: resource-lab
spec:
  containers:
  - name: app
    image: nginx:1.25
```

적용

```
kubectl apply -f besteffort.yaml
kubectl get pod -n resource-lab -o wide
kubectl describe po besteffort-pod | egrep -A 2 "Requests|Limits|QoS Class" | egrep -v "\--" | egrep "Requests|Limits|QoS Class|cpu|memory"
```

해설

* `resources:`가 없으므로 requests/limits 둘 다 없음 → QoS `BestEffort`로 잡힌다

* `describe` 출력에서 `QoS Class`가 무엇인지 확인한다

---

### 3.2 Burstable 파드 생성 (requests만 지정)

`burstable.yaml`

```
apiVersion: v1
kind: Pod
metadata:
  name: burstable-pod
  namespace: resource-lab
spec:
  containers:
  - name: app
    image: nginx:1.25
    resources:
      requests:
        cpu: "200m"
        memory: "128Mi"
```

적용/확인

```
kubectl apply -f burstable.yaml
kubectl describe pod burstable-pod -n resource-lab | egrep -A 2 "Requests|Limits|QoS Class" | egrep -v "\--" | egrep "Requests|Limits|QoS Class|cpu|memory"
```

해설

* requests만 있으므로 QoS `Burstable`이 된다

* 스케줄러는 이 파드를 노드에 배치할 때 `cpu 200m`, `mem 128Mi`를 “점유한 것”처럼 계산한다

---

### 3.3 Guaranteed 파드 생성 (requests == limits)

`guaranteed.yaml`

```
apiVersion: v1
kind: Pod
metadata:
  name: guaranteed-pod
  namespace: resource-lab
spec:
  containers:
  - name: app
    image: nginx:1.25
    resources:
      requests:
        cpu: "300m"
        memory: "256Mi"
      limits:
        cpu: "300m"
        memory: "256Mi"
```

적용/확인

```
kubectl apply -f guaranteed.yaml
kubectl describe pod guaranteed-pod -n resource-lab | egrep -A 2 "Requests|Limits|QoS Class" | egrep -v "\--" | egrep "Requests|Limits|QoS Class|cpu|memory"
```

해설

* CPU/Memory 모두 requests==limits → QoS `Guaranteed`가 된다

* 노드 압박 시 상대적으로 퇴출 우선순위에서 유리한 편이다

---

## 4. Limits 동작 확인 실습 (메모리 OOMKilled)

### 4.1 메모리 제한을 걸고, 의도적으로 메모리 초과를 유도한다

`oom.yaml`

```
apiVersion: v1
kind: Pod
metadata:
  name: oom-pod
  namespace: resource-lab
spec:
  containers:
  - name: stress
    image: polinux/stress
    args: ["--vm", "1", "--vm-bytes", "200M", "--vm-hang", "1"]
    resources:
      requests:
        memory: "64Mi"
        cpu: "100m"
      limits:
        memory: "100Mi"
        cpu: "200m"
```

적용

```
kubectl apply -f oom.yaml
kubectl get pod -n resource-lab -w
```

상태 확인

```
kubectl describe pod oom-pod -n resource-lab
kubectl get pod oom-pod -n resource-lab -o jsonpath='{.status.containerStatuses[0].state.terminated.reason}{"\n"}'
```

해설

* `stress`가 200MB를 쓰려 하는데 limits 100Mi라서 초과한다

* 이 경우 컨테이너가 **OOMKilled**로 종료될 수 있다

* CPU는 초과해도 보통 느려짐(throttling)인데, Memory는 초과 시 종료가 빈번하다

정리

```
kubectl delete pod oom-pod -n resource-lab
```

---

## 5. 조직 정책 적용 (ResourceQuota/LimitRange)

|  |  |  |
| --- | --- | --- |
| **구분** | **ResourceQuota (자원 할당량)** | **LimitRange (자원 범위 제한)** |
| **관리 대상** | **네임스페이스 전체**의 자원 합계 | **개별 컨테이너/파드**의 자원 설정 |
| **주요 목적** | 특정 팀/프로젝트의 자원 독점 방지 | 개별 파드의 잘못된 설정 방지 및 자동화 |
| **주요 기능** | CPU/Mem 합계, 파드 개수, PVC 개수 제한 | 기본값 부여(Default), 최소/최대 범위 강제 |

### 5.1 ResourceQuota로 네임스페이스 총량 제한

`quota.yaml`

```
apiVersion: v1
kind: ResourceQuota
metadata:
  name: ns-quota
  namespace: resource-lab
spec:
  hard:
    Pods: "2"
    requests.cpu: "1"
    requests.memory: "1Gi"
    limits.cpu: "2"
    limits.memory: "2Gi"
    pods: "20"
```

적용/확인

```
kubectl apply -f quota.yaml
kubectl describe quota ns-quota -n resource-lab
```

해설

* 네임스페이스 단위로 “requestss/limits 총량”을 제한한다

* 팀별 멀티테넌시 환경에서 필수로 쓰는 정책이다

* 동작테스트

다음 Pod 2개 생성 가능.

```
apiVersion: v1
kind: Pod
metadata:
  name: test-pod-1
  namespace: resource-lab
spec:
  containers:
  - name: nginx
    image: nginx
    resources:
      requests:
        cpu:"500m"
        memory:"512Mi"
      limits:
        cpu:"1"
        memory:"1Gi"
```

3번째 Pod 생성 시:

```
Error from server (Forbidden): exceeded quota
```

생성 거부됨.

---

### 5.2 LimitRange로 “기본값/최소/최대” 강제한다

`limitrange.yaml`

```
apiVersion: v1
kind: LimitRange
metadata:
  name: default-limits
  namespace: resource-lab
spec:
  limits:
  - type: Container
    default:
      cpu: "300m"
      memory: "256Mi"
    defaultRequest:
      cpu: "100m"
      memory: "128Mi"
    min:
      cpu: "50m"
      memory: "64Mi"
    max:
      cpu: "1000m"
      memory: "1024Mi"
```

적용/확인

```
kubectl apply -f limitrange.yaml
kubectl describe limitrange default-limits -n resource-lab
```

해설

* `default`는 limits 기본값이다

* `defaultRequest`는 requests 기본값이다

* 개발자가 resources를 안 적어도, 네임스페이스 정책이 자동으로 채워준다

* `min/max`는 범위를 벗어나면 생성 자체가 거부된다

**자원 미지정 Pod 생성**

```
apiVersion: v1
kind: Pod
metadata:
  name: default-test
  namespace: resource-lab
spec:
  containers:
  - name: nginx
    image: nginx
```

생성 후 확인:

```
kubectlget pod default-test-o yaml-n resource-lab
```

→ 자동으로 defaultRequest / default 적용됨.

---

최소값 위반 테스트

```
resources:
  requests:
    cpu:"50m"
    memory:"64Mi"
```

결과:

```
Error from server: minimum cpu usage per Container is 100m
```

생성 거부됨.

---

**최대값 초과 테스트**

```
resources:
  limits:
    cpu:"2"
```

→ max 1 초과

→ 생성 거부됨.

---

## 6. **Horizontal Pod Autoscaling**

HPA는 replicas를 사용하는 리소스에 적용되며, cpu,memory 등의 사용량을 측정해 정해진 값 이상으로 수치가 넘어가면 replicas를 수평 확장하고 정해진 값 아래로 수치가 내려가면 replicas를 줄인다.

### HPA 실습 (CPU/Memory 기반 자동 확장)

### 6.1 사전조건: metrics-server 설치/동작 확인

HPA는 메트릭 없으면 동작하지 않는다.

* metric-server 설치

### **1. 공식 YAML 파일 다운로드**

먼저 최신 버전의 선언형 파일을 로컬로 다운로드합니다. (직접 수정이 필요하므로 바로 `apply` 하지 않음.)

```
wget https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

---

### **2. YAML 파일 핵심 수정 (3가지 포인트)**

다운로드한 `components.yaml` 파일을 열어 `Deployment` 섹션을 아래와 같이 수정한다.

* **인증서 무시:** 사설 인증서를 사용하는 온프레미스 환경을 위해 `-kubelet-insecure-tls` 옵션이 필수이다.

* **포트 우회:** Kubelet(10250)과의 충돌을 피하기 위해 전용 포트(**4443**)를 수정한다. 클라우드서비스 사용시에는 변경 불필요.

* **서비스(Service) 포트 매핑:** 외부(API 서버)는 443으로 들어오고, 내부(Pod)는 4443으로 전달되도록 `Service` 섹션을 수정한다.

```
apiVersion: v1
kind: Service
metadata:
  labels:
    k8s-app: metrics-server
  name: metrics-server
  namespace: kube-system
spec:
  ports:
  - appProtocol: https
    name: https
    port: 443
    protocol: TCP
    targetPort: 4443
  selector:
    k8s-app: metrics-server
---
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    k8s-app: metrics-server
  name: metrics-server
  namespace: kube-system
spec:
  selector:
    matchLabels:
      k8s-app: metrics-server
  strategy:
    rollingUpdate:
      maxUnavailable: 0
  template:
    metadata:
      labels:
        k8s-app: metrics-server
    spec:
      containers:
      - args:
        - --cert-dir=/tmp
        - --secure-port=4443
        - --kubelet-preferred-address-types=InternalIP,ExternalIP,Hostname
        - --kubelet-use-node-status-port
        - --kubelet-insecure-tls
        - --metric-resolution=15s
        image: registry.k8s.io/metrics-server/metrics-server:v0.8.1
        imagePullPolicy: IfNotPresent
        livenessProbe:
          failureThreshold: 3
          httpGet:
            path: /livez
            port: https
            scheme: HTTPS
          periodSeconds: 10
        name: metrics-server
        ports:
        - containerPort: 4443
          name: https
          protocol: TCP
        readinessProbe:
          failureThreshold: 3
          httpGet:
            path: /readyz
            port: https
            scheme: HTTPS
          initialDelaySeconds: 20
          periodSeconds: 10
```

---

```
kubectl apply -f components.yaml
kubectl get apiservice v1beta1.metrics.k8s.io

kubectl get apiservices | grep metrics
kubectl top nodes
kubectl top pods -A | head
```

* `kubectl top`이 동작해야 한다

* 동작하지 않으면 metrics-server 미설치/미정상 가능성이 높다

---

### 6.2 HPA 대상 Deployment 생성 (requests 필수)

HPA는 보통 “목표 사용률(%)”을 계산하므로 **requests가 반드시 있어야** 의미 있는 비율이 나온다.

`deploy.yaml`

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  namespace: resource-lab
spec:
  replicas: 1
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: web
        image: nginx:1.25
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "300m"
            memory: "256Mi"
```

적용

```
kubectl apply -f deploy.yaml
kubectl get deploy,po -n resource-lab -o wide
```

---

### 6.3 부하 발생용 Service 생성

`svc.yaml`

```
apiVersion: v1
kind: Service
metadata:
  name: web-svc
  namespace: resource-lab
spec:
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
```

적용

```
kubectl apply -f svc.yaml
kubectl get svc -n resource-lab
```

---

### 6.4 HPA(v2) 생성: CPU + Memory 기준

테스트를 위해 설정값을 낮게 잡음.

`hpa.yaml`

```
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web-hpa
  namespace: resource-lab
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web
  minReplicas: 1
  maxReplicas: 5
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 10
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 10
```

적용/확인

```
kubectl apply -f hpa.yaml
kubectl get hpa -n resource-lab
kubectl describe hpa web-hpa -n resource-lab
```

해설

* `averageUtilization`은 “requests 대비 사용률”이다

* CPU 50%면 `100m requests` 기준으로 평균 50m 이상이면 확장 방향으로 평가한다

* 메모리도 동일한 방식으로 requests 대비 비율로 평가한다

hpa는 replicas를 줄일때 안정적인 운영을 위해 5분정도를 기다린다. 다음 옵션 수정으로 1분으로 줄여 테스트한다. 운영시에는 변경하지 않음.

```
spec:
  # ... 기존 설정들 (maxReplicas, minReplicas 등) ...
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 60  # 5분(300초) 대신 1분(60초)으로 수정
```

---

## 7. HPA 동작 확인 (부하 발생 → 확장 → 부하 제거 → 축소)

### 7.1 임시 부하 파드 실행(클러스터 내부에서 요청)

아래는 busybox로 무한 루프 요청을 보내는 방식이다.

```
kubectl run -n resource-lab -it --rm loadgen \
  --image=busybox:1.36 \
  --restart=Never \
  -- /bin/sh
```

busybox 쉘 안에서 실행

```
while true; do
  wget -q -O- http://web-svc.resource-lab.svc.cluster.local >/dev/null
done
```

설명

* `kubectl run ... -it --rm`
  + `it`는 터미널 상호작용 모드로 접속한다
  + `-rm`은 종료 시 파드를 자동 삭제한다
  + `-restart=Never`는 Deployment가 아니라 “1회성 Pod”로 뜨게 한다

* 내부 DNS로 Service를 호출한다
  + `서비스명.네임스페이스.svc.cluster.local` 형식이다

---

### 7.2 HPA 상태 관찰

다른 터미널에서 실행

```
kubectl get hpa -n resource-lab -w
```

또는

```
kubectl get deploy -n resource-lab -w
kubectl top pods -n resource-lab
```

기대 결과

* 일정 시간 후 replicas가 2,3…으로 증가한다

* 부하 제거하면 안정화 구간 지나 replicas가 다시 감소한다

부하 중단

* busybox 터미널에서 `Ctrl+C` 후 `exit` 한다

* `-rm`라서 파드 자동 삭제됨

---

## 8. 운영에서 자주 막히는 포인트 (트러블슈팅)

### 8.1 HPA가 `<unknown>` 뜨는 경우

확인

```
kubectl describe hpa web-hpa -n resource-lab
kubectl top pods -n resource-lab
kubectl get apiservices | grep metrics
```

원인 후보

* metrics-server 미설치/비정상

* API aggregation TLS 문제(환경 따라 발생)

* requests 미지정(비율 계산 자체가 의미 없거나 동작이 제한되는 구성)

---

### 8.2 CPU는 제한했는데 “느려지기만 하고 죽지는 않음”

* CPU limits는 초과 시 throttling이 일반적이다

* 메모리 limits는 초과 시 OOMKilled가 흔하다

* 즉 “CPU는 성능저하, Memory는 종료”로 관찰되는 경우가 많다

---

## 9. 정리 과제(실습 문제)

1. Burstable 파드를 하나 만들고, Guaranteed로 바꿔 QoS 변화를 확인한다

2. ResourceQuota를 더 낮춰서(예: requests.cpu=300m) Deployment replicas를 늘리려 하면 어떤 에러가 나는지 확인한다

3. HPA의 `maxReplicas`를 2로 제한하고 부하를 걸어 확장이 더 이상 못 되는 상황을 만든다

---

## 10. 실습 리소스 일괄 정리

```
kubectl delete ns resource-lab
```

* namespace 삭제로 실습 리소스가 한 번에 정리된다