---
title: "실습 AWS - GCP Static VPN 연결"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Google 쿠버네티스 아키텍처 설계 및 구축"]
is_public: true
draft: false
---

# 실습. AWS - GCP Static VPN 연결

## 개요

AWS와 GCP를 **IPsec VPN**으로 연결하고, **정적 라우팅(Static Routing)** 으로 양쪽 사설 대역이 통신되도록 구성한다.

실습의 핵심은 다음과 같다.

* AWS와 GCP에 서로 다른 사설 네트워크를 준비함

* AWS 쪽 VPN Gateway와 GCP 쪽 VPN Gateway를 연결함

* 터널을 통해 암호화된 통신 경로를 만듦

* BGP 없이 각 클라우드에 **상대편 CIDR에 대한 정적 경로를 직접 등록**함

* 실제로 사설 IP 기반 통신이 되는지 확인함

---

## 학습 목표

* AWS와 GCP 간 Static VPN 연결 흐름을 설명할 수 있음

* GCP VPN Gateway, External VPN Gateway, VPN Tunnel의 역할을 설명할 수 있음

* Static Routing 방식에서 왜 라우트를 직접 등록해야 하는지 설명할 수 있음

* AWS와 GCP 간 사설 대역 통신 확인 절차를 수행할 수 있음

* 이중 터널 구성의 목적을 설명할 수 있음

---

## 핵심 키워드

* Cloud VPN

* HA VPN Gateway

* External VPN Gateway

* VPN Tunnel

* Static Routing

* Route Table

* Traffic Selector

* Redundancy

* IPsec

* Pre-shared Key

---

[![](%EC%8B%A4%EC%8A%B5%20AWS%20-%20GCP%20Static%20VPN%20%EC%97%B0%EA%B2%B0/image.png)](%EC%8B%A4%EC%8A%B5%20AWS%20-%20GCP%20Static%20VPN%20%EC%97%B0%EA%B2%B0/image.png)

# 1. 실습에서 구성할 구조

이번 실습은 다음 구조를 기준으로 진행한다.

## GCP 측

* VPC: `gcp-vpc-main`

* Subnet: `10.20.1.0/24`

* VM 1대 배치

* HA VPN Gateway 생성

* External VPN Gateway 생성

* VPN Tunnel 2개 또는 4개 구성 가능

* Static Route 생성

## AWS 측

* VPC: `aws-vpc-main`

* Subnet: `10.10.1.0/24`

* EC2 1대 배치

* Virtual Private Gateway 또는 Transit Gateway 기반 Site-to-Site VPN 구성

* Customer Gateway 생성

* VPN Connection 생성

* Route Table에 정적 경로 등록

---

# 2. Static Routing 방식에서 고려할 점

상대방 네트워크 경로를 자동으로 학습하지 않음.

따라서 반드시 아래 작업이 필요하다.

* AWS는 `10.20.1.0/24` 대역으로 가는 경로를 VPN 쪽으로 직접 등록해야 함

* GCP는 `10.10.1.0/24` 대역으로 가는 경로를 VPN 터널 쪽으로 직접 등록해야 함

즉, Static Routing 방식은 다음처럼 이해하면 된다.

* **장점**
  + 구조가 단순함
  + 학습용 실습에 적합함
  + BGP ASN, peer IP, session 상태를 덜 신경 써도 됨

* **단점**
  + 경로가 자동 전파되지 않음
  + 광고 대역이 바뀌면 수동 수정해야 함
  + 운영 자동화 측면에서는 BGP보다 불편함

---

# 3. 실습 전 준비사항

## 3.1 CIDR 설계

대역이 겹치면 안 된다.

예시 구성:

* AWS VPC CIDR: `10.10.0.0/16`

* AWS Subnet CIDR: `10.10.1.0/24`

* GCP VPC CIDR: `10.20.0.0/16`

* GCP Subnet CIDR: `10.20.1.0/24`

## 3.2 테스트 대상 인스턴스

양쪽에 테스트용 인스턴스를 1대씩 준비한다.

* AWS EC2 Private IP 예시: `10.10.1.10`

* GCP VM Internal IP 예시: `10.20.1.10`

## 3.3 보안 설정

통신이 안 되는 가장 흔한 이유는 VPN 자체가 아니라 보안 정책이다.

확인해야 할 것:

* AWS Security Group

* AWS NACL

* AWS Route Table

* GCP Firewall Rule

* OS 방화벽

* ICMP 허용 여부

* TCP 테스트 포트 허용 여부

---

# 4. 전체 실습 흐름

이번 실습은 아래 순서로 진행한다.

1. AWS VPC와 EC2 준비

2. GCP VPC와 VM 준비

3. AWS Customer Gateway 생성

4. AWS VPN Gateway 연결

5. AWS Site-to-Site VPN 생성

6. AWS VPN 구성 파일 다운로드

7. GCP HA VPN Gateway 생성

8. GCP External VPN Gateway 생성

9. GCP VPN Tunnel 생성

10. GCP Static Route 생성

11. AWS Route Table에 정적 경로 반영

12. 터널 상태 확인

13. 사설 IP 통신 테스트

---

# 5. 실습 1. AWS 네트워크 준비

## 목적

AWS에서 VPN 연결 대상이 될 네트워크와 테스트 인스턴스를 준비한다.

## 구성 예시

* VPC 이름: `aws-vpc-main`

* CIDR: `10.10.0.0/16`

* Subnet: `10.10.1.0/24`

* EC2: Amazon Linux 2023, `t3.micro`

## 확인 포인트

* EC2가 정상 실행 중인지 확인

* EC2의 Private IP 확인

* AWS Route Table이 어떤 서브넷에 연결돼 있는지 확인

* 추후 GCP 대역으로 가는 라우트를 여기에 추가할 예정임

---

# 6. 실습 2. GCP 네트워크 준비

## 목적

GCP에서 VPN 연결 대상이 될 네트워크와 테스트 VM을 준비한다.

## 구성 예시

* VPC 이름: `gcp-vpc-main`

* 서브넷 이름: `gcp-subnet-seoul`

* 서브넷 CIDR: `10.20.1.0/24`

* 리전: `asia-northeast3`

* VM: e2-micro

## 예시 CLI

```
gcloud compute networks create gcp-vpc-main \
--subnet-mode=custom
```

```
gcloud compute networks subnets create gcp-subnet-seoul \
--network=gcp-vpc-main \
--region=asia-northeast3 \
--range=10.20.1.0/24
```

## 설명

* `networks create` 는 VPC를 생성하는 명령이다

* `--subnet-mode=custom` 은 자동 서브넷 생성이 아니라 직접 서브넷을 정의하겠다는 의미다

* `subnets create` 는 특정 리전에 서브넷을 만드는 명령이다

* `--range` 는 해당 서브넷에 사용할 CIDR 대역이다

---

# 7. 실습 3. GCP 테스트 VM 생성

## 예시 CLI

```
gcloud compute instances create gcp-test-vm \
--zone=asia-northeast3-a \
--machine-type=e2-micro \
--subnet=gcp-subnet-seoul \
--private-network-ip=10.20.1.10 \
--image-family=debian-12 \
--image-project=debian-cloud
```

## 설명

* `instances create` 는 VM 생성 명령이다

* `--subnet` 으로 어느 서브넷에 VM을 둘지 지정한다

* `--private-network-ip` 로 내부 IP를 고정해두면 이후 테스트가 편하다

* `--image-family`, `--image-project` 는 사용할 OS 이미지를 지정한다

---

# 8. 실습 4. GCP 방화벽 규칙 생성

## 목적

AWS에서 GCP VM으로 테스트할 수 있도록 ICMP 또는 TCP를 허용한다.

## 예시 CLI

```
gcloud compute firewall-rules create allow-aws-to-gcp-icmp \
--network=gcp-vpc-main \
--allow=icmp \
--source-ranges=10.10.0.0/16
```

```
gcloud compute firewall-rules create allow-aws-to-gcp-ssh \
--network=gcp-vpc-main \
--allow=tcp:22 \
--source-ranges=10.10.0.0/16
```

## 설명

* `firewall-rules create` 는 VPC 방화벽 규칙을 생성한다

* `-source-ranges` 는 허용할 출발지 대역이다

* 여기서는 AWS VPC 대역인 `10.10.0.0/16` 에서 오는 트래픽만 허용한다

* ICMP가 막혀 있으면 ping 테스트가 실패하므로 실습 편의를 위해 허용해두는 편이 좋다

---

# 9. 실습 5. AWS Customer Gateway 생성

## 목적

AWS가 GCP 쪽 VPN 장비를 외부 피어로 인식하도록 등록한다.

여기서 중요한 점은 **GCP HA VPN Gateway의 외부 IP** 를 알아야 한다는 점이다.

따라서 실제 구성 순서는 AWS부터 시작할 수도 있고, GCP VPN Gateway를 먼저 만들고 AWS에 반영할 수도 있다.

---

# 10. 실습 6. GCP HA VPN Gateway 생성

## 목적

GCP 측 VPN 종단점을 만든다.

## 예시 CLI

```
gcloud compute vpn-gateways create gcp-ha-vpn \
--network=gcp-vpc-main \
--region=asia-northeast3
```

## 설명

* `vpn-gateways create` 는 HA VPN Gateway 생성 명령이다

* `--network` 는 어느 VPC에 연결할지 지정한다

* `--region` 은 게이트웨이가 생성될 리전이다

* 생성 후에는 인터페이스 0, 1 이 존재하는 구조로 이해하면 된다

## 확인 명령

```
gcloud compute vpn-gateways describe gcp-ha-vpn \
--region=asia-northeast3
```

## 여기서 확인할 것

* 인터페이스 정보

* 외부 IP 주소

* 이후 AWS Customer Gateway 또는 VPN peer 설정에 사용할 값

# 11. 실습 7. AWS Site-to-Site VPN 생성

## 목적

AWS에서 GCP를 향하는 VPN 연결을 만든다.

## 콘솔에서 수행할 작업

1. **Virtual Private Gateway 생성**

2. 해당 VGW를 AWS VPC에 연결

3. **Customer Gateway 생성**
   * GCP HA VPN Gateway 외부 IP 사용

4. **Site-to-Site VPN Connection 생성**
   * 라우팅 옵션은 **Static**
   * 정적 라우트 대역에 `10.20.0.0/16` 또는 `10.20.1.0/24` 입력

## 설명 포인트

* 여기서 라우팅 옵션을 Dynamic으로 하지 않고 **Static** 으로 선택해야 한다

* AWS는 이 VPN을 통해 어느 목적지 대역으로 갈 것인지 알아야 하므로**정적 라우트 대역**을 수동 입력해야 한다

* VPN 연결이 생성되면 **터널 2개**가 자동으로 만들어진다

## AWS 구성 파일 다운로드

VPN Connection 생성 후 구성 파일을 다운로드한다.

여기서 확인할 정보:

* Tunnel 1 Outside IP

* Tunnel 2 Outside IP

* Pre-Shared Key

* 내부 터널 IP

* 라우팅 방식이 Static인지 여부

> Static Routing 방식에서는 BGP Peer IP, ASN 같은 정보는 핵심이 아니다.
>
> **Outside IP와 PSK** 가 가장 중요하다.

---

# 12. 실습 8. GCP External VPN Gateway 생성

## 목적

AWS 쪽 VPN 피어 정보를 GCP에 등록한다.

즉, GCP가 “내가 어떤 외부 VPN 장비와 연결할 것인가”를 알도록 만드는 단계다.

## 예시 CLI

```
gcloud compute external-vpn-gateways create aws-vpn-peer \
--interfaces=0=AWS_TUNNEL1_OUTSIDE_IP,1=AWS_TUNNEL2_OUTSIDE_IP \
--redundancy-type=TWO_IPS_REDUNDANCY
```

## 예시

```
gcloud compute external-vpn-gateways create aws-vpn-peer \
--interfaces=0=3.38.10.10,1=52.79.20.20 \
--redundancy-type=TWO_IPS_REDUNDANCY
```

## 설명

* `external-vpn-gateways create` 는 외부 VPN 장비를 GCP에 등록하는 명령이다

* `-interfaces` 는 상대편 터널 외부 IP를 인터페이스 번호와 함께 지정한다

* `0=IP주소,1=IP주소` 형식으로 입력한다

* `TWO_IPS_REDUNDANCY` 는 외부 피어가 이중 인터페이스를 가진 구성임을 의미한다

---

# 13. 실습 9. GCP VPN Tunnel 생성

## 목적

AWS가 제공한 두 개의 터널에 대해 GCP에서도 대응되는 터널을 생성한다.

Static Routing 방식이므로 **각 터널마다 원격 트래픽 대역(remote traffic selector)** 을 명시하는 것이 중요하다.

## 터널 1 생성 예시

```
gcloud compute vpn-tunnels create gcp-to-aws-tunnel-1 \
--region=asia-northeast3 \
--vpn-gateway=gcp-ha-vpn \
--interface=0 \
--peer-external-gateway=aws-vpn-peer \
--peer-external-gateway-interface=0 \
--shared-secret='AWS_TUNNEL1_PSK' \
--remote-traffic-selector=10.10.0.0/16
```

## 터널 2 생성 예시

```
gcloud compute vpn-tunnels create gcp-to-aws-tunnel-2 \
--region=asia-northeast3 \
--vpn-gateway=gcp-ha-vpn \
--interface=1 \
--peer-external-gateway=aws-vpn-peer \
--peer-external-gateway-interface=1 \
--shared-secret='AWS_TUNNEL2_PSK' \
--remote-traffic-selector=10.10.0.0/16
```

## 설명

* `vpn-tunnels create` 는 실제 IPsec 터널을 만드는 명령이다

* `--vpn-gateway` 는 GCP 쪽 HA VPN Gateway 이름이다

* `--interface` 는 GCP HA VPN Gateway의 어느 인터페이스를 사용할지 지정한다

* `--peer-external-gateway` 는 AWS 피어 정보를 담은 External VPN Gateway 리소스다

* `--peer-external-gateway-interface` 는 AWS 측 인터페이스 번호다

* `--shared-secret` 는 AWS 구성 파일의 pre-shared key 값이다

* `--remote-traffic-selector` 는 이 터널을 통해 도달할 원격 대역이다

### remote-traffic-selector가 중요한 이유

BGP를 쓰지 않기 때문에, GCP는 상대편 네트워크 대역을 자동 학습하지 않는다.

따라서 어떤 대역으로 가는 트래픽을 이 VPN 터널로 보낼 것인지 명시해야 한다.

---

# 14. 실습 10. GCP Static Route 생성

## 목적

GCP에서 AWS 대역으로 가는 트래픽이 VPN 터널을 타도록 라우트를 만든다.

## 예시 CLI

```
gcloud compute routes create route-to-aws-via-vpn1 \
--network=gcp-vpc-main \
--destination-range=10.10.0.0/16 \
--next-hop-vpn-tunnel=gcp-to-aws-tunnel-1 \
--next-hop-vpn-tunnel-region=asia-northeast3 \
--priority=1000
```

## 백업 라우트 예시

```
gcloud compute routes create route-to-aws-via-vpn2 \
--network=gcp-vpc-main \
--destination-range=10.10.0.0/16 \
--next-hop-vpn-tunnel=gcp-to-aws-tunnel-2 \
--next-hop-vpn-tunnel-region=asia-northeast3 \
--priority=1100
```

## 설명

* `routes create` 는 정적 라우트를 만드는 명령이다

* `--destination-range` 는 목적지 대역이다

* `--next-hop-vpn-tunnel` 은 이 목적지로 갈 때 사용할 VPN 터널이다

* `--priority` 값이 낮을수록 우선순위가 높다

* 따라서 `vpn1` 을 기본 경로로 쓰고, `vpn2` 를 보조 경로처럼 둘 수 있다

---

# 15. 실습 11. AWS Route Table 정적 경로 확인

## 목적

AWS에서도 GCP 대역으로 가는 트래픽이 VPN으로 전달되도록 해야 한다.

## 확인할 내용

AWS Route Table에 아래 경로가 있어야 한다.

* 목적지: `10.20.0.0/16` 또는 `10.20.1.0/24`

* 대상: Virtual Private Gateway 또는 VPN Connection 경유 경로

## 설명

AWS에서 Static VPN을 생성할 때 정적 라우트를 넣으면,

라우트 전파 또는 수동 반영 방식으로 VPC 라우트 테이블에 경로가 반영된다.

반드시 확인해야 한다.

### 확인 포인트

* EC2가 속한 서브넷의 라우트 테이블인지 확인

* GCP 대역이 VPN 대상으로 잡혀 있는지 확인

* Local, IGW, NAT 경로와 충돌하지 않는지 확인

---

# 16. 실습 12. 터널 상태 확인

## GCP에서 확인

```
gcloud compute vpn-tunnels describe gcp-to-aws-tunnel-1 \
--region=asia-northeast3
```

```
gcloud compute vpn-tunnels describe gcp-to-aws-tunnel-2 \
--region=asia-northeast3
```

## 확인 항목

* 상태가 `ESTABLISHED` 인지 확인

* peer IP가 예상한 AWS tunnel outside IP와 일치하는지 확인

* shared secret 오입력이 없는지 확인

## AWS에서 확인

AWS 콘솔에서 Site-to-Site VPN Connection 상세 화면으로 이동해서 본다.

확인 항목:

* Tunnel 1 상태

* Tunnel 2 상태

* UP / DOWN 여부

* Static route 상태

---

# 17. 실습 13. 통신 테스트 준비

ping외에, TCP 테스트도 같이 하는 것이 좋다.

## GCP VM에서 웹 서버 실행 예시

```
sudo apt update
sudo apt install -y nginx
sudo systemctl enable --now nginx
```

## AWS EC2에서 웹 서버 실행 예시

```
sudo dnf install -y nginx
sudo systemctl enable--now nginx
```

## 설명

* 한쪽에서 웹 서버를 띄워두면

* 반대편에서 `curl`, `telnet`, `nc` 같은 방식으로 실제 애플리케이션 레벨 테스트가 가능하다

* ICMP가 막혀도 TCP/HTTP 테스트는 가능하다

---

# 18. 실습 14. 실제 통신 테스트

## GCP VM → AWS EC2 테스트

```
ping 10.10.1.10
```

```
curl http://10.10.1.10
```

## AWS EC2 → GCP VM 테스트

```
ping 10.20.1.10
```

```
curl http://10.20.1.10
```

## 설명

* `ping` 은 ICMP 기반 확인이다

* `curl` 은 실제 TCP 80 포트와 HTTP 응답까지 확인할 수 있다

* 운영 환경에서는 ping이 차단된 경우도 많으므로 `curl` 테스트가 더 실무적이다

---

# 19. 장애가 날 때 우선 확인할 것

Static VPN 실습에서 자주 막히는 지점은 아래다.

## 19.1 PSK 불일치

AWS 구성 파일의 pre-shared key와 GCP 터널 생성 시 입력한 값이 다르면 터널이 올라오지 않는다.

## 19.2 peer interface 매핑 오류

* GCP interface 0 이 AWS tunnel 1 과 연결돼야 하는데

* 실수로 tunnel 2 값을 넣는 경우가 있음

이 경우 터널 상태가 이상하거나 통신이 안 될 수 있다.

## 19.3 GCP Static Route 누락

터널은 살아 있어도 GCP에 `10.10.0.0/16` 경로가 없으면 AWS로 패킷이 가지 않는다.

## 19.4 AWS Route Table 누락

반대로 AWS 라우트 테이블에 `10.20.0.0/16` 경로가 없으면 응답이 돌아오지 않는다.

## 19.5 방화벽 문제

* AWS Security Group에서 `10.20.0.0/16` 허용 안 됨

* GCP Firewall에서 `10.10.0.0/16` 허용 안 됨

* OS 방화벽이 열려 있지 않음

## 19.6 테스트 대역 불일치

실제로는 `10.20.1.0/24` 만 쓰는데

라우트는 `10.20.2.0/24` 로 넣어버린 경우 통신이 안 된다.

---

# 20. 이중 터널을 두는 이유

이번 실습은 Static Routing 기반이지만, 그래도 터널을 2개 두는 이유는 중요하다.

## 이유

* 한 터널 장애 시 다른 터널을 사용할 수 있음

* 단일 터널보다 가용성이 좋아짐

* 운영형 VPN 구조의 기본 감각을 익힐 수 있음

다만 BGP가 없기 때문에, 장애 전환은 BGP 기반 자동 전환보다 단순하지 않다.

그래도 GCP 쪽에서는 **우선순위가 다른 정적 라우트** 를 두어 기본/보조 경로 형태를 이해할 수 있다.

---

# 21. 실습 정리

이번 실습에서 한 작업은 다음과 같다.

* AWS VPC와 EC2 준비

* GCP VPC와 VM 준비

* AWS Site-to-Site VPN을 Static Routing으로 생성

* AWS 구성 파일에서 tunnel outside IP와 PSK 확인

* GCP HA VPN Gateway 생성

* GCP External VPN Gateway 생성

* GCP VPN Tunnel 생성

* GCP Static Route 생성

* AWS Route Table 정적 경로 확인

* 양쪽 VM 간 사설 IP 통신 테스트 수행

---

# 22. 핵심 정리

## 이번 실습의 핵심 포인트

* BGP 없이도 AWS와 GCP는 VPN으로 연결 가능함

* 이 경우 경로는 자동 교환되지 않음

* 따라서 양쪽에서 **상대 대역으로 가는 정적 라우트** 를 직접 넣어야 함

* 터널이 올라와 있어도 라우트와 방화벽이 맞지 않으면 통신되지 않음

* 실습에서는 ping보다 HTTP/TCP 테스트까지 같이 해야 실제 연결 여부를 더 정확히 판단할 수 있음

## 최종 결론

**Static Routing 기반 AWS-GCP VPN 실습은 멀티클라우드 사설 연결의 기본 구조를 가장 단순하게 익히는 방법이다.**