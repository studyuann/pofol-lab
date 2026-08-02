---
title: "MetalLB + Ingress"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "온프레미스 ICT 인프라구조", "BGP(Border Gateway Protocol)"]
is_public: true
draft: false
---

# MetalLB + Ingress

* **MetalLB**: 외부에서 접근 가능한 VIP를 할당하고 BGP로 광고

* **Ingress Controller**: HTTP/HTTPS 요청을 Host/Path 기준으로 분기

* **Service**: Ingress Controller가 백엔드 애플리케이션으로 연결

* **Pod**: 실제 애플리케이션 실행

---

## 1. 학습 목표

이 교안의 목표는 다음과 같다.

* MetalLB와 Ingress의 역할 차이를 이해함

* 외부 클라이언트가 Kubernetes 서비스에 접속하는 전체 흐름을 이해함

* MetalLB가 VIP를 어떻게 광고하는지 이해함

* Ingress Controller가 HTTP/HTTPS 요청을 어떻게 분기하는지 이해함

* Cisco Router - MetalLB - Ingress Controller - Backend Pod 구조를 실습할 수 있음

---

# 2. 왜 MetalLB와 Ingress를 같이 사용하는가

Kubernetes에서 외부 서비스를 공개하는 방식은 여러 가지가 있다.

대표적으로 다음 3가지가 있다.

* NodePort

* LoadBalancer

* Ingress

이 중에서 실제 운영에서는 보통 다음 구조를 많이 사용한다.

```
MetalLB + Ingress Controller
```

이유는 다음과 같다.

### MetalLB만 사용할 경우

서비스마다 LoadBalancer IP가 하나씩 필요하다.

예를 들어 서비스가 3개라면

* web1 → VIP 1개

* web2 → VIP 1개

* web3 → VIP 1개

즉 외부 IP를 많이 사용하게 된다.

---

### MetalLB + Ingress를 사용할 경우

Ingress Controller 앞에 **VIP 하나만 할당**하고,

그 뒤에서 Host/Path 기준으로 여러 서비스를 분기할 수 있다.

예를 들어

* `app1.example.com` → service1

* `app2.example.com` → service2

* `example.com/shop` → service3

즉 **VIP 하나로 여러 웹 서비스를 운영할 수 있다.**

---

# 3. 전체 구조

## 3.1 논리 구조

```
Client Network
      │
      │
     R1
      │
      │ iBGP
      │
     R2
      │
      │ eBGP
      │
Kubernetes Nodes
      │
      │
MetalLB VIP
      │
      │
Ingress Controller Service (LoadBalancer)
      │
      │
Ingress Controller Pod
      │
 ┌────┴───────────────┐
 │                    │
Service 1          Service 2
 │                    │
Pod 1                Pod 2
```

---

## 3.2 핵심 해석

이 구조를 한 줄로 표현하면 다음과 같다.

```
MetalLB는 외부 진입점(VIP)을 만들고,
Ingress Controller는 그 트래픽을 여러 서비스로 분배한다.
```

즉 역할이 다르다.

| 구성요소 | 역할 |
| --- | --- |
| MetalLB | 외부 접속용 VIP 제공 |
| Router | VIP 경로 라우팅 |
| Ingress Controller | HTTP/HTTPS 분기 |
| Service | Pod 접근용 내부 추상화 |
| Pod | 실제 애플리케이션 실행 |

---

# 4. 역할 구분

## 4.1 MetalLB 역할

MetalLB는 Kubernetes에서 `type: LoadBalancer` 서비스를 사용할 수 있게 해주는 구성요소다.

MetalLB의 핵심 역할은 다음과 같다.

* LoadBalancer IP(VIP) 할당

* VIP를 BGP 또는 L2로 외부 네트워크에 광고

* 외부 라우터가 해당 VIP로 트래픽을 보낼 수 있게 함

중요한 점은 다음이다.

```
MetalLB는 HTTP 라우팅을 하지 않는다.
```

즉 MetalLB는 **L4 수준의 진입점 제공자**라고 이해하면 된다.

---

## 4.2 Ingress Controller 역할

Ingress Controller는 **HTTP/HTTPS 레벨의 요청 분기 장치**다.

예를 들어 다음과 같은 동작을 한다.

* `app1.example.com` 요청은 service1로 전달

* `app2.example.com` 요청은 service2로 전달

* `/api` 요청은 api-service로 전달

* `/shop` 요청은 shop-service로 전달

즉 Ingress Controller는 다음 역할을 한다.

* Host 기반 라우팅

* Path 기반 라우팅

* TLS 종료(HTTPS 인증서 처리)

* 여러 서비스에 대한 단일 진입점 제공

---

## 4.3 Service 역할

Service는 Pod 앞에 위치한 가상 네트워크 객체다.

역할은 다음과 같다.

* Pod 집합을 하나의 네트워크 엔드포인트처럼 제공

* Pod IP가 바뀌어도 안정적인 접근 경로 제공

* kube-proxy를 통해 로드밸런싱 처리

---

# 5. 네트워크 흐름 이해

## 5.1 외부 클라이언트 요청 흐름

예를 들어 클라이언트가 다음 URL로 접속한다고 가정한다.

```
http://app1.example.com
```

DNS 또는 hosts 설정을 통해 다음과 같이 연결된다고 가정한다.

```
app1.example.com → 192.168.90.10
```

여기서 `192.168.90.10` 은 MetalLB가 할당한 VIP다.

---

## 5.2 패킷 흐름

전체 흐름은 다음과 같다.

```
Client
 → R1
 → R2
 → VIP(192.168.90.10)
 → Ingress Controller Service
 → Ingress Controller Pod
 → Service1
 → Pod1
```

즉 단계별로 보면 다음과 같다.

### 1단계

클라이언트는 `app1.example.com` 을 VIP로 해석한다.

### 2단계

VIP에 대한 경로는 BGP를 통해 R1, R2가 알고 있다.

### 3단계

R2는 VIP 트래픽을 Kubernetes Node로 전달한다.

### 4단계

Node에 도착한 트래픽은 Ingress Controller Service로 들어간다.

### 5단계

Ingress Controller는 Host/Path 규칙을 보고 backend service를 선택한다.

### 6단계

선택된 service가 실제 Pod로 트래픽을 전달한다.

---

# 6. 왜 Ingress Controller에도 External IP가 할당되는가

정확히 말하면 다음과 같다.

```
Ingress Controller Pod에 External IP가 할당되는 것이 아니라,
Ingress Controller를 노출하는 Service에 External IP가 할당된다.
```

즉 구조는 다음과 같다.

```
Ingress Controller Pod
        ↑
Ingress Controller Service (type: LoadBalancer)
        ↑
MetalLB가 VIP 할당
```

예를 들어 다음 명령을 보면

```
kubectl get svc -n ingress-nginx
```

다음처럼 보일 수 있다.

```
AME                       TYPE           EXTERNAL-IP
ingress-nginx-controller   LoadBalancer   192.168.90.10
```

여기서 `192.168.90.10` 은 **Ingress Controller Service의 VIP**다.

---

# 7. 실습 환경 구성

## 7.1 네트워크 구조

### Client Network

* Client: `10/24`

* Gateway(R1): `10.1.1.1/24`

### R1 - R2

* R1 g0/1: `172.16.12.1/30`

* R2 g0/0: `172.16.12.2/30`

### R2 - Kubernetes Node Network

* R2 g0/1: `192.168.80.1/24`

* Node1: `192.168.80.121/24`

* Node2: `192.168.80.122/24`

### MetalLB VIP Pool

* `192.168.90.0/24`

### ASN

* R1: `65000`

* R2: `65000`

* MetalLB: `65010`

즉

* R1 ↔ R2 : iBGP

* R2 ↔ MetalLB : eBGP

---

# 8. Cisco Router 설정

## 8.1 R1 설정

```
enable
conf t
hostname R1

interface f0/1
 ip address 192.168.20.253 255.255.255.0
 no shutdown

interface f0/0
 ip address 192.168.12.1 255.255.255.0
 no shutdown

router bgp 65000
 neighbor 192.168.12.2 remote-as 65000

end
write memory
```

---

## 8.2 R2 설정

```
enable
conf t
hostname R2

interface f0/0
 ip address 192.168.12.2 255.255.255.0
 no shutdown

interface f0/1
 ip address 192.168.80.253 255.255.255.0
 no shutdown

router bgp 65000
 neighbor 192.168.12.1 remote-as 65000
 neighbor 192.168.12.1 next-hop-self

 neighbor 192.168.80.120 remote-as 65010
 neighbor 192.168.80.130 remote-as 65010

end
write memory
```

---

## 8.3 next-hop-self 설명

MetalLB는 VIP를 R2에 광고한다.

예를 들어 다음처럼 보일 수 있다.

```
192.168.90.10/32 via 192.168.80.120
192.168.90.10/32 via 192.168.80.130
```

이 경로를 R2가 iBGP로 R1에게 넘기면,

기본적으로 next-hop을 바꾸지 않는다.

그러면 R1은 다음처럼 배운다.

```
192.168.90.10 via 192.168.80.120
```

그런데 R1은 192.168.80.0/24 네트워크에 직접 연결되어 있지 않다.

그래서 이 next-hop은 사용할 수 없다.

따라서 반드시 다음 설정이 필요하다.

```
neighbor 192.168.12.1 next-hop-self
```

그러면 R1은 다음처럼 배운다.

```
192.168.90.10 via 192.168.12.2
```

즉 R1은 R2를 통해 VIP로 갈 수 있게 된다.

---

# 9. MetalLB 설정

## 9.1 IPAddressPool

```
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: bgp-pool
  namespace: metallb-system
spec:
  addresses:
  - 192.168.90.10-192.168.90.20
```

적용

```
kubectl apply -f ip-pool.yaml
```

---

## 9.2 BGPPeer

```
apiVersion: metallb.io/v1beta2
kind: BGPPeer
metadata:
  name: r2-peer
  namespace: metallb-system
spec:
  peerAddress: 192.168.80.253
  peerASN: 65000
  myASN: 65010
```

적용

```
kubectl apply -f bgp-peer.yaml
```

---

## 9.3 BGPAdvertisement

```
apiVersion: metallb.io/v1beta1
kind: BGPAdvertisement
metadata:
  name: bgp-adv
  namespace: metallb-system
spec:
  ipAddressPools:
  - bgp-pool
```

적용

```
kubectl apply -f bgp-adv.yaml
```

---

# 10. Ingress Controller 설치

여기서는 ingress-nginx를 예시로 사용한다.

## 10.1 설치

```
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml
```

---

## 10.2 Service 타입 확인

설치 후 `ingress-nginx-controller` 서비스 타입이 `LoadBalancer` 이어야 한다.

```
kubectl get svc -n ingress-nginx
```

예시

```
NAME                       TYPE           EXTERNAL-IP
ingress-nginx-controller   LoadBalancer   192.168.90.10
```

여기서 `192.168.90.10` 이 VIP다.

즉 MetalLB가 Ingress Controller Service에 VIP를 할당한 것이다.

---

# 11. 테스트용 애플리케이션 배포

## 11.1 app1 배포

```
kubectl create deployment app1 --image=nginx
kubectl expose deployment app1 --port=80 --name=app1-svc
```

---

## 11.2 app2 배포

```
kubectl create deployment app2 --image=httpd
kubectl expose deployment app2 --port=80 --name=app2-svc
```

---

# 12. Ingress 리소스 생성

아래 예시는 Host 기반 라우팅 예시다.

```
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: demo-ingress
spec:
  ingressClassName: nginx
  rules:
  - host: app1.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app1-svc
            port:
              number: 80
  - host: app2.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app2-svc
            port:
              number: 80
```

적용

```
kubectl apply -f ingress.yaml
```

---

# 13. 클라이언트 이름 해석 설정

실습 환경에서는 DNS 대신 hosts 파일을 사용해도 된다.

클라이언트에서 다음처럼 설정한다.

```
192.168.90.10 app1.example.com
192.168.90.10 app2.example.com
```

즉 두 도메인 모두 같은 VIP를 바라보게 한다.

---

# 14. BGP 및 라우팅 확인

## 14.1 R2에서 확인

```
show ip bgp
```

예시

```
192.168.90.10/32 via 192.168.80.120
192.168.90.10/32 via 192.168.80.130
```

---

## 14.2 R1에서 확인

```
show ip bgp
```

예시

```
192.168.90.10/32 via 192.168.12.2
```

---

## 14.3 라우팅 테이블 확인

```
show ip route 192.168.90.10
```

R1에서는 next-hop이 R2로 보이고,

R2에서는 next-hop이 Kubernetes Node로 보이게 된다.

---

# 15. 접속 테스트

클라이언트에서 다음을 실행한다.

```
curl -H "Host: app1.example.com" http://192.168.90.10
curl -H "Host: app2.example.com" http://192.168.90.10
```

또는 브라우저에서 hosts 파일 설정 후 접속해도 된다.

* `http://app1.example.com`

* `http://app2.example.com`

---

# 16. 전체 트래픽 흐름

## app1.example.com 요청

```
Client
 → R1
 → R2
 → VIP(192.168.90.10)
 → ingress-nginx-controller Service
 → ingress-nginx-controller Pod
 → app1-svc
 → app1 Pod
```

---

## app2.example.com 요청

```
Client
 → R1
 → R2
 → VIP(192.168.90.10)
 → ingress-nginx-controller Service
 → ingress-nginx-controller Pod
 → app2-svc
 → app2 Pod
```

---

# 17. MetalLB와 Ingress의 차이 정리

이 부분은 반드시 따로 정리해주는 것이 좋다.

| 항목 | MetalLB | Ingress Controller |
| --- | --- | --- |
| 역할 | 외부 IP 제공 | HTTP/HTTPS 요청 분기 |
| 동작 계층 | L4 중심 | L7 중심 |
| 처리 기준 | IP, TCP/UDP | Host, Path, TLS |
| 결과 | VIP 생성 | 여러 서비스 분기 |

핵심은 다음 한 문장이다.

```
MetalLB는 들어오는 문을 만들고,
Ingress는 들어온 요청을 어느 방으로 보낼지 결정한다.
```

---

# 18. 자주 헷갈리는 포인트

## 18.1 Ingress에 external-ip가 할당되는가

정확히는 다음과 같다.

```
Ingress 객체 자체에 할당되는 것이 아니라,
Ingress Controller Service에 external-ip가 할당된다.
```

---

## 18.2 MetalLB가 HTTP 라우팅을 하는가

아니다.

MetalLB는 VIP를 할당하고 광고만 한다.

HTTP 요청을 `app1`, `app2`로 분기하는 것은 Ingress Controller가 처리한다.

---

## 18.3 Pod 네트워크를 라우터가 알아야 하는가

일반적인 MetalLB + Ingress 구조에서는

라우터가 Pod 네트워크를 직접 알 필요가 없는 경우가 많다.

라우터는 보통 다음까지만 알면 된다.

```
VIP → Node
```

Node 내부에서 kube-proxy와 Ingress Controller가 backend Pod로 전달한다.

---

# 19. 실습 문제

## 문제 1

`app3.example.com` 을 추가하여 세 번째 서비스까지 연결한다.

---

## 문제 2

Ingress의 Host 기반 라우팅 대신 Path 기반 라우팅으로 변경한다.

예

* `/app1` → app1-svc

* `/app2` → app2-svc

---

## 문제 3

Ingress Controller Service의 VIP가 라우터에 어떻게 보이는지 R1, R2에서 각각 확인한다.

명령어

```
show ip bgp
show ip route
```

---

## 문제 4

R2에서 `maximum-paths 2` 를 적용하고 VIP에 대한 ECMP 동작 여부를 확인한다.

---

# 20. 최종 정리

이번 구조를 한 문장으로 정리하면 다음과 같다.

```
MetalLB는 외부에서 접근 가능한 VIP를 만들고,
Ingress Controller는 그 VIP로 들어온 HTTP/HTTPS 요청을
적절한 Kubernetes 서비스로 분기한다.
```

즉 전체 흐름은 다음과 같다.

```
Client
 → Router
 → Router
 → VIP
 → Ingress Controller
 → Service
 → Pod
```

운영 관점에서 보면 다음처럼 기억하면 된다.

* **MetalLB = 외부 진입점 제공**

* **Ingress = 웹 트래픽 분기**

* **Service = Pod 연결**

* **Pod = 실제 애플리케이션**

---