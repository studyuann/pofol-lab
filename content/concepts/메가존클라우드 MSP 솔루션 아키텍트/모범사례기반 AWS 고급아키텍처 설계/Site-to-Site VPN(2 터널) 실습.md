---
title: "Site-to-Site VPN(2 터널) 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "모범사례기반 AWS 고급아키텍처 설계"]
is_public: true
draft: false
---

# Site-to-Site VPN(2 터널) 실습

[![](Site-to-Site%20VPN(2%20%ED%84%B0%EB%84%90)%20%EC%8B%A4%EC%8A%B5/image.png)](Site-to-Site%20VPN(2%20%ED%84%B0%EB%84%90)%20%EC%8B%A4%EC%8A%B5/image.png)

## 🌐 전체 네트워크 설계도

* **도쿄 VPC (**`10.20.0.0/16`**)**
  + VPN 서버 (Libreswan): `10.20.0.221` (Public: `13.112.251.28`)
  + 일반 EC2: `10.20.1.101`

* **서울 VPC (**`10.10.0.0/16`**)**
  + VGW (Virtual Private Gateway) 사용
  + 퍼블릭 EC2: `10.10.0.225`
  + 프라이빗 EC2: `10.10.1.x`

---

## 1. AWS 콘솔 설정 (서울 리전)

### 1.1 가상 프라이빗 게이트웨이(VGW) 및 고객 게이트웨이(CGW)

1. **VGW 생성**: 서울 VPC에 생성 후 'Attach' 합니다.

2. **CGW 생성**: 도쿄 VPN EC2의 \*\*공인 IP(EIP)\*\*를 입력하여 생성합니다.

### 1.2 VPN 연결 생성

1. **VPN 연결 생성**: 위에서 만든 VGW와 CGW를 선택합니다.

2. **라우팅 옵션**: \*\*정적(Static)\*\*을 선택하고 도쿄 대역인 `10.0.0.0/16`을 입력합니다.

3. **구성 다운로드**: 생성이 완료되면 '구성 다운로드'를 눌러 **Vendor: Generic** 파일을 받습니다. (여기에 터널 1, 2의 Outside IP와 Pre-Shared Key가 들어있습니다.)

### 1.3 라우팅 테이블 업데이트

* 서울 VPC의 서브넷 라우팅 테이블에 `10.0.0.0/16` -> 대상: `vgw-xxxx` 경로를 추가합니다.

---

## 1. 도쿄 VPN 서버(Libreswan) 보안 그룹 설정

### **인바운드 규칙 (Inbound Rules)**

|  |  |  |  |
| --- | --- | --- | --- |
| **프로토콜** | **포트 범위** | **소스 (Source)** | **설명** |
| **UDP** | **500** | `52.79.222.196/32` | 서울 Tunnel 1 공인 IP (IKE) |
| **UDP** | **4500** | `52.79.222.196/32` | 서울 Tunnel 1 공인 IP (NAT-T) |
| **UDP** | **500** | `54.116.55.60/32` | 서울 Tunnel 2 공인 IP (IKE) |
| **UDP** | **4500** | `54.116.55.60/32` | 서울 Tunnel 2 공인 IP (NAT-T) |
| **모든 ICMP** | **All** | `10.10.0.0/16` | **서울 VPC 전체 대역** (통신 허용) |
| **모든 트래픽** | **All** | `10.20.0.0/16` | **도쿄 VPC 내부 대역** (로컬 서버 통신) |

---

## 2. Libreswan 설정 (`/etc/ipsec.d/seoul-vpn.conf`)

VTI 인터페이스 연동을 위해 `mark`와 `0.0.0.0/0` 서브넷 설정을 적용합니다.

```
conn seoul-tunnel-1
    authby=secret
    auto=start
    left=%defaultroute
    leftid=13.112.251.28      # 도쿄 VPN 서버 공인 IP
    leftsubnet=0.0.0.0/0
    right=52.79.222.196       # 서울 VGW Tunnel 1 공인 IP
    rightsubnet=0.0.0.0/0
    ikev2=yes
    encapsulation=yes         # NAT-T 활성화 (UDP 4500 사용)
    dpdaction=restart
    mark=5/0xffffffff         # vti0 인터페이스 매칭용
    vti-interface=vti0
    vti-routing=no
    vti-shared=yes
    leftvti=10.20.0.221

conn seoul-tunnel-2
    authby=secret
    auto=start
    left=%defaultroute
    leftid=13.112.251.28
    leftsubnet=0.0.0.0/0
    right=54.116.55.60        # 서울 VGW Tunnel 2 공인 IP
    rightsubnet=0.0.0.0/0
    ikev2=yes
    encapsulation=yes
    dpdaction=restart
    mark=6/0xffffffff         # vti1 인터페이스 매칭용
    vti-interface=vti1
    vti-routing=no
    vti-shared=yes
    leftvti=10.20.0.221
```

---

## 3. VTI 및 라우팅 자동화 (도쿄 VPN 서버)

서버에서 터널 인터페이스를 생성하고, 이중화 경로를 지정합니다.

```
# VTI 인터페이스 생성
sudo ip tunnel add vti0 mode vti remote 52.79.222.196 key 5
sudo ip addr add 169.254.43.50/30 remote 169.254.43.49 dev vti0
sudo ip link set vti0 up

sudo ip tunnel add vti1 mode vti remote 54.116.55.60 key 6
sudo ip addr add 169.254.199.34/30 remote 169.254.199.33 dev vti1
sudo ip link set vti1 up

# 서울 대역(10.10.0.0/16) 라우팅 (Metric으로 우선순위 부여)
sudo ip route add 10.10.0.0/16 dev vti0 metric 100
sudo ip route add 10.10.0.0/16 dev vti1 metric 200

# 커널 설정 (IP 포워딩 및 비대칭 라우팅 방지)
sudo sysctl -w net.ipv4.ip_forward=1
sudo sysctl -w net.ipv4.conf.all.rp_filter=0
sudo sysctl -w net.ipv4.conf.default.rp_filter=0
```

---

## 4. AWS 인프라 설정 요약

### **[서울 리전]**

1. **VPC 라우팅 테이블:** `10.20.0.0/16` (도쿄) → `vgw-xxxx` (VGW) 추가.

2. **VPN Static Routes:** VPN 연결 설정에서 `10.20.0.0/16` 명시적 등록.

3. **EC2 보안 그룹:** 인바운드 규칙에 도쿄 사설 대역(`10.20.0.0/16`) ICMP/TCP/UDP 허용.

### **[도쿄 리전]**

1. **VPC 라우팅 테이블:** `10.10.0.0/16` (서울) → `i-xxxx` (도쿄 VPN 서버 ID) 추가.

2. **VPN 서버 인스턴스:** **Source/Dest. Check**를 반드시 \*\*중지(Stop)\*\*로 설정.

---