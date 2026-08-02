---
title: "실습 GKE Ingress Gateway API 서비스 노출"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Google 쿠버네티스 아키텍처 설계 및 구축"]
is_public: true
draft: false
---

# 실습. GKE Ingress / Gateway API 서비스 노출

## 1. 실습 목표

1. GKE 클러스터에 샘플 애플리케이션을 배포한다.

2. Service를 생성한다.

3. Ingress를 이용해 외부 HTTP 접속을 구성한다.

4. Gateway API를 이용해 외부 HTTP 접속을 구성한다.

5. 외부 IP를 확인하고 브라우저 또는 `curl`로 접속을 검증한다.

6. 실습 종료 후 리소스를 정리한다.

---

## 2. 실습 환경

다음 환경을 기준으로 진행한다.

* GCP 프로젝트 1개

* GKE Standard 클러스터 1개

* Cloud Shell 또는 `kubectl`, `gcloud`가 설치된 터미널

* 리전/존 예시
  + 리전: `asia-northeast3`
  + 존: `asia-northeast3-a`

---

## 3. 사전 준비

## 3-1. 환경 변수 설정

Cloud Shell에서 아래 값을 먼저 설정한다.

```
export PROJECT_ID=$(gcloud config get-value project)
export CLUSTER_NAME=이니셜-std-cluster-1
export ZONE=asia-northeast3-c
export REGION=asia-northeast3
export NAMESPACE=expose-lab
```

확인:

```
echo $PROJECT_ID
echo $CLUSTER_NAME
echo $ZONE
echo $REGION
echo $NAMESPACE
```

---

## 3-2. API 활성화

```
gcloud services enable container.googleapis.com
```

---

## 3-3. 클러스터 접속 정보 가져오기

```
gcloud container clusters get-credentials $CLUSTER_NAME \
  --zone=$ZONE
```

현재 컨텍스트 확인:

```
kubectl config current-context
```

노드 확인:

```
kubectl get nodes
```

---

## 3-4. 네임스페이스 생성

```
kubectl create namespace $NAMESPACE
```

확인:

```
kubectl get ns
```

---

# 4. 공통 실습 - 샘플 애플리케이션 배포

Ingress와 Gateway API 둘 다 같은 애플리케이션을 대상으로 실습한다.

## 4-1. 샘플 Deployment 생성

파일명: `web-deploy.yaml`

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  namespace: expose-lab
spec:
  replicas: 2
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
        image: us-docker.pkg.dev/google-samples/containers/gke/hello-app:1.0
        ports:
        - containerPort: 8080
```

적용:

```
kubectl apply -f web-deploy.yaml
```

확인:

```
kubectl get deploy -n $NAMESPACE
kubectl get pods -n $NAMESPACE -o wide
```

### 설정 설명

`replicas: 2`

같은 애플리케이션 Pod를 2개 실행한다. 하나가 재시작되거나 문제가 생겨도 다른 Pod가 계속 서비스할 수 있게 하기 위함이다.

`containerPort: 8080`

컨테이너 내부 애플리케이션이 8080 포트에서 동작함을 의미한다. 실제 외부 노출 포트는 나중에 Service나 Ingress/Gateway에서 별도로 지정한다.

---

## 4-2. Service 생성

Ingress와 Gateway API는 모두 결국 Service를 백엔드 대상으로 사용한다.

파일명: `web-svc.yaml`

```
apiVersion: v1
kind: Service
metadata:
  name: web
  namespace: expose-lab
spec:
  selector:
    app: web
  ports:
  - port: 8080
    targetPort: 8080
  type: NodePort
```

적용:

```
kubectl apply -f web-svc.yaml
```

확인:

```
kubectl get svc -n $NAMESPACE
kubectl describe svc web -n $NAMESPACE
```

---

# 5. 실습 1 - Ingress를 이용한 서비스 노출

GKE의 기본 Ingress는 `kind: Ingress` 리소스를 생성하면 외부 Application Load Balancer를 자동 구성한다. 별도의 서드파티 NGINX Ingress 컨트롤러 기준이 아니라, **GKE 기본 Ingress** 기준 실습이다.

## 5-1. 가장 단순한 Ingress 생성

파일명: `basic-ingress.yaml`

```
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: basic-ingress
  namespace: expose-lab
spec:
  defaultBackend:
    service:
      name: web
      port:
        number: 8080
```

적용:

```
kubectl apply -f basic-ingress.yaml
```

---

## 5-2. Ingress 상태 확인

```
kubectl get ingress -n $NAMESPACE
kubectl describe ingress basic-ingress -n $NAMESPACE
```

### 확인 포인트

`ADDRESS` 컬럼에 외부 IP가 할당되는지 확인한다.

처음에는 비어 있거나 `pending`처럼 보일 수 있다.

외부 Application Load Balancer가 생성되고 전파되는 데 몇 분 정도 걸릴 수 있다.

외부 IP만 따로 보고 싶다면:

```
kubectl get ingress basic-ingress -n $NAMESPACE \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}'; echo
```

---

## 5-3. 접속 테스트

외부 IP를 변수로 저장:

```
export INGRESS_IP=$(kubectl get ingress basic-ingress -n $NAMESPACE \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo $INGRESS_IP
```

접속 확인:

```
curl http://$INGRESS_IP
```

정상이라면 다음과 비슷한 응답이 나온다.

```
Hello, world!
Version: 1.0.0
```

---

## 5-4. 경로 기반 라우팅 확장 실습

이번에는 `/`와 `/v2` 경로를 서로 다른 서비스로 보내는 예시를 실습한다.

### 두 번째 앱 배포

파일명: `web2-deploy.yaml`

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web2
  namespace: expose-lab
spec:
  replicas: 2
  selector:
    matchLabels:
      app: web2
  template:
    metadata:
      labels:
        app: web2
    spec:
      containers:
      - name: web2
        image: us-docker.pkg.dev/google-samples/containers/gke/hello-app:2.0
        ports:
        - containerPort: 8080
```

적용:

```
kubectl apply -f web2-deploy.yaml
```

### 두 번째 Service 생성

파일명: `web2-svc.yaml`

```
apiVersion: v1
kind: Service
metadata:
  name: web2
  namespace: expose-lab
spec:
  selector:
    app: web2
  ports:
  - port: 8080
    targetPort: 8080
  type: NodePort
```

적용:

```
kubectl apply -f web2-svc.yaml
```

### Fanout Ingress 생성

파일명: `fanout-ingress.yaml`

```
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: fanout-ingress
  namespace: expose-lab
spec:
  rules:
  - http:
      paths:
      - path: /*
        pathType: ImplementationSpecific
        backend:
          service:
            name: web
            port:
              number: 8080
      - path: /v2/*
        pathType: ImplementationSpecific
        backend:
          service:
            name: web2
            port:
              number: 8080
```

적용:

```
kubectl apply -f fanout-ingress.yaml
```

---

## 5-5. Fanout Ingress 검증

```
kubectl get ingress -n $NAMESPACE
kubectl describe ingress fanout-ingress -n $NAMESPACE
```

IP 확인:

```
export FANOUT_IP=$(kubectl get ingress fanout-ingress -n $NAMESPACE \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo $FANOUT_IP
```

테스트:

```
curl http://$FANOUT_IP/
curl http://$FANOUT_IP/v2/
```

### 기대 결과

* `/` 요청은 `web` 서비스로 전달된다.

* `/v2/` 요청은 `web2` 서비스로 전달된다.

---

# 6. 실습 2 - Gateway API를 이용한 서비스 노출

Gateway API는 Ingress보다 역할이 더 분리돼 있다.

* `GatewayClass`: 어떤 종류의 로드밸런서를 만들지 결정

* `Gateway`: 어디서 어떻게 받을지 결정

* `HTTPRoute`: 어떤 요청을 어느 Service로 보낼지 결정

GKE는 여러 GatewayClass를 제공하며, 외부 공개용으로는 `gke-l7-global-external-managed` 또는 `gke-l7-regional-external-managed`를 사용할 수 있다. 단일 실습에서는 전역 외부 ALB 기반인 `gke-l7-global-external-managed`가 가장 일반적이다.

---

## 6-1. 사용 가능한 GatewayClass 확인

```
kubectl get gatewayclass
```

정상이라면 다음과 비슷한 항목이 보일 수 있다.

```
gke-l7-global-external-managed
gke-l7-regional-external-managed
gke-l7-rilb
```

---

## 6-2. Gateway 생성

가장 단순한 외부 HTTP Gateway를 생성한다.

파일명: `external-gateway.yaml`

```
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: external-http
  namespace: expose-lab
spec:
  gatewayClassName: gke-l7-global-external-managed
  listeners:
  - name: http
    protocol: HTTP
    port: 80
```

적용:

```
kubectl apply -f external-gateway.yaml
```

`gatewayClassName: gke-l7-global-external-managed`가 전역 외부 Application Load Balancer를 의미한다.

---

## 6-3. Gateway 상태 확인

```
kubectl get gateway -n $NAMESPACE
kubectl describe gateway external-http -n $NAMESPACE
```

외부 IP 확인:

```
kubectl get gateway external-http -n $NAMESPACE \
  -o jsonpath='{.status.addresses[0].value}'; echo
```

`status.addresses.value`에 외부 IP가 표시된다.

---

## 6-4. HTTPRoute 생성

이제 Gateway로 들어온 요청을 `web` 서비스로 연결한다.

파일명: `web-route.yaml`

```
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: web-route
  namespace: expose-lab
spec:
  parentRefs:
  - kind: Gateway
    name: external-http
  rules:
  - backendRefs:
    - name: web
      port: 8080
```

적용:

```
kubectl apply -f web-route.yaml
```

`HTTPRoute`는 Gateway로 들어온 HTTP(S) 트래픽을 Kubernetes Service로 라우팅하는 리소스다.

---

## 6-5. HTTPRoute 상태 확인

```
kubectl get httproute -n $NAMESPACE
kubectl describe httproute web-route -n $NAMESPACE
```

### 확인 포인트

`Accepted=True`

HTTPRoute가 Gateway에 정상적으로 바인딩됐다는 뜻이다.

`Reconciled=True`

실제 구성 반영이 정상적으로 진행됐다는 뜻이다.

---

## 6-6. 접속 테스트

외부 IP 변수 저장:

```
export GATEWAY_IP=$(kubectl get gateway external-http -n $NAMESPACE \
  -o jsonpath='{.status.addresses[0].value}')
echo $GATEWAY_IP
```

접속 테스트:

```
curl http://$GATEWAY_IP
```

정상이라면 `hello-app` 응답이 출력된다.

---

# 7. Gateway API 경로 기반 라우팅 확장 실습

이번에는 Gateway API에서 `/`는 `web`, `/v2`는 `web2`로 라우팅한다.

파일명: `fanout-route.yaml`

```
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: fanout-route
  namespace: expose-lab
spec:
  parentRefs:
  - kind: Gateway
    name: external-http
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /v2
    backendRefs:
    - name: web2
      port: 8080
  - matches:
    - path:
        type: PathPrefix
        value: /
    backendRefs:
    - name: web
      port: 8080
```

적용:

```
kubectl apply -f fanout-route.yaml
```

검증:

```
kubectl describe httproute fanout-route -n $NAMESPACE
curl http://$GATEWAY_IP/
curl http://$GATEWAY_IP/v2
```

HTTPRoute는 경로 기반 라우팅, 헤더 기반 라우팅, URL rewrite 같은 규칙을 제공하며, 경로 매칭은 `PathPrefix`를 사용한다.

---

# 8. Ingress와 Gateway API 실습 결과 비교

## Ingress 방식

Ingress에서는 `Ingress` 리소스 하나가 진입점과 라우팅 규칙을 포함한다.

### 핵심 확인 명령

```
kubectl get ingress -n $NAMESPACE
kubectl describe ingress basic-ingress -n $NAMESPACE
```

### 외부 IP 확인 위치

```
.status.loadBalancer.ingress[0].ip
```

GKE Ingress는 생성 시 외부 Application Load Balancer를 자동으로 구성한다.

---

## Gateway API 방식

Gateway API에서는 역할이 분리된다.

* GatewayClass는 로드밸런서 종류

* Gateway는 수신 포트/프로토콜

* HTTPRoute는 라우팅 규칙

조금 더 리소스가 많지만, 대규모 운영이나 팀 분리 관점에서는 더 구조적이다.

### 핵심 확인 명령

```
kubectl get gateway -n $NAMESPACE
kubectl get httproute -n $NAMESPACE
kubectl describe gateway external-http -n $NAMESPACE
kubectl describe httproute web-route -n $NAMESPACE
```

### 외부 IP 확인 위치

```
.status.addresses[0].value
```

---

# 10. 정리

## 10-1. Ingress 관련 리소스 삭제

```
kubectl delete ingress fanout-ingress -n $NAMESPACE --ignore-not-found
kubectl delete ingress basic-ingress -n $NAMESPACE --ignore-not-found
```

---

## 10-2. Gateway API 관련 리소스 삭제

```
kubectl delete httproute fanout-route -n $NAMESPACE --ignore-not-found
kubectl delete httproute web-route -n $NAMESPACE --ignore-not-found
kubectl delete gateway external-http -n $NAMESPACE --ignore-not-found
```

---

## 10-3. 애플리케이션 삭제

```
kubectl delete svc web2 -n $NAMESPACE --ignore-not-found
kubectl delete svc web -n $NAMESPACE --ignore-not-found

kubectl delete deploy web2 -n $NAMESPACE --ignore-not-found
kubectl delete deploy web -n $NAMESPACE --ignore-not-found
```

---

## 10-4. 네임스페이스 삭제

```
kubectl delete namespace $NAMESPACE
```

---