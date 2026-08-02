---
title: "Amazon ECR 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "모범사례기반 AWS 고급아키텍처 설계"]
is_public: true
draft: false
---

# Amazon ECR 실습

# 1. 실습 개요

ECR은 **컨테이너 이미지를 저장하는 AWS의 Docker Registry 서비스**다.

실습은 아래 흐름으로 진행함.

[![](Amazon%20ECR%20%EC%8B%A4%EC%8A%B5/image.png)](Amazon%20ECR%20%EC%8B%A4%EC%8A%B5/image.png)

---

# 2. 실습 환경

## 2.1 준비 사항

실습을 위해 아래 항목이 준비되어 있어야 함.

* AWS 계정

* IAM 권한
  + ECR 생성/조회 권한
  + EC2 접속 권한

* Docker 설치 환경
  + 로컬 PC
  + 또는 Amazon Linux 2023 / Ubuntu EC2

* AWS CLI 설치

* 리전 예시: **ap-northeast-2 (서울)**

---

## 2.2 실습 방식

### 방식 1. 로컬 PC에서 실습

* Docker Desktop 설치

* AWS CLI 설치

* 로컬에서 이미지 생성 후 ECR Push

### 방식 2. EC2에서 실습

* EC2에 Docker 설치

* AWS CLI 설치

* EC2에서 이미지 생성 후 ECR Push

---

# 3. 실습 구성도

```
[EC2 - Docker 설치]
   ├─ Dockerfile 작성
   ├─ 이미지 빌드
   ├─ aws ecr get-login-password
   ├─ docker login
   ├─ docker push
   └─ docker pull

[AWS]
   └─ Amazon ECR Repository
```

---

# 4. 사전 준비

## 4.1 EC2 생성

다음과 같은 EC2 1대를 준비함.

예시

* OS: Amazon Linux 2023

* Instance Type: t3.micro

* Security Group
  + SSH(22) 허용
  + 테스트용 웹 확인 시 8080 허용

---

## 4.2 EC2 접속

```
ssh -i mykey.pem ec2-user@EC2-Public-IP
```

---

# 5. Docker 설치

## 5.1 Amazon Linux 2023에서 Docker 설치

```
sudo dnf update -y
sudo dnf install docker -y
```

---

## 5.2 Docker 서비스 시작

```
sudo systemctl start docker
sudo systemctl enable docker
```

---

## 5.3 현재 사용자에게 Docker 실행 권한 부여

```
sudo usermod -aG docker ec2-user
```

---

## 5.4 Docker 설치 확인

```
docker --version
```

예시 출력

```
Docker version 25.x.x, build ...
```

---

# 6. ECR 리포지토리 생성

## 6.1 콘솔에서 생성

AWS Console → ECR → **Repositories** → **Create repository**

설정 예시

* Repository name: `sample-web`

* Visibility settings: **Private**

* 나머지는 기본값 사용

생성이 완료되면 아래와 같은 URI를 확인할 수 있음.

```
123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/sample-web
```

이 URI는 이후 Docker Tag와 Push에서 사용함.

---

## 6.2 CLI로 생성하는 방법

```
aws ecr create-repository \
  --repository-name sample-web \
  --region ap-northeast-2
```

```
aws ecr-public create-repository \
--repository-name sample-web \
--region ap-northeast-2
```

### 명령어 설명

### `aws ecr create-repository`

* Amazon ECR에 새로운 이미지 저장소를 생성함

### `--repository-name sample-web`

* 저장소 이름을 지정함

* Docker Hub의 repository처럼 이미지가 저장될 논리적 공간임

### `--region ap-northeast-2`

* 서울 리전에 생성하겠다는 의미임

* ECR은 리전 단위 서비스이므로, 생성 리전과 Push/Pull 리전이 같아야 함

---

## 6.3 리포지토리 조회

```
aws ecr describe-repositories
```

---

# 7. 실습용 애플리케이션 작성

## 7.1 작업 디렉터리 생성

```
mkdir ~/ecr-lab
cd ~/ecr-lab
```

---

## 7.2 HTML 파일 작성

```
cat > index <<'EOF'
<h1>Hello ECR</h1>
<p>This container image is stored in Amazon ECR.</p>
EOF
```

### 명령어 설명

### `cat > index <<'EOF'`

* 여러 줄 내용을 한 번에 파일로 저장할 때 사용하는 방식임

* `EOF` 전까지 입력한 문자열이 `index` 파일 내용으로 저장됨

---

## 7.3 Dockerfile 작성

```
cat > Dockerfile <<'EOF'
FROM nginx:latest
COPY index /usr/share/nginx/html/index
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
EOF
```

### Dockerfile 설명

### `FROM nginx:latest`

* 베이스 이미지로 nginx 최신 이미지를 사용함

* 즉, 웹서버 기능은 nginx가 담당함

### `COPY index /usr/share/nginx/html/index`

* 현재 디렉터리에 있는 `index` 파일을 컨테이너 내부 nginx 웹 루트 경로에 복사함

### `EXPOSE 80`

* 컨테이너가 80번 포트를 사용한다는 의미를 문서화한 것임

* 실제 외부 노출은 `docker run -p` 옵션으로 결정됨

---

# 8. Docker 이미지 빌드

## 8.1 이미지 생성

```
docker build -t sample-web:v1 .
```

### 명령어 설명

### `docker build`

* Dockerfile을 기준으로 이미지를 생성함

### `t sample-web:v1`

* 생성할 이미지 이름과 태그를 지정함

* `sample-web`는 이미지 이름

* `v1`은 태그 버전

### `.`

* 현재 디렉터리를 build context로 사용한다는 의미임

* Dockerfile과 index이 현재 디렉터리에 있어야 함

---

## 8.2 이미지 확인

```
docker images
```

예시 출력

```
REPOSITORY   TAG   IMAGE ID       CREATED         SIZE
sample-web   v1    xxxxxxxxxxxx   10 seconds ago  xxxMB
```

---

# 9. ECR 로그인

Docker가 ECR에 Push하려면 먼저 인증을 해야 함.

## 12.1 로그인 명령 실행

```
aws ecr get-login-password  | \
docker login --username AWS --password-stdin 계정ID.dkr.ecr.ap-northeast-2.amazonaws.com
```

### 명령어 상세 설명

### `aws ecr get-login-password`

* AWS가 ECR 인증용 임시 로그인 비밀번호를 생성해줌

* 예전에는 `get-login` 명령을 사용했지만 지금은 `get-login-password` 방식이 표준임

### `|`

* 파이프 기호임

* 앞 명령의 출력 결과를 뒤 명령의 입력값으로 전달함

### `docker login --username AWS --password-stdin ...`

* Docker Registry에 로그인하는 명령임

* ECR은 사용자명을 실제 IAM 사용자명으로 받지 않고 고정값 `AWS`를 사용함

* 비밀번호는 표준 입력(stdin)으로 전달받음

정상 로그인 시 아래처럼 출력됨.

```
Login Succeeded
```

---

# 10. Docker 이미지에 ECR URI 태그 부여

현재 이미지는 `sample-web:v1`이라는 로컬 이름만 가지고 있음.

이를 ECR에 Push하려면 **ECR 형식의 이름으로 다시 태그**해야 함.

## 10.1 태그 변경

```
docker tag sample-web:v1 123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/sample-web:v1
```

### 명령어 설명

### `docker tag`

* 이미지를 복사하는 것이 아니라, **같은 이미지에 새로운 이름표를 붙이는 작업**임

형식

```
docker tag 기존이미지이름 대상이미지이름
```

여기서 대상 이미지 이름은 반드시 아래 구조를 따라야 함.

```
AWS계정ID.dkr.ecr.리전.amazonaws.com/리포지토리명:태그
```

---

## 10.2 태그 확인

```
docker images
```

예시

```
REPOSITORY                                                           TAG   IMAGE ID
sample-web                                                           v1    abcdef123456
123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/sample-web        v1    abcdef123456
```

`IMAGE ID`가 같다면 같은 이미지에 이름만 두 개 붙은 상태임.

---

# 11. ECR에 이미지 Push

## 11.1 Push 실행

```
docker push 123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/sample-web:v1
```

### 명령어 설명

### `docker push`

* 로컬에 있는 이미지를 원격 Docker Registry로 업로드함

* 여기서는 대상 Registry가 Amazon ECR임

Push가 진행되면 레이어 단위로 업로드됨.

이미 업로드된 레이어는 재사용될 수 있음.

---

## 11.2 콘솔에서 Push 결과 확인

AWS Console → ECR → `sample-web` Repository 선택

확인 항목

* Image tag: `v1`

* Image size

* Push time

---

# 12. ECR 이미지 Pull 및 실행

## 12.1 기존 로컬 이미지 삭제(선택)

Pull 테스트를 명확히 하려면 기존 이미지를 삭제한 뒤 진행해도 됨.

```
docker rmi 123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/sample-web:v1
docker rmi sample-web:v1
```

### 명령어 설명

### `docker rmi`

* 로컬 Docker 이미지를 삭제함

* Pull이 실제로 원격 저장소에서 내려받는 동작인지 확인할 때 자주 사용함

---

## 12.2 이미지 Pull

```
docker pull 123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/sample-web:v1
```

### 명령어 설명

### `docker pull`

* 원격 Registry에 있는 이미지를 로컬 환경으로 다운로드함

---

## 12.3 컨테이너 실행

```
docker run -d --name sample-web-container -p 8080:80 123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/sample-web:v1
```

### 명령어 상세 설명

### `docker run`

* 이미지로부터 컨테이너를 생성하고 실행함

### `-d`

* detached mode

* 백그라운드에서 실행함

### `--name sample-web-container`

* 컨테이너 이름을 지정함

### `-p 8080:80`

* 호스트의 8080 포트를 컨테이너의 80 포트와 연결함

* 즉, 브라우저에서 `EC2-IP:8080`으로 접속하면 컨테이너 내부 nginx 80 포트로 연결됨

---

## 12.4 실행 확인

```
docker ps
```

정상 실행 중이면 컨테이너가 표시됨.

---

## 12.5 웹 접속 확인

브라우저 접속

```
http://EC2-Public-IP:8080
```

정상이라면 다음 내용이 보임.

```
Hello ECR
This container image is stored in Amazon ECR.
```

---

# 13. ECR 이미지 목록 확인

## 13.1 CLI 확인

```
aws ecr list-images \
  --repository-name sample-web \
  --region ap-northeast-2
```

예시 출력

```
{
  "imageIds": [
    {
      "imageTag": "v1",
      "imageDigest": "sha256:xxxxxxxx"
    }
  ]
}
```

---

# 14. 태그 버전 변경 실습

실무에서는 `latest`만 쓰지 않고 버전을 나눠 관리하는 경우가 많음.

이번에는 `v2`를 만들어보는 실습을 진행함.

## 14.1 HTML 수정

```
cat > index <<'EOF'
<h1>Hello ECR v2</h1>
<p>This is version 2 image.</p>
EOF
```

---

## 14.2 이미지 재빌드

```
docker build -t sample-web:v2 .
```

---

## 14.3 ECR 태그 부여

```
docker tag sample-web:v2 123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/sample-web:v2
```

---

## 14.4 Push

```
docker push 123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/sample-web:v2
```

---

## 14.5 확인

콘솔에서 `v1`, `v2` 두 개의 태그가 보이는지 확인함.

---

# 15. 실습 후 정리

## 15.1 컨테이너 중지 및 삭제

```
docker stop sample-web-container
docker rm sample-web-container
```

---

## 15.2 로컬 이미지 삭제

```
docker rmi sample-web:v1
docker rmi sample-web:v2
docker rmi 123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/sample-web:v1
docker rmi 123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/sample-web:v2
docker rmi 123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/sample-web:latest
```

---

## 15.3 ECR 리포지토리 삭제

이미지가 남아 있으면 바로 삭제되지 않을 수 있음.

따라서 먼저 이미지를 삭제하거나 force 옵션을 사용함.

```
aws ecr delete-repository \
  --repository-name sample-web \
  --force \
  --region ap-northeast-2
```

### 명령어 설명

### `--force`

* 리포지토리 안의 이미지를 먼저 비우지 않아도 강제로 함께 삭제함

---