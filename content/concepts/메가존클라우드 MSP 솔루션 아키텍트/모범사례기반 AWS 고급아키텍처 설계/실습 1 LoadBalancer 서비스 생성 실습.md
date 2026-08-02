---
title: "실습 1 LoadBalancer 서비스 생성 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "모범사례기반 AWS 고급아키텍처 설계"]
is_public: true
draft: false
---

# 실습 1. LoadBalancer 서비스 생성 실습

## 1. 실습 목표

nginx 애플리케이션을 배포하고, 이를 `Service type=LoadBalancer`로 외부에 공개해 봄.

* Deployment가 Pod를 생성하는 방식

* Service가 Pod 앞단에 고정 진입점을 제공하는 방식

* `LoadBalancer` 타입 서비스가 EKS에서 외부 로드밸런서와 연결되는 방식

* 온프레미스 Kubernetes와 EKS의 차이점

Kubernetes 공식 문서는 `LoadBalancer`를 지원되는 클라우드 공급자 환경에서 외부 로드밸런서를 생성하는 Service 방식으로 설명함.

---

## 2. 실습 개요

온프레미스 Kubernetes에서는 Pod를 외부에 공개하려면 보통 다음 중 하나가 필요함.

* NodePort 사용

* Ingress Controller 설치

* MetalLB 같은 별도 LoadBalancer 구성

* 외부 L4/L7 장비와 수동 연동

반면 EKS에서는 `Service`를 `LoadBalancer` 타입으로 만들면 AWS 쪽 로드밸런서 생성과 연결이 가능함.

---

## 3. 실습 전 확인 사항

다음 조건이 준비되어 있어야 함.

1. EKS 클러스터가 이미 생성되어 있어야 함

2. `kubectl`이 현재 클러스터에 연결된 상태여야 함

3. 워커 노드가 `Ready` 상태여야 함

4. 실습용 네임스페이스 또는 기본 네임스페이스를 사용할 수 있어야 함

먼저 아래 명령으로 현재 연결 상태를 확인함.

```
kubectl config current-context
kubectl get nodes
```

`kubectl get nodes` 결과에서 노드 상태가 `Ready`로 보이면 기본적인 클러스터 연결은 정상임. Kubernetes에서 Service는 결국 선택된 Pod 집합에 트래픽을 보내는 추상화 계층이므로, 노드와 Pod가 정상이어야 의미 있는 실습이 가능함.

---

## 4. 실습 흐름

이번 실습은 다음 순서로 진행함.

1. nginx Deployment 생성

2. Pod 생성 여부 확인

3. LoadBalancer 타입 Service 생성

4. Service 상태 확인

5. 외부 주소 확인

6. 브라우저 또는 `curl`로 접속 테스트

7. 결과 해석

8. 실습 정리 및 삭제

이 순서는 Kubernetes의 기본 객체 관계를 이해하기에 좋음. 먼저 Deployment가 Pod를 만들고, 그 다음 Service가 Pod 집합을 네트워크로 노출함.

---

## 5. 1단계 - nginx Deployment 생성

먼저 nginx 애플리케이션을 배포함.

```
kubectl create deployment nginx --image=nginx
```

### 명령어 설명

### `kubectl create deployment`

Deployment 리소스를 생성하는 명령임.

Deployment는 단순히 Pod 하나만 띄우는 것이 아니라,

원하는 개수의 Pod가 항상 유지되도록 관리하는 상위 리소스임.

### `nginx`

Deployment 이름임.

### `--image=nginx`

Docker Hub의 `nginx` 이미지를 사용해서 컨테이너를 생성하라는 의미임.

즉, 이 명령은 nginx 웹 서버 컨테이너를 실행하는 Deployment를 생성하는 명령임.

---

## 6. 2단계 - Pod 생성 여부 확인

Deployment가 생성되었다고 바로 애플리케이션이 준비된 것은 아님.

실제로 Pod가 정상 생성되고 실행 중인지 확인해야 함.

```
kubectl get pods
```

조금 더 자세히 보고 싶으면 아래 명령도 가능함.

```
kubectl get pods -o wide
```

### 확인 포인트

* `STATUS`가 `Running`인지 확인

* `READY` 값이 `1/1`인지 확인

* 어떤 노드에 배치되었는지 확인

* `-o wide` 옵션은 Pod IP, Node 정보까지 출력

---

## 7. 3단계 - LoadBalancer 타입 Service 생성

이제 nginx Deployment를 외부에 공개함.

```
kubectl expose deployment nginx --port=80 --type=LoadBalancer
```

### 명령어 설명

### `kubectl expose deployment nginx`

기존 Deployment를 네트워크 서비스로 노출하라는 의미임.

### `--port=80`

Service가 외부에 제공할 포트를 80으로 지정함.

### `--type=LoadBalancer`

Service 타입을 `LoadBalancer`로 지정함.

이 설정이 핵심임.

Kubernetes에서 `LoadBalancer`는 `NodePort`를 포함하는 상위 개념으로 동작하며, 지원되는 클라우드 환경에서는 외부 로드밸런서를 생성함.

---

## 8. 4단계 - Service 상태 확인

Service가 제대로 생성되었는지 확인함.

```
kubectl get svc
```

예상 출력 예시는 다음과 비슷함.

```
NAME         TYPE           CLUSTER-IP      EXTERNAL-IP                                                               PORT(S)        AGE
kubernetes   ClusterIP      10.100.0.1      <none>                                                                    443/TCP        1h
nginx        LoadBalancer   10.100.20.145   a1b2c3d4e5f6g7h8.ap-northeast-2.elb.amazonaws.com                        80:31245/TCP   2m
```

### 각 항목 해설

### `NAME`

Service 이름임.

### `TYPE`

Service 타입임.

이번 실습에서는 `LoadBalancer`여야 함.

### `CLUSTER-IP`

클러스터 내부에서만 사용하는 가상 IP임.

Pod나 다른 서비스가 내부 통신할 때 사용함.

### `EXTERNAL-IP`

외부 접속용 주소임.

EKS에서는 ELB 계열 DNS 이름이 표시될 수 있음.

### `PORT(S)`

서비스 포트 정보임.

`80:31245/TCP`처럼 보이면 앞의 `80`은 서비스 포트, 뒤의 숫자는 NodePort임.

Kubernetes 문서 기준으로 `LoadBalancer`는 클러스터 밖에서 접근 가능한 주소를 제공하며, 내부적으로 `NodePort` 메커니즘을 포함할 수 있음.

---

## 9. 5단계 - EXTERNAL-IP 또는 DNS 이름 대기

Service를 만들자마자 바로 외부 주소가 생기지 않을 수 있음.

잠시 후 다시 확인해야 할 수 있음.

```
kubectl get svc
```

처음에는 `EXTERNAL-IP`가 아래처럼 보일 수 있음.

```
<pending>
```

이 상태는 아직 외부 로드밸런서 생성 및 연결이 완료되지 않았다는 뜻임.

EKS에서 외부 로드밸런서 생성은 Kubernetes 리소스 생성 직후 즉시 끝나는 것이 아니라, AWS 측 리소스 프로비저닝 과정을 거침. AWS Load Balancer Controller 또는 클라우드 공급자 로직이 AWS ELB 리소스를 생성하고 연결해야 하므로 대기 시간이 생길 수 있음.

---

## 10. 6단계 - 브라우저 또는 curl로 접속 테스트

`EXTERNAL-IP` 또는 DNS 이름이 생성되면 접속을 확인함.

CMD에서는 아래처럼 테스트 가능함.

```
curl http://a1b2c3d4e5f6g7h8.ap-northeast-2.elb.amazonaws.com
```

또는 브라우저 주소창에 해당 DNS 이름을 그대로 넣어도 됨.

정상이라면 nginx 기본 페이지 HTML이 보이거나, 브라우저에서 nginx 시작 화면이 열림.

---

## 11. 7단계 - Service 상세 정보 확인

문제 해결이나 구조 설명을 위해 아래 명령도 자주 사용함.

```
kubectl describe svc nginx
```

이 명령은 Service 상세 정보를 보여줌.

특히 다음 항목을 볼 수 있음.

* Labels

* Selector

* Type

* IP

* Port

* Endpoints

* Events

### 중요한 확인 포인트

### `Selector`

이 Service가 어떤 Pod를 선택하는지 보여줌.

### `Endpoints`

실제로 트래픽을 전달할 Pod IP와 포트가 보임.

즉, Service는 라벨 셀렉터로 Pod를 고르고, 그 Pod를 엔드포인트로 등록해서 트래픽을 전달함.

---

## 12. 결과

### 12-1. Deployment와 Service는 역할이 다름

* Deployment는 애플리케이션 실행 상태를 유지함

* Service는 애플리케이션에 접근하는 네트워크 진입점을 제공함

### 12-2. `LoadBalancer`는 EKS에서 특히 의미가 큼

온프레미스에서는 `LoadBalancer` 타입 Service가 바로 외부 공개로 이어지지 않는 경우가 많음.

EKS에서는 AWS 로드밸런서 서비스와 결합되므로, 같은 Kubernetes 명령이라도 결과가 훨씬 실무적임.

---

## 13. 자주 발생하는 문제

### 13-1. `EXTERNAL-IP`가 계속 `<pending>` 상태인 경우

가능한 원인은 다음과 같음.

* 로드밸런서 생성 권한 문제

* 서브넷 태그 문제

* AWS Load Balancer Controller 또는 관련 설정 문제

* VPC/서브넷 네트워크 설정 문제

특히 AWS Load Balancer Controller를 사용하는 구성에서는 IAM 권한과 서브넷 태그가 중요함.

## 14. 실습 정리

이번 실습을 통해 확인한 내용은 다음과 같음.

* `kubectl create deployment`로 애플리케이션을 배포할 수 있음

* `kubectl expose deployment --type=LoadBalancer`로 외부 공개 구성을 만들 수 있음

* EKS에서는 이 Service가 AWS 외부 로드밸런서와 연결될 수 있음

---

## 15. 실습 후 정리 명령

실습이 끝났으면 리소스를 삭제함.

```
kubectl delete svc nginx
kubectl delete deployment nginx
```

서비스를 먼저 지우면 외부 로드밸런서 정리도 함께 진행됨. 외부 공개용 Service는 클라우드 로드밸런서와 연결될 수 있으므로, 비용과 리소스 정리를 위해 실습 후 반드시 삭제

---