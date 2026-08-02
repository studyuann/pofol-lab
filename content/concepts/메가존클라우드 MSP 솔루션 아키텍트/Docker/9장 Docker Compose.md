---
title: "9장 Docker Compose"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Docker"]
is_public: true
draft: false
---

# 9장. Docker Compose

---

## 멀티 컨테이너 서비스 관리

## 9장 학습 목표

* Docker Compose가 **왜 필요한지**를 설명할 수 있다.

* `docker-compose.yml` 파일의 **구조와 문법**을 이해한다.

* 여러 컨테이너(Web, DB 등)를 **하나의 서비스로 묶어 실행**할 수 있다.

* Volume, Network, Environment를 **Compose에서 선언적으로 관리**할 수 있다.

* 단일 컨테이너 운영과 **Compose 기반 운영의 차이**를 설명할 수 있다.

---

## 9.1 Docker Compose가 필요한 이유

### 9.1.1 단일 컨테이너 운영의 한계

지금까지는 다음과 같이 컨테이너를 실행했다.

```
docker run -d --name web -p 8080:80 nginx
docker run -d --name db mysql
```

이 방식의 문제:

* 컨테이너 개수가 늘어날수록 명령어 관리 불가

* 실행 순서 의존성 관리 어려움

* 네트워크/볼륨/환경변수 설정이 분산됨

* **“이 서비스 전체를 실행한다”는 개념이 없음**

---

### 9.1.2 Docker Compose의 역할

Docker Compose는 다음을 가능하게 한다.

* 여러 컨테이너를 **하나의 서비스 스택**으로 정의

* 실행/중지/삭제를 **한 번의 명령**으로 처리

* 설정을 **코드(yaml)** 로 관리 (IaC 개념)

> **“docker run을 코드로 작성한 것이 Docker Compose다.”**

[![](https://media2.dev.to/dynamic/image/width%3D1000%2Cheight%3D420%2Cfit%3Dcover%2Cgravity%3Dauto%2Cformat%3Dauto/https%3A%2F%2Fdev-to-uploads.s3.amazonaws.com%2Fuploads%2Farticles%2F3jdqbz263qx7iufkm63b.png)](https://media2.dev.to/dynamic/image/width%3D1000%2Cheight%3D420%2Cfit%3Dcover%2Cgravity%3Dauto%2Cformat%3Dauto/https%3A%2F%2Fdev-to-uploads.s3.amazonaws.com%2Fuploads%2Farticles%2F3jdqbz263qx7iufkm63b.png)

---

## 9.2 Docker Compose 설치 및 버전 확인

### 9.2.1 Docker Compose v2

현재 Docker Compose는 **Docker CLI에 통합된 v2**가 표준이다.

```
docker compose version
```

* `docker-compose` (하이픈) ❌

* `docker compose` (공백) ⭕

👉 실무/교육에서는 **v2 기준** 사용 권장

---

## 9.3 docker-compose.yml 기본 구조

### 9.3.1 기본 골격

```
services:       # 컨테이너 서비스 정의
  service_name:
    # 서비스 설정

volumes:        # 볼륨 정의 (선택사항)
  volume_name:

networks:       # 네트워크 정의 (선택사항)
  network_name:
```

Compose 파일의 핵심은 **services**다.

---

### 9.3.2 주요 최상위 키

| 키 | 의미 |
| --- | --- |
| services | 컨테이너 정의 |
| volumes | 볼륨 정의 |
| networks | 네트워크 정의 |

---

## 9.4 Service 정의 상세

### 9.4.1 image

```
services:
  web:
    image: nginx:latest
```

* Docker Hub 이미지 사용

* `docker run nginx`와 동일

---

### 9.4.2 container\_name

```
container_name: web01
```

* 컨테이너 이름 고정

* 교육/운영에서는 명확성 위해 사용

* 대규모 운영에서는 충돌 주의

---

### 9.4.3 ports

```
ports:
  - "8080:80"
```

* 호스트:컨테이너 포트 매핑

* 문자열로 작성 권장

---

### 9.4.4 environment

```
environment:
  - APP_ENV=production
```

또는

```
environment:
  APP_ENV: production
```

---

### 9.4.5 volumes

```
volumes:
  - webdata:/usr/share/nginx/html
```

* Docker Volume 연결

* 5장 내용과 동일 개념

---

### 9.4.6 depends\_on

```
depends_on:
  - db
```

* 컨테이너 **실행 순서 보장**

* 서비스 준비 완료 보장은 ❌ (중요)

---

## 9.5 네트워크와 DNS (Compose의 강력한 장점)

### 9.5.1 Compose 네트워크 기본 동작

* Compose는 **프로젝트별 사용자 정의 bridge 네트워크 자동 생성**

* 서비스 이름 = DNS 이름

👉 6장에서 배운 사용자 정의 bridge가 **자동 적용**

---

### 9.5.2 컨테이너 간 통신 예

```
services:
  web:
    image: nginx
  db:
    image: mysql
```

* web → db 접근 시

```
db:3306
```

👉 IP 필요 없음

---

## 9.6 실습: Web + DB 멀티 컨테이너

### 9.6.1 docker-compose.yml 예제

```
services:
  web:
    image: nginx:latest
    ports:
      - "8080:80"
    depends_on:
      - db

  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpass
```

---

### 9.6.2 실행

```
docker compose up -d
```

확인:

```
docker compose ps
docker ps
```

---

### 9.6.3 중지 및 제거

```
docker compose down
```

* 컨테이너 중지 + 삭제

* 네트워크 제거

* 볼륨은 기본 유지

---

## 9.7 Compose 명령어 정리

| 명령 | 의미 |
| --- | --- |
| docker compose up | 서비스 실행 |
| docker compose up -d | 백그라운드 실행 |
| docker compose down | 전체 종료 |
| docker compose ps | 상태 확인 |
| docker compose logs | 로그 확인 |

---

## 9.8 Compose와 docker run 비교

| 항목 | docker run | Docker Compose |
| --- | --- | --- |
| 단일 컨테이너 | ⭕ | ⭕ |
| 멀티 컨테이너 | ❌ | ⭕ |
| 설정 관리 | 분산 | YAML로 통합 |
| 재현성 | 낮음 | 높음 |
| 협업 | 어려움 | 쉬움 |

## 9.9 실습 예제: 간단한 웹 애플리케이션

이 실습에서는 Nginx 웹 서버와 간단한 HTML 페이지로 구성된 웹 애플리케이션을 만들어보겠습니다.

### 9.9.1 프로젝트 구조 생성

```
my-web-app/
├── docker-compose.yml
├── web/
│   └── index.html
└── nginx/
    └── nginx.conf
```

### 9.9.2 HTML 파일 생성

**web/index.html**

```
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Docker Compose 실습</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 50px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .container {
            background: rgba(255,255,255,0.1);
            padding: 40px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🐳 Docker Compose 실습</h1>
        <p>멀티 컨테이너 애플리케이션이 성공적으로 실행되었습니다!</p>
        <h2>✅ 현재 실행 중인 서비스</h2>
        <ul>
            <li>Nginx 웹 서버</li>
            <li>정적 웹 페이지</li>
        </ul>
    </div>
</body>
</html>
```

### 9.9.3 Nginx 설정 파일

**nginx/nginx.conf**

```
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    server {
        listen 80;
        server_name localhost;

        location / {
            root /usr/share/nginx/html;
            index index.html;
        }

        # 에러 페이지 설정
        error_page 500 502 503 504 /50x.html;
        location = /50x.html {
            root /usr/share/nginx/html;
        }
    }
}
```

### 9.9.4 Docker Compose 파일 작성

**docker-compose.yml**

```
services:
  web:
    image: nginx:alpine
    container_name: my-web-server
    ports:
      - "8080:80"
    volumes:
      - ./web:/usr/share/nginx/html
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
    networks:
      - web-network
    restart: unless-stopped

networks:
  web-network:
    driver: bridge
```

### 9.9.5 실습 진행

**1단계: 프로젝트 디렉터리 생성**

```
mkdir my-web-app
cd my-web-app
mkdir web nginx
```

**2단계: 파일 생성**  
위에서 제공한 파일들을 각각 생성한다.

**3단계: 애플리케이션 실행**

```
# 백그라운드에서 실행
docker compose up -d

# 실행 상태 확인
docker compose ps

# 로그 확인
docker compose logs web
```

**4단계: 웹 페이지 확인**  
브라우저에서 `http://localhost:8080`으로 접속하여 페이지 확인

**5단계: 애플리케이션 중지**

```
docker compose down
```

## 9.10 심화 실습: 데이터베이스 포함

### 9.10.1 WordPress + MySQL 환경

**docker-compose.yml**

```
services:
  mysql:
    image: mysql:8.0
    container_name: wordpress-db
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: rootpass123
      MYSQL_DATABASE: wordpress
      MYSQL_USER: wpuser
      MYSQL_PASSWORD: wppass123
    volumes:
      - mysql_data:/var/lib/mysql
    networks:
      - wordpress-network

  wordpress:
    image: wordpress:latest
    container_name: wordpress-site
    restart: unless-stopped
    ports:
      - "8080:80"
    environment:
      WORDPRESS_DB_HOST: mysql:3306
      WORDPRESS_DB_NAME: wordpress
      WORDPRESS_DB_USER: wpuser
      WORDPRESS_DB_PASSWORD: wppass123
    volumes:
      - wordpress_data:/var/www/html
    depends_on:
      - mysql
    networks:
      - wordpress-network

volumes:
  mysql_data:
  wordpress_data:

networks:
  wordpress-network:
    driver: bridge
```

### 9.10.2 실행 및 관리

```
# 실행
docker compose up -d

# 상태 확인
docker compose ps

# MySQL 컨테이너 접속
docker compose exec mysql mysql -u root -p

# WordPress 컨테이너 접속
docker compose exec wordpress bash

# 특정 서비스만 재시작
docker compose restart wordpress

# 볼륨 포함 완전 삭제
docker compose down -v
```

## 9.11 모니터링과 로깅

### 9.11.1 로그 관리

```
# 모든 서비스 로그
docker compose logs

# 특정 서비스 로그
docker compose logs wordpress

# 실시간 로그 확인
docker compose logs -f

# 최근 100줄만 확인
docker compose logs --tail=100
```

### 9.11.2 리소스 모니터링

```
# 컨테이너 리소스 사용량
docker compose top

# 상세 정보 확인
docker compose exec mysql ps aux
```

## 9.12 환경별 설정 관리

### 9.12.1 환경 파일 사용

**.env**

```
# 데이터베이스 설정
DB_ROOT_PASSWORD=rootpass123
DB_NAME=wordpress
DB_USER=wpuser
DB_PASSWORD=wppass123

# 서비스 포트
WEB_PORT=8080
```

**docker-compose.yml에서 환경 변수 사용:**

```
services:
  mysql:
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
      MYSQL_DATABASE: ${DB_NAME}
      MYSQL_USER: ${DB_USER}
      MYSQL_PASSWORD: ${DB_PASSWORD}

  wordpress:
    ports:
      - "${WEB_PORT}:80"
```

### 9.12.2 다중 Compose 파일

**docker-compose.yml (기본)**

```
services:
  web:
    image: nginx:alpine
    ports:
      - "80:80"
```

**docker-compose.dev.yml (개발용)**

```
services:
  web:
    ports:
      - "8080:80"
    volumes:
      - ./src:/usr/share/nginx/html
```

**실행:**

```
# 개발 환경으로 실행
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

## 9.13 문제 해결

### 9.13.1 일반적인 문제들

**포트 충돌:**

```
# 사용 중인 포트 확인
netstat -tulpn | grep :8080

# 다른 포트로 변경
ports:
  - "8081:80"
```

**볼륨 권한 문제:**

```
# 권한 확인
ls -la ./data

# 권한 수정
sudo chown -R $USER:$USER ./data
```

**네트워크 문제:**

```
# 네트워크 정보 확인
docker compose exec web ip addr show

# 연결 테스트
docker compose exec web ping mysql
```