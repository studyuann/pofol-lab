---
title: "실습 GKE와 Filestore 연동"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Google 쿠버네티스 아키텍처 설계 및 구축"]
is_public: true
draft: false
---

# 실습. GKE와 Filestore 연동

## 정적 프로비저닝 + 동적 프로비저닝 통합 실습

---

# 1. 실습 목표

1. 클러스터에서 Filestore CSI 드라이버 활성화

2. Google Cloud 콘솔에서 Filestore 인스턴스 생성

3. **정적 프로비저닝** 방식으로 기존 Filestore 인스턴스를 PV/PVC에 연결

4. **동적 프로비저닝** 방식으로 StorageClass와 PVC만으로 Filestore 볼륨 자동 생성

5. Deployment를 통해 여러 Pod가 같은 공유 스토리지를 사용하는 구조 확인

6. 파일 생성, 조회, 공유 동작 검증

---

# 2. 실습 개념 정리

## 2-1. Filestore란 무엇인가

Filestore는 Google Cloud의 **관리형 NFS 파일 스토리지 서비스**임.

즉, 리눅스 환경에서 흔히 쓰는 NFS(Network File System)를 Google Cloud가 관리형으로 제공하는 서비스라고 보면 됨.

애플리케이션 입장에서는 디렉터리처럼 마운트해서 사용 가능함.

예를 들면 아래 같은 용도로 많이 씀.

* 여러 Pod가 같은 파일을 공유해야 할 때

* 웹 서버 여러 대가 공통 정적 파일을 읽어야 할 때

* 업로드 파일을 공용 저장소에 저장해야 할 때

* 상태 저장형 애플리케이션에서 공유 파일 시스템이 필요할 때

---

## 2-2. 정적 프로비저닝이란 무엇인가

정적 프로비저닝은 **스토리지를 미리 만들어 두고**, Kubernetes 쪽에서 그 스토리지를 **직접 PV로 연결하는 방식**임.

즉 순서는 아래와 같음.

1. 관리자가 Google Cloud에서 Filestore 인스턴스를 먼저 만듦

2. Kubernetes에서 그 인스턴스를 가리키는 PV를 작성

3. PVC가 그 PV를 바인딩

4. Pod가 PVC를 마운트

### 장점

* 어떤 Filestore를 연결하는지 명확함

* 기존 인프라를 재사용하기 좋음

* 운영자가 스토리지를 직접 통제 가능함

### 단점

* 수작업이 많음

* 자동화 수준이 낮음

* PVC를 만들 때마다 관리 개입이 필요할 수 있음

---

## 2-3. 동적 프로비저닝이란 무엇인가

동적 프로비저닝은 **StorageClass를 기반으로 PVC를 만들면, CSI 드라이버가 자동으로 스토리지를 생성하는 방식**임.

즉 순서는 아래와 같음.

1. StorageClass 생성 또는 GKE 기본 StorageClass 사용

2. 사용자가 PVC 생성

3. CSI 드라이버가 Filestore 인스턴스 또는 share를 자동으로 프로비저닝

4. Pod가 PVC를 사용

### 장점

* 자동화가 쉬움

* DevOps/플랫폼 운영에 적합함

* 사용자 입장에서 PVC만 만들면 됨

### 단점

* 내부적으로 어떤 Filestore가 생성됐는지 구조를 모르면 추적이 어려울 수 있음

* 네트워크/클래스/티어 설계를 잘 해야 함

---

# 3. 실습 환경

예시 환경은 아래처럼 잡음.

```
export PROJECT_ID=my-gcp-project
export REGION=asia-northeast3
export ZONE=asia-northeast3-c
export CLUSTER_NAME=이니셜-std-cluster-1

export NAMESPACE_STATIC=filestore-static
export NAMESPACE_DYNAMIC=filestore-dynamic

export FILESTORE_INSTANCE=fs-static-demo
export FILESTORE_SHARE=vol1
export FILESTORE_TIER=BASIC_HDD
```

프로젝트 기본값도 맞춰둠.

```
gcloud config set project $PROJECT_ID
```

---

# 4. Filestore CSI 드라이버 활성화

GKE Standard 클러스터에서는 Filestore CSI 드라이버를 활성화해야 함. Autopilot은 기본 활성화지만, Standard는 별도 활성화가 필요함.

## 4-1. 콘솔에서 설정하는 방법

1. Google Cloud 콘솔 접속

2. **Kubernetes Engine > Clusters** 이동

3. 대상 Standard 클러스터 클릭

4. **Features** 항목 확인

5. **Filestore CSI driver** 옆의 수정 버튼 클릭

6. **Enable Filestore CSI driver** 체크

7. 저장

## 4-2. CLI로 설정하는 방법

```
gcloud container clusters update $CLUSTER_NAME \
  --zone $ZONE \
  --update-addons=GcpFilestoreCsiDriver=ENABLED
```

### 명령 설명

* `gcloud container clusters update`

  기존 GKE 클러스터 설정 변경 명령

* `--update-addons=GcpFilestoreCsiDriver=ENABLED`

  Filestore CSI 드라이버 활성화

### 확인

```
kubectl get sc
```

드라이버가 활성화되면 GKE에서 Filestore용 StorageClass들이 자동 설치됨. 예를 들면 `zonal-rwx`, `enterprise-rwx`, `enterprise-multishare-rwx`, `standard-rwx`, `premium-rwx` 등이 생성될 수 있음.

---

# 5. 정적 프로비저닝 실습

정적 프로비저닝은 **미리 만든 Filestore 인스턴스를 Kubernetes PV로 직접 연결**하는 방식임.

* FileStore API 활성화

---

```
gcloud services enable file.googleapis.com
```

## 5-1. Filestore 인스턴스 생성

### 콘솔에서 생성

1. Google Cloud 콘솔에서 **Filestore** 검색 후 이동

2. **Create instance** 클릭

3. 인스턴스 이름: `fs-static-demo`

4. 리전: GKE 클러스터와 같은 리전 선택

5. 존: 클러스터 노드가 접근 가능한 위치 선택

6. 서비스 티어: 실습이라면 `Basic HDD` 또는 `Zonal` 중 하나 선택

7. 파일 공유 이름: `vol1`

8. 용량 설정

9. VPC 네트워크는 GKE 클러스터와 같은 네트워크 선택

10. 생성

### 중요

Filestore는 **NFS 서버** 역할을 하는 관리형 스토리지임.

따라서 Pod가 마운트하려면 **같은 VPC 네트워크 및 접근 가능한 IP 대역**에 있어야 함.

---

## 5-2. CLI로 Filestore 인스턴스 생성

예시로 Basic HDD 1TiB 생성:

```
gcloud filestore instances create $FILESTORE_INSTANCE \
  --zone=$ZONE \
  --tier=$FILESTORE_TIER \
  --file-share=name=$FILESTORE_SHARE,capacity=10GB \
  --network=name=default
```

### 명령 설명

* `gcloud filestore instances create`

  Filestore 인스턴스 생성

* `--zone=$ZONE`

  Filestore 인스턴스 생성 위치

* `--tier=$FILESTORE_TIER`

  서비스 티어 지정

* `--file-share=name=$FILESTORE_SHARE,capacity=1GB`

  생성할 파일 공유 이름과 용량 지정

* `--network=name=kdtmsp-vpc`

  연결할 VPC 네트워크 지정

### 인스턴스 IP 확인

```
gcloud filestore instances describe $FILESTORE_INSTANCE \
  --zone=$ZONE
```

출력에서 `networks.ipAddresses` 값을 확인함.

이 값을 아래 변수에 저장해둠.

```
export FILESTORE_IP=10.10.20.2
```

---

## 5-3. 네임스페이스 생성

```
kubectl create namespace $NAMESPACE_STATIC
```

---

## 5-4. 정적 프로비저닝용 PV/PVC 작성

`PersistentVolume`의 `csi.driver`를 `filestore.csi.storage.gke.io`로 지정하고, `volumeHandle`에 `modeInstance/LOCATION/INSTANCE/SHARE` 형식을 사용하며, `volumeAttributes`에 Filestore IP와 share 이름 등을 넣는 구조임. 또한 NFSv4.1을 사용하려면 `protocol: NFS_V4_1`을 설정하고, 기본은 NFSv3임.

### `preprov-filestore.yaml`

```
apiVersion: v1
kind: PersistentVolume
metadata:
  name: filestore-static-pv
spec:
  storageClassName: ""
  capacity:
    storage: 1Ti
  accessModes:
    - ReadWriteMany
  persistentVolumeReclaimPolicy: Retain
  volumeMode: Filesystem
  csi:
    driver: filestore.csi.storage.gke.io
    volumeHandle: "modeInstance/asia-northeast3-a/fs-static-demo/vol1"
    volumeAttributes:
      ip: "x.x.x.x"
      volume: "vol1"
      protocol: "NFS_V3"
  claimRef:
    name: filestore-static-pvc
    namespace: filestore-static
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: filestore-static-pvc
  namespace: filestore-static
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: ""
  resources:
    requests:
      storage: 1Gi
```

### 항목 설명

### `storageClassName: ""`

이 값이 중요함.

동적 프로비저닝을 쓰지 않고 **수동 바인딩**하겠다는 의미.

### `accessModes: ReadWriteMany`

여러 Pod가 동시에 읽기/쓰기 가능함.

NFS 계열 공유 스토리지를 쓰는 핵심 이유 중 하나가 이 모드임.

### `persistentVolumeReclaimPolicy: Retain`

PVC 삭제 후에도 Filestore 데이터를 유지하려는 설정임.

### `volumeHandle`

형식은 다음과 같음.

```
modeInstance/FILESTORE_INSTANCE_LOCATION/FILESTORE_INSTANCE_NAME/FILESTORE_SHARE_NAME
```

예시에서는:

```
modeInstance/asia-northeast3-a/fs-static-demo/vol1
```

### `volumeAttributes.ip`

Filestore 인스턴스의 내부 IP 주소

### `volumeAttributes.volume`

Filestore share 이름

### `protocol`

* `NFS_V3` 또는 생략 시 기본 NFSv3

* `NFS_V4_1` 지정 가능

---

## 5-5. 정적 PV/PVC 생성

```
kubectl apply -f preprov-filestore.yaml
```

### 확인

```
kubectl get pv
kubectl get pvc -n $NAMESPACE_STATIC
```

정상이라면 `Bound` 상태가 보여야 함.

---

## 5-6. 정적 프로비저닝용 Deployment 작성

### `static-deployment.yaml`

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: static-writer
  namespace: filestore-static
spec:
  replicas: 2
  selector:
    matchLabels:
      app: static-writer
  template:
    metadata:
      labels:
        app: static-writer
    spec:
      containers:
      - name: writer
        image: busybox
        command: ["/bin/sh", "-c"]
        args:
          - |
            while true; do
              echo "$(hostname) wrote at $(date)" >> /data/static-log.txt;
              sleep 10;
            done
        volumeMounts:
        - name: filestore-vol
          mountPath: /data
      volumes:
      - name: filestore-vol
        persistentVolumeClaim:
          claimName: filestore-static-pvc
```

### 설명

* `busybox` 컨테이너를 사용해 간단하게 파일 쓰기 테스트 수행

* 2개의 Pod가 같은 `/data/static-log.txt` 파일에 내용을 계속 기록

* `/data`는 실제로 Filestore에 마운트된 디렉터리임

---

## 5-7. 정적 프로비저닝 배포

```
kubectl apply -f static-deployment.yaml
kubectl get pods -n $NAMESPACE_STATIC
```

---

## 5-8. 정적 프로비저닝 결과 확인

### Pod 내부 파일 확인

```
kubectl exec -it -n $NAMESPACE_STATIC deploy/static-writer -- sh
```

컨테이너 안에서:

```
cat /data/static-log.txt
ls -l /data
```

또는 바로 확인:

```
kubectl exec -it -n $NAMESPACE_STATIC deploy/static-writer -- cat /data/static-log.txt
```

### 기대 결과

* 여러 Pod가 같은 파일을 공유해서 기록한 내용이 보임

* Pod를 재시작해도 파일이 유지됨

* 이는 Pod 내부 로컬 디스크가 아니라 Filestore 공유 스토리지를 쓰고 있기 때문임

---

# 6. 동적 프로비저닝 실습

동적 프로비저닝은 Kubernetes가 StorageClass를 참고해서 Filestore 리소스를 **자동으로 생성**하는 방식임.

Filestore CSI 드라이버를 활성화하면 GKE가 여러 Filestore용 StorageClass를 자동 설치함. 또한 이 기본 StorageClass들은 `volumeBindingMode: WaitForFirstConsumer`를 사용하므로 PVC를 만든 직후가 아니라, PVC를 사용하는 Pod가 스케줄될 때 실제 Filestore 인스턴스 생성이 진행됨.

---

## 6-1. 기본 StorageClass 확인

```
kubectl get sc
```

* `standard-rwx`

* `premium-rwx`

* `zonal-rwx`

* `enterprise-rwx`

* `enterprise-multishare-rwx`

### 1. standard-rwx (StorageClass)

* **용도:** 개발 및 테스트 환경 또는 성능 요구치가 낮은 공유 저장소로 사용한다.

* **GKE 설정:** `serviceLevel: standard` 파라미터를 가진 StorageClass로 정의한다.

* **특징:** 비용이 가장 저렴하며, 여러 파드(Pod)가 동시에 읽기/쓰기를 수행하는 RWX(ReadWriteMany) 모드를 지원한다.

### 2. premium-rwx (StorageClass)

* **용도:** 일반적인 프로덕션 웹 애플리케이션 및 엔터프라이즈 서비스용이다.

* **설명:** standard보다 높은 스루풋(Throughput)을 보장하며, GKE 클러스터 내에서 안정적인 파일 공유 성능을 제공한다.

### 3. zonal-rwx (StorageClass)

* **용도:** 특정 데이터 센터(Zone) 내의 컴퓨팅 리소스와 가깝게 배치하여 지연 시간을 줄여야 할 때 사용한다.

* **특징:** 고성능 처리가 필요한 스테이트풀셋(StatefulSet) 워크로드에 적합하며, 해당 영역 내에서 최적의 IOPS를 구현한다.

### 4. enterprise-rwx (StorageClass)

* **용도:** 고성능 데이터베이스(DBMS)나 금융권 시스템 등 미션 크리티컬한 워크로드용이다.

* **설명:** 가장 높은 수준의 가용성과 성능을 보장하는 StorageClass로, 무중단 운영이 필수적인 GKE 서비스에 할당한다.

### 5. enterprise-multishare-rwx (StorageClass)

* **용도:** 하나의 대규모 스토리지 풀을 여러 개의 PersistentVolume(PV)이 나누어 사용해야 하는 복합 환경에 적합하다.

* **특징:** 스토리지 효율성을 극대화할 수 있으며, 다수의 마이크로서비스(MSA)가 복합적으로 저장소를 공유할 때 관리 이점을 제공한다.

---

## 6-2. 동적 프로비저닝 방식 이해

### 방식 A. GKE가 기본 제공하는 StorageClass 사용

예: `standard-rwx`, `premium-rwx`, `enterprise-rwx`

* PVC를 생성

* Pod가 해당 PVC를 참조

* Filestore 인스턴스가 자동 생성됨

### 방식 B. multishare 기반 StorageClass 사용

예: `enterprise-multishare-rwx`

* 여러 PVC가 하나 이상의 Filestore 인스턴스 내 share로 배치됨

* Enterprise multishare 기반 공유 구조

* 더 효율적인 공유/자동 확장 모델을 제공

`enterprise-multishare-rwx`는 **동적 프로비저닝**을 통해 share lifecycle을 자동 관리함.

---

## 6-3. 사용자 정의 StorageClass 작성

`filestore.csi.storage.gke.io`를 provisioner로 갖는 커스텀 StorageClass 를 생성할 수 있으며 `tier`, `network`, `protocol`, `volumeBindingMode` 등을 지정할 수 있음.

### `filestore-example-class.yaml`

```
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: filestore-standard-custom
provisioner: filestore.csi.storage.gke.io
volumeBindingMode: Immediate
allowVolumeExpansion: true
parameters:
  tier: standard
  network: kdtmsp-vpc
  protocol: NFS_V3
```

### 항목 설명

### `provisioner: filestore.csi.storage.gke.io`

Filestore CSI 드라이버를 사용하겠다는 의미임.

### `volumeBindingMode: Immediate`

PVC 생성 즉시 프로비저닝 시작 가능

GKE 기본 제공 StorageClass는 보통 `WaitForFirstConsumer`를 사용함.

### `allowVolumeExpansion: true`

나중에 PVC 용량 확장 가능

### `parameters.tier`

서비스 티어 지정

### `parameters.network`

Filestore를 어떤 VPC에 만들지 지정

기본 네트워크가 아니라면 맞는 VPC 이름을 넣어야 함

### `parameters.protocol`

`NFS_V3` 또는 `NFS_V4_1`

---

## 6-4. StorageClass 생성

```
kubectl create namespace $NAMESPACE_DYNAMIC
kubectl apply -f filestore-example-class.yaml
```

---

## 6-5. 동적 프로비저닝용 PVC 작성

### `dynamic-pvc.yaml`

```
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: filestore-dynamic-pvc
  namespace: filestore-dynamic
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: filestore-standard-custom
  resources:
    requests:
      storage: 1Ti
```

### 설명

* 사용자는 PVC만 생성함

* CSI 드라이버가 이를 보고 Filestore 리소스를 자동 생성

* `ReadWriteMany` 이므로 여러 Pod가 함께 사용 가능

```
kubectl apply -f dynamic-pvc.yaml
```

### 확인

```
kubectl get pvc -n $NAMESPACE_DYNAMIC
kubectl get pv
```

---

## 6-6. 동적 프로비저닝용 Deployment 작성

### `dynamic-deployment.yaml`

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dynamic-writer
  namespace: filestore-dynamic
spec:
  replicas: 2
  selector:
    matchLabels:
      app: dynamic-writer
  template:
    metadata:
      labels:
        app: dynamic-writer
    spec:
      containers:
      - name: writer
        image: busybox
        command: ["/bin/sh", "-c"]
        args:
          - |
            while true; do
              echo "$(hostname) dynamic write $(date)" >> /shared/dynamic-log.txt;
              sleep 10;
            done
        volumeMounts:
        - name: filestore-vol
          mountPath: /shared
      volumes:
      - name: filestore-vol
        persistentVolumeClaim:
          claimName: filestore-dynamic-pvc
```

배포:

```
kubectl apply -f dynamic-deployment.yaml
kubectl get pods -n $NAMESPACE_DYNAMIC
```

---

## 6-7. 동적 프로비저닝 결과 확인

```
kubectl exec -it -n $NAMESPACE_DYNAMIC deploy/dynamic-writer -- sh
```

컨테이너 내부에서:

```
cat /shared/dynamic-log.txt
ls -l /shared
```

또는 바로 확인:

```
kubectl exec -it -n $NAMESPACE_DYNAMIC deploy/dynamic-writer -- cat /shared/dynamic-log.txt
```

### 기대 결과

* Filestore가 자동 생성 또는 자동 매핑됨

* 여러 Pod가 같은 공유 디렉터리를 사용함

* 파일 내용이 여러 Pod에서 공통으로 보임

---

# 7. enterprise-multishare-rwx 클래스

동적 프로비저닝에서 조금 더 실무적으로 중요한 건 `enterprise-multishare-rwx`임.

이 클래스는 **Enterprise multishares** 기반으로 동작하며, 여러 PVC가 하나의 Filestore 인스턴스 share들을 나눠 쓰는 구조를 제공함. GKE Filestore CSI driver 1.23 이상이 필요하고, 1.27 이상에서는 최대 80개의 share까지 지원함. 또한 PVC 삭제 시 share가 회수되고, 모든 share가 삭제되면 Filestore 인스턴스도 삭제될 수 있음.

### 기본 확인

```
kubectl describe sc enterprise-multishare-rwx
```

이 StorageClass가 다음과 같은 특성을 가짐.

* `Provisioner: filestore.csi.storage.gke.io`

* `Parameters: instance-storageclass-label=enterprise-multishare-rwx,multishare=true,tier=enterprise`

* `AllowVolumeExpansion: True`

### 간단한 PVC 예시

```
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: multishare-pvc
  namespace: filestore-dynamic
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: enterprise-multishare-rwx
  resources:
    requests:
      storage: 100Gi
```

### 설명

* 이 PVC 하나가 곧 Filestore 인스턴스 전체를 독점하는 것이 아니라

* multishare 구조에서 하나의 share처럼 배치될 수 있음

* 여러 애플리케이션 팀이 작은 RWX 스토리지를 많이 요구하는 환경에서 효율적임

---

# 8. 정적 프로비저닝과 동적 프로비저닝 비교

## 8-1. 구조 비교

### 정적 프로비저닝

* Filestore 인스턴스를 먼저 생성

* 운영자가 PV를 직접 작성

* PVC가 해당 PV에 바인딩

* 제어권이 크고 구조가 명확함

### 동적 프로비저닝

* StorageClass만 준비

* 사용자는 PVC만 생성

* CSI 드라이버가 Filestore를 자동 생성 또는 자동 할당

* 자동화 친화적임

---

## 8-2. 실습 관점 비교

| 항목 | 정적 프로비저닝 | 동적 프로비저닝 |
| --- | --- | --- |
| 스토리지 생성 시점 | Kubernetes 밖에서 미리 생성 | PVC/Pod 생성 시 자동 |
| 관리 주체 | 운영자 중심 | 플랫폼/자동화 중심 |
| 실습 난이도 | 구조 이해는 쉬움, 작업은 많음 | 자동화 이해 필요 |
| 운영 적합성 | 기존 자원 재사용에 적합 | 신규 배포 자동화에 적합 |
| 추적성 | 매우 명확함 | 자동 생성이라 추적 설계 필요 |

---

# 9. 콘솔에서 확인할 항목

## 9-1. GKE 콘솔

1. **Kubernetes Engine > Clusters**

2. 대상 클러스터 클릭

3. **Features**에서 Filestore CSI driver 활성화 확인

4. **Workloads**에서 배포된 Pod 상태 확인

5. **Storage** 관련 리소스는 `kubectl`과 함께 병행 확인

---

## 9-2. Filestore 콘솔

1. **Filestore** 메뉴 이동

2. 정적 프로비저닝용 인스턴스 확인

3. 동적 프로비저닝 후 자동 생성된 인스턴스 또는 share 확인

4. 용량, 네트워크, IP 확인

---

# 10. 자주 발생하는 문제

## 10-1. PVC가 Pending 상태로 오래 머무름

원인 후보:

* Filestore CSI 드라이버 미활성화

* StorageClass 이름 오타

* 동적 프로비저닝인데 Pod가 아직 생성되지 않음

  기본 StorageClass는 `WaitForFirstConsumer`를 쓸 수 있음

* 요청 용량이 선택한 티어의 최소 용량 조건과 맞지 않음

GKE 기본 StorageClass는 `WaitForFirstConsumer`를 사용하므로 PVC 생성 직후 바로 Filestore 인스턴스가 만들어지지 않을 수 있음. Pod가 PVC를 참조해야 프로비저닝이 시작될 수 있음.

---

## 10-2. 마운트 실패

원인 후보:

* Filestore와 GKE가 같은 VPC 또는 접근 가능한 네트워크가 아님

* 방화벽 규칙 문제

* Filestore IP 오타

* share 이름 오타

* PV의 `volumeHandle` 형식 오류

---

## 10-3. 정적 프로비저닝에서 Bound가 안 됨

원인 후보:

* PV와 PVC의 `storageClassName` 값이 맞지 않음

* 용량 조건 불일치

* claimRef namespace 또는 name 불일치

* accessModes 불일치

---

# 11. 정리

## 정적 프로비저닝 핵심

* Filestore를 먼저 만듦

* PV에서 정확한 Filestore 인스턴스와 share를 지정

* 기존 자원을 Kubernetes에 연결하는 방식

## 동적 프로비저닝 핵심

* StorageClass와 PVC 중심

* CSI 드라이버가 Filestore를 자동 생성/관리

* 운영 자동화에 적합

## 실무 관점에서 기억할 점

* **기존 Filestore를 연결해야 하면 정적 프로비저닝**

* **새 서비스 배포 자동화가 중요하면 동적 프로비저닝**

* **작은 RWX 스토리지를 여러 개 유연하게 쓰려면 enterprise-multishare-rwx 고려**

---