---
title: "AWS Client VPN 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 아키텍처 설계(ARC)"]
is_public: true
draft: false
---

# AWS Client VPN 실습

## Easy-RSA를 이용한 인증서 생성과 Client VPN 구성

### Ubuntu / Windows 기준

---

# 1. 실습 목표

본 실습에서는 **Easy-RSA를 이용해 CA 인증서, 서버 인증서, 클라이언트 인증서**를 생성하고,

이를 이용해 **AWS Client VPN Endpoint**를 구성한 뒤,

외부 사용자 PC에서 **AWS VPC 내부 Private Subnet 자원에 안전하게 접속**하는 환경을 구성한다.

실습을 통해 다음 내용을 이해한다.

* Easy-RSA를 이용한 인증서 생성 방법

* CA 인증서, 서버 인증서, 클라이언트 인증서의 역할

* AWS Certificate Manager(ACM)로 인증서를 가져오는 방법

* AWS Client VPN Endpoint 생성 방법

* Target Network Association의 의미

* Authorization Rule의 의미

* `.ovpn` 구성 파일 수정 방법

* AWS VPN Client를 이용한 접속 방법

* VPN 연결 후 Private EC2와 통신 확인 방법

---

# 2. 실습 구성 개요

AWS Client VPN은 사용자의 PC가 인터넷을 통해 AWS VPC 내부 네트워크에 접속할 수 있도록 해주는

AWS의 관리형 원격 접속 VPN 서비스다.

구조는 다음과 같다.

```
사용자 PC
   │
   │ AWS VPN Client
   │
Internet
   │
AWS Client VPN Endpoint
   │
Target Network Association
   │
VPC Subnet
   │
Private Subnet EC2
```

실습 흐름은 다음과 같다.

```
1. Easy-RSA 설치
2. PKI 초기화
3. CA 인증서 생성
4. 서버 인증서 생성
5. 클라이언트 인증서 생성
6. ACM에 서버 인증서 등록
7. Client VPN Endpoint 생성
8. 대상 네트워크 연결
9. 권한부여 규칙 생성
10. 클라이언트 구성 파일 다운로드
11. 클라이언트 인증서와 키를 .ovpn 파일에 삽입
12. AWS VPN Client로 연결
13. Private EC2 통신 확인
```

---

# 3. 사전 준비

실습 전에 다음 환경이 준비되어 있어야 한다.

* AWS 계정

* VPC 1개

* Private Subnet에 배치된 EC2 인스턴스 1대 이상

* VPC 내부 IP를 가진 테스트 대상 서버

* AWS Console 접속 가능 환경

* Ubuntu 또는 Windows PC

* 관리자 권한 계정

* 텍스트 편집기
  + Ubuntu: vim, nano, code 중 하나
  + Windows: VS Code, Notepad++ 권장

---

# 4. 핵심 개념 이해

## 4.1 왜 인증서가 필요한가

AWS Client VPN에서 **Mutual Authentication**을 사용할 경우

서버와 클라이언트가 서로를 인증해야 한다.

여기서 필요한 것이 인증서다.

| 인증서 | 역할 |
| --- | --- |
| CA 인증서 | 전체 인증서 체계의 신뢰 기준 |
| 서버 인증서 | Client VPN 서버가 정상적인 서버임을 증명 |
| 클라이언트 인증서 | 접속 사용자가 허가된 사용자임을 증명 |

즉,

서버는 자신의 서버 인증서를 제시하고,

클라이언트는 자신의 클라이언트 인증서를 제시한다.

그리고 둘 다 같은 CA 기준으로 검증된다.

---

## 4.2 Easy-RSA란 무엇인가

Easy-RSA는 OpenVPN 환경에서 자주 사용하는 **간단한 PKI 관리 도구**다.

OpenSSL을 직접 길게 다루지 않고도 다음 작업을 쉽게 수행할 수 있다.

* PKI 초기화

* CA 생성

* 서버 인증서 생성

* 클라이언트 인증서 생성

* 인증서 서명

즉, 인증서 실습을 할 때 가장 간단하게 시작하기 좋은 도구다.

---

# 5. Ubuntu에서 Easy-RSA 설치 및 인증서 생성

---

## 5.1 패키지 설치

Ubuntu에서 먼저 패키지를 설치한다.

```
sudo apt-get update
sudo apt-get install easy-rsa-y
```

### 명령 설명

### `sudo apt-get update`

패키지 저장소 목록을 최신 상태로 갱신한다.

### `sudo apt-get install easy-rsa -y`

Easy-RSA 패키지를 설치한다.

---

## 5.2 작업 디렉터리 생성

Ubuntu에서는 Easy-RSA 관련 파일을 작업용 디렉터리로 복사해서 사용하는 방식이 일반적이다.

```
sudomkdir-p /etc/openvpn/easy-rsa
sudo cp-r /usr/share/easy-rsa/* /etc/openvpn/easy-rsa/
cd /etc/openvpn/easy-rsa
```

### 명령 설명

### `mkdir -p /etc/openvpn/easy-rsa`

작업 디렉터리를 생성한다.

### `cp -r /usr/share/easy-rsa/* /etc/openvpn/easy-rsa/`

설치된 Easy-RSA 기본 파일들을 작업 디렉터리로 복사한다.

### `cd /etc/openvpn/easy-rsa`

작업 디렉터리로 이동한다.

---

## 5.3 PKI 초기화

```
./easyrsa init-pki
```

### 설명

이 명령은 인증서와 키를 저장할 PKI 구조를 초기화한다.

실행 후 `pki/` 디렉터리가 생성된다.

PKI는 Public Key Infrastructure의 약자이며,

인증서와 키를 체계적으로 관리하기 위한 디렉터리 구조라고 이해하면 된다.

---

## 5.4 CA 인증서 생성

```
./easyrsa build-ca nopass
```

실행 중 Common Name 입력이 나오면 예를 들어 다음처럼 입력한다.

```
Easy-RSA CA
```

### 설명

이 명령은 다음 두 가지를 만든다.

* CA 인증서

* CA 개인키

생성 결과는 보통 다음 위치에 저장된다.

```
pki/ca.crt
pki/private/ca.key
```

여기서 `nopass`는 개인키 암호를 설정하지 않겠다는 의미다.

실습 편의상 많이 사용하지만 운영 환경에서는 보안 정책을 검토해야 한다.

---

## 5.5 클라이언트 인증서 생성

```
./easyrsa build-client-full client1.kyt nopass
```

### 설명

이 명령은 `client1.kyt` 라는 이름의 클라이언트 인증서를 생성한다.

생성 결과

```
pki/issued/client1.kyt.crt
pki/private/client1.kyt.key
```

* `.crt` : 인증서

* `.key` : 개인키

---

## 5.6 서버 인증서 생성

```
./easyrsa build-server-full server1.kyt nopass
```

### 설명

이 명령은 `server1.kyt` 라는 이름의 서버 인증서를 생성한다.

생성 결과

```
pki/issued/server1.kyt.crt
pki/private/server1.kyt.key
```

---

## 5.7 생성 결과 확인

```
pwd
ls
ls pki
ls pki/issued
ls pki/private
cat pki/ca.crt
```

중요 파일은 다음과 같다.

```
pki/ca.crt
pki/private/ca.key
pki/issued/server1.kyt.crt
pki/private/server1.kyt.key
pki/issued/client1.kyt.crt
pki/private/client1.kyt.key
```

---

# 6. Windows에서 Easy-RSA 설치 및 인증서 생성

<https://docs.aws.amazon.com/ko_kr/vpn/latest/clientvpn-admin/client-auth-mutual-enable.html>

### 6.1 Easy-RSA 압축 해제

예시 경로

```
C:\EasyRSA-3.2.4
```

### 6.2 CMD 실행 후 경로 이동

```
cd C:\EasyRSA-3.1.7
```

### 6.3 Easy-RSA 시작 배치 파일 실행

```
.\EasyRSA-Start.bat
```

### 6.4 PKI 초기화

```
easyrsa init-pki
```

### 6.5 CA 생성

```
easyrsa build-ca nopass
```

### 6.6 클라이언트 인증서 생성

```
easyrsa build-client-full client1.kyt nopass
```

### 6.7 서버 인증서 생성

```
easyrsa build-server-full server1.kyt nopass
```

---

# 7. 생성된 파일의 역할 정리

| 파일 | 설명 | 사용 위치 |
| --- | --- | --- |
| `ca.crt` | CA 인증서 | ACM 체인, `.ovpn`의 `<ca>` |
| `ca.key` | CA 개인키 | 외부 제공 금지 |
| `server1.kyt.crt` | 서버 인증서 | ACM 등록 |
| `server1.kyt.key` | 서버 개인키 | ACM 등록 |
| `client1.kyt.crt` | 클라이언트 인증서 | `.ovpn`의 `<cert>` |
| `client1.kyt.key` | 클라이언트 개인키 | `.ovpn`의 `<key>` |

---

# 8. ACM에 서버 인증서 가져오기

AWS Client VPN Endpoint는 AWS 내부에서 서버 인증서를 사용해야 하므로

서버 인증서를 **AWS Certificate Manager(ACM)** 에 등록해야 한다.

---

## 8.1 ACM 이동

AWS Console에서 다음 메뉴로 이동한다.

```
Certificate Manager → Import certificate
```

---

## 8.2 입력 항목

다음 파일 내용을 각각 복사해서 넣는다.

### Certificate body

`server1.kyt.crt`

### Certificate private key

`server1.kyt.key`

### Certificate chain

`ca.crt`

---

## 9.3 파일 내용 확인 예시

```
cat /etc/openvpn/easy-rsa/pki/issued/server1.kyt.crt
cat /etc/openvpn/easy-rsa/pki/private/server1.kyt.key
cat /etc/openvpn/easy-rsa/pki/ca.crt
```

복사한 내용을 ACM 입력창에 붙여 넣고 인증서를 가져온다.

---

# 10. AWS Client VPN Endpoint 생성

---

## 10.1 메뉴 이동

AWS Console에서 다음으로 이동한다.

```
VPC → Client VPN Endpoints → Create Client VPN Endpoint
```

---

## 10.2 주요 설정값

### Name tag

예시

```
lab-client-vpn
```

### Client IPv4 CIDR

예시

```
10.250.0.0/22
```

### 중요 설명

이 CIDR은 **VPN 사용자에게 할당될 가상 IP 대역**이다.

VPC의 서브넷 CIDR이 아니다.

주의할 점은 다음과 같다.

* VPC CIDR과 중복되면 안 됨

* 온프레미스 네트워크와도 중복되지 않는 것이 좋음

* 다른 VPN과도 중복되지 않는 것이 좋음

---

## 10.3 Server certificate ARN

ACM에 등록한 서버 인증서를 선택한다.

---

## 10.4 Authentication options

**Mutual authentication** 을 선택한다.

이 설정은 클라이언트도 인증서를 제출해야 접속 가능하도록 하는 방식이다.

---

## 10.5 Split-tunnel 활성화

분할 터널을 활성화하면

AWS 네트워크로 가는 트래픽만 VPN을 이용하고

일반 인터넷 트래픽은 기존 인터넷 회선을 그대로 사용한다.

즉,

* AWS VPC 목적지 → VPN 경유

* 일반 웹사이트 접속 → 기존 인터넷 사용

실습에서는 활성화하는 것이 편하다.

---

## 10.6 Transport protocol

다음 중 선택한다.

* UDP

* TCP

일반적으로 UDP를 많이 사용한다.

이유는 성능 오버헤드가 적기 때문이다.

---

## 10.7 VPN port

다음 중 선택한다.

* 443

* 1194

실습에서는 보통 1194를 많이 사용한다.

다만 방화벽 환경에 따라 443이 더 유리할 수도 있다.

---

# 11. 대상 네트워크 연결

Client VPN Endpoint를 만들었다고 해서 바로 VPC에 들어갈 수 있는 것은 아니다.

어느 서브넷과 연결할지 지정해야 한다.

이 작업이 **Target Network Association** 이다.

---

## 11.1 설정 위치

```
Client VPN Endpoint 선택
→ Associate target network
```

---

## 11.2 설정 항목

* VPC 선택

* Subnet 선택

* Security Group 선택

---

## 11.3 개념 설명

대상 네트워크 연결은 VPN 사용자가 AWS 내부로 진입할 때 어느 VPC의 어느 서브넷을 기준으로 연결할지 정하는 작업이다.

즉, Endpoint만 만들어서는 길이 열린 것이 아니고, 어느 네트워크로 보낼지를 연결해야 한다.

---

# 12. 권한부여 규칙 생성

대상 네트워크를 연결했더라도 사용자가 어떤 네트워크 대역까지 접근 가능한지는 별도로 허용해야 한다.

이 작업이 **Authorization Rule** 이다.

---

## 12.1 설정 위치

---

## 12.2 예시

VPC CIDR이 `10.10.0.0/16` 이라면 다음처럼 설정할 수 있다.

```
Destination network to enable access : 10.10.0.0/16
Grant access to : Allow access to all users
```

---

## 12.3 개념 정리

* Target Network Association  
  → 어느 VPC / Subnet 쪽으로 연결할지 결정

* Authorization Rule  
  → 어떤 목적지 네트워크에 접근할 수 있을지 허용

이 둘은 서로 다른 역할이다.

---

# 13. 보안 그룹 설정

VPN이 연결되어도 실제 EC2 접속이 안 되는 경우가 많다.

대부분 보안 그룹 문제다.

---

## 13.1 Private EC2 보안 그룹 예시

### SSH 허용

```
Type: SSH
Protocol: TCP
Port: 22
Source: 10.250.0.0/22
```

### Ping 허용

```
Type: All ICMP - IPv4
Source: 10.250.0.0/22
```

### HTTP 허용

```
Type: HTTP
Protocol: TCP
Port: 80
Source: 10.250.0.0/22
```

즉, **VPN 클라이언트 IP 대역(Client CIDR)** 에서 오는 트래픽을 허용해야 한다.

---

# 14. 클라이언트 구성 파일 다운로드

Client VPN Endpoint가 생성되고 상태가 Active가 되면

클라이언트 설정 파일을 다운로드할 수 있다.

---

## 14.1 메뉴 위치

```
Client VPN Endpoint 선택
→ Download client configuration
```

파일 이름 예시

```
downloaded-client-config.ovpn
```

---

# 15. `.ovpn` 파일 구조 이해

다운로드한 파일은 대략 다음과 같은 구조를 가진다.

```
client
dev tun
proto udp
remote cvpn-endpoint-xxxxxxxx.prod.clientvpn.ap-northeast-1.amazonaws.com 1194
remote-random-hostname
resolv-retry infinite
nobind
remote-cert-tls server
cipher AES-256-GCM
verb 3

<ca>
-----BEGIN CERTIFICATE-----
...
-----END CERTIFICATE-----
</ca>

<cert>

</cert>

<key>

</key>

reneg-sec 0
verify-x509-name myserver name
```

여기서 핵심은 다음 세 구간이다.

* `<ca>` : CA 인증서

* `<cert>` : 클라이언트 인증서

* `<key>` : 클라이언트 개인키

---

# 16. `.ovpn` 파일 수정

다운로드한 `.ovpn` 파일에는 `<cert>` 와 `<key>` 가 비어 있는 경우가 많다.

여기에 생성한 클라이언트 인증서와 클라이언트 키를 넣어야 한다.

---

## 16.1 Ubuntu에서 클라이언트 인증서 확인

```
cat /etc/openvpn/easy-rsa/pki/issued/client1.kyt.crt
cat /etc/openvpn/easy-rsa/pki/private/client1.kyt.key
```

## 16.2 Windows에서 클라이언트 인증서 확인

```
cat /c/openvpn/easy-rsa/pki/issued/client1.kyt.crt
cat /c/openvpn/easy-rsa/pki/private/client1.kyt.key
```

---

## 16.3 붙여 넣는 위치

`.ovpn` 파일에서 다음처럼 수정한다.

```
<cert>
-----BEGIN CERTIFICATE-----
클라이언트 인증서 내용
-----END CERTIFICATE-----
</cert>

<key>
-----BEGIN PRIVATE KEY-----
클라이언트 개인키 내용
-----END PRIVATE KEY-----
</key>
```

---

## 16.4 주의사항

* BEGIN / END 줄까지 반드시 포함해야 함

* 줄바꿈이 깨지면 안 됨

* 다른 클라이언트의 인증서와 키를 섞으면 안 됨

* VS Code 같은 편집기를 사용하는 것이 좋음

---

# 17. AWS VPN Client 설치

Windows 환경에서는 AWS VPN Client를 설치해서 접속할 수 있다.

실습 흐름은 다음과 같다.

```
1. AWS VPN Client 설치
2. Profile 추가
3. 수정한 .ovpn 파일 가져오기
4. Connect 클릭
```

---

# 18. VPN 연결 수행

## 18.1 프로파일 추가

AWS VPN Client를 실행한 뒤

수정한 `.ovpn` 파일을 Import 한다.

## 18.2 연결

프로파일을 선택하고 Connect를 실행한다.

정상 연결되면 사용자 PC는

Client CIDR 대역의 가상 IP를 할당받는다.

---

# 19. 연결 확인

---

## 19.1 Windows에서 확인

```
ipconfig
route print
```

VPN 어댑터가 보이고

VPC 네트워크로 가는 경로가 추가되었는지 확인한다.

---

## 19.2 Ubuntu에서 확인

```
ip addr
ip route
```

VPN 인터페이스와 라우팅 경로를 확인한다.

---

## 19.3 Private EC2 Ping 테스트

예를 들어 Private EC2 IP가 `10.10.2.100` 이라면 다음처럼 확인한다.

### Windows

```
ping 10.10.2.100
```

---

## 19.4 SSH 접속 테스트

### 윈도우 또는 Linux 클라이언트

```
ssh ubuntu@10.10.2.100
```

---

>> Certificate Manager에서 인증서 가져오기(서버, 클라이언트)

[![](AWS%20Client%20VPN%20%EC%8B%A4%EC%8A%B5/image.png)](AWS%20Client%20VPN%20%EC%8B%A4%EC%8A%B5/image.png)[![](AWS%20Client%20VPN%20%EC%8B%A4%EC%8A%B5/image%201.png)](AWS%20Client%20VPN%20%EC%8B%A4%EC%8A%B5/image%201.png)

• 클라이언트 VPN 엔드포인트 생성

[![](AWS%20Client%20VPN%20%EC%8B%A4%EC%8A%B5/image%202.png)](AWS%20Client%20VPN%20%EC%8B%A4%EC%8A%B5/image%202.png)[![](AWS%20Client%20VPN%20%EC%8B%A4%EC%8A%B5/image%203.png)](AWS%20Client%20VPN%20%EC%8B%A4%EC%8A%B5/image%203.png)

* 클라이언트 IP CIDR은 임의의 사설주소 입력. 단 현재 연결하려는 VPC와 중복되지 않게 설정

* 상호 인증 사용 선택

[![](AWS%20Client%20VPN%20%EC%8B%A4%EC%8A%B5/image%204.png)](AWS%20Client%20VPN%20%EC%8B%A4%EC%8A%B5/image%204.png)[![](AWS%20Client%20VPN%20%EC%8B%A4%EC%8A%B5/image%205.png)](AWS%20Client%20VPN%20%EC%8B%A4%EC%8A%B5/image%205.png)

* 분할터널 활성화 : VPN을 사용하지 않는 트래픽은 외부와 통신 가능하도록 설정

* 전송프로토콜은 UDP 또는 TCP중에 선택

* VPN포트 443 또는 1194 중에 선택

[![](AWS%20Client%20VPN%20%EC%8B%A4%EC%8A%B5/image%206.png)](AWS%20Client%20VPN%20%EC%8B%A4%EC%8A%B5/image%206.png)

* 대상 네트워크 연결 : 통신하려고 하는 서브넷 연결

* 보안 그룹 : VPN연결시 필요한 포트 및 연결 후 사용할 포트 또는 프로토콜을 규칙에 적용하여 생성하고 연결

* 권한부여규칙 : Client VPN 엔드포인트 연결시 통신할 네트워크 지정.

* Client VPN 엔드포인트가 활성화되기까지 시간이 걸림.

**◆ 클라이언트 구성 다운로드 후 내용 수정하기**

다운로드한 구성파일 : downloaded-client-config.ovpn

client

dev tun

proto udp

remote cvpn-endpoint-0a3e74948a1914dc6.prod.clientvpn.ap-northeast-1.amazonaws.com 1194

remote-random-hostname

resolv-retry infinite

nobind

remote-cert-tls server

cipher AES-256-GCM

verb 3

<ca>

* ----BEGIN CERTIFICATE-----

MIIDSzCCAjOgAwIBAgIUKLVKyhhXvQ/7TmAFr9VRaooSsWAwDQYJKoZIhvcNAQEL

BQAwFjEUMBIGA1UEAwwLRWFzeS1SU0EgQ0EwHhcNMjMxMjI1MTIzNzMyWhcNMzMx

MjIyMTIzNzMyWjAWMRQwEgYDVQQDDAtFYXN5LVJTQSBDQTCCASIwDQYJKoZIhvcN

AQEBBQADggEPADCCAQoCggEBAKpy2kPNMiUUCl/HnlRzL8z3kZB/0KQHa5Rer3w8

ze+EYrFfwbfkmVBawRD5Dk7TtDxX25LAWTDHoc+C1nYzhHqQxVNlq5dPJA5lKW4G

mD+r8NV8sb4uIUTy3JH0Szln7l1zvBUSobHdnlrdBjh3auvtVpbVIGKRPPgYhw3U

yEkaTblApUit6ospuhdNHM3JSEy0U1EE07Kf7/qt7X+2JdpZLiZ18Dz1/gFz3B3U

KZYopPGFWPEPeymSfW2NfO4xZkpN88CM2foahMOvRjA14Kn9+vFjoc13QWEw4Zqg

iMCZJ/lc2yZcH6t15vAHuZ9rgH53/BnPrpEsnXAbZjZYUOcCAwEAAaOBkDCBjTAd

BgNVHQ4EFgQU6NaMKAho6aruo7SO5J0ZLVN7FXYwUQYDVR0jBEowSIAU6NaMKAho

6aruo7SO5J0ZLVN7FXahGqQYMBYxFDASBgNVBAMMC0Vhc3ktUlNBIENBghQotUrK

GFe9D/tOYAWv1VFqihKxYDAMBgNVHRMEBTADAQH/MAsGA1UdDwQEAwIBBjANBgkq

hkiG9w0BAQsFAAOCAQEAAd4gxhhVBHv7BJzIR62PFUo50EyB+FEwBLunVl+0GJkD

j/8joN/TSGjdLsH+W6WJTV4pVJMqiwW69qXT5Pe3xJUHfqmOshqJek5maSwR/JMo

K6uE1EOqut3yke4YXVyx5yDjlSghM2qiUQEWsQXo+m8pU01FLf22QFLk4LpjalP4

lL/LC2TZG5af2HgdXkhLkm3J+pvwGH/Aq433tvpdTriOMV1whDn3zWiFBasbra3y

hXJSJU+r0DB8R7rU87/EEGE8Z3riSF6XgIhRJEVMPHIYjneGmTgXfK3MQiRiwHBh

jwVBNB9FfMPm07Dxd0gffRFC2yJESOUzPTga/2vr4g==

* ----END CERTIFICATE-----

</ca>

<cert>

</cert>

<key>

</key>

reneg-sec 0

verify-x509-name myserver name

* 클라이언트 인증서 <cert> </cert>사이에 추가

* 클라이언트 키 <key> </key> 사이에 추가 하고 저장

* AWS Client VPN용 클라이언트 프로그램(윈도우용) 다운로드 설치(맥, 리눅스는 별도 프로그램)

<https://d20adtppz83p9s.cloudfront.net/WPF/latest/AWS_VPN_Client.msi>

[![](AWS%20Client%20VPN%20%EC%8B%A4%EC%8A%B5/image%207.png)](AWS%20Client%20VPN%20%EC%8B%A4%EC%8A%B5/image%207.png)[![](AWS%20Client%20VPN%20%EC%8B%A4%EC%8A%B5/image%208.png)](AWS%20Client%20VPN%20%EC%8B%A4%EC%8A%B5/image%208.png)

* 연결된 후 Private Subnet에 있는 EC2와 통신이 가능함.