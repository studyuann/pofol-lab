---
title: "NAT instance 설정"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 클라우드 기술 기초(TESS)"]
is_public: true
draft: false
---

# NAT instance 설정

### 1. nftables 설치 및 활성화

먼저 패키지를 설치하고 서비스를 올리는 작업부터 시작한다.

```
# 1. 패키지 설치
sudo dnf install nftables -y

# 2. 서비스 활성화 (부팅 시 자동 실행)
sudo systemctl enable nftables

# 3. 서비스 시작
sudo systemctl start nftables
```

```
# 1. IP 포워딩 설정 파일 생성
echo "net.ipv4.ip_forward = 1" | sudo tee /etc/sysctl.d/95-ipv4-forwarding.conf

# 2. 설정 적용
sudo sysctl -p /etc/sysctl.d/95-ipv4-forwarding.conf
```

### 2. NAT 규칙 적용 (AL2023 전용)

설치가 끝났다면 이제 다시 NAT 규칙을 넣어준다. (인터페이스 이름이 `ens5`인지 `ip link`로 꼭 확인!)

```
# 기존 규칙 초기화 (깨끗하게 시작)
sudo nft flush ruleset

# NAT 테이블과 체인 생성
sudo nft add table ip nat
sudo nft add chain ip nat postrouting { type nat hook postrouting priority 100 \; }

# 마스커레이드 규칙 추가 (외부로 나가는 인터페이스가 ens5일 때)
sudo nft add rule ip nat postrouting oifname "ens5" counter masquerade
```

### 3. 설정 영구 저장 (중요)

`nft` 명령어로 넣은 규칙은 메모리에만 저장되므로, 파일을 생성해 저장해야 재부팅 후에도 유지된다.

```
# 현재 설정된 규칙을 파일로 저장
sudo sh -c "nft list ruleset > /etc/nftables/main.nft"

# (참고) /etc/sysconfig/nftables.conf 파일에 
# include "/etc/nftables/main.nft" 가 포함되어 있는지 확인하면 완벽합니다.
```

---

### 마지막 체크리스트

1. **Source/Dest. Check:** AWS 콘솔에서 이 인스턴스의 '소스/대상 확인'을 **'중지(Stop)'** 한다.

2. **보안 그룹:** NAT 인스턴스의 **인바운드**에 Private Subnet의 IP 대역으로부터 오는 모든 트래픽(혹은 80, 443)이 허용한다.

3. **라우팅 테이블:** Private Subnet의 라우팅 테이블에 `0.0.0.0/0` -> `NAT 인스턴스 ID`가 등록한다.