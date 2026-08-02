---
title: "IPsec(Internet Protocol Security)"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "온프레미스 ICT 인프라구조", "VPN(Virtual Private Network)"]
is_public: true
draft: false
---

# **IPsec(Internet Protocol Security)**

IPsec(Internet Protocol Security)은 **IP 계층에서 보안 기능을 제공하는 프로토콜 스위트**로, **데이터 무결성, 기밀성, 인증 및 재전송 방지(Anti-Replay) 기능**을 제공합니다. 주로 **VPN, 사이트 간 보안 통신, 원격 접속 보안**에 사용됩니다.

---

## **1. IPsec의 주요 기능**

|  |  |
| --- | --- |
| 기능 | 설명 |
| **기밀성 (Confidentiality)** | 암호화를 통해 데이터 보호 (예: AES, 3DES) |
| **무결성 (Integrity)** | 데이터 변경 여부를 검증 (예: HMAC-SHA, HMAC-MD5) |
| **인증 (Authentication)** | 통신하는 장치 간 신뢰성 확보 (예: Pre-Shared Key, RSA, X.509) |
| **재전송 방지 (Anti-Replay)** | 패킷 재전송 공격 방어 (일련번호 기반) |

---

## **2. IPsec의 주요 구성 요소**

IPsec은 여러 개의 프로토콜로 구성되며, **보안 서비스 제공 방식과 동작 모드**에 따라 설정됩니다.

### **🔹 (1) 보안 프로토콜**

IPsec은 두 가지 주요 프로토콜을 사용합니다.

1. **AH (Authentication Header)**
   * **데이터 무결성과 인증 제공 (암호화는 X)**
   * 데이터 변경 여부 확인 가능
   * `IP 프로토콜 번호 51` 사용

2. **ESP (Encapsulating Security Payload)**
   * **데이터 암호화 + 무결성 + 인증 제공**
   * `IP 프로토콜 번호 50` 사용
   * **일반적으로 AH 대신 ESP를 사용**

|  |  |  |
| --- | --- | --- |
| 비교 항목 | AH (Authentication Header) | ESP (Encapsulating Security Payload) |
| 암호화 지원 | ❌ (암호화 X) | ✅ (암호화 O) |
| 무결성 검증 | ✅ | ✅ |
| 인증 | ✅ | ✅ |
| 재전송 방지 | ✅ | ✅ |
| 일반적인 사용 | 보안 강화 (암호화 불필요) | VPN, 보안 통신 (암호화 필수) |

---

### **🔹 (2) IPsec의 동작 모드**

IPsec은 **트래픽 보호 범위**에 따라 **전송 모드**와 **터널 모드**로 나뉩니다.

|  |  |  |
| --- | --- | --- |
| 모드 | 설명 | 사용 예시 |
| **전송 모드 (Transport Mode)** | 원본 IP 헤더 유지, 페이로드(데이터)만 보호 | 호스트 간 통신 보호 (예: SSH 보안) |
| **터널 모드 (Tunnel Mode)** | 전체 IP 패킷을 캡슐화하여 새 IP 헤더 추가 | VPN, 사이트 간 통신 |

🔹 **전송 모드 예시 (Host-to-Host)**

```
[원본 패킷]  | IP 헤더 | TCP/UDP 데이터 |
[AH 적용]    | IP 헤더 | AH | TCP/UDP 데이터 |
[ESP 적용]   | IP 헤더 | ESP Header | 암호화된 데이터 | ESP Trailer |
```

🔹 **터널 모드 예시 (Site-to-Site VPN)**

```
[원본 패킷]  | 원본 IP 헤더 | TCP/UDP 데이터 |
[터널 모드]  | 새 IP 헤더 | ESP Header | 암호화된 원본 패킷 | ESP Trailer |
```

---

## **3. IPsec의 작동 과정 (ISAKMP & SA)**

IPsec은 **두 장치 간 보안 협상을 위해 SA(Security Association)** 를 설정합니다.

### **🔹 (1) IKE (Internet Key Exchange) - 키 교환**

IPsec에서 **IKE(Internet Key Exchange)** 는 **암호화 키와 보안 매개변수를 설정**하는 역할을 합니다.

IKE는 **Phase 1, Phase 2** 두 단계로 나뉩니다.

1️⃣ **IKE Phase 1 (ISAKMP SA 설정)**

* 장치 간 **보안 채널 수립**

* **메시지 인증 및 키 교환**

* **세션연결: 메인 모드(Main Mode), 공격 대응용 빠른 모드(Aggressive Mode)**

2️⃣ **IKE Phase 2 (IPsec SA 설정)**

* 실제 **IPsec 트래픽을 보호할 보안 연결(SA) 설정**

* ESP 또는 AH 사용

* **세션연결: 빠른 모드(Quick Mode)**

### **🔹 (2) SA (Security Association) - 보안 연결 설정**

* **IPsec SA**: 두 장비 간 **보안 정책을 설정하고 유지하는 데이터베이스**

* SA는 단방향(One-way)으로 설정됨 (따라서 양방향 통신 시 SA 2개 필요)

* SA는 **SPI(Security Parameter Index) 값**을 통해 구분됨

```
show crypto ipsec sa  # SA 상태 확인 명령어
```

---

## **4. IPsec의 암호화 및 인증 알고리즘**

IPsec은 다양한 암호화 및 인증 알고리즘을 지원합니다.

### **🔹 (1) 암호화 알고리즘 (Encryption)**

|  |  |  |  |
| --- | --- | --- | --- |
| 알고리즘 | 키 길이 | 보안성 | 비고 |
| DES | 56-bit | 낮음 | 사용 지양 |
| 3DES | 168-bit | 중간 | 성능 저하 가능 |
| AES | 128/192/256-bit | 높음 | 강력한 보안 |

### **🔹 (2) 무결성 검증 알고리즘 (Integrity)**

|  |  |  |
| --- | --- | --- |
| 알고리즘 | 해시 크기 | 보안성 |
| MD5 | 128-bit | 낮음 (충돌 가능) |
| SHA-1 | 160-bit | 중간 (보안 취약) |
| SHA-256 | 256-bit | 높음 |
| SHA-512 | 512-bit | 매우 높음 |

---

## **5. IPsec VPN 구성 예제 (Cisco)**

Cisco 장비에서 **Site-to-Site IPsec VPN** 을 설정하는 기본 명령어입니다.

### **🔹 1) IKE Phase 1 설정**

```
crypto isakmp policy 10
 encr aes 256
 hash sha256
 authentication pre-share
 group 5
 lifetime 86400
```

### **🔹 2) IKE Phase 2 (IPsec SA) 설정**

```
crypto ipsec transform-set MYSET esp-aes esp-sha-hmac
```

### **🔹 3) VPN 피어(상대 라우터) 및 키 설정**

```
crypto isakmp key MY_SECRET_KEY address 192.168.2.1
```

### **🔹 4) 암호화 맵 적용**

```
crypto map MYMAP 10 ipsec-isakmp
 set peer 192.168.2.1
 set transform-set MYSET
 match address 101
```

### **🔹 5) 인터페이스에 암호화 적용**

```
interface GigabitEthernet0/0
 crypto map MYMAP
```

---

## **6. IPsec의 장점과 단점**

✅ **장점**

* **강력한 보안** (암호화 + 무결성 + 인증)

* **유연한 사용 가능** (VPN, 원격 접속 등)

* **공용 네트워크에서도 안전한 통신 가능**

❌ **단점**

* **설정이 복잡** (SA, 키 교환, 암호화 설정 필요)

* **암호화로 인한 네트워크 성능 저하 가능**

* **방화벽에서 ESP (IP 프로토콜 50) 및 AH (IP 프로토콜 51) 허용 필요**

---

## **7. 결론**

* IPsec은 **VPN, 원격 보안 접속, 네트워크 보안**에 필수적인 프로토콜

* **ESP 모드**(암호화 포함)가 일반적으로 사용됨

* **터널 모드**는 VPN 연결에 최적, **전송 모드**는 호스트 간 보호에 적합

* **IKE를 통한 SA(Security Association) 설정이 중요**