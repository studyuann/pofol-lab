---
title: "kube-ops-view 설치"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "쿠버네티스", "2장 실습환경구축"]
is_public: true
draft: false
---

# kube-ops-view 설치

## 1️⃣ kube-ops-view란?

[![](https://cdn.thenewstack.io/media/2023/02/aa9e6ffc-kube-ops-screenshot.png)](https://cdn.thenewstack.io/media/2023/02/aa9e6ffc-kube-ops-screenshot.png)[![](https://ec2spotworkshops.com/images/using_ec2_spot_instances_with_eks/helm/kube-ops-view-legend.png)](https://ec2spotworkshops.com/images/using_ec2_spot_instances_with_eks/helm/kube-ops-view-legend.png)[![](https://openshift-tutorial.schoolofdevops.com/images/kube-ops-view.png)](https://openshift-tutorial.schoolofdevops.com/images/kube-ops-view.png)

**kube-ops-view**는 Kubernetes 클러스터의

* 노드 상태

* Pod 배치 현황

* 리소스 분포

를 웹 UI로 시각화해주는 도구이다.

### 특징

* 실시간 클러스터 상태 시각화

* 노드별 Pod 분포 확인 가능

* 학습/데모 환경에서 매우 유용

* Helm Chart 제공

---

# 2️⃣ 실습 환경 가정

* kubeadm 기반 클러스터

* Control Plane 1대

* Worker Node 2대

* Helm 설치 완료

Helm 버전 확인:

```
helm version
```

kubectl 정상 확인:

```
kubectl get nodes -o wide
```

---

# 3️⃣ Helm Repository 추가

현재 stable repo는 사라졌기 때문에

공식 Chart가 있는 저장소를 추가해야 한다.

```
helm repo add christianhuth https://christianhuth.github.io/helm-charts
helm repo update
```

등록 확인:

```
helm repo list
helm search repo kube-ops-view
```

---

# 4️⃣ monitoring 네임스페이스 생성

```
kubectl create namespace monitoring
```

확인:

```
kubectl get ns
```

---

# 5️⃣ kube-ops-view 설치

```
helm install kube-ops-view christianhuth/kube-ops-view -n monitoring
```

설치 확인:

```
kubectl get all -n monitoring
```

Pod 상태 확인:

```
kubectl get pod -n monitoring -o wide
```

Service 확인:

```
kubectl get svc -n monitoring
```

기본 타입은 ClusterIP이다.

---

# 6️⃣ 접속 방법 ① Port-Forward (로컬 테스트)

```
kubectl -n monitoring port-forward svc/kube-ops-view 8080:80
```

브라우저 접속:

```
http://127.0.0.1:8080
```

---

# 7️⃣ 접속 방법 ② NodePort 방식

Service를 NodePort로 변경한다.

```
kubectl edit svc kube-ops-view -n monitoring
```

수정:

```
spec:
  type: NodePort
```

또는 values로 설치 시 지정 가능:

```
helm uninstall kube-ops-view -n monitoring

helm install kube-ops-view christianhuth/kube-ops-view \
  -n monitoring \
  --set service.type=NodePort
```

확인:

```
kubectl get svc -n monitoring
```

NodePort 예:

```
31492/TCP
```

접속:

```
http://<노드IP>:31492
```

---

# 8️⃣ LoadBalancer (MetalLB 환경)

MetalLB가 설치되어 있다면:

```
helm upgrade kube-ops-view christianhuth/kube-ops-view \
  -n monitoring \
  --set service.type=LoadBalancer
```

확인:

```
kubectl get svc -n monitoring
```

External-IP가 할당되면 접속:

```
http://<External-IP>
```

---

# 9️⃣ values.yaml 기반 커스터마이징

values 파일 추출:

```
helm show values christianhuth/kube-ops-view > values.yaml
```

주요 설정 예시:

```
service:
  type: NodePort
  nodePort: 32080

resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
```

적용:

```
helm upgrade kube-ops-view christianhuth/kube-ops-view \
  -n monitoring \
  -f values.yaml
```

---

# 10️⃣ 실습 과제

### 과제 1

kube-ops-view를 NodePort로 설치하고 특정 포트(32080)로 고정하시오.

### 과제 2

Replica를 2개로 늘려서 Pod 분산 배치를 확인하시오.

### 과제 3

Resource limit를 50m CPU로 낮추고 동작 확인하시오.

### 과제 4

MetalLB 환경에서 LoadBalancer로 변경 후 외부 IP로 접속하시오.

### 과제 5

Helm uninstall 후 재설치하고, 이전 설정이 유지되는지 확인하시오.

---

# 🔍 트러블슈팅

### NodePort 한 노드만 접속될 때

* flannel / CNI 라우팅 문제

* kube-proxy iptables 확인

* FORWARD 정책 확인

* PodCIDR 정상 할당 여부 확인

### 접속 안 될 때 확인 순서

```
kubectl get pod -n monitoring -o wide
kubectl get endpoints -n monitoring
kubectl get svc -n monitoring
sudo iptables -t nat -L | grep <NodePort>
```

---

# 📘 정리

| 항목 | 설명 |
| --- | --- |
| 설치 방법 | Helm |
| 기본 타입 | ClusterIP |
| 외부 접속 | NodePort / LoadBalancer |
| 목적 | 클러스터 시각화 |

---