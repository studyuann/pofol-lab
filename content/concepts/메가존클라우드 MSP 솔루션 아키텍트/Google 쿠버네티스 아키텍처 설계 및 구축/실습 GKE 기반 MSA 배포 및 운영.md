---
title: "실습 GKE 기반 MSA 배포 및 운영"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Google 쿠버네티스 아키텍처 설계 및 구축"]
is_public: true
draft: false
---

# 실습. GKE 기반 MSA 배포 및 운영

---

## 0. 실습 목표

* GKE 클러스터에 마이크로서비스 애플리케이션을 배포함

* 서비스별 Pod, Service, Deployment 상태를 확인함

* 특정 서비스만 중단했을 때 영향 범위를 확인함

* 특정 서비스만 확장하여 독립 확장을 확인함

* 특정 서비스만 롤링 재시작하고 롤백 흐름을 확인함

* 서비스 이름 기반 내부 통신 구조를 확인함

---

# 1. 실습 개요

**Online Boutique** 애플리케이션을 GKE에 배포하고, 배포 이후 다음 4가지를 직접 확인한다.

* 서비스가 여러 개로 분리되어 배포되는 구조

* 일부 서비스만 장애를 내도 전체가 완전히 중단되지 않는 구조

* 필요한 서비스만 따로 확장 가능한 구조

* 특정 서비스만 업데이트·복구 가능한 구조

즉, 이번 실습의 핵심은 **MSA 운영 특성을 Kubernetes 위에서 관찰하는 것**이다.

---

# 2. 클러스터 연결 확인

실습 대상 클러스터에 현재 `kubectl`이 연결되어 있는지 확인한다.

```
export REGION=asia-northeast3
export CLUSTER_NAME=이니셜-std-cluster-1

gcloud container clusters get-credentials $CLUSTER_NAME \
  --region $REGION
```

## 확인

```
kubectl config current-context
kubectl get nodes
```

## 확인 포인트

* 현재 컨텍스트가 실습 대상 클러스터인지 확인함

* 노드가 `Ready` 상태인지 확인함

---

# 3. 샘플 애플리케이션 받기

```
git clone --depth 1 https://github.com/GoogleCloudPlatform/microservices-demo.git
cd microservices-demo
```

## 확인

```
ls
```

다음 디렉터리나 파일이 보이면 정상이다.

* `release`

* `src`

* `README.md`

---

# 4. 애플리케이션 배포

## 4-1. 전체 매니페스트 적용

```
kubectl apply -f ./release/kubernetes-manifests.yaml
```

## 확인

```
kubectl get pods
```

처음에는 일부 Pod가 `Pending`, `ContainerCreating` 상태일 수 있다.

조금 지나 대부분 `Running`으로 바뀌면 정상이다.

실시간으로 보려면 다음 명령을 사용한다.

```
kubectl get pods -w
```

## 관찰 포인트

다음과 같은 서비스 Pod가 생성되는지 확인한다.

* `frontend`

* `cartservice`

* `checkoutservice`

* `currencyservice`

* `productcatalogservice`

* `recommendationservice`

* `paymentservice`

* `shippingservice`

* `emailservice`

* `adservice`

* `redis-cart`

---

# 5. 배포된 구성 확인

## 5-1. Deployment 확인

```
kubectl get deployments
```

## 확인 포인트

* 각 서비스가 개별 Deployment로 배포되었는지 확인함

* `READY`, `UP-TO-DATE`, `AVAILABLE` 값이 정상인지 확인함

예를 들어 대부분 `1/1`이면 정상이다.

---

## 5-2. Service 확인

```
kubectl get svc
```

## 확인 포인트

* 각 마이크로서비스 앞단에 Service가 존재하는지 확인함

* 외부 노출용 서비스와 내부 통신용 서비스를 구분해서 봄

* `frontend-external` 서비스가 외부 노출용인지 확인함

---

## 5-3. Pod 라벨 기준 조회

```
kubectl get pods --show-labels
```

## 관찰 포인트

* 서비스별 Pod에 어떤 라벨이 붙어 있는지 확인함

* 이후 특정 서비스만 조회할 때 라벨 셀렉터를 사용함

예:

```
kubectl get pods -l app=frontend
kubectl get pods -l app=recommendationservice
```

**서비스 단위로 운영 대상을 좁혀서 보려면 라벨 기반 조회가 중요**하다.

---

# 6. 외부 접속 확인

## 6-1. 외부 서비스 확인

```
kubectl get service frontend-external
```

## 확인 포인트

* `TYPE`이 `LoadBalancer`인지 확인함

* `EXTERNAL-IP`가 할당되었는지 확인함

예시:

```
NAME                TYPE           CLUSTER-IP      EXTERNAL-IP     PORT(S)        AGE
frontend-external   LoadBalancer   34.x.x.x        35.x.x.x        80:xxxxx/TCP   2m
```

`EXTERNAL-IP`가 `pending`이면 조금 더 기다린다.

---

## 6-2. 외부 IP 추출

```
kubectl get service frontend-external -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

출력된 IP로 브라우저 접속한다.

```
http://외부IP
```

---

# 7. 애플리케이션 동작 확인

브라우저에서 다음 동작을 수행한다.

1. 메인 페이지 접속

2. 상품 목록 확인

3. 상품 상세 페이지 이동

4. 장바구니 추가

5. 장바구니 화면 확인

6. 체크아웃 화면 진입

## 관찰 포인트

* 여러 기능이 하나의 애플리케이션처럼 보이지만 실제로는 여러 서비스 호출 결과가 합쳐진 화면이라는 점을 인식함

* 이후 특정 서비스만 중단하면 어떤 기능이 영향을 받는지 비교할 준비를 함

---

# 8. 서비스 상세 확인

## 8-1. frontend Service 상세

```
kubectl describe svc frontend
```

## 확인 포인트

다음 항목만 집중해서 본다.

* `Selector`

* `Endpoints`

* `Port`

### 해석

* `Selector` : 어떤 Pod들을 대상으로 삼는지

* `Endpoints` : 현재 실제 연결 중인 Pod IP와 포트가 무엇인지

* `Port` : 이 Service가 내부적으로 제공하는 포트가 무엇인지

즉, **frontend 서비스가 실제 어느 Pod로 연결되는지 확인**할 수 있다.

---

## 8-2. frontend Deployment 상세

```
kubectl describe deployment frontend
```

## 확인 포인트

* 현재 이미지

* replica 수

* 이벤트 내역

**현재 frontend가 어떤 상태로 실행 중인지 확인하는 운영 점검**할 수 있다.

---

# 9. 로그 확인

## 9-1. frontend 로그 확인

```
kubectl logs deployment/frontend
```

## 9-2. checkoutservice 로그 확인

```
kubectl logs deployment/checkoutservice
```

## 9-3. recommendationservice 로그 확인

```
kubectl logs deployment/recommendationservice
```

## 실습 방법

한쪽 터미널에서 로그를 보고, 브라우저에서 상품 조회나 장바구니 추가를 반복한다.

## 관찰 포인트

* 사용자 동작에 따라 어떤 서비스 로그가 반응하는지 확인함

* 전체 앱이 아니라 서비스 단위로 관찰해야 한다는 점을 확인함

필요하면 다음처럼 실시간 추적도 가능하다.

```
kubectl logs -f deployment/frontend
kubectl logs -f deployment/checkoutservice
```

---

# 10. 장애 주입 실습

이번 단계의 핵심은

**특정 기능 서비스만 중단했을 때 전체가 어떻게 반응하는지 확인하는 것**이다.

---

## 10-1. recommendationservice 중단

```
kubectl scale deployment recommendationservice --replicas=0
```

## 확인

```
kubectl get pods
kubectl get deployment recommendationservice
```

또는 서비스만 좁혀서 본다.

```
kubectl get pods -l app=recommendationservice
```

## 브라우저 확인

상품 상세 페이지나 메인 화면을 다시 확인한다.

## 관찰 포인트

* 추천 상품 영역이 비정상 동작하거나 비어 있을 수 있음

* 하지만 전체 쇼핑몰이 완전히 죽지 않을 수 있음

* 즉, 일부 서비스 장애가 전체 장애로 바로 이어지지 않음을 확인함

**장애 격리**, **부분 실패 허용**, **서비스 분리 운영**이MSA로 구현하는 이유이다.

---

## 10-2. recommendationservice 복구

```
kubectl scale deployment recommendationservice --replicas=1
```

## 확인

```
kubectl get pods -l app=recommendationservice
```

새 Pod가 `Running`이 되면 브라우저를 새로고침해서 추천 기능이 회복되는지 확인한다.

---

# 11. 독립 확장 실습

이번에는 전체가 아니라 특정 서비스만 확장한다.

## 11-1. frontend 확장

```
kubectl scale deployment frontend --replicas=3
```

## 확인

```
kubectl get pods -l app=frontend
kubectl get deployment frontend
```

## 관찰 포인트

* frontend Pod가 여러 개로 증가함

* 사용자는 여전히 동일한 `frontend-external` 주소로 접속함

* 외부 진입점은 같지만 내부 실행 인스턴스 수만 늘어남

즉, 트래픽 증가가 있다고 해서 전체 서비스를 모두 늘리는 것이 아니라

**필요한 서비스만 선택적으로 확장**할 수 있다.

---

## 11-2. 다시 원래 상태로 축소

```
kubectl scale deployment frontend --replicas=1
```

## 확인

```
kubectl get pods -l app=frontend
```

---

# 12. 롤링 재시작 및 배포 상태 확인

이번 단계에서는 특정 서비스만 재배포 흐름으로 다뤄본다.

## 12-1. 배포 이력 확인

```
kubectl rollout history deployment/frontend
```

## 12-2. 현재 배포 상태 확인

```
kubectl rollout status deployment/frontend
```

## 12-3. 롤링 재시작

```
kubectl rollout restart deployment/frontend
```

## 확인

```
kubectl rollout status deployment/frontend
kubectl get pods -l app=frontend -w
```

## 관찰 포인트

* 기존 Pod가 한 번에 모두 종료되지 않음

* 새 Pod가 순차적으로 준비되면서 교체됨

* frontend만 재시작되며 다른 서비스에는 직접 영향이 없음

이 단계에서는 “서비스 전체 재배포”가 아니라

**특정 서비스 단위 운영**이 가능하다는 점을 강조하면 좋다.

---

# 13. 롤백 흐름 확인

```
kubectl rollout undo deployment/frontend
kubectl rollout undo deployment/frontend --to-revision=2 // 특정 revision으로 롤백
```

## 확인

```
kubectl rollout history deployment/frontend
kubectl rollout status deployment/frontend
```

## 관찰 포인트

* 문제가 생긴 서비스만 되돌릴 수 있음

* 전체 애플리케이션을 한꺼번에 롤백하는 구조가 아님

* MSA 운영에서는 부분 롤백이 가능하다는 점이 중요함

---

# 14. 내부 DNS 기반 서비스 통신 확인

서비스 이름으로 통신하는 구조를 직접 확인한다.

## 14-1. 임시 디버그 Pod 실행

```
kubectl run debug-shell --rm -it --image=busybox -- sh
```

## 14-2. 서비스 이름 조회

Pod 내부 셸에서 다음 명령을 실행한다.

```
nslookup frontend
nslookup cartservice
nslookup productcatalogservice
nslookup recommendationservice
```

## 관찰 포인트

* 서비스 이름이 내부 클러스터 DNS로 해석되는지 확인함

* 애플리케이션이 Pod IP를 직접 바라보지 않아도 된다는 점을 확인함

필요하면 다음도 시도할 수 있다.

```
wget -qO- http://frontend
```

셸 종료:

```
exit
```

---

# 15. 추가 명령

## 전체 리소스 한 번에 보기

```
kubectl get all
```

## 특정 서비스 Pod만 보기

```
kubectl get pods -l app=checkoutservice
kubectl get pods -l app=cartservice
```

## 이벤트 확인

```
kubectl get events --sort-by=.metadata.creationTimestamp
```

## 특정 Pod 상세 보기

```
kubectl describe pod <POD_NAME>
```

---

# 16. 실습 정리

이번 실습에서 확인한 핵심은 다음과 같다.

* 애플리케이션이 여러 서비스로 나뉘어 독립 배포됨

* 특정 서비스만 장애를 내도 전체가 항상 같이 죽지는 않음

* 필요한 서비스만 따로 확장할 수 있음

* 필요한 서비스만 따로 재시작·롤백할 수 있음

* 서비스 이름 기반 내부 통신이 가능함

즉, Kubernetes는 단순 컨테이너 실행 도구가 아니라 **마이크로서비스 운영을 위한 실행 플랫폼** 역할을 한다고 볼 수 있다.

---

# 17. 실습 종료

실습이 끝나면 사용한 애플리케이션 리소스를 정리한다.

## 애플리케이션만 삭제

```
kubectl delete -f ./release/kubernetes-manifests.yaml
```

## 확인

```
kubectl get pods
kubectl get svc
```

---