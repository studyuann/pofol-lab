---
title: "실습 2 EBS CSI 기반 동적 볼륨 프로비저닝 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "모범사례기반 AWS 고급아키텍처 설계"]
is_public: true
draft: false
---

# 실습 2. EBS CSI 기반 동적 볼륨 프로비저닝 실습

## 1. 실습 목표

이번 실습에서는 EKS에서 **Amazon EBS CSI Driver**를 설치하고, PVC를 생성했을 때 **Amazon EBS 볼륨이 자동 생성**되어 Pod에 연결되는 과정을 확인함.

이 실습을 통해 다음을 이해할 수 있음.

* EBS CSI Driver가 왜 필요한가

* StorageClass, PV, PVC 관계

* 동적 프로비저닝 개념

* EKS와 Amazon EBS의 연동 방식

* 온프레미스 스토리지 구성과 EKS 스토리지 구성의 차이

AWS는 Amazon EBS CSI driver가 Kubernetes 볼륨 수명주기와 Amazon EBS API를 연결하는 CSI 플러그인이라고 설명함.

---

## 2. 실습 개요

Kubernetes에서 스토리지는 보통 아래 흐름으로 이해하면 됨.

* **StorageClass**: 어떤 방식으로 스토리지를 만들지 정의

* **PersistentVolumeClaim(PVC)**: 사용자가 저장소를 요청

* **PersistentVolume(PV)**: 실제 제공되는 저장소

* **Pod**: PVC를 마운트해서 사용

온프레미스에서는 NFS, Ceph, SAN/NAS, CSI 드라이버, 백엔드 스토리지 구성을 직접 준비하는 경우가 많음.

반면 EKS에서는 EBS CSI driver가 설치되어 있으면 PVC 요청이 실제 **EBS 볼륨 생성**으로 이어질 수 있음.

---

## 3. 실습 전 확인 사항

다음 조건이 준비되어 있어야 함.

1. EKS 클러스터가 생성되어 있어야 함

2. `kubectl`과 `aws cli` 가 사용 가능해야 함

3. 워커 노드는 **EC2 기반 노드**여야 함

4. `aws-ebs-csi-driver` add-on이 설치되어 있어야 함

5. add-on이 사용할 IAM 권한이 준비되어 있어야 함

AWS는 EBS 볼륨을 Fargate Pod에 마운트할 수 없다고 명시하고 있음. 또한 EBS CSI 컨트롤러는 설치 가능하지만, 실제 노드 측 DaemonSet은 EC2 인스턴스에서만 동작한다고 설명함.

먼저 노드 상태를 확인함.

```
kubectl get nodes -o wide
```

---

## 4. EBS CSI Driver 설치 여부 확인

현재 add-on 설치 상태를 확인함.

```
aws eks list-addons --cluster-name my-eks-cluster --region ap-northeast-2
```

출력에 `aws-ebs-csi-driver`가 보이면 add-on이 설치된 상태임. EKS add-on 이름은 `aws-ebs-csi-driver`임.

조금 더 자세히 확인하려면 다음 명령도 가능함.

```
aws eks describe-addon --cluster-name my-eks-cluster --addon-name aws-ebs-csi-driver --region ap-northeast-2
```

Kubernetes 쪽에서도 확인 가능함.

```
kubectl get pods -n kube-system
```

`ebs-csi-controller` 관련 Pod가 보이면 설치된 상태일 가능성이 높음.

---

## 5. IAM 역할 준비

## EBS CSI Driver용 권한

EBS CSI driver는 AWS API를 호출해 EBS 볼륨을 생성하고 연결해야 하므로 IAM 권한이 필요함. AWS는 이 권한을 위해 `AmazonEBSCSIDriverPolicy` 관리형 정책을 사용하도록 안내함. 또한 권한 부여 방식으로는 **EKS Pod Identity** 사용을 권장하고, 준비되지 않았다면 **IRSA**를 사용할 수 있다고 설명함. ([docs.aws.amazon.com](https://docs.aws.amazon.com/eks/latest/userguide/ebs-csi?utm_source=chatgpt.com))

### 5-1. Pod Identity Agent 설치 여부 확인

```
aws eks list-addons --cluster-name my-eks-cluster --region ap-northeast-2
```

여기에 `eks-pod-identity-agent`가 없으면 먼저 설치함.

```
eksctl create addon --cluster my-eks-cluster --name eks-pod-identity-agent --region ap-northeast-2
```

AWS는 Pod Identity를 사용하려면 Pod Identity Agent add-on이 필요하다고 설명함.

### 5-2. EBS CSI Driver용 IAM 역할 생성

먼저 trust policy 파일을 만듦.

아래 내용을 `ebs-csi-trust-policy.json` 파일로 저장함.

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowEksAuthToAssumeRoleForPodIdentity",
      "Effect": "Allow",
      "Principal": {
        "Service": "pods.eks.amazonaws.com"
      },
      "Action": [
        "sts:AssumeRole",
        "sts:TagSession"
      ]
    }
  ]
}
```

작성:

```
notepad ebs-csi-trust-policy.json
```

역할 생성:

```
aws iam create-role --role-name AmazonEKS_EBS_CSI_DriverRole --assume-role-policy-document file://ebs-csi-trust-policy.json
```

정책 연결:

```
aws iam attach-role-policy --role-name AmazonEKS_EBS_CSI_DriverRole --policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy
```

EBS CSI driver에 `AmazonEBSCSIDriverPolicy`를 연결

### 5-3. 역할 ARN 확인

```
aws iam get-role --role-name AmazonEKS_EBS_CSI_DriverRole
```

출력의 `Arn` 값을 복사해 둠.

예시:

```
arn:aws:iam::123456789012:role/AmazonEKS_EBS_CSI_DriverRole
```

---

## 6. EBS CSI Driver add-on 설치

이제 EBS CSI driver add-on을 설치함.

EKS add-on은 AWS CLI, 콘솔, `eksctl`로 만들 수 있음. AWS는 add-on 생성 방법으로 이 세 가지를 안내함.

### 6-1. AWS CLI로 설치

```
aws eks create-addon --cluster-name my-eks-cluster --addon-name aws-ebs-csi-driver --pod-identity-associations serviceAccount=ebs-csi-controller-sa,roleArn=arn:aws:iam::123456789012:role/AmazonEKS_EBS_CSI_DriverRole --region ap-northeast-2
```

이 명령은 `aws-ebs-csi-driver` add-on을 만들고, `ebs-csi-controller-sa` 서비스어카운트에 IAM 역할을 연결함. AWS는 add-on 생성 시 Pod Identity association을 함께 지정할 수 있다고 설명함.

### 6-2. eksctl로 설치

## 대체 방법

`eksctl`을 쓰고 싶다면 add-on 생성도 가능함.

```
eksctl create addon --cluster my-eks-cluster --name aws-ebs-csi-driver --region ap-northeast-2
```

다만 권한 연결까지 포함하려면 AWS CLI 방식이 더 분명함. `eksctl`은 EKS add-on 관리 기능을 제공함.

### 6-3. 설치 확인

```
aws eks list-addons --cluster-name my-eks-cluster --region ap-northeast-2
aws eks describe-addon --cluster-name my-eks-cluster --addon-name aws-ebs-csi-driver --region ap-northeast-2
kubectl get pods -n kube-system
```

---

## 7. StorageClass 확인

EBS CSI driver가 준비되었으면 StorageClass를 확인함.

```
kubectl get storageclass
```

예상 예시는 다음과 비슷함.

```
NAME            PROVISIONER         RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
ebs-sc          ebs.csi.aws.com     Delete          WaitForFirstConsumer   true                   10m
```

핵심은 `PROVISIONER`가 `ebs.csi.aws.com`인지 확인하는 것임. AWS는 EBS CSI driver의 프로비저너 이름으로 `ebs.csi.aws.com`을 사용함.

---

## 8. StorageClass 생성

## 없는 경우만 수행

기본 StorageClass가 없다면 직접 생성함.

아래 내용을 `ebs-sc.yaml` 파일로 저장함.

```
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ebs-sc
provisioner: ebs.csi.aws.com
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
parameters:
  type: gp3
```

작성:

```
notepad ebs-sc.yaml
```

적용:

```
kubectl apply -f ebs-sc.yaml
```

### 항목 설명

* `provisioner: ebs.csi.aws.com`

  EBS CSI driver가 실제 볼륨을 생성함

* `volumeBindingMode: WaitForFirstConsumer`

  Pod가 실제로 스케줄될 때까지 볼륨 생성을 지연함

* `allowVolumeExpansion: true`

  나중에 볼륨 크기 확장을 허용함

* `type: gp3`

  EBS 볼륨 유형을 `gp3`로 지정함

AWS는 EBS CSI driver와 EBS 볼륨 사용을 연결하고, 일반적인 EBS 스토리지 사용 시 add-on을 통해 driver를 설치하도록 안내함.

---

## 9. PVC 생성

이제 EBS 볼륨을 요청하는 PVC를 생성함.

아래 내용을 `ebs-pvc.yaml` 파일로 저장함.

```
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ebs-pvc
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: ebs-sc
  resources:
    requests:
      storage: 4Gi
```

적용:

```
kubectl apply -f ebs-pvc.yaml
```

### 항목 설명

* `ReadWriteOnce`

  일반적인 EBS 블록 스토리지 사용 방식에 맞는 접근 모드임

* `storageClassName: ebs-sc`

  앞에서 만든 StorageClass 사용

* `storage: 4Gi`

  4Gi 크기 요청

---

## 10. PVC 상태 확인

```
kubectl get pvc
```

처음에는 다음처럼 `Pending`일 수 있음.

```
NAME      STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
ebs-pvc   Pending                                      ebs-sc         10s
```

이 상태는 `WaitForFirstConsumer` 모드 때문에 이상한 것이 아닐 수 있음. Pod가 이 PVC를 실제로 사용하려 할 때 PV 생성이 이어질 수 있음.

---

## 11. PVC를 사용하는 Pod 생성

아래 내용을 `app-ebs.yaml` 파일로 저장함.

```
apiVersion: v1
kind: Pod
metadata:
  name: app-ebs
spec:
  containers:
    - name: app
      image: nginx
      volumeMounts:
        - mountPath: /usr/share/nginx/html
          name: ebs-volume
  volumes:
    - name: ebs-volume
      persistentVolumeClaim:
        claimName: ebs-pvc
```

적용:

```
kubectl apply -f app-ebs.yaml
```

---

## 12. Pod, PVC, PV 확인

```
kubectl get pods
kubectl get pvc
kubectl get pv
```

정상 흐름은 다음과 같음.

* Pod → `Running`

* PVC → `Bound`

* PV → 자동 생성됨

예상 예시:

```
NAME      READY   STATUS    RESTARTS   AGE
app-ebs   1/1     Running   0          1m
```

```
NAME      STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
ebs-pvc   Bound    pvc-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx   4Gi        RWO            ebs-sc         2m
```

```
NAME                                       CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM             STORAGECLASS   AGE
pvc-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx   4Gi        RWO            Delete           Bound    default/ebs-pvc   ebs-sc         2m
```

---

## 13. Pod 안에서 쓰기 확인

```
kubectl exec -it app-ebs -- sh
```

컨테이너 안에서 실행:

```
echo EBS Volume Test > /usr/share/nginx/html/index
cat /usr/share/nginx/html/index
```

정상이라면 다음처럼 보임.

```
EBS Volume Test
```

이 파일은 컨테이너 로컬 디스크가 아니라, PVC를 통해 연결된 EBS 볼륨 위에 기록되는 것임.

---

## 14. 온프레미스 Kubernetes와 비교 포인트

### 온프레미스 Kubernetes

* CSI 드라이버와 스토리지 백엔드를 직접 구성해야 하는 경우가 많음

* NFS, Ceph, SAN/NAS 설계를 직접 해야 할 수 있음

### EKS

* EBS CSI driver add-on 설치

* IAM 권한 연결

* PVC 생성 시 실제 EBS 볼륨 자동 생성 가능

---

## 15. 실습 후 정리

```
kubectl delete pod app-ebs
kubectl delete pvc ebs-pvc
kubectl delete -f ebs-sc.yaml
```