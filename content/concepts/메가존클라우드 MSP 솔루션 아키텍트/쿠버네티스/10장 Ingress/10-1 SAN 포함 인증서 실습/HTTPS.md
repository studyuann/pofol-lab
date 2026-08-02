---
title: "HTTPS"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "쿠버네티스", "10장 Ingress", "10-1 SAN 포함 인증서 실습"]
is_public: true
draft: false
---

# HTTPS

[[SSL-TLS\_HTTPS.pdf]]

```
암호화 통신 :  암호 알고리즘
                        대칭키 : DES, 3DES, AES     => 암복호화시 동일한 키 사용 
                                                                  사용자 데이터 암복호화에 사용됨.
                                                                  키 교환이 어려움.           

                        공개키 : RSA,  DSA, EC2     => 암복호화에 사용되는 키가 다름.
                                                                 (공개키, 개인키) 
                                                                 속도가 느려서 인증에 사용됨.
                                                                 키 교환 불필요.

인터넷상에서 암호화 통신 :  상대방 인증에는 공개키 방식을 사용하고 데이터 통신에는
                                      대칭키 방식 사용

 브라우저와 웹서버간 통신시 클라이언트가 웹서버에게 공개키를 요청하고 웹서버가  
 보내준 공개키를 이용해서 세션키(대칭키)를 암호화해서 전송하면 서버는 자신의 개인키로
 암호데이터를 복호화해서 세션키를 얻게 됨.   클라이언트와 웹서버간에 동일한 세션키를
 갖게 되므로 이후 통신은 세션키를 통해 암호화 통신이 가능함. 이때 사용되는 프로토콜이
 SSL/TLS 임.(SSL 사용되다가 TLS로 개선됨.)

HTTPS :  서버의 공개키가 맞는 공개키인지 확인하기위해 인증기관에서 발행한 인증서를
            이용하는 절차를 정해놓은 프로토콜
```

인증서와 SSL/TLS를 이용하여 브라우저와 웹서버간에 암호화 통신을 함.

1. 키 생성  
   #openssl genrsa -des3 -out example.com.key 2048 => 키크기 2048비트의 공개키와 개인키 생성. passphrase로 키 보호

2. CSR(Certificate Signing Request) 생성 ⇒ Self Signed Certificate 생성시 불필요  
   => 인증서에 사인을 요청하는 CSR 생성하여 CA에 전송  
   #openssl req -new -key example.com.key -out example.com.csr

3. Self Signed Certificate 생성  
   => 외부의 공인 CA를 이용하지 않고 내부의 서버를 이용하여 인증서를 발급하고자 하는 경우  
   openssl req -new -x509 -nodes -sha256 -days 365 -key example.com.key -out example.com.crt

* Apache 웹서버에 인증서 적용하기

```
yum install httpd
yum install openssl
yum install mod_ssl   => Apache에서 사용할 SSL 모듈 설치

/etc/httpd/conf.d/ssl.conf 파일에 서버 설정과 인증서,개인키 파일 지정
```

* nginx에 ssl 적용하기

```
/etc/nginx/nginx.conf 파일에서 ssl 설정부분 주석 제거

server {
    listen       443 ssl http2 default_server;
    listen       [::]:443 ssl http2 default_server;
    server_name  www.cloudai.com;
    root         /usr/share/nginx/html;

    ssl_certificate "/etc/nginx/pki/cloudai.com.crt";
    ssl_certificate_key "/etc/nginx/pki/cloudai.com.key";
    ssl_session_cache shared:SSL:1m;
    ssl_session_timeout  10m;
    ssl_ciphers PROFILE=SYSTEM;
    ssl_prefer_server_ciphers on;
    ssl_password_file       "/etc/nginx/pki/ssl.pass";

    # Load configuration files for the default server block.
    include /etc/nginx/default.d/*.conf;

    location / {
    }

    error_page 404 /404.html;
        location = /40x.html {
    }

    error_page 500 502 503 504 /50x.html;
        location = /50x.html {
    }
}
```

```
ssl_certificate에 인증서와 ssl_certificate_key에 개인키파일을 지정.

ssl passphrase 설정 :  다음과 같이 임의의 파일에 패스워드를 입력하고 ssl_password_file 설정

ssl_password_file       "/etc/nginx/pki/ssl.pass"; 

nginx.conf파일을 저장하고 systemctl restart nginx  실행
```