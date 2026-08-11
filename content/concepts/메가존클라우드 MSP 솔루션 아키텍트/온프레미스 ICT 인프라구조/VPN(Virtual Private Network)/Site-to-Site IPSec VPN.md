---
title: "Site-to-Site IPSec VPN"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "온프레미스 ICT 인프라구조", "VPN(Virtual Private Network)"]
is_public: true
draft: false
---

# **Site-to-Site IPSec VPN**

---

# **1. Site-to-Site IPSec VPN 개요**

**Site-to-Site VPN**은 두 개의 네트워크(예: 본사와 지사)를 **보안 터널**을 통해 안전하게 연결하는 방식입니다.

이때, IPSec(Internet Protocol Security)을 사용하여 **데이터를 암호화하고 보호**합니다.

💡 **Site-to-Site VPN의 주요 특징**

✅ **기업 네트워크 간 보안 연결**

✅ **라우터 또는 방화벽 장비에서 설정됨**

✅ **사용자가 개별 VPN 접속 없이 자동으로 통신 가능**

---

# **2. Site-to-Site IPSec VPN 동작 과정**

Site-to-Site IPSec VPN은 \*\*두 단계(Phase 1, Phase 2)\*\*로 구성됩니다.

## **🔹 (1) Phase 1: IKE SA(Security Association) 설정**

* ISAKMP(Security Association Key Management Protocol)을 사용하여 **보안 정책을 협상**

* **Diffie-Hellman 키 교환**을 통해 **암호화 키를 안전하게 공유**

* **인증(Authentication)** 및 **암호화 알고리즘 결정**

### **📝 Phase 1 과정**

```
라우터A                      라우터B
   |--- 1. IKE SA 협상 요청 --->  |
   |<--- 2. IKE SA 응답   ----    |
   |--- 3. Diffie-Hellman 키 교환  |
   |<--- 4. 인증 및 암호화 설정 완료 |
```

---

## **🔹 (2) Phase 2: IPSec SA(Security Association) 설정**

* **ESP(Encapsulating Security Payload)** 또는 \*\*AH(Authentication Header)\*\*를 사용하여 **데이터 암호화**

* **IP 패킷을 터널링(Tunneling)하여 안전한 데이터 전송**

### **📝 Phase 2 과정**

```
라우터A                      라우터B
   |--- 5. IPSec SA 협상 요청 --->  |
   |<--- 6. IPSec SA 응답   ----    |
   |--- 7. 터널 생성 및 데이터 암호화 전송 |
   |<--- 8. 암호화된 데이터 수신 및 복호화 |
```

---

# **3. Site-to-Site IPSec VPN 그림**

아래 그림은 두 라우터가 **IPSec VPN 터널을 형성하여 데이터를 안전하게 전송**하는 과정을 보여줍니다.

```
+-------------+      IPSec VPN Tunnel      +-------------+
| 라우터 A    |==========================>| 라우터 B    |
| (본사)      |                            | (지사)      |
| Private LAN |                            | Private LAN |
+-------------+                            +-------------+

단계 1: IKE Phase 1 (키 교환 및 SA 설정)
단계 2: IKE Phase 2 (데이터 암호화 및 터널링)
단계 3: 암호화된 데이터 전송
```

---

# **4. IPSec VPN 설정 주요 파라미터**

Site-to-Site IPSec VPN을 구성할 때 **주요 설정 값**을 확인해야 합니다.

|  |  |
| --- | --- |
| 설정 항목 | 설명 |
| **암호화 알고리즘** | AES, 3DES |
| **인증 알고리즘** | SHA-256, SHA-512 |
| **키 교환 방식** | Diffie-Hellman Group 1, 2, 5,14, 19 |
| **IPSec 모드** | 터널 모드(Tunnel Mode), 전송 모드(Transport Mode) |
| **보안 프로토콜** | ESP (Encapsulating Security Payload) 또는 AH (Authentication Header) |

---

# **5. 결론**

✅ **Phase 1**: IKE SA 설정 → **보안 정책 협상 & 키 교환**

✅ **Phase 2**: IPSec SA 설정 → **데이터 암호화 및 안전한 통신**

✅ **IPSec VPN 터널을 통해 두 라우터 간 안전한 연결을 유지**

- [[실습예제 Cisco IOS에서 Site-to-Site IPSec VPN을 설정하는 예제|실습예제: Cisco IOS에서 Site-to-Site IPSec VPN을 설정하는 예제]]