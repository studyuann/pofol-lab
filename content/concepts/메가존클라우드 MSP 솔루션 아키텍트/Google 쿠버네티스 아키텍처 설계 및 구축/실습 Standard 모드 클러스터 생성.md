---
title: "실습 Standard 모드 클러스터 생성"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Google 쿠버네티스 아키텍처 설계 및 구축"]
is_public: true
draft: false
---

# 실습. Standard 모드 클러스터 생성

---

## 1. 실습 목표

* GKE **Standard 모드** 클러스터를 콘솔에서 생성함

* GKE **Standard 모드** 클러스터를 `gcloud`로 생성함

* 생성한 클러스터에 `kubectl`로 접속함

* 노드와 클러스터 상태를 확인함

* 실습 종료 후 클러스터를 삭제함

---

# 2. 사전 준비

## 2-1. 프로젝트 선택

1. Google Cloud Console 로그인

2. 상단 프로젝트 선택

3. 실습용 프로젝트 선택

---

## 2-2. Kubernetes Engine API 활성화

콘솔에서:

1. 좌측 메뉴에서 **Kubernetes Engine** 이동

2. 처음 진입 시 **사용 설정** 클릭

또는 Cloud Shell / 로컬 터미널에서 실행:

```
gcloud services enable container.googleapis.com
```

---

## 2-3. Cloud Shell 또는 로컬 환경 준비

Cloud Shell 사용을 권장함.

확인 명령:

```
gcloud version
kubectl version --client
```

---

## 2-4. 기본 프로젝트와 위치 설정

이번 실습은 **최소 설정**이 목적이라서 **zonal Standard cluster**로 진행함.

서울 기준 예시는 다음과 같음.

```
gcloud config set project [PROJECT_ID]
gcloud config set compute/zone asia-northeast3-a
```

설정 확인:

```
gcloud config list
```

GKE Standard 클러스터는 zonal 또는 regional로 만들 수 있는데, 실습을 가장 단순하게 하려면 zonal 방식이 적합함.

---

# 3. 콘솔로 Standard 모드 클러스터 생성

## 3-1. GKE 메뉴 이동

1. Google Cloud Console 접속

2. 좌측 메뉴에서 **Kubernetes Engine**

3. **Clusters** 화면 이동

4. **Create** 클릭

---

## 3-2. Standard 선택

생성 화면에서 다음 중 하나를 선택하는 화면이 나옴.

* Autopilot

* Standard

여기서는 **Standard** 선택

---

## 3-3. 꼭 필요한 값만 입력

아래 항목만 입력 또는 확인함.

* **Name**: `gke-std-lab`

* **Location type / 위치**: **Zonal**

* **Zone**: `asia-northeast3-a`

나머지는 기본값 유지

### 실습 기준으로 건드리지 않는 항목

* 네트워크

* 보안

* 가용성 설정

* 노드풀 세부 설정

* 유지보수 정책

* 버전 고정

* 고급 기능

---

## 3-4. 생성 실행

1. **Create** 클릭

2. 클러스터 생성 상태 확인

3. 상태가 정상으로 바뀔 때까지 대기

---

## 3-5. 생성 결과 확인

클러스터 목록에서 확인할 항목:

* 이름: `gke-std-lab`

* 모드: `Standard`

* 위치: `asia-northeast3-a`

* 상태: 정상

---

# 4. gcloud로 Standard 모드 클러스터 생성

GKE Standard 클러스터는 `create-auto`가 아니라 `create` 명령을 사용함.

## 4-1. 최소 설정으로 생성

```
gcloud container clusters create gke-std-cli \
  --zone=asia-northeast3-a
```

### 명령 설명

### `gcloud container clusters create`

* GKE **Standard 모드** 클러스터 생성 명령임

* Autopilot 생성 명령인 `create-auto`와 다름

### `gke-std-cli`

* 생성할 클러스터 이름임

### `--zone=asia-northeast3-a`

* zonal 클러스터를 만들 위치를 지정함

* 이 옵션이 없으면 위치 관련 오류가 날 수 있음

---

## 4-2. 생성 완료 확인

```
gcloud container clusters list
```

특정 클러스터 상세 확인:

```
gcloud container clusters describe gke-std-cli \
  --zone=asia-northeast3-a
```

### 확인 포인트

* 이름 확인

* 위치 확인

* 상태 확인

* 노드풀 생성 여부 확인

---

# 5. kubectl 접속 정보 가져오기

콘솔에서 만든 클러스터 접속:

```
gcloud container clusters get-credentials gke-std-lab \
  --zone=asia-northeast3-a
```

CLI에서 만든 클러스터 접속:

```
gcloud container clusters get-credentials gke-std-cli \
  --zone=asia-northeast3-a
```

### 명령 설명

### `get-credentials`

* 생성한 GKE 클러스터의 접속 정보를 로컬 kubeconfig에 저장함

* 이후 `kubectl` 명령으로 클러스터에 접근 가능해짐

---

# 6. 클러스터 상태 확인

## 6-1. 현재 컨텍스트 확인

```
kubectl config current-context
```

## 6-2. 노드 확인

```
kubectl get nodes
```

## 6-3. 네임스페이스 확인

```
kubectl get ns
```

## 6-4. 시스템 Pod 확인

```
kubectl get pods -A
```

정상이라면 노드가 `Ready` 상태로 보이고, `kube-system` 관련 Pod들도 조회됨.

---

# 7. 실습 종료 후 삭제

## 7-1. 콘솔에서 만든 클러스터 삭제

```
gcloud container clusters delete gke-std-lab \
  --zone=asia-northeast3-a
```

## 7-2. gcloud에서 만든 클러스터 삭제

```
gcloud container clusters delete gke-std-cli \
  --zone=asia-northeast3-a
```

---

# 8. 실습 절차

## 8-1. 콘솔 방식

### 실습 순서

1. 프로젝트 선택

2. Kubernetes Engine API 활성화

3. Kubernetes Engine → Clusters 이동

4. **Create** 클릭

5. **Standard** 선택

6. Name: `gke-std-lab`

7. Location type: **Zonal**

8. Zone: `asia-northeast3-a`

9. **Create** 클릭

10. 생성 완료 확인

11. Cloud Shell 실행

12. 아래 명령 실행

```
gcloud container clusters get-credentials gke-std-lab \
  --zone=asia-northeast3-a

kubectl get nodes
kubectl get pods -A
```

---

## 8-2. gcloud 방식

### 실습 순서

1. 프로젝트 선택

2. API 활성화

3. Cloud Shell 실행

4. 아래 명령 순서대로 실행

```
gcloud config set project [PROJECT_ID]
gcloud config set compute/zone asia-northeast3-a

gcloud services enable container.googleapis.com

gcloud container clusters create gke-std-cli \
  --zone=asia-northeast3-a

gcloud container clusters get-credentials gke-std-cli \
  --zone=asia-northeast3-a

kubectl get nodes
kubectl get pods -A
```

1. 실습 종료 후 삭제

```
gcloud container clusters delete gke-std-cli \
  --zone=asia-northeast3-a
```

---