---
title: "실습 노드풀 확장에 따른 DaemonSet 자동 배포"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Google 쿠버네티스 아키텍처 설계 및 구축"]
is_public: true
draft: false
---

# 실습. 노드풀 확장에 따른 DaemonSet 자동 배포

---

# 실습 목표

이 실습에서 확인할 내용은 아래와 같음.

* 현재 GKE Standard 클러스터에 노드가 2개 존재함

* DaemonSet 배포 후 각 노드에 Pod가 1개씩 생성됨

* 노드풀 크기를 3으로 확장하면 새 노드에도 DaemonSet Pod가 자동 생성됨

* `kubectl get ds`, `kubectl get pods -o wide`, `kubectl get nodes`로 이를 검증함

---

# 실습 환경

* 클러스터 이름: `이니셜-std-cluster-1`

* 현재 노드 수: `2`

* 존: `asia-northeast3-c`

---

# 실습 흐름

1. 현재 클러스터 인증 정보 가져오기

2. 현재 노드 2개 상태 확인

3. 실습용 DaemonSet 배포

4. 현재 노드별 DaemonSet Pod 확인

5. 노드풀 크기를 2 → 3으로 증가

6. 새 노드 Ready 확인

7. 새 노드에 DaemonSet Pod가 자동 생성됐는지 확인

---

# 1. 클러스터 인증 정보 가져오기

먼저 `kubectl`이 GKE 클러스터에 연결되도록 인증 정보를 가져옴.

```
gcloud container clusters get-credentials 이니셜-std-cluster-1 \
  --zone asia-northeast3-c
```

---

# 2. 현재 노드 상태 확인

```
kubectl get nodes
```

예상 출력 예시:

```
NAME                                                  STATUS   ROLES    AGE   VERSION
gke-이니셜-std-cluster-1-default-pool-xxxx            Ready    <none>   20m   v1.xx.x
gke-이니셜-std-cluster-1-default-pool-yyyy            Ready    <none>   20m   v1.xx.x
```

## 확인 포인트

* 노드가 정확히 2개인지 확인

* 두 노드 모두 `Ready` 상태인지 확인

* 아직 실습용 DaemonSet은 배포하지 않았으므로 관련 Pod는 없음

---

# 3. 노드풀 이름 확인

노드 확장 명령에서 **노드풀 이름**이 필요함.

일반적으로 기본값은 `default-pool`인 경우가 많지만, 실제 이름을 확인하는 것이 안전함.

```
gcloud container node-pools list \
  --cluster 이니셜-std-cluster-1 \
  --zone asia-northeast3-c
```

예상 출력 예시:

```
NAME          MACHINE_TYPE  DISK_SIZE_GB  NODE_VERSION
default-pool  e2-medium     100           1.xx.x-gke.xxx
```

## 확인 포인트

* 노드풀 이름이 `default-pool`인지 확인

* 다르면 아래 이후 명령에서 해당 이름으로 바꾸면 됨

---

# 4. 실습용 네임스페이스 생성

```
kubectl create namespace ds-lab
```

---

# 5. DaemonSet 매니페스트 작성

파일명: `daemonset-lab.yaml`

```
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: ds-nginx
  namespace: ds-lab
spec:
  selector:
    matchLabels:
      app: ds-nginx
  template:
    metadata:
      labels:
        app: ds-nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.25
        ports:
        - containerPort: 80
```

---

# 6. DaemonSet 배포

```
kubectl apply -f daemonset-lab.yaml
```

확인:

```
kubectl get daemonset -n ds-lab
```

예상 출력 예시:

```
NAME       DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR   AGE
ds-nginx   2         2         2       2            2           <none>          10s
```

## 항목 설명

* `DESIRED`

  DaemonSet이 배치하려는 목표 Pod 수임

  현재 배치 대상 노드 수와 거의 같게 보임

* `CURRENT`

  현재 실제 생성된 Pod 수임

* `READY`

  정상 실행 중인 Pod 수임

---

# 7. 현재 어떤 노드에 Pod가 배치됐는지 확인

```
kubectl get pods -n ds-lab -o wide
```

예상 출력 예시:

```
NAME             READY   STATUS    RESTARTS   AGE   IP           NODE
ds-nginx-2k8l9   1/1     Running   0          20s   10.52.1.10   gke-이니셜-std-cluster-1-default-pool-xxxx
ds-nginx-7q9xw   1/1     Running   0          20s   10.52.2.11   gke-이니셜-std-cluster-1-default-pool-yyyy
```

## 확인 포인트

* Pod가 2개 생성됐는지 확인

* 각 Pod가 서로 다른 노드에 1개씩 떠 있는지 확인

* `NODE` 컬럼이 핵심임

---

# 8. 노드풀 크기를 2개에서 3개로 확장

```
gcloud container clusters resize 이니셜-std-cluster-1 \
  --node-pool default-pool \
  --num-nodes 3 \
  --zone asia-northeast3-c
```

## 명령 설명

* `gcloud container clusters resize`

  GKE 클러스터의 특정 노드풀 크기를 조정하는 명령임

* `-node-pool default-pool`

  어떤 노드풀을 조정할지 지정함

  3단계에서 확인한 실제 노드풀 이름을 넣으면 됨

* `-num-nodes 3`

  노드풀의 노드 수를 3개로 맞춤

  현재 2개였으므로 1개가 새로 추가됨

* `-zone asia-northeast3-c`

  zonal cluster 기준 위치 정보임

GKE는 Standard 클러스터의 노드풀 크기를 수동으로 조정할 수 있고, 수요가 높을 때 클러스터 오토스케일러가 노드를 추가하는 기능도 제공함.

---

# 9. 새 노드 Ready 상태 확인

노드가 늘어나는 과정은 즉시 끝나지 않을 수 있음.

아래 명령으로 상태를 실시간 확인하면 됨.

```
kubectl get nodes -w
```

예상 흐름 예시:

```
gke-이니셜-std-cluster-1-default-pool-xxxx   Ready
gke-이니셜-std-cluster-1-default-pool-yyyy   Ready
gke-이니셜-std-cluster-1-default-pool-zzzz   NotReady
gke-이니셜-std-cluster-1-default-pool-zzzz   Ready
```

## `-w` 옵션 설명

* `watch` 옵션임

* 리소스 상태 변경을 계속 보여줌

* 새 노드가 `NotReady → Ready`로 바뀌는 과정 확인에 적합함

GKE 문서에서도 새 노드 생성에는 시간이 걸릴 수 있고, 노드가 시작된 뒤에 Pod가 배치된다고 설명함. ([Google Cloud Documentation](https://docs.cloud.google.com/kubernetes-engine/docs/how-to/capacity-provisioning?utm_source=chatgpt.com))

---

# 10. DaemonSet 상태 다시 확인

```
kubectl get daemonset -n ds-lab
```

예상 출력 예시:

```
NAME       DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR   AGE
ds-nginx   3         3         3       3            3           <none>          5m
```

## 핵심 확인 포인트

* `DESIRED`가 `2 → 3`으로 증가했는지 확인

* `CURRENT`, `READY`도 `3`이 되었는지 확인

이 값이 늘어났다면 **DaemonSet 컨트롤러가 새 노드를 인식했고, 새 노드에도 Pod를 자동 생성했음**을 의미함. ([Google Cloud Documentation](https://docs.cloud.google.com/kubernetes-engine/docs/tutorials/automatically-bootstrapping-gke-nodes-with-daemonsets?utm_source=chatgpt.com))

---

# 11. 새 노드에 Pod가 자동 생성됐는지 최종 확인

```
kubectl get pods -n ds-lab -o wide
```

예상 출력 예시:

```
NAME             READY   STATUS    RESTARTS   AGE    IP           NODE
ds-nginx-2k8l9   1/1     Running   0          6m     10.52.1.10   gke-이니셜-std-cluster-1-default-pool-xxxx
ds-nginx-7q9xw   1/1     Running   0          6m     10.52.2.11   gke-이니셜-std-cluster-1-default-pool-yyyy
ds-nginx-p4t8n   1/1     Running   0          40s    10.52.3.12   gke-이니셜-std-cluster-1-default-pool-zzzz
```

---

# 12. 정리

이번 실습으로 확인한 핵심은 아래와 같음.

* Deployment는 replica 수 중심으로 동작함

* DaemonSet은 노드 수 중심으로 동작함

* GKE에서 노드풀이 확장되면 새 노드가 클러스터에 참여함

* DaemonSet은 새 노드를 감지해서 해당 노드에 Pod를 자동 생성함

---

# 13. 정리

실습 리소스 삭제:

```
kubectl delete namespace ds-lab
```

노드 수를 다시 2개로 축소하려면:

```
gcloud container clusters resize 이니셜-std-cluster-1 \
  --node-pool default-pool \
  --num-nodes 2 \
  --zone asia-northeast3-c
```

---