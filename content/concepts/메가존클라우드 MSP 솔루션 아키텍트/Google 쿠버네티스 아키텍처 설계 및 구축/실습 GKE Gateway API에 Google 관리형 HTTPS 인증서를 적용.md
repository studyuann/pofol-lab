---
title: "실습 GKE Gateway API에 Google 관리형 HTTPS 인증서를 적용"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Google 쿠버네티스 아키텍처 설계 및 구축"]
is_public: true
draft: false
---

# **실습. GKE Gateway API에 Google 관리형 HTTPS 인증서를 적용**

---

# 1. 실습 목표

이 실습에서는 다음을 수행한다.

* Route 53에서 관리 중인 `이니셜.cloudai.store` 도메인을 사용한다.

* `www.이니셜.cloudai.store` 이름으로 Google 관리형 인증서를 발급한다.

* GKE Gateway API에 Certificate Manager 인증서를 연결한다.

* Route 53에서 `www` A 레코드를 Gateway 외부 IP로 연결한다.

* 최종적으로 `https://www.이니셜.cloudai.store` 로 접속해 HTTPS가 정상 동작하는지 확인한다.

---

# 2. 실습에 사용할 기준 값

실습 중 아래 값을 예시로 사용한다.

```
GCP 프로젝트 ID: my-gcp-project
GKE 클러스터 이름: 이니셜-std-cluster-1
GKE 리전: asia-northeast3-c
호스팅 영역 도메인: abc.cloudai.store
실제 접속 도메인: www.abc.cloudai.store
DNS Authorization 이름: my-dns-auth
인증서 이름: my-gke-cert
Certificate Map 이름: my-gke-cert-map
Map Entry 이름: my-cert-map-entry
Gateway 이름: my-gateway
HTTPRoute 이름: hello-route
Service 이름: hello-service
```

여기서 `abc` 부분은 본인 이니셜로 바꾸면 된다.

예를 들어 이니셜이 `kyt` 라면:

```
호스팅 영역 도메인: kyt.cloudai.store
실제 접속 도메인: www.kyt.cloudai.store
```

---

# 3. 실습 전 확인 사항

GKE Gateway를 사용하려면 Gateway API가 활성화되어 있어야 하고, GatewayClass가 생성되어 있어야 한다. GKE 문서 기준으로 Gateway API를 사용하는 클러스터는 VPC-native여야 하며, Gateway 배포 후 `gke-l7-global-external-managed` 같은 GatewayClass를 사용할 수 있다. 또한 Gateway 상태 확인 시 `Programmed=True` 조건이 중요하다.

GatewayClass 확인:

```
kubectl get gatewayclass
```

예상 예시:

```
NAME                               CONTROLLER
gke-l7-global-external-managed     networking.gke.io/gateway
gke-l7-regional-external-managed   networking.gke.io/gateway
```

---

# 4. 전체 실습 흐름

1. `www.이니셜.cloudai.store` 에 대한 DNS Authorization 생성

2. Route 53에 검증용 CNAME 등록

3. `www.이니셜.cloudai.store` 이름으로 Google 관리형 인증서 생성

4. Certificate Map / Map Entry 생성

5. 샘플 애플리케이션 배포

6. Gateway / HTTPRoute 배포

7. Gateway 외부 IP 확인

8. Route 53에 `www` A 레코드 등록

9. HTTPS 접속 확인

10. 리소스 삭제

Certificate Manager의 DNS Authorization은 도메인별로 생성되며, 그 결과로 나온 `dnsResourceRecord.name` 과 `dnsResourceRecord.data` 값을 DNS에 등록해야 인증서 발급이 진행된다. GKE Gateway에서 Certificate Manager를 사용할 때는 Gateway annotation에 certmap을 연결한다. ([Google Cloud Documentation](https://docs.cloud.google.com/kubernetes-engine/docs/how-to/secure-gateway?utm_source=chatgpt.com))

---

# 5. 1단계 - DNS Authorization 생성

이번 실습에서는 인증서를 `www.이니셜.cloudai.store` 로 발급할 것이므로 DNS Authorization도 그 이름 기준으로 생성한다.

예를 들어 이니셜이 `kyt` 라면:

```
gcloud certificate-manager dns-authorizations create my-dns-auth \
  --domain="www.kyt.cloudai.store"
```

이 명령은 Google이 DNS를 통해 도메인 소유권을 검증할 수 있도록 Authorization 리소스를 만든다. DNS Authorization은 Google-managed certificate의 발급과 갱신에 사용된다.

생성 후 상세 정보를 확인한다.

```
gcloud certificate-manager dns-authorizations describe my-dns-auth
```

예상 출력 예시:

```
dnsResourceRecord:
  name: _acme-challenge.www.kyt.cloudai.store.
  type: CNAME
  data: 12345678-aaaa-bbbb-cccc-1234567890ab.4.authorize.certificatemanager.goog.
domain: www.kyt.cloudai.store
```

여기서 반드시 메모할 값은 아래 3개다.

```
name
type
data
```

즉 예시 기준으로는 다음과 같다.

```
name: _acme-challenge.www.kyt.cloudai.store.
type: CNAME
data: 12345678-aaaa-bbbb-cccc-1234567890ab.4.authorize.certificatemanager.goog.
```

---

# 6. 2단계 - Route 53에 검증용 CNAME 등록

현재 Route 53 호스팅 영역은 `kyt.cloudai.store` 라고 가정한다.

즉, Route 53의 레코드 이름 입력칸 오른쪽에 `kyt.cloudai.store` 가 보이는 상태라면, 왼쪽 입력칸에는 **앞부분만** 넣으면 된다.

지금 검증 대상은:

```
www.kyt.cloudai.store
```

이고, Authorization 결과의 `name` 이:

```
_acme-challenge.www.kyt.cloudai.store.
```

이므로 Route 53에서는 아래처럼 넣는다.

## Route 53 입력값

* 레코드 이름: `_acme-challenge.www`

* 레코드 유형: `CNAME`

* 값: `12345678-aaaa-bbbb-cccc-1234567890ab.4.authorize.certificatemanager.goog`

이렇게 입력하면 Route 53은 최종적으로 다음 FQDN으로 해석한다.

```
_acme-challenge.www.kyt.cloudai.store
```

이 값이 바로 Google이 도메인 검증에 사용하는 레코드다.

DNS 반영 여부를 확인한다.

```
dig CNAME _acme-challenge.www.kyt.cloudai.store
```

정상이라면 `ANSWER SECTION` 에 `authorize.certificatemanager.goog` 값이 보여야 한다.

---

# 7. 3단계 - Google 관리형 인증서 생성

DNS Authorization이 준비되었으면 `www.kyt.cloudai.store` 이름으로 인증서를 생성한다.

```
gcloud certificate-manager certificates create my-gke-cert \
  --domains="www.kyt.cloudai.store" \
  --dns-authorizations="my-dns-auth"
```

이 명령은 `www.kyt.cloudai.store` 이름을 SAN으로 포함하는 Google-managed certificate를 생성한다. 인증서는 DNS Authorization이 정상 검증되면 발급되고, 이후에도 자동 갱신에 같은 Authorization이 사용된다.

인증서 상태를 확인한다.

```
gcloud certificate-manager certificates describe my-gke-cert
```

주요 확인 포인트:

* `managed.status`

* `sanDnsnames`

* `authorizationAttemptInfo`

발급 직후에는 `PROVISIONING` 상태가 나올 수 있다.

DNS 전파와 검증이 끝나면 활성 상태로 바뀐다.

반복 확인하려면:

```
watch -n 10 'gcloud certificate-manager certificates describe my-gke-cert --format="yaml(name,managed.status,sanDnsnames)"'
```

---

# 8. 4단계 - Certificate Map 및 Map Entry 생성

GKE Gateway에서 Certificate Manager 인증서를 사용할 때는 일반적으로 Certificate Map을 만들고, Gateway metadata annotation `networking.gke.io/certmap` 으로 연결한다.

먼저 Certificate Map을 생성한다.

```
gcloud certificate-manager maps create my-gke-cert-map
```

다음으로 Map Entry를 만든다.

```
gcloud certificate-manager maps entries create my-cert-map-entry \
  --map="my-gke-cert-map" \
  --certificates="my-gke-cert" \
  --hostname="www.kyt.cloudai.store"
```

여기서 `--hostname` 값은 매우 중요하다.

실제 접속할 도메인과 동일해야 한다.

```
www.kyt.cloudai.store
```

로 맞춰야 한다.

확인:

```
gcloud certificate-manager maps describe my-gke-cert-map

gcloud certificate-manager maps entries describe my-cert-map-entry \
  --map="my-gke-cert-map"
```

---

# 9. 5단계 - 샘플 애플리케이션 배포

실습용 애플리케이션을 먼저 배포한다.

## app.yaml

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hello-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: hello
  template:
    metadata:
      labels:
        app: hello
    spec:
      containers:
      - name: hello-app
        image: us-docker.pkg.dev/google-samples/containers/gke/hello-app:1.0
        ports:
        - containerPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: hello-service
spec:
  type: ClusterIP
  selector:
    app: hello
  ports:
  - port: 80
    targetPort: 8080
```

적용:

```
kubectl apply -f app.yaml
```

확인:

```
kubectl get deploy
kubectl get pods
kubectl get svc
```

이 Service는 Gateway가 backend로 참조할 대상이다. GKE Gateway 배포 흐름에서도 Gateway/Route는 Service를 backendRef로 연결한다.

---

# 10. 6단계 - Gateway 및 HTTPRoute 배포

이번 실습에서 Gateway는 `www.kyt.cloudai.store` 에 대한 HTTPS 리스너를 가진다.

그리고 Certificate Map을 annotation으로 연결한다.

GKE Gateway에서 Certificate Manager를 사용할 때는 `networking.gke.io/certmap` annotation을 사용한다. GKE Gateway는 `gke-l7-global-external-managed` GatewayClass로 글로벌 외부 Application Load Balancer를 만든다.

## gateway.yaml

```
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: my-gateway
  annotations:
    networking.gke.io/certmap: my-gke-cert-map
spec:
  gatewayClassName: gke-l7-global-external-managed
  listeners:
  - name: https
    protocol: HTTPS
    port: 443
    hostname: www.kyt.cloudai.store
    allowedRoutes:
      namespaces:
        from: Same
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: hello-route
spec:
  parentRefs:
  - name: my-gateway
  hostnames:
  - www.kyt.cloudai.store
  rules:
  - backendRefs:
    - name: hello-service
      port: 80
```

### 핵심 설명

이번 파일에서 반드시 동일해야 하는 값은 아래 3개다.

```
Gateway listener hostname
HTTPRoute hostnames
Certificate Map Entry hostname
```

즉 전부 아래처럼 맞아야 한다.

```
www.kyt.cloudai.store
```

적용:

```
kubectl apply -f gateway.yaml
```

확인:

```
kubectl get gateway
kubectl describe gateway my-gateway
kubectl get httproute
kubectl describe httproute hello-route
```

Gateway는 `Programmed=True` 상태가 되면 외부 부하분산기가 준비된 것으로 본다.

---

# 11. 7단계 - Gateway 외부 IP 확인

아래 명령으로 Gateway 외부 IP를 확인한다.

```
kubectl get gateway my-gateway
```

예상 예시:

```
NAME         CLASS                              ADDRESS         PROGRAMMED   AGE
my-gateway   gke-l7-global-external-managed    34.111.22.33    True         6m
```

여기서 `ADDRESS` 값이 Route 53에 넣을 최종 A 레코드 대상이다.

---

# 12. 8단계 - Route 53에 최종 A 레코드 등록

이번 실습의 실제 접속 도메인은:

```
www.kyt.cloudai.store
```

호스팅 영역은:

```
kyt.cloudai.store
```

이므로 Route 53에서는 아래처럼 입력한다.

## Route 53 입력값

* 레코드 이름: `www`

* 레코드 유형: `A`

* 값: Gateway 외부 IP

예를 들어 Gateway IP가 `34.111.22.33` 이라면:

* 레코드 이름: `www`

* 레코드 유형: `A`

* 값: `34.111.22.33`

이렇게 넣으면 최종 레코드 이름은:

```
www.kyt.cloudai.store
```

가 된다.

확인:

```
dig www.kyt.cloudai.store
```

정상이라면 Gateway 외부 IP가 조회된다.

---

# 13. 9단계 - HTTPS 접속 확인

브라우저에서 아래 주소로 접속한다.

```
https://www.kyt.cloudai.store
```

정상이라면:

* 주소창에 자물쇠가 표시됨

* 인증서 이름이 `www.kyt.cloudai.store` 로 보임

* hello-app 응답이 표시됨

CLI 확인:

```
curl -I https://www.kyt.cloudai.store
```

좀 더 자세히 보려면:

```
curl -v https://www.kyt.cloudai.store
```

---

# 14. 실습용 전체 명령어 모음

아래 순서대로 실행하면 된다.

```
# 프로젝트 설정
gcloud config set project my-gcp-project

# API 활성화
gcloud services enable \
  container.googleapis.com \
  certificatemanager.googleapis.com \
  compute.googleapis.com \
  networkservices.googleapis.com

# 클러스터 연결
gcloud container clusters get-credentials my-gke-cluster \
  --location=asia-northeast3

# 기존 클러스터라면 Gateway API 활성화
gcloud container clusters update my-gke-cluster \
  --location=asia-northeast3 \
  --gateway-api=standard

# GatewayClass 확인
kubectl get gatewayclass

# DNS Authorization 생성
gcloud certificate-manager dns-authorizations create my-dns-auth \
  --domain="www.kyt.cloudai.store"

# DNS Authorization 확인
gcloud certificate-manager dns-authorizations describe my-dns-auth

# 인증서 생성
gcloud certificate-manager certificates create my-gke-cert \
  --domains="www.kyt.cloudai.store" \
  --dns-authorizations="my-dns-auth"

# 인증서 상태 확인
gcloud certificate-manager certificates describe my-gke-cert

# Certificate Map 생성
gcloud certificate-manager maps create my-gke-cert-map

# Map Entry 생성
gcloud certificate-manager maps entries create my-cert-map-entry \
  --map="my-gke-cert-map" \
  --certificates="my-gke-cert" \
  --hostname="www.kyt.cloudai.store"

# 앱 배포
kubectl apply -f app.yaml

# Gateway 배포
kubectl apply -f gateway.yaml

# Gateway 상태 확인
kubectl get gateway
kubectl describe gateway my-gateway

# HTTPRoute 확인
kubectl get httproute
kubectl describe httproute hello-route
```

---

# 15. Route 53에 실제로 넣는 값 정리

이번 실습 기준에서 Route 53에 넣는 값은 딱 두 종류다.

## 1) 인증서 검증용 CNAME

GCP 출력값이 예를 들어 이렇게 나왔다고 가정한다.

```
name: _acme-challenge.www.kyt.cloudai.store.
data: 12345678-aaaa-bbbb-cccc-1234567890ab.4.authorize.certificatemanager.goog.
```

Route 53 입력:

* 레코드 이름: `_acme-challenge.www`

* 레코드 유형: `CNAME`

* 값: `12345678-aaaa-bbbb-cccc-1234567890ab.4.authorize.certificatemanager.goog`

## 2) 실제 서비스용 A 레코드

Gateway IP가 예를 들어 `34.111.22.33` 이라면 Route 53 입력:

* 레코드 이름: `www`

* 레코드 유형: `A`

* 값: `34.111.22.33`

---

# 16. 자주 헷갈리는 부분

## `kyt.cloudai.store` 와 `www.kyt.cloudai.store` 는 다르다

이 둘은 서로 다른 이름이다.

이번 실습에서는 인증서를 루트 도메인이 아니라 `www.kyt.cloudai.store` 로 발급받는다.

즉 아래 값들은 모두 같은 이름으로 통일해야 한다.

```
DNS Authorization domain
Certificate domain
Certificate Map Entry hostname
Gateway listener hostname
HTTPRoute hostname
Route 53 A record 이름
```

이번 실습에서는 전부 최종적으로 아래를 가리키게 된다.

```
www.kyt.cloudai.store
```

---

# 17. 삭제 순서

비용 방지를 위해 실습 종료 후 아래 순서대로 삭제한다.

```
kubectl delete -f gateway.yaml
kubectl delete -f app.yaml

gcloud certificate-manager maps entries delete my-cert-map-entry \
  --map="my-gke-cert-map"

gcloud certificate-manager maps delete my-gke-cert-map

gcloud certificate-manager certificates delete my-gke-cert

gcloud certificate-manager dns-authorizations delete my-dns-auth
```

Route 53에서도 아래 레코드를 삭제한다.

* `_acme-challenge.www` CNAME

* `www` A 레코드

---