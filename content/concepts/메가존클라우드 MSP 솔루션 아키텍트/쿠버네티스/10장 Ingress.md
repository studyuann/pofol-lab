---
title: "10장 Ingress"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "쿠버네티스"]
is_public: true
draft: false
---

# 10장. Ingress

## 1. Ingress 개요

### 1.1 Ingress가 필요한 이유

Service만으로 외부 공개를 하면 다음 한계가 있다.

1. **NodePort**

* 노드 IP + 고정 포트로 접근한다.

* 포트가 30000~32767 범위로 강제된다.

* 서비스가 늘어나면 포트 관리가 복잡해진다.

* 도메인 기반 분기(Host)나 URL 경로 기반 분기(Path)를 직접 처리하기 어렵다.

2. **LoadBalancer**

* 클라우드에서는 Service를 LoadBalancer로 만들면 외부 로드밸런서가 자동 생성되고 IP가 붙는다.

* 하지만 서비스마다 LoadBalancer를 만들면 외부 IP/로드밸런서가 여러 개 필요해진다.

* 온프레미스에서는 자동 생성이 안 되므로 추가 구성(MetalLB 등)이 필요하다.

Ingress는 다음을 해결한다.

* **도메인 기반 라우팅**: `app1.local`, `app2.local`

* **경로 기반 라우팅**: `/`, `/api`, `/admin`

* **TLS(HTTPS) 종료**: 인증서 하나로 여러 서비스 처리 가능

* **단일 진입점**: 외부 IP 하나로 여러 서비스 라우팅

---

### 1.2 Ingress 동작 구조

Ingress는 단독으로 동작하지 않는다. 반드시 **Ingress Controller**가 필요하다.

```
Client(브라우저)
   ↓ (외부 IP:80/443)
Service(ingress-nginx-controller, LoadBalancer/NodePort)
   ↓
Ingress Controller Pod(NGINX)
   ↓ (Ingress 규칙 적용)
Service(app1/app2 등, ClusterIP)
   ↓
Pod
```

* **Ingress 리소스**: “라우팅 규칙(정책)” 정의

* **Ingress Controller**: 실제로 HTTP 요청을 받아 규칙대로 전달하는 “엔진”

---

## 2. 클라우드 vs 온프레미스 차이

### 2.1 클라우드에서 LoadBalancer

클라우드 환경에서는:

* `type: LoadBalancer` Service 생성 시

* 클라우드 컨트롤러가 외부 LB 생성

* EXTERNAL-IP 자동 할당

즉 “자동”이다.

### 2.2 온프레미스에서 LoadBalancer

온프레미스는 클라우드 API가 없다.

* `type: LoadBalancer`로 만들어도 EXTERNAL-IP가 `<pending>` 상태가 된다.

* 따라서 LoadBalancer 역할을 대신해줄 구성요소가 필요하다.

대표가 **MetalLB**다.

---

## 3. 실습 환경 및 목표

### 3.1 실습 환경

* VM 3대
  + `k8s-cp` (control-plane)
  + `k8s-w1` (worker)
  + `k8s-w2` (worker)

* Pod CIDR: `10.244.0.0/16` (Flannel 기본)

* 클러스터 노드 대역 예시: `192.168.80.0/24`

* Windows 클라이언트에서 접속 테스트

### 3.2 목표

* MetalLB로 외부 IP(VIP) 할당

* Ingress NGINX Controller를 LoadBalancer로 노출

* app1/app2를 Host 기반으로 라우팅

* Windows에서 `http://app1.local`, `http://app2.local` 접속 성공

---

## 4. 사전 점검

### 4.1 노드 상태 확인

```
kubectl get nodes
```

* STATUS가 전부 `Ready`여야 한다.

* NotReady면 CNI/DNS/Container Runtime 문제 가능성이 높다.

### 4.2 DNS(CoreDNS) 확인

```
kubectl get pods -n kube-system -l k8s-app=kube-dns -o wide
```

* CoreDNS가 `1/1 Running`이 아니면 Ingress/MetalLB도 연쇄적으로 불안정해진다.

DNS 테스트:

```
kubectl run dns-test --rm -it --image=busybox -- sh
nslookup kubernetes.default.svc.cluster.local
exit
```

* 항상 성공해야 한다. 간헐 timeout이 나오면 DNS/Service 라우팅이 흔들리는 상태다.

---

## 5. MetalLB 설치 (온프레미스 LoadBalancer 구현)

### 5.1 MetalLB 설치

```
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.13.7/config/manifests/metallb-native.yaml
```

* `metallb-system` 네임스페이스에 controller/speaker가 설치된다.

확인:

```
kubectl get pods -n metallb-system -o wide
```

* controller 1개: Running

* speaker는 노드 수만큼: Running

---

### 5.2 IPAddressPool + L2Advertisement 생성

MetalLB는 “어떤 IP 범위에서 VIP를 뽑을지” 알아야 한다.

그 범위를 **IPAddressPool**로 정의한다.

또한 L2 모드에서는 **L2Advertisement**로 “이 풀을 L2(ARP) 방식으로 광고한다”를 선언한다.

`metallb-l2.yaml`:

```
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: first-pool
  namespace: metallb-system
spec:
  addresses:
  - 192.168.80.200-192.168.80.210
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: l2
  namespace: metallb-system
```

적용:

```
kubectl apply -f metallb-l2.yaml
```

### 주소 범위 선정 규칙

* 노드들과 같은 L2 대역이어야 한다.

* DHCP 범위와 겹치면 안 된다.

* 이미 사용 중인 IP와 겹치면 안 된다.

---

## 6. Ingress NGINX Controller 설치

### 6.1 Ingress NGINX 설치 (baremetal)

```
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/baremetal/deploy.yaml
```

확인:

```
kubectl get pods -n ingress-nginx -o wide
kubectl get svc -n ingress-nginx
```

* controller Pod가 `1/1 Running`이어야 한다.

* baremetal 배포는 Service가 NodePort로 생성되는 경우가 많다.

---

### 6.2 Ingress Controller Service를 LoadBalancer로 변경

MetalLB를 사용할 것이므로 Service 타입을 LoadBalancer로 바꾼다.

```
kubectl patch svc ingress-nginx-controller -n ingress-nginx -p '{"spec":{"type":"LoadBalancer"}}'
```

확인:

```
kubectl get svc -n ingress-nginx
```

예상 출력 예:

```
ingress-nginx-controller   LoadBalancer   10.x.x.x   192.168.80.200   80:xxxxx/TCP,443:yyyyy/TCP
```

* `EXTERNAL-IP`가 VIP로 잡혀야 한다.

* VIP가 잡히지 않으면 MetalLB(IPPool/L2Adv) 또는 DNS 문제부터 점검한다.

---

## 7. 테스트 애플리케이션 배포

### 7.1 app1 배포 + Service 생성

```
kubectl create deployment app1 --image=nginx
kubectl expose deployment app1 --port=80
```

* `create deployment`는 ReplicaSet/Pod를 자동 생성한다.

* `expose`는 Deployment의 라벨(selector)을 이용해 Service를 만든다.

확인:

```
kubectl get deploy,po,svc
```

### 7.2 app2 배포 + Service 생성

```
kubectl create deployment app2 --image=httpd
kubectl expose deployment app2 --port=80
```

---

## 8. Ingress 리소스 생성 (Host 기반 라우팅)

### 8.1 Ingress YAML 작성

`ingress.yaml`:

```
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: example-ingress
spec:
  ingressClassName: nginx
  rules:
  - host: app1.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app1
            port:
              number: 80
  - host: app2.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app2
            port:
              number: 80
```

### 옵션 설명

* `ingressClassName: nginx`
  + 어떤 Ingress Controller가 이 규칙을 처리할지 지정한다.
  + 이게 없으면 `CLASS <none>` 상태가 되며, Controller가 무시해서 404가 날 수 있다.

* `rules.host`
  + 요청의 Host 헤더와 일치해야 라우팅된다.
  + 브라우저에서 도메인으로 접근해야 한다.

* `pathType: Prefix`
  + `/`로 시작하는 모든 경로를 매칭한다.
  + `/api` 같은 경로를 나누고 싶으면 path를 추가한다.

* `backend.service.name/port`
  + 라우팅 대상 Service 이름/포트를 지정한다.

적용:

```
kubectl apply -f ingress.yaml
```

확인:

```
kubectl get ingress
kubectl describe ingress example-ingress
```

ADDRESS가 EXTERNAL-IP가 아니라 노드 IP가 할당된 경우 다음 명령 실행하거나 edit 사용해서 옵션 추가

```
kubectl patch deployment ingress-nginx-controller -n ingress-nginx --type='json' -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--publish-service=$(POD_NAMESPACE)/ingress-nginx-controller"}]'
```

인그레스 컨트롤러 디플로이먼트의 인자(`args`)에 아래 내용을 추가

kubectl edit deploy ingress-nginx-controller -n ingress-nginx

```
- --publish-service=$(POD_NAMESPACE)/ingress-nginx-controller
```

---

## 9. Windows 클라이언트 접속 설정

### 9.1 VIP 확인

```
kubectl get svc -n ingress-nginx
```

여기서 `EXTERNAL-IP` 값을 확인한다. 예: `192.168.80.200`

### 9.2 hosts 파일 수정

Windows에서:

`C:\Windows\System32\drivers\etc\hosts`

맨 아래에 추가:

```
192.168.80.200 app1.local
192.168.80.200 app2.local
```

### 9.3 브라우저 테스트

* `http://app1.local`

* `http://app2.local`

---

## 10. 동작 확인 및 진단 명령

### 10.1 Ingress 확인

```
kubectl get ingress
kubectl describe ingress example-ingress
```

### 10.2 Ingress Controller 확인

```
kubectl get pods -n ingress-nginx -o wide
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller --tail=100
```

### 10.3 라우팅 테스트(curl)

Host 헤더를 강제로 넣어 확인할 수 있다.

```
curl -H "Host: app1.local" http://192.168.80.200
curl -H "Host: app2.local" http://192.168.80.200
```

---

## 11. 자주 발생하는 문제와 해결

### 11.1 404 Not Found가 뜬다

의미:

* Ingress Controller는 응답 중이다.

* 하지만 규칙 매칭이 안 됐다.

점검:

1. `ingressClassName: nginx`가 있는지 확인

2. hosts 파일이 VIP로 정확히 매핑됐는지 확인

3. Ingress에 설정한 `host`가 요청과 정확히 일치하는지 확인

확인:

```
kubectl get ingress example-ingress -o yaml
kubectl get ingressclass
```

---

### 11.2 EXTERNAL-IP가 `<pending>`이다

의미:

* MetalLB가 VIP 할당을 못 했다.

점검:

1. IPAddressPool/L2Advertisement 존재 확인

2. speaker Pod가 모든 노드에 Running인지 확인

3. IP 대역이 실제 노드 네트워크와 같은지 확인

```
kubectl get ipaddresspool -n metallb-system
kubectl get l2advertisement -n metallb-system
kubectl get pods -n metallb-system -o wide
kubectl describe svc -n ingress-nginx ingress-nginx-controller
```

---

### 11.3 webhook 오류가 발생한다 (metallb apply 시)

대부분 DNS/CoreDNS 문제로 시작한다.

점검:

* CoreDNS가 1/1 Running인지

* DNS 질의가 간헐 timeout인지

```
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl run dns-test --rm -it --image=busybox -- sh
nslookup kubernetes.default.svc.cluster.local
exit
```

---

## 12. 핵심 정리

* Ingress는 규칙이다. 엔진은 Ingress Controller다.

* 온프레미스에서 LoadBalancer를 쓰려면 MetalLB 같은 구현체가 필요하다.

* Ingress Controller Service를 LoadBalancer로 바꾸면 MetalLB가 VIP를 할당한다.

* Ingress에 `ingressClassName`이 없으면 404가 날 수 있다.

* CoreDNS가 불안정하면 MetalLB/Ingress 모두 연쇄 장애가 난다.

---

## 13. 실습 전체 명령 요약

```
# (사전) 노드 Ready 확인
kubectl get nodes

# DNS 확인
kubectl get pods -n kube-system -l k8s-app=kube-dns

# MetalLB 설치
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.13.7/config/manifests/metallb-native.yaml
kubectl apply -f metallb-l2.yaml

# Ingress NGINX 설치
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/baremetal/deploy.yaml
kubectl patch svc ingress-nginx-controller -n ingress-nginx -p '{"spec":{"type":"LoadBalancer"}}'
kubectl get svc -n ingress-nginx

# 앱 배포
kubectl create deployment app1 --image=nginx
kubectl expose deployment app1 --port=80
kubectl create deployment app2 --image=httpd
kubectl expose deployment app2 --port=80

# Ingress 생성
kubectl apply -f ingress.yaml
kubectl describe ingress example-ingress
```

---

호스트 기반(Host-based) 인그레스가 도메인 이름(`app1.local`)으로 구분했다면, **경로 기반(Path-based) 인그레스**는 하나의 도메인 뒤에 붙는 경로(`/blog`, `/shop` 등)에 따라 트래픽을 다른 서비스로 보내는 방식.

하나의 IP(`200`번)와 하나의 도메인(`example.local`)을 사용하면서 내부 서비스만 갈라지는 예제.

---

### 경로 기반(Path-based) Ingress YAML 구성

이 예제에서는 `example.local`이라는 주소 하나를 쓰되, 뒤에 붙는 경로에 따라 `app1` 서비스와 `app2` 서비스로 나누어 전달한다.

YAML

```
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: path-based-ingress
  namespace: test-ns
  annotations:
    # / # 외부 경로(/app1)는 무시하고, 실제 서비스의 루트(/)로 연결해라
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - example.local
    secretName: app-tls-secret # 아까 만든 SAN 인증서(example.local 포함 필요)
  rules:
  - host: example.local # 하나의 도메인만 사용
    http:
      paths:
      - path: /app1 # example.local/app1 로 접속 시
        pathType: Prefix
        backend:
          service:
            name: app1
            port:
              number: 80
      - path: /app2 # example.local/app2 로 접속 시
        pathType: Prefix
        backend:
          service:
            name: app2
            port:
              number: 80
```

---

### 주요 설정 포인트

1. `pathType: Prefix`: 지정한 경로로 시작하는 모든 요청을 해당 서비스로 보낸다. 예를 들어 `/app1/images` 같은 요청도 `app1` 서비스로 가게 된다.

2. `rewrite-target: /` **(중요!)**:
   * 웹 브라우저는 `example.local/app1`로 요청을 보내지만, 실제 `app1` 파드 안의 웹 서버는 root 경로(`/`)에서 실행 중일 수 있다.
   * 이 설정이 있으면 인그레스가 중간에서 `/app1`이라는 경로를 지우고 파드에게는 `/`로 요청을 전달해 준다. 이게 없으면 파드가 "난 `/app1`이라는 폴더는 없는데?"라며 404 에러를 낼 수 있다.

---

### 테스트 방법

**1. 설정 적용**

```
kubectl apply -f path-ingress.yaml
```

**2.** `/etc/hosts` **파일 확인**

`example.local` 도메인이 로드밸런서 IP(`192.168.80.200`)로 지정되어 있는지 확인하세요.

```
192.168.80.200  example.local
```

**3. 접속 확인**

```
# app1 서비스로 접속
curl -k https://example.local/app1

# app2 서비스로 접속
curl -k https://example.local/app2
```

---

### 정리

경로 기반 인그레스는 **하나의 인증서**만 관리하면 된다는 큰 장점이 있다. 기존 `san.cnf` 파일의 `[ alt_names ]` 섹션에 `DNS.3 = example.local`을 추가해서 인증서를 다시 만들면 HTTPS까지 적용된다.

 [[10-1 SAN 포함 인증서 실습|10-1. SAN 포함 인증서 실습]]