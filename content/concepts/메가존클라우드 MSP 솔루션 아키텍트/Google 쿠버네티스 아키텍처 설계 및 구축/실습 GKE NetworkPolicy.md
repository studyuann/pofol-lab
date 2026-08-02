---
title: "실습 GKE NetworkPolicy"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Google 쿠버네티스 아키텍처 설계 및 구축"]
is_public: true
draft: false
---

# 실습. GKE NetworkPolicy

## 1. 실습 목표

GKE 클러스터에서 **Kubernetes NetworkPolicy**를 이용해 Pod 간 통신을 제어하는 방법을 확인한다. Kubernetes의 NetworkPolicy는 **IP와 포트 수준에서 Pod 트래픽 흐름을 제어하는 리소스**이며, 이를 통해 특정 Pod만 접근 허용하거나 특정 방향의 통신만 허용할 수 있다.

* Autopilot 클러스터를 생성할 수 있음

* 기본 상태에서 Pod 간 통신이 가능한지 확인할 수 있음

* 특정 Pod에 대해 ingress 기본 차단 정책을 적용할 수 있음

* 특정 라벨을 가진 Pod만 접근 허용하도록 구성할 수 있음

* ingress와 egress 정책 차이를 이해할 수 있음

---

## 2. NetworkPolicy란

NetworkPolicy는 **Pod 단위의 네트워크 접근제어 정책**이다.

이 정책은 **어떤 Pod가 어떤 Pod와 통신 가능한지**를 IP/포트 레벨에서 제어한다. 다만 NetworkPolicy API가 있다고 해서 무조건 동작하는 것은 아니고, 실제 네트워크 플러그인이 정책 enforcement를 지원해야 한다. GKE는 이 enforcement를 지원한다.

중요한 점은 다음과 같다.

* 기본적으로 Pod 간 통신은 허용되는 상태임

* NetworkPolicy가 적용되면 **정책 대상 Pod가 격리됨**

* `Ingress`는 **들어오는 트래픽**

* `Egress`는 **나가는 트래픽**

* 정책은 “허용 목록” 중심으로 생각하는 것이 이해하기 쉬움

즉, 어떤 Pod에 정책이 적용되면 그 Pod는 이제 “아무나 접근 가능한 상태”가 아니라, **정책에서 허용한 대상만 접근 가능한 상태**가 됨.

* Autopilot 모드에서는 기본적으로 활성화되며, Standard 모드에서는 클러스터 생성시 활성화해야 사용가능함.

---

## 3. 실습 시나리오

실습에서는 Autopilot 모드 클러스터를 사용함.

1. Autopilot 클러스터 생성

2. `np-demo` 네임스페이스 생성

3. `server` Pod 생성

4. `client-allowed`, `client-blocked` Pod 생성

5. 정책 적용 전 두 Pod 모두 `server` 접속 가능 여부 확인

6. `server`에 대해 기본 차단 정책 적용

7. 두 client 모두 차단되는지 확인

8. `client-allowed`만 허용하는 정책 적용

9. 허용/차단 결과 비교 확인

10. egress 정책 예시 확인

---

## 4. 실습 환경 준비

### 4-1. 환경 변수 설정

```
export PROJECT_ID=$(gcloud config get-value project)
export REGION=asia-northeast3
export CLUSTER_NAME=np-autopilot-cluster
export VPCNETWORK=kdtmsp-vpc
export GKESUBNET=auto-subnet
```

명령 설명:

* PROJECT\_ID는 현재 설정된 GCP 프로젝트 ID를 자동으로 가져옴

* REGION은 클러스터 생성 리전임

* CLUSTER\_NAME은 생성할 클러스터 이름임

* VPCNETWORK는 cluster를 생성할 VPC네트워크임

* GKESUBNET은 클러스터가 생성될 서브넷임. (이때 서브넷에 파드가 생성될 secondary range 가 필요함. 서비스는 생성하지 않아도 됨.)

확인:

```
echo $PROJECT_ID
echo $REGION
echo $CLUSTER_NAME
echo $VPCNETWORK
echo $GKESUBNET
```

---

### 4-2. Autopilot 클러스터 생성

```
gcloud container clusters create-auto $CLUSTER_NAME \
  --region $REGION \
  --network $VPCNETWORK \
  --subnetwork $GKESUBNET
```

이 명령은 **Autopilot 클러스터를 생성하는 명령**이다.

클러스터 확인:

```
gcloud container clusters list
```

---

### 4-3. kubectl 인증 정보 가져오기

```
gcloud container clusters get-credentials $CLUSTER_NAME --region $REGION
```

명령 설명:

* 이 명령을 실행하면 현재 PC의 kubeconfig에 GKE 접속 정보가 등록됨

* 이후 `kubectl` 명령으로 클러스터 리소스를 조회하고 생성할 수 있게 됨

노드 확인:

```
kubectl get nodes
```

Autopilot이어도 내부적으로 워크로드가 올라갈 노드는 존재하므로 `kubectl get nodes` 결과가 보임.

다만, 파드가 없으면 노드가 보이지 않을 수 있음.

---

## 5. 네임스페이스와 테스트 Pod 생성

### 5-1. 네임스페이스 생성

```
kubectl create namespace np-demo
```

확인:

```
kubectl get ns
```

---

### 5-2. server Pod 생성

아래 내용을 `server.yaml` 파일로 저장한다.

```
apiVersion: v1
kind: Pod
metadata:
  name: server
  namespace: np-demo
  labels:
    app: server
spec:
  containers:
  - name: nginx
    image: nginx:1.25
    ports:
    - containerPort: 80
```

적용:

```
kubectl apply -f server.yaml
```

설명:

* `labels.app: server`

  이 Pod를 NetworkPolicy의 대상으로 선택할 때 사용함

* `image: nginx:1.25`

  HTTP 요청을 받을 테스트 서버 이미지임

* `containerPort: 80`

  컨테이너가 80번 포트로 요청을 받는다는 의미임

---

### 5-3. client Pod 2개 생성

아래 내용을 `clients.yaml`로 저장한다.

```
apiVersion: v1
kind: Pod
metadata:
  name: client-allowed
  namespace: np-demo
  labels:
    app: client
    access: allowed
spec:
  containers:
  - name: client
    image: curlimages/curl:8.7.1
    command: ["sleep", "3600"]

---
apiVersion: v1
kind: Pod
metadata:
  name: client-blocked
  namespace: np-demo
  labels:
    app: client
    access: blocked
spec:
  containers:
  - name: client
    image: curlimages/curl:8.7.1
    command: ["sleep", "3600"]
```

적용:

```
kubectl apply -f clients.yaml
```

설명:

* `curlimages/curl` 이미지는 `curl` 명령이 포함된 테스트용 컨테이너 이미지임

* `sleep 3600`은 컨테이너가 바로 종료되지 않도록 유지하는 용도임

* 두 Pod의 핵심 차이는 라벨이다
  + `client-allowed` → `access=allowed`
  + `client-blocked` → `access=blocked`

상태 확인:

```
kubectl get pods -n np-demo -o wide
```

---

## 6. 정책 적용 전 통신 확인

Kubernetes에서는 일반적으로 정책 적용 전 Pod 간 통신이 허용된다.

### 6-1. server Pod IP 확인

```
kubectl get pod server -n np-demo -o wide
```

또는 변수 저장:

```
export SERVER_IP=$(kubectl get pod server -n np-demo -o jsonpath='{.status.podIP}')
echo $SERVER_IP
```

명령 설명:

* `jsonpath`는 Kubernetes 리소스의 특정 필드만 추출할 때 사용함

* `{.status.podIP}`는 현재 Pod IP를 의미함

---

### 6-2. client-allowed에서 접속

```
kubectl exec -n np-demo client-allowed -- curl -I --max-time 3 http://$SERVER_IP
```

예상 결과:

```
HTTP/1.1 200 OK
```

---

### 6-3. client-blocked에서 접속

```
kubectl exec -n np-demo client-blocked -- curl -I --max-time 3 http://$SERVER_IP
```

예상 결과:

```
HTTP/1.1 200 OK
```

현재는 아무 정책도 없으므로 둘 다 접속 가능해야 정상이다.

---

## 7. server Pod에 대한 기본 차단 정책 적용

이제 `server` Pod로 들어오는 ingress를 전부 차단한다.

### 7-1. 정책 파일 작성

아래 내용을 `deny-all-ingress-to-server.yaml`로 저장한다.

```
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress-to-server
  namespace: np-demo
spec:
  podSelector:
    matchLabels:
      app: server
  policyTypes:
  - Ingress
```

적용:

```
kubectl apply -f deny-all-ingress-to-server.yaml
```

---

### 7-2. YAML 해설

### `podSelector`

```
podSelector:
  matchLabels:
    app: server
```

이 정책은 `app=server` 라벨을 가진 Pod에만 적용된다.

즉, `server` Pod가 격리 대상이 됨.

### `policyTypes`

```
policyTypes:
- Ingress
```

이 정책은 ingress, 즉 **들어오는 트래픽**에 대해서만 적용됨.

중요한 점은 이 정책에 `ingress:` 허용 규칙이 없다는 것이다.

따라서 결과적으로는 **server Pod로 들어오는 모든 ingress가 차단됨**.

---

### 7-3. 차단 확인

```
kubectl exec -n np-demo client-allowed -- curl -I --max-time 3 http://$SERVER_IP
```

```
kubectl exec -n np-demo client-blocked -- curl -I --max-time 3 http://$SERVER_IP
```

예상 결과:

* 둘 다 timeout 또는 연결 실패가 발생함

이 상태는 정상이다.

이제 `server` Pod는 ingress 측면에서 완전히 격리된 상태다.

정책 확인:

```
kubectl get networkpolicy -n np-demo
kubectl describe networkpolicy deny-all-ingress-to-server -n np-demo
```

---

## 8. 특정 Pod만 허용하는 정책 적용

이제 `client-allowed`만 `server`에 접근할 수 있도록 허용한다.

### 8-1. 허용 정책 파일 작성

아래 내용을 `allow-client-allowed-to-server.yaml`로 저장한다.

```
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-client-allowed-to-server
  namespace: np-demo
spec:
  podSelector:
    matchLabels:
      app: server
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          access: allowed
    ports:
    - protocol: TCP
      port: 80
```

적용:

```
kubectl apply -f allow-client-allowed-to-server.yaml
```

---

### 8-2. YAML 해설

### `podSelector`

```
podSelector:
  matchLabels:
    app: server
```

이 정책도 `server` Pod에 적용됨.

### `ingress.from.podSelector`

```
from:
- podSelector:
    matchLabels:
      access: allowed
```

`access=allowed` 라벨을 가진 Pod만 `server`에 접근 가능하다는 의미다.

### `ports`

```
ports:
- protocol: TCP
  port: 80
```

허용되는 포트는 TCP 80번이다.

즉, `allowed` 라벨이 붙은 Pod라도 80번 포트 외의 다른 포트 접근은 이 규칙으로 허용되지 않음.

Kubernetes NetworkPolicy는 허용 규칙을 조합해 동작하며, 적용된 Pod에 대해서는 허용된 트래픽만 통과시키는 방식으로 이해하면 된다.

---

### 8-3. 허용/차단 결과 확인

### 허용 Pod 테스트

```
kubectl exec -n np-demo client-allowed -- curl -I --max-time 3 http://$SERVER_IP
```

예상 결과:

```
HTTP/1.1 200 OK
```

### 차단 Pod 테스트

```
kubectl exec -n np-demo client-blocked -- curl -I --max-time 3 http://$SERVER_IP
```

예상 결과:

* timeout 또는 연결 실패

즉, 이제는 다음과 같은 상태가 됨.

* `client-allowed` → 접근 가능

* `client-blocked` → 접근 불가

---

## 9. egress 정책 추가 실습

지금까지는 `server`로 들어오는 ingress를 제어했음.

이번에는 `client-blocked` Pod가 **밖으로 나가는 통신**을 제한하는 egress 예시를 본다.

### 9-1. egress 차단 정책 작성

아래 내용을 `deny-egress-client-blocked.yaml`로 저장한다.

```
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-egress-client-blocked
  namespace: np-demo
spec:
  podSelector:
    matchLabels:
      access: blocked
  policyTypes:
  - Egress
```

적용:

```
kubectl apply -f deny-egress-client-blocked.yaml
```

설명:

* `access=blocked` 라벨을 가진 Pod에 적용됨

* `policyTypes: Egress` 이므로 나가는 통신을 제어함

* 허용 규칙이 없으므로 해당 Pod의 egress가 기본 차단됨

---

### 9-2. egress 차단 확인

`client-blocked`에서 외부 접속을 시도한다.

```
kubectl exec -n np-demo client-blocked -- curl -I --max-time 5 https://example.com
```

예상 결과:

* 실패하거나 timeout이 발생할 수 있음

반면 `client-allowed`는 egress 정책 대상이 아니므로 다음 테스트는 성공함.

```
kubectl exec -n np-demo client-allowed -- curl -I --max-time 5 https://example.com
```

---

## 10. 현재 적용된 정책 전체 확인

```
kubectl get networkpolicy -n np-demo
```

상세 확인:

```
kubectl describe networkpolicy -n np-demo
```

이 명령을 통해 다음을 확인하면 된다.

* 어떤 Pod가 정책 대상으로 선택됐는지

* ingress인지 egress인지

* 어떤 라벨의 Pod가 허용됐는지

* 어떤 포트가 허용됐는지

---

## 11. 정리

### 11-1. 정책이 없을 때

모든 Pod가 자유롭게 통신 가능했음

### 11-2. ingress 기본 차단 후

`server` Pod로 들어오는 모든 트래픽이 차단됐음

### 11-3. 특정 라벨 허용 후

`access=allowed` 라벨을 가진 Pod만 `server`의 80번 포트로 접근 가능했음

### 11-4. egress 차단 후

`client-blocked` Pod의 외부 통신이 제한됐음

---

## 12. Autopilot 실습 시 주의사항

### 12-1. 노드 직접 관리 개념은 약함

Autopilot은 워크로드 중심 운영 모드다.

따라서 “노드 생성/노드풀 설정”보다 “배포 manifest와 정책 적용”에 초점을 두면 됨.

### 12-2. 보안 제한이 더 강함

Autopilot은 기본 보안 정책이 더 강하게 적용된다. 따라서 일부 privileged 워크로드나 특정 host-level 설정은 Standard보다 제약이 있을 수 있다. 하지만 일반적인 nginx, curl, NetworkPolicy 실습은 큰 문제 없이 가능하다.

### 12-3. VPC-native는 기본

Autopilot은 VPC-native 네트워킹이 기본이며 별도 해제 불가다. 즉, Pod/Service 네트워크 구조가 GKE 권장 방식에 맞춰 기본 제공된다고 보면 됨.

---

## 13. 정리 명령

실습 종료 후 리소스를 삭제한다.

### 13-1. 네임스페이스 삭제

```
kubectl delete namespace np-demo
```

### 13-2. 클러스터 삭제

```
gcloud container clusters delete $CLUSTER_NAME --region $REGION
```

삭제 확인 메시지가 나오면 `y` 입력하면 된다.

---

## 14. 추가 실습 과제

### 과제 1

`client-blocked`도 허용하되, 80번 포트만 허용되도록 수정해보기

### 과제 2

`server` Pod를 2개로 늘리고, `app=server` 라벨 전체에 동일 정책이 적용되는지 확인해보기

### 과제 3

별도 `db` Pod를 만들고, `server`만 `db`로 접근 가능하도록 egress/ingress 조합 정책 작성해보기

### 과제 4

`namespaceSelector`를 활용해서 특정 네임스페이스의 Pod만 접근 가능하도록 바꿔보기

---