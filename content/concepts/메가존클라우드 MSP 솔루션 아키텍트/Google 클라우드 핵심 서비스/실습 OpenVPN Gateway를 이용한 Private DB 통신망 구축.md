---
title: "실습 OpenVPN Gateway를 이용한 Private DB 통신망 구축"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Google 클라우드 핵심 서비스"]
is_public: true
draft: false
---

# 실습. OpenVPN Gateway를 이용한 Private DB 통신망 구축

## 1. 실습 배경 및 목적

클라우드 보안의 핵심은 '최소 노출'이다. 기업의 핵심 데이터가 담긴 DB는 공인 IP 없이 사설망(Private Subnet)에만 존재해야 한다. 본 실습은 외부망(집/사무실)에서 클라우드 내부의 폐쇄된 DB에 접속하기 위한 안전한 통로(VPN)를 구축하고, 네트워크 패킷의 흐름을 제어하는 능력을 배양한다.

---

## 2. 전체 구성도 (Logical Architecture)

|  |  |  |
| --- | --- | --- |
| **구성 요소** | **상세 사양** | **역할** |
| **Local Client** | Windows 10/11, OpenVPN Connect | VPN 터널의 시작점 및 DB 관리 도구 실행 |
| **VPN Gateway** | Ubuntu 22.04 LTS (e2-medium 권장) | 외부 패킷을 수신하여 VPC 내부로 중계 (Router 역할) |
| **Cloud SQL** | MySQL 8.0 (Private IP 전용) | 외부 노출이 차단된 핵심 데이터 저장소 |
| **Network** | GCP Custom VPC | 프로젝트 전용 격리된 네트워크 환경 |

---

## 3. 상세 구축 절차

### 단계 1: Custom VPC 및 Cloud SQL 준비

1. **VPC 생성:** `10.0.0.0/20` 대역의 Custom VPC를 생성한다.

2. **Cloud SQL 생성:** [연결] 설정에서 비공개 IP(Private IP)를 활성화한다.
   * 연결할 네트워크를 위에서 생성한 Custom VPC로 지정한다.
   * ※ 이때 할당되는 사설 IP(예: `10.160.1.3`)를 반드시 기록한다.

### 단계 2: VPN Gateway VM 인스턴스 생성

1. **VPC 위치:** 반드시 DB가 속한 **Custom VPC** 내부에 생성한다. (Default VPC 사용 시 통신 단절의 원인이 됨)

2. **방화벽(핵심):** VM 인스턴스 설정 화면에서 \*\*'Allow HTTP/HTTPS traffic'\*\*을 체크한다.
   * 이는 GCP가 제공하는 시스템 태그(`http-server`)를 활용하여 인바운드 정책을 가장 확실하게 적용하는 방법이다.

3. **외부 IP:** 클라이언트가 접속할 수 있도록 고정(Static) 외부 IP를 할당한다.

### 단계 3: OpenVPN 서버 구축 및 최적화

1. **설치 스크립트 활용:**Bash

   # 

   ```
   wget https://git.io/vpn -O openvpn-install.sh
   chmod +x openvpn-install.sh
   sudo ./openvpn-install.sh
   ```

2. **환경 설정 (가정용 공유기 트러블슈팅):**
   * **Protocol:** **TCP** 선택 (UDP는 공유기 방화벽에서 드랍될 확률이 높음)
   * **Port:** **443** (표준 HTTPS 포트를 사용하여 필터링 우회)

3. **OS 레벨 패킷 포워딩:** \* `/etc/sysctl.conf`에서 `net.ipv4.ip_forward = 1` 주석을 해제하거나 추가한다.
   * `sudo sysctl -p`로 즉시 적용한다.

### 단계 4: IPTables를 이용한 네트워크 주소 변환(NAT)

VPN을 통해 들어온 패킷은 `10.8.0.x` 주소를 가진다. DB는 이 대역을 모르기 때문에 VM의 내부 IP로 변장시켜야 응답을 받을 수 있다.

```
# 내부 인터페이스 명칭(예: ens4)을 확인 후 실행
sudo iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o ens4 -j MASQUERADE

# 설정 영구 저장
sudo apt-get install iptables-persistent
sudo netfilter-persistent save
```

### 단계 5: 클라이언트(Windows) 연동 및 라우팅 추가

1. **파일 다운로드:** 생성된 `.ovpn` 파일을 로컬 PC로 가져와 OpenVPN Connect에 등록한다.

2. **라우팅 테이블 수정 (가장 중요):** VPN 연결 후, 사설 대역(`10.160.x.x`)을 향하는 패킷만 터널로 보내도록 이정표를 세운다.PowerShell

   ```
   # 관리자 권한 CMD에서 실행
   route add 10.160.0.0 mask 255.255.0.0 10.8.0.1
   ```

---

## 4. 검증 및 디버깅 (Verification)

### 1단계: 통로 확인 (Ping)

* 로컬 CMD에서 `ping 10.160.1.3`을 실행한다.

* 응답이 없다면 VM에서 `tcpdump -ni any icmp`를 실행하여 패킷이 VM까지 도달하는지 확인한다.

### 2단계: 서비스 확인 (Telnet/TNC)

* 파워쉘에서 `tnc 10.160.1.3 -port 3306`을 실행한다.

* `TcpTestSucceeded : True`가 떠야 최종 성공이다.

---