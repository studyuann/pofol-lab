---
title: "7장 StatefulSet & DaemonSet"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "쿠버네티스"]
is_public: true
draft: false
---

# 7장. StatefulSet & DaemonSet

---

# 1. StatefulSet

---

## 1.1 개념

StatefulSet은 상태를 가진 애플리케이션(Stateful Application)을 관리하는 Kubernetes 리소스다.

각 Pod은 고유한 정체성(Identity)을 가지며 순서대로 배포되고 삭제된다.

Deployment와의 가장 큰 차이점은 다음과 같다.

* Pod 이름이 고정된다.

* Pod마다 독립적인 스토리지를 가진다.

* 생성 및 삭제 순서가 보장된다.

---

## 1.2 특징

---

### 1. 안정적인 네트워크 ID

Pod 이름이 고정된다.

```
mysql-0
mysql-1
mysql-2
```

DNS 주소:

```
mysql-0.mysql-headless
```

Pod이 재시작되어도 동일한 이름과 DNS를 유지한다.

Headless Service가 반드시 필요하며, `clusterIP: None` 설정이 있어야 Pod 개별 DNS가 생성된다.

---

### 2. 순차적 배포 및 삭제

생성 순서:

```
mysql-0 → mysql-1 → mysql-2
```

삭제 순서:

```
mysql-2 → mysql-1 → mysql-0
```

앞 Pod이 Ready 상태가 되기 전에는 다음 Pod이 생성되지 않는다.

이 동작은 기본값 `podManagementPolicy: OrderedReady` 때문이다.

필요 시 `Parallel`로 변경 가능하다.

---

### 3. Persistent Volume 연결

각 Pod이 자신의 독립적인 저장소를 가진다.

Pod 재시작 후에도 같은 PVC에 연결된다.

🔹 매우 중요

운영 환경에서는 반드시 `volumeClaimTemplates`를 사용해야 한다.

emptyDir는 임시 저장소이므로 DB에서는 사용하면 안 된다.

---

### 4. Headless Service 필요

StatefulSet은 반드시 Headless Service와 함께 사용한다.

```
clusterIP: None
```

이 설정이 없으면 Pod DNS가 생성되지 않는다.

---

## 1.3 사용 사례

* 데이터베이스 (MySQL, PostgreSQL, MongoDB)

* 메시지 큐 (Kafka, RabbitMQ)

* 분산 시스템 (Cassandra, Elasticsearch)

공통점:

* 순서 중요

* 고정 hostname 필요

* 데이터 영속성 필요

---

## 1.4 YAML 예제(statefulset.yaml)

```
apiVersion: v1
kind: Service
metadata:
  name: mysql-headless
spec:
  clusterIP: None  # Headless Service
  selector:
    app: mysql
  ports:
  - port: 3306
    targetPort: 3306
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql
spec:
  serviceName: mysql-headless  # StatefulSet과 연결할 Service
  replicas: 3
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
      - name: mysql
        image: mysql:8.0
        ports:
        - containerPort: 3306
        env:
        - name: MYSQL_ROOT_PASSWORD
          value: "password123"
        volumeMounts:
        - name: mysql-storage
          mountPath: /var/lib/mysql
      volumes:
      - name: mysql-storage
        emptyDir: {}  # 임시 저장소, pod 삭제 시 데이터도 삭제됨
```

---

## 1.5 YAML 설명

### Service 부분

* `clusterIP: None` → Headless Service 설정

* `selector` → StatefulSet Pod과 연결

* `port` → Service 포트

* `targetPort` → Pod 내부 포트

---

### StatefulSet 부분

* `serviceName` → Headless Service 이름과 반드시 일치

* `replicas` → 생성할 Pod 수

* `selector.matchLabels` → 관리 대상 Pod 라벨

* `template.metadata.labels` → 반드시 selector와 동일

* `containers.image` → 컨테이너 이미지

* `env` → 환경변수 설정

* `volumeMounts` → Pod 내부 경로에 볼륨 연결

* `volumes.emptyDir` → 임시 저장소

---

### 🔴 중요한 보완 사항

현재 예제는:

```
emptyDir: {}
```

으로 되어 있다.

이 경우:

* Pod 삭제 시 데이터 삭제됨

* StatefulSet의 장점이 사라짐

운영 환경에서는 다음과 같이 변경해야 한다.

```
volumeClaimTemplates:
- metadata:
    name: mysql-storage
  spec:
    accessModes: ["ReadWriteOnce"]
    resources:
      requests:
        storage: 1Gi
```

---

## 1.6 실습 보완 포인트

StatefulSet 삭제 시 PVC는 자동 삭제되지 않는다.

확인:

```
kubectl get pvc
```

이 점을 반드시 설명해야 한다.

---

# 2. DaemonSet

---

## 2.1 개념

DaemonSet은 **모든 노드(또는 특정 노드)에 1개씩 Pod을 실행**시키는 리소스다.

replicas를 지정하지 않는다.

노드 수가 곧 Pod 수다.

---

## 2.2 특징

---

### 1. 모든 노드에서 실행

* 새로운 노드가 추가되면 자동으로 Pod 배포

* 노드 제거 시 Pod 삭제

* 노드당 정확히 1개 Pod 생성

---

### 2. 상태 비저장

* Pod 간 순서 없음

* 고유 ID 없음

* 재시작 가능

---

### 3. 노드 선택 가능

* nodeSelector

* affinity

* tolerations

특정 조건에 맞는 노드에만 배포 가능.

---

## 2.3 사용 사례

모든 노드에 필요:

* 로그 수집기 (Fluentd)

* 모니터링 에이전트 (Node Exporter)

* 네트워크 플러그인

특정 노드에만 필요:

* GPU 노드 전용 작업

---

## 2.4 YAML 예제(daemonset.yaml)

```
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-logger
  namespace: default
spec:
  selector:
    matchLabels:
      app: node-logger
  template:
    metadata:
      labels:
        app: node-logger
    spec:
      containers:
      - name: logger
        image: busybox:latest
        command: ["sh", "-c"]
        args:
          - |
            while true; do
              echo "Running on node: $(hostname)"
              sleep 10
            done
        resources:
          limits:
            cpu: 100m
            memory: 128Mi
          requests:
            cpu: 50m
            memory: 64Mi
```

---

## 2.5 YAML 설명

* `selector.matchLabels` → 관리 대상 Pod 선택

* `template.metadata.labels` → 반드시 동일해야 함

* `command` → ENTRYPOINT override

* `args` → CMD override

* `resources.requests` → 스케줄 기준

* `resources.limits` → 최대 사용 자원

---

## 🔹 추가 보완 (운영 관점)

DaemonSet에는 `updateStrategy`가 존재한다.

기본값:

```
RollingUpdate
```

옵션:

```
updateStrategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 1
```

대규모 클러스터에서는 이 설정이 중요하다.

---

# 3. 비교 분석

| 항목 | StatefulSet | DaemonSet |
| --- | --- | --- |
| 목적 | 상태 있는 앱 관리 | 모든 노드 실행 |
| Pod 개수 | replicas 수 | 노드 수 |
| Pod 정체성 | 고정 | 노드마다 자동 |
| 배포 순서 | 순차 | 동시 |
| 네트워크 ID | 안정적 DNS | 변할 수 있음 |
| 스토리지 | PersistentVolume 필요 | 보통 필요 없음 |
| 사용 사례 | DB, 메시지큐 | 로깅, 모니터링 |
| 스케일링 | 수동 (replicas) | 노드 추가 시 자동 |

---

## 4. 실습 예제(sts-ds-client.yaml)

```
# ============================================
# PersistentVolume 생성
# ============================================
---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: mysql-pv-1
spec:
  capacity:
    storage: 1Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: /mnt/data/mysql-1
---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: mysql-pv-2
spec:
  capacity:
    storage: 1Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: /mnt/data/mysql-2
---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: mysql-pv-3
spec:
  capacity:
    storage: 1Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: /mnt/data/mysql-3

# ============================================
# StatefulSet 예제
# ============================================
---
# Headless Service (StatefulSet과 함께 사용)
apiVersion: v1
kind: Service
metadata:
  name: mysql-headless
  namespace: tutor-ns
spec:
  clusterIP: None  # 중요: Headless Service
  selector:
    app: mysql
  ports:
  - port: 3306
    targetPort: 3306
    name: mysql
---
# StatefulSet
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql
  namespace: tutor-ns
spec:
  serviceName: mysql-headless  # Headless Service 이름
  replicas: 3
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
      - name: mysql
        image: mysql:5.7
        ports:
        - containerPort: 3306
          name: mysql
        env:
        - name: MYSQL_ROOT_PASSWORD
          value: "password123"
        volumeMounts:
        - name: mysql-storage
          mountPath: /var/lib/mysql
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
  # 각 Pod마다 독립적인 PVC 생성 (PV와 자동 바인딩)
  volumeClaimTemplates:
  - metadata:
      name: mysql-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 1Gi

# ============================================
# DaemonSet 예제
# ============================================
---
# DaemonSet (모든 노드에 배포)
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-exporter
  namespace: tutor-ns
spec:
  selector:
    matchLabels:
      app: node-exporter
  template:
    metadata:
      labels:
        app: node-exporter
    spec:
      containers:
      - name: node-exporter
        image: prom/node-exporter:latest
        ports:
        - containerPort: 9100
        args:
        - --path.procfs=/host/proc
        - --path.sysfs=/host/sys
        - --collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)
        volumeMounts:
        - name: proc
          mountPath: /host/proc
          readOnly: true
        - name: sys
          mountPath: /host/sys
          readOnly: true
        resources:
          requests:
            memory: "32Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "200m"
      
      volumes:
      - name: proc
        hostPath:
          path: /proc
      - name: sys
        hostPath:
          path: /sys

# ============================================
# 테스트용 Client Pod
# ============================================
---
# busybox 테스트 Client (DNS 도구 포함)
apiVersion: v1
kind: Pod
metadata:
  name: debug-client
  namespace: tutor-ns
spec:
  containers:
  - name: client
    image: busybox:latest
    command: ['sleep', '3600']
  restartPolicy: Never
```

### 실습 1: StatefulSet 배포 및 확인

```
# StatefulSet 배포
kubectl apply -f statefulset.yaml

# Pod 확인 (순차적 생성 확인)
kubectl get pods -w

# 특정 Pod의 hostname 확인
kubectl exec mysql-0 -- cat /etc/hostname
# 출력: mysql-0

kubectl exec mysql-1 -- cat /etc/hostname
# 출력: mysql-1

# debug-client pod 접속
kubectl exec -it debug-client -n tutor-ns -- sh

nslookup mysql-0.mysql-headless.tutor-ns.svc.cluster.local
```

### 실습 2: DaemonSet 배포 및 확인

```
# DaemonSet 배포
kubectl apply -f daemonset.yaml

# 각 노드에 1개씩 Pod 생성 확인
kubectl get pods -o wide

# 노드별 Pod 개수 확인
kubectl get pods --all-namespaces -o wide | grep node-exporter


# DaemonSet 삭제
kubectl delete daemonset node-exporter
```

### 실습 3: StatefulSet 영속성 확인

```
# Pod 내 파일 생성
kubectl exec mysql-0 -- sh -c 'echo "test data" > /var/lib/mysql/test.txt'

# Pod 삭제
kubectl delete pod mysql-0

# StatefulSet이 자동으로 mysql-0 재생성
# 같은 PV에 연결되므로 파일 유지됨
kubectl exec mysql-0 -- cat /var/lib/mysql/test.txt
# 출력: test data
```

---

## 핵심 정리

**StatefulSet 선택 기준:**

* ✓ 순서가 중요한 애플리케이션

* ✓ 고유한 네트워크 ID 필요

* ✓ 데이터 영속성 필요

* ✓ Pod 간 역할 구분 필요

**DaemonSet 선택 기준:**

* ✓ 모든 노드에서 실행 필요

* ✓ 노드별 1개 Pod 필요

* ✓ 상태 비저장 작업

* ✓ 노드 추가 시 자동 확장 필요