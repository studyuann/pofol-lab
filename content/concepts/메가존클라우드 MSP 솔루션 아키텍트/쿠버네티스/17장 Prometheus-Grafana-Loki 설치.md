---
title: "17장 Prometheus-Grafana-Loki 설치"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "쿠버네티스"]
is_public: true
draft: false
---

# 17장. Prometheus-Grafana-Loki 설치

---

# 1. 사전 준비

## 1) Kubernetes 클러스터 상태 확인

```
kubectl get node -o wide
kubectl get pod -A | head
```

## 2) Helm 준비

```
helm version
```

## 3) 네임스페이스 생성

```
kubectl create ns monitoring
```

## 4) Helm repo 등록/업데이트

```
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
```

---

# 2. Prometheus + Grafana 설치 (kube-prometheus-stack 58.2.2)

## 1) 설치

```
helm install prometheus-stack prometheus-community/kube-prometheus-stack \
  -n monitoring \
  --version 58.2.2
```

### 설치 확인

```
kubectl get pod -n monitoring
helm list -n monitoring
```

kube-prometheus-stack 구성요소가 정상적으로 올라왔는지 확인함.

* prometheus-operator

* prometheus-kube-prom-prometheus

* alertmanager

* kube-state-metrics

* node-exporter

* grafana

---

## 2) Grafana 외부 접속(NodePort로 노출)

기본 설치는 ClusterIP일 수 있어서 외부 접속을 위해 NodePort로 바꿈.

```
helm upgrade prometheus-stack prometheus-community/kube-prometheus-stack \
  -n monitoring \
  --version 58.2.2 \
  --set grafana.service.type=NodePort
```

### Grafana NodePort 확인

```
kubectl get svc -n monitoring | grep grafana
```

브라우저 접속:

```
http://<노드IP>:<NodePort>
```

---

## 3) Grafana 초기 비밀번호 확인

kube-prometheus-stack은 grafana secret에 admin password가 들어감.

```
kubectl get secret -n monitoring prometheus-stack-grafana \
  -o jsonpath='{.data.admin-password}' | base64 -d; echo
```

* ID: `admin`

* PW: 위 출력값

---

# 3. Prometheus 정상 동작 검증

## 1) Prometheus 서비스 확인

```
kubectl get svc -n monitoring | egrep -i "prometheus|operated"
```

## 2) Prometheus Target 확인(권장)-클라이언트

Prometheus UI를 NodePort로 안 열어도 되지만, 확인이 필요하면 port-forward로 봄.

```
kubectl port-forward -n monitoring svc/prometheus-stack-kube-prom-prometheus 9090:9090
```

브라우저:

```
http://localhost:9090
```

Status → Targets에서 scrape 상태 확인함.

---

# 4. Loki 설치 (loki-stack 2.10.3, Loki 2.9.3)

## 1) Loki 설치

### **loki-values.yaml 파일 작성**

### 1. 파일 생성

```
vi loki-values.yaml
```

### 2. 아래 내용 입력

```
loki:
  image:
    tag: 2.9.3

  persistence:
    enabled: false

  config:
    auth_enabled: false

    server:
      http_listen_port: 3100

    common:
      path_prefix: /data/loki
      replication_factor: 1

    ingester:
      lifecycler:
        ring:
          kvstore:
            store: inmemory
      chunk_idle_period: 3m
      chunk_block_size: 262144

    schema_config:
      configs:
        - from: 2023-01-01
          store: boltdb-shipper
          object_store: filesystem
          schema: v12
          index:
            prefix: index_
            period: 24h

    storage_config:
      boltdb_shipper:
        active_index_directory: /data/loki/index
        cache_location: /data/loki/index_cache
        shared_store: filesystem
      filesystem:
        directory: /data/loki/chunks

promtail:
  enabled: true

  config:
    clients:
      - url: http://loki:3100/loki/api/v1/push
```

---

### Loki + Promtail 설치

```
helm install loki grafana/loki-stack -n monitoring \
  -f loki-values.yaml
```

설치 확인:

```
helm list -n monitoring
kubectl get pod -n monitoring
```

정상 상태:

* loki-0 Running

* promtail-xxxxx (DaemonSet) Running (노드 수만큼)

---

### Loki 정상 동작 확인

### 1. Loki readiness 확인

```
kubectl exec -n monitoring -it \
<grafana pod명> \
-- curl -s http://loki:3100/ready
```

정상 출력:

```
ready
```

---

## 2. 버전 확인

```
kubectl exec -n monitoring -it \
<grafana pod명> -- curl -s http://loki:3100/loki/api/v1/status/buildinfo
```

출력에:

```
"version":"2.9.3"
```

확인

---

### Promtail 정상 동작 확인

### 1. DaemonSet 확인

```
kubectl get ds -n monitoring | grep promtail
```

노드 수만큼 READY 1/1 확인

---

### 2. 로그 확인

```
kubectl logs -n monitoring -l app.kubernetes.io/name=promtail --tail=50
```

정상일 경우:

* "client connected"

* "pushed log batch"

같은 메시지 출력됨Grafana에서 Loki 연결

---

Grafana → Connections → Data Sources → Add data source → Loki

설정:

```
URL: http://loki:3100
```

Save & Test

---

### 로그 확인

Grafana → Explore → Loki 선택

쿼리 입력:

```
{namespace="monitoring"}
```

또는

```
{job="varlogs"}
```

로그 출력되면 성공

---

### 구성 구조 이해

## 🔹 전체 흐름

```
Node Container Logs
        ↓
    Promtail (DaemonSet)
        ↓  (push)
      Loki
        ↓
     Grafana
```

---

## 🔹 promtail 역할

* /var/log/containers 파일 감시

* 로그에 라벨(namespace, pod, container 등) 추가

* Loki에 push

---

### 설치 완료 검증 체크리스트

| 확인 항목 | 명령 |
| --- | --- |
| Loki Pod Running | kubectl get pod -n monitoring |
| Promtail DS Running | kubectl get ds -n monitoring |
| Loki Ready | curl /ready |
| Buildinfo 버전 | curl /status/buildinfo |
| Grafana 연결 성공 | Save & Test OK |
| 로그 조회 가능 | Explore에서 LogQL |

---