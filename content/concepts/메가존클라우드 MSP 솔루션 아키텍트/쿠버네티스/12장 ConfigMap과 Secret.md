---
title: "12장 ConfigMap과 Secret"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "쿠버네티스"]
is_public: true
draft: false
---

# 12장. ConfigMap과 Secret

## 1. ConfigMap과 Secret의 개념

---

### 왜 필요한가?

Kubernetes에서 **ConfigMap**과 **Secret**은 애플리케이션 코드와 설정 데이터를 분리하기 위해 사용하는 아주 중요한 리소스들다. 쉽게 말해, 소스코드를 수정하지 않고도 환경에 따라 설정을 바꿀 수 있게 해주는 저장소 역할을 한다.  
  
**ConfigMap vs Secret**

| 항목 | ConfigMap | Secret |
| --- | --- | --- |
| **목적** | 일반 설정 데이터 저장 | 민감한 데이터 저장 |
| **데이터 형식** | 평문(Plain text) | Base64로 인코딩 |
| **사용 예** | 로그 레벨, 포트 번호 | 비밀번호, API 키, 토큰 |
| **보안** | 낮음 (암호화 없음) | 조금 높음 (암호화 권장) |
| **크기 제한** | 1MB | 1MB |

---

## 2. ConfigMap

### 2.1 ConfigMap이란?

ConfigMap은 **설정 데이터를 키-값 쌍으로 저장**하는 쿠버네티스 리소스.

**특징:**

* 데이터가 평문으로 저장

* 환경변수, 설정 파일로 Pod에 전달

* 수정 후 Pod을 재시작해야 반영

* 재배포 없이 설정 변경 가능

### 2.2 ConfigMap 생성 방법

### 방법 1: YAML로 생성 : configmap.yaml

```
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: 
data:
  LOG_LEVEL: "info"
  DATABASE_URL: "postgres://db.default.svc.cluster.local:5432"
  CACHE_TTL: "3600"
  MAX_CONNECTIONS: "100"
```

**설명:**

* `data` 섹션에 키-값 쌍 저장

* 모든 값이 문자열 형식

* 숫자도 따옴표로 문자열화

```
kubectl apply -f configmap.yaml
```

### 방법 2: kubectl 명령어로 생성

```
# 1. 직접 입력
kubectl create configmap app-config \
  --from-literal=LOG_LEVEL=info \
  --from-literal=DATABASE_URL=postgres://db:5432 \
  --from-literal=CACHE_TTL=3600

# 2. 파일에서 생성
kubectl create configmap app-config --from-file=config.properties

# 3. 디렉토리 파일들로 생성
kubectl create configmap app-config --from-file=/etc/config/
```

### 방법 3: 멀티라인 데이터 (파일 형식)

```
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-config
data:
  nginx.conf: |
    server {
      listen 80;
      server_name example.com;

      location / {
        proxy_pass http://backend:8080;
      }
    }

  default.conf: |
    upstream backend {
      server backend1:8080;
      server backend2:8080;
    }
```

**설명:**

* `|` 기호로 여러 줄의 파일 내용 저장

* 설정 파일 전체를 ConfigMap에 보관 가능

### 2.3 ConfigMap 조회

```
# ConfigMap 목록 조회
kubectl get configmap

# 상세 정보 조회
kubectl describe configmap app-config

# YAML 형식으로 조회
kubectl get configmap app-config -o yaml

# 특정 값 조회
kubectl get configmap app-config -o jsonpath='{.data.LOG_LEVEL}'
```

### 2.4 Pod에서 ConfigMap 사용

### 방식 1: 환경변수로 사용

```
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
spec:
  containers:
  - name: app
    image: myapp:latest
    env:
    # 직접 환경변수 설정
    - name: LOG_LEVEL
      valueFrom:
        configMapKeyRef:
          name: app-config        # ConfigMap 이름
          key: LOG_LEVEL          # ConfigMap의 키

    # 여러 환경변수를 한 번에 로드
    envFrom:
    - configMapRef:
        name: app-config          # app-config의 모든 키-값이 환경변수가 됨
```

**동작:**

```
# app-config ConfigMap의 내용
LOG_LEVEL: "info"
DATABASE_URL: "postgres://db:5432"
CACHE_TTL: "3600"

# Pod 내 환경변수
$LOG_LEVEL = "info"
$DATABASE_URL = "postgres://db:5432"
$CACHE_TTL = "3600"
```

**차이점:**

* `valueFrom`: 특정 키만 선택

* `envFrom`: ConfigMap의 모든 키-값 사용

### 방식 2: 파일로 마운트

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:latest
        ports:
        - containerPort: 80
        volumeMounts:
        - name: config-volume
          mountPath: /etc/nginx/conf.d  # 파일들이 위치할 폴더
          readOnly: true
      volumes:
      - name: config-volume
        configMap:
          name: nginx-config
          items:
          - key: nginx.conf       # configmap의 key
            path: custom.conf     # pod내에 생성될 파일
       
          # items를 생략하면 data 아래의 모든 key가 파일로 생성된다.
```

---

### 🔍 설정 포인트 및 결과

1. `items` **생략**: `volumes` 섹션에서 `items`를 따로 적지 않았다. 이렇게 하면 `data` 아래에 있는 `nginx.conf`와 `default.conf`가 각각 파일명으로 자동 생성된다.

2. `mountPath` **위치**:
   * 컨테이너 내부의 `/etc/nginx/conf.d/` 경로를 확인해보면 아래와 같이 두 개의 파일이 생겨난다.
   * `/etc/nginx/conf.d/nginx.conf`
   * `/etc/nginx/conf.d/default.conf`

---

### 실시간 반영 확인하기

ConfigMap을 사용하면 파드를 재시작하지 않고도 설정을 바꿀 수 있다는 장점이 있다.

1. `kubectl edit cm nginx-config`로 내용을 수정하고 저장한다.

2. 잠시 기다리면(약 10~60초) 컨테이너 내부의 파일 내용이 자동으로 업데이트된다.

3. 단, Nginx는 설정이 바뀌어도 스스로 다시 읽지 않으므로 아래 명령어로 설정을 리로드해줘야 한다.

   ```
   kubectl exec -it <파드명> -- nginx -s reload
   ```

### 2.5 ConfigMap 수정 및 삭제

```
# ConfigMap 수정
kubectl edit configmap app-config

# ConfigMap 삭제
kubectl delete configmap app-config

# 여러 ConfigMap 삭제
kubectl delete configmap app-config db-config cache-config
```

**주의:**  
ConfigMap을 수정해도 이미 실행 중인 Pod에는 반영되지 않음.  
Pod을 재시작해야 새 설정이 적용됨.

```
# Pod 재시작으로 새 설정 적용
kubectl rollout restart deployment/myapp

# 특정 Pod만 재시작
kubectl delete pod <pod-name>
```

---

## 3. Secret

### 3.1 Secret이란?

Secret은 **민감한 데이터를 저장**하는 쿠버네티스 리소스.

**특징:**

* Base64로 인코딩 (암호화 아님, 단순 인코딩)

* ConfigMap과 유사하지만 민감한 데이터 용도

* etcd에 암호화되어 저장하도록 설정 가능 (고급)

* 최대 1MB 크기 제한

**Secret 종류:**

| Secret 타입 | 용도 | 예시 |
| --- | --- | --- |
| `Opaque` (기본값) | 일반 비밀 데이터 | 비밀번호, API 키 |
| `kubernetes.io/basic-auth` | 기본 인증 | username, password |
| `kubernetes.io/ssh-auth` | SSH 인증 | SSH 개인키 |
| `kubernetes.io/dockercfg` | Docker 설정 | Docker 레지스트리 인증 |
| `kubernetes.io/service-account-token` | 서비스 어카운트 토큰 | (자동 생성) |

### 3.2 Secret 생성 방법

### 방법 1: YAML로 생성 (Base64 인코딩)

```
# 먼저 데이터를 Base64로 인코딩
echo -n "admin" | base64
# 출력: YWRtaW4=

echo -n "secretpassword123" | base64
# 출력: c2VjcmV0cGFzc3dvcmQxMjM=
```

```
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
data:
  username: YWRtaW4=                    # base64로 인코딩된 "admin"
  password: c2VjcmV0cGFzc3dvcmQxMjM=   # base64로 인코딩된 "secretpassword123"
```

### 방법 2: 평문으로 작성 (권장)

```
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
stringData:                    # 평문으로 작성 (자동 인코딩됨)
  username: admin
  password: secretpassword123
```

**장점:** 평문으로 작성해도 쿠버네티스가 자동으로 Base64로 인코딩합니다.

### 3.3 Secret 조회

```
# Secret 목록 조회
kubectl get secret

# 상세 정보 조회 (Base64로 보임)
kubectl describe secret db-secret

# YAML 형식으로 조회 (Base64로 인코딩된 상태)
kubectl get secret db-secret -o yaml

# 디코딩해서 실제 값 조회
kubectl get secret db-secret -o jsonpath='{.data.password}' | base64 -d

# 모든 Secret 값 디코딩해서 보기
kubectl get secret db-secret -o go-template='{{range $k,$v := .data}}{{$k}}: {{$v|base64decode}}{{"\n"}}{{end}}'
```

### 3.4 Pod에서 Secret 사용

### 방식 1: 환경변수로 사용

```
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
spec:
  containers:
  - name: app
    image: alpine
    command: ["sleep", "3600"]  # 1시간 유지
    env:
    # 특정 Secret 키를 환경변수로
    - name: DB_USERNAME
      valueFrom:
        secretKeyRef:
          name: db-secret         # Secret 이름
          key: username           # Secret의 키

    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: db-secret
          key: password

    # 모든 Secret 값을 환경변수로 로드
    envFrom:
    - secretRef:
        name: db-secret
```

**동작:**

```
# db-secret Secret의 내용 (Base64 디코딩됨)
username: "admin"
password: "secretpassword123"

# Pod 내 환경변수
$DB_USERNAME = "admin"
$DB_PASSWORD = "secretpassword123"
```

### 방식 2: 파일로 마운트

```
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
spec:
  containers:
  - name: app
    image: alpine
    command: ["sleep", "3600"]  # 1시간 유지
    volumeMounts:
    - name: secret-volume
      mountPath: /etc/secrets/db
      readOnly: true
  volumes:
  - name: secret-volume
    secret:
      secretName: db-secret
      defaultMode: 0400
```

**동작:**

```
# 컨테이너 내부
/etc/secrets/db/username      # "admin" 내용
/etc/secrets/db/password      # "secretpassword123" 내용

# 파일 읽기
cat /etc/secrets/db/username
# 출력: admin
```

---