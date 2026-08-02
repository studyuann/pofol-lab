---
title: "실습 Service Mesh"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Google 쿠버네티스 아키텍처 설계 및 구축"]
is_public: true
draft: false
---

# 실습. Service Mesh

---

# 1. 실습 개요

## 1-1. 실습 목적

이미 배포해둔 **Online Boutique 마이크로서비스 애플리케이션** 위에

**Service Mesh를 적용해보는 실습**이다.

이전 실습에서는 Kubernetes만으로도 다음이 가능했음.

* 여러 서비스 배포

* 서비스 간 통신

* 외부 노출

* 장애 시 Pod 재생성

* 확장 및 축소

하지만 실제 MSA 운영에서는 이것만으로 부족한 경우가 많다.

서비스 수가 많아질수록 **서비스 간 통신을 더 정교하게 제어할 필요**가 생긴다.

예를 들면 다음 같은 요구가 생긴다.

* 새 버전으로 10%만 보내고 싶다.

* 특정 서비스 호출에 지연을 일부러 넣고 싶다.

* 서비스 간 통신 흐름을 더 세밀하게 제어하고 싶다.

* 내부 서비스 간 통신도 보안적으로 강화하고 싶다.

이런 요구를 해결하기 위해 Service Mesh를 사용한다.

---

## 1-2. 실습 목표

이번 실습의 목표는 다음과 같다.

1. Service Mesh가 왜 필요한지 이해한다.

2. Kubernetes와 Service Mesh의 역할 차이를 이해한다.

3. Online Boutique에 Service Mesh를 적용하는 구조를 이해한다.

4. 사이드카 주입 후 Pod 구조 변화를 확인한다.

5. `frontend` 서비스를 두 버전으로 나누고 트래픽을 분할한다.

6. `recommendationservice`에 지연 장애를 주입한다.

7. 서비스 메시가 운영 환경에서 왜 유용한지 체감한다.

---

# 2. Service Mesh가 왜 필요한가

---

## 2-1. Kubernetes만으로도 애플리케이션은 잘 동작한다

Kubernetes는 매우 강력한 오케스트레이션 플랫폼이다.

지금까지의 실습에서도 이미 확인했듯이 Kubernetes만으로도 다음은 충분히 가능하다.

* 애플리케이션 배포

* 서비스 디스커버리

* 롤링 업데이트

* 스케일 조정

* 장애 복구

* 외부 노출

즉, **애플리케이션을 실행하고 관리하는 플랫폼**으로 Kubernetes는 매우 훌륭하다.

---

## 2-2. 하지만 서비스 간 통신 제어는 더 복잡해진다

문제는 서비스 수가 많아질수록 **서비스 간 호출 자체를 어떻게 다룰 것인가**가 중요해진다는 점이다.

예를 들어 Online Boutique를 생각해보면 다음처럼 여러 서비스가 연결된다.

* `frontend`

* `productcatalogservice`

* `cartservice`

* `checkoutservice`

* `recommendationservice`

* `currencyservice`

* `adservice`

이 구조에서는 단순히 “서비스가 호출된다” 수준을 넘어서 이런 요구가 생긴다.

* 특정 버전의 `frontend`로 일부 요청만 보내고 싶다.

* `recommendationservice`가 느릴 때 어떤 현상이 생기는지 보고 싶다.

* 서비스 호출 실패나 지연을 정책으로 제어하고 싶다.

* 앱 코드를 수정하지 않고 트래픽 정책을 바꾸고 싶다.

---

## 2-3. Service Mesh의 역할

Service Mesh는 **서비스 간 통신을 제어하는 전용 계층**이라고 보면 된다.

한 줄로 정리하면 다음과 같다.

* **Kubernetes**: 애플리케이션 배포, 실행, 확장, 복구

* **Service Mesh**: 서비스 간 통신 제어, 보안, 관측, 트래픽 관리

즉, 둘은 경쟁 관계가 아니라 **서로 역할이 다르다**.

---

## 2-4. Service Mesh가 제공하는 대표 기능

Service Mesh는 보통 다음 같은 기능을 제공한다.

* 버전별 트래픽 분할

* 카나리 배포

* A/B 테스트

* 장애 주입

* Retry / Timeout / Circuit Breaker

* 서비스 간 인증 및 암호화

* 서비스 호출 관측

이번 실습에서는 이 중에서 가장 체감이 쉬운 아래 3가지만 다룬다.

1. 사이드카 주입

2. 트래픽 분할

3. 지연 장애 주입

---

# 3. 왜 Online Boutique에 잘 맞는가

Online Boutique는 여러 마이크로서비스가 연결된 구조라서

Service Mesh를 붙였을 때 효과를 설명하기 좋다.

특히 다음 이유 때문에 실습 대상으로 적합하다.

* 이미 서비스가 많아서 서비스 간 호출 구조를 설명하기 좋다.

* `frontend`를 대상으로 버전 분리를 하기 쉽다.

* `recommendationservice` 같은 서비스를 대상으로 장애 주입을 체감하기 쉽다.

* 기존 실습에서 이미 구조를 알고 있으므로 Service Mesh 적용 전후 비교가 쉽다.

즉, 이번 실습은 **새 애플리케이션을 만드는 실습이 아니라**,

**이미 배포해둔 MSA 위에 운영 제어 계층을 얹는 실습**이라고 보면 된다.

---

# 4. 실습 전체 흐름

이번 실습은 아래 순서로 진행한다.

1. 클러스터 및 기존 Online Boutique 상태 확인

2. Istio 설치

3. 사이드카 자동 주입 활성화

4. Online Boutique Pod 재생성

5. `istio-proxy` 확인

6. `frontend`를 `v1`, `v2` 두 버전으로 분리

7. `DestinationRule` 생성

8. `VirtualService` 생성

9. 트래픽 분할 확인

10. `recommendationservice` 지연 장애 주입

11. 정책 삭제 및 원복

12. 정리

---

# 5. 실습 전제 조건

아래 항목이 완료되어 있다고 가정한다.

* GKE Standard 클러스터 생성 완료

* Online Boutique 기본 배포 완료

* `frontend-external`을 통한 접속 가능

* `kubectl` 사용 가능

* 클러스터 관리자 권한 보유

---

# 6. 실습 1: 환경 확인

---

## 6-1. 환경 변수 설정

```
export PROJECT_ID=내_프로젝트_ID
export REGION=asia-northeast3
export CLUSTER_NAME=이니셜-std-cluster-1
export NAMESPACE=default
```

### 설명

* `PROJECT_ID`는 현재 실습에 사용하는 GCP 프로젝트 ID다.

* `REGION`은 GKE Standard 클러스터가 생성된 리전이다.

* `CLUSTER_NAME`은 클러스터 이름이다.

* `NAMESPACE`는 Online Boutique가 배포된 네임스페이스다. 기본적으로 `default`를 사용한다고 가정한다.

---

## 6-2. 클러스터 연결 확인

```
gcloud container clusters get-credentials $CLUSTER_NAME --region $REGION

kubectl get nodes
```

### 설명

### `gcloud container clusters get-credentials`

로컬 환경의 kubeconfig에 해당 클러스터 접속 정보를 저장한다.

이 명령을 실행해야 `kubectl`이 어느 클러스터를 대상으로 동작할지 알 수 있다.

### `kubectl get nodes`

현재 연결된 클러스터의 노드 목록을 보여준다.

노드가 정상적으로 보이면 클러스터 연결이 완료된 것이다.

---

## 6-3. 기존 Online Boutique 상태 확인

```
kubectl get deploy -n $NAMESPACE
kubectl get pods -n $NAMESPACE
kubectl get svc -n $NAMESPACE
```

### 설명

기존 Online Boutique가 정상 배포되어 있는지 확인한다.

특히 아래를 중점적으로 본다.

* 주요 Deployment가 존재하는가

* Pod가 Running 상태인가

* `frontend-external` Service가 존재하는가

---

# 7. 실습 2: Istio 설치

이번 실습에서는 Service Mesh 구현체로 **Istio**를 사용한다.

교육용으로는 가장 이해하기 쉽고, 이후 `VirtualService`, `DestinationRule` 같은 리소스를 설명하기에도 적합하다.

---

## 7-1. Istio 다운로드

```
curl -L https://istio.io/downloadIstio | sh -
cd istio-*
export PATH=$PWD/bin:$PATH
istioctl version
```

### 설명

### `curl -L https://istio.io/downloadIstio | sh -`

Istio 설치 파일을 다운로드하고 압축을 푼다.

### `cd istio-*`

압축이 해제된 Istio 디렉터리로 이동한다.

### `export PATH=$PWD/bin:$PATH`

현재 디렉터리의 `bin` 폴더를 PATH에 추가해서 `istioctl` 명령을 바로 실행할 수 있게 한다.

### `istioctl version`

설치된 `istioctl` 버전을 확인한다.

---

## 7-2. Istio 설치

```
istioctl install --set profile=demo -y
```

### 설명

### `istioctl install`

Istio control plane을 클러스터에 설치한다.

### `--set profile=demo`

실습용 데모 프로파일을 사용한다.

데모 프로파일은 실습과 이해 중심 환경에 적합하다.

---

## 7-3. 설치 확인

```
kubectl get pods -n istio-system
```

### 설명

`istio-system` 네임스페이스에 `istiod` 관련 Pod가 Running 상태인지 확인한다.

이 Pod가 Service Mesh의 제어 평면 역할을 수행한다.

---

# 8. 실습 3: 사이드카 자동 주입

## 8-1. 사이드카란 무엇인가

Service Mesh 환경에서는 각 Pod 안에 원래 애플리케이션 컨테이너만 있는 것이 아니라,

그 옆에 **프록시 컨테이너**가 함께 붙는다.

이 프록시가 트래픽을 가로채고 정책을 적용한다.

즉, 애플리케이션 코드가 직접 복잡한 네트워크 정책을 처리하지 않아도

Service Mesh가 통신을 제어할 수 있게 된다.

이 프록시 컨테이너가 바로 **사이드카**다.

---

## 8-2. 네임스페이스 라벨 확인

```
kubectl get ns --show-labels
```

### 설명

네임스페이스에 어떤 라벨이 붙어 있는지 확인한다.

Istio는 네임스페이스 라벨을 기준으로 사이드카 자동 주입 여부를 판단한다.

---

## 8-3. 사이드카 자동 주입 활성화

```
kubectl label namespace $NAMESPACE istio-injection=enabled --overwrite
```

### 설명

이 명령은 `default` 네임스페이스에 사이드카 자동 주입 라벨을 설정한다.

### `istio-injection=enabled`

이 라벨이 붙은 네임스페이스에 새로 생성되는 Pod에는

`istio-proxy` 컨테이너가 자동으로 함께 주입된다.

### `--overwrite`

기존에 같은 키의 라벨이 있어도 덮어쓴다.

---

## 8-4. 기존 Pod 재시작

라벨을 추가했다고 해서 이미 실행 중인 Pod에 바로 사이드카가 생기지는 않는다.

새로 생성되는 Pod부터 적용되므로 Deployment를 재시작해야 한다.

```
kubectl get deployments -n $NAMESPACE -o name | xargs -n1 kubectl rollout restart -n $NAMESPACE
```

### 설명

### `kubectl get deployments -o name`

현재 네임스페이스의 Deployment 목록을 이름 형식으로 출력한다.

### `xargs -n1 kubectl rollout restart`

각 Deployment를 하나씩 롤링 재시작한다.

이 과정에서 새 Pod가 생성되고, 그 새 Pod에 사이드카가 붙는다.

---

## 8-5. 사이드카 확인

```
kubectl get pods -n $NAMESPACE
kubectl describe pod -n $NAMESPACE <frontend-pod-name>
```

### 설명

`kubectl describe pod` 출력에서 `Containers:` 항목을 보면

원래 앱 컨테이너 외에 `istio-proxy` 컨테이너가 추가된 것을 확인할 수 있다.

### 이해해야 할 점

이제부터 서비스 간 통신은

앱 컨테이너가 직접 네트워크를 처리하는 구조가 아니라,

각 Pod의 사이드카 프록시를 통해 제어되는 구조가 된다.

---

# 9. 실습 4: `frontend` 버전 분리 준비

트래픽 분할을 하려면 **같은 서비스에 대해 두 개 이상의 버전**이 있어야 한다.

이번 실습에서는 `frontend`를 두 버전으로 나눈다.

* `frontend-v1`

* `frontend-v2`

중요한 점은 다음이다.

* 사용자 입장에서는 여전히 `frontend` 서비스 하나만 보인다.

* 하지만 실제 Pod는 `v1`, `v2` 두 그룹으로 나뉜다.

* Service Mesh는 이 두 그룹에 요청 비율을 다르게 보낼 수 있다.

---

## 9-1. 현재 `frontend` 리소스 확인

```
kubectl get deploy frontend -n $NAMESPACE
kubectl get svc frontend -n $NAMESPACE -o yaml
kubectl get pods -n $NAMESPACE -l app=frontend --show-labels
```

### 설명

먼저 현재 `frontend` Service의 selector를 확인해야 한다.

보통 아래와 비슷하게 되어 있다.

```
spec:
  selector:
    app: frontend
```

즉, `frontend` Service는 `app=frontend` 라벨을 가진 Pod를 대상으로 트래픽을 보낸다.

따라서 새로 만들 `frontend-v1`, `frontend-v2` Pod도

반드시 `app=frontend` 라벨을 가져야 한다.

대신 버전 구분을 위해 다음 라벨을 추가한다.

* `version=v1`

* `version=v2`

---

## 9-2. 기존 `frontend` 백업

```
kubectl get deploy frontend -n $NAMESPACE -o yaml > frontend-original-backup.yaml
kubectl get svc frontend -n $NAMESPACE -o yaml > frontend-service-backup.yaml
```

### 설명

실습 중 문제가 생겼을 때 원복할 수 있도록 기존 `frontend` Deployment와 Service 설정을 백업한다.

---

## 9-3. 기존 `frontend` Deployment 삭제

```
kubectl delete deploy frontend -n $NAMESPACE
```

### 설명

기존 `frontend` Deployment를 제거하고,

그 자리를 `frontend-v1`, `frontend-v2` 두 Deployment로 대체한다.

Service는 삭제하지 않는다.

즉, `frontend` Service는 그대로 유지된다.

---

# 10. 실습 5: `frontend-v1`, `frontend-v2` Deployment 생성

---

## 10-1. `frontend-v1.yaml`

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend-v1
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: frontend
      version: v1
  template:
    metadata:
      labels:
        app: frontend
        version: v1
    spec:
      containers:
      - name: server
        image: us-central1-docker.pkg.dev/google-samples/microservices-demo/frontend:v0.10.3
        ports:
        - containerPort: 8080
        env:
        - name: PORT
          value: "8080"
        - name: PRODUCT_CATALOG_SERVICE_ADDR
          value: "productcatalogservice:3550"
        - name: CURRENCY_SERVICE_ADDR
          value: "currencyservice:7000"
        - name: CART_SERVICE_ADDR
          value: "cartservice:7070"
        - name: RECOMMENDATION_SERVICE_ADDR
          value: "recommendationservice:8080"
        - name: SHIPPING_SERVICE_ADDR
          value: "shippingservice:50051"
        - name: CHECKOUT_SERVICE_ADDR
          value: "checkoutservice:5050"
        - name: AD_SERVICE_ADDR
          value: "adservice:9555"
        - name: SHOPPING_ASSISTANT_SERVICE_ADDR
          value: "shoppingassistantservice:80"
```

---

## 10-2. `frontend-v2.yaml`

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend-v2
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: frontend
      version: v2
  template:
    metadata:
      labels:
        app: frontend
        version: v2
    spec:
      containers:
      - name: server
        image: us-central1-docker.pkg.dev/google-samples/microservices-demo/frontend:v0.10.3
        ports:
        - containerPort: 8080
        env:
        - name: PORT
          value: "8080"
        - name: PRODUCT_CATALOG_SERVICE_ADDR
          value: "productcatalogservice:3550"
        - name: CURRENCY_SERVICE_ADDR
          value: "currencyservice:7000"
        - name: CART_SERVICE_ADDR
          value: "cartservice:7070"
        - name: RECOMMENDATION_SERVICE_ADDR
          value: "recommendationservice:8080"
        - name: SHIPPING_SERVICE_ADDR
          value: "shippingservice:50051"
        - name: CHECKOUT_SERVICE_ADDR
          value: "checkoutservice:5050"
        - name: AD_SERVICE_ADDR
          value: "adservice:9555"
        - name: SHOPPING_ASSISTANT_SERVICE_ADDR
          value: "shoppingassistantservice:80"
```

---

## 10-3. Deployment 적용

```
kubectl apply -f frontend-v1.yaml
kubectl apply -f frontend-v2.yaml
```

---

## 10-4. 확인

```
kubectl get deploy -n $NAMESPACE
kubectl get pods -n $NAMESPACE -l app=frontend -L version
kubectl get endpoints frontend -n $NAMESPACE
```

### 설명

### `kubectl get pods -L version`

`version` 라벨 값을 컬럼으로 보여준다.

`v1`, `v2`가 분리되어 보이는지 확인한다.

### `kubectl get endpoints frontend`

`frontend` Service가 실제로 어떤 Pod IP를 backend로 잡고 있는지 확인한다.

여기서 `frontend-v1`, `frontend-v2` Pod가 모두 endpoint에 포함되어야 한다.

# 11. 실습 6: DestinationRule 생성

트래픽 분할을 하려면 먼저 Service Mesh에

“`frontend` 서비스 안에 `v1`, `v2` 두 버전 그룹이 있다”는 사실을 알려줘야 한다.

이 역할을 하는 것이 `DestinationRule`이다.

---

## 11-1. `frontend-destinationrule.yaml`

```
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: frontend
  namespace: default
spec:
  host: frontend.default.svc.cluster.local
  subsets:
  - name: v1
    labels:
      version: v1
  - name: v2
    labels:
      version: v2
```

### 설명

### `host`

어떤 Kubernetes Service를 대상으로 할지 지정한다.

여기서는 `frontend` Service를 의미한다.

### `subsets`

서비스 내부의 버전 그룹을 정의한다.

* `v1` subset → `version=v1`

* `v2` subset → `version=v2`

즉, 이 리소스는

“`frontend` 안에는 `v1`, `v2`라는 두 개의 버전 그룹이 있다”

라고 Service Mesh에 알려주는 역할을 한다.

---

## 11-2. 적용 및 확인

```
kubectl apply -f frontend-destinationrule.yaml
kubectl get destinationrule -n $NAMESPACE
kubectl describe destinationrule frontend -n $NAMESPACE
```

---

# 12. 실습 7: VirtualService로 트래픽 분할

이제 실제로 트래픽을 나눠 보낸다.

이번 실습에서는 다음처럼 설정한다.

* `v1`로 90%

* `v2`로 10%

즉, 대부분 요청은 기존 버전으로 보내고,

일부 요청만 새 버전으로 보내는 카나리 배포 구조를 체험하는 것이다.

---

## 12-1. `frontend-virtualservice.yaml`

```
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: frontend
  namespace: default
spec:
  hosts:
  - frontend.default.svc.cluster.local
  http:
  - route:
    - destination:
        host: frontend.default.svc.cluster.local
        subset: v1
      weight: 90
    - destination:
        host: frontend.default.svc.cluster.local
        subset: v2
      weight: 10
```

### 설명

### `hosts`

어떤 서비스의 트래픽을 제어할지 지정한다.

### `route`

트래픽을 어느 목적지로 보낼지 정의한다.

### `subset`

DestinationRule에서 정의한 버전 그룹을 지정한다.

### `weight`

각 버전으로 보낼 비율을 의미한다.

즉, 위 설정은

`frontend`로 들어오는 요청 중

* 90%는 `v1`

* 10%는 `v2`

로 보낸다는 뜻이다.

---

## 12-2. 적용 및 확인

```
kubectl apply -f frontend-virtualservice.yaml
kubectl get virtualservice -n $NAMESPACE
kubectl describe virtualservice frontend -n $NAMESPACE
```

---

## 12-3. Kubernetes rollout과 Service Mesh traffic split은 다르다

* **Kubernetes rollout**  
  새 Pod로 점차 교체하는 방식이다.

* **Service Mesh traffic split**  
  여러 버전이 동시에 존재하는 상태에서 요청 비율을 조정하는 방식이다.

즉, 트래픽 분할은 단순히 Pod를 교체하는 것이 아니라

**사용자 요청의 흐름 자체를 제어**하는 기능이다.

이 차이 때문에 Service Mesh는 카나리 배포, A/B 테스트, 점진 배포에 매우 유리하다.

---

# 13. 실습 8: 지연 장애 주입

이번에는 `recommendationservice`에 지연을 일부러 넣어본다.

즉 **앱을 죽이지 않고도 네트워크 장애를 재현할 수 있다**는 점을 보여주는 것이다. 장애를 재현해 대처방안을 마련할 수 있음.

---

## 13-1. 왜 이 실습이 중요한가

장애를 발생시키려면 보통 다음처럼 진행했다.

* Pod 삭제

* Deployment scale down

* 서비스 중지

하지만 실제 운영 환경에서는

서비스가 완전히 죽는 경우보다 **느려지는 경우**가 훨씬 더 자주 문제를 일으킨다.

예를 들면 다음과 같다.

* 추천 서비스가 응답이 매우 늦어짐

* DB 연결이 느려짐

* 외부 API 호출이 지연됨

이런 상황을 Service Mesh는 정책만으로 시뮬레이션할 수 있다.

---

## 13-2. `recommendation-delay.yaml`

```
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: recommendationservice-delay
  namespace: default
spec:
  hosts:
  - recommendationservice.default.svc.cluster.local
  http:
  - fault:
      delay:
        percentage:
          value: 100
        fixedDelay: 5s
    route:
    - destination:
        host: recommendationservice.default.svc.cluster.local
```

### 설명

### `fault`

정상 요청 흐름에 인위적인 장애 조건을 삽입한다.

### `delay`

장애 유형 중 지연을 의미한다.

### `percentage.value: 100`

전체 요청에 모두 지연을 적용한다.

### `fixedDelay: 5s`

각 요청마다 5초 지연을 강제로 추가한다.

즉, 이 정책은 `recommendationservice`를 죽이는 것이 아니라

**5초 느려지게 만드는 정책**이다.

---

## 13-3. 적용

```
kubectl apply -f recommendation-delay.yaml
```

---

## 13-4. 브라우저에서 확인

브라우저에서 Online Boutique 화면을 새로고침하면서 다음을 관찰한다.

* 추천 영역이 늦게 뜨는가

* 페이지 일부가 느려지는가

* 사용자 경험이 어떻게 달라지는가

즉, Service Mesh는 네트워크 동작 자체를 제어할 수 있다.

장애 주입 후에는 단순히 페이지가 느려졌는지만 보는 것이 아니라, 어떤 기능이 영향을 받는지, 응답 시간이 실제로 증가했는지, 서비스가 완전히 중단된 것인지 아니면 일부 기능만 느려진 것인지를 함께 확인해야 한다. 이를 통해 MSA 환경에서 부분 장애가 전체 사용자 경험에 어떤 영향을 주는지 이해할 수 있다.

---

## 13-5. 원복

```
kubectl delete-f recommendation-delay.yaml
```

---

# 15. 정리

---

## 15-1. 사이드카 주입

Pod 안에 `istio-proxy`가 추가되었고,

서비스 간 통신 제어가 애플리케이션 코드 바깥으로 분리되었다.

---

## 15-2. 트래픽 분할

같은 `frontend` 서비스 안에서도 `v1`, `v2` 버전을 구분할 수 있고,

요청을 90:10처럼 비율로 분배할 수 있다.

즉, Service Mesh는 **버전별 트래픽 제어**를 가능하게 한다.

---

## 15-3. 지연 장애 주입

서비스를 죽이지 않고도 느린 서비스 상황을 재현할 수 있다.

이것은 운영 시뮬레이션과 복원력 테스트에 매우 유용하다.

---

## 15-4. 왜 필요한가

Service Mesh는 복잡한 MSA 운영 환경에서 **트래픽 제어, 보안, 장애 실험, 관측성**을 제공하는 핵심 계층이다.

---

# 16. 실습 원복

---

## 16-1. 트래픽 분할 정책 삭제

```
kubectl delete -f frontend-virtualservice.yaml
kubectl delete -f frontend-destinationrule.yaml
```

---

## 16-2. 지연 주입 정책 삭제

```
kubectl delete -f recommendation-delay.yaml
```

---

## 16-3. 사이드카 자동 주입 라벨 제거

```
kubectl label namespace $NAMESPACE istio-injection-
kubectl get deployments -n $NAMESPACE -o name | xargs-n1 kubectl rollout restart -n $NAMESPACE
```

### 설명

네임스페이스 라벨을 제거한 뒤 Deployment를 다시 재시작해야

새로 생성되는 Pod부터 사이드카가 없는 상태로 돌아간다.

---

## 17-4. 원래 `frontend`로 복구

실습 후 `frontend-v1`, `frontend-v2` 대신 원래 `frontend` Deployment로 복구하려면

백업해둔 YAML을 다시 적용하면 된다.

```
kubectl delete deploy frontend-v1 -n $NAMESPACE
kubectl delete deploy frontend-v2 -n $NAMESPACE

kubectl apply -f frontend-original-backup.yaml
```

---