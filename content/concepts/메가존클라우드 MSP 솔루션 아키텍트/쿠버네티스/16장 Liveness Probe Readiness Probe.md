---
title: "16장 Liveness Probe Readiness Probe"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "쿠버네티스"]
is_public: true
draft: false
---

# 16장. Liveness Probe / Readiness Probe

쿠버네티스에서 Pod가 **Running**이라고 해서 서비스가 정상이라는 보장은 없음.

프로세스는 살아있는데 응답이 멈추는 경우(Deadlock), 초기화가 끝나지 않았는데 트래픽이 들어오는 경우, 특정 포트는 열렸지만 실제 기능은 망가진 경우가 흔함.

이를 자동으로 감지/복구/차단하기 위해 **Probe(헬스체크)** 를 사용함.

---

# 1. Probe가 해결하는 운영 문제

1. 프로세스가 멈췄는데 Pod는 Running으로 유지됨

2. 앱이 초기화 중인데 Service가 트래픽을 전달함

3. DB 장애로 기능이 불능인데도 트래픽이 계속 유입됨

4. 포트는 열려있지만 내부 로직이 실패하는 상태가 계속됨

Probe를 쓰면 다음이 가능함.

* **Readiness 실패**: 트래픽 차단(Service Endpoint에서 제외) 됨

* **Liveness 실패**: 컨테이너 재시작되어 자동 복구 시도함

---

# 2. Liveness vs Readiness 핵심 차이

| 구분 | Liveness Probe | Readiness Probe |
| --- | --- | --- |
| 질문 | “컨테이너가 살아있나?” | “지금 트래픽 받아도 되나?” |
| 실패 시 | 컨테이너 재시작됨 | Service Endpoint에서 제외됨 |
| 트래픽 영향 | 간접적(재시작으로 다운타임 발생 가능) | 직접적(트래픽 차단) |
| 주 사용 목적 | Deadlock, 내부 멈춤 복구 | 초기화/의존성 준비 전 트래픽 차단 |

---

# 3. Probe 방식 3가지 (Readiness / Liveness 공통)

Readiness도, Liveness도 **동일하게 3가지 방식** 지원함.

1. **httpGet** : HTTP 응답 코드로 판단함

2. **exec** : 컨테이너 내부 명령 실행 exit code로 판단함

3. **tcpSocket** : 특정 포트로 TCP 연결 가능한지로 판단함

---

# 4. 공통 옵션

| 옵션 | 의미 |
| --- | --- |
| initialDelaySeconds | Pod 시작 후 첫 검사까지 대기함 |
| periodSeconds | 검사 주기임 |
| timeoutSeconds | 응답/실행 대기 시간임 |
| failureThreshold | 연속 실패 몇 번이면 실패로 확정할지 결정함 |
| successThreshold | 연속 성공 몇 번이면 성공으로 확정할지 결정함(readiness에서 자주 의미 있음) |

옵션 조합이 잘못되면 “정상인데 장애로 오판”하거나 “장애인데 정상으로 오판”함.

---

# 5. 실습

실습은 다음 순서로 진행함.

1. Readiness(HTTP) : 정상/비정상에 따라 Endpoint가 붙었다/빠졌다 확인함

2. Readiness(TCP Socket) : 포트 열림 여부로 Endpoint 제어 확인함

3. Readiness(Exec) : 커스텀 조건으로 Endpoint 제어 확인함

4. Liveness(Exec) : 실패 시 컨테이너 재시작 확인함

실습 전 공통 명령어는 이 3개를 계속 사용함.

```
kubectl get pod -w
kubectl describe pod <pod-name>
kubectl get endpoints <svc-name>
```

---

# 6. 실습 1 — Readiness Probe (HTTP 방식)

## 목표

HTTP 응답이 정상일 때만 Service가 트래픽을 전달하도록 만들고, 비정상 상태에서 Endpoint가 제거되는 것 확인함.

## 1단계: Deployment + Service 생성

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rd-http-deploy
spec:
  replicas: 1
  selector:
    matchLabels:
      app: rd-http
  template:
    metadata:
      labels:
        app: rd-http
    spec:
      containers:
      - name: nginx
        image: nginx:1.27
        ports:
        - containerPort: 80
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 3
          periodSeconds: 3
          timeoutSeconds: 1
          failureThreshold: 2
---
apiVersion: v1
kind: Service
metadata:
  name: rd-http-svc
spec:
  selector:
    app: rd-http
  ports:
  - port: 80
    targetPort: 80
```

적용함.

```
kubectl apply -f rd-http.yaml
```

## 2단계: Endpoint 확인

```
kubectl get endpoints rd-http-svc
```

Pod IP가 찍히면 readiness 성공했음.

## 3단계: 의도적으로 HTTP 실패 만들기

nginx를 죽이면 `/` 응답이 불가해짐.

```
kubectl get pod -l app=rd-http
kubectl exec -it <pod-name> -- pkill nginx
```

## 4단계: Endpoint 제거 확인

```
kubectl get endpoints rd-http-svc -w
```

Endpoint가 비면 readiness 실패로 판단했음.

이때 중요한 점은 **컨테이너가 재시작되는 게 아니라 트래픽만 차단됨**임.

---

# 7. 실습 2 — Readiness Probe (TCP Socket 방식)

## 목표

HTTP가 아니라, 특정 포트로 TCP 연결이 되면 준비 완료로 판단하게 구성함.

## 1단계: netcat 기반 TCP 서버 Pod + Service

아래 컨테이너는 8080 포트를 열고 대기함. (단순 TCP 서버)

```
apiVersion: v1
kind: Pod
metadata:
  name: rd-tcp-pod
  labels:
    app: rd-tcp
spec:
  containers:
  - name: tcp-server
    image: busybox:1.36
    command: ["sh","-c","nc -lk -p 8080 -e echo OK"]
    ports:
    - containerPort: 8080
    readinessProbe:
      tcpSocket:
        port: 8080
      initialDelaySeconds: 3
      periodSeconds: 3
      timeoutSeconds: 1
      failureThreshold: 2
---
apiVersion: v1
kind: Service
metadata:
  name: rd-tcp-svc
spec:
  selector:
    app: rd-tcp
  ports:
  - port: 8080
    targetPort: 8080
```

적용함.

```
kubectl apply -f rd-tcp.yaml
```

## 2단계: Endpoint 확인

```
kubectl get endpoints rd-tcp-svc
```

## 3단계: 포트가 닫히도록 프로세스 종료

```
kubectl exec -it rd-tcp-pod -- pkill nc
```

## 4단계: Endpoint 제거 확인

```
kubectl get endpoints rd-tcp-svc -w
```

TCP 연결이 안되니 readiness 실패로 판단했고 Endpoint 제거됐음.

### TCP 방식의 한계

포트가 열려있다는 것만 확인함.

앱 내부 로직이 고장났는지는 판단 못함.

---

# 8. 실습 3 — Readiness Probe (Exec 방식)

## 목표

“내가 정한 조건”을 만족할 때만 준비 완료로 판단하도록 구성함.

예시는 `/tmp/ready` 파일이 있을 때만 준비 완료로 판단함.

## 1단계: Pod + Service 생성

```
apiVersion: v1
kind: Pod
metadata:
  name: rd-exec-pod
  labels:
    app: rd-exec
spec:
  containers:
  - name: app
    image: busybox:1.36
    command: ["sh","-c","sleep 3600"]
    readinessProbe:
      exec:
        command: ["sh","-c","test -f /tmp/ready"]
      initialDelaySeconds: 3
      periodSeconds: 3
      timeoutSeconds: 1
      failureThreshold: 2
---
apiVersion: v1
kind: Service
metadata:
  name: rd-exec-svc
spec:
  selector:
    app: rd-exec
  ports:
  - port: 80
    targetPort: 80
```

적용함.

```
kubectl apply -f rd-exec.yaml
```

## 2단계: 처음 상태 확인

```
kubectl describe pod rd-exec-pod
kubectl get endpoints rd-exec-svc
```

처음엔 `/tmp/ready` 파일이 없으니 readiness 실패 상태라 Endpoint 비어있음.

## 3단계: 준비 완료 조건 만들기

```
kubectl exec -it rd-exec-pod -- sh -c "touch /tmp/ready"
```

## 4단계: Endpoint 등록 확인

```
kubectl get endpoints rd-exec-svc
```

Pod IP가 나타나면 readiness 성공했음.

## 5단계: 다시 준비 불가 상태 만들기

```
kubectl exec -it rd-exec-pod -- sh -c "rm -f /tmp/ready"
kubectl get endpoints rd-exec-svc -w
```

Endpoint가 다시 빠지면 readiness 제어가 제대로 됐음.

### Exec 방식 주의점

* 주기가 너무 짧으면 컨테이너 내부 명령 실행이 잦아짐 → CPU 사용량 증가 가능함

* 단순한 체크 스크립트로 구성하는 것이 안전함

---

# 9. 실습 4 — Liveness Probe (Exec 방식)로 “재시작” 확인

## 목표

liveness는 실패하면 컨테이너를 재시작한다는 것을 눈으로 확인함.

예시는 `/tmp/healthy` 파일이 없으면 실패하도록 구성함.

## 1단계: Pod 생성

```
apiVersion: v1
kind: Pod
metadata:
  name: lv-exec-pod
spec:
  containers:
  - name: app
    image: busybox:1.36
    command: ["sh","-c","sleep 3600"]
    livenessProbe:
      exec:
        command: ["sh","-c","test -f /tmp/healthy"]
      initialDelaySeconds: 3
      periodSeconds: 3
      timeoutSeconds: 1
      failureThreshold: 2
```

적용함.

```
kubectl apply -f lv-exec.yaml
```

## 2단계: 바로 재시작 되는지 확인

처음엔 `/tmp/healthy` 파일이 없으니 liveness 실패 → 재시작 반복함.

```
kubectl get pod lv-exec-pod -w
```

RESTARTS 증가 확인함.

## 3단계: 정상 상태로 만들기

재시작 루프를 멈추려면 파일을 만들어야 함.

다만 재시작이 계속 발생하면 exec 접속이 어려울 수 있음. 이 경우 `failureThreshold`나 `initialDelaySeconds`를 늘려서 접근 창을 확보하는 방식이 일반적임.

학습용으로는 아래처럼 Pod를 삭제하고 `initialDelaySeconds`를 크게 바꿔서 진행하는 편이 편함.

예시

```
apiVersion: v1
kind: Pod
metadata:
  name: lv-exec-pod
spec:
  containers:
  - name: app
    image: busybox:1.36
    command: ["sh","-c","touch /tmp/healthy; sleep 3600"]
    livenessProbe:
      exec:
        command: ["sh","-c","test -f /tmp/healthy"]
      initialDelaySeconds: 10
      periodSeconds: 3
      failureThreshold: 2
```

이제 실행 후 정상 유지됨.

## 4단계: 일부러 장애 만들기(파일 삭제)

```
kubectl exec -it lv-exec-pod -- sh -c "rm -f /tmp/healthy"
kubectl get pod lv-exec-pod -w
```

liveness 실패로 재시작 발생함.

---

# 10. 운영 설계 가이드

1. 웹 애플리케이션
   * readiness: HTTP `/health` 권장
   * liveness: HTTP 또는 exec(단순 체크) 권장

2. DB/캐시 같은 TCP 서비스
   * readiness: tcpSocket으로 “포트 오픈” 체크 가능함
   * 다만 “쿼리 가능 상태”까지 보려면 exec/커스텀 스크립트 필요함

3. readiness는 의존성(DB, 외부 API) 체크를 넣는 경우가 많음
   * 장애 시 재시작보다 트래픽 차단이 더 안전한 경우가 많음

---