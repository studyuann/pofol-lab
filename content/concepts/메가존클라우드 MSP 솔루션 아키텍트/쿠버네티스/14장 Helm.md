---
title: "14장 Helm"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "쿠버네티스"]
is_public: true
draft: false
---

# 14장. Helm

## 0. 학습 목표

* Helm의 목적과 구성요소(Chart, Release, Repository)를 이해한다

* Helm으로 애플리케이션을 설치/업그레이드/롤백/삭제한다

* values.yaml로 설정을 오버라이드한다

* 네임스페이스 분리 배포를 수행한다

* (선택) LoadBalancer(MetalLB) 환경에서 외부 접속을 확인한다

---

## 1. Helm 개요

### 1.1 Helm이 필요한 이유

쿠버네티스에서 애플리케이션을 배포하려면 보통 Deployment, Service, ConfigMap, Secret, Ingress 등 여러 리소스를 작성해야 한다.

리소스가 늘어나면 다음 문제가 발생한다.

* YAML 파일이 너무 많아짐

* 환경별(dev/stage/prod) 설정 값만 바꿔야 하는데 YAML을 복사해서 관리하게 됨

* 업그레이드/롤백 시점 관리가 어려워짐

* 배포 표준화가 깨짐

Helm은 위 문제를 “패키지(Chart) + 변수(values) + 버전(release revision)”으로 해결한다.

---

## 2. Helm 핵심 용어

### 2.1 Chart

쿠버네티스 매니페스트 템플릿 묶음이다.

* `templates/` : Deployment/Service 등의 템플릿 YAML이 들어간다

* `values.yaml` : 템플릿에 주입할 기본 변수 값이다

* `Chart.yaml` : 차트 메타정보(이름/버전/설명 등)이다

### 2.2 Release

차트를 특정 클러스터/네임스페이스에 설치한 “실제 배포 인스턴스”이다.

같은 Chart라도 Release 이름이 다르면 서로 다른 배포로 관리된다.

예시:

* chart: bitnami/nginx

* release: `nginx-dev`, `nginx-prod`

### 2.3 Repository

차트 저장소이다. apt의 패키지 저장소와 같은 개념이다.

---

## 3. Helm 설치 및 기본 확인

### 3.1 설치 확인

```
helm version
```

* Helm 클라이언트가 정상 설치되었는지 확인하는 명령이다

* 버전 정보가 출력되면 설치 완료 상태이다

### 3.2 kubectl 연동 확인

```
kubectl get nodes
```

* Helm은 쿠버네티스 API를 통해 리소스를 생성한다

* kubectl이 정상 동작해야 Helm도 정상 동작한다

---

## 4. Helm Repository 관리 실습

### 4.1 bitnami 저장소 추가

```
helm repo add bitnami https://charts.bitnami.com/bitnami
```

* `repo add` : 원격 차트 저장소를 로컬 Helm에 등록한다

* `bitnami` : 저장소 별칭(alias)이다. 이후 `bitnami/nginx` 형태로 참조한다

* URL : 실제 차트 인덱스가 있는 저장소 주소다

### 4.2 저장소 목록 확인

```
helm repo list
```

* 로컬에 등록된 repo 목록을 확인한다

### 4.3 차트 목록 업데이트

```
helm repo update
```

* repo의 index 정보를 최신으로 갱신한다

* 새로 올라온 차트 버전이 보이게 된다

### 4.4 차트 검색

```
helm search repo nginx
```

* repo에 있는 차트를 키워드로 검색한다

* `bitnami/nginx` 같은 결과를 확인한다

---

## 5. 네임스페이스 분리 배포 실습

### 5.1 네임스페이스 생성

```
kubectl create namespace nginx
```

* 네임스페이스는 쿠버네티스 리소스를 논리적으로 분리하는 단위이다

* 같은 이름의 리소스라도 네임스페이스가 다르면 충돌하지 않는다

### 5.2 (선택) 현재 컨텍스트 기본 네임스페이스 변경

```
kubectl config set-context --current --namespace=nginx
```

* `set-context` : kubeconfig의 context 설정을 변경한다

* `--current` : 현재 사용 중인 context를 대상으로 한다

* `--namespace=nginx` : 이후 kubectl 명령의 기본 namespace가 nginx가 된다

* Helm은 kubectl 기본 namespace와 “별개로” `-n` 옵션으로 namespace를 지정하는 습관이 좋다

---

## 6. Helm으로 Nginx 설치 실습

### 6.1 기본 설치 (namespace 지정)

```
helm install nginx bitnami/nginx -n nginx --create-namespace
```

* `install` : 차트를 설치한다

* `nginx` : release 이름이다(사용자가 정한다)

* `bitnami/nginx` : repo/chart 이름이다

* `-n nginx` : 설치할 네임스페이스를 지정한다

* `--create-namespace` : 네임스페이스가 없으면 자동 생성한다

### 6.2 설치 확인

```
helm list -n nginx
```

* 지정한 namespace의 release 목록을 본다

리소스 확인:

```
kubectl get pod -n nginx -o wide
kubectl get svc -n nginx
kubectl get endpoints -n nginx
```

* Pod가 Running인지 확인한다

* Service 타입과 ClusterIP/External-IP 상태를 확인한다

* Endpoints가 비어 있으면 selector/label 매칭이 깨졌을 가능성이 크다

---

## 7. values.yaml 오버라이드 실습

### 7.1 현재 설치된 release의 values 확인

```
helm get values nginx -n nginx
```

* 설치 시 실제로 적용된 values(사용자가 오버라이드한 값)를 보여준다

전체 매니페스트 확인:

```
helm get manifest nginx -n nginx
```

* 템플릿이 렌더링된 최종 YAML을 확인한다

* “Helm이 실제로 무엇을 생성했는지” 추적할 때 사용한다

### 7.2 차트 기본 values.yaml 확인

```
helm show values bitnami/nginx > values-nginx-default.yaml
```

* `show values` : 차트의 기본 values.yaml을 출력한다

* `>` : 표준출력을 파일로 저장한다(리다이렉션)

### 7.3 사용자 values 파일 작성

예: `my-values.yaml`

```
service:
  type: LoadBalancer

replicaCount: 2
```

* `service.type: LoadBalancer` 로 바꾸면 MetalLB 같은 LB 환경에서 External-IP(VIP)가 할당된다

* `replicaCount`로 파드 개수를 조절한다

### 7.4 upgrade로 적용

```
helm upgrade nginx bitnami/nginx -n nginx -f my-values.yaml
```

* `upgrade` : 기존 release를 새로운 설정으로 업데이트한다

* `f my-values.yaml` : values 오버라이드 파일을 적용한다

* `upgrade`는 “차트 재설치”가 아니라 “release revision 증가 + 변경 반영”이다

변경 확인:

```
helm history nginx -n nginx
kubectl get pod -n nginx
kubectl get svc -n nginx
```

* history에 revision이 증가했는지 확인한다

* 파드 재생성/스케일 변경 여부를 확인한다

* 서비스 타입/External-IP 변화를 확인한다

---

## 8. 롤백 실습

### 8.1 revision 확인

```
helm history nginx -n nginx
```

예시로 revision 1, 2가 있다고 가정한다.

### 8.2 롤백 실행

```
helm rollback nginx 1 -n nginx
```

* `rollback` : 특정 revision 상태로 되돌린다

* `1` : 되돌릴 revision 번호다

* 롤백 후에도 revision이 하나 더 증가한다(롤백 자체가 새 revision이 됨)

검증:

```
helm history nginx -n nginx
kubectl get pod -n nginx
kubectl get svc -n nginx
```

---

## 9. 삭제 실습

### 9.1 release 삭제

```
helm uninstall nginx -n nginx
```

* 해당 release가 생성했던 리소스를 제거한다

* 네임스페이스는 자동 삭제되지 않는다

### 9.2 namespace까지 정리(선택)

```
kubectl delete namespace nginx
```

* namespace 삭제 시 내부 리소스가 전부 삭제된다

* 실습 후 환경 정리에 사용한다

---

## 10. (선택) LoadBalancer(MetalLB)에서 외부 접속 확인 흐름

> LoadBalancer가 동작하려면 MetalLB가 설치되어 있어야 한다.

서비스 확인:

```
kubectl get svc -n nginx -o wide
```

* `EXTERNAL-IP`가 할당되었는지 확인한다 (예: `192.168.80.200`)

* NodePort도 함께 열리는 경우가 많다

외부(클러스터 외부 PC)에서 접속:

```
curl -v http://<EXTERNAL-IP>/
```

---

## 11. 트러블슈팅 체크리스트

### 11.1 ClusterIP 접속이 안 됨

1. Endpoint 확인

```
kubectl get endpoints -n nginx
```

1. PodIP 직접 접근이 되는지 확인(노드에서)

```
curl -v http://<PodIP>:8080/
```

* PodIP도 안 되면 CNI(Flannel/Calico) 문제 가능성 큼

* PodIP는 되는데 ClusterIP만 안 되면 kube-proxy/iptables/IPVS 문제 가능성 큼

### 11.2 Helm release가 왜 실패했는지 확인

```
helm status nginx -n nginx
kubectl describe pod -n nginx
kubectl events -n nginx --sort-by='.lastTimestamp'
```

---

## 12. 실습 과제

1. `nginx-dev`, `nginx-prod` 두 release를 서로 다른 namespace에 설치한다

2. dev는 replica 1, prod는 replica 3으로 구성한다

3. prod에만 LoadBalancer를 적용한다

4. prod를 revision 1로 롤백한다