---
title: "실습예제 Cisco IOS에서 Site-to-Site IPSec VPN을 설정하는 예제"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "온프레미스 ICT 인프라구조", "VPN(Virtual Private Network)", "Site-to-Site IPSec VPN"]
is_public: true
draft: false
---

# 실습예제: Cisco IOS에서 **Site-to-Site IPSec VPN**을 설정하는 예제

---

# **📌 예제 환경**

* **본사 라우터 (R1)**: 192.168.1.0/24

* **지사 라우터 (R2)**: 192.168.2.0/24

* **양쪽 공인 IP**
  + R1 WAN: **203.0.113.1**
  + R2 WAN: **198.51.100.1**

* **IPSec VPN 터널을 통해 본사와 지사를 연결**

---

# **🔹 Step 1: ISAKMP (IKE Phase 1) 설정**

```
R1(config)# crypto isakmp policy 10   ! ISAKMP 정책 생성
R1(config-isakmp)# encryption aes 256  ! AES-256 암호화 사용
R1(config-isakmp)# hash sha256         ! SHA-256 해시 알고리즘 사용
R1(config-isakmp)# authentication pre-share  ! 사전 공유 키 사용
R1(config-isakmp)# group 14            ! Diffie-Hellman Group 14 사용
R1(config-isakmp)# lifetime 86400       ! 키 수명 설정 (초)
R1(config-isakmp)# exit
```

🔹 **동일한 설정을 R2에서도 적용**

```
R2(config)# crypto isakmp policy 10
R2(config-isakmp)# encryption aes 256
R2(config-isakmp)# hash sha256
R2(config-isakmp)# authentication pre-share
R2(config-isakmp)# group 14
R2(config-isakmp)# lifetime 86400
R2(config-isakmp)# exit
```

---

# **🔹 Step 2: 사전 공유 키 설정**

```
R1(config)# crypto isakmp key VPNKEY address 198.51.100.1
```

```
R2(config)# crypto isakmp key VPNKEY address 203.0.113.1
```

✅ **VPNKEY**는 본사(R1)와 지사(R2)에서 **동일한 키**를 설정해야 합니다.

---

# **🔹 Step 3: IPSec Transform Set (IKE Phase 2) 설정**

```
R1(config)# crypto ipsec transform-set VPN-SET esp-aes 256 esp-sha-hmac
R1(config)# exit
```

```
R2(config)# crypto ipsec transform-set VPN-SET esp-aes 256 esp-sha-hmac
R2(config)# exit
```

✅ **AES-256 & SHA-1**를 사용하여 데이터 암호화

---

# **🔹 Step 4: Crypto Map 설정**

```
R1(config)# crypto map VPN-MAP 10 ipsec-isakmp
R1(config-crypto-map)# set peer 198.51.100.1
R1(config-crypto-map)# set transform-set VPN-SET
R1(config-crypto-map)# match address VPN-TRAFFIC
R1(config-crypto-map)# exit
```

```
R2(config)# crypto map VPN-MAP 10 ipsec-isakmp
R2(config-crypto-map)# set peer 203.0.113.1
R2(config-crypto-map)# set transform-set VPN-SET
R2(config-crypto-map)# match address VPN-TRAFFIC
R2(config-crypto-map)# exit
```

---

# **🔹 Step 5: ACL을 사용하여 트래픽 정의**

```
R1(config)# access-list 100 permit ip 192.168.1.0 0.0.0.255 192.168.2.0 0.0.0.255
```

```
R2(config)# access-list 100 permit ip 192.168.2.0 0.0.0.255 192.168.1.0 0.0.0.255
```

✅ **ACL을 통해 VPN 트래픽을 허용**

---

# **🔹 Step 6: Crypto Map을 인터페이스에 적용**

```
R1(config)# interface GigabitEthernet0/0
R1(config-if)# crypto map VPN-MAP
R1(config-if)# exit
```

```
R2(config)# interface GigabitEthernet0/0
R2(config-if)# crypto map VPN-MAP
R2(config-if)# exit
```

✅ **WAN 인터페이스에 VPN을 적용**

---

# **🔹 Step 7: NAT 예외 설정 (필요 시)**

```
R1(config)# ip access-list extended NAT-EXEMPT
R1(config-ext-nacl)# permit ip 192.168.1.0 0.0.0.255 192.168.2.0 0.0.0.255
R1(config-ext-nacl)# exit

R1(config)# route-map NAT permit 10
R1(config-route-map)# match ip address NAT-EXEMPT
R1(config-route-map)# exit

R1(config)# interface GigabitEthernet0/0
R1(config-if)# ip nat inside source route-map NAT interface GigabitEthernet0/0 overload
```

✅ NAT을 사용하는 경우 **VPN 트래픽을 NAT 제외(Exempt) 처리**

---

# **🔹 Step 8: VPN 상태 확인 명령어**

✅ **IPSec SA(Security Association) 확인**

```
R1# show crypto ipsec sa
```

✅ **ISAKMP 상태 확인**

```
R1# show crypto isakmp sa
```

✅ **VPN 터널 활성화 여부 확인**

```
R1# show crypto session
```

---

# **✅ 최종 요약**

💡 **Cisco IOS에서 Site-to-Site IPSec VPN을 설정하는 과정**

1️⃣ **IKE Phase 1** 설정 (ISAKMP 정책 정의, 키 교환)

2️⃣ **IKE Phase 2** 설정 (IPSec Transform Set 구성)

3️⃣ **VPN 트래픽을 허용하는 ACL 생성**

4️⃣ **Crypto Map을 생성하고 인터페이스에 적용**

5️⃣ **NAT 예외 처리 (필요 시)**

6️⃣ **VPN 터널 활성화 및 상태 확인**