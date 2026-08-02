---
title: "실습 4 AWS 서비스만을 이용한 CI CD 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "DevOps 환경에서의 CI CD"]
is_public: true
draft: false
---

# 실습 4. AWS 서비스만을 이용한 CI/CD 실습

## CodeCommit + CodeBuild + CodeDeploy + CodePipeline + EC2

---

# 1. 실습 개요

이번 실습에서는 AWS 서비스만 사용해서 애플리케이션 소스 변경부터 EC2 배포까지 자동화하는 CI/CD 파이프라인을 구성함.

구성 흐름은 다음과 같음.

```
개발자
  ↓
CodeCommit 에 소스 push
  ↓
CodePipeline 이 변경 감지
  ↓
CodeBuild 가 빌드 수행
  ↓
CodeDeploy 가 EC2 에 배포
  ↓
EC2 웹서버 반영
```

즉, 개발자가 소스를 직접 서버에 복사하는 방식이 아니라

**Git 저장소에 push만 하면 자동으로 빌드와 배포가 수행되는 구조**를 만드는 실습임.

---

# 2. 실습 목표

이 실습을 통해 다음 내용을 확인함.

* CodeCommit 저장소 생성 방법

* Git을 이용한 소스 업로드 방법

* CodeBuild로 빌드 자동화하는 방법

* CodeDeploy로 EC2 배포 자동화하는 방법

* CodePipeline으로 전체 단계를 연결하는 방법

* 소스 수정 후 자동 재배포 확인 방법

---

# 3. 실습 구성

## 3.1 사용 서비스

* Amazon EC2

* IAM

* AWS CodeCommit

* AWS CodeBuild

* AWS CodeDeploy

* AWS CodePipeline

* Amazon S3

* CloudWatch Logs

---

## 3.2 실습 대상 애플리케이션

이번 실습에서는 복잡한 프로그램 대신 **정적 HTML 웹페이지**를 사용함.

* CI/CD 흐름 자체를 이해하기 쉬움

* 빌드 결과와 배포 결과를 바로 눈으로 확인 가능함

* 불필요한 프레임워크 설정 없이 핵심 서비스에 집중 가능함

---

## 3.3 전체 아키텍처

```
사용자 브라우저
   ↓
EC2 (Nginx)
   ↑
CodeDeploy
   ↑
CodePipeline
   ├─ Source  : CodeCommit
   ├─ Build   : CodeBuild
   └─ Deploy  : CodeDeploy
```

---

# 4. 사전 준비

## 4.1 리전

실습 리전 예시

```
ap-northeast-2 (서울)
```

---

## 4.2 로컬 환경 준비

* Git

* AWS CLI

* 텍스트 편집기(VS Code 등)

---

## 4.3 실습 리소스 목록

* EC2 인스턴스 1대

* CodeCommit Repository 1개

* CodeBuild Project 1개

* CodeDeploy Application 1개

* CodeDeploy Deployment Group 1개

* CodePipeline Pipeline 1개

* S3 Artifact Bucket 1개

* IAM Role 여러 개

---

# 5. 실습 순서

전체 순서는 아래와 같음.

```
1. EC2 생성
2. EC2에 nginx 설치
3. EC2에 CodeDeploy Agent 설치
4. CodeCommit 저장소 생성
5. 로컬에 프로젝트 파일 작성
6. Git으로 CodeCommit에 push
7. CodeDeploy Application / Deployment Group 생성
8. CodeBuild Project 생성
9. CodePipeline 생성
10. 변경 사항 push
11. 자동 빌드 / 자동 배포 확인
```

---

# 6. EC2 생성

## 6.1 EC2 인스턴스 생성

이름 예시

```
이니셜-cicd-web-ec2
```

운영체제

```
Amazon Linux 2023
```

인스턴스 타입

```
t3.micro
```

보안 그룹 인바운드 규칙

```
SSH   TCP 22   내 IP
HTTP  TCP 80   0.0.0.0/0
```

설명

* 22번 포트는 SSH 접속용임

* 80번 포트는 웹페이지 확인용임

* 실습에서는 HTTP로 충분함

---

## 6.2 EC2 IAM Role 연결

EC2에 연결할 IAM Role 예시

```
EC2CodeDeployRole
```

다음 정책을 포함.

* AmazonSSMManagedInstanceCore

* AmazonS3ReadOnlyAccess

실제로는 CodeDeploy Agent 동작에 필요한 최소 권한만 부여하는 것이 더 좋음.

---

## 6.3 태그 추가

EC2에 다음 태그를 추가함.

```
Key   : Deploy
Value : 이니셜-Web
```

이 태그는 나중에 CodeDeploy Deployment Group에서 배포 대상을 식별할 때 사용함.

---

# 7. EC2 초기 설정

## 7.1 SSH 접속

```
ssh-i mykey.pem ec2-user@EC2_PUBLIC_IP
```

---

## 7.2 시스템 업데이트

```
sudo dnf update -y
```

---

# 8. Nginx 설치 및 실행

## 8.1 nginx 설치

```
sudo dnf install nginx -y
```

---

## 8.2 nginx 서비스 시작

```
sudo systemctl enable nginx
sudo systemctlstart nginx
```

---

## 8.3 웹서버 확인

브라우저에서 접속

```
http://EC2_PUBLIC_IP
```

nginx 기본 페이지가 보이면 정상임.

---

# 9. CodeDeploy Agent 설치

CodeDeploy는 EC2에 파일을 복사하고 스크립트를 실행하기 위해

대상 서버에 **CodeDeploy Agent**가 필요함.

## 9.1 Ruby 설치

```
sudo dnf install ruby -y
```

* CodeDeploy 설치 스크립트 실행에 Ruby가 사용됨

---

## 9.2 설치 파일 다운로드

```
wget https://aws-codedeploy-ap-northeast-2.s3.ap-northeast-2.amazonaws.com/latest/install
chmod +x install
```

---

## 9.3 Agent 설치

```
sudo ./install auto
```

* `auto` 옵션은 자동 설치 방식임

* 설치가 완료되면 서비스가 등록됨

---

## 9.4 상태 확인

```
sudo systemctl status codedeploy-agent
```

정상이라면 `active (running)` 상태가 보여야 함.

추가로 부팅 후 자동 시작도 확인함.

```
sudo systemctl enable codedeploy-agent
```

---

# 10. Artifact 저장용 S3 버킷 생성

CodePipeline과 CodeBuild는 중간 산출물을 저장할 위치가 필요함.

버킷 이름 예시

```
이니셜-cicd-artifact-계정식별자
aws s3 mb s3://버킷-이름
```

* CodeCommit이 소스 저장소 역할을 하기 때문에 S3는 **소스 저장용이 아니라 아티팩트 저장용**으로 사용함

* 아티팩트는 빌드 결과물, 배포 패키지 등을 의미함

---

# 11. CodeCommit 저장소 생성

## 11.1 Repository 생성

CodeCommit 콘솔에서 생성

이름 예시

```
이니셜-cicd-repo

aws codecommit create-repository --repository-name 저장소-이름
```

* 이 저장소가 Git 원격 저장소 역할을 함

* 로컬에서 작업한 파일을 여기에 push함

---

## 11.2 접근 방식

HTTPS + Git credentials 또는 HTTPS + credential helper 방식 사용 가능함.

**AWS 자격증명**을 사용하는 것이 편함.

---

# 12. 로컬 프로젝트 생성

이번 실습에서는 아래 구조로 프로젝트를 만듦.

```
cicd-demo/
├─ index
├─ buildspec.yml
├─ appspec.yml
└─ scripts/
   ├─ install_dependencies.sh
   ├─ start_server.sh
   └─ validate_service.sh
```

---

# 13. 파일 작성

## 13.1 index

```
<!DOCTYPE html>
<htmllang="ko">
<head>
<metacharset="UTF-8">
<title>AWS Native CI/CD Demo</title>
</head>
<body>
<h1>AWS Native CI/CD Demo - Version 1</h1>
<p>This page was deployed from CodeCommit through CodePipeline.</p>
</body>
</html>
```

* 웹 브라우저에서 바로 결과를 확인할 수 있는 테스트 파일임

* 나중에 `Version 2`로 수정해서 재배포를 확인할 예정임

---

## 13.2 buildspec.yml

```
version: 0.2

phases:
  install:
    commands:
      - echo "Install phase started"
  build:
    commands:
      - echo "Build phase started"
      - mkdir -p output
      - cp -r index appspec.yml scripts output/
  post_build:
    commands:
      - echo "Build phase completed"

artifacts:
  files:
    - '**/*'
  base-directory: output
```

설명

### `version: 0.2`

CodeBuild가 해석하는 빌드 스펙 버전임.

### `phases`

빌드 과정을 단계별로 정의함.

* `install` : 패키지 설치, 환경 준비

* `build` : 실제 빌드, 파일 복사, 압축 등 수행

* `post_build` : 빌드 후 후처리 수행

### `mkdir -p output`

* `output` 디렉터리를 생성함

* `p`는 디렉터리가 이미 있어도 오류 없이 넘어감

### `cp -r index appspec.yml scripts output/`

* 배포에 필요한 파일을 `output` 폴더로 복사함

* `r` 옵션은 디렉터리 복사 시 필요함

* 여기서는 `scripts` 폴더를 함께 복사해야 하므로 `r` 사용함

### `artifacts`

다음 단계로 넘길 결과물을 정의함.

### `files: '**/*'`

* `output` 디렉터리 안의 모든 파일을 아티팩트에 포함함

### `base-directory: output`

* 결과물의 기준 디렉터리를 `output`으로 설정함

즉, 최종적으로 CodeDeploy는 `output` 내부 파일을 받아서 배포하게 됨.

---

## 13.3 appspec.yml

```
version: 0.0
os: linux
files:
  - source: /
    destination: /usr/share/nginx/html # Nginx 기본 경로
permissions:
  - object: /usr/share/nginx/html
    pattern: "**" 
    owner: nginx
    group: nginx
    mode: 755
hooks:
  BeforeInstall:
    - location: scripts/install_dependencies.sh
      timeout: 300
      runas: root
  ApplicationStart:
    - location: scripts/start_server.sh
      timeout: 300
      runas: root
  ValidateService:
    - location: scripts/validate_service.sh
      timeout: 300
      runas: root
```

설명

### `version: 0.0`

EC2/온프레미스 배포용 AppSpec 버전임.

### `os: linux`

대상 서버 운영체제가 Linux임을 지정함.

### `files`

배포 파일 복사 규칙임.

* `source: /`
  + 배포 패키지 전체를 의미함

* `destination: /var/www/html`
  + nginx 기본 웹 문서 루트 경로임

즉, 배포 패키지의 파일들을 `/var/www/html` 아래로 복사함.

### `permissions`

배포된 파일의 권한과 소유자를 지정함.

* `owner: nginx`

* `group: nginx`

* `mode: 755`

웹서버가 파일을 읽을 수 있도록 맞춰줌.

### `hooks`

배포 라이프사이클별 실행 스크립트 정의함.

* `BeforeInstall`
  + 설치 전 처리

* `ApplicationStart`
  + 애플리케이션 시작 또는 재시작

* `ValidateService`
  + 정상 동작 검증

---

## 13.4 scripts/install\_dependencies.sh

```
#!/bin/bash
set -e
echo "=== BeforeInstall 시작 ==="
dnf install nginx -y || true
mkdir -p /usr/share/nginx/html
# 중요: 기존에 있던 기본 Welcome 페이지를 지워야 우리 파일이 보입니다.
rm -f /usr/share/nginx/html/index
chown -R nginx:nginx /usr/share/nginx/html
```

* set -e : 스크립트 실행 중 오류 발생시 즉시 중단.

---

## 13.5 scripts/start\_server.sh

```
#!/bin/bash
set -e

echo "=== ApplicationStart started ==="

systemctl enable nginx
systemctl restart nginx

echo "=== ApplicationStart completed ==="
```

설명

### `systemctl enable nginx`

부팅 후 자동 시작되게 등록함.

### `systemctl restart nginx`

nginx 재시작함.

여기서 `restart`를 사용한 이유는 다음과 같음.

* 최초 배포 시 시작 가능

* 이후 재배포 시 최신 파일 기준으로 다시 반영 가능

즉, `start`보다 재배포 환경에서 더 유연하게 사용 가능함.

---

## 13.6 scripts/validate\_service.sh

```
#!/bin/bash
set-e

echo "=== ValidateService started ==="

curl -f http://localhost/index

echo "=== ValidateService completed ==="
```

설명

### `curl -f`

* `curl`은 HTTP 요청 테스트 명령어임

* `f` 옵션은 HTTP 오류 발생 시 실패 코드 반환함

즉, 웹서버가 정상 동작하지 않으면 이 스크립트가 실패하고 CodeDeploy도 배포 실패로 판단함.

단순 파일 복사만 끝났다고 배포 성공으로 보면 안 되고, 실제 서비스 가능 상태까지 확인해야 하기 때문임.

---

## 13.7 실행 권한 부여

```
chmod +x scripts/*.sh
```

---

# 14. Git 초기화 및 CodeCommit에 업로드

## 14.1 로컬 저장소 초기화

```
cd cicd-demo
git init
```

* `git init`은 현재 디렉터리를 Git 로컬 저장소로 초기화함

---

## 14.2 사용자 정보 설정

```
git config user.name"your-name"
git config user.email"your-email@example.com"
```

* 커밋 작성자 정보를 설정함

* 저장소별 또는 전역으로 설정 가능함. 생략해도 됨.

---

## 14.3 파일 추가

```
git add .
```

* 현재 폴더의 모든 파일을 staging area에 추가함

* 커밋 대상 파일로 등록하는 과정임

---

## 14.4 첫 커밋 생성

```
git commit -m "Initial commit"
```

---

## 14.5 원격 저장소 등록

```
git remote add origin codecommit::ap-northeast-2://kyt-cicd-repo
```

설명

* `origin`은 원격 저장소의 별칭임

* 뒤 URL은 CodeCommit 저장소 주소임. aws 자격증명을 이용해서 인증하기 위한 방식의 주소. 별도의 인증이 필요하지 않음.

---

## 14.6 기본 브랜치 지정

```
git branch -M main
```

설명

* 현재 브랜치 이름을 `main`으로 변경함

* `M`은 강제 이름 변경 옵션임

---

## 14.7 CodeCommit으로 push

```
git push -u origin main
```

설명

### `push`

로컬 커밋을 원격 저장소에 업로드함.

### `-u`

현재 브랜치와 원격 브랜치를 추적 관계로 설정함.

즉, 이후부터는 `git push`만 입력해도 자동으로 `origin main`에 반영됨.

---

# 15. CodeDeploy 구성

## 15.1 CodeDeploy Application 생성

이름 예시

```
이니셜-cicd-app
```

컴퓨팅 플랫폼

```
EC2
```

---

## 15.2 CodeDeploy 서비스 역할 생성

이름 예시

```
CodeDeployServiceRole
```

이 역할은 CodeDeploy가 EC2 대상을 찾아 배포 작업을 수행할 때 사용함.

---

## 15.3 Deployment Group 생성

이름 예시

```
이니셜-cicd-dg
```

환경 구성

```
Amazon EC2 instances
```

대상 선택 방식

```
태그 기반 선택
```

태그 조건

```
Deploy = 이니셜-Web
```

* EC2에 미리 붙여둔 태그와 일치하는 인스턴스에만 배포함

* 수동으로 인스턴스를 지정하는 것보다 운영 관점에서 더 유연함

* 나중에 같은 태그를 가진 EC2가 늘어나면 동일한 배포 그룹으로 확장 가능함

---

# 16. CodeBuild 구성

## 16.1 CodeBuild Project 생성

이름 예시

```
이니셜-cicd-build
```

소스 공급자

```
CodeCommit
```

설명

* CodeBuild가 직접 저장소에서 받는 것이 아니라  
  CodeCommit이 소스를 전달해주는 구조임

환경

```
Managed image
Amazon Linux
```

Buildspec

```
Use a buildspec file
```

서비스 역할

```
CodeBuildServiceRole

"s3:GetObject"  => artifact에 추
```

아티팩트

```
S3
```

설명

* 빌드 결과물은 CodePipeline을 통해 다음 단계로 전달됨

* 별도 zip 업로드 위치를 직접 지정하지 않아도 됨

---

# 17. CodePipeline 구성

## 17.1 파이프라인 생성

이름 예시

```
이니셜-cicd-pipeline
```

서비스 역할

```
CodePipelineServiceRole

기본 권한 외에 codedeploy:GetApplicationRevision, codedeploy:GetDeploymentConfig 권한 추가
```

아티팩트 저장소

```
기존 S3 버킷 선택
이니셜-cicd-artifact-계정식별자
```

---

## 17.2 Source 단계

소스 공급자

```
AWS CodeCommit
```

Repository name

```
my-cicd-repo
```

Branch name

```
main
```

변경 감지 방식

```
CloudWatch Events / EventBridge 기반 변경 감지
```

설명

* `main` 브랜치에 push가 발생하면 파이프라인이 자동 실행됨

---

## 17.3 Build 단계

빌드 공급자

```
AWS CodeBuild
```

Project name

```
my-cicd-build
```

입력 아티팩트 이름은 기본값으로 두어도 무방함.

---

## 17.4 Deploy 단계

배포 공급자

```
AWS CodeDeploy
```

Application name

```
my-cicd-app
```

Deployment group

```
my-cicd-dg
```

설명

* Build 단계 결과물을 CodeDeploy가 받아 EC2에 배포함

---

# 18. 첫 배포 확인

CodePipeline 생성 후

이미 CodeCommit에 소스가 올라가 있다면 첫 실행이 가능함.

확인 순서

```
1. Source 성공
2. Build 성공
3. Deploy 성공
```

브라우저에서 확인

```
http://EC2_PUBLIC_IP
```

정상이라면 아래 문구가 보임.

```
AWS Native CI/CD Demo - Version 1
```

---

# 19. 변경 후 자동 배포 실습

## 19.1 index 수정

기존 문구를 아래처럼 수정함.

```
<!DOCTYPE html>
<htmllang="ko">
<head>
<metacharset="UTF-8">
<title>AWS Native CI/CD Demo</title>
</head>
<body>
<h1>AWS Native CI/CD Demo - Version 2</h1>
<p>This page was redeployed automatically after git push.</p>
</body>
</html>
```

---

## 19.2 변경 사항 커밋

```
git add .
git commit -m "Update version to 2"
```

* 수정 파일을 staging area에 올리고

* 새 커밋을 생성함

---

## 19.3 CodeCommit에 다시 push

```
git push
```

---

## 19.4 자동 실행 확인

확인 항목

* CodePipeline이 자동 실행되었는지 확인

* CodeBuild가 다시 수행되었는지 확인

* CodeDeploy가 다시 수행되었는지 확인

* 브라우저 새로고침 시 `Version 2`가 보이는지 확인

---

# 20. 동작 원리 정리

이번 실습 전체 동작은 다음과 같음.

## 20.1 Source 단계

CodeCommit `main` 브랜치에 코드 변경이 push됨.

## 20.2 Build 단계

CodeBuild가 `buildspec.yml`을 읽고

배포에 필요한 파일만 정리해서 아티팩트 생성함.

## 20.3 Deploy 단계

CodeDeploy가 `appspec.yml`을 읽고

EC2의 `/var/www/html`로 파일을 복사함.

## 20.4 Hook 단계

CodeDeploy가 훅 스크립트를 순서대로 실행함.

* BeforeInstall

* ApplicationStart

* ValidateService

## 20.5 최종 결과

브라우저에서 최신 배포 결과가 확인됨.

---

# 21. 자주 발생하는 오류와 점검 방법

## 21.1 CodeDeploy에서 대상 EC2를 찾지 못함

원인

* EC2 태그가 Deployment Group 조건과 다름

확인

* EC2 태그가 `Deploy=Web`인지 확인

* Deployment Group 태그 조건 확인

---

## 21.2 appspec.yml 오류

원인

* 파일 이름 오타

* YAML 들여쓰기 오류

* 최상위 경로에 appspec.yml이 없음

확인 포인트

```
저장소 루트
├─ index
├─ buildspec.yml
├─ appspec.yml
└─ scripts/
```

`appspec.yml`은 루트에 있어야 함.

---

## 21.3 스크립트 실행 실패

원인

* 실행 권한 없음

* bash 문법 오류

* 경로 오타

확인

```
chmod +x scripts/*.sh
```

추가로 로컬에서 직접 실행 테스트해보는 것도 좋음.

---

## 21.4 Build 단계 실패

원인

* buildspec.yml 오타

* 복사 대상 파일 누락

* YAML 문법 오류

확인

* CodeBuild 로그 확인

* `cp -r` 경로 확인

* `output` 폴더 구조 확인

---

## 21.5 ValidateService 실패

원인

* nginx 미실행

* `/var/www/html/index` 누락

* localhost HTTP 응답 실패

EC2에서 직접 점검

```
sudo systemctl status nginx
curl -I http://localhost
ls -al /var/www/html
```

---

## 21.6 Git push 인증 실패

원인

* IAM Git 자격 증명 설정 누락

* HTTPS 인증 정보 오류

* 올바른 CodeCommit URL 미사용

확인

* CodeCommit clone URL 재확인

* IAM 사용자 Git credentials 확인

* Git credential helper 사용 여부 확인

---

# 22. 정리

## 22.1 Git 저장소와 배포 서버는 다름

CodeCommit은 소스 저장소임.

실제 서비스는 EC2에서 실행됨.

즉,

* CodeCommit은 코드 보관

* CodeBuild는 빌드 수행

* CodeDeploy는 배포 수행

* EC2는 서비스 실행

이 역할 분리가 핵심임.

---

## 22.2 CodePipeline은 전체 오케스트레이션 도구임

CodePipeline은 직접 코드를 빌드하거나 배포하는 서비스가 아님.

각 단계를 연결하고 흐름을 제어하는 서비스임.

즉,

* Source는 어디서 가져올지

* Build는 누가 처리할지

* Deploy는 어디에 배포할지

이 과정을 연결해주는 역할을 함.

---

## 22.3 CodeDeploy는 단순 복사 도구가 아님

CodeDeploy는 단순 파일 복사만 하는 것이 아니라

라이프사이클 이벤트에 따라 스크립트를 실행할 수 있음.

그래서 다음과 같은 자동화가 가능함.

* 패키지 설치

* 웹서버 재시작

* 환경파일 교체

* 서비스 검증

---

## 22.4 배포 성공은 파일 복사 완료가 아니라 서비스 정상 동작까지 포함해야 함

그래서 `ValidateService` 훅이 중요함.

단순히 `/var/www/html`에 파일이 들어갔다고 끝이 아니라

실제로 `curl http://localhost`가 성공해야 진짜 배포 성공이라고 볼 수 있음.

---