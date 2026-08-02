---
title: "AWS Load Balancer Controller 설치"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "모범사례기반 AWS 고급아키텍처 설계", "실습 3 ALB Ingress 실습"]
is_public: true
draft: false
---

# AWS Load Balancer Controller 설치

EBS CSI 드라이버와 마찬가지로 **권한(IAM)** 설정이 가장 중요.

### 1단계: IAM 정책 및 역할 생성

컨트롤러가 AWS API를 호출해서 로드밸런서를 만들 수 있는 권한을 준다.

```
# 1. IAM 정책 다운로드 (AWS 제공)
curl -O https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.7.2/docs/install/iam_policy.json

# 2. 정책 생성
aws iam create-policy ^
    --policy-name AWSLoadBalancerControllerIAMPolicy ^
    --policy-document file://iam_policy.json

# 3. iamserviceaccount 생성 (Role 생성 및 연결)
eksctl create iamserviceaccount ^
  --cluster=이니셜-eks-cluster ^
  --namespace=kube-system ^
  --name=aws-load-balancer-controller ^
  --role-name AmazonEKSLoadBalancerControllerRole ^
  --attach-policy-arn=arn:aws:iam::<내-계정-ID>:policy/AWSLoadBalancerControllerIAMPolicy ^
  --approve
```

### 2단계: Helm을 이용한 컨트롤러 설치

쿠버네티스 패키지 매니저인 **Helm**을 사용하여 클러스터 내부에 컨트롤러 파드를 띄다.

```
# Helm 리포지토리 추가
helm repo add eks https://aws.github.io/eks-charts
helm repo update

# 컨트롤러 설치
helm install aws-load-balancer-controller eks/aws-load-balancer-controller ^
  -n kube-system ^
  --set clusterName=이니셜-eks-cluster ^
  --set serviceAccount.create=false ^
  --set serviceAccount.name=aws-load-balancer-controller
```