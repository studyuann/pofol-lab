---
title: "실습 3 ALB Ingress 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "모범사례기반 AWS 고급아키텍처 설계"]
is_public: true
draft: false
---

# 실습 3. ALB Ingress 실습

## 1. 실습 목표

이 실습을 통해 다음을 이해할 수 있음.

* Kubernetes Ingress의 역할

* Service와 Ingress의 차이

* ALB와 Kubernetes Ingress의 연결 방식

* 경로 기반 라우팅(Path-based routing)

* 온프레미스 Ingress와 EKS Ingress의 차이

---

## 2. 실습 개요

앞선 실습 1에서는 `Service type=LoadBalancer`를 사용했음.

이 방식은 단순하고 빠르지만, 서비스마다 로드밸런서가 따로 생기거나, HTTP 경로 기반 제어가 제한적일 수 있음.

Ingress는 이보다 한 단계 상위 개념임.

즉, 여러 서비스를 하나의 외부 진입점 뒤에 두고, 경로나 호스트 이름에 따라 분기할 수 있음. Kubernetes 문서도 Ingress는 외부에서 서비스로 가는 HTTP/HTTPS 경로를 제어하는 객체라고 설명함. ([kubernetes.io](https://kubernetes.io/docs/concepts/services-networking/ingress/?utm_source=chatgpt.com))

EKS에서는 AWS Load Balancer Controller가 이 Ingress를 해석해서 **AWS ALB**를 생성함.

즉, 다음 흐름이 성립함.

> Kubernetes Ingress → AWS Load Balancer Controller → AWS ALB 생성 및 설정

이것이 EKS에서 매우 중요한 이유는, 온프레미스에서는 보통 NGINX Ingress Controller 같은 별도 Ingress Controller만 설치되고, 외부 L7 장비 연동은 별도로 해야 하는 경우가 많기 때문임.

---

## 3. 실습 전 확인 사항

다음 조건이 준비되어 있어야 함.

1. EKS 클러스터가 생성되어 있어야 함

2. `kubectl`이 현재 클러스터에 연결되어 있어야 함

3. AWS Load Balancer Controller가 설치되어 있어야 함

4. Ingress를 생성할 수 있는 권한과 서브넷 태그 설정이 준비되어 있어야 함

- [[AWS Load Balancer Controller 설치]]

먼저 현재 컨텍스트와 노드를 확인함.

```
kubectl config current-context
kubectl get nodes
```

그 다음 AWS Load Balancer Controller 관련 Pod가 존재하는지 확인함.

```
kubectl get pods -n kube-system
```

또는 더 직접적으로 Deployment를 확인할 수도 있음.

```
kubectl get deployment -n kube-system
```

일반적으로 `aws-load-balancer-controller`라는 이름의 Deployment가 보여야 함. AWS는 Helm을 사용한 설치 절차와 함께 `aws-load-balancer-controller` 리소스를 기준으로 안내함. ([docs.aws.amazon.com](https://docs.aws.amazon.com/eks/latest/userguide/lbc-helm.html?utm_source=chatgpt.com))

---

## 4. AWS Load Balancer Controller가 왜 필요한가

Kubernetes Ingress 객체는 **라우팅 규칙을 정의하는 API 객체**일 뿐임.

Ingress 자체가 로드밸런서를 만드는 것은 아님.

실제로 Ingress를 해석하고, 외부 로드밸런서를 만들고, 리스너 규칙과 대상 그룹을 구성하는 것은 **Ingress Controller**의 역할임.

EKS에서는 그 역할을 **AWS Load Balancer Controller**가 담당함.

AWS는 이 컨트롤러가 Kubernetes Service와 Ingress를 만족시키기 위해 AWS ELB 리소스를 프로비저닝한다고 설명함.

---

## 5. 실습 흐름

이번 실습은 다음 순서로 진행함.

1. 백엔드용 Deployment 2개 생성

2. 각 Deployment를 ClusterIP Service로 노출

3. Ingress 리소스 생성

4. ALB 생성 여부 확인

5. 경로 기반 라우팅 테스트

6. 결과 해석

7. 실습 정리

---

## 6. 1단계 - 테스트용 Deployment 2개 생성

서로 다른 경로로 분기할 수 있도록 nginx 기반 애플리케이션 2개를 생성함.

### app1 생성

```
kubectl create deployment app1 --image=nginx
```

### app2 생성

```
kubectl create deployment app2 --image=httpd
```

Pod 생성 여부를 확인함.

```
kubectl get pods
```

---

## 7. 2단계 - 각 Deployment를 ClusterIP Service로 노출

Ingress는 일반적으로 Service를 대상으로 라우팅함.

따라서 먼저 내부 서비스 두 개를 생성함.

### app1 서비스 생성

```
kubectl expose deployment app1 --port=80 --target-port=80 --type=ClusterIP
```

### app2 서비스 생성

```
kubectl expose deployment app2 --port=80 --target-port=80 --type=ClusterIP
```

서비스 확인:

```
kubectl get svc
```

예상 예시는 다음과 같음.

```
NAME         TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
app1         ClusterIP   10.100.10.11    <none>        80/TCP    1m
app2         ClusterIP   10.100.20.22    <none>        80/TCP    1m
kubernetes   ClusterIP   10.100.0.1      <none>        443/TCP   1d
```

### 왜 ClusterIP를 쓰는가

Ingress는 보통 **클러스터 내부 Service 앞단의 L7 라우터** 역할을 함.

즉, 외부 공개는 Ingress(ALB)가 담당하고, 실제 백엔드는 내부 `ClusterIP` 서비스가 담당함.

---

## 8. 3단계 - Ingress 리소스 생성

이제 Ingress를 생성함.

아래 내용을 `alb-ingress.yaml` 파일로 저장함.

```
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
spec:
  ingressClassName: alb
  rules:
    - http:
        paths:
          - path: /app1
            pathType: Prefix
            backend:
              service:
                name: app1
                port:
                  number: 80
          - path: /app2
            pathType: Prefix
            backend:
              service:
                name: app2
                port:
                  number: 80
```

CMD 기준으로 파일을 만들 때는 메모장을 사용하면 편함.

```
notepad alb-ingress.yaml
```

저장 후 적용함.

```
kubectl apply -f alb-ingress.yaml
```

---

## 9. Ingress YAML 상세 설명

### `kind: Ingress`

Ingress 리소스를 생성함.

### `alb.ingress.kubernetes.io/scheme: internet-facing`

외부 인터넷에서 접근 가능한 ALB를 생성하라는 의미임.

내부 전용으로 만들고 싶으면 `internal`을 사용함. AWS는 ALB scheme 설정으로 외부형과 내부형을 구분할 수 있다고 설명함.

### `alb.ingress.kubernetes.io/target-type: ip`

ALB 대상 그룹이 인스턴스가 아니라 **Pod IP**를 대상으로 라우팅하도록 지정함.

EKS에서는 `ip` 모드가 많이 사용됨. AWS Load Balancer Controller 문서도 `target-type`으로 `instance`와 `ip`를 지원하며, `ip` 모드는 Pod를 직접 대상으로 등록한다고 설명함.

### `ingressClassName: alb`

이 Ingress를 어떤 Ingress Controller가 처리할지 지정함.

즉, AWS Load Balancer Controller가 이 Ingress를 처리하게 됨.

### `rules`

라우팅 규칙을 정의함.

### `/app1`, `/app2`

경로 기반 라우팅 예시임.

`/app1` 요청은 app1 서비스로, `/app2` 요청은 app2 서비스로 전달됨.

Kubernetes 공식 문서도 Ingress에서 path 기반 라우팅을 정의할 수 있다고 설명함. ([kubernetes.io](https://kubernetes.io/docs/concepts/services-networking/ingress/?utm_source=chatgpt.com))

---

## 10. 4단계 - Ingress 상태 확인

Ingress가 생성되었는지 확인함.

```
kubectl get ingress
```

예상 예시는 다음과 같음.

```
NAME          CLASS   HOSTS   ADDRESS                                                                    PORTS   AGE
app-ingress   alb     *       k8s-default-appingre-1234567890.ap-northeast-2.elb.amazonaws.com         80      2m
```

### 확인 포인트

* `CLASS`가 `alb`인지 확인

* `ADDRESS`가 생성되었는지 확인

* `ADDRESS`가 AWS ELB 도메인 형식인지 확인

처음에는 `ADDRESS`가 비어 있을 수 있음.

이 경우 잠시 기다렸다가 다시 확인함.

```
kubectl get ingress
```

AWS Load Balancer Controller는 Ingress 리소스를 기반으로 ALB를 프로비저닝하므로, AWS 쪽 리소스 생성 시간이 조금 걸릴 수 있음.

---

## 11. 5단계 - ALB 주소로 접속 테스트

`kubectl get ingress`에서 나온 ALB 주소를 확인한 후, CMD에서 `curl`로 접속 테스트를 수행함.

### app1 경로 테스트

```
curl http://ALB주소/app1
```

### app2 경로 테스트

```
curl http://ALB주소/app2
```

기본 nginx 페이지가 나오면 정상임.

다만 현재 app1, app2 둘 다 같은 nginx 이미지를 쓰므로, 응답 내용이 거의 같을 수 있음.

---

## 12. 6단계 - Ingress 상세 정보 확인

문제 해결과 학습을 위해 상세 정보도 확인함.

```
kubectl describe ingress app-ingress
```

이 명령을 통해 다음을 확인할 수 있음.

* Ingress rules

* Backend service 연결 정보

* 이벤트(Event)

* ALB 생성 관련 상태

### 특히 볼 항목

### Rules

어떤 경로가 어떤 서비스로 라우팅되는지 확인 가능함.

### Address

생성된 ALB 주소를 볼 수 있음.

### Events

ALB 생성 실패, 권한 오류, 서브넷 태그 오류 등이 있으면 여기서 단서를 찾을 수 있음.

---

## 13. AWS 콘솔에서 확인

* EC2 → Load Balancers

* EC2 → Target Groups

* ALB의 리스너 규칙

* Target Group에 등록된 대상

Ingress 리소스 하나가 AWS 쪽에서 어떤 리소스로 바뀌는지 확인할 수 있음.

즉,

* Ingress → ALB

* Path rule → Listener rule

* Service/Pod → Target Group 대상

AWS Load Balancer Controller는 Ingress와 Service에 대응하는 ALB 및 대상 그룹을 생성하고 관리함.

---

## 14. 실습 결과

### 14-1. Service와 Ingress는 역할이 다름

* Service는 내부 또는 단순 외부 공개용 네트워크 추상화임

* Ingress는 HTTP/HTTPS 기반 라우팅 정책을 정의함

### 14-2. Ingress 자체는 로드밸런서를 만들지 않음

Ingress는 규칙만 정의함.

실제로 ALB를 만들고 규칙을 적용하는 것은 AWS Load Balancer Controller임.

### 14-3. EKS에서는 Ingress가 AWS ALB와 직접 연결됨

이 점이 온프레미스와 매우 다름.

온프레미스에서는 Ingress Controller까지만 설치되는 경우가 많고, 외부 L7 장비는 별도 구성해야 하는 경우가 많음.

### 14-4. EKS는 Kubernetes L7 라우팅과 AWS 네트워크 서비스를 통합함

즉, EKS에서는 쿠버네티스 객체 하나가 실제 AWS 인프라 객체로 변환되는 경험을 할 수 있음.

---

## 15. 자주 발생하는 문제

### 15-1. `ADDRESS`가 계속 비어 있는 경우

가능한 원인은 다음과 같음.

* AWS Load Balancer Controller 미설치

* IAM 권한 부족

* 서브넷 태그 누락

* Ingress class 설정 오류

AWS는 컨트롤러 설치 전 IAM 정책, 서비스어카운트, 서브넷 태그가 필요하다고 안내함.

### 15-2. `kubectl describe ingress`에 에러 이벤트가 보이는 경우

이벤트를 보고 다음을 확인함.

* 권한 오류

* 대상 그룹 생성 실패

* 서브넷 자동 검색 실패

* 보안 그룹 문제

### 15-3. `/app1`, `/app2`가 기대대로 안 나뉘는 경우

다음 항목을 확인함.

* Service 이름 오타

* Service 포트 번호 오류

* path 설정 오류

* `pathType` 오류

---

## 16. 실습 후 정리 명령

실습이 끝나면 리소스를 삭제함.

```
kubectl delete ingress app-ingress
kubectl delete svc app1
kubectl delete svc app2
kubectl delete deployment app1
kubectl delete deployment app2
```

Ingress를 먼저 삭제하면 ALB 정리가 시작됨.

AWS 리소스 정리에는 약간의 시간이 걸릴 수 있음.

---