---
title: "실습 GKE VPC-native"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Google 쿠버네티스 아키텍처 설계 및 구축"]
is_public: true
draft: false
---

# 실습. GKE VPC-native

---

### nginx 파드 생성 후 동일 VPC의 다른 서브넷 VM에서 Pod IP로 직접 접속하기

---

## 1. 실습 목표

* VPC-native GKE 클러스터를 생성한다

* nginx 파드를 배포한다

* 파드에 부여된 **Pod IP**를 확인한다

* 동일 VPC의 다른 서브넷에 있는 VM에서 **Pod IP로 직접** `curl` 한다

* 이를 통해 **Pod IP가 VPC 내부에서 라우팅된다**는 점을 확인한다

---

## 2. 실습 구조

구성은 다음과 같다.

* VPC : `vpc-native-lab-vpc`

* GKE용 서브넷 : `gke-subnet`
  + Primary range: `10.10.0.0/24`
  + Secondary range(Pod): `10.20.0.0/16`
  + Secondary range(Service): `10.30.0.0/20`

* VM용 서브넷 : `vm-subnet`
  + Primary range: `10.40.0.0/24`

* GKE Standard 클러스터 : `vpc-native-cluster`

* 테스트 VM : `curl-vm`

* 테스트 대상 파드 : `nginx`

핵심 포인트

* **노드 IP**는 GKE 서브넷의 기본 대역에서 할당됨

* **Pod IP**는 GKE 서브넷의 Secondary range에서 할당됨

* 이 **Pod IP가 같은 VPC 안에서 직접 라우팅**됨

---

## 3. 사전 준비

Cloud Shell 또는 gcloud가 설치된 환경에서 진행한다.

프로젝트와 리전을 변수로 지정한다.

```
export PROJECT_ID=$(gcloud config get-value project)
export REGION=asia-northeast3
export ZONE=asia-northeast3-a
```

현재 프로젝트 확인:

```
gcloud config get-value project
```

필요 API 활성화:

```
gcloud services enable container.googleapis.com compute.googleapis.com
```

---

## 4. VPC와 서브넷 생성

### 4-1. VPC 생성

```
gcloud compute networks create vpc-native-lab-vpc \
  --subnet-mode=custom
```

설명:

* `--subnet-mode=custom`
  + 자동 모드 VPC가 아니라 직접 서브넷을 설계하는 방식이다
  + GKE 실습에서는 IP 대역을 명확하게 제어하기 위해 custom 모드를 사용한다

---

### 4-2. GKE용 서브넷 생성

이 서브넷에는 **기본 대역 + secondary range 두 개**가 필요하다.

```
gcloud compute networks subnets create gke-subnet \
  --network=vpc-native-lab-vpc \
  --region=$REGION \
  --range=10.10.0.0/24 \
  --secondary-range=gke-pod-range=10.20.0.0/16,gke-svc-range=10.30.0.0/20
```

설명:

* `--range=10.10.0.0/24`
  + 노드 NIC가 붙는 기본 subnet 대역이다

* `--secondary-range=...`
  + VPC-native에서 Pod와 Service IP를 위한 보조 대역이다

* `gke-pod-range=10.20.0.0/16`
  + Pod IP가 여기서 할당됨

* `gke-svc-range=10.30.0.0/20`
  + ClusterIP Service 대역이다

VPC-native 클러스터는 subnet의 secondary range를 사용해 Pod/Service IP를 관리한다. -

---

### 4-3. VM용 서브넷 생성

VM은 같은 VPC지만 **다른 서브넷**에 둔다.

```
gcloud compute networks subnets create vm-subnet \
  --network=vpc-native-lab-vpc \
  --region=$REGION \
  --range=10.40.0.0/24
```

---

## 5. 방화벽 규칙 생성

같은 VPC라도 GCP에서는 **VPC 방화벽 규칙**이 적용된다.

따라서 VM에서 Pod로 HTTP 접근이 가능하도록 허용 규칙을 만든다.

### 5-1. 내부 통신 허용 규칙

```
gcloud compute firewall-rules create allow-internal-lab \
  --network=vpc-native-lab-vpc \
  --allow=tcp:80,tcp:22,icmp \
  --source-ranges=10.10.0.0/24,10.20.0.0/16,10.30.0.0/20,10.40.0.0/24
```

설명:

* `tcp:80`
  + nginx 접속용

* `tcp:22`
  + SSH 접속용

* `icmp`
  + 네트워크 테스트용

* `--source-ranges`
  + 실습에 사용하는 주요 내부 대역을 모두 허용함

좀 더 엄격하게 하려면 VM 서브넷만 source로 허용해도 된다.

예:

```
gcloud compute firewall-rules create allow-vm-to-pod-http \
  --network=vpc-native-lab-vpc \
  --allow=tcp:80 \
  --source-ranges=10.40.0.0/24
```

---

## 6. GKE Standard 클러스터 생성

### 6-1. VPC-native 클러스터 생성

```
gcloud container clusters create vpc-native-cluster \
  --zone=$ZONE \
  --network=vpc-native-lab-vpc \
  --subnetwork=gke-subnet \
  --enable-ip-alias \
  --cluster-secondary-range-name=gke-pod-range \
  --services-secondary-range-name=gke-svc-range \
  --num-nodes=2
```

설명:

* `--enable-ip-alias`
  + VPC-native 클러스터를 만드는 핵심 옵션이다
  + Alias IP 기반으로 Pod IP를 사용한다

* `--cluster-secondary-range-name=gke-pod-range`
  + Pod IP로 사용할 secondary range 이름 지정

* `--services-secondary-range-name=gke-svc-range`
  + Service IP range 지정

* `--num-nodes=2`

VPC-native 생성 시 `--enable-ip-alias`를 사용하며, 이 방식이 권장된다.

클러스터 생성 확인:

```
gcloud container clusters list
```

```
gcloud container clusters list \
    --format="table(name, zone, networkConfig.network, ipAllocationPolicy.useIpAliases)"
```

kubectl 인증 정보 가져오기:

```
gcloud container clusters get-credentials vpc-native-cluster --zone=$ZONE
```

---

## 7. 테스트용 VM 생성

같은 VPC의 다른 서브넷에 VM을 만든다.

```
gcloud compute instances create curl-vm \
  --zone=$ZONE \
  --machine-type=e2-micro \
  --subnet=vm-subnet \
  --image-family=debian-12 \
  --image-project=debian-cloud
```

설명:

* `--subnet=vm-subnet`
  + GKE와는 다른 서브넷에 VM 생성

* `debian-12`
  + 기본 네트워크 실습용으로 무난함

VM 내부 IP 확인:

```
gcloud compute instances describe curl-vm \
  --zone=$ZONE \
  --format="get(networkInterfaces[0].networkIP)"
```

---

## 8. nginx 파드 배포

### 8-1. nginx 파드 생성

```
kubectl run nginx \
  --image=nginx \
  --port=80
```

파드 상태 확인:

```
kubectl get pods -o wide
```

예상 결과 예시:

```
NAME    READY   STATUS    RESTARTS   AGE   IP          NODE
nginx   1/1     Running   0          20s   10.20.0.5   gke-vpc-native-cluster-default-pool-...
```

여기서 중요한 것은 `IP` 항목이다.

* `10.20.0.5`
  + Pod IP
  + 아까 secondary range로 지정한 `10.20.0.0/16` 대역에서 할당된 주소다

즉, Pod가 단순히 노드 내부 가상 주소가 아니라, **VPC가 인지하는 Alias IP 체계로 붙어 있는 주소**라는 점이 핵심이다.-

---

### 8-2. nginx 응답 페이지를 구분 가능하게 수정

```
kubectl exec nginx -- /bin/sh -c 'echo "hello from gke pod" > /usr/share/nginx/html/index.html'
```

파드 내부에서 직접 확인:

```
kubectl exec nginx -- curl -s localhost
```

예상 결과:

```
hello from gke pod
```

---

## 9. Pod IP 확인

Pod IP만 따로 추출한다.

```
export POD_IP=$(kubectl get pod nginx -o jsonpath='{.status.podIP}')
echo $POD_IP
```

예상 예시:

```
10.20.0.5
```

---

## 10. VM에서 Pod IP로 직접 curl

### 10-1. VM에 SSH 접속

```
gcloud compute ssh curl-vm --zone=$ZONE
```

---

### 10-2. VM에서 Pod IP로 curl

SSH 접속 후 다음 명령 실행:

```
curl http://10.20.0.5
```

또는 Cloud Shell에서 환경변수 값을 이용해 바로 실행하려면:

```
gcloud compute ssh curl-vm --zone=$ZONE --command="curl -s http://$POD_IP"
```

예상 결과:

```
hello from gke pod
```

이 결과가 의미하는 것은 다음과 같다.

* VM은 **다른 서브넷**에 있음

* 그런데도 Pod IP로 **직접 HTTP 요청**이 감

* 별도의 NodePort, LoadBalancer, Ingress 없이도 됨

* 즉, **Pod IP 자체가 VPC 내부에서 라우팅 가능한 주소로 동작**함을 확인한 것이다

---

## 11. 왜 이게 중요한가

GKE의 VPC-native에서는 다음과 같이 동작한다.

* Pod IP가 VPC 내부에서 직접 라우팅됨

* 노드에 Alias IP 형태로 연결됨

* VPC가 그 주소를 인지함

* 그래서 같은 VPC 안의 다른 VM도 그 Pod IP로 직접 접근 가능함.

---

## 12. 전체 명령어 모음

```
export PROJECT_ID=$(gcloud config get-value project)
export REGION=asia-northeast3
export ZONE=asia-northeast3-a

gcloud services enable container.googleapis.com compute.googleapis.com

gcloud compute networks create vpc-native-lab-vpc \
  --subnet-mode=custom

gcloud compute networks subnets create gke-subnet \
  --network=vpc-native-lab-vpc \
  --region=$REGION \
  --range=10.10.0.0/24 \
  --secondary-range=gke-pod-range=10.20.0.0/16,gke-svc-range=10.30.0.0/20

gcloud compute networks subnets create vm-subnet \
  --network=vpc-native-lab-vpc \
  --region=$REGION \
  --range=10.40.0.0/24

gcloud compute firewall-rules create allow-internal-lab \
  --network=vpc-native-lab-vpc \
  --allow=tcp:80,tcp:22,icmp \
  --source-ranges=10.10.0.0/24,10.20.0.0/16,10.30.0.0/20,10.40.0.0/24

gcloud container clusters create vpc-native-cluster \
  --zone=$ZONE \
  --network=vpc-native-lab-vpc \
  --subnetwork=gke-subnet \
  --enable-ip-alias \
  --cluster-secondary-range-name=gke-pod-range \
  --services-secondary-range-name=gke-svc-range \
  --num-nodes=2

gcloud container clusters get-credentials vpc-native-cluster --zone=$ZONE

gcloud compute instances create curl-vm \
  --zone=$ZONE \
  --machine-type=e2-micro \
  --subnet=vm-subnet \
  --image-family=debian-12 \
  --image-project=debian-cloud

kubectl run nginx --image=nginx --port=80

kubectl exec nginx -- /bin/sh -c 'echo "hello from gke pod" > /usr/share/nginx/html/index.html'

kubectl get pods -o wide

export POD_IP=$(kubectl get pod nginx -o jsonpath='{.status.podIP}')
echo $POD_IP

gcloud compute ssh curl-vm --zone=$ZONE --command="curl -s http://$POD_IP"
```

---

## 16. 정리

> VPC-native GKE에서는 Pod IP가 subnet의 secondary range에서 할당되며, 이 주소는 같은 VPC 내부에서 직접 라우팅된다. 따라서 동일 VPC의 다른 서브넷에 있는 VM도 Pod IP로 직접 접근할 수 있다.