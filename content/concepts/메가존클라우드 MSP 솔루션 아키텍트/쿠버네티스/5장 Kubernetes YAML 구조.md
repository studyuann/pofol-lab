---
title: "5장 Kubernetes YAML 구조"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "쿠버네티스"]
is_public: true
draft: false
---

# 5장. Kubernetes YAML 구조

---

# 5-1. YAML

쿠버네티스에서 **YAML 파일**은 "내가 원하는 클러스터의 상태(Desired State)"를 정의하는 설계도와 같다. 쿠버네티스는 이 파일을 읽어 실제 상태(Current State)를 설계도와 똑같이 맞추려고 한다.  
  
Kubernetes는 명령어 기반 시스템이 아니라 **선언형(Declarative) 시스템**이다.

```
kubectl apply -f file.yaml
```

이 명령은 “이 파일에 적힌 상태로 클러스터를 맞춰라”는 의미다.

따라서 YAML 구조를 이해하지 못하면:

* 오류 분석이 어렵고

* 리소스 관계를 이해하기 힘들며

* 실무에서 문제 해결이 불가능해진다

---

# 5-2. 모든 리소스의 공통 최상위 구조

모든 Kubernetes 리소스는 동일한 4개 필드를 가진다.

```
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
spec:
  containers:
  - name: nginx
    image: nginx
```

---

## 🔹 4개 최상위 필드

| 필드 | 의미 |
| --- | --- |
| apiVersion | API 그룹과 버전 |
| kind | 생성할 리소스 종류 |
| metadata | 리소스 식별 정보 |
| spec | 원하는 상태 정의 |

이 구조는 모든 리소스에 동일하게 적용된다.

---

# 5-3. apiVersion

## 1️⃣ 의미

해당 리소스가 속한 API 그룹과 버전을 지정한다.

Kubernetes는 내부적으로 여러 API 그룹을 가진다.

---

## 2️⃣ 주요 apiVersion

| apiVersion | 사용 리소스 |
| --- | --- |
| v1 | Pod, Service, ConfigMap |
| apps/v1 | Deployment, StatefulSet |
| batch/v1 | Job, CronJob |
| networking.k8s.io/v1 | Ingress |

---

## 3️⃣ 실습: apiVersion 오류 확인

wrong.yaml 작성

```
apiVersion: v1
kind: Deployment
metadata:
  name: test
spec:
  replicas: 1
```

적용

```
kubectl apply -f wrong.yaml
```

오류 발생 이유:

* Deployment는 apps/v1 그룹에 속한다.

* API Server가 해당 버전에서 Deployment를 찾지 못한다.

---

# 5-4. kind

## 의미

생성할 리소스 종류를 지정한다.

예:

```
kind: Pod
kind: Deployment
kind: Service
```

API Server는 kind를 보고 내부 객체 타입을 결정한다.

---

# 5-5. metadata

리소스의 식별 및 분류 정보다.

```
metadata:
  name: web
  namespace: dev
  labels:
    app: web
    tier: frontend
  annotations:
    description: "frontend app"
```

---

## 1️⃣ name

* 네임스페이스 내에서 유일해야 한다.

* 동일 네임스페이스에 같은 이름 존재 불가.

* 소문자, 숫자, 하이픈만 사용.

---

## 2️⃣ namespace

지정하지 않으면 default 네임스페이스 사용.

현재 기본 namespace 확인:

```
kubectl config view --minify | grep namespace
```

---

## 3️⃣ labels (중요)

리소스를 선택하고 그룹화하는 기준이다.

```
labels:
  app: web
  version: v1
```

조회 실습:

```
kubectl get pods -l app=web
```

* l 옵션은 label selector 기능이다.

---

## 4️⃣ annotations

설명 목적의 메타데이터.

* selector로 사용 불가

* 긴 문자열 가능

* 배포 기록 등에 사용

---

# 5-6. spec

리소스의 실제 동작을 정의한다.

⚠ spec 내용은 리소스마다 다르다.

---

# 5-7. Pod spec 구조 분석

```
spec:
  containers:
  - name: web
    image: nginx
    ports:
    - containerPort: 80
    env:
    - name: ENV
      value: "prod"
    resources:
      requests:
        cpu: "100m"
        memory: "128Mi"
      limits:
        cpu: "500m"
        memory: "256Mi"
```

---

## 1️⃣ containers

Pod 내 실행할 컨테이너 목록.

* name: Pod 내부에서 유일

* image: 실행할 컨테이너 이미지

이미지 형식:

```
[registry]/[repository]:[tag]
```

---

## 2️⃣ ports

```
ports:
- containerPort: 80
```

의미:

* 컨테이너 내부에서 열려있는 포트

* Service에서 targetPort로 참조 가능

---

## 3️⃣ env

```
env:
- name: DB_HOST
  value: "mysql"
```

숫자도 반드시 문자열로 작성:

```
value: "8080"
```

YAML은 숫자를 자동 형변환할 수 있으므로 따옴표 권장.

---

## 4️⃣ resources

```
resources:
  requests:
    cpu: "100m"
  limits:
    cpu: "500m"
```

### requests

* 스케줄러가 노드를 선택할 때 참고

* 최소 보장 자원

### limits

* 절대 초과 불가 자원

* 초과 시:

메모리 → OOMKilled

CPU → throttling 발생

확인 실습:

```
kubectl describe pod <pod-name>
```

Events 항목에서 상태 확인 가능.

---

# 5-8. Deployment spec 구조

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-deploy
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: nginx
        image: nginx
```

---

## 1️⃣ replicas

유지할 Pod 개수.

```
replicas: 3
```

의미:

* Controller가 항상 3개 유지

* 1개 죽으면 자동 재생성

---

## 2️⃣ selector

관리 대상 Pod 선택 기준.

```
selector:
  matchLabels:
    app: web
```

이 값은 반드시 template.metadata.labels와 동일해야 한다.

---

## 3️⃣ template

실제 생성될 Pod 설계도.

구조는 Pod과 동일하다.

---

# 5-9. Service spec 구조

```
apiVersion: v1
kind: Service
metadata:
  name: web-svc
spec:
  type: ClusterIP
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8080
```

---

## 1️⃣ type

| 타입 | 설명 |
| --- | --- |
| ClusterIP | 내부 통신 |
| NodePort | 노드 포트로 외부 접근 |
| LoadBalancer | 클라우드 LB |

---

## 2️⃣ port vs targetPort

* port → Service 포트

* targetPort → Pod 내부 포트

트래픽 흐름:

```
Client → Service:port → Pod:targetPort
```

---

# 5-10. 다중 리소스 파일

```
---
apiVersion: apps/v1
kind: Deployment
...
---
apiVersion: v1
kind: Service
...
```

* -- 는 문서 구분자.

적용:

```
kubectl apply -f app.yaml
```

하나의 파일로 여러 리소스 생성 가능.

---

# 5-11. 자주 하는 실수

---

## 1️⃣ selector 불일치

```
selector:
  matchLabels:
    app: nginx

template:
  metadata:
    labels:
      app: web
```

결과:

* Deployment가 Pod을 관리하지 못함

* 자동 복구 동작하지 않음

---

## 2️⃣ apiVersion 오류

Deployment는 반드시:

```
apiVersion: apps/v1
```

---

## 3️⃣ 숫자 따옴표 누락

```
value: 8080      # 문제 발생 가능
value: "8080"    # 권장
```

---

## 4️⃣ 들여쓰기 오류

YAML은 들여쓰기 기반 문법이다.

```
spec:
  containers:
  - name: web
```

2칸 들여쓰기 권장.

---

# 5-12. 내부 동작 연결

YAML은 단순 설정 파일이 아니다.

동작 흐름:

```
1. kubectl apply
2. API Server 저장
3. etcd 기록
4. Controller 감지
5. 현재 상태와 비교
6. 차이 수정
```

즉 YAML은 “Desired State 선언서”다.

---

# 5-13. 실습 과제

1. selector를 일부러 다르게 작성 후 동작 확인

2. apiVersion을 잘못 작성 후 오류 확인

3. Deployment + Service 하나의 파일로 작성 후 적용

---

# 5-14. 핵심 정리

```
1. 모든 리소스는 apiVersion, kind, metadata, spec 구조
2. spec은 리소스마다 다르다
3. labels는 선택의 기준이다
4. selector는 반드시 template.labels와 일치
5. YAML 이해는 Kubernetes의 핵심이다
```

---