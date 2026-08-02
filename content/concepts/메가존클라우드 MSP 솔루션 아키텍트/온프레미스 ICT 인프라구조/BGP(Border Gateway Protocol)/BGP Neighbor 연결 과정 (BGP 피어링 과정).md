---
title: "BGP Neighbor 연결 과정 (BGP 피어링 과정)"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "온프레미스 ICT 인프라구조", "BGP(Border Gateway Protocol)"]
is_public: true
draft: false
---

# **BGP Neighbor 연결 과정 (BGP 피어링 과정)**

BGP(Border Gateway Protocol)는 **자율 시스템(AS, Autonomous System)** 간의 경로를 교환하는 라우팅 프로토콜이다.

BGP는 **Neighbor(피어, Peer)** 라우터와 **TCP 연결(Port 179)** 을 맺고, **경로 정보(라우팅 테이블)** 를 공유한다.

## **1. BGP Neighbor 연결 과정 (Finite State Machine)**

BGP 피어링이 형성될 때, 라우터는 **6단계의 상태 변화(Finite State Machine, FSM)** 를 거칩니다.

|  |  |  |
| --- | --- | --- |
| 단계 | 상태 이름 | 설명 |
| 1️⃣ | **Idle** | BGP 프로세스가 시작되었지만, 아직 연결을 시도하지 않음 |
| 2️⃣ | **Connect** | TCP(포트 179)를 사용하여 Neighbor와 연결 시도 |
| 3️⃣ | **Active** | 이전 단계에서 연결 실패 시, 다시 연결을 시도 |
| 4️⃣ | **OpenSent** | Open 메시지를 보내고, 상대방의 Open 메시지를 기다림 |
| 5️⃣ | **OpenConfirm** | Keepalive 메시지를 주고받으며 세션 확인 |
| 6️⃣ | **Established** ✅ | BGP Neighbor 관계가 성립되고, 경로 정보(UPDATE 메시지) 교환 시작 |

---

## **2. BGP Neighbor 연결 과정 상세 설명**

### **🔹 (1) Idle 상태**

* BGP 프로세스가 실행되었지만, 아직 Neighbor(피어)와 연결을 시도하지 않음

* **원인:** 초기 상태이거나, 이전 세션이 종료되었을 때

* **Idle 상태에서 빠져나오려면?**
  + `neighbor` 명령을 통해 수동으로 설정
  + 라우터 설정에 문제가 없는지 확인

### **🔹 (2) Connect 상태**

* 라우터가 **TCP(포트 179)** 를 사용하여 BGP Neighbor(피어)와 연결을 시도

* **성공 시:** OpenSent 상태로 이동

* **실패 시:** Active 상태로 이동

### **🔹 (3) Active 상태**

* Connect 상태에서 TCP 연결이 실패하면 Active 상태로 변경됨

* 다시 TCP 연결을 시도

* **반복적으로 Active 상태가 유지되면?**
  + **Neighbor IP 설정 확인** (올바른 IP인지 확인)
  + **TCP 연결 가능 여부 확인** (`telnet [neighbor IP] 179` 실행)
  + **AS 번호가 맞는지 확인**

### **🔹 (4) OpenSent 상태**

* TCP 연결이 성공하면 **BGP Open 메시지를 전송**

* 상대방의 **Open 메시지를 기다리는 상태**

* **Open 메시지에는 다음 정보 포함**
  + BGP 버전
  + AS 번호
  + BGP 라우터 ID
  + 홀드 타임(Hold Time)

### **🔹 (5) OpenConfirm 상태**

* BGP Open 메시지를 주고받은 후 **Keepalive 메시지 교환**

* BGP Neighbor가 정상적으로 동작하는지 확인

* **만약 문제가 발생하면?**
  + Notification 메시지를 보내고 세션 종료

### **🔹 (6) Established 상태 ✅**

* BGP 피어링이 성공적으로 맺어짐

* **UPDATE 메시지를 교환**하여 라우팅 정보를 공유

* **BGP 상태가 Established가 아니면, 경로 정보가 교환되지 않음!**
  + `show ip bgp summary` 명령어로 확인 가능

---

## **3. BGP Neighbor 연결 상태 확인**

Cisco 라우터에서 BGP Neighbor 상태를 확인하는 명령어입니다.

```
Router# show ip bgp summary
```

출력 예시:

```
Neighbor        V    AS     MsgRcvd MsgSent  State   PfxRcd
192.168.1.2    4  65002       120      130  Established  10
```

✅ **State가 Established이면 BGP 피어링이 성공적으로 맺어짐**

---

## **4. BGP Neighbor 연결 문제 해결 (Troubleshooting)**

BGP Neighbor가 **Established 상태로 올라가지 않는 경우**, 다음을 확인해야 합니다.

|  |  |  |
| --- | --- | --- |
| 상태 | 원인 | 해결 방법 |
| Idle | BGP 설정 없음, IP 오류, ACL 차단 | `neighbor` 설정 확인, 방화벽 확인 |
| Connect | TCP 연결 실패 | 상대방 라우터와 네트워크 연결 확인 |
| Active | 상대방 라우터 응답 없음 | AS 번호, IP 주소, 포트 179 확인 |
| OpenSent | BGP 버전 불일치 | 같은 BGP 버전 사용하도록 설정 |
| OpenConfirm | Keepalive 메시지 문제 | BGP 설정 다시 확인 |

### **🔹 네트워크 연결 확인**

```
ping [neighbor IP]
telnet [neighbor IP] 179
```

🔍 **TCP 포트 179가 열려 있는지 확인**

### **🔹 BGP 설정 확인**

```
show running-config | include bgp
```

🔍 **AS 번호, Neighbor IP가 올바른지 확인**

---

## **5. BGP Neighbor 연결 예제**

### **🔹 eBGP 설정 (AS 65001 ↔ AS 65002)**

### **🔹 Router A (AS 65001)**

```
RouterA(config)# router bgp 65001
RouterA(config-router)# neighbor 192.168.1.2 remote-as 65002
RouterA(config-router)# exit
```

### **🔹 Router B (AS 65002)**

```
RouterB(config)# router bgp 65002
RouterB(config-router)# neighbor 192.168.1.1 remote-as 65001
RouterB(config-router)# exit
```

🔹 **설정이 올바르면,** `show ip bgp summary` **에서 Established 확인 가능**

---

## **결론**

* BGP Neighbor 연결은 **6단계의 FSM(State Machine) 과정**을 거친다.

* **Established 상태가 되어야 정상적인 BGP 피어링 및 경로 교환 가능**

* **BGP 문제 발생 시, Neighbor IP / AS 번호 / TCP 179 포트 등을 확인해야 함**

* **BGP 설정이 정상이라면** `show ip bgp summary`**에서 Established 상태 확인 가능**