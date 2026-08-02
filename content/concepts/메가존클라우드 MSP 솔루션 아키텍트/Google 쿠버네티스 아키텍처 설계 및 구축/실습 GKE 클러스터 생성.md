---
title: "실습 GKE 클러스터 생성"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Google 쿠버네티스 아키텍처 설계 및 구축"]
is_public: true
draft: false
---

# 실습. GKE 클러스터 생성

## 실습 목표

* GKE Autopilot 클러스터를 콘솔에서 생성함

* GKE Autopilot 클러스터를 `gcloud`로 생성함

* 생성한 클러스터에 `kubectl`로 접속함

* 클러스터 상태를 확인함

* 실습 종료 후 클러스터를 삭제함

---

# 1. 사전 준비

## 1-1. 프로젝트 선택

1. Google Cloud Console에 로그인

2. 상단의 프로젝트 선택 메뉴 클릭

3. 실습에 사용할 프로젝트 선택

---

## 1-2. API 활성화

GKE를 사용하려면 **Kubernetes Engine API**를 활성화해야 함. 클러스터 생성 전에 GKE API 활성화가 필요함.

콘솔에서 진행:

1. 좌측 상단 메뉴

2. **Kubernetes Engine** 검색 또는 선택

3. 처음 진입 시 **사용 설정** 버튼 클릭

또는 Cloud Shell / 로컬 터미널에서 실행:

```
gcloud services enable container.googleapis.com
```

### 명령 설명

* `gcloud services enable`
  + 특정 Google Cloud API를 활성화하는 명령

* `container.googleapis.com`
  + GKE에서 사용하는 Kubernetes Engine API 이름

---

## 1-3. Cloud Shell 또는 로컬 환경 준비

권장 방식은 **Cloud Shell** 사용임.

이유는 `gcloud`와 `kubectl`이 기본 준비돼 있어서 바로 실습 가능하기 때문임.

로컬 PC에서 진행한다면 다음 확인이 필요함.

```
gcloud version
kubectl version --client
```

---

## 1-4. 기본 프로젝트 및 리전 설정

예시는 서울 리전 기준으로 작성했음.

```
gcloud config set project [PROJECT_ID]
gcloud config set compute/region asia-northeast3
gcloud config set compute/zone asia-northeast3-a
```

예시:

```
gcloud config set project my-gke-project
gcloud config set compute/region asia-northeast3
gcloud config set compute/zone asia-northeast3-a
```

설정 확인:

```
gcloud config list
```

### 명령 설명

* `gcloud config set project`
  + 현재 작업할 프로젝트를 지정함

* `gcloud config set compute/region`
  + 기본 리전을 지정함

* `gcloud config set compute/zone`
  + 기본 존을 지정함

---

# 2. 콘솔로 GKE 클러스터 생성

## 2-1. GKE 메뉴 진입

1. Google Cloud Console 접속

2. 좌측 메뉴에서 **Kubernetes Engine**

3. 클러스터 만들기 클

4. **Create** 클릭

---

## 2-2. Autopilot 클러스터 만들기

Standard 클러스터를 만들려면 생성 화면에서 우측 상단에 Standard 클러스터 전환.

---

## 2-3. 클러스터 정보 입력

다음과 같이 입력

* **Name**: `이니셜-gke-cluster-1`

* **Region**: `asia-northeast3`

---

## 2-4. 네트워킹

* VPC 네트워크 선택 : Custom-vpc

* 노드 서브넷 선택 : subnet-seoul-1

* 클러스터 기본 포드 IP주소 범위 설정(선택) : 192.168.0.0/16

## 2-4. 생성 실행

1. 하단의 **Create** 클릭

2. 클러스터 생성 진행 상태 확인

3. 상태가 정상으로 바뀔 때까지 대기

---

## 2-5. 생성 결과 확인

클러스터 목록에서 다음 항목 확인

* 클러스터 이름: `이니셜-gke-cluster-1`

* 위치: `asia-northeast3`

* 모드: `Autopilot`

* 상태: 정상

---

# 3. gcloud로 GKE 클러스터 생성

Autopilot 클러스터 생성 명령은 `gcloud container clusters create-auto` 형식을 사용함.

## 3-1. 기본 생성 명령

```
gcloud container clusters create-auto 이니셜-gke-cluster-1 \
  --location=asia-northeast3
```

### 명령 설명

* `gcloud container clusters`
  + GKE 클러스터를 다루는 명령 그룹

* `create-auto`
  + Autopilot 클러스터 생성 명령

* `이니셜-gke-cluster-1`
  + 생성할 클러스터 이름

* `--location=asia-northeast3`
  + 클러스터 생성 위치 지정

---

## 3-2. 생성 완료 후 클러스터 목록 확인

```
gcloud container clusters list
```

특정 클러스터 상세 확인:

```
gcloud container clusters describe 이니셜-gke-cluster-1 \
  --location=asia-northeast3
```

Autopilot 여부 확인 포인트:

```
autopilot:
  enabled: true
```

---

# 4. kubectl 접속 정보 가져오기

클러스터를 생성했다고 해서 바로 `kubectl`이 연결되는 것은 아님.

`get-credentials` 명령으로 kubeconfig에 접속 정보를 저장해야 함.

클러스터를 연결:

```
gcloud container clusters get-credentials 이니셜-gke-cluster-1 \
  --location=asia-northeast3
```

### 명령 설명

* `get-credentials`
  + 클러스터 접속 정보를 로컬 kubeconfig에 등록함

* 이후 `kubectl` 명령이 해당 클러스터 대상으로 동작하게 됨

---

# 5. 클러스터 상태 확인

## 5-1. 현재 컨텍스트 확인

```
kubectl config current-context
```

---

## 5-2. 노드 확인

```
kubectl get nodes
```

정상이라면 `Ready` 상태의 노드 정보가 보임.

---

## 5-3. 시스템 네임스페이스 확인

```
kubectl get ns
```

---

## 5-4. 전체 Pod 확인

```
kubectl get pods -A
```

---

# 6. 실습 확인용 최소 테스트

클러스터 생성만 검증하려면 아래 정도만 확인하면 됨.

```
gcloud container clusters list
kubectl config current-context
kubectl get nodes
kubectl get pods -A
```

---

# 7. 삭제 실습

실습 종료 후 반드시 삭제해야 함.

## 7-1. 콘솔에서 만든 클러스터 삭제

```
gcloud container clusters delete gke-auto-lab \
  --location=asia-northeast3
```

## 7-2. gcloud로 만든 클러스터 삭제

```
gcloud container clusters delete gke-auto-cli \
  --location=asia-northeast3
```

### 명령 설명

* `delete`
  + 지정한 GKE 클러스터를 삭제함

* `-location`
  + 생성한 위치와 동일하게 지정해야 함

---

# 8. 그대로 따라 하는 최소 실습 절차

## 8-1. 콘솔 생성 방식

### 실습 순서

1. 프로젝트 선택

2. Kubernetes Engine API 활성화

3. Kubernetes Engine 메뉴 이동

4. Create 클릭

5. Autopilot 선택

6. Name: `gke-auto-lab`

7. Region: `asia-northeast3`

8. Create 클릭

9. 생성 완료 확인

10. Cloud Shell 열기

11. 아래 명령 실행

```
gcloud container clusters get-credentials gke-auto-lab \
  --location=asia-northeast3

kubectl get nodes
kubectl get pods -A
```

---

## 8-2. gcloud 생성 방식

### 실습 순서

1. 프로젝트 선택

2. Kubernetes Engine API 활성화

3. Cloud Shell 실행

4. 아래 명령 순서대로 실행

```
gcloud config set project [PROJECT_ID]
gcloud config set compute/region asia-northeast3

gcloud services enable container.googleapis.com

gcloud container clusters create-auto gke-auto-cli \
  --location=asia-northeast3 \
  --release-channel=regular

gcloud container clusters get-credentials gke-auto-cli \
  --location=asia-northeast3

kubectl get nodes
kubectl get pods -A
```

1. 실습 종료 후 삭제

```
gcloud container clusters delete gke-auto-cli \
  --location=asia-northeast3
```

---

# 9. 자주 발생하는 오류

## 9-1. API 비활성화 오류

증상:

* 클러스터 생성 시 API 관련 오류 발생

해결:

```
gcloud services enable container.googleapis.com
```

공식 빠른 시작 문서에서도 GKE 사용 전 API 활성화가 필요하다고 안내함. ([Google Cloud Documentation](https://docs.cloud.google.com/kubernetes-engine/docs/quickstarts/create-cluster?utm_source=chatgpt.com))

---

## 9-2. `kubectl get nodes` 실패

증상:

* 인증 오류

* 현재 컨텍스트 없음

* 서버 연결 실패

해결:

```
gcloud container clusters get-credentials gke-auto-cli \
  --location=asia-northeast3

kubectl config current-context
```

---

## 9-3. 잘못된 프로젝트에 생성함

확인:

```
gcloud config list
```

필요 시 다시 지정:

```
gcloud config set project [PROJECT_ID]
```

---

# 10. 강의용 최종 실습본

## A안. 콘솔 생성만 진행하는 짧은 실습

```
1. 프로젝트 선택
2. Kubernetes Engine API 활성화
3. Kubernetes Engine > Clusters > Create
4. Autopilot 선택
5. Name: gke-auto-lab
6. Region: asia-northeast3
7. Create
8. Cloud Shell 실행
9. get-credentials 실행
10. kubectl get nodes 확인
11. 클러스터 삭제
```

## B안. gcloud만으로 진행하는 짧은 실습

```
gcloud config set project [PROJECT_ID]
gcloud services enable container.googleapis.com

gcloud container clusters create-auto gke-auto-cli \
  --location=asia-northeast3 \
  --release-channel=regular

gcloud container clusters get-credentials gke-auto-cli \
  --location=asia-northeast3

kubectl get nodes
kubectl get pods -A

gcloud container clusters delete gke-auto-cli \
  --location=asia-northeast3
```

원하면 다음 단계로 이어서 \*\*“GKE 클러스터 생성 후 NGINX 배포까지 포함한 실습본”\*\*으로 바로 확장해주겠어요.