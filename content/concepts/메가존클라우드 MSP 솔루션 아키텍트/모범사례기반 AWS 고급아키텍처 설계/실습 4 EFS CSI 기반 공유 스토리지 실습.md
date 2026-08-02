---
title: "실습 4 EFS CSI 기반 공유 스토리지 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "모범사례기반 AWS 고급아키텍처 설계"]
is_public: true
draft: false
---

# 실습 4. EFS CSI 기반 공유 스토리지 실습

## 정적 PV 방식 + StorageClass 동적 프로비저닝 방식

## 1. 실습 목표

이번 실습에서는 Amazon EFS를 EKS에 연결하고, **여러 Pod가 동시에 같은 저장소를 마운트해서 파일을 공유하는 구조**를 확인함.

또한 같은 EFS 실습을 **정적 PV 방식**과 **StorageClass 기반 동적 프로비저닝 방식** 두 가지로 나누어 비교함.

이 실습을 통해 다음을 이해할 수 있음.

* EFS와 EBS의 차이

* 블록 스토리지와 파일 스토리지의 차이

* `ReadWriteMany` 접근 방식의 의미

* 정적 PV 방식과 동적 프로비저닝 방식의 차이

* EFS Access Point가 어떤 역할을 하는가

---

## 2. 실습 개요

이 실습은 두 단계로 진행함.

### 1단계: 정적 PV 방식

* 관리자가 PV를 직접 생성함

* PVC가 그 PV에 바인딩됨

* 여러 Pod가 같은 PVC를 마운트함

### 2단계: StorageClass 기반 동적 프로비저닝 방식

* 관리자가 StorageClass만 준비함

* 사용자는 PVC만 생성함

* EFS CSI 드라이버가 EFS Access Point를 자동 생성함

* PVC는 자동 생성된 PV에 바인딩됨

**“EFS는 공유 파일 스토리지이고, EKS에서는 이를 정적/동적 두 방식으로 연결할 수 있다”**

---

## 3. 실습 전 확인 사항

다음 조건이 준비되어 있어야 함.

1. EKS 클러스터가 생성되어 있어야 함

2. `kubectl`과 `aws` CLI가 사용 가능해야 함

3. EFS 파일 시스템이 이미 하나 존재해야 함

4. EFS CSI driver가 설치되어 있어야 함

5. EKS 노드가 EFS mount target에 접근 가능해야 함

6. 동적 프로비저닝 방식은 **EC2 기반 노드 환경**이어야 함

---

## 4. EFS CSI Driver 설치 여부 확인

먼저 add-on 상태를 확인함.

```
aws eks list-addons --cluster-name my-eks-cluster --region ap-northeast-2
```

여기서 `aws-efs-csi-driver`가 보여야 함.

또는 Kubernetes 쪽에서도 확인 가능함.

```
kubectl get pods -n kube-system
```

### 설치가 안 되어 있으면

```
eksctl create addon --cluster my-eks-cluster --name aws-efs-csi-driver --region ap-northeast-2
```

---

## 5. EFS 파일 시스템 ID 확인

현재 리전의 EFS 파일 시스템을 조회함.

```
aws efs describe-file-systems --region ap-northeast-2
```

출력에서 `FileSystemId` 값을 확인함.

예시:

```
fs-0abc1234def567890
```

이 값을 이후 YAML의 `fileSystemId` 또는 `volumeHandle`에 사용함.

EFS 에 연결된 보안그룹에 TCP 2049를 Inbound 규칙에 추가

---

# Part A. 정적 PV 방식

## 6. 정적 PV 방식 설명

정적 방식은 관리자가 먼저 PV를 만들고, PVC가 그 PV에 연결되는 방식임.

개념 이해에는 가장 쉬움.

즉, 이 방식은 다음 흐름임.

* EFS 파일 시스템 준비됨

* PV를 직접 생성함

* PVC가 PV에 바인딩됨

* 여러 Pod가 같은 PVC를 사용함

---

## 7. 정적 PV 생성

아래 내용을 `efs-pv.yaml` 파일로 저장함.

```
apiVersion: v1
kind: PersistentVolume
metadata:
  name: efs-pv
spec:
  capacity:
    storage: 5Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteMany
  persistentVolumeReclaimPolicy: Retain
  csi:
    driver: efs.csi.aws.com
    volumeHandle: fs-0abc1234def567890
```

여기서 `volumeHandle`은 실제 EFS 파일 시스템 ID로 바꿔야 함.

CMD에서 작성:

```
notepad efs-pv.yaml
```

적용:

```
kubectl apply -f efs-pv.yaml
```

### 항목 설명

* `accessModes: ReadWriteMany`

  여러 Pod가 동시에 읽기/쓰기 가능함

* `persistentVolumeReclaimPolicy: Retain`

  PVC를 삭제해도 실제 스토리지를 바로 지우지 않음

* `driver: efs.csi.aws.com`

  EFS CSI 드라이버 사용

* `volumeHandle`

  실제 EFS 파일 시스템 ID

---

## 8. 정적 PVC 생성

아래 내용을 `efs-pvc.yaml` 파일로 저장함.

```
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: efs-pvc
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 5Gi
  volumeName: efs-pv
```

적용:

```
kubectl apply -f efs-pvc.yaml
```

확인:

```
kubectl get pv
kubectl get pvc
```

정상이라면 `efs-pvc`가 `Bound` 상태가 됨.

---

## 9. 같은 PVC를 두 Pod에 연결

### Pod 1

`efs-pod1.yaml`

```
apiVersion: v1
kind: Pod
metadata:
  name: efs-pod1
spec:
  containers:
    - name: app
      image: nginx
      volumeMounts:
        - name: shared-data
          mountPath: /usr/share/nginx/html
  volumes:
    - name: shared-data
      persistentVolumeClaim:
        claimName: efs-pvc
```

### Pod 2

`efs-pod2.yaml`

```
apiVersion: v1
kind: Pod
metadata:
  name: efs-pod2
spec:
  containers:
    - name: app
      image: nginx
      volumeMounts:
        - name: shared-data
          mountPath: /usr/share/nginx/html
  volumes:
    - name: shared-data
      persistentVolumeClaim:
        claimName: efs-pvc
```

적용:

```
kubectl apply -f efs-pod1.yaml
kubectl apply -f efs-pod2.yaml
```

확인:

```
kubectl get pods
```

---

## 10. 공유 저장소 동작 확인

## 정적 방식

첫 번째 Pod에서 파일을 생성함.

```
kubectl exec -it efs-pod1 -- sh
```

컨테이너 내부에서 실행:

```
echo EFS Shared Storage Test > /usr/share/nginx/html/index.html
cat /usr/share/nginx/html/index.html
```

두 번째 Pod에서 같은 파일을 확인함.

```
kubectl exec -it efs-pod2 -- sh
```

컨테이너 내부에서 실행:

```
cat /usr/share/nginx/html/index.html
```

같은 내용이 보이면 공유 스토리지가 정상 동작한 것임.

---

# Part B. StorageClass 기반 동적 프로비저닝 방식

## 11. 동적 프로비저닝 방식 설명

동적 방식은 관리자가 일일이 PV를 만들지 않고, StorageClass만 준비해 두면 사용자가 PVC만 만들어도 자동으로 PV가 생성되는 방식임.

EFS에서는 이 동적 프로비저닝이 **EFS Access Point 자동 생성**과 연결됨.

즉, 이 방식은 다음 흐름임.

* StorageClass 생성

* PVC 생성

* EFS CSI 드라이버가 Access Point 생성

* PV 자동 생성

* Pod가 PVC 사용

---

## 12. StorageClass 생성

아래 내용을 `efs-sc.yaml` 파일로 저장함.

```
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: efs-sc
provisioner: efs.csi.aws.com
parameters:
  provisioningMode: efs-ap
  fileSystemId: fs-0abc1234def567890
  directoryPerms: "700"
  gidRangeStart: "1000"
  gidRangeEnd: "2000"
  basePath: "/dynamic_provisioning"
reclaimPolicy: Delete
volumeBindingMode: Immediate
```

`fileSystemId`는 실제 EFS 파일 시스템 ID로 변경해야 함.

작성:

```
notepad efs-sc.yaml
```

적용:

```
kubectl apply -f efs-sc.yaml
```

### 핵심 항목 설명

* `provisioner: efs.csi.aws.com`

  EFS CSI 드라이버 사용

* `provisioningMode: efs-ap`

  Access Point 기반 동적 프로비저닝

* `fileSystemId`

  어느 EFS 파일 시스템 안에서 Access Point를 만들지 지정

* `basePath`

  Access Point가 생성될 기본 경로

* `reclaimPolicy: Delete`

  실습 편의를 위한 설정

---

## PVC에서 PV를 연결하기 위한 권한 설정

## 1) 현재 클러스터 이름과 리전 변수 지정

```
exportCLUSTER_NAME=<클러스터이름>
exportAWS_REGION=<리전>
exportACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
```

예시:

```
exportCLUSTER_NAME=이니셜-eks-cluster
exportAWS_REGION=ap-northeast-2
exportACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
```

명령 설명:

* `export` 는 현재 셸 세션에 변수를 저장함

* `CLUSTER_NAME` 은 EKS 클러스터 이름

* `AWS_REGION` 은 클러스터가 있는 리전

* `ACCOUNT_ID` 는 현재 로그인한 AWS 계정 번호를 자동으로 가져옴

---

## 2) OIDC provider가 있는지 확인

IRSA(IAM Role for Service Accounts)를 쓰려면 EKS OIDC(OpenID Connect) provider가 먼저 있어야 함.

```
oidc_id=$(aws eks describe-cluster --name $CLUSTER_NAME --region$AWS_REGION --query "cluster.identity.oidc.issuer" --output text | cut -d'/' -f 5)
echo $oidc_id
aws iam list-open-id-connect-providers | grep $oidc_id
```

결과가 안 나오면 OIDC provider를 생성해야 함.

`eksctl` 이 있으면 가장 간단함.

```
eksctl utils associate-iam-oidc-provider--cluster$CLUSTER_NAME--region$AWS_REGION--approve
```

이 명령은 EKS 클러스터의 OIDC issuer를 IAM OIDC provider로 등록함.

IRSA가 동작하려면 이 단계가 반드시 맞아야 함.

---

## 3) EFS CSI용 IAM Role 생성

가장 쉬운 방법은 `eksctl create iamserviceaccount` 사용임.

```
eksctl create iamserviceaccount \
--name efs-csi-controller-sa \
--namespace kube-system \
--cluster $CLUSTER_NAME \
--region $AWS_REGION \
--role-name AmazonEKS_EFS_CSI_DriverRole \
--attach-policy-arn arn:aws:iam::aws:policy/service-role/AmazonEFSCSIDriverPolicy \
--approve \
--override-existing-serviceaccounts
```

이 명령이 하는 일:

* `efs-csi-controller-sa` 서비스어카운트에 IAM Role 연결

* `AmazonEFSCSIDriverPolicy` 를 role에 attach

* 서비스어카운트에 `eks.amazonaws.com/role-arn` annotation 자동 추가

* 기존 같은 이름의 service account가 있어도 덮어써서 반영

---

## 4) annotation이 실제로 붙었는지 확인

```
kubectl-n kube-systemget sa efs-csi-controller-sa-o yaml
```

이제 아래 같은 항목이 보여야 함.

```
metadata:
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::<계정ID>:role/AmazonEKS_EFS_CSI_DriverRole
```

이게 없으면 여전히 IRSA가 안 붙은 상태임.

IRSA에서는 서비스어카운트 annotation이 핵심 연결점임.

---

## 5) controller가 그 서비스어카운트를 쓰는지 확인

```
kubectl-n kube-systemget deploy efs-csi-controller-ojsonpath='{.spec.template.spec.serviceAccountName}'
echo
```

결과가 반드시 아래여야 함.

```
efs-csi-controller-sa
```

다른 이름이면, role을 잘 만들어도 controller가 못 씀.

---

## 6) controller 재시작

기존 파드가 이전 상태를 잡고 있을 수 있으니 재시작함.

```
kubectl-n kube-system rolloutrestart deployment efs-csi-controller
kubectl-n kube-system rollout status deployment efs-csi-controller
```

명령 설명:

* `rollout restart` 는 Deployment의 Pod를 새로 띄움

* 새 Pod는 수정된 ServiceAccount annotation 기준으로 AWS 자격 증명을 다시 가져옴

* `rollout status` 는 재시작이 정상 완료됐는지 확인함

---

## 13. 동적 PVC 생성

아래 내용을 `efs-dynamic-pvc.yaml` 파일로 저장함.

```
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: efs-dynamic-pvc
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: efs-sc
  resources:
    requests:
      storage: 5Gi
```

적용:

```
kubectl apply -f efs-dynamic-pvc.yaml
```

확인:

```
kubectl get pvc
kubectl get pv
kubectl get storageclass
```

정상이라면 PVC가 `Bound` 상태가 되고, PV가 자동 생성됨.

---

## 14. 동적 PVC를 두 Pod에 연결

### Pod 1

`efs-dynamic-pod1.yaml`

```
apiVersion: v1
kind: Pod
metadata:
  name: efs-dynamic-pod1
spec:
  containers:
    - name: app
      image: nginx
      volumeMounts:
        - name: shared-data
          mountPath: /usr/share/nginx/html
  volumes:
    - name: shared-data
      persistentVolumeClaim:
        claimName: efs-dynamic-pvc
```

### Pod 2

`efs-dynamic-pod2.yaml`

```
apiVersion: v1
kind: Pod
metadata:
  name: efs-dynamic-pod2
spec:
  containers:
    - name: app
      image: nginx
      volumeMounts:
        - name: shared-data
          mountPath: /usr/share/nginx/html
  volumes:
    - name: shared-data
      persistentVolumeClaim:
        claimName: efs-dynamic-pvc
```

적용:

```
kubectl apply -f efs-dynamic-pod1.yaml
kubectl apply -f efs-dynamic-pod2.yaml
```

확인:

```
kubectl get pods
```

---

## 15. 공유 저장소 동작 확인

## 동적 방식

첫 번째 Pod에서 파일 생성:

```
kubectl exec -it efs-dynamic-pod1 -- sh
```

컨테이너 내부에서 실행:

```
echo EFS Dynamic Provisioning Test > /usr/share/nginx/html/index.html
cat /usr/share/nginx/html/index.html
```

두 번째 Pod에서 확인:

```
kubectl exec -it efs-dynamic-pod2 -- sh
```

컨테이너 내부에서 실행:

```
cat /usr/share/nginx/html/index.html
```

같은 내용이 보이면 동적 방식도 공유 스토리지로 정상 동작한 것임.

---

## 16. Access Point 확인 방법

StorageClass 기반 동적 프로비저닝의 핵심은 **EFS Access Point가 자동 생성되는지 확인하는 것**임.

### AWS 콘솔에서 확인

### 방법 1

**AWS Console → Amazon EFS → 왼쪽 메뉴** `Access points`

### 방법 2

**AWS Console → Amazon EFS → File systems → 해당 File System 선택 →** `Access points` **탭**

### AWS CLI에서 확인

전체 Access Point 목록:

```
aws efs describe-access-points --region ap-northeast-2
```

특정 파일 시스템 기준 조회:

```
aws efs describe-access-points --file-system-id fs-0abc1234def567890 --region ap-northeast-2
```

특정 Access Point 상세 조회:

```
aws efs describe-access-points --access-point-id fsap-0123456789abcdef0 --region ap-northeast-2
```

### 실습에서 확인할 포인트

* PVC 생성 전보다 Access Point가 하나 더 생겼는지

* 해당 Access Point가 같은 `fileSystemId` 아래에 생성되었는지

* `basePath` 아래 경로가 반영되는지

즉,

**PVC 생성 → PV 자동 생성 → Access Point 자동 생성**

이 흐름을 확인하면 됨.

---

## 17. 정적 방식과 동적 방식 비교

| 항목 | 정적 PV 방식 | StorageClass 동적 방식 |
| --- | --- | --- |
| 준비 방식 | PV를 먼저 직접 생성 | StorageClass만 준비 |
| 사용자 요청 | PVC가 기존 PV에 바인딩 | PVC만 만들면 자동 처리 |
| AWS 측 동작 | 기존 EFS 파일 시스템 직접 사용 | Access Point 자동 생성 |
| 운영 편의성 | 개념 이해 쉬움 | 자동화에 유리 |
| 운영 감각 | 실습용으로 단순함 | 실제 운영 구조에 더 가까움 |

---

## 18. 자주 발생하는 문제

### 18-1. PVC가 Pending 상태인 경우

확인:

```
kubectl get storageclass
kubectl get pvc
kubectl describe pvc efs-dynamic-pvc
```

가능한 원인:

* EFS CSI 드라이버 미설치

* `fileSystemId` 오타

* StorageClass 이름 오타

* IAM 권한 부족

* Fargate 환경에서 동적 프로비저닝 시도

### 18-2. Pod가 Running이 안 되는 경우

확인:

```
kubectl describe pod efs-pod1
kubectl describe pod efs-pod2
kubectl describe pod efs-dynamic-pod1
kubectl describe pod efs-dynamic-pod2
```

가능한 원인:

* EFS mount target 접근 불가

* 보안 그룹 문제

* PV/PVC 바인딩 문제

### 18-3. Access Point가 안 보이는 경우

확인:

```
aws efs describe-access-points --file-system-id fs-0abc1234def567890 --region ap-northeast-2
kubectl get pvc
kubectl get pv
```

가능한 원인:

* PVC가 실제로 Bound 되지 않음

* EFS CSI 드라이버가 동적 프로비저닝에 실패함

* `provisioningMode: efs-ap` 설정 오류

---

## 19. 실습 후 정리 명령

### 정적 방식 정리

```
kubectl delete pod efs-pod1
kubectl delete pod efs-pod2
kubectl delete pvc efs-pvc
kubectl delete pv efs-pv
```

### 동적 방식 정리

```
kubectl delete pod efs-dynamic-pod1
kubectl delete pod efs-dynamic-pod2
kubectl delete pvc efs-dynamic-pvc
kubectl delete storageclass efs-sc
```

동적 방식은 `reclaimPolicy: Delete`로 설정했으므로 실습 후 Access Point가 정리되는지도 확인.

---

## 20. 실습 정리

* EFS는 여러 Pod가 동시에 사용할 수 있는 공유 파일 스토리지임

* 정적 방식은 PV를 직접 만들기 때문에 이해가 쉬움

* 동적 방식은 StorageClass와 Access Point 자동 생성 때문에 운영 자동화에 더 가까움.

* EKS에서는 Kubernetes의 PVC 요청이 실제 AWS EFS 구조와 연결됨

* 온프레미스에서 NFS/공유 파일 시스템으로 하던 개념을 EKS에서는 관리형 EFS로 실습할 수 있음

---