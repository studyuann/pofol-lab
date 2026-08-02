---
title: "Nginx 기반 리버스 프록시 및 로드밸런서 설정"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Docker"]
is_public: true
draft: false
---

# Nginx 기반 리버스 프록시 및 로드밸런서 설정

---

## 📋 목차

1. Nginx 개요

2. 프록시 서버란?

3. 리버스 프록시와 포워드 프록시 개념

4. Nginx 설치 실습 (Ubuntu / Rocky Linux)

5. Nginx 리버스 프록시 설정 실습

6. Nginx 로드밸런서 설정 실습

7. 실습 문제 및 미니 프로젝트

---

## 1. Nginx 개요

* Nginx란?
  + 고성능 웹 서버, 리버스 프록시, 메일 프록시 등 다양한 역할
  + 이벤트 기반 아키텍처로 높은 동시 접속 처리

* 주요 역할
  + 웹 서버
  + 리버스 프록시
  + 로드밸런서
  + 캐시 서버

---

## 2. 프록시 서버란?

* 클라이언트와 서버 사이에서 중계 역할

* IP 은닉, 캐싱, 로드분산 등의 기능 수행

---

## 3. 리버스 프록시 vs 포워드 프록시

|  |  |  |
| --- | --- | --- |
| 항목 | 포워드 프록시 | 리버스 프록시 |
| 위치 | 클라이언트 앞단 | 서버 앞단 |
| 역할 | 인터넷 접근 제한, 캐시 | 백엔드 서버 분산, SSL 종료 |
| 클라이언트 입장 | 서버가 프록시인지 모름 | 프록시가 서버인 척함 |

---

## 4. Nginx 설치 실습

### Ubuntu

```
sudo apt update
sudo apt install nginx -y
sudo systemctl enable nginx
sudo systemctl start nginx
```

### Rocky Linux

```
sudo dnf install epel-release -y
sudo dnf install nginx -y
sudo systemctl enable nginx
sudo systemctl start nginx
```

---

## 5. 리버스 프록시 설정 실습

### 시나리오

* 외부 요청을 포트 80으로 받고 내부의 2개 웹 서버(8081, 8082)로 프록시 처리

### 설정 예시 (`/etc/nginx/conf.d/reverse_proxy.conf`)

```
server {
    listen 80;

    location / {
        proxy_pass http://localhost:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 실습 단계

1. Nginx 설치

2. 백엔드 서버 준비

```
# Rocky 2
dnf install httpd
vi /etc/httpd/conf/httpd.conf
Listen 8081
:wq

systemctl restart httpd
firewall-cmd --add-port=8081/tcp

# Rocky 3
dnf install httpd
vi /etc/httpd/conf/httpd.conf
Listen 8081
:wq

systemctl restart httpd
firewall-cmd --add-port=8082/tcp
```

3. `proxy_pass` 대상 변경해보기

4. 프록시 헤더 확인 (`curl -I`)

---

## 6. 로드밸런서 설정 실습

### 시나리오

* Nginx가 여러 웹 서버에 라운드로빈 방식으로 로드 분산

### 설정 예시 (`/etc/nginx/conf.d/load_balancer.conf`)

```
upstream backend {
    server rocky2-IP주소:8081;
    server rocky3-IP주소:8082;
}

server {
    listen 80;

    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### nginx.conf 파일 수정하기

```
nginx.conf 파일의 server 블록을 주석처리한다.

include /etc/nginx/conf.d/*.conf;  => 이 설정에 의해 load_balancer.conf 파일이 포함됨.
```

### 실습 단계

1. 위 설정으로 로드밸런서 구성

2. 두 개의 백엔드 서버 실행

3. 윈도우 브라우저에서 Rocky1의 웹서버에 여러 번 웹접속을 하여 라운드로빈 확인

4. sticky 세션 및 weight 설정 실습

```
upstream backend {
    server 127.0.0.1:8081 weight=3;
    server 127.0.0.1:8082;
}
```

```
upstream backend {
sticky cookie srv_id expires=1h path=/;
server 192.168.0.101;
server 192.168.0.102;
}
```

---

## 7. 실습 과제

1. 다음 조건에 맞는 리버스 프록시 구성 파일을 작성하시오:
   * 외부 요청 포트: 8080
   * 내부 포트: 9001
   * 헤더 로그 남기기

2. 다음 조건에 맞는 로드밸런서 설정 구성:
   * 서버 1: `localhost:9001` (가중치 2)
   * 서버 2: `localhost:9002` (가중치 1)
   * sticky session 없이 라운드로빈 동작