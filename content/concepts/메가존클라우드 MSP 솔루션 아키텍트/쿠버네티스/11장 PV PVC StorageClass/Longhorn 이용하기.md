---
title: "Longhorn 이용하기"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "쿠버네티스", "11장 PV PVC StorageClass"]
is_public: true
draft: false
---

# Longhorn 이용하기

---

## 1. 사전 준비 (모든 노드에서 실행)

Longhorn은 각 노드의 OS 레벨에서 특정 도구들이 설치되어 있어야 한다. 이 단계를 건너뛰면 설치 후에 볼륨이 마운트되지 않는 에러를 겪게 된다.

### ① 필수 패키지 설치

모든 워커 노드와 마스터 노드에서 실행.

```
sudo apt update
sudo apt install open-iscsi nfs-common util-linux -y

# iscsid 서비스 활성화 및 시작
sudo systemctl enable --now iscsid
```

### ② 환경 검사 스크립트 실행

Longhorn 팀에서 제공하는 체크용 스크립트를 통해 설치 가능 여부를 미리 확인할 수 있다.

```
sudo apt install jq -y
curl -sSfL https://raw.githubusercontent.com/longhorn/longhorn/v1.5.3/scripts/environment_check.sh | bash
```

> **Tip:** 여기서 `ERROR`가 나오지 않아야 한다. 특히 `iscsid`가 실행 중인지 꼭 확인 필요.

---

## 2. Longhorn 설치 (Helm 기준) - control plane에서 실행

가장 권장되는 설치 방식은 Helm이다.

```
# 1. Helm 설치 스크립트 다운로드
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3

# 2. 스크립트에 실행 권한 부여
chmod 700 get_helm.sh

# 3. 스크립트 실행 (설치 진행)
./get_helm.sh
```

```
# 1. Helm 리포지토리 추가
helm repo add longhorn https://charts.longhorn.io
helm repo update

# 2. 전용 네임스페이스 생성 및 설치
kubectl create namespace longhorn-system
helm install longhorn longhorn/longhorn --namespace longhorn-system
```

설치 후 모든 파드가 `Running` 상태가 될 때까지 기다린다.

```
kubectl get pods -n longhorn-system -w
```

---

## 3. 대시보드(GUI) 접속하기

Longhorn의 가장 큰 장점은 웹 UI이다. 기본적으로 `ClusterIP`로 설정되어 있으므로, 외부에서 접속하려면 서비스를 노출해야 한다.

### NodePort로 변경

```
kubectl edit svc longhorn-frontend -n longhorn-system
```

http://노드IP주소:노드포트로 접속할 수 있다.

### Ingress 설정

아래와 같이 인그레스를 설정하면 `http://longhorn.local` 같은 주소로 접속할 수 있다.

```
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: longhorn-ingress
  namespace: longhorn-system
spec:
  ingressClassName: nginx
  rules:
  - host: longhorn.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: longhorn-frontend
            port:
              number: 80
```

---

## 4. 실전 사용: StorageClass 확인 및 PVC 생성

설치가 완료되면 `longhorn`이라는 이름의 **StorageClass**가 자동으로 생성된다.

### ① 서비스 상태 확인

```
kubectl get sc
```

* `longhorn`이 목록에 있고 `(default)`로 표시된다면 성공.

### ② 테스트 PVC 생성

이제 NFS 때처럼 복잡한 서버 설정 없이, 그냥 "longhorn 클래스로 용량 줘!"라고 요청만 하면 된다.

```
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: longhorn-pvc
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: longhorn # 자동 생성된 클래스 이름
  resources:
    requests:
      storage: 2Gi
```

---

## 💡 Longhorn이 NFS보다 좋은 점

1. **복제(Replication):** 데이터를 여러 노드에 복제해 둔다. 노드 한 대가 죽어도 데이터 유실 없이 다른 노드에서 파드가 바로 살아난다.

2. **스냅샷 및 백업:** GUI에서 클릭 한 번으로 시점 복구 포인트를 만들거나 S3/NFS로 외부 백업을 보낼 수 있다.

3. **리소스 통합:** 별도의 NFS 서버 VM을 만들 필요 없이, 워커 노드들의 남는 SSD 공간을 묶어서 알뜰하게 사용한다.

### ⚠️ 주의사항

* **사양:** Longhorn은 각 노드에서 에이전트 파드를 띄우므로 RAM을 약간 점유한다. (노드당 최소 2GB 이상의 여유 RAM 권장)

* **디스크 경로:** 기본적으로 `/var/lib/longhorn` 경로를 사용한다.