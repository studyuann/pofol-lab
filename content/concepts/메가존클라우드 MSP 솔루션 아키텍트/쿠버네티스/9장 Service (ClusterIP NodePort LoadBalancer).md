---
title: "9장 Service (ClusterIP NodePort LoadBalancer)"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "쿠버네티스"]
is_public: true
draft: false
---

# 9장. Service (ClusterIP / NodePort / LoadBalancer)

[![](9%EC%9E%A5%20Service%20(ClusterIP%20NodePort%20LoadBalancer)/image.png)](9%EC%9E%A5%20Service%20(ClusterIP%20NodePort%20LoadBalancer)/image.png)

# 1. Service란 무엇인가?

---

## 1.1 왜 Service가 필요한가?

Pod의 특징:

* Pod IP는 동적으로 생성됨

* Pod 재생성 시 IP 변경

* 직접 IP 접근은 불안정

예:

```
Pod A → 10.244.1.5
Pod 재시작 → 10.244.2.7
```

이 문제를 해결하기 위해 Service를 사용한다.

Service는:

> Pod 집합에 대한 고정된 네트워크 진입점

---

## 1.2 Service의 핵심 기능

Service는 다음 3가지를 제공한다.

1. 고정 가상 IP (ClusterIP)

2. 라벨 기반 Pod 선택

3. 자동 로드밸런싱

---

## 1.3 Service 내부 구조

```
Client
   ↓
Service (Virtual IP)
   ↓
kube-proxy (iptables/IPVS)
   ↓
Pod 여러 개로 분산
```

kube-proxy가 실제 트래픽 전달을 담당한다.

---

# 2. Service 타입 3가지 (이론)

---

| 타입 | 외부 접근 | 사용 목적 |
| --- | --- | --- |
| ClusterIP | ❌ | 내부 통신 |
| NodePort | O | 테스트 |
| LoadBalancer | O | 운영 |

---

# 3. ClusterIP

---

## 3.1 개념

* 기본 Service 타입

* 클러스터 내부에서만 접근 가능

---

## 3.2 구조

```
Pod A
Pod B
Pod C
   ↑
Service (ClusterIP)
   ↑
다른 Pod
```

---

## 3.3 YAML 예제

```
apiVersion: v1
kind: Service
metadata:
  name: web-clusterip
spec:
  type: ClusterIP
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 80
```

---

# 4. NodePort

---

## 4.1 개념

* 노드 IP + 포트로 외부 접근 가능

* 모든 노드에서 동일 포트 오픈

---

## 4.2 구조

```
Internet
   ↓
NodeIP:30007
   ↓
Service
   ↓
Pod
```

---

## 4.3 특징

* 포트 범위: 30000~32767

* 내부적으로 ClusterIP 포함

* 운영보다는 테스트 환경에 적합

---

# 5. LoadBalancer

---

## 5.1 개념

* 외부 Load Balancer 생성 요청

* 클라우드 환경에서 자동 생성

* 운영 환경에서 사용

---

## 5.2 내부 구조

LoadBalancer는 실제로 다음 구조다.

```
Internet
   ↓
External LoadBalancer
   ↓
NodePort
   ↓
ClusterIP
   ↓
Pod
```

즉,

```
LoadBalancer ⊃ NodePort ⊃ ClusterIP
```

---

# 6. 클라우드 vs 온프레미스 차이

---

## 6.1 클라우드 환경

지원 환경:

* AWS

* GCP

* Azure

* KakaoCloud

### 동작 과정

```
Service 생성
   ↓
Cloud Controller Manager 감지
   ↓
클라우드 API 호출
   ↓
외부 LB 생성
   ↓
Public IP 자동 할당
```

확인:

```
kubectl get svc
```

```
EXTERNAL-IP  34.123.45.67
```

---

## 6.2 온프레미스 환경

온프레미스에서는:

```
EXTERNAL-IP  <pending>
```

이유:

* 클라우드 API 없음

* 외부 LB 자동 생성 불가

---

## 6.3 해결 방법 – MetalLB

MetalLB는:

* 온프레미스에서 LoadBalancer 구현

* IP Pool에서 IP 자동 할당

구조:

```
Service (LoadBalancer)
   ↓
MetalLB
   ↓
외부 IP 할당
```

---

# 7. 단계별 실습

---

# 7.1 Step 1 – Deployment 생성

```
kubectl create deployment web --image=nginx
kubectl scale deployment web --replicas=3
```

확인:

```
kubectl get pods -o wide
```

---

# 7.2 Step 2 – ClusterIP 실습

```
kubectl expose deployment web --port=80 --target-port=80 --type=ClusterIP
```

확인:

```
kubectl get svc
kubectl get endpoints
```

내부 테스트:

```
kubectl run test --image=busybox -it --rm -- sh
wget -qO- http://web
```

---

# 7.3 Step 3 – NodePort 변경

```
kubectl patch svc web -p '{"spec":{"type":"NodePort"}}'
```

```
apiVersion: v1
kind: Service
metadata:
  name: web-nodeport
spec:
  type: NodePort
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30080
```

확인:

```
kubectl get svc
```

접속:

```
http://NodeIP:<nodePort>
```

---

# 7.4 Step 4 – LoadBalancer 변경 (클라우드)

```
apiVersion: v1
kind: Service
metadata:
  name: web-lb
spec:
  type: LoadBalancer
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 80
```

```
kubectl patch svc web -p '{"spec":{"type":"LoadBalancer"}}'
```

확인:

```
kubectl get svc
```

EXTERNAL-IP 확인.

---

# 7.5 온프레미스에서 확인

```
kubectl get svc
```

```
EXTERNAL-IP <pending>
```

이 상태가 정상이다.

---

# 8. Endpoint 이해 실습

라벨 변경:

```
kubectl label pod <pod이름> app=other --overwrite
```

확인:

```
kubectl get endpoints
```

Endpoint 비어 있음.

→ Service는 라벨 기반 동작.

---

# 9. 트러블슈팅

---

## 외부 접속 안 됨

* 보안 그룹 확인

* 방화벽 확인

* NodePort 범위 확인

---

## EXTERNAL-IP 계속 pending

* 클라우드 환경인지 확인

* MetalLB 설치 여부 확인

---

# 10. 핵심 정리

Service는:

* Pod 집합에 대한 고정 진입점

* 라벨 기반 연결

* 자동 로드밸런싱

타입 요약:

1. ClusterIP → 내부 전용

2. NodePort → 노드 포트 외부 접근

3. LoadBalancer → 클라우드 외부 서비스

환경 차이:

* 클라우드 → 자동 IP

* 온프레미스 → 추가 구성 필요 (MetalLB)

---

- [[MetalLB(로드밸런서 구현체)]]