---
title: "실습 1 Jenkins 기반 CI 파이프라인 구성"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "DevOps 환경에서의 CI CD"]
is_public: true
draft: false
---

# 실습 1. Jenkins 기반 CI 파이프라인 구성

## 실습 목표

이 실습에서는 Jenkins를 이용해 GitHub 저장소의 코드 변경을 감지하고, 자동으로 소스코드를 가져와 Docker 이미지를 빌드한 뒤 컨테이너 레지스트리에 업로드하는 **기본 CI 파이프라인**을 구성한다.

또한 Jenkins가 단순 빌드 도구가 아니라, **코드 변경 → 자동 실행 → 이미지 생성 → 결과물 배포 준비**까지 연결하는 자동화 서버라는 점을 실습으로 확인한다.

이 실습을 끝내면 다음이 가능해진다.

* Jenkins 설치 및 초기 접속

* GitHub 저장소 연동

* Jenkins Pipeline Job 생성

* GitHub Webhook 기반 자동 실행

* Docker 이미지 빌드

* 컨테이너 레지스트리 Push

* 전체 CI 흐름 검증

---

## 실습 개요

이번 실습은 앞에서 나눠서 보았던 Jenkins 관련 세부 실습을 **하나의 흐름**으로 묶어서 수행하는 통합 실습이다.

실습 전체 흐름은 다음과 같다.

```
Jenkins 설치
→ 초기 관리자 설정
→ GitHub 저장소 준비
→ Jenkins Pipeline Job 생성
→ GitHub Webhook 등록
→ 코드 push 시 자동 실행
→ Docker 이미지 빌드
→ 컨테이너 레지스트리 Push
→ 결과 확인
```

즉, 이번 실습은 Jenkins를 "설치만 해보는 것"이 아니라

**실제로 CI 파이프라인 역할을 수행하게 만드는 것**이 목적이다.

---

## 전체 아키텍처

```
개발자
   ↓ git push
GitHub Repository
   ↓ Webhook
Jenkins Server
   ├─ Pipeline Job 실행
   ├─ Git checkout
   ├─ Docker 이미지 빌드
   └─ Registry Push
        ↓
Container Registry
```

이 구조에서 각 구성요소 역할은 다음과 같다.

### GitHub

소스코드 저장소 역할을 하며, 코드 변경 이벤트를 Jenkins에 전달한다.

### Jenkins

CI 파이프라인 실행 서버 역할을 하며, 코드를 받아 이미지 빌드와 업로드를 수행한다.

### Container Registry

Jenkins가 생성한 이미지를 저장하는 중앙 저장소 역할을 한다.

---

## 실습 환경

### 서버 환경

* OS: Ubuntu 22.04 LTS

* CPU: 2 vCPU 이상

* Memory: 4GB 이상

* Disk: 20GB 이상

### 소프트웨어

* Jenkins LTS

* OpenJDK 21

* Git

* Docker

* 브라우저

* GitHub 계정

* Docker Hub 계정 또는 다른 컨테이너 레지스트리 계정

### 네트워크 조건

* Jenkins 서버에서 인터넷 접근 가능

* GitHub에서 Jenkins로 접근 가능한 주소 보유

* Jenkins 8080 포트 외부 접근 가능

* Docker Hub 또는 사용하는 레지스트리 접근 가능

---

## 사전 준비사항

실습 전에 다음을 준비한다.

* GitHub 저장소 1개

* Docker Hub 계정 1개

* Jenkins 서버 1대

* 공인 IP 또는 외부 접근 가능한 도메인

* Ubuntu 서버 sudo 권한 계정

---

## 실습용 GitHub 저장소 준비

이번 실습에서는 Docker 이미지 빌드를 위해 간단한 정적 웹 예제를 사용한다.

저장소 예시 이름:

```
jenkins-ci-lab
```

저장소 구조는 다음처럼 구성한다.

```
jenkins-ci-lab/
 ├─ Dockerfile
 ├─ index.html
 └─ README.md
```

### `index.html`

```
<!DOCTYPE html>
<html>
<head>
<metacharset="UTF-8">
<title>Jenkins CI Lab</title>
</head>
<body>
<h1>Jenkins CI Pipeline Success</h1>
<p>This page is served from an image built by Jenkins.</p>
</body>
</html>
```

### `Dockerfile`

```
FROM nginx:latest

COPY index.html /usr/share/nginx/html/index.html
```

### Dockerfile 설명

### `FROM nginx:latest`

Nginx 공식 이미지를 기반 이미지로 사용한다.

### `COPY index.html ...`

현재 저장소의 `index.html` 파일을 Nginx 웹 루트 위치에 복사한다.

즉, 이 이미지는 **Nginx + 사용자 정의 정적 페이지** 구조를 가진다.

---

## 1단계. Jenkins 설치

먼저 Ubuntu 서버에 접속한다.

### 1-1. 패키지 목록 갱신

```
sudo apt update
sudo apt upgrade -y
```

### 설명

* `apt update`는 설치 가능한 패키지 목록을 최신화한다.

* `apt upgrade -y`는 현재 설치된 패키지를 최신 버전으로 갱신한다.

---

### 1-2. Java 설치

```
sudo apt install -y openjdk-21-jdk
```

설치 확인:

```
java-version
```

### 설명

Jenkins는 Java 기반 애플리케이션이다.

즉, Java 런타임이 없으면 Jenkins 자체가 동작할 수 없다.

---

### 1-3. Jenkins 저장소 키 등록

```
sudo wget -O /etc/apt/keyrings/jenkins-keyring.asc \
  https://pkg.jenkins.io/debian-stable/jenkins.io-2026.key
```

### 설명

Jenkins 공식 저장소의 서명 키를 시스템에 등록한다.

이 키는 이후 Jenkins 패키지를 신뢰 가능한 출처에서 받았는지 검증하는 데 사용된다.

---

### 1-4. Jenkins 저장소 등록

```
echo "deb [signed-by=/etc/apt/keyrings/jenkins-keyring.asc]" \
  https://pkg.jenkins.io/debian-stable binary/ | sudo tee \
  /etc/apt/sources.list.d/jenkins.list > /dev/null
```

다시 패키지 목록을 갱신한다.

```
sudo apt update
```

---

### 1-5. Jenkins 설치

```
sudo apt install -y jenkins
```

설치 후 서비스 상태 확인:

```
sudo systemctl status jenkins
```

### 정상 확인 포인트

* `Active: active (running)` 이 보이면 정상 실행 상태다.

---

### 1-6. 방화벽 및 포트 확인

```
sudo ufw status
sudo ufw allow 8080/tcp
```

* Amazon Linux 2023에 설치

```
sudo wget -O /etc/yum.repos.d/jenkins.repo \
    https://pkg.jenkins.io/rpm-stable/jenkins.repo
sudo dnf upgrade
# Add required dependencies for the jenkins package
sudo dnf install java-21-amazon-corretto-devel -y
sudo dnf install jenkins
sudo systemctl daemon-reload
```

### 설명

Jenkins 기본 웹 포트는 8080이다.

외부 브라우저에서 접속하려면 서버 방화벽과 클라우드 보안그룹 모두 8080 허용이 필요하다.

---

### 1-7. 초기 관리자 비밀번호 확인

```
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

이 값을 복사해둔다.

---

### 1-8. 브라우저 접속 및 초기 설정

브라우저에서 접속:

```
http://서버IP:8080
```

또는

```
http://도메인:8080
```

초기 설정 절차:

* Unlock Jenkins 화면에서 초기 비밀번호 입력

* Install suggested plugins 선택

* 관리자 계정 생성

* Jenkins URL 확인

* 대시보드 진입

---

## 2단계. Git 및 Docker 설치

Jenkins 서버에서 Git과 Docker가 필요하다.

### 2-1. Git 설치

```
sudo apt install -y git | sudo dnf install -y git
git --version
```

### 설명

Jenkins가 GitHub 저장소를 checkout 하려면 Git CLI가 필요하다.

---

### 2-2. Docker 저장소 추가

```
# Add Docker's official GPG key:
sudo apt update
sudo apt install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update
```

### 2-3. Docker 설치

```
sudo apt install -y docker-ce docker-ce-cli containerd.io \ 
docker-buildx-plugin docker-compose-plugin
```

```
sudo dnf install -y docker
```

서비스 상태 확인:

```
sudo systemctl status docker
```

버전 확인:

```
sudo docker version
```

---

## 3단계. Jenkins가 Docker 명령을 실행할 수 있도록 권한 설정

Jenkins Job 안에서 Docker build를 하려면 `jenkins` 사용자에게 Docker 접근 권한이 필요하다.

### 3-1. jenkins 사용자를 docker 그룹에 추가

```
sudo usermod -aG docker jenkins
```

### 설명

* `usermod -aG docker jenkins` 는 `jenkins` 사용자를 docker 그룹에 추가한다.

* Docker 소켓 접근 권한을 위해 필요한 설정이다.

---

### 3-2. Jenkins 재시작

```
sudo systemctl restart jenkins
```

필요 시 Docker도 재시작한다.

```
sudo systemctl restart docker
```

그룹 반영 확인:

```
id jenkins
```

### 확인 포인트

출력 결과에 `docker` 그룹이 포함되어 있어야 한다.

---

## 4단계. Docker Hub 자격증명 준비

### 4-1. Docker Hub 계정 확인

예시 사용자명:

```
mydockerid
```

### 4-2. Access Token 준비

실습용 비밀번호 대신 Docker Hub Access Token 사용을 권장한다.

### 이유

* 비밀번호 직접 사용보다 안전함

* 자동화 도구에 적합함

* 추후 폐기와 교체가 쉬움

---

## 5단계. Jenkins Credentials 등록

Jenkins에 레지스트리 인증정보를 안전하게 저장한다.

### 이동 경로

* **Manage Jenkins**

* **Credentials**

환경에 따라 **System → Global credentials** 구조가 보일 수 있다.

### 5-1. Add Credentials 클릭

다음 값 입력:

* Kind: `Username with password`

* Username: Docker Hub 사용자명

* Password: Docker Hub 토큰

* ID: `dockerhub-creds`

* Description: `Docker Hub registry credentials`

저장한다.

### 설명

이 Credential은 이후 Pipeline에서 참조한다.

절대로 Jenkinsfile이나 Shell 스크립트 안에 비밀번호를 직접 적지 않는다.

---

## 6단계. GitHub 저장소를 Jenkins와 연동할 Pipeline Job 생성

### 6-1. New Item 생성

* Item name: `jenkins-ci-pipeline`

* Type: **Pipeline**

* OK 클릭

---

### 6-2. Pipeline Job이 필요한 이유

이번 실습 전체 CI 흐름

* Git checkout

* Docker build

* 태그 지정

* 레지스트리 로그인

* 이미지 Push

이런 흐름은 Freestyle보다 Pipeline으로 관리하는 편이 훨씬 구조적이다.

즉, Stage 단위로 나눠서 실행 흐름을 보기 쉽게 만들 수 있다.

---

## 7단계. Pipeline Script 작성

이번 실습에서는 Jenkins UI 안에 직접 Script를 넣는 방식으로 시작한다.

실무에서는 Git 저장소 안 `Jenkinsfile`로 분리하는 것이 일반적이지만, 지금은 흐름 이해가 우선이다.

Pipeline 섹션에서 `Pipeline script` 선택 후 아래 코드를 입력한다.

```
pipeline {
    agent any

    environment {
        // Docker Hub 계정 ID와 Credential ID를 환경변수로 빼두면 관리가 편합니다.
        DOCKERHUB_USER = '사용자명' // 실제 본인의 ID로 수정하세요
        DOCKERHUB_CREDS = 'dockerhub-creds'
        
        IMAGE_NAME = 'sample-docker-app'
        IMAGE_TAG  = 'latest'
        
        // 최종 이미지 전체 경로 (변수 조합)
        REGISTRY_IMAGE = "${DOCKERHUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}"
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/사용자명/jenkins-ci-lab.git'
            }
        }

        stage('Build & Tag Image') {
            steps {
                script {
                    // docker DSL을 사용하여 객체지향적으로 빌드
                    def myApp = docker.build("${REGISTRY_IMAGE}")
                    
                    // (선택 사항) 빌드된 이미지의 ID 등을 확인하고 싶을 때
                    sh "docker images | grep ${IMAGE_NAME}"
                }
            }
        }

        stage('Push Image') {
            steps {
                script {                  
                    // 로그인-푸시-로그아웃을 한 번에 처리합니다.
                    docker.withRegistry('', DOCKERHUB_CREDS) {
                        sh "docker push ${REGISTRY_IMAGE}"
                        
                        // 만약 빌드 번호를 태그로 추가하고 싶다면?
                        // sh "docker tag ${REGISTRY_IMAGE} ${DOCKERHUB_USER}/${IMAGE_NAME}:${env.BUILD_NUMBER}"
                        // sh "docker push ${DOCKERHUB_USER}/${IMAGE_NAME}:${env.BUILD_NUMBER}"
                    }
                }
            }
        }

        stage('Verify') {
            steps {
                echo "Successfully pushed to: ${REGISTRY_IMAGE}"
                // 빌드 후에 로컬 이미지를 정리하고 싶다면 아래 주석 해제
                // sh "docker rmi ${REGISTRY_IMAGE}"
            }
        }
    }

    post {
        success {
            echo "✅ Jenkins CI Pipeline 실행 성공: ${REGISTRY_IMAGE}"
        }
        failure {
            echo '❌ Jenkins CI Pipeline 실행 실패'
        }
        always {
            echo '🏁 Pipeline 종료'
        }
    }
}
```

---

## 8단계. Pipeline 코드 상세 설명

이 코드는 길어 보이지만, 흐름은 매우 단순하다.

---

### 8-1. 환경 변수 정의 및 사전 설정 (Environment)

본격적인 작업에 앞서, 파이프라인 전반에서 반복적으로 사용할 값들을 변수로 선언한다.

* `DOCKERHUB_CREDS`: Jenkins의 'Credentials' 메뉴에 저장된 도커 허브 인증 정보의 ID를 호출한다. 이는 코드에 비밀번호를 노출하지 않으면서 안전하게 인증을 처리하기 위함이다.

* `REGISTRY_IMAGE`: 사용자 ID와 이미지 이름, 태그를 하나의 문자열로 결합한다. 이렇게 변수화해 두면 나중에 이미지 이름이나 태그(버전)가 바뀌더라도 상단의 환경 변수만 수정하면 되므로 유지보수가 매우 편리해진다.

### 8-2. 소스 코드 가져오기 (Checkout)

파이프라인의 첫 번째 단계로, 대상이 되는 소스 코드를 Jenkins 에이전트 환경으로 복사해온다.

* `git` 명령을 사용하여 GitHub 리포지토리의 `main` 브랜치로부터 최신 코드를 내려받는다. 이 과정이 완료되어야 이후 단계에서 `Dockerfile`을 찾고 이미지를 빌드하는 작업이 가능하다.

### 8-3. 도커 이미지 빌드 및 태깅 (Build & Tag Image)

내려받은 소스 코드에 포함된 `Dockerfile`을 읽어 실행 가능한 컨테이너 이미지를 생성한다.

* `docker.build`: Jenkins의 Docker 전용 플러그인 기능을 사용하여 빌드를 수행한다. 터미널에서 `docker build -t ...` 명령어를 직접 입력하는 것과 동일한 효과를 내며, 앞서 정의한 `REGISTRY_IMAGE` 명칭으로 이미지가 생성된다.

* 빌드 직후 `sh` 명령을 통해 로컬에 이미지가 정상적으로 생성되었는지 리스트를 확인하는 과정을 거친다.

### 8-4. 도커 레지스트리 전송 (Push Image)

로컬에서 빌드된 이미지를 전 세계 어디서든 꺼내 쓸 수 있도록 도커 허브(Registry)로 전송한다.

* `docker.withRegistry`: 이 구문은 해당 블록 안에서만 유효한 임시 인증 세션을 생성한다. 안전하게 로그인을 수행하고, 전송이 끝나면 자동으로 로그아웃까지 처리하므로 보안상 매우 강력한 방식이다.

* 전송 시 이미지 태그를 `latest` 외에 `env.BUILD_NUMBER`(Jenkins 빌드 번호)로 추가 생성하여 푸시하면, 문제 발생 시 특정 시점으로 롤백하기 쉬운 관리 체계가 구축된다.

### 8-5. 검증 및 사후 처리 (Verify & Post)

모든 작업이 끝난 후의 결과물 확인과 알림 과정을 수행한다.

* **Verify**: 푸시된 최종 이미지 경로를 콘솔에 출력하여 작업이 성공했음을 명시적으로 알린다. 필요에 따라 빌드에 사용된 로컬 이미지를 삭제하여 서버의 디스크 용량을 관리하는 작업을 추가하기도 한다.

* **Post Actions**: 파이프라인 전체의 성공과 실패 여부를 감지한다. `success` 시에는 축하 메시지를, `failure` 시에는 에러 로그를 출력하며, 실무에서는 이 단계에서 담당자에게 슬랙(Slack) 메시지를 보내 실시간으로 장애를 인지할 수 있도록 구성한다.

---

## 9단계. 수동 실행으로 1차 검증

먼저 Webhook 없이 수동으로 한 번 실행해본다.

### 실행 방법

* Job 화면

* **Build Now** 클릭

### 기대 결과

Stage가 순서대로 실행된다.

```
Checkout
→ Prepare
→ Build Image
→ Push Image
→ Verify
```

---

## 10단계. Console Output 확인

성공 시 로그에서 다음을 확인한다.

### 10-1. checkout 성공

* Git clone/fetch 로그

* Workspace 경로 확인

### 10-2. docker version 정상 출력

* Docker Client/Server 정보 보임

### 10-3. docker build 성공

* `load build definition from Dockerfile`

* `COPY index.html ...`

* `naming to ... sample-docker-app:latest`

### 10-4. docker login 성공

* `Login Succeeded`

### 10-5. docker push 성공

* `The push refers to repository ...`

* `digest: sha256: ...`

### 10-6. Finished: SUCCESS

최종 성공 상태 확인

---

## 11단계. Docker Hub 업로드 결과 확인

Docker Hub 웹사이트에서 다음을 확인한다.

* Repository 생성 여부

* `sample-docker-app` 저장 여부

* `latest` 태그 존재 여부

* 최근 push 시간

이 단계는 매우 중요하다.

Jenkins 콘솔 로그만으로 끝내지 않고, **실제 레지스트리에 결과물이 올라갔는지 외부 시점에서 확인**해야 한다.

---

## 12단계. GitHub Webhook 연동

이제 코드 push 시 Jenkins가 자동 실행되도록 연결한다.

---

### 12-1. Jenkins Job Trigger 설정

Job 설정으로 들어간다.

**Build Triggers** 섹션에서 아래 항목 체크:

```
GitHub hook trigger for GITScm polling
```

저장한다.

---

### 12-2. GitHub Webhook 등록

GitHub 저장소로 이동:

* **Settings**

* **Webhooks**

* **Add webhook**

입력값:

### Payload URL

```
http://JENKINS주소/github-webhook/
```

예:

```
http://203.0.113.10:8080/github-webhook/
```

### Content type

```
application/json
```

### Events

```
Just the push event
```

### Active

체크 상태 유지

저장한다.

---

## 13단계. Webhook 기반 자동 실행 검증

이제 로컬 저장소에서 파일을 하나 수정하고 push 한다.

예:

```
echo"<p>Webhook triggered build</p>" >> index.html
git add index.html
git commit-m"test: trigger jenkins webhook build"
git push origin main
```

### 기대 동작

* GitHub push 발생

* GitHub가 Jenkins Webhook URL 호출

* Jenkins Pipeline 자동 실행

* Build History에 새 실행 번호 생성

---

## 14단계. 자동 실행 여부 확인

Jenkins Build History에서 새 Build를 클릭한다.

### 확인 포인트

* 수동 실행이 아니라 자동 실행인가

* 시작 원인에 GitHub push 관련 메시지가 있는가

* 전체 Stage가 다시 정상 수행되는가

즉, 지금부터 Jenkins는 사람이 버튼을 누르는 시스템이 아니라

**코드 변경에 반응하는 이벤트 기반 CI 서버**가 된다.

---

## 15단계. 최종 검증 포인트

이번 실습이 정상적으로 끝났다면 다음이 모두 충족되어야 한다.

* Jenkins 웹 UI 접속 가능

* Pipeline Job 생성 완료

* GitHub 저장소 checkout 성공

* Docker build 성공

* Docker Hub Push 성공

* GitHub Webhook 등록 완료

* 코드 push 시 Jenkins 자동 실행 성공

* Docker Hub에 최신 이미지 반영 확인

---

## 자주 발생하는 오류

## 오류 1. Jenkins 접속 불가

### 원인 가능성

* Jenkins 서비스 미실행

* 8080 포트 차단

* 보안그룹 미허용

* 방화벽 문제

### 점검 명령

```
sudo systemctl status jenkins
sudo ss-tulnp |grep8080
sudo ufw status
```

---

## 오류 2. Docker build 시 권한 오류

예:

```
permission denied while trying to connect to the Docker daemon socket
```

### 원인

* `jenkins` 사용자가 docker 그룹에 없음

* 그룹 변경 후 Jenkins 재시작 안 함

### 해결

```
sudo usermod-aG docker jenkins
sudo systemctlrestart jenkins
id jenkins
```

---

## 오류 3. Docker login 실패

예:

```
unauthorized: incorrect username or password
```

### 원인

* Docker Hub 사용자명 오류

* 토큰 오류

* Credential ID 잘못 참조

* Credential 값 오입력

### 해결

* Jenkins Credentials 값 재확인

* Docker Hub 토큰 재생성

* `credentialsId: 'dockerhub-creds'` 오타 확인

---

## 오류 4. Push는 되는데 Docker Hub에서 안 보임

### 원인 가능성

* 잘못된 사용자명 namespace로 Push

* 다른 태그로 Push

* private/public 혼동

### 해결

* Console Output의 repository 이름 확인

* Docker Hub에서 해당 계정 repository 목록 확인

* 이미지 이름 형식 재확인

---

## 오류 5. GitHub Webhook이 동작하지 않음

### 원인 가능성

* Jenkins 주소가 외부에서 접근 불가

* `/github-webhook/` 경로 누락

* Job Trigger 미설정

* GitHub Delivery 실패

### 확인 포인트

* GitHub Webhooks 화면의 Recent Deliveries

* 응답 코드 200 여부

* Jenkins Job Trigger 체크 여부

---

## 오류 6. Checkout 실패

### 원인 가능성

* GitHub 저장소 URL 오타

* main 브랜치 오타

* private 저장소 접근 권한 없음

### 해결

* 저장소 URL 다시 확인

* 브랜치명 확인

* 필요 시 GitHub Credential 등록 후 사용

---

## 실습 후 정리해야 할 핵심 개념

### 1) Jenkins는 설치형 CI 서버다

즉, 직접 설치하고 운영해야 한다.

### 2) CI 파이프라인은 단순 빌드가 아니라 전체 자동화 흐름이다

이번 실습에서는 checkout, build, push까지 연결했다.

### 3) Docker 이미지는 CI 결과물로 매우 중요하다

운영에 반영 가능한 표준 배포 단위 역할을 한다.

### 4) 레지스트리 Push가 되어야 결과물이 다른 환경에서 사용 가능해진다

즉, 빌드 성공과 배포 준비 완료는 다르다.

### 5) Jenkins Credentials는 필수다

인증정보를 Job 스크립트에 하드코딩하면 안 된다.

### 6) GitHub Webhook을 연결하면 Jenkins가 이벤트 기반으로 동작한다

즉, 사람이 수동으로 빌드 버튼을 누르지 않아도 된다.

---

## 실습 결과 요약

이번 실습을 통해 다음을 완료했음.

* Jenkins 설치 및 초기 설정

* Git, Docker 설치

* Jenkins Docker 권한 구성

* Docker Hub Credential 등록

* Jenkins Pipeline Job 생성

* GitHub 저장소 checkout

* Docker 이미지 빌드

* Docker Hub Push

* GitHub Webhook 등록

* 코드 push 시 Jenkins 자동 실행 확인

---