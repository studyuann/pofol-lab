---
title: "실습 5 Pod Identity 기반 S3 접근 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "모범사례기반 AWS 고급아키텍처 설계"]
is_public: true
draft: false
---

# 실습 5. Pod Identity 기반 S3 접근 실습

## 1. 실습 목표

이번 실습에서는 특정 Kubernetes 서비스어카운트에 IAM 역할을 연결한 뒤, 해당 서비스어카운트를 사용하는 Pod만 S3 버킷 목록을 조회하도록 구성함.

이 실습을 통해 다음을 이해할 수 있음.

* EKS Pod Identity의 개념

* Kubernetes ServiceAccount와 IAM Role의 연결 방식

* Pod 안에 액세스 키를 넣지 않는 권한 부여 방식

* 최소 권한 원칙(Least Privilege)

* 온프레미스 Kubernetes와 EKS의 권한 모델 차이

AWS는 EKS Pod Identity association을 생성하면, 그 서비스어카운트를 사용하는 Pod가 연결된 IAM 역할의 권한으로 AWS 서비스에 접근할 수 있다고 설명함. 또한 자격 증명은 자동 회전되는 임시 자격 증명임.

---

## 2. 실습 개요

예전에는 Pod가 AWS 자원에 접근해야 하면 다음 같은 방법을 쓰는 경우가 많았음.

* 컨테이너 환경 변수에 Access Key 직접 저장

* Secret에 액세스 키를 넣고 Pod에 주입

* 노드 IAM Role에 너무 넓은 권한 부여

이 방식들은 보안상 문제가 큼.

EKS에서는 더 좋은 방법으로 다음 흐름을 사용할 수 있음.

1. IAM 역할 생성

2. 해당 IAM 역할에 S3 조회 권한 부여

3. Kubernetes 서비스어카운트 생성

4. EKS Pod Identity association으로 서비스어카운트와 IAM 역할 연결

5. 해당 서비스어카운트를 사용하는 Pod 실행

6. Pod 안에서 AWS CLI로 S3 API 호출

AWS는 EKS Pod Identity가 서비스어카운트와 IAM 역할을 연결하고, 노드에서 동작하는 Pod Identity Agent가 Pod에 자격 증명을 전달함.

---

## 3. 실습 전 확인 사항

다음 조건이 준비되어 있어야 함.

1. EKS 클러스터가 이미 생성되어 있어야 함

2. `kubectl`과 `aws` CLI가 모두 사용 가능해야 함

3. 클러스터에 **EKS Pod Identity Agent**가 설치되어 있어야 함

4. IAM 역할 생성 권한이 있어야 함

5. 테스트용 S3 버킷이 있으면 더 좋지만, 이번 실습은 `s3 ls` 정도만으로도 확인 가능함

AWS는 EKS Pod Identity를 쓰려면 클러스터에 `eks-pod-identity-agent` add-on이 있어야 한다고 설명함. `eksctl` 문서도 association 생성 전에 이 add-on이 선설치되어 있어야 한다고 안내함. ([AWS Documentation](https://docs.aws.amazon.com/ko_kr/eks/latest/eksctl/pod-identity-associations?utm_source=chatgpt.com))

먼저 현재 add-on을 확인함.

```
aws eks list-addons --cluster-name my-eks-cluster --region ap-northeast-2
```

출력 결과에 `eks-pod-identity-agent`가 없으면 add-on부터 설치해야 함.

---

## 4. Pod Identity Agent 설치

## 없는 경우만 수행

`eksctl`로 add-on을 설치할 수 있음.

```
eksctl create addon --cluster my-eks-cluster --name eks-pod-identity-agent --region ap-northeast-2
```

설치 후 다시 확인함.

```
aws eks list-addons --cluster-name my-eks-cluster --region ap-northeast-2
```

또는 Kubernetes 쪽에서 Pod를 확인할 수도 있음.

```
kubectl get pods -n kube-system
```

`eks-pod-identity-agent` 관련 Pod가 보이면 됨. AWS는 Agent 설치가 완료되면 이제 Pod Identity association을 사용할 수 있다.

---

## 5. IAM 역할 생성 준비

이번 실습에서는 **S3 목록 조회 권한**만 있는 IAM 역할을 하나 만들어 사용함.

핵심은 이 IAM 역할이 **EKS Pod Identity용 trust policy**를 가져야 한다는 점임.

AWS는 EKS Pod Identity용 역할의 신뢰 정책에 다음 서비스 주체를 사용한다고 설명함.

```
"Service": "pods.eks.amazonaws.com"
```

즉, 이 역할은 일반 EC2 Role이나 일반 사용자 Role과 다르게, EKS Pod Identity가 대신 수행할 수 있도록 만들어 줌.

---

## 6. Trust Policy 파일 작성

아래 내용을 `pod-identity-trust-policy.json` 파일로 저장함.

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

CMD 기준으로 메모장으로 파일을 만들면 됨.

```
notepad pod-identity-trust-policy.json
```

---

## 7. IAM 역할 생성

이제 IAM 역할을 생성함.

```
aws iam create-role --role-name EKS-PodIdentity-S3-ReadOnly --assume-role-policy-document file://pod-identity-trust-policy.json
```

### 명령어 설명

### `aws iam create-role`

새 IAM 역할을 생성함.

### `--role-name EKS-PodIdentity-S3-ReadOnly`

IAM 역할 이름임.

### `--assume-role-policy-document`

누가 이 역할을 맡을 수 있는지 정의하는 trust policy 파일을 지정함.

정상 생성되면 출력 JSON에 `Arn` 값이 보임.

Pod Identity association에서 IAM 역할 ARN이 필요.

---

## 8. S3 읽기 정책 연결

간단하게 AWS 관리형 정책을 연결함.

```
aws iam attach-role-policy --role-name EKS-PodIdentity-S3-ReadOnly --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
```

### 설명

이 명령은 IAM 역할에 **AmazonS3ReadOnlyAccess** 정책을 연결함.

즉, 이 역할을 가진 Pod는 S3를 읽을 수 있지만 수정이나 삭제는 하지 못함.

실무에서는 보통 더 좁게, 특정 버킷만 허용하는 사용자 정의 정책을 만드는 것이 좋음.

하지만 실습에서는 먼저 관리형 정책으로 개념을 확인하는 것이 편함.

---

## 9. Kubernetes 서비스어카운트 생성

이제 Pod가 사용할 서비스어카운트를 생성함.

```
kubectl create serviceaccount s3-reader
```

서비스어카운트 생성 여부를 확인함.

```
kubectl get serviceaccount
```

출력에 `s3-reader`가 보이면 됨.

### 서비스어카운트가 왜 필요한가

Kubernetes에서 서비스어카운트는 Pod가 클러스터 또는 외부 시스템과 상호작용할 때 사용하는 정체성 역할을 함.

EKS Pod Identity는 이 서비스어카운트를 기준으로 IAM 역할을 연결함. Pod Identity association이 **클러스터 + 네임스페이스 + 서비스어카운트 + IAM 역할**을 연결.

---

## 10. Pod Identity association 생성

이제 서비스어카운트와 IAM 역할을 연결함.

먼저 역할 ARN을 확인해야 함. 역할 ARN을 모르면 다음 명령으로 조회 가능함.

```
aws iam get-role --role-name EKS-PodIdentity-S3-ReadOnly
```

출력에 `Arn` 값이 보이면 복사함.

예시:

```
arn:aws:iam::123456789012:role/EKS-PodIdentity-S3-ReadOnly
```

이제 association을 생성함.

```
aws eks create-pod-identity-association --cluster-name my-eks-cluster --namespace default --service-account s3-reader --role-arn arn:aws:iam::123456789012:role/EKS-PodIdentity-S3-ReadOnly --region ap-northeast-2
```

### 명령어 설명

### `aws eks create-pod-identity-association`

EKS Pod Identity association을 생성함.

### `--cluster-name`

대상 EKS 클러스터 이름

### `--namespace default`

서비스어카운트가 존재하는 네임스페이스

### `--service-account s3-reader`

연결할 Kubernetes 서비스어카운트 이름

### `--role-arn ...`

부여할 IAM 역할 ARN

association은 서비스어카운트 하나당 한 IAM 역할만 연결할 수 있다.

---

## 11. association 확인

생성 결과를 확인하려면 다음 명령을 사용함.

```
aws eks list-pod-identity-associations --cluster-name my-eks-cluster --region ap-northeast-2
```

또는 생성 결과 JSON에서 association ID를 확인했다면 상세 조회도 가능함.

association이 보이면 서비스어카운트와 IAM 역할 연결은 완료된 상태임.

association이 클러스터, 네임스페이스, 서비스어카운트, 역할 ARN 정보를 가진다.

---

## 12. 테스트용 Pod 실행

이제 실제로 S3를 조회할 Pod를 생성함.

아래 내용을 `s3-reader-pod.yaml` 파일로 저장함.

```
apiVersion: v1
kind: Pod
metadata:
  name: s3-reader-pod
spec:
  serviceAccountName: s3-reader
  containers:
    - name: aws-cli
      image: amazon/aws-cli
      command: ["sleep", "3600"]
```

CMD에서 메모장으로 파일을 작성함.

```
notepad s3-reader-pod.yaml
```

적용함.

```
kubectl apply -f s3-reader-pod.yaml
```

Pod 상태 확인:

```
kubectl get pods
```

---

## 13. Pod 내부에서 S3 접근 테스트

이제 Pod 안에 들어가서 S3 API를 호출함.

```
kubectl exec -it s3-reader-pod -- sh
```

컨테이너 내부에서 다음 명령을 실행함.

```
aws sts get-caller-identity
```

이 명령은 현재 Pod가 어떤 IAM 자격으로 동작하는지 보여줌.

정상이라면 앞에서 생성한 IAM 역할 ARN 정보가 보일 수 있음.

그 다음 S3 조회를 시도함.

```
aws s3 ls
```

정상이라면 현재 계정에서 접근 가능한 S3 버킷 목록이 표시됨.

이 결과가 나오면 Pod Identity가 정상 동작한 것임.

Pod Identity association을 사용한 Pod가 AWS SDK 또는 CLI의 기본 credential chain을 통해 임시 자격 증명을 받아 AWS 서비스에 접근할 수 있다.

---

## 14. 비교 실습

## 서비스어카운트를 쓰지 않는 Pod

차이를 더 분명히 보려면 서비스어카운트를 지정하지 않은 Pod도 테스트하면 좋음.

아래 내용을 `normal-pod.yaml`로 저장함.

```
apiVersion: v1
kind: Pod
metadata:
  name: normal-pod
spec:
  containers:
    - name: aws-cli
      image: amazon/aws-cli
      command: ["sleep", "3600"]
```

적용함.

```
kubectl apply -f normal-pod.yaml
```

Pod 안으로 들어감.

```
kubectl exec -it normal-pod -- sh
```

그 다음 아래 명령을 실행함.

```
aws sts get-caller-identity
aws s3 ls
```

이 Pod는 `s3-reader` 서비스어카운트를 사용하지 않았으므로, Pod Identity association이 적용되지 않음.

따라서 권한 오류가 나거나 원하는 결과가 나오지 않을 수 있음.

---

## 15. 실습 정리

### 15-1. 액세스 키를 Pod 안에 넣지 않음

Pod 내부에 AWS Access Key를 직접 저장하지 않았음.

그럼에도 AWS API를 호출할 수 있었음.

### 15-2. 권한은 서비스어카운트를 기준으로 부여됨

즉, Pod 자체가 아니라 **그 Pod가 사용하는 서비스어카운트**가 권한의 기준이 됨.

### 15-3. IAM 역할은 Pod별 최소 권한 제어 수단이 됨

특정 Pod만 S3를 읽게 만들 수 있고, 다른 Pod는 못 하게 할 수 있음.

### 15-4. EKS는 Kubernetes와 IAM을 통합할 수 있음

이 점이 온프레미스 Kubernetes와 큰 차이임.

온프레미스에서는 보통 이런 클라우드 IAM 연동 실습을 직접 재현하기 어려움.

EKS Pod Identity가 최소 권한, 역할 재사용성, 운영 분리, 임시 자격 증명 전달을 장점으로 가진다.

---

## 16. 자주 발생하는 문제

### 16-1. `aws sts get-caller-identity`가 실패하는 경우

가능한 원인은 다음과 같음.

* Pod Identity Agent가 설치되지 않음

* association이 잘못 생성됨

* IAM 역할 trust policy가 잘못됨

* Pod가 올바른 서비스어카운트를 사용하지 않음

먼저 아래를 확인함.

```
aws eks list-addons --cluster-name my-eks-cluster --region ap-northeast-2
aws eks list-pod-identity-associations --cluster-name my-eks-cluster --region ap-northeast-2
kubectl get pod s3-reader-pod -o yaml
```

### 16-2. S3 접근이 AccessDenied로 실패하는 경우

이 경우는 대개 IAM 정책이 부족한 것임.

역할에 연결한 정책을 확인함.

```
aws iam list-attached-role-policies --role-name EKS-PodIdentity-S3-ReadOnly
```

### 16-3. 서비스어카운트 이름이나 네임스페이스가 안 맞는 경우

association은 **클러스터 + 네임스페이스 + 서비스어카운트** 조합에 정확히 맞아야 함.

이 셋 중 하나라도 다르면 권한이 적용되지 않음. AWS CLI 문서도 namespace와 service-account를 명시적으로 받음. ([AWS Documentation](https://docs.aws.amazon.com/cli/latest/reference/eks/create-pod-identity-association?utm_source=chatgpt.com))

---

## 17. 온프레미스 Kubernetes와 비교 포인트

### 온프레미스 Kubernetes

* 보통 액세스 키를 Secret으로 넣는 식의 우회가 자주 등장함

* 외부 IAM 연동은 별도 솔루션이 필요할 수 있음

* 노드 권한과 Pod 권한 분리가 어려운 경우가 많음

### EKS

* 서비스어카운트에 IAM 역할 연결 가능

* Pod별 최소 권한 제어 가능

* 액세스 키를 직접 배포하지 않아도 됨

* AWS 서비스와 권한 모델이 자연스럽게 통합됨

---

## 18. 실습 후 정리 명령

실습이 끝났으면 Pod와 association을 정리함.

```
kubectl delete pod s3-reader-pod
kubectl delete pod normal-pod
kubectl delete serviceaccount s3-reader
```

association 삭제는 다음처럼 수행 가능함. 먼저 association 목록을 확인하고 ID를 찾음.

```
aws eks list-pod-identity-associations --cluster-name my-eks-cluster --region ap-northeast-2
```

그 다음 association ID를 사용해 삭제함.

```
aws eks delete-pod-identity-association --cluster-name my-eks-cluster --association-id 연결ID --region ap-northeast-2
```

IAM 역할도 실습용이면 정리함.

```
aws iam detach-role-policy --role-name EKS-PodIdentity-S3-ReadOnly --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
aws iam delete-role --role-name EKS-PodIdentity-S3-ReadOnly
```

---