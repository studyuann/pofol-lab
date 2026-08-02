---
title: "터널링(Tunneling)"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "온프레미스 ICT 인프라구조", "VPN(Virtual Private Network)"]
is_public: true
draft: false
---

# 터널링(Tunneling)

## 1. 개요

암호화가 적용되지 않은 터널링은 패킷을 암호화하지 않고 단순히 encapsulation하여 다른 네트워크를 통해 전송하는 방식입니다.

대표적인 기술로 **GRE(Generic Routing Encapsulation)** 터널이 있으며, 다양한 프로토콜을 IP 네트워크를 통해 전달할 수 있도록 해줍니다.

---

## 2. GRE (Generic Routing Encapsulation) 개념

### ▶ GRE란?

* **비암호화 터널링 프로토콜**로, 서로 다른 네트워크를 연결하기 위해 사용됩니다.

* 다양한 프로토콜(IPv4, IPv6, MPLS, AppleTalk 등)을 IP 네트워크를 통해 전달할 수 있도록 지원합니다.

* IPsec과 달리 **암호화 기능이 없으며** 무결성이나 인증을 제공하지 않습니다.

### ▶ GRE의 특징

|  |  |
| --- | --- |
| 특징 | 설명 |
| **암호화 없음** | 데이터가 암호화되지 않음 (보안 취약) |
| **다양한 프로토콜 지원** | IPv4, IPv6, IPX 등 다양한 프로토콜을 캡슐화 가능 |
| **오버헤드 증가** | GRE 헤더(4바이트)와 새로운 IP 헤더(20바이트) 추가 |
| **멀티캐스트 지원** | OSPF, EIGRP 등의 동적 라우팅 프로토콜 사용 가능 |

---

## 3. GRE 터널 구성

### ▶ GRE 터널링 동작 방식

1. **GRE 헤더 추가**: 원본 패킷에 GRE 헤더와 새로운 IP 헤더를 추가함.

2. **IP 네트워크를 통해 전송**: GRE 패킷이 공중망을 통해 전송됨.

3. **수신측에서 해제**: GRE 헤더를 제거하고 원본 패킷을 목적지로 전달함.

### ▶ GRE 패킷 구조

```
| New IP Header | GRE Header | Original Packet |
```

* **New IP Header**: 터널의 출발지와 목적지를 정의함.

* **GRE Header**: 캡슐화된 패킷의 프로토콜 유형 등을 포함.

* **Original Packet**: 원래 전송하고자 했던 데이터.

---

## 4. Cisco GRE 터널 설정 예제

### ▶ 구성 환경

* 라우터 A (Tunnel Source: 192.168.1.1)

* 라우터 B (Tunnel Destination: 192.168.2.1)

* 터널 인터페이스: **Tunnel 0**

### ▶ 라우터 A 설정

```
interface Tunnel0
 ip address 10.1.1.1 255.255.255.0
 tunnel source 192.168.1.1
 tunnel destination 192.168.2.1
!
ip route 192.168.2.0 255.255.255.0 10.1.1.2
```

### ▶ 라우터 B 설정

```
interface Tunnel0
 ip address 10.1.1.2 255.255.255.0
 tunnel source 192.168.2.1
 tunnel destination 192.168.1.1
!
ip route 192.168.1.0 255.255.255.0 10.1.1.1
```

---

## 5. GRE 터널 검증 및 문제 해결

### ▶ GRE 터널 상태 확인

```
show ip interface brief
show interfaces tunnel 0
show ip route
```

### ▶ 터널 통신 테스트

```
ping 10.1.1.2
```

### ▶ 일반적인 문제 해결 방법

|  |  |
| --- | --- |
| 문제 | 해결 방법 |
| 터널 인터페이스가 **down** 상태 | `show interfaces tunnel 0` 명령어로 확인 후, 소스 및 목적지 주소 검토 |
| **핑(Ping)이 안됨** | `show ip route` 확인, 터널 인터페이스의 경로 추가 |
| **MTU 문제 발생** | `ip mtu 1400` 및 `tunnel path-mtu-discovery` 명령어 추가 |

---

## 6. GRE 터널의 장점과 단점

### ▶ 장점

✅ 다양한 프로토콜 캡슐화 가능 (IPv4, IPv6, MPLS 등)  
✅ 동적 라우팅 프로토콜(OSPF, EIGRP) 지원  
✅ 멀티캐스트 트래픽 전송 가능

### ▶ 단점

❌ 암호화 기능이 없음 (보안 취약)  
❌ 추가적인 오버헤드 발생 (GRE + IP 헤더 증가)  
❌ 패킷 필터링 및 방화벽 설정 필요 (IP 프로토콜 47 허용 필요)

---

## 7. 결론

* **GRE는 다양한 프로토콜을 캡슐화할 수 있는 강력한 터널링 기술이지만, 보안 기능이 부족하므로 IPsec과 함께 사용하는 것이 일반적**

* **멀티캐스트, 동적 라우팅 프로토콜을 사용할 경우 GRE 터널이 적합**

* **보안이 필요한 경우 GRE over IPsec을 고려해야 함**

---