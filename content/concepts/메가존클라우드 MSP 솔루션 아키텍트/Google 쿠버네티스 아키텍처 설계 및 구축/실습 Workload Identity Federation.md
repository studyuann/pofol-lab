---
title: "실습 Workload Identity Federation"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Google 쿠버네티스 아키텍처 설계 및 구축"]
is_public: true
draft: false
---

# 실습. Workload Identity Federation

## 1. 실습 목표

* 기존 GKE Standard 클러스터에 Workload Identity Federation for GKE를 활성화함

* Kubernetes ServiceAccount를 생성함

* Cloud Storage 버킷에 대한 IAM 권한을 Kubernetes ServiceAccount에 부여함

* Pod에서 별도 서비스 계정 키 파일 없이 Google Cloud API에 접근함

* 실습 종료 후 IAM 권한과 리소스를 정리함

---

## 2. 실습 구성

1. GKE Standard 클러스터 준비

2. Workload Identity Federation for GKE 활성화

3. 노드풀에 GKE metadata server 적용

4. Kubernetes 네임스페이스와 ServiceAccount 생성

5. Cloud Storage 버킷 생성

6. 버킷 권한을 KSA에 부여

7. 테스트 Pod 실행

8. Pod 내부에서 인증 및 접근 확인

9. 리소스 정리

---

## 3. 사전 준비

## 3-1. 필요한 권한

실습용 계정에는 최소한 다음 역할이 있어야 함.

* `roles/container.admin`

* `roles/iam.serviceAccountAdmin`

또한 프로젝트에서 **IAM Service Account Credentials API**도 활성화돼 있어야 함.

---

## 3-2. 환경 변수 설정

Cloud Shell에서 아래 값을 먼저 설정함.

```
export PROJECT_ID=$(gcloud config get-value project)
export CLUSTER_NAME=이니셜-std-cluster-1
export LOCATION=asia-northeast3-c
export NODEPOOL_NAME=이니셜-node-pool
export NAMESPACE=demo-wif
export KSA_NAME=ksa-demo
export BUCKET_NAME=${PROJECT_ID}-wif-demo-$(date +%s)
```

프로젝트 번호도 함께 변수로 저장함.

```
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
```

확인:

```
echo $PROJECT_ID
echo $PROJECT_NUMBER
echo $CLUSTER_NAME
echo $LOCATION
```

---

## 4. 실습 1 - API 활성화

필요 API를 활성화함.

```
gcloud services enable container.googleapis.com
gcloud services enable iamcredentials.googleapis.com
gcloud services enable storage.googleapis.com
```

---

## 5. 실습 2 - Standard 클러스터 준비

없다면 최소 설정으로 생성함.

```
gcloud container clusters create $CLUSTER_NAME \
  --zone=$LOCATION
```

생성 확인:

```
gcloud container clusters list
```

클러스터 접속 정보 등록:

```
gcloud container clusters get-credentials $CLUSTER_NAME \
  --zone=$LOCATION
```

---

## 6. 실습 3 - 클러스터에 Workload Identity Federation for GKE 활성화

## 6-1. gcloud로 활성화

기존 Standard 클러스터에 Workload Identity Federation for GKE를 활성화함.

```
gcloud container clusters update $CLUSTER_NAME \
  --location=$LOCATION \
  --workload-pool=${PROJECT_ID}.svc.id.goog
```

---

## 6-2. 활성화 여부 확인

```
gcloud container clusters describe $CLUSTER_NAME \
  --location=$LOCATION \
  --format="value(workloadIdentityConfig.workloadPool)"
```

정상이라면 다음과 비슷하게 보임.

```
PROJECT_ID.svc.id.goog
```

---

## 7. 실습 4 - 노드풀에 GKE metadata server 적용

클러스터에서 기능을 켰더라도, Standard에서는 노드풀에도 설정이 필요함.

```
gcloud container node-pools update $NODEPOOL_NAME \
  --cluster=$CLUSTER_NAME \
  --location=$LOCATION \
  --workload-metadata=GKE_METADATA
```

---

## 7-2. 노드풀 적용 여부 확인

```
gcloud container node-pools describe $NODEPOOL_NAME \
  --cluster=$CLUSTER_NAME \
  --location=$LOCATION \
  --format="value(config.workloadMetadataConfig.mode)"
```

정상이라면 다음과 비슷하게 보임.

```
GKE_METADATA
```

---

## 8. 실습 5 - 네임스페이스와 Kubernetes ServiceAccount 생성

네임스페이스 생성:

```
kubectl create namespace $NAMESPACE
```

Kubernetes ServiceAccount 생성:

```
kubectl create serviceaccount $KSA_NAME --namespace $NAMESPACE
```

확인:

```
kubectl get sa -n $NAMESPACE
```

---

## 9. 실습 6 - Cloud Storage 버킷 생성

검증용으로 빈 버킷을 하나 생성함.

```
gcloud storage buckets create gs://$BUCKET_NAME
```

---

## 10. 실습 7 - 버킷 접근 권한을 KSA에 부여

Kubernetes ServiceAccount에 직접 IAM principal 형식으로 권한을 부여함.

```
gcloud storage buckets add-iam-policy-binding gs://$BUCKET_NAME \
  --role=roles/storage.objectViewer \
  --member=principal://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${PROJECT_ID}.svc.id.goog/subject/ns/${NAMESPACE}/sa/${KSA_NAME} \
  --condition=None
```

---

## 11. 실습 8 - 테스트 Pod 배포

아래 YAML 파일을 작성함.

파일명: `wif-test-pod.yaml`

```
apiVersion: v1
kind: Pod
metadata:
  name: wif-test-pod
  namespace: demo-wif
spec:
  serviceAccountName: ksa-demo
  containers:
  - name: cloud-sdk
    image: google/cloud-sdk:slim
    command: ["/bin/sh", "-c"]
    args:
      - sleep 3600
```

배포:

```
kubectl apply -f wif-test-pod.yaml
```

상태 확인:

```
kubectl get pod -n $NAMESPACE
```

`Running` 상태가 될 때까지 확인함.

---

## 12. 실습 9 - Pod 내부에서 인증 확인

Pod 안으로 접속:

```
kubectl exec -it -n $NAMESPACE wif-test-pod -- /bin/sh
```

Pod 내부에서 액세스 토큰 요청 테스트:

```
curl -H "Metadata-Flavor: Google" \
  http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token
```

정상이라면 JSON 형태의 토큰 정보가 출력됨.

예시 형태:

```
{
  "access_token": "...",
  "expires_in": 3599,
  "token_type": "Bearer"
}
```

---

## 13. 실습 10 - 버킷 접근 테스트

Pod 내부에서 아래 명령 실행:

```
gcloud storage ls gs://$BUCKET_NAME
```

또는 파일이 없더라도 버킷 자체 접근이 되는지 확인:

```
gcloud storage buckets describe gs://$BUCKET_NAME
```

ls 명령은 실행되지만 describe 명령은 거부된다. 현재 부여된 역할은 `roles/storage.objectViewer` 이다. 이 역할에는 `storage.objects.get`, `storage.objects.list` 등 객체 관련 권한은 들어있으나, 버킷의 설정을 보는 `storage.buckets.get` 권한이 포함되어 있지 않다.

* describe 할 수 있는 역할을 부여한다.

```
gcloud storage buckets add-iam-policy-binding gs://$BUCKET_NAME \
  --role=roles/storage.legacyBucketReader \
  --member=principal://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${PROJECT_ID}.svc.id.goog/subject/ns/${NAMESPACE}/sa/${KSA_NAME}
```

* Storage Admin 권한 부여 (가장 확실함)

모든 권한을 부여하여 `describe` 및 수정까지 가능하게 한다.

```
gcloud storage buckets add-iam-policy-binding gs://$BUCKET_NAME \
  --role=roles/storage.admin \
  --member=principal://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloa
```

### 확인 포인트

* 별도 JSON 키 파일 없이 접근되는지 확인

* `Permission denied`가 아니라 정상 응답이 오는지 확인

* 이 Pod는 `ksa-demo`를 사용하고 있으므로, 버킷 권한이 정확히 KSA 단위로 적용된 것임

---

## 14. 실습 11 - 권한이 없는 경우 비교 테스트

권한 차이를 보여주기 위해 별도 ServiceAccount 없이 Pod를 하나 더 만들어도 좋음.

파일명: `wif-noauth-pod.yaml`

```
apiVersion: v1
kind: Pod
metadata:
  name: wif-noauth-pod
  namespace: demo-wif
spec:
  containers:
  - name: cloud-sdk
    image: google/cloud-sdk:slim
    command: ["/bin/sh", "-c"]
    args:
      - sleep 3600
```

배포:

```
kubectl apply -f wif-noauth-pod.yaml
```

접속:

```
kubectl exec -it -n $NAMESPACE wif-noauth-pod -- /bin/sh
```

버킷 조회 시도:

```
gcloud storage ls gs://$BUCKET_NAME
```

### 결과

* `ksa-demo`를 사용하는 Pod는 접근 가능

* 권한을 받지 않은 Pod는 접근 실패 가능

결과적으로 **노드 서비스 계정 전체 권한에 기대지 않고, 워크로드 단위로 권한을 분리**하는 효과.

Workload Identity Federation for GKE는 각 애플리케이션에 세분화된 ID와 권한을 부여하기 위한 방식

---