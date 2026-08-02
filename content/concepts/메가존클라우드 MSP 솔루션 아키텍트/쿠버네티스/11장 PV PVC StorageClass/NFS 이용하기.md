---
title: "NFS 이용하기"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "쿠버네티스", "11장 PV PVC StorageClass"]
is_public: true
draft: false
---

# NFS 이용하기

[[NFS 서비스]] 

직접 설치하고 사용하시려면 크게 **두 가지 단계**를 거쳐야 한다. 하나는 실제 파일을 저장할 **NFS 서버**를 만드는 것이고, 다른 하나는 쿠버네티스가 이 서버를 자동으로 연결하게 해주는 프로비저너(Provisioner)를 설치하는 것이다.

---

### 1단계: NFS 서버 준비 (VM 중 한 곳 또는 외부 서버)

쿠버네티스 노드들이 접근할 수 있는 Linux 서버(예: 마스터 노드나 별도 VM)에서 NFS 서비스를 활성화해야 한다.

```
# 1. NFS 관련 패키지 설치
sudo apt update && sudo apt install nfs-kernel-server -y

# 2. 공유할 폴더 생성 및 권한 부여
sudo mkdir -p /srv/nfs/kubedata
sudo chown nobody:nogroup /srv/nfs/kubedata
sudo chmod 777 /srv/nfs/kubedata

# 3. 설정 파일에 공유 대역 추가 (/etc/exports)
# 모든 노드(192.168.80.0/24 대역 등)에서 접근 가능하도록 설정
echo "/srv/nfs/kubedata 192.168.80.0/24(rw,sync,no_subtree_check,no_root_squash)" | sudo tee -a /etc/exports

# 4. 서비스 재시작
sudo exportfs -a
sudo systemctl restart nfs-kernel-server
```

---

### 2단계: 모든 워커 노드에 클라이언트 설치

**중요:** 모든 노드는 NFS 서버에 접속할 수 있는 '손'이 있어야 합니다. 모든 노드에서 아래 명령어를 실행하세요.

```
sudo apt install nfs-common -y
```

---

### 3단계: NFS Subdir External Provisioner 설치 및 StorageClass 생성

이제 쿠버네티스 안에서 `example.com/nfs` 역할을 할 Provisioner를 배포해야 한다. 가장 대중적인 오픈소스인 **nfs-subdir-external-provisioner**를 사용.

**Helm을 사용한 간편 설치:**

```
# 1. Helm 리포지토리 추가
helm repo add nfs-subdir-external-provisioner https://kubernetes-sigs.github.io/nfs-subdir-external-provisioner/

# 2. 설치 (NFS 서버 IP와 경로를 본인 환경에 맞게 수정)
helm install nfs-provisioner nfs-subdir-external-provisioner/nfs-subdir-external-provisioner \
    --set nfs.server=192.168.80.110 \
    --set nfs.path=/srv/nfs/kubedata \
    --set storageClass.name=nfs-share \
    --set storageClass.provisionerName=example.com/nfs
```

* `storageClass.provisionerName`: 이 이름이 `StorageClass`의 `provisioner` 필드와 일치해야 한다.

* helm으로 생성시 --set storageClass.provisionerName=example.com/nfs 옵션으로 일치됨.

---

### 4단계: 테스트 (자동 생성 확인)

이제 `StorageClass`를 사용하여 PVC를 만들면, 수동으로 PV를 만들지 않아도 NFS 서버의 `/srv/nfs/kubedata` 폴더 안에 **자동으로 서브 디렉토리가 생기며** 연결된다.

```
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: nfs-pvc-test
spec:
  accessModes:
    - ReadWriteMany  # Many(RWX) 모드 사용이 가능함
  storageClassName: nfs-share
  resources:
    requests:
      storage: 100Mi
```

---

**동작 흐름:**

* PVC 생성

* provisioner가 PV 자동 생성

* PVC ↔ PV Bound

* Pod에서 PVC 사용

### - 이 방식의 장점

* **RWX 지원:** 여러 노드에 흩어진 파드들이 동시에 같은 파일을 읽고 쓸 수 있다.

* **관리 효율:** PV를 일일이 미리 만들 필요가 없다. PVC만 던지면 프로비저너가 NFS 서버 안에 폴더를 만들어준다.

---