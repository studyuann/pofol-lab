---
title: "Site-to-Site VPN(1 터널) 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "모범사례기반 AWS 고급아키텍처 설계"]
is_public: true
draft: false
---

# Site-to-Site VPN(1 터널) 실습

[![](Site-to-Site%20VPN(1%20%ED%84%B0%EB%84%90)%20%EC%8B%A4%EC%8A%B5/image.png)](Site-to-Site%20VPN(1%20%ED%84%B0%EB%84%90)%20%EC%8B%A4%EC%8A%B5/image.png)

### 🌐 네트워크 정보

* **서울 VPC**: `10.10.0.0/16` (VGW 사용)

* **도쿄 VPC**: `10.110.0.0/16` (VPN EC2 사용)

* **도쿄 VPN 서버 공인 IP**: `13.112.251.28` (EIP 권장)

---

### 1. AWS 콘솔 설정 (서울 리전)

1. **CGW/VGW 생성**: 기존과 동일하게 도쿄 VPN 서버의 공인 IP로 생성한다.

2. **VPN 연결 생성**:
   * **정적(Static) 라우팅** 선택 후 도쿄 대역(`10.20.0.0/16`) 입력.
   * 생성 후 **[구성 다운로드]** (Vendor: Generic)에서 **PSK**와 **Tunnel 1 Outside IP**를 확인한다.

3. **서울 라우팅 테이블**: `10.20.0.0/16` -> `vgw-xxxx` 추가.

---

### 2. 도쿄 VPN 서버(Libreswan) 설정

VTI를 사용하지 않으므로 설정이 훨씬 단순해진다.

### 2.1 `/etc/ipsec.d/seoul.secrets` (비밀키)

```
13.112.251.28 52.79.222.196 : PSK "YOUR_PRE_SHARED_KEY"
```

### 2.2 `/etc/ipsec.d/seoul.conf` (정책 기반 설정)

`leftsubnet`과 `rightsubnet`에 실제 VPC 대역을 넣는 것이 핵심이다.

```
cat <<EOF | sudo tee /etc/ipsec.d/seoul.conf
conn seoul-vpn
    authby=secret
    auto=start
    ikev2=yes
    
    # 도쿄 쪽 설정 (Local)
    left=%defaultroute
    leftid=13.112.251.28
    leftsubnet=10.20.0.0/16    # 도쿄 VPC 대역
    
    # 서울 쪽 설정 (Remote)
    right=52.79.222.196        # 서울 Tunnel 1 공인 IP
    rightsubnet=10.10.0.0/16   # 서울 VPC 대역
    
    # 터널 유지 설정
    dpdaction=restart
    encapsulation=yes          # NAT-T 활성화
EOF

# 서비스 재시작
sudo systemctl restart ipsec
```

---

### 3. OS 커널 및 라우팅 설정 (도쿄 서버)

VTI가 없기 때문에 `ip route` 명령어로 인터페이스를 만들 필요가 없습니다. 하지만 **패킷 포워딩**은 반드시 켜져 있어야 한다.

```
# 1. 패킷 포워딩 활성화
sudo sysctl -w net.ipv4.ip_forward=1

# 2. (선택) 영구 적용을 위해 /etc/sysctl.conf에 추가
echo "net.ipv4.ip_forward = 1" | sudo tee -a /etc/sysctl.conf

# 3. AWS 도쿄 VPC 라우팅 테이블 (콘솔에서 설정)
# 목적지: 10.10.0.0/16 (서울) -> 대상: i-xxxx (도쿄 VPN 서버 인스턴스 ID)
```

---

### 4. 핵심 체크포인트

* **Source/Dest. Check**: 도쿄 VPN 서버 인스턴스 설정에서 이 항목을 반드시 **'중지(Disabled)'** 해야 한다. 그렇지 않으면 도쿄의 다른 서버에서 보낸 패킷이 VPN 서버를 통과하지 못한다.

* **Security Group**:
  + 도쿄 VPN 서버: 서울 Tunnel 1 IP로부터 UDP 500, 4500 허용.
  + 서울/도쿄 일반 서버들: 상대방 VPC 대역(`10.x.x.x`)으로부터의 ICMP(Ping)를 허용해야 테스트가 가능하다.

---

**상태 확인 방법:**

설정 후 `sudo ipsec status`를 실행 때, `Total IPsec connections: loaded 1, active 1`출력 확인