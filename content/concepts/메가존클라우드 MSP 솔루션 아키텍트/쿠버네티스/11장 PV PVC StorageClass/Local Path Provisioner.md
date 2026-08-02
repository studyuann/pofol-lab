---
title: "Local Path Provisioner"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "쿠버네티스", "11장 PV PVC StorageClass"]
is_public: true
draft: false
---

# Local Path Provisioner

### 1. 프로비저너 설치

가장 가볍고 널리 쓰이는 Rancher의 오픈소스를 사용다. 노드에서 다음 명령어를 실행하면 즉시 `StorageClass`가 생성된다.

```
# 1. 설치용 매니페스트 적용
kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/v0.0.24/deploy/local-path-storage.yaml

# 2. StorageClass 생성 확인
kubectl get sc
```

* **결과:** `local-path`라는 이름의 StorageClass가 리스트에 나오면 성공.

* **기본 경로:** 각 워커 노드의 `/opt/local-path-provisioner` 디렉토리에 데이터가 저장.

---

### 2. 기본 StorageClass로 설정하기

학생들이 매번 YAML에 SC 이름을 적지 않아도 되도록 기본값으로 설정한다.

```
kubectl patch storageclass local-path -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```

---

### 3. [실습 예시] MySQL 데이터베이스 배포 (PVC 활용)

이제 별도의 PV를 수동으로 만들 필요 없이, **PVC만 선언**하면 됩니다.

### **(1) PVC 생성 (**`mysql-pvc.yaml`**)**

```
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mysql-pvc
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: local-path # 위에서 만든 SC 사용
  resources:
    requests:
      storage: 2Gi
```

### **(2) Deployment에 마운트 (**`mysql-deploy.yaml`**)**

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mysql
spec:
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
        env:
        - name: MYSQL_ROOT_PASSWORD
          value: "password123"
        ports:
        - containerPort: 3306
        volumeMounts:
        - name: mysql-data
          mountPath: /var/lib/mysql
      volumes:
      - name: mysql-data
        persistentVolumeClaim:
          claimName: mysql-pvc
```

---