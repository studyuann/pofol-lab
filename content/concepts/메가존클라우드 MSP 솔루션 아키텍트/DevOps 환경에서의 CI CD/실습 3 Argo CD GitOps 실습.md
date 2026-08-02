---
title: "실습 3 Argo CD GitOps 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "DevOps 환경에서의 CI CD"]
is_public: true
draft: false
---

# 실습 3. Argo CD GitOps 실습

# 1. 실습 목표

이 실습의 목표는 아래 흐름을 직접 확인하는 것임.

```
소스코드 수정
→ GitHub Actions 실행
→ Docker 이미지 빌드
→ Docker Hub Push
→ GitOps 저장소 deployment.yaml 이미지 태그 변경
→ Argo CD가 Git 변경 감지
→ EKS에 Sync
→ 새 Pod 생성
→ 기존 Pod 종료
```

즉, **소스코드 저장소의 변경이 최종적으로 Kubernetes Pod 교체까지 이어지는 GitOps 흐름**을 완성하는 실습임.

---

# 2. 전체 구조

저장소는 2개 사용함.

## 2.1 Application Source Repository

이 저장소에는 애플리케이션 코드와 CI 파이프라인 파일이 들어감.

역할

* 애플리케이션 코드 저장

* Docker 이미지 빌드

* Docker Hub Push

* GitOps 저장소의 Deployment 이미지 태그 자동 변경

---

## 2.2 GitOps Repository

이 저장소에는 Kubernetes 배포 파일이 들어감.

역할

* 원하는 Kubernetes 상태를 Git에 저장

* Argo CD가 이 저장소를 감시

* 변경 감지 시 EKS에 반영

---

# 3. 실습에서 만들 리소스

이번 실습에서 만들 것은 다음과 같음.

* EKS 클러스터 1개

* GitHub 저장소 2개

* Docker Hub 저장소 1개

* Argo CD 설치

* Flask 애플리케이션 1개

* Kubernetes Namespace / Deployment / Service

* GitHub Actions Workflow 1개

---

# 4. 사전 준비

## 4.1 계정 준비

필요한 계정

* AWS 계정

* GitHub 계정

* Docker Hub 계정

---

## 4.2 설치 프로그램 준비

Git Bash 기준으로 아래 명령이 동작해야 함.

* `aws`

* `kubectl`

* `eksctl`

* `git`

* `docker` 또는 Docker Desktop(설치)

확인 명령

```
aws --version
kubectl version --client
eksctl version
git --version
docker --version
```

`aws login` 명령은 AWS CLI 2.32.0 이상이 필요함.

---

# 5. 실습에서 사용할 이름

아래 이름으로 통일해서 진행함.

## 5.1 AWS / Kubernetes

* Region: `ap-northeast-2`

* EKS Cluster Name: `gitops-lab`

* Namespace: `gitops-demo`

## 5.2 GitHub 저장소

* 애플리케이션 저장소: `gitops-app-source`

* GitOps 저장소: `gitops-manifests`

## 5.3 Docker Hub

* Docker Hub 사용자명: `본인도커허브ID`

* 이미지 이름: `gitops-demo-app`

최종 이미지 예시

```
본인도커허브ID/gitops-demo-app:커밋SHA
```

---

# 6. Git Bash에서 AWS 로그인

프로파일 이름은 예시로 `bootcamp` 사용함.

## 6.1 로그인

```
aws login --profile bootcamp
```

이 명령을 실행하면 브라우저가 열리고 로그인 후 임시 자격 증명이 생성됨. AWS 공식 문서도 `aws login` 이 기존 콘솔 자격 증명을 사용한 로그인 흐름이며, 로그인 후 임시 자격 증명을 자동 생성하고 자동 갱신한다고 설명함.

## 6.2 현재 셸에 프로파일 지정

Git Bash에서는 이후 명령들이 같은 프로파일을 계속 쓰도록 환경변수를 지정하는 것이 편함.

```
export AWS_PROFILE=bootcamp
```

## 6.3 로그인 확인

```
aws sts get-caller-identity
```

정상적으로 계정 정보가 나오면 됨.

---

# 7. EKS 클러스터 생성

AWS 문서 기준으로 EKS를 빠르게 시작하는 가장 단순한 흐름 중 하나가 `eksctl` 사용 방식임. `eksctl` 은 CLI 명령 또는 YAML 설정 파일로 클러스터를 생성할 수 있음.

## 7.1 작업 폴더 생성

```
mkdir -p ~/eks-gitops-lab
cd ~/eks-gitops-lab
```

---

## 7.2 EKS 설정 파일 작성

파일명: `eks-cluster.yaml`

```
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: gitops-lab
  region: ap-northeast-2

managedNodeGroups:
  - name: workers
    instanceType: t3.medium
    desiredCapacity: 2
    minSize: 2
    maxSize: 3
    volumeSize: 20
```

### 설명

* `metadata.name`  
  EKS 클러스터 이름

* `region`  
  생성할 리전

* `managedNodeGroups`  
  관리형 노드 그룹 설정

* `instanceType`  
  워커 노드 EC2 타입

* `desiredCapacity`  
  최초 생성 노드 수

* `minSize`, `maxSize`  
  오토스케일 범위

---

## 7.3 클러스터 생성

```
eksctl create cluster -f eks-cluster.yaml
```

이 명령은 내부적으로 필요한 AWS 리소스를 생성함. 시간이 꽤 걸림.

---

## 7.4 kubectl 연결 설정

클러스터 생성이 끝나면 kubeconfig를 갱신함.

```
aws eks update-kubeconfig --region ap-northeast-2--name gitops-lab
```

AWS 문서에서도 EKS 클러스터에 `kubectl` 을 연결할 때 `aws eks update-kubeconfig` 사용 흐름을 안내함.

---

## 7.5 클러스터 확인

```
kubectl get nodes
```

정상 예시

```
NAME                                                STATUS   ROLES    AGE   VERSION
ip-192-168-xx-xx.ap-northeast-2.compute.internal    Ready    <none>   ...
ip-192-168-yy-yy.ap-northeast-2.compute.internal    Ready    <none>   ...
```

---

# 8. Argo CD 설치

Argo CD 공식 문서 기준 기본 설치 흐름은 `argocd` 네임스페이스를 만들고 stable 설치 manifest를 적용하는 방식임. Argo CD는 Git에 정의된 목표 상태와 실제 클러스터 상태를 계속 비교함.

## 8.1 namespace 생성

```
kubectl create namespace argocd
```

---

## 8.2 Argo CD 설치

```
kubectl apply -n argocd --server-side --force-conflicts -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

---

## 8.3 Pod 상태 확인

```
kubectl get pods -n argocd
```

모든 Pod가 `Running` 또는 필요한 경우 `Completed` 될 때까지 확인

---

## 8.4 Argo CD 서버 외부 노출

실습 편의상 `LoadBalancer` 로 노출함.

```
kubectl patch svc argocd-server -n argocd -p '{"spec":{"type":"LoadBalancer"}}'
```

확인

```
kubectl get svc argocd-server -n argocd
```

`EXTERNAL-IP` 가 생기면 접속 가능

```
https://EXTERNAL-IP
```

---

## 8.5 초기 admin 비밀번호 확인

```
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d;echo
```

로그인 정보

* ID: `admin`

* PW: 위 명령 출력값

---

# 9. GitHub 저장소 2개 생성

GitHub에서 아래 저장소를 생성함.

## 9.1 애플리케이션 저장소

```
gitops-app-source
```

## 9.2 GitOps 저장소

```
gitops-manifests
```

처음 실습은 두 저장소를 **Public** 으로 두는 것이 가장 단순함. 그러면 Argo CD가 별도 Git 인증 없이 GitOps 저장소를 읽기 쉬움.

---

# 10. Docker Hub 저장소 생성

Docker Hub에서 아래 저장소 생성

```
gitops-demo-app
```

이미지 경로 예시

```
본인도커허브ID/gitops-demo-app
```

# 11. 애플리케이션 저장소 구성

로컬에서 애플리케이션 저장소 작업 디렉터리 생성

```
cd ~
mkdir -p gitops-app-source
cd gitops-app-source
git init
```

---

## 11.1 디렉터리 구조

```
gitops-app-source/
├── app.py
├── requirements.txt
├── Dockerfile
├── .gitignore
└── .github/
    └── workflows/
        └── ci.yaml
```

---

## 11.2 app.py

파일명: `app.py`

```
from flask import Flask
import os
import socket

app = Flask(__name__)

VERSION = os.environ.get("APP_VERSION", "v1")
HOSTNAME = socket.gethostname()

@app.route("/")
def home():
    return f"""
    <html>
      <head>
        <title>GitOps Demo Application - Updated</title>
      </head>
      <body>
        <h1>GitOps Demo Application</h1>
        <p><strong>Version:</strong> {VERSION}</p>
        <p><strong>Pod Hostname:</strong> {HOSTNAME}</p>
        <p>ThisappisrunningonEKSanddeployedbyArgoCD.</p>
      </body>
    </html>
    """

@app.route("/health")
def health():
    return {
        "status": "ok",
        "version": VERSION,
        "hostname": HOSTNAME
    }, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

### 설명

* `VERSION`  
  컨테이너 환경변수에서 앱 버전 문자열을 읽음

* `HOSTNAME`  
  현재 Pod 내부 호스트명을 표시함

* `/`  
  웹 페이지 출력

* `/health`  
  헬스체크용 API

`hostname` 을 같이 보여주는 이유는 **배포 후 Pod가 바뀌었는지 확인하기 쉬워지기 때문**임.

---

## 11.3 requirements.txt

파일명: `requirements.txt`

```
Flask==3.0.3
```

---

## 11.4 Dockerfile

파일명: `Dockerfile`

```
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

ENV APP_VERSION=v1

EXPOSE 5000

CMD ["python","app.py"]
```

### 설명

* `FROM python:3.11-slim`  
  가벼운 Python 베이스 이미지 사용

* `WORKDIR /app`  
  컨테이너 내부 작업 디렉터리 지정

* `COPY requirements.txt .`  
  의존성 파일 복사

* `RUN pip install ...`  
  Flask 설치

* `COPY app.py .`  
  앱 소스 복사

* `ENV APP_VERSION=v1`  
  기본 버전값 설정

* `EXPOSE 5000`  
  컨테이너 내부 포트 문서화

* `CMD ["python", "app.py"]`  
  컨테이너 시작 시 실행할 명령

---

## 11.5 .gitignore

파일명: `.gitignore`

```
__pycache__/
*.pyc
*.pyo
*.pyd
.env
venv/
.venv/
```

---

# 12. GitOps 저장소 구성

```
cd ~
mkdir -p gitops-manifests
cd gitops-manifests
git init
```

---

## 12.1 디렉터리 구조

```
gitops-manifests/
└── kubernetes/
    ├── namespace.yaml
    ├── deployment.yaml
    ├── service.yaml
    └── kustomization.yaml
```

---

## 12.2 namespace.yaml

파일명: `kubernetes/namespace.yaml`

```
apiVersion: v1
kind: Namespace
metadata:
  name: gitops-demo
```

---

## 12.3 deployment.yaml

파일명: `kubernetes/deployment.yaml`

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gitops-demo-app
  namespace: gitops-demo
spec:
  replicas: 2
  selector:
    matchLabels:
      app: gitops-demo-app
  template:
    metadata:
      labels:
        app: gitops-demo-app
    spec:
      containers:
        - name: gitops-demo-app
          image: DOCKER_USERNAME/gitops-demo-app:initial
          imagePullPolicy: Always
          ports:
            - containerPort: 5000
          env:
            - name: APP_VERSION
              value:"initial"
          readinessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 5
            periodSeconds: 5
          livenessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 10
            periodSeconds: 10
```

### 매우 중요

`DOCKERHUB_USERNAME` 는 **본인 Docker Hub 아이디로 반드시 변경**해야 함.

예

```
image: mydockerid/gitops-demo-app:initial
```

### 설명

* `replicas: 2`  
  Pod 2개 실행

* `imagePullPolicy: Always`  
  이미지 새 버전 pull 시도

* `APP_VERSION`  
  웹 화면에 표시될 버전 문자열

* `readinessProbe`  
  트래픽 받기 전 준비 여부 확인

* `livenessProbe`  
  살아있는지 확인

---

## 12.4 service.yaml

파일명: `kubernetes/service.yaml`

```
apiVersion: v1
kind: Service
metadata:
  name: gitops-demo-service
  namespace: gitops-demo
spec:
  type: LoadBalancer
  selector:
    app: gitops-demo-app
  ports:
    - port: 80
      targetPort: 5000
      protocol: TCP
```

### 설명

EKS에서는 `LoadBalancer` 서비스 생성 시 외부 접속용 AWS Load Balancer가 연결되는 구조를 사용할 수 있음.

---

## 12.5 kustomization.yaml

파일명: `kubernetes/kustomization.yaml`

```
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - namespace.yaml
  - deployment.yaml
  - service.yaml
```

---

# 13. GitHub에 두 저장소 업로드

## 13.1 애플리케이션 저장소 업로드

GitHub에서 `gitops-app-source` 저장소 생성 후 아래 실행

```
cd ~/gitops-app-source
git branch -M main
git remote add origin https://github.com/본인깃허브ID/gitops-app-source.git
git add .
git commit -m "initial app source"
git push -u origin main
```

---

## 13.2 GitOps 저장소 업로드

GitHub에서 `gitops-manifests` 저장소 생성 후 아래 실행

```
cd ~/gitops-manifests
git branch -M main
git remote add origin https://github.com/본인깃허브ID/gitops-manifests.git
git add .
git commit -m "initial manifests"
git push -u origin main
```

---

# 14. 첫 배포용 초기 이미지 Push

Argo CD가 처음 Sync 할 때는 `deployment.yaml` 의 이미지가 실제로 Docker Hub에 존재해야 함.

그래서 로컬에서 먼저 `initial` 태그 이미지를 빌드해서 1회 Push 함.

## 14.1 Docker Hub 로그인

```
docker login
```

---

## 14.2 이미지 빌드

```
cd ~/gitops-app-source
docker build -t 본인도커허브ID/gitops-demo-app:initial .
```

---

## 14.3 이미지 Push

```
docker push 본인도커허브ID/gitops-demo-app:initial
```

---

# 15. Argo CD Application 생성

Argo CD는 GitOps 저장소를 감시해야 하므로 `Application` 리소스를 생성해야 함.

## 15.1 Application 파일 작성

작업 폴더는 아무 곳이나 가능

파일명: `argocd-app.yaml`

```
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: gitops-demo-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/본인깃허브ID/gitops-manifests.git
    targetRevision: main
    path: kubernetes
  destination:
    server: https://kubernetes.default.svc
    namespace: gitops-demo
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

### 설명

* `repoURL`  
  Argo CD가 감시할 GitOps 저장소

* `targetRevision`  
  감시할 브랜치

* `path`  
  Kubernetes 파일이 들어 있는 디렉터리

* `destination.server`  
  같은 클러스터 내부 Kubernetes API 서버

* `automated`  
  Git 변경 시 자동 동기화

* `prune`  
  Git에서 삭제된 리소스 제거

* `selfHeal`  
  클러스터에서 수동 변경이 생겨도 Git 기준으로 다시 맞춤

---

## 15.2 Application 생성

```
kubectl apply -f argocd-app.yaml
```

---

## 15.3 동기화 확인

```
kubectl get applications -n argocd
kubectl get all -n gitops-demo
```

또는 Argo CD UI에서 상태 확인 가능

정상이라면

* `gitops-demo` namespace 생성됨

* Deployment 생성됨

* Pod 2개 생성됨

* Service `LoadBalancer` 생성됨

---

# 16. 애플리케이션 접속 확인

## 16.1 서비스 외부 주소 확인

```
kubectlget svc -n gitops-demo
```

예시

```
NAME                  TYPE           CLUSTER-IP      EXTERNAL-IP
gitops-demo-service   LoadBalancer   10.x.x.x        a1b2c3d4....
```

브라우저 접속

```
http://EXTERNAL-IP
```

처음에는 화면에 대략 아래처럼 보이면 됨.

```
GitOps Demo Application
Version: initial
Pod Hostname: ...
This app is running on EKS and deployed by Argo CD.
```

---

# 17. GitHub Actions 설정

이제 핵심인 **코드 변경 → 이미지 빌드 → GitOps 저장소 수정** 자동화를 구성함.

---

## 17.1 GitHub Personal Access Token 준비

애플리케이션 저장소의 Workflow가 **다른 저장소인 GitOps 저장소에 push** 해야 하므로 GitHub 토큰이 필요함.

권장 방식

* Fine-grained Personal Access Token 생성

* 대상 저장소: `gitops-manifests`

* 권한: Contents - Read and Write

이 토큰은 애플리케이션 저장소의 GitHub Secrets에 넣을 것임.

---

## 17.2 GitHub Secrets 등록

애플리케이션 저장소 `gitops-app-source` 의

**Settings → Secrets and variables → Actions** 로 이동해서 아래 4개 등록

### 1) `DOCKERHUB_USERNAME`

```
본인도커허브ID
```

### 2) `DOCKERHUB_TOKEN`

```
Docker Hub Access Token
```

### 3) `GITOPS_REPO_TOKEN`

```
GitHub PAT 또는 fine-grained token
```

### 4) `GITOPS_REPO_USERNAME`

```
본인깃허브ID
```

---

# 18. GitHub Actions Workflow 파일 작성

파일명: `.github/workflows/ci.yaml`

```
name: Build Image And Update GitOps Repo

on:
  push:
    branches:
      - main

jobs:
  build-and-update:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout application source
        uses: actions/checkout@v4

      - name: Set image tag
        run: echo "IMAGE_TAG=${GITHUB_SHA::7}" >> $GITHUB_ENV

      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build Docker image
        run: |
          docker build -t ${{ secrets.DOCKERHUB_USERNAME }}/gitops-demo-app:${IMAGE_TAG} .

      - name: Push Docker image
        run: |
          docker push ${{ secrets.DOCKERHUB_USERNAME }}/gitops-demo-app:${IMAGE_TAG}

      - name: Checkout GitOps repository
        uses: actions/checkout@v4
        with:
          repository: ${{ secrets.GITOPS_REPO_USERNAME }}/gitops-manifests
          token: ${{ secrets.GITOPS_REPO_TOKEN }}
          path: gitops-manifests

      - name: Update deployment image and version
        run: |
          cd gitops-manifests
          sed -i "s|image: .*|image: ${{ secrets.DOCKERHUB_USERNAME }}/gitops-demo-app:${IMAGE_TAG}|g" kubernetes/deployment.yaml
          sed -i "s|value: \".*\"|value: \"${IMAGE_TAG}\"|g" kubernetes/deployment.yaml

      - name: Commit and push GitOps changes
        run: |
          cd gitops-manifests
          git config user.name "github-actions"
          git config user.email "github-actions@github.com"
          git add kubernetes/deployment.yaml
          git commit -m "Update image to ${IMAGE_TAG}" || echo "No changes to commit"
          git push origin HEAD:main
```

---

## 18.1 이 Workflow가 하는 일

### `actions/checkout@v4`

현재 애플리케이션 소스코드 저장소를 러너에 checkout 함.

### `IMAGE_TAG=${GITHUB_SHA::7}`

현재 커밋 해시 앞 7자리를 태그로 사용함.

예

```
a1b2c3d
```

### Docker Hub 로그인

GitHub Secrets에 넣은 사용자명과 토큰으로 로그인함.

### 이미지 빌드 및 Push

새 커밋 기준 이미지 생성 후 Docker Hub로 Push 함.

예

```
mydockerid/gitops-demo-app:a1b2c3d
```

### GitOps 저장소 clone

다른 저장소인 `gitops-manifests` 를 clone 함.

### `sed -i`

`deployment.yaml` 안의 아래 2개를 바꿈.

* `image:` 줄

* `APP_VERSION` 환경변수 값

즉

```
image: mydockerid/gitops-demo-app:initial
value: "initial"
```

이 부분이 예를 들어 이렇게 바뀜.

```
image: mydockerid/gitops-demo-app:a1b2c3d
value:"a1b2c3d"
```

### commit / push

GitOps 저장소에 변경사항을 commit 하고 push 함.

이 순간 Argo CD가 감지할 수 있는 Git 변경이 발생함.

---

# 19. Workflow 업로드

```
cd ~/gitops-app-source
git add .
git commit -m "add githubactions workflow"
git push origin main
```

이 push 자체로도 Workflow가 실행됨.

GitHub 저장소의 **Actions 탭** 에서 성공 여부 확인

---

# 20. 첫 자동 배포 확인

## 20.1 GitOps 저장소 확인

GitHub의 `gitops-manifests` 저장소에서 `kubernetes/deployment.yaml` 파일을 확인하면

`image:` 와 `APP_VERSION` 값이 커밋 SHA로 바뀌어 있어야 함.

---

## 20.2 Argo CD 확인

Argo CD UI에서 보면

* OutOfSync → Synced

* Healthy 상태

흐름이 보일 수 있음.

Argo CD는 Git과 클러스터 상태를 비교하고 차이가 있으면 Sync 함.

---

## 20.3 Pod 변경 확인

기존 Pod 확인

```
kubectl get pods -n gitops-demo -o wide
```

잠시 후 다시 확인

```
kubectl get pods -n gitops-demo -o wide
```

Pod 이름이 바뀌면 **새 ReplicaSet / 새 Pod 생성** 이 이루어진 것임.

Deployment에서 Pod 템플릿이 바뀌면 일반적으로 새 Pod가 생성되고 기존 Pod가 순차적으로 종료되는 롤링 업데이트가 일어남. 이것은 Kubernetes Deployment의 기본적인 동작 방식에 따른 결과라고 보면 됨.

---

# 21. GitOps 흐름 확인 실습

코드 변경을 하고 적용이 되는지 확인.

---

## 21.1 app.py 수정

`~/gitops-app-source/app.py` 파일에서 화면 문구를 바꿔봄.

기존

```
<p>ThisappisrunningonEKSanddeployedbyArgoCD.</p>
```

변경

```
<p>ThisappisrunningonEKSandupdatedthroughGitOpspipeline.</p>
```

또는 제목도 바꿔도 됨.

기존

```
<h1>GitOpsDemoApplication</h1>
```

변경

```
<h1>GitOpsDemoApplication-Updated</h1>
```

---

## 21.2 Git push

```
cd ~/gitops-app-source
git add .
git commit -m "update app message"
git push origin main
```

---

## 21.3 확인 순서

### 1) GitHub Actions 실행 확인

GitHub Actions 탭에서 Workflow 성공 여부 확인

### 2) Docker Hub 확인

새 태그 이미지가 추가되었는지 확인

### 3) GitOps 저장소 확인

`deployment.yaml` 의 `image:` 값이 새 SHA로 바뀌었는지 확인

### 4) Argo CD 확인

자동 Sync 되었는지 확인

### 5) Pod 확인

```
kubectl get pods -n gitops-demo -w
```

이 명령은 Pod 상태 변화를 실시간으로 보여줌.

예를 들어 이런 흐름이 보일 수 있음.

* 새 Pod `ContainerCreating`

* 새 Pod `Running`

* 기존 Pod `Terminating`

### 6) 웹 화면 확인

브라우저 새로고침

* Version 값이 새 SHA로 바뀌었는지

* 화면 문구가 수정되었는지

* Pod Hostname 이 바뀌었는지

---

# 22. 왜 Pod가 바뀌는가

이번 실습의 핵심은 이 부분임.

GitHub Actions가 GitOps 저장소의 `deployment.yaml` 안에서 아래 항목을 변경함.

```
image: 본인도커허브ID/gitops-demo-app:새태그
```

그리고 Deployment의 Pod 템플릿이 바뀌면 Kubernetes는 이를 **새로운 버전의 Pod가 필요하다고 판단**함.

그래서 보통 아래 흐름이 일어남.

```
기존 Pod 2개 실행 중
→ 새 이미지 태그가 적용된 ReplicaSet 생성
→ 새 Pod 생성
→ readinessProbe 통과
→ 기존 Pod 종료
```

즉, **컨테이너 내부만 덮어쓰는 것이 아니라 새 Pod가 생성되는 구조**로 이해하면 됨.

---

# 23. 실습 후 확인해야 할 핵심 포인트

이 실습이 제대로 된 경우 아래를 모두 확인할 수 있어야 함.

## 23.1 소스 저장소

코드가 수정되었음

## 23.2 CI

GitHub Actions가 성공했음

## 23.3 이미지 저장소

새 Docker 이미지가 Push 되었음

## 23.4 GitOps 저장소

`deployment.yaml` 의 이미지 태그가 자동 변경되었음

## 23.5 Argo CD

Git 변경을 감지하고 Sync 했음

## 23.6 Kubernetes

새 Pod가 생성되고 기존 Pod가 교체되었음

## 23.7 사용자 화면

웹 페이지 내용과 버전 문자열이 바뀌었음

---

# 24. 실습 중 자주 막히는 부분

## 24.1 `aws login` 이 안 되는 경우

확인

```
aws --version
```

CLI 버전이 너무 낮으면 `aws login` 이 동작하지 않을 수 있음. 최소 2.32.0 이상 필요함.

---

## 24.2 `kubectl get nodes` 가 안 되는 경우

다시 kubeconfig 갱신

```
aws eks update-kubeconfig--region ap-northeast-2 --name gitops-lab
```

그리고 프로파일이 현재 셸에 설정되어 있는지 확인

```
echo $AWS_PROFILE
```

---

## 24.3 Argo CD UI 접속이 안 되는 경우

```
kubectl get svc argocd-server -n argocd
```

`EXTERNAL-IP` 가 아직 `pending` 이면 잠시 더 기다려야 함.

---

## 24.4 앱 서비스 접속이 안 되는 경우

```
kubectl get svc -n gitops-demo
kubectl get pods -n gitops-demo
kubectl describe pod -n gitops-demo <pod이름>
```

특히 이미지 pull 실패가 많은 원인임.

* Docker Hub 이미지 이름 오타

* private repo인데 인증 미설정

* initial 이미지 미리 Push 안 함

---

## 24.5 GitHub Actions에서 GitOps 저장소 push 실패

주로 아래 원인임.

* `GITOPS_REPO_TOKEN` 권한 부족

* 저장소명 오타

* 사용자명 오타

* fine-grained token 대상 저장소 미포함

---

# 25. 최종 정리

이번 실습은 아래 구조를 완성하는 것임.

```
[gitops-app-source]
  app.py 수정
      ↓
  GitHub Actions
      ↓
  Docker 이미지 빌드 / Push
      ↓
  [gitops-manifests] deployment.yaml 수정
      ↓
  Argo CD가 Git 변경 감지
      ↓
  EKS Deployment 업데이트
      ↓
  새 Pod 생성
      ↓
  웹 화면 변경 확인
```