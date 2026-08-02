---
title: "MetalLB(로드밸런서 구현체)"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "쿠버네티스", "9장 Service (ClusterIP NodePort LoadBalancer)"]
is_public: true
draft: false
---

# MetalLB(로드밸런서 구현체)

## 1. 학습 목표

* Kubernetes `Service`의 역할과 `type: LoadBalancer` 동작 원리 이해

* VM 기반 클러스터에서 `LoadBalancer`를 쓰기 위해 필요한 구성(= **MetalLB**) 설치

* `EXTERNAL-IP`를 할당받아 외부에서 접속(브라우저/curl)까지 검증

* 장애/미할당(“pending”) 시 확인 포인트 숙지

---

## 2. 사전 구성(실습 환경)

### 2.1 VM 구성 예시

* `k8s-m1` (Control Plane) : `192.168.80.110`

* `k8s-w1` (Worker) : `192.168.80.120`

* `k8s-w2` (Worker) : `192.168.80.130`

* VM들은 같은 L2 네트워크(같은 브리지/Host-only 등)에 있다고 가정

> **중요 포인트**
>
> MetalLB(L2 모드)는 “외부에서 접속할 IP(= EXTERNAL-IP)”를 **같은 네트워크 대역에서 하나 골라** 클러스터 노드가 **ARP로 ‘내가 그 IP의 주인’이라고 광고**해서 트래픽을 받는 방식.
>
> 그래서 **IP 풀**은 “VM들이 붙어 있는 네트워크에서 사용 가능한(다른 장비가 안 쓰는) IP 범위”여야 한다.

### 2.2 kubectl 동작 확인

```
kubectl get nodes -o wide
```

* `STATUS`가 `Ready`인지 확인

* `INTERNAL-IP`(노드 IP)가 예상한 대역인지 확인

---

## 3. 이론: LoadBalancer 서비스가 하는 일

### 3.1 Service란?

* Pod는 IP가 자주 바뀔 수 있고(재배치/재시작), 여러 개로 수평 확장됨

* Service는 \*\*“고정된 접속 지점(가상 IP + DNS)”\*\*을 제공하고, 내부적으로 **Pod로 로드밸런싱**함

### 3.2 Service 타입 비교 핵심

* `ClusterIP` : 클러스터 내부에서만 접근(기본값)

* `NodePort` : 모든 노드의 특정 포트를 열어 외부 접근 가능(예: `nodeIP:30080`)

* `LoadBalancer` : 외부용 IP(또는 도메인)를 제공하고 그 IP로 들어온 트래픽을 서비스로 전달
  + 클라우드: 클라우드 LB가 자동 생성됨
  + 온프레미스: **MetalLB** 등으로 LoadBalancer 기능을 구현해야 함

---

## 4. 실습 1: MetalLB 설치 (온프레미스 LoadBalancer 구현)

> 아래 실습은 “**MetalLB + L2 모드**” 기준입니다. 가장 단순하고 VM 환경에서 많이 쓴다.

### 4.1 MetalLB 설치

공식 매니페스트를 적용합니다(버전 고정 추천). 예시는 `v0.14.8` 기준:

```
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.15.3/config/manifests/metallb-native.yaml
```

### 명령어 해설

* `kubectl apply -f <URL 또는 파일>`
  + Kubernetes 리소스(YAML)를 클러스터에 **생성/갱신**합니다.
  + `f`는 “파일(file) 또는 URL에 있는 매니페스트를 적용”한다는 뜻입니다.

* 위 URL의 매니페스트에는 MetalLB가 동작하는 데 필요한 구성요소가 포함된다.
  + `metallb-system` 네임스페이스
  + 컨트롤러/스피커(노드에서 ARP/NDP 광고 담당) 관련 Deployment/DaemonSet 등

설치 후 확인:

```
kubectl get ns | grep metallb
kubectl get pods -n metallb-system -o wide
```

* `controller` Pod와 `speaker` Pod들이 `Running`인지 확인한다.

* `speaker`는 보통 DaemonSet이라 노드마다 1개씩 뜬다.

---

## 5. 실습 2: IPAddressPool / L2Advertisement 설정

MetalLB는 “어떤 IP를 LoadBalancer용으로 나눠줄지”를 풀(Pool)로 정의한다.

### 5.1 사용할 IP 범위 정하기

예: `192.168.80.200 ~ 192.168.80.220`을 LB 전용으로 쓰겠다고 가정

(이 범위는 **DHCP/다른 장비가 사용하지 않는** 범위여야 한다)

### 5.2 IP 풀과 L2 광고 설정 YAML 작성

아래 내용을 `metallb-pool.yaml`로 저장합니다.

```
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: lb-pool
  namespace: metallb-system
spec:
  addresses:
  - 192.168.80.200-192.168.80.220
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: lb-l2adv
  namespace: metallb-system
spec:
  ipAddressPools:
  - lb-pool
```

적용:

```
kubectl apply -f metallb-pool.yaml
```

### YAML 해설

* `IPAddressPool`
  + MetalLB가 **EXTERNAL-IP로 할당 가능한 IP 목록/범위**를 정의한다.
  + `addresses`에 CIDR(`192.168.80.0/24`) 또는 범위(`A-B`)를 넣을 수 있습니다.

* `L2Advertisement`
  + L2 모드로 동작하겠다는 의미이다.
  + “이 풀에서 할당한 IP는 ARP로 광고해서 트래픽을 받겠다”는 동작을 활성화한다.

* 에러발생시 다음 명령 실행: **Validating Webhook 삭제** (설정값이 올바른지 검사하는 기능 제거)

```
kubectl delete validatingwebhookconfigurations.admissionregistration.k8s.io metallb-webhook-configuration
```

---

## 6. 실습 3: 테스트용 애플리케이션 배포 + LoadBalancer 서비스 생성

### 6.1 웹 서버 배포(nginx)

```
kubectl create deploy web --image=nginx
```

Pod 확인:

```
kubectl get pods -o wide
```

### 6.2 Service를 LoadBalancer로 노출

```
kubectl expose deploy web --port=80 --target-port=80 --type=LoadBalancer
```

### 명령어 옵션 해설

* `kubectl expose deploy web`
  + `web` Deployment를 대상으로 Service를 생성한다.

* `--port=80`
  + Service가 외부/내부에서 **제공할 포트**이다.

* `--target-port=80`
  + Service가 트래픽을 전달할 **Pod(컨테이너) 포트**이다.

* `--type=LoadBalancer`
  + Service 타입을 LoadBalancer로 생성한다.
  + MetalLB가 있다면 `EXTERNAL-IP`가 IP 풀에서 할당된다.

서비스 확인:

```
kubectl get svc -o wide
```

정상 예시:

* `EXTERNAL-IP`에 `192.168.80.200` 같은 값이 잡힘

* `PORT(S)`는 `80:<NodePort>/TCP` 형태로 보일 수 있음
  + LoadBalancer는 내부적으로 NodePort도 함께 만들어서 트래픽을 전달하는 경우가 많다.

---

## 7. 실습 4: “클러스터 외부”에서 접속 확인

### 7.1 같은 네트워크 대역(예: 내 PC가 VM 네트워크에 붙어있음)에서 접속

이제 외부 PC에서:

```
curl http://192.168.80.200
```

또는 브라우저로 `http://192.168.80.200` 접속 → nginx 기본 페이지가 뜨면 성공

### 7.2 “진짜 외부 인터넷”에서 접속하려면?

VM 네트워크가 NAT/사설망이면, 인터넷에서 바로 `192.168.80.200`으로는 접근이 안 됩니다. 이 경우 보통 두 가지 중 하나가 필요하다.

1. **라우터/방화벽에서 포트포워딩(DNAT)**

* 공인 IP(또는 외부 라우터 IP)의 80 포트를 `192.168.80.200:80`으로 포워딩

* 외부에서는 `http://<공인IP>`로 접속

1. **퍼블릭 대역 IP를 VM 네트워크에 직접 부여**

* 데이터센터/공인망에서 VM이 공인 대역을 직접 받는 구조라면
  + MetalLB 풀도 그 공인 대역에서 잡고
  + 외부에서 공인 IP로 바로 접속 가능

---

## 8. 동작 원리

1. 사용자가 `type: LoadBalancer` Service 생성

2. MetalLB가 Service를 감지하고 IP 풀에서 **사용 가능한 IP**를 하나 할당

3. speaker(노드)가 그 IP에 대해 **ARP 응답**(L2 광고)

4. 외부 클라이언트가 `EXTERNAL-IP:80`으로 접속 → 해당 노드로 패킷 도착

5. Kubernetes 서비스(iptables/IPVS)가 트래픽을 적절한 Pod로 전달

6. 여러 Pod가 있으면 Service가 라운드로빈/해시 등으로 분산

---

## 9. 자주 발생하는 문제 & 트러블슈팅

### 9.1 `EXTERNAL-IP`가 `<pending>`에서 안 바뀜

체크리스트:

* MetalLB Pod 정상?

  ```
  kubectl get pods -n metallb-system
  ```

* IPAddressPool/L2Advertisement 적용했나?

  ```
  kubectl get ipaddresspool -n metallb-system
  kubectl get l2advertisement -n metallb-system
  ```

* 풀에 준 IP가 **실제로 사용 가능한 IP**인가? (중복 사용/ DHCP 충돌)

* 노드들이 같은 L2 네트워크인가? (서로 ARP가 통하는 구조인지)

로그 확인:

```
kubectl logs -n metallb-system deploy/controller
kubectl logs -n metallb-system ds/speaker
```

### 9.2 외부에서 접속이 안 되는데 EXTERNAL-IP는 있음

* 내 PC에서 그 대역으로 라우팅이 되는지 확인(같은 네트워크냐?)

* VM/호스트 방화벽이 80 포트를 막는지 확인

* 외부 인터넷이라면 **포트포워딩/라우팅**이 구성되어 있는지 확인

### 9.3 NodePort와 혼동

* `LoadBalancer`는 보통 내부적으로 `NodePort`도 같이 잡힌다.

* 일반 사용자는 `EXTERNAL-IP:서비스포트(80)`로 접근한다.

---