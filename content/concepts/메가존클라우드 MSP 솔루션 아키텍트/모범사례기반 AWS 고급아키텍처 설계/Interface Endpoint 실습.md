---
title: "Interface Endpoint 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "모범사례기반 AWS 고급아키텍처 설계"]
is_public: true
draft: false
---

# Interface Endpoint 실습

## 프론트엔드 VPC와 백엔드 VPC 분리 후 PrivateLink로 연동하기

---

# 1. 실습 목표

이번 실습에서는 서로 다른 두 개의 VPC를 구성하고,

프론트엔드 서버가 백엔드 서버에 직접 노출 없이 접근할 수 있도록

**AWS PrivateLink**를 이용해 내부 연동 구조를 구현한다.

이 실습을 통해 다음 내용을 이해하는 것이 목적이다.

* VPC를 서비스 역할별로 분리하는 구조 이해

* Network Load Balancer 기반 Endpoint Service 구성

* Interface Endpoint 생성 및 Private DNS 동작 이해

* 프론트 서버와 백엔드 서버를 PrivateLink로 연결하는 방식 이해

* 백엔드 서버를 인터넷에 직접 공개하지 않는 아키텍처 이해

---

# 2. 실습 아키텍처

[![](Interface%20Endpoint%20%EC%8B%A4%EC%8A%B5/image.png)](Interface%20Endpoint%20%EC%8B%A4%EC%8A%B5/image.png)

## 2.1 구성 개요

* **VPC A**는 사용자 요청을 받는 프론트엔드 영역이다.

* **VPC B**는 실제 API를 제공하는 백엔드 영역이다.

* 백엔드 EC2는 외부에 직접 공개하지 않는다.

* 백엔드 앞단에 **NLB**를 배치한다.

* NLB를 기반으로 **Endpoint Service**를 생성한다.

* 프론트 VPC에서는 **Interface Endpoint**를 생성해 백엔드 서비스에 접속한다.

---

## 2.2 구성 정보

| 구성 요소 | 리전 | CIDR | 설명 |
| --- | --- | --- | --- |
| VPC A (프론트) | 동일 리전 | 10.10.0.0/16 | 사용자 접근 가능 |
| VPC B (백엔드) | 동일 리전 | 10.20.0.0/16 | 백엔드 API 서버 존재 |
| EC2 A (프론트) | VPC A | 10.10.1.10 | Nginx 또는 Flask 웹서버 |
| EC2 B (백엔드) | VPC B | 10.20.1.10 | HTTP API 서버 |
| NLB | VPC B | - | EC2 B 대상으로 설정 |
| Endpoint Service | VPC B | - | NLB 기반 |
| Interface Endpoint | VPC A | - | PrivateLink 소비자 |

---

## 2.3 보안 설정

| 인스턴스 | 포트 | 설명 |
| --- | --- | --- |
| EC2 B (백엔드) | 80 | Interface Endpoint에서 접근 허용 |
| EC2 A (프론트) | 22, 80 | SSH 및 웹 접근 허용 |

---

## 2.4 트래픽 흐름

| 구간 | 방식 |
| --- | --- |
| 사용자 → 프론트 EC2 | 인터넷을 통한 HTTP 또는 HTTPS |
| 프론트 EC2 → 백엔드 EC2 | PrivateLink Interface Endpoint 사용 |
| 백엔드 EC2 | NLB 뒤에서 동작, 직접 노출 없음 |

---

# 3. 실습 시나리오

사용자는 브라우저로 프론트엔드 EC2에 접속한다.

프론트엔드 EC2는 사용자의 요청을 받아

백엔드 API 서버로 요청을 전달한다.

이때 프론트엔드와 백엔드 간 연결은

VPC Peering이나 Transit Gateway가 아니라

**PrivateLink Interface Endpoint**를 통해 수행한다.

즉, 프론트 서버는

백엔드 VPC 전체에 접근하는 것이 아니라

오직 특정 서비스(Endpoint Service)에만 접속하게 된다.

이 구조는 다음 장점이 있다.

* 백엔드 네트워크 전체를 열 필요가 없음

* 서비스 단위로 접근 통제 가능

* 공급자/소비자 구조로 명확히 분리 가능

* 백엔드 서버 직접 노출 방지 가능

---

# 4. 사전 준비

실습 전 다음 항목을 준비한다.

* 동일 리전에 VPC 2개 생성

* 각 VPC에 서브넷 생성

* EC2 2대 생성

* SSH 접속 가능한 키 페어 준비

* Security Group 준비

예시 구성은 다음과 같이 잡으면 된다.

---

## 4.1 VPC A 생성

* 이름: `vpc-front`

* CIDR: `10.10.0.0/16`

서브넷 예시

* `10.10.1.0/24` : Public Subnet

---

## 4.2 VPC B 생성

* 이름: `vpc-back`

* CIDR: `10.20.0.0/16`

서브넷 예시

* `10.20.1.0/24` : Private 또는 내부 서비스용 Subnet

* NLB 배치를 위해 최소 1개 이상 서브넷 필요

* 운영 환경에서는 다중 AZ 구성이 일반적이지만 실습에서는 단일 AZ로 단순화해도 됨

---

# 5. 보안 그룹 설계

## 5.1 프론트엔드 EC2용 보안 그룹

이름 예시

* `sg-front-ec2`

인바운드 규칙

* SSH 22 : 실습 접속용

* HTTP 80 : 테스트용

아웃바운드 규칙

* 기본 전체 허용 또는 Endpoint 대상 허용

---

## 5.2 백엔드 EC2용 보안 그룹

이름 예시

* `sg-back-ec2`

인바운드 규칙

* HTTP 80 허용

여기서 중요한 점이 있다.

**Interface Endpoint는 소비자 VPC 쪽에 ENI를 생성한다.**

즉, 실제 백엔드 입장에서 들어오는 트래픽은

프론트 EC2의 원래 IP가 아니라

PrivateLink 연결 구조를 따라 전달된다.

실습에서는 보통 다음 두 방식 중 하나를 사용한다.

* 백엔드 EC2 인바운드에서 `10.10.0.0/16` 허용

* 또는 NLB/엔드포인트 경유 구조에 맞춰 필요한 보안 허용

다만 **NLB 자체에는 Security Group을 붙이지 않는 경우가 많다**는 점을 함께 설명하면 좋다.

학생들이 ALB와 NLB를 혼동하는 경우가 많기 때문이다.

실습 단순화를 위해 다음처럼 잡으면 된다.

* TCP 80 허용

* Source: `10.10.0.0/16`

---

# 6. 백엔드 EC2 구성

백엔드 EC2는 간단한 HTTP API 서버로 구성한다.

예를 들어 Flask를 사용해

`/` 요청이 오면 JSON 또는 텍스트를 반환하도록 만든다.

---

## 6.1 백엔드 EC2 접속

```
ssh -i mykey.pem ec2-user@<백엔드EC2-공인IP>
```

Ubuntu라면

```
ssh -i mykey.pem ubuntu@<백엔드EC2-공인IP>
```

---

## 6.2 Python 및 Flask 설치

Amazon Linux 계열 예시

```
sudo dnf install -y python3
pip3 install flask
```

Ubuntu 예시

```
sudo apt update
sudo apt install -y python3-pip python3.12-venv
mkdir backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install flask
```

---

## 6.3 백엔드 API 코드 작성

`app.py`

```
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def index():
    return jsonify({
        "message": "Hello from Backend API",
        "server": "EC2 B",
        "service": "privatelink-demo"
    })

@app.route("/health")
def health():
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```

---

## 6.4 백엔드 서버 실행

```
python3 app.py
```

또는 백그라운드 실행

```
nohup python3 app.py > /tmp/backend.log 2>&1 &
```

---

## 6.5 백엔드 동작 확인

백엔드 EC2 내부에서 테스트

```
curl http://localhost:8080/
```

예상 결과

```
{"message":"Hello from Backend API","server":"EC2 B","service":"privatelink-demo"}
```

---

# 7. Target Group 생성

이제 NLB가 백엔드 EC2를 바라보도록 Target Group을 만든다.

---

## 7.1 Target Group 생성

설정 예시

* Target type: Instances

* Protocol: TCP

* Port: 80

* VPC: `vpc-back`

여기서 설명 포인트는 다음과 같다.

* NLB는 4계층 로드밸런서다.

* HTTP 헤더 기반 라우팅이 아니라 TCP 레벨에서 전달한다.

* 따라서 백엔드 애플리케이션이 HTTP여도 NLB에서는 TCP 리스너를 쓰는 경우가 많다.

---

## 7.2 대상 등록

* EC2 B를 Target Group에 등록

* 포트 80 지정

헬스 체크는 기본값을 써도 되지만

실습에서는 `/health`를 별도로 확인하는 HTTP 기반으로 설명할 수도 있다.

다만 NLB 실습 단순화를 위해 기본 TCP 헬스 체크로 가도 무방하다.

---

# 8. NLB 생성

이제 백엔드 VPC에 NLB를 생성한다.

---

## 8.1 NLB 생성 설정

* Load Balancer 타입: Network Load Balancer

* Scheme: Internal

* VPC: `vpc-back`

* Subnet: 백엔드가 위치한 서브넷 선택

* Listener: TCP 80

* Target Group: 앞에서 만든 Target Group 연결

---

## 8.2 내부형 NLB를 사용하는 이유

여기서는 백엔드 서비스를 외부 인터넷에 공개할 필요가 없기 때문이다.

즉,

* 사용자는 직접 백엔드에 접속하지 않음

* 프론트 VPC만 소비자 역할을 수행함

* PrivateLink 제공용 NLB이므로 내부형 구성이 적합함

---

# 9. Endpoint Service 생성

이 단계가 PrivateLink 제공자(provider) 측 핵심이다.

---

## 9.1 Endpoint Service 생성

메뉴 예시

```
VPC → Endpoint Services → Create endpoint service
```

설정

* 대상 NLB 선택

* Acceptance required: 필요 시 활성화

* Private DNS name: 선택 사항

설명 포인트

* Endpoint Service는 PrivateLink에서 **서비스 제공자 역할**을 한다.

* 이 서비스는 NLB를 통해 실제 백엔드 인스턴스로 연결된다.

* 다른 VPC는 이 서비스에 대해 Interface Endpoint를 생성해 소비자가 된다.

---

## 9.2 허용할 Principal 설정

필요하면 특정 AWS 계정 또는 조직만 연결 가능하도록 제한할 수 있다.

실습에서는 같은 계정 내에서 수행하므로

간단히 진행할 수 있다.

같은 계정 내 실습이면

허용 작업이 비교적 단순하다.

---

# 10. Interface Endpoint 생성

이 단계는 프론트 VPC에서 수행한다.

---

## 10.1 Interface Endpoint 생성

메뉴 예시

```
VPC → Endpoints → Create endpoint
```

설정

* Type: Endpoint services that use NLBs and GWLBs

* Service name: 방금 생성한 Endpoint Service 선택

* VPC: `vpc-front`

* Subnet: 프론트엔드 EC2가 있는 서브넷 선택

* Security Group: Endpoint ENI에 적용할 SG 지정

---

## 10.2 Endpoint용 보안 그룹

이 보안 그룹은 Interface Endpoint ENI에 연결된다.

예시

* 인바운드 80 허용

* Source: 프론트 EC2 보안 그룹 또는 `10.10.0.0/16`

실습에서는 간단하게

* TCP 80

* Source: `10.10.0.0/16`

로 설정해도 된다.

---

## 10.3 Interface Endpoint의 의미

이 부분은 반드시 자세히 설명하는 것이 좋다.

Interface Endpoint를 생성하면

소비자 VPC 내부 서브넷에 **ENI(Elastic Network Interface)** 가 만들어진다.

즉, 프론트 VPC 안에

백엔드 서비스로 향하는 전용 네트워크 인터페이스가 생기는 것이다.

프론트 EC2는 이 ENI의 프라이빗 IP로 접속하고,

AWS 내부망을 통해 Endpoint Service → NLB → 백엔드 EC2 순서로 요청이 전달된다.

즉, 프론트 서버 입장에서는

백엔드가 마치 자기 VPC 안쪽에 있는 내부 서비스처럼 보이게 된다.

---

# 11. 프론트엔드 EC2 구성

프론트엔드 EC2는 사용자의 요청을 받고

백엔드 API를 호출한 결과를 보여주는 역할을 한다.

Nginx reverse proxy로 구성해도 되고

Flask에서 직접 백엔드 호출을 수행해도 된다.

여기서는 이해를 쉽게 하기 위해 Flask 예시로 작성한다.

---

## 11.1 프론트엔드 EC2 접속

```
ssh -i mykey.pem ec2-user@<프론트EC2-공인IP>
```

또는 Ubuntu

```
ssh -i mykey.pem ubuntu@<프론트EC2-공인IP>
```

---

## 11.2 Python 및 requests 설치

```
sudo dnf install -y python3
pip3 install flask requests
```

Ubuntu

```
sudo apt update
sudo apt install -y python3-pip
pip3 install flask requests
```

---

## 11.3 Interface Endpoint DNS 이름 확인

VPC 콘솔에서 Interface Endpoint를 생성하면

다음과 같은 전용 DNS 이름이 보인다.

예시 형태

```
vpce-xxxxxxxxxxxxxxxxx-abcdefg.vpce-svc-xxxxxxxx.ap-northeast-2.vpce.amazonaws.com
```

이 이름을 프론트 애플리케이션에서 백엔드 주소로 사용하면 된다.

---

## 11.4 프론트엔드 Flask 코드 작성

`frontend.py`

```
from flask import Flask
import requests

app = Flask(__name__)

BACKEND_URL = "http://<Interface-Endpoint-DNS>"

@app.route("/")
def index():
    try:
        r = requests.get(BACKEND_URL, timeout=3)
        return f"""
        <h1>Frontend Server</h1>
        <p>Backend Response:</p>
        <pre>{r.text}</pre>
        """
    except Exception as e:
        return f"""
        <h1>Frontend Server</h1>
        <p>Backend connection failed</p>
        <pre>{str(e)}</pre>
        """, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
```

---

## 11.5 프론트엔드 실행

```
sudo python3 frontend.py
```

또는 백그라운드 실행

```
sudo nohup python3 frontend.py > /tmp/frontend.log 2>&1 &
```

---

# 12. 테스트

## 12.1 프론트 서버 내부에서 테스트

프론트 EC2에 접속 후

```
curl http://<Interface-Endpoint-DNS>
```

정상이라면 백엔드 API 응답이 출력된다.

예시

```
{"message":"Hello from Backend API","server":"EC2 B","service":"privatelink-demo"}
```

---

## 12.2 사용자 브라우저에서 테스트

브라우저에서 프론트 EC2 공인 IP 접속

```
http://<프론트EC2-공인IP>
```

정상이라면 다음과 같은 구조로 보인다.

* Frontend Server

* Backend Response

* Hello from Backend API

즉, 사용자는 프론트 서버에만 접속했지만

실제로는 프론트 서버가 PrivateLink를 통해 백엔드와 통신한 결과를 보게 된다.

---

# 13. 동작 원리 정리

이 실습의 핵심은

**네트워크 전체를 연결하지 않고 서비스만 연결했다**는 점이다.

VPC Peering과 비교하면 차이가 분명하다.

---

## 13.1 VPC Peering과 차이

VPC Peering은 두 VPC를 네트워크 단위로 연결한다.

즉,

* 라우팅 테이블 설정 필요

* CIDR 충돌 고려 필요

* 상대 VPC의 여러 리소스에 접근 가능성 존재

반면 PrivateLink는 서비스 단위 연결이다.

즉,

* 특정 Endpoint Service만 접근 가능

* 소비자 VPC는 제공자 VPC 전체를 보지 못함

* 더 제한적이고 보안적인 구조 구성 가능

---

## 13.2 왜 NLB가 필요한가

PrivateLink는 Endpoint Service를 만들 때

백엔드 대상 앞단으로 **NLB**를 사용한다.

이유는 다음과 같다.

* 고정된 서비스 진입점 제공

* AWS 내부 PrivateLink 구조와 연동 가능

* 다수의 백엔드 타겟을 안정적으로 분산 가능

즉, NLB는 단순 로드밸런서 역할이 아니라

PrivateLink 서비스의 네트워크 진입점 역할도 수행한다.

---

# 14. 점검 포인트

---

## 14.1 백엔드 EC2에 직접 curl은 되는데 프론트에서 안 되는 경우

확인 항목

* 백엔드 Flask가 `0.0.0.0:80` 으로 실행 중인지

* Target Group에 EC2가 정상 등록되었는지

* Target Health가 healthy 인지

* 백엔드 보안 그룹에서 80 포트 허용했는지

* Interface Endpoint 보안 그룹이 올바른지

---

## 14.2 Interface Endpoint DNS로 접속이 안 되는 경우

확인 항목

* Endpoint가 `available` 상태인지

* Endpoint Service가 연결 승인을 요구하는 경우 승인했는지

* 올바른 DNS 이름을 사용했는지

* 프론트 EC2가 해당 Endpoint ENI에 네트워크 접근 가능한지

---

## 14.3 브라우저로 프론트는 보이는데 백엔드 응답이 실패하는 경우

확인 항목

* 프론트 Flask 코드의 `BACKEND_URL` 값 확인

* 프론트 서버에서 직접 curl 테스트 수행

* requests timeout 값 확인

* NLB 리스너와 Target Group 포트가 일치하는지 확인

---

# 15. 실습 완료 후 이해해야 할 핵심

이 실습이 끝난 뒤 반드시 정리해야 할 핵심은 다음과 같다.

1. 사용자 트래픽은 프론트엔드에만 도달함

2. 프론트엔드는 백엔드와 직접 네트워크 피어링 없이 통신함

3. 그 통신 통로가 PrivateLink Interface Endpoint임

4. 백엔드는 NLB 뒤에 숨겨져 직접 노출되지 않음

5. 서비스 제공자와 소비자 구조를 AWS 내부망에서 안전하게 구성할 수 있음

---

# 16. 최종 아키텍처 요약

```
[User]
   │
   │ HTTP/HTTPS
   ▼
[EC2 A - Frontend in VPC A]
   │
   │ PrivateLink
   ▼
[Interface Endpoint in VPC A]
   │
   │ AWS Private Network
   ▼
[Endpoint Service in VPC B]
   │
   ▼
[NLB in VPC B]
   │
   ▼
[EC2 B - Backend API]
```

---