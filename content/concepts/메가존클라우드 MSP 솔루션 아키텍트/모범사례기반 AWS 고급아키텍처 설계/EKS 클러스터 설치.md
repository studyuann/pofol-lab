---
title: "EKS 클러스터 설치"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "모범사례기반 AWS 고급아키텍처 설계"]
is_public: true
draft: false
---

# EKS 클러스터 설치

## 윈도우 CMD 클라이언트 기준

## 1. Kubernetes와 EKS 이해

Kubernetes는 컨테이너 기반 애플리케이션을 배포, 확장, 복구하기 위한 오케스트레이션 플랫폼임.

Amazon EKS는 AWS가 제공하는 관리형 Kubernetes 서비스임.

가장 큰 특징은 **Control Plane을 AWS가 관리한다는 점**임.

즉, 사용자는 Kubernetes를 사용하지만, API Server, etcd, 고가용성 Control Plane, 일부 업그레이드 부담을 AWS가 대신 처리해 줌. AWS는 EKS 클러스터를 각자의 제어 플레인으로 운영하고, 제어 플레인 고가용성을 AWS가 관리한다고 설명함.

---

## 2. EKS 기본 구조

### 2-1. Control Plane

Control Plane은 클러스터를 제어하는 핵심 영역임.

대표 구성 요소는 다음과 같음.

* **kube-apiserver**

  모든 요청의 진입점 역할을 함

  `kubectl` 명령도 결국 API Server와 통신함

* **etcd**

  클러스터 상태를 저장하는 분산 Key-Value 저장소임

* **kube-scheduler**

  Pod를 어느 Node에 배치할지 결정함

* **kube-controller-manager**

  Deployment, ReplicaSet, Node 상태를 원하는 상태로 유지함

온프레미스에서는 이 영역을 직접 설치하고 직접 운영해야 함.

반면 EKS에서는 Control Plane이 AWS 관리형으로 제공됨. ([AWS Documentation](https://docs.aws.amazon.com/eks/latest/userguide/getting-started-eksctl?utm_source=chatgpt.com))

### 2-2. Worker Node

Worker Node는 실제 애플리케이션 컨테이너가 실행되는 서버임.

여기에는 보통 다음이 포함됨.

* kubelet

* kube-proxy

* container runtime

* 실제 Pod 실행 환경

EKS에서는 Worker Node를 다음 방식으로 운영할 수 있음.

* Managed Node Group

* Self-managed Node

* Fargate

초급 실습에서는 **Managed Node Group**이 가장 적합함.

노드 생성과 기본 운영을 단순화하기 때문임. ([AWS Documentation](https://docs.aws.amazon.com/eks/latest/eksctl/AmazonEksEksctlDocs.pdf?utm_source=chatgpt.com))

---

## 3. 실습 전 준비 사항

**윈도우 PC에서 CMD를 클라이언트로 사용**.

또한 **AWS CLI는 이미 설치 완료** 상태.

실습에 필요한 도구는 다음과 같음.

* AWS CLI

* kubectl

* eksctl

각 도구의 역할은 다음과 같음.

* **AWS CLI**

  AWS 리소스를 명령줄에서 제어함

* **kubectl**

  Kubernetes 클러스터를 제어하는 표준 명령줄 도구임

* **eksctl**

  EKS 클러스터 생성과 관리를 단순화하는 CLI 도구임

AWS는 `eksctl` 설치 시 **공식 GitHub 릴리스만 사용**할 것을 권장함.

---

## 4. AWS CLI 동작 확인

AWS CLI가 이미 설치되어 있다면, 설치보다 먼저 **인증 상태**를 확인해야 함.

### 4-1. 버전 확인

```
aws --version
```

이 명령은 AWS CLI 실행 여부를 확인함.

정상이라면 버전 정보가 출력됨.

### 4-2. 현재 인증 사용자 확인

```
aws sts get-caller-identity
```

이 명령은 현재 어떤 IAM 사용자 또는 IAM 역할로 AWS API를 호출하는지 보여줌.

예시:

```
{
  "UserId": "AIDAXXXXXXXXXXXXX",
  "Account": "123456789012",
  "Arn": "arn:aws:iam::123456789012:user/admin"
}
```

* 현재 로그인된 계정이 맞는지 확인 가능함

* 실습용 계정인지 확인 가능함

* EKS 생성 권한이 있는지 점검하는 출발점이 됨

### 4-3. 기본 리전 확인

```
aws configure list
```

이 명령은 현재 AWS CLI 설정값을 보여줌.

특히 `region` 값을 확인해야 함.

서울 리전은 다음 코드임.

```
ap-northeast-2
```

---

## 5. kubectl 설치

## 윈도우 CMD 기준

`kubectl`은 Kubernetes 클러스터를 제어하는 표준 도구이며, AWS 전용 바이너리가 아니라 Kubernetes 공식 바이너리를 사용함. 또한 `kubectl` 버전은 클러스터 버전과 **마이너 버전 차이가 1 이내**인 것이 권장됨.

### 5-1. 다운로드

CMD에서 다음 명령을 실행함.

```
curl.exe -LO "https://dl.k8s.io/release/v1.34.0/bin/windows/amd64/kubectl.exe"
```

### 5-2. 명령어 설명

### `curl.exe -LO`

윈도우에서도 `curl`이 제공될 수 있지만, PowerShell 별칭과 혼동을 피하려고 `curl.exe`라고 명확히 쓰는 것이 좋음.

* `L` : 리다이렉션을 따라감

* `O` : 원격 파일 이름 그대로 저장함

즉, 현재 디렉터리에 `kubectl.exe` 파일을 다운로드하는 명령임.

### 5-3. 실행 파일 이동

예를 들어 `C:\Tools` 폴더를 만들어 그 안에 넣는 방식으로 설명하면 실습이 단순함.

```
mkdir C:\Tools
move kubectl.exe C:\Tools\
```

### 5-4. PATH 등록

CMD에서 임시로 PATH를 잡는 방법과 영구 등록 방법이 있음.

교안에서는 영구 등록까지 같이 설명하는 것이 좋음.

```
setx PATH "%PATH%;C:\Tools"
```

설정 후 **새 CMD 창을 다시 열어야 함**.

`setx`는 현재 창이 아니라 이후에 새로 열리는 세션에 반영됨.

### 5-5. 설치 확인

```
kubectl version --client
```

정상 설치되면 클라이언트 버전이 출력됨.

---

## 6. eksctl 설치

## 윈도우 CMD 기준

`eksctl`은 EKS 클러스터 생성과 관리를 단순화하는 도구임.

중요한 점은 설치 출처인데, AWS는 `eksctl`을 **공식 GitHub 릴리스에서만 설치할 것**을 권장함.

윈도우 CMD에서는 압축 해제까지 포함해 다음처럼 설명하면 됨.

### 6-1. 다운로드

```
curl.exe -L -o eksctl.zip "https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_Windows_amd64.zip"
```

### 6-2. 압축 해제

윈도우에는 기본 `tar`가 있는 경우가 많으므로 다음처럼 해제 가능함.

```
tar -xf eksctl.zip
```

압축을 해제하면 `eksctl.exe`가 생성됨.

### 6-3. 실행 파일 이동

```
move eksctl.exe C:\Tools\
```

### 6-4. 설치 확인

```
eksctl version
```

정상 설치되면 버전 정보가 출력됨. ([AWS Documentation](https://docs.aws.amazon.com/eks/latest/eksctl/installation?utm_source=chatgpt.com))

---

## 7. EKS 클러스터 생성

## 윈도우 CMD 기준

AWS는 `eksctl`을 이용한 시작 방식을 EKS 빠른 시작 방법으로 안내함. ([AWS Documentation](https://docs.aws.amazon.com/eks/latest/userguide/getting-started-eksctl?utm_source=chatgpt.com))

CMD에서 여러 줄로 쓰려면 줄 끝에 `^` 문자를 사용해야 함.

### 7-1. 클러스터 생성 명령

```
eksctl create cluster ^
  --name 이니셜-eks-cluster ^
  --region ap-northeast-2 ^
  --nodegroup-name my-nodes ^
  --node-type t3.medium ^
  --nodes 2 ^
  --nodes-min 2 ^
  --nodes-max 3 ^
  --managed
```

```
eksctl create cluster \
  --name 이니셜-eks-cluster \
  --region ap-northeast-2 \
  --nodegroup-name my-nodes \
  --node-type t3.medium \
  --nodes 2 \
  --nodes-min 2 \
  --nodes-max 3 \
  --managed
```

### 7-2. 명령어 설명

### `eksctl create cluster`

새로운 EKS 클러스터를 생성함.

### `--name my-eks-cluster`

클러스터 이름을 지정함.

### `--region ap-northeast-2`

클러스터를 서울 리전에 생성함.

### `--nodegroup-name my-nodes`

Worker Node 그룹 이름을 지정함.

### `--node-type t3.medium`

노드로 사용할 EC2 인스턴스 유형을 지정함.

### `--nodes 2`

초기 노드 수를 2대로 지정함.

### `--nodes-min 2`

오토스케일 최소 노드 수를 지정함.

### `--nodes-max 3`

오토스케일 최대 노드 수를 지정함.

### `--managed`

Managed Node Group 방식으로 생성함.

### 7-3. 생성 시 실제로 함께 만들어지는 것

이 명령은 Kubernetes만 만드는 것이 아님.

실제로는 여러 AWS 리소스를 함께 생성함.

* EKS Cluster

* IAM Role

* Security Group

* Subnet/VPC 관련 연결

* Managed Node Group

* Auto Scaling 관련 구성

* CloudFormation Stack

즉, `eksctl`은 여러 AWS 리소스를 한 번에 구성해 주는 자동화 도구라고 이해하면 됨.

---

## 8. kubeconfig와 클러스터 연결

`kubectl`이 Kubernetes API 서버와 통신하려면 kubeconfig가 필요함.

AWS CLI의 `aws eks update-kubeconfig`는 지정한 EKS 클러스터에 대해 kubeconfig를 생성 또는 업데이트하는 명령임.

### 8-1. 수동 업데이트 명령

```
aws eks update-kubeconfig --region ap-northeast-2 --name my-eks-cluster
```

### 8-2. 윈도우에서 kubeconfig 위치

윈도우에서는 보통 다음 경로를 사용함.

```
%USERPROFILE%\.kube\config
```

### 8-3. 현재 컨텍스트 확인

```
kubectl config get-contexts
kubectl config current-context
```

### 8-4. config 파일 직접 확인

```
type %USERPROFILE%\.kube\config
```

### 8-5. 노드 확인

```
kubectl get nodes
```

정상이라면 Worker Node 목록이 출력됨.

---

## 9. 테스트 애플리케이션 배포

클러스터가 정상 동작하는지 확인하기 위해 Nginx를 배포함.

### 9-1. Deployment 생성

```
kubectl create deployment nginx --image=nginx
```

이 명령은 `nginx` 컨테이너 이미지를 사용하는 Deployment를 생성함.

### 9-2. Pod 확인

```
kubectl get pods
```

### 9-3. 외부 공개용 Service 생성

```
kubectl expose deployment nginx --port=80 --type=LoadBalancer
```

이 명령은 Deployment를 외부에서 접근 가능한 서비스로 노출함.

EKS에서는 AWS 로드밸런서와 쉽게 통합되므로 `LoadBalancer` 타입을 비교적 쉽게 사용할 수 있음.

### 9-4. 서비스 확인

```
kubectl get svc
```

`EXTERNAL-IP` 또는 로드밸런서 주소가 생성되면 외부 접속이 가능함.

---

## 10. EKS 네트워크 구조

## VPC, Subnet, Security Group 중심

EKS 클러스터는 **VPC 안에 생성**되고, Pod 네트워킹은 기본적으로 **Amazon VPC CNI**가 제공함.

### 10-1. VPC

VPC는 AWS 안에서 만드는 논리적 가상 네트워크임.

쉽게 말하면 AWS 안에 만드는 내 전용 사설 네트워크라고 보면 됨.

EKS에서 중요한 이유는 다음과 같음.

* 클러스터는 VPC 안에 생성됨

* Worker Node는 VPC 안의 서브넷에 배치됨

* Pod 네트워킹이 VPC 주소 체계와 연결됨

* 로드밸런서도 VPC 안에 연결됨

### 10-2. Subnet

Subnet은 VPC를 더 작은 네트워크 구역으로 나눈 것임.

EKS에서 Subnet은 다음 용도로 중요함.

* Worker Node 배치

* EKS 제어 플레인 연결용 ENI 배치

* Load Balancer 배치

* Pod IP 운영 기반

AWS는 클러스터 생성 시 사용하는 서브넷이 **최소 2개 서로 다른 AZ**에 있어야 하고, 각 서브넷은 **최소 6개 IP, 권장 16개 이상 여유 IP**를 가져야 한다고 안내함.

### Public Subnet

인터넷 게이트웨이로 직접 나가는 경로가 있는 서브넷임.

### Private Subnet

인터넷 게이트웨이로 직접 나가는 경로가 없는 서브넷임.

필요하면 NAT Gateway를 통해 외부로 나갈 수 있음.

실무에서는 보통 다음 구조를 권장함.

* Public Subnet: NAT Gateway, Public Load Balancer

* Private Subnet: Worker Node, 내부 Pod

즉, 노드는 Private Subnet에 두고, 외부 공개는 Load Balancer로 처리하는 구조가 일반적임.

### 10-3. Security Group

Security Group은 AWS의 상태 저장형 가상 방화벽임.

어떤 트래픽을 허용할지 제어함.

EKS에서는 다음 위치에서 중요함.

* Control Plane이 사용하는 ENI

* Worker Node EC2

* 필요 시 Pod 단위 보안 그룹

AWS는 EKS에서 Security Group을 사용해 **제어 플레인과 노드 사이**, **노드와 다른 VPC 리소스 사이**, **외부 IP와의 통신**을 제어한다고 설명함.

### 10-4. EKS 네트워크를 한 줄로 정리

온프레미스에서는 Kubernetes 네트워크와 인프라 네트워크를 어느 정도 분리해서 생각하는 경우가 많음.

하지만 EKS에서는 다음처럼 이해하는 것이 정확함.

**EKS 네트워크 설계 = AWS VPC 네트워크 설계와 거의 함께 움직임**

즉, 서브넷 크기, AZ 분산, 보안 그룹 설계가 곧 Kubernetes 운영 품질과 연결됨.

---

## 11. 실습 종료 후 삭제

실습이 끝났다면 비용 절감을 위해 클러스터를 삭제해야 함.

CMD 기준 명령은 다음과 같음.

```
eksctl delete cluster --name 이니셜-eks-cluster --region ap-northeast-2
```

EKS 클러스터와 관련된 리소스를 정리하는 명령임.

---