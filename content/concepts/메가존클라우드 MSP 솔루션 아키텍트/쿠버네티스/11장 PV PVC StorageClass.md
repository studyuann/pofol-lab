---
title: "11장 PV PVC StorageClass"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "쿠버네티스"]
is_public: true
draft: false
---

# 11장. PV / PVC / StorageClass

---

## 1. 왜 PV/PVC가 필요한가

### 1.1 컨테이너/Pod의 저장소 문제

Pod는 기본적으로 **일시적(ephemeral) 저장소**를 사용한다.

* Pod 삭제 → Pod 내부 파일 시스템도 같이 사라짐

* 재스케줄링(다른 노드로 이동) → 이전 데이터 접근 불가

즉 DB, 업로드 파일, 로그, 사용자 데이터처럼 “남아야 하는 데이터”는 Pod 내부에 저장하면 안 된다.

---

## 2. PV/PVC/StorageClass

### 2.1 개념 정리

* **PV(PersistentVolume)**

  클러스터에 미리 준비된 “저장소 자원”

  관리자가 만들어두는 저장소 객체라고 이해하면 됨

* **PVC(PersistentVolumeClaim)**

  사용자가 “이 정도 용량/이런 모드로 저장소 필요함”을 요청하는 객체

  Pod는 PV를 직접 쓰지 않고 PVC를 통해서만 저장소를 사용함

* **StorageClass**

  “저장소를 만드는 방식(Provisioner)과 정책”을 정의하는 템플릿

  PVC가 StorageClass를 지정하면, 필요 시 PV가 자동으로 생성되는 방식(동적 프로비저닝)에 사용함

---

### 2.2 동작 흐름 2가지

### (1) 정적 프로비저닝(Static Provisioning)

```
1) 관리자가 PV를 미리 생성
   ↓
2) 사용자가 PVC 생성 (요청)
   ↓
3) PVC ↔ PV 바인딩
   ↓
4) Pod가 PVC를 마운트해서 사용
```

### (2) 동적 프로비저닝(Dynamic Provisioning) = StorageClass 사용

```
1) 관리자가 StorageClass 생성(또는 클라우드 기본 제공)
   ↓
2) 사용자가 PVC 생성(storageClassName 지정)
   ↓
3) Provisioner가 PV를 자동 생성
   ↓
4) PVC ↔ PV 자동 바인딩
   ↓
5) Pod가 PVC 사용
```

---

## 3. PV(PersistentVolume)

### 3.1 PV YAML 예시 (hostPath 기반, 학습용)

> hostPath는 “노드의 로컬 디렉터리”를 저장소로 쓰는 방식이라
>
> 단일 노드 테스트/교육용으로만 권장됨.(노드가 바뀌면 데이터 위치가 달라질 수 있음)

`pv.yaml`

```
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-1
spec:
  capacity:
    storage: 1Gi

  accessModes:
  - ReadWriteOnce

  persistentVolumeReclaimPolicy: Retain

  storageClassName: manual

  hostPath:
    path: /mnt/data
```

### 3.2 PV 옵션 설명

* `capacity.storage: 1Gi`

  PV가 제공하는 최대 용량임. PVC 요청이 이보다 크면 바인딩 안 됨

* `accessModes`

  PV를 어떤 방식으로 붙일 수 있는지 결정함. PVC와 반드시 호환되어야 함

* `persistentVolumeReclaimPolicy`

  PVC가 삭제된 뒤 PV를 어떻게 처리할지 결정함

  + `Retain` : PV와 실제 데이터 유지함(중요 데이터 권장)
  + `Delete` : PVC 삭제 시 PV도 삭제하도록 동작(주로 동적 프로비저닝에서 사용)

* `storageClassName`

  PV가 어떤 스토리지 클래스 소속인지 나타냄

  정적 바인딩에서도 “같은 storageClassName끼리 묶어서 자동 바인딩” 가능함

* `hostPath.path`

  실제 노드에 있는 디렉터리 경로임. 파드가 생성되는 노드에 생성됨

  디렉터리가 없으면 kubelet이 생성할 수도 있으나 권한/보안에 주의해야 함

### 3.3 PV 생성/확인

```
kubectl apply -f pv.yaml
kubectl get pv
kubectl describe pv pv-1
```

---

## 4. 접근 모드(AccessModes)

### 4.1 모드 종류

* `ReadWriteOnce(RWO)`

  한 번에 “하나의 노드”에서만 Read/Write로 붙을 수 있음

  DB 같은 상태 저장 워크로드에 흔함

* `ReadWriteOncePod(RWOP)`

  한 번에 “하나의 Pod”만 Read/Write로 붙을 수 있음

  여러 Pod이 공유하면 안 되는 경우에 유용함

* `ReadOnlyMany(ROX)`

  여러 노드에서 ReadOnly로 붙을 수 있음. 공유 스토리지 필요.

* `ReadWriteMany(RWX)`

  여러 노드에서 Read/Write로 동시에 붙을 수 있음

  NFS 같은 공유 스토리지에서 자주 사용함

중요 포인트:

* **ROX, RWX는 보통 네트워크 스토리지(NFS/CEPH 등)가 필요함**

* hostPath는 구조상 RWX 의미가 거의 없음(노드 로컬이라 다중 노드 공유 불가)

---

## 5. PVC(PersistentVolumeClaim)

### 5.1 PVC YAML 예시 (정적 바인딩: volumeName 사용)

`pvc.yaml`

```
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-pvc
spec:
  volumeName: pv-1
  accessModes:
  - ReadWriteOnce
  storageClassName: manual
  resources:
    requests:
      storage: 1Gi
```

### 5.2 PVC 옵션 설명

* `volumeName: pv-1`

  특정 PV를 “지정해서” 바인딩함. 정적 프로비저닝에서 자주 쓰는 방식임

  volumeName을 쓰면 “다른 PV와 자동 매칭”하지 않고 해당 PV만 바라봄

* `storageClassName`

  정적 바인딩에서도 PV/PVC가 같은 storageClassName이면 자동 매칭이 쉬움

  동적 프로비저닝에서는 사실상 필수 설정임

* `resources.requests.storage`

  요청 용량임. PV보다 크면 Pending에서 멈춤

---

### 5.3 PVC 생성/확인

```
kubectl apply -f pvc.yaml
kubectl get pvc
kubectl describe pvc app-pvc
```

상태:

* `Pending` : 조건 맞는 PV를 못 찾음

* `Bound` : PV와 연결 완료됨

---

## 6. Pod에서 PVC 사용

### 6.1 Pod YAML

`pod.yaml`

```
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
spec:
  containers:
  - name: app
    image: nginx:latest
    volumeMounts:
    - name: data-volume
      mountPath: /data
  volumes:
  - name: data-volume
    persistentVolumeClaim:
      claimName: app-pvc
```

옵션 설명:

* `volumeMounts.mountPath`

  컨테이너 내부에서 저장소가 연결될 경로임

* `volumes.persistentVolumeClaim.claimName`

  어떤 PVC를 마운트할지 지정함

  Pod는 PV를 직접 참조하지 않음(PVC만 참조함)

### 6.2 데이터 유지 확인 실습

```
kubectl apply -f pod.yaml
kubectl exec -it app-pod -- sh

echo "hello" > /data/test.txt
cat /data/test.txt
exit
```

Pod 삭제 후 재생성:

```
kubectl delete pod app-pod
kubectl apply -f pod.yaml
kubectl exec -it app-pod -- sh -c "cat /data/test.txt"
```

`hello`가 그대로 나오면 PV/PVC 영속성 확인 완료됨.

---

## 7. StorageClass

### 7.1 StorageClass가 필요한 이유

정적 방식은 PV를 사람이 미리 다 만들어야 해서 운영이 번거로움.

StorageClass를 쓰면:

* PVC만 만들면

* PV가 자동 생성되고

* 자동 바인딩됨

즉, 동적 프로비저닝임.

---

### 7.2 StorageClass 주요 필드

StorageClass 예시는 클러스터 환경에 따라 달라짐.

(온프레미스에서 “진짜 동적 프로비저닝” 하려면 NFS Provisioner, Longhorn, Rook-Ceph 같은 외부 provisioner가 필요함)

StorageClass에서 주로 보는 핵심 옵션은 다음임.

* `provisioner`

  PV를 자동 생성하는 “스토리지 플러그인” 이름임

  예:

  + AWS EBS: `ebs.csi.aws.com`
  + NFS provisioner: 설치한 provisioner 이름 사용

* `reclaimPolicy`

  동적으로 생성된 PV를 PVC 삭제 시 어떻게 처리할지

  + Delete: 같이 삭제(테스트/자동화에 편함)
  + Retain: PV 유지(데이터 보호)

* `volumeBindingMode`

  PV를 언제 생성/바인딩할지 결정함

  + `Immediate`: PVC 생성 즉시 PV 생성/바인딩
  + `WaitForFirstConsumer`: Pod가 어디 노드에 배치될 지 정해진 후 바인딩(멀티 노드에서 자주 권장)

[Local Path Provisioner](11%EC%9E%A5%20PV%20PVC%20StorageClass/Local%20Path%20Provisioner) 

---

## 8. MySQL 예제(정적 PV/PVC + Pod)

> hostPath는 학습용. 실무 DB는 보통 네트워크 스토리지 또는 CSI 기반 스토리지를 사용함.

### 8.1 PV 생성

`mysql-pv.yaml`

```
apiVersion: v1
kind: PersistentVolume
metadata:
  name: mysql-user-pv
spec:
  capacity:
    storage: 1Gi
  accessModes:
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual
  hostPath:
    path: /mnt/mysql-data
```

```
kubectl apply -f mysql-pv.yaml
```

### 8.2 PVC 생성

`mysql-pvc.yaml`

```
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mysql-pvc
spec:
#  volumeName: mysql-user-pv
  storageClassName: manual
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

```
kubectl apply -f mysql-pvc.yaml
kubectl get pvc
```

### 8.3 MySQL Pod 생성

`mysql-pod.yaml`

```
apiVersion: v1
kind: Pod
metadata:
  name: mysql
spec:
  containers:
  - name: mysql
    image: mysql:5.7
    env:
    - name: MYSQL_ROOT_PASSWORD
      value: password123
    ports:
    - containerPort: 3306
    volumeMounts:
    - name: mysql-storage
      mountPath: /var/lib/mysql
  volumes:
  - name: mysql-storage
    persistentVolumeClaim:
      claimName: mysql-pvc
```

```
kubectl apply -f mysql-pod.yaml
kubectl get pod
```

---

## 9. Deployment와 PVC (주의)

### 9.1 Deployment에서 PVC 사용

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mysql-deploy
spec:
  replicas: 1
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
        env:
        - name: MYSQL_ROOT_PASSWORD
          value: password123
        volumeMounts:
        - name: mysql-storage
          mountPath: /var/lib/mysql
      volumes:
      - name: mysql-storage
        persistentVolumeClaim:
          claimName: mysql-pvc
```

주의:

* RWO 볼륨은 기본적으로 “한 번에 하나 노드/하나 Pod” 성격이 강함

* replicas를 2로 올리면 한 PV/PVC를 여러 Pod이 동시에 쓰려고 시도할 수 있음

* DB는 보통 Deployment보다 StatefulSet을 권장하는 이유가 여기에도 있음

---

## 10. Reclaim Policy(삭제 정책)

### 10.1 Retain vs Delete

* `Retain`

  PVC 삭제 후에도 PV 유지함

  운영에서 데이터 보호용으로 자주 사용함

* `Delete`

  PVC 삭제 시 PV도 삭제됨

  동적 프로비저닝 테스트에서 많이 사용함

---

## 11. 자주 하는 실수

### 11.1 emptyDir로 데이터 저장

* `emptyDir`는 Pod 삭제 시 데이터 날아감

* 영속 데이터는 반드시 PVC 사용해야 함

### 11.2 accessModes 불일치

PV/PVC 모드가 맞지 않으면 Pending 상태로 멈춤

### 11.3 PVC 요청 용량이 PV보다 큼

PVC가 더 크면 PV를 찾지 못해 Pending

### 11.4 hostPath를 멀티노드 공유 스토리지로 착각

hostPath는 “노드 로컬 디렉터리”임

노드가 바뀌면 데이터 위치가 달라짐

---

## 12. 핵심 정리

* PV는 “저장소 자체”

* PVC는 “저장소 요청서”

* Pod는 PV를 직접 쓰지 않고 PVC를 사용함

* StorageClass는 “PV를 자동으로 만드는 방식(동적 프로비저닝)”

* 온프레미스에서 동적 프로비저닝을 하려면 NFS Provisioner/Longhorn/Rook-Ceph 같은 구성요소가 추가로 필요함

---

## 13. 실습 명령 요약

```
# 1) PV/PVC 생성
kubectl apply -f pv.yaml
kubectl apply -f pvc.yaml

# 2) 바인딩 확인
kubectl get pv
kubectl get pvc

# 3) Pod 생성 및 데이터 확인
kubectl apply -f pod.yaml
kubectl exec -it app-pod -- sh
echo hello > /data/test.txt
cat /data/test.txt
exit

# 4) Pod 삭제 후 데이터 유지 확인
kubectl delete pod app-pod
kubectl apply -f pod.yaml
kubectl exec -it app-pod -- sh -c "cat /data/test.txt"
```

---

[NFS 이용하기](11%EC%9E%A5%20PV%20PVC%20StorageClass/NFS%20%EC%9D%B4%EC%9A%A9%ED%95%98%EA%B8%B0)[Longhorn 이용하기](11%EC%9E%A5%20PV%20PVC%20StorageClass/Longhorn%20%EC%9D%B4%EC%9A%A9%ED%95%98%EA%B8%B0)