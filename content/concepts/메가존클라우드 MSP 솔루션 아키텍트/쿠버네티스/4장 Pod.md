---
title: "4장 Pod"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "쿠버네티스"]
is_public: true
draft: false
---

# 4장. Pod

---

# 4-1. Pod란 무엇인가?

## 🔹 정의

> Pod는 Kubernetes에서 **가장 작은 배포 단위**이다.

* 1개 이상의 컨테이너 포함

* 같은 네트워크 네임스페이스 공유

* 같은 IP 주소 공유

* Volume 공유 가능

---

## 🔹 왜 Pod 단위로 묶을까?

Docker는 “컨테이너”가 실행 단위였지만

Kubernetes는 **여러 컨테이너가 하나의 애플리케이션 단위를 구성**하는 경우를 고려했다.

예:

* nginx + log 수집기

* app + sidecar proxy

* app + metrics exporter

---

# 4-2. Pod 내부 구조

```
Pod
 ├─ pause container  ← 네트워크 유지
 ├─ main container
 └─ sidecar container
```

## 🔹 Pause 컨테이너

* Pod의 네트워크 네임스페이스 유지

* 사용자가 직접 관리하지 않음

* kubelet이 자동 생성

👉 존재만 이해하면 충분

---

# 4-3. Pod 생성 실습 (명령형)

---

## 1️⃣ Pod 생성

```
kubectl run my-nginx --image=nginx:1.21
```

---

## 2️⃣ 확인

```
kubectl get pods
kubectl get pods -o wide
```

확인 항목:

* READY

* STATUS

* IP

* NODE

---

## 3️⃣ 상세 분석

```
kubectl describe pod my-nginx
```

중요 확인:

* Node

* Container ID

* Events

---

# 4-4. YAML로 Pod 생성

---

## nginx-pod.yaml

```
apiVersion: v1
kind: Pod
metadata:
  name: my-web
  labels:
    app: web
spec:
  containers:
  - name: nginx
    image: nginx:1.21
    ports:
    - containerPort: 80
```

---

## 적용

```
kubectl apply -f nginx-pod.yaml
```

---

# 4-5. Pod 네트워크 특징

## 🔹 Pod는 고유 IP를 가진다

```
kubectl get pods -o wide
```

출력 예:

```
my-web   1/1   Running   10.244.1.5
```

---

## 🔹 Pod 내부 컨테이너는 localhost 공유

Multi-container Pod에서는:

```
localhost:8080
```

으로 통신 가능

---

# 4-6. Multi-Container Pod 실습

---

## multi-container.yaml

```
apiVersion: v1
kind: Pod
metadata:
  name: multi-pod
spec:
  containers:
  - name: web
    image: nginx
    volumeMounts:
    - name: shared
      mountPath: /shared

  - name: logger
    image: busybox
    command:
    - sh
    - -c
    - |
      while true; do
        date >> /shared/log.txt
        sleep 5
      done
    volumeMounts:
    - name: shared
      mountPath: /shared

  volumes:
  - name: shared
    emptyDir: {}
```

---

## 적용

```
kubectl apply -f multi-container.yaml
```

로그 확인:

```
kubectl logs multi-pod -c logger
```

---

# 4-7. Init Container 실습 포함

---

## 🔹 Init Container란?

Pod 시작 전에 실행되는 준비 컨테이너

* 반드시 성공해야 메인 컨테이너 실행

* 순차 실행

* 준비 작업 전용

---

## 실습: HTML 생성 후 실행

### init-web.yaml

```
apiVersion: v1
kind: Pod
metadata:
  name: init-web
spec:
  initContainers:
  - name: create-html
    image: busybox
    command:
    - sh
    - -c
    - echo "<h1>Hello from Init</h1>" > /work/index
    volumeMounts:
    - name: html
      mountPath: /work

  containers:
  - name: nginx
    image: nginx
    ports:
    - containerPort: 80
    volumeMounts:
    - name: html
      mountPath: /usr/share/nginx/html

  volumes:
  - name: html
    emptyDir: {}
```

---

## 실행

```
kubectl apply -f init-web.yaml
kubectl get pods
```

상태 확인:

```
Init:0/1 → Init:1/1 → Running
```

---

# 4-8. Pod 접속 및 로그

---

## 로그 확인

```
kubectl logs my-web
kubectl logs my-web -f
kubectl logs my-web --tail=20
```

---

## 컨테이너 접속

```
kubectl exec -it my-web -- /bin/bash
```

특정 컨테이너 지정:

```
kubectl exec -it multi-pod -c web -- /bin/bash
```

---

# 4-9. Port Forward

Pod는 기본적으로 외부 접근 불가.

```
kubectl port-forward my-web 8080:80
```

테스트:

```
curl http://localhost:8080
```

---

# 4-10. Pod 상태 이해

```
kubectl get pods
```

| 상태 | 의미 |
| --- | --- |
| Pending | 스케줄 대기 |
| Running | 실행 중 |
| CrashLoopBackOff | 반복 실패 |
| Completed | 종료 |

---

# 4-11. Pod 리소스 제한

---

## 예시

```
resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "500m"
    memory: "256Mi"
```

* requests → 최소 보장

* limits → 최대 사용

---

# 4-12. Pod 동작 내부 흐름

```
1. kubectl apply
2. API Server 저장
3. etcd 기록
4. Scheduler가 Node 선택
5. kubelet이 Pod 생성
6. containerd가 컨테이너 실행
```

---

# 4-13. Pod의 한계

Pod를 직접 운영하면 문제 발생:

```
1. 자동 복구 없음
2. 스케일링 불편
3. 업데이트 어려움
4. IP 변경
```

그래서 등장:

* ReplicaSet

* Deployment

---

# 4-14. 실습 과제

---

### 과제 1

* Pod 생성

* IP 확인

* port-forward 테스트

---

### 과제 2

* multi-container Pod 생성

* shared volume 확인

---

### 과제 3

* init container 포함 Pod 생성

* 상태 변화 확인

---

# 4-15. 핵심 정리

```
1. Pod는 최소 배포 단위
2. 하나 이상의 컨테이너 포함
3. 같은 IP 공유
4. Init Container는 준비 작업용
5. 직접 운영용이 아니라 관리 객체 필요
```

---