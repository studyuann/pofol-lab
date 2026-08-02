---
title: "BGP (Border Gateway Protocol) 개념 정리"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "온프레미스 ICT 인프라구조", "BGP(Border Gateway Protocol)"]
is_public: true
draft: false
---

# **BGP (Border Gateway Protocol) 개념 정리**

## **1. BGP란?**

* BGP (Border Gateway Protocol)은 인터넷에서 **자율 시스템(AS, Autonomous System)** 간의

라우팅 정보를 교환하는 프로토콜입니다.

인터넷을 구성하는 여러 네트워크 간에 **최적의 경로를 찾고 유지**하는 역할을 합니다.

---

## **2. BGP의 주요 특징**

✅ **인터넷의 핵심 라우팅 프로토콜**

✅ **AS(자율 시스템) 간의 경로를 설정하고 최적화**

✅ **경로 벡터 프로토콜(Path Vector Protocol)** 사용

✅ **Path Attribute (경로 속성)를 기반으로 라우팅 결정**

✅ **신뢰성이 높은 연결을 위해 TCP(포트 179) 사용**

---

## **3. BGP의 작동 방식**

### **🔹 3.1. BGP 라우터 간의 관계**

BGP는 AS 간의 경로를 관리하기 위해 BGP 피어링(Peering)을 설정합니다.

BGP 라우터 간의 관계는 크게 두 가지로 나뉩니다.

1️⃣ **eBGP (External BGP)**

* 서로 다른 AS 간에 BGP 정보를 교환

* 인터넷 서비스 제공자(ISP) 간에 사용됨

* 보통 직접 연결된 네트워크에서 실행됨

2️⃣ **iBGP (Internal BGP)**

* 같은 AS 내부에서 BGP 정보를 공유

* 여러 라우터가 있을 때 AS 내부에서 BGP 경로를 유지하기 위해 사용

* 스플릿 호라이즌(Split Horizon) 규칙 적용 (Loop 방지)

---

### **🔹 3.2. BGP 메시지 유형**

BGP는 4가지 주요 메시지를 사용하여 피어링을 설정하고 경로를 업데이트합니다.

|  |  |
| --- | --- |
| 메시지 유형 | 설명 |
| **OPEN** | BGP 피어링 관계 설정 |
| **UPDATE** | 네트워크 경로 정보 업데이트 |
| **KEEPALIVE** | 피어 간 연결 유지 (주기적 전송) |
| **NOTIFICATION** | 에러 발생 시 피어 연결 종료 |

---

### **🔹 3.3. BGP 경로 선택 과정**

BGP는 단순히 **가장 짧은 경로를 선택하지 않고** 다양한 속성을 기반으로 최적의 경로를 선택합니다.

1️⃣ **선호도 높은 경로 선택 (Weight 값이 높은 경로 우선)**

2️⃣ **Local Preference (지역 우선순위가 높은 경로 선택)**

3️⃣ **AS Path (경로가 짧은 AS를 선호)**

4️⃣ **Origin Type (IGP > EGP > Unknown 순서로 선호)**

5️⃣ **Multi-Exit Discriminator (MED) 값이 작은 경로 선호**

6️⃣ **eBGP 경로가 iBGP 경로보다 우선됨**

7️⃣ **라우터 ID가 작은 경로 선택**

💡 **BGP는 최적의 경로를 선택할 때 위의 기준을 차례대로 비교하여 결정합니다.**

---

## **4. BGP 경로 속성 (Path Attributes)**

BGP 경로를 제어하는 중요한 속성들입니다.

|  |  |  |
| --- | --- | --- |
| 속성 | 설명 | 필수 여부 |
| **AS\_PATH** | 지나온 AS 목록 | ✅ 필수 |
| **NEXT\_HOP** | 다음 목적지 라우터 IP 주소 | ✅ 필수 |
| **LOCAL\_PREF** | AS 내부에서 우선순위 결정 | 선택 |
| **MED (Metric)** | 특정 경로를 선호하도록 조정 | 선택 |
| **COMMUNITY** | 특정 그룹 내에서 정책 적용 | 선택 |

---

## **5. BGP와 IGP (내부 게이트웨이 프로토콜) 비교**

|  |  |  |
| --- | --- | --- |
| 항목 | BGP (Border Gateway Protocol) | IGP (OSPF, EIGRP, RIP 등) |
| **역할** | AS 간 라우팅 (인터넷) | AS 내부 라우팅 |
| **프로토콜 유형** | Path Vector Protocol | Link-State 또는 Distance Vector |
| **라우팅 대상** | 인터넷 전체 경로 | 내부 네트워크 경로 |
| **경로 결정 기준** | Path Attributes (AS\_PATH, LOCAL\_PREF 등) | 메트릭 (Cost, Hop Count 등) |
| **속도** | 느림 (수초~수분) | 빠름 (밀리초~초) |
| **규모** | 대규모 네트워크 (인터넷) | 소규모, 중규모 네트워크 |

---

## **6. BGP의 장점과 단점**

### **✅ BGP의 장점**

✔ 인터넷에서 **가장 안정적인 라우팅 프로토콜**

✔ 다양한 **경로 선택 기준 제공 (정책 기반 라우팅 가능)**

✔ **대규모 네트워크 확장 가능**

### **❌ BGP의 단점**

❌ **설정이 복잡하고 운영이 어려움**

❌ **라우팅 갱신 속도가 느림 (Failover가 느릴 수 있음)**

❌ **초기 설정 및 튜닝 필요 (Best Path Selection)**

---

## **7. BGP 구성 예제 (Cisco 설정 예시)**

### **🔹 eBGP 설정 (AS 65001 ↔ AS 65002)**

```
Router_A(config)# router bgp 65001
Router_A(config-router)# neighbor 192.168.1.2 remote-as 65002
Router_A(config-router)# network 10.10.10.0 mask 255.255.255.0
```

### **🔹 iBGP 설정 (AS 65001 내부)**

```
Router_B(config)# router bgp 65001
Router_B(config-router)# neighbor 192.168.2.1 remote-as 65001
Router_B(config-router)# network 10.20.20.0 mask 255.255.255.0
```

---

## **8. BGP 활용 사례**

📌 **ISP (인터넷 서비스 제공자) 간의 연결**

📌 **대기업 및 클라우드 네트워크 (Google, AWS, Azure)**

📌 **CDN (Content Delivery Network) 트래픽 관리**

📌 **멀티홈 네트워크 (하나의 AS가 여러 ISP와 연결된 환경)**

---

## **결론**

* **BGP는 인터넷에서 사용되는 가장 중요한 라우팅 프로토콜**

* **AS 간에 최적의 경로를 선택하여 안정적인 네트워크 운영**

* **정책 기반 라우팅 가능하지만 설정 및 운영이 복잡**

* **인터넷 백본(Backbone) 네트워크를 구성하는 핵심 요소**

BGP는 **인터넷 라우팅의 핵심 기술**이므로, 네트워크 엔지니어나 시스템 관리자는 기본적인 개념을 이해하는 것이 중요하다.