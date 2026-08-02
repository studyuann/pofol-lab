---
title: "SQS를 활용한 아키텍처 설계 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "모범사례기반 AWS 고급아키텍처 설계"]
is_public: true
draft: false
---

# SQS를 활용한 아키텍처 설계 실습

# 1. 실습 개요

## 1.1 실습 주제

사용자가 웹 애플리케이션에 요청을 보내면

애플리케이션이 요청을 즉시 모두 처리하지 않고

**Amazon SQS에 작업 메시지를 적재**한 뒤

별도의 **Worker 서버가 메시지를 가져가서 처리**하는 구조를 구현한다.

이 구조는 AWS 아키텍처 모범사례에서 자주 사용하는 방식이다.

예를 들면 다음과 같은 업무에 적합하다.

* 이미지 변환

* 이메일 발송

* 주문 처리

* 로그 후처리

* 배치성 작업

* 외부 API 호출

* 보고서 생성

---

## 1.2 실습 목표

본 실습을 통해 다음을 이해한다.

* SQS를 이용한 비동기 아키텍처 구성

* 웹 서버와 작업 처리 서버의 역할 분리

* Auto Scaling 환경에서의 웹 계층 설계

* Worker 계층의 메시지 Polling 구조

* SQS Visibility Timeout 개념

* Dead Letter Queue 구성

* 장애 시 메시지 유실 방지 구조

* CloudWatch를 통한 큐 모니터링

---

## 1.3 실습 아키텍처

```
User
  ↓
ALB
  ↓
Web EC2 (Auto Scaling Group)
  ↓
Amazon SQS (Main Queue)
  ↓
Worker EC2
  ↓
처리 결과 로그 / DB 저장 / 파일 저장
```

확장 구조는 다음과 같이 볼 수 있다.

```
User
  ↓
Application Load Balancer
  ↓
Auto Scaling Group (Web Tier)
  ↓
SQS Standard Queue
  ↓
Worker Tier (1대 이상)
  ↓
RDS 또는 S3 또는 DynamoDB
```

---

# 2. 왜 SQS를 사용하는가

웹 서버가 모든 작업을 직접 처리하면 다음 문제가 발생한다.

* 사용자 응답 시간이 길어짐

* 순간 트래픽 증가 시 웹 서버 부하 급증

* 긴 작업 때문에 타임아웃 발생 가능

* 일부 작업 실패 시 전체 요청 품질 저하

* 시스템 결합도 증가

이때 SQS를 사용하면 다음 장점이 생긴다.

* 요청 접수와 실제 처리 분리 가능

* 웹 계층은 빠르게 응답 가능

* Worker 수를 늘려 처리량 확장 가능

* 메시지 기반 재처리 가능

* 장애 격리 가능

* 서비스 간 느슨한 결합 가능

즉, SQS는 **탄력성, 확장성, 내결함성**을 높이는 핵심 구성요소다.

---

# 3. 실습 시나리오

이번 실습에서는 사용자가 웹 페이지에서 작업 요청을 등록하면

Web 서버가 이 작업을 SQS에 넣고

Worker 서버가 큐에서 메시지를 가져가 처리하는 구조를 만든다.

예시 업무는 다음처럼 가정한다.

* 사용자가 `/submit` 요청 전송

* 요청 내용: `report-001`, `image-task-001`, `order-1001`

* Web 서버는 요청을 SQS에 넣고 즉시 응답

* Worker 서버는 SQS에서 메시지를 받아 10초 동안 처리하는 것으로 가정

* 처리 완료 후 로그 파일 기록

---

# 4. 실습 구성 요소

## 4.1 AWS 서비스

* VPC

* Public Subnet

* Private Subnet

* Internet Gateway

* NAT Gateway 또는 실습 편의상 Public Worker

* EC2

* Auto Scaling Group

* Application Load Balancer

* Amazon SQS

* IAM Role

* CloudWatch

---

## 4.2 인스턴스 역할

| 구성 요소 | 역할 |
| --- | --- |
| ALB | 사용자 요청 분산 |
| Web EC2 | 사용자 요청 수신, SQS에 메시지 전송 |
| Worker EC2 | SQS 메시지 수신 및 작업 처리 |
| SQS Main Queue | 비동기 작업 적재 |
| SQS DLQ | 반복 실패 메시지 보관 |

---

# 5. 실습 전제

## 5.1 네트워크 구성

실습 단순화를 위해 다음처럼 구성한다.

| 자원 | 예시 |
| --- | --- |
| VPC | 10.0.0.0/16 |
| Public Subnet A | 10.0.1.0/24 |
| Public Subnet C | 10.0.2.0/24 |
| Private Subnet A | 10.0.11.0/24 |
| Private Subnet C | 10.0.12.0/24 |

권장 구성은 다음과 같다.

* ALB: Public Subnet

* Web EC2: Private Subnet

* Worker EC2: Private Subnet

* NAT Gateway: Public Subnet

다만 실습 난이도를 낮추기 위해

Web과 Worker를 Public Subnet에 두고 시작해도 됨.

최종적으로는 Private Subnet 배치가 모범사례에 더 적합하다.

---

# 6. 실습 전체 흐름

1. SQS Main Queue 생성

2. Dead Letter Queue 생성

3. IAM Role 생성

4. Web 서버 구축

5. Worker 서버 구축

6. ALB 구성

7. Web 서버를 Auto Scaling Group으로 확장

8. 요청 전송

9. SQS 메시지 적재 확인

10. Worker 처리 확인

11. DLQ 동작 확인

12. CloudWatch 모니터링 확인

---

# 7. SQS Queue 생성

# 7.1 Dead Letter Queue 생성

먼저 실패 메시지를 저장할 DLQ를 생성한다.

AWS Console 기준

```
Amazon SQS → Create queue
```

설정

```
Type: Standard
Name: app-task-dlq
```

생성 완료

---

# 7.2 Main Queue 생성

다시 Queue 생성

설정

```
Type: Standard
Name: app-task-queue
Visibility timeout: 30 seconds
Message retention period: 4 days
Delivery delay: 0 seconds
Receive message wait time: 10 seconds
```

### Redrive policy 설정

```
Dead-letter queue: app-task-dlq
Maximum receives: 3
```

설명

* **Visibility timeout**: Worker가 메시지를 가져간 뒤 일정 시간 동안 다른 소비자에게 보이지 않게 하는 시간

* **Message retention**: 메시지를 큐에 보관하는 최대 시간

* **Receive message wait time**: Long Polling 시간

* **Maximum receives**: 처리 실패가 3번 누적되면 DLQ로 이동

---

# 8. IAM Role 생성

SQS를 사용하려면 EC2가 SQS에 접근할 권한이 필요하다.

---

## 8.1 Web 서버용 Role

IAM → Roles → Create role

신뢰할 엔터티

```
AWS service → EC2
```

권한 정책 예시 이름

```
WebServerSQSRole
```

인라인 정책 또는 커스텀 정책 추가

```
{
  "Version":"2012-10-17",
  "Statement": [
    {
      "Sid":"SendMessageToQueue",
      "Effect":"Allow",
      "Action": [
           "sqs:SendMessage",
           "sqs:GetQueueUrl",
           "sqs:GetQueueAttributes"
      ],
      "Resource":"arn:aws:sqs:ap-northeast-2:계정ID:app-task-queue"
    }
  ]
}
```

---

## 8.2 Worker 서버용 Role

역할 이름 예시

```
WorkerSQSRole
```

권한 정책

```
{
  "Version":"2012-10-17",
  "Statement": [
    {
      "Sid":"ConsumeMessagesFromQueue",
      "Effect":"Allow",
      "Action": [
         "sqs:ReceiveMessage",
         "sqs:DeleteMessage",
         "sqs:ChangeMessageVisibility",
         "sqs:GetQueueUrl",
         "sqs:GetQueueAttributes"
      ],
      "Resource":"arn:aws:sqs:ap-northeast-2:계정ID:app-task-queue"
    }
  ]
}
```

---

# 9. Security Group 구성

## 9.1 ALB Security Group

인바운드

```
TCP 80  0.0.0.0/0
```

아웃바운드

```
All traffic
```

---

## 9.2 Web EC2 Security Group

인바운드

```
TCP 80  ALB Security Group
TCP 22  내 공인 IP
```

아웃바운드

```
All traffic
```

---

## 9.3 Worker EC2 Security Group

인바운드

```
TCP 22  내 공인 IP
```

아웃바운드

```
All traffic
```

Worker는 일반적으로 외부에서 직접 접근받지 않으므로

애플리케이션 포트 오픈이 필요하지 않음.

---

# 10. Web 서버 구축

이번 실습에서는 Python Flask 애플리케이션으로

사용자 요청을 받아 SQS에 메시지를 넣도록 구성한다.

---

## 10.1 Web EC2 생성

예시

```
AMI: Amazon Linux 2023
Type: t3.micro
IAM Role: WebServerSQSRole
Security Group: Web EC2 SG
```

---

## 10.2 패키지 설치

EC2 접속 후 실행

```
sudo dnf update -y
sudo dnf install -y python3 python3-pip
pip3 install flask boto3
```

설명

* `python3`: 파이썬 런타임

* `python3-pip`: 파이썬 패키지 관리자

* `flask`: 웹 애플리케이션 프레임워크

* `boto3`: AWS SDK for Python

---

## 10.3 애플리케이션 파일 작성

```
mkdir -p ~/sqs-web
cd ~/sqs-web
vi app.py
```

다음 내용 입력

```
from flask import Flask, request, jsonify, render_template_string
import boto3
import json
import os
from datetime import datetime

app = Flask(__name__)

# --- 설정 (환경 변수 사용 권장) ---
REGION = "ap-northeast-2"
# AWS 콘솔에서 복사한 실제 URL로 교체하세요.
QUEUE_URL = os.getenv("SQS_QUEUE_URL", "https://sqs.ap-northeast-2.amazonaws.com/계정ID/app-task-queue")

# Boto3 클라이언트 초기화
# 로컬 테스트 시에는 AWS CLI 설정을 따르거나 액세스 키를 주입해야 합니다.
sqs = boto3.client("sqs", region_name=REGION)

@app.route("/")
def index():
    # 간단한 HTML 템플릿 (가독성을 위해 멀티라인 문자열 사용)
    return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head><title>SQS Async Task Demo</title></head>
        <body>
            <h1>SQS 비동기 작업 데모</h1>
            <p>메시지를 입력하면 SQS 큐로 전송됩니다.</p>
            <form action="/submit" method="post">
                <input type="text" name="task_name" placeholder="작업명 입력" required />
                <button type="submit">큐로 전송</button>
            </form>
        </body>
        </html>
    """)

@app.route("/submit", methods=["POST"])
def submit():
    # 1. 입력값 검증
    task_name = request.form.get("task_name")
    if not task_name:
        return jsonify({"error": "task_name이 누락되었습니다."}), 400

    # 2. 메시지 본문 생성
    message_body = {
        "task_name": task_name,
        "requested_at": datetime.utcnow().isoformat() + "Z", # UTC 명시
        "source": "web-app"
    }

    try:
        # 3. SQS 메시지 전송
        response = sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(message_body)
        )
        
        # 4. 결과 반환
        return jsonify({
            "status": "success",
            "message": "메시지가 성공적으로 큐에 담겼습니다.",
            "details": {
                "task_name": task_name,
                "message_id": response.get("MessageId"),
                "md5": response.get("MD5OfMessageBody")
            }
        }), 200

    except Exception as e:
        # AWS 연결 오류 또는 권한 오류 발생 시 처리
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    # 포트 80은 리눅스에서 root 권한이 필요할 수 있습니다. 
    # 로컬 테스트라면 5000번 등을 권장합니다.
    app.run(host="0.0.0.0", port=80, debug=True)
```

---

## 10.4 코드 설명

### `boto3.client("sqs")`

AWS SDK를 통해 SQS API를 호출하는 객체를 만든다.

### `QUEUE_URL`

메시지를 보낼 대상 큐 주소다.

SQS에서 Queue 상세 화면에 들어가면 확인 가능하다.

### `/submit`

사용자가 작업명을 입력하면

이 값을 JSON 형태 메시지로 만들어 SQS에 넣는다.

### `send_message()`

SQS에 실제 메시지를 적재하는 핵심 함수다.

주요 인자

* `QueueUrl`: 대상 큐

* `MessageBody`: 보낼 메시지 본문

---

## 10.5 앱 실행

```
sudo python3 app.py
```

브라우저에서 인스턴스 Public IP로 접속해도 되지만

최종적으로는 ALB 뒤에 둘 것이므로 ALB 구성 후 확인하는 것이 좋다.

---

## 10.6 systemd 서비스 등록

실습 중 재부팅 후 자동 실행되도록 서비스 등록한다.

```
sudovi /etc/systemd/system/sqs-web.service
```

내용 입력

```
[Unit]
Description=Flask SQS Web App
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/sqs-web
ExecStart=/usr/bin/python3 /home/ec2-user/sqs-web/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

적용

```
sudo systemctl daemon-reload
sudo systemctl enable sqs-web
sudo systemctlstart sqs-web
sudo systemctl status sqs-web
```

---

# 11. Worker 서버 구축

Worker는 큐에서 메시지를 계속 Polling 하다가 메시지가 있으면 가져와 작업을 수행한 뒤

정상 처리되면 메시지를 삭제한다.

---

## 11.1 Worker EC2 생성

예시

```
AMI: Amazon Linux 2023
Type: t3.micro
IAM Role: WorkerSQSRole
Security Group: Worker EC2 SG
```

---

## 11.2 패키지 설치

```
sudo dnf update -y
sudo dnf install -y python3 python3-pip
pip3 install boto3
```

---

## 11.3 Worker 코드 작성

```
mkdir-p ~/sqs-worker
cd ~/sqs-worker
vi worker.py
```

다음 내용 입력

```
import boto3
import json
import time
import os
from datetime import datetime

# --- 설정 ---
REGION = "ap-northeast-2"
# 환경 변수 사용을 권장하며, 없을 경우 기본값 사용
QUEUE_URL = os.getenv("SQS_QUEUE_URL", "https://sqs.ap-northeast-2.amazonaws.com/계정ID/app-task-queue")

# SQS 클라이언트 생성
sqs = boto3.client("sqs", region_name=REGION)

def process_task(task_data):
    """
    메시지를 실제 처리하는 로직 (비즈니스 로직)
    """
    task_name = task_data.get("task_name", "unknown")
    print(f"[{datetime.now()}] 🚀 작업 시작: {task_name}")
    
    # 작업 처리 시뮬레이션 (10초 소요)
    # 이 시간이 Visibility Timeout(30초)보다 길어지면 메시지가 다시 큐에 보입니다.
    time.sleep(10) 
    
    print(f"[{datetime.now()}] ✅ 작업 완료: {task_name}")

def start_worker():
    print(f"[{datetime.now()}] SQS 워커 시작... (Queue: {QUEUE_URL})")
    
    while True:
        try:
            # 1. 메시지 수신 (Long Polling 적용)
            response = sqs.receive_message(
                QueueUrl=QUEUE_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20,     # 최대 20초까지 대기 (비용 절감 및 효율성)
                VisibilityTimeout=30    # 처리 중 다른 곳에서 안 보이게 하는 시간
            )

            messages = response.get("Messages", [])

            if not messages:
                print(f"[{datetime.now()}] 😴 새로운 메시지 없음. 다시 대기...")
                continue

            for message in messages:
                receipt_handle = message["ReceiptHandle"]
                
                try:
                    # JSON 파싱 에러 대비
                    body = json.loads(message["Body"])
                    
                    # 2. 작업 처리
                    process_task(body)

                    # 3. 처리 완료 후 메시지 삭제 (중요: 삭제 안 하면 다시 나타남)
                    sqs.delete_message(
                        QueueUrl=QUEUE_URL,
                        ReceiptHandle=receipt_handle
                    )
                    print(f"[{datetime.now()}] 🗑️ 메시지 처리 및 삭제 완료")

                except json.JSONDecodeError:
                    print(f"[{datetime.now()}] ❌ 잘못된 메시지 형식입니다.")
                except Exception as e:
                    print(f"[{datetime.now()}] ⚠️ 처리 중 오류 발생: {str(e)}")
                    # 여기서 에러가 나면 delete_message가 호출되지 않으므로,
                    # VisibilityTimeout이 지나면 자동으로 다시 큐에 나타나거나 DLQ로 이동합니다.

        except Exception as global_e:
            print(f"[{datetime.now()}] 🚨 네트워크 또는 시스템 오류: {str(global_e)}")
            time.sleep(5)  # 오류 발생 시 잠시 쉬었다가 재시도

if __name__ == "__main__":
    start_worker()
```

---

## 11.4 코드 설명

### `receive_message()`

SQS에서 메시지를 가져오는 함수다.

주요 옵션 설명

* `MaxNumberOfMessages=1`
  + 한 번에 1개 메시지만 가져옴

* `WaitTimeSeconds=10`
  + Long Polling 10초
  + 메시지가 없으면 즉시 빈 응답하지 않고 최대 10초 기다림

* `VisibilityTimeout=30`
  + 이 Worker가 메시지를 가져간 후 30초간 다른 Worker에게 보이지 않음

### `ReceiptHandle`

메시지를 삭제할 때 필요한 식별값이다.

메시지 본문이 아니라 **수신 시점의 고유 핸들**을 사용한다.

### `delete_message()`

작업이 정상 완료된 뒤 메시지를 큐에서 제거한다.

이 삭제를 하지 않으면 Visibility Timeout이 끝난 뒤 메시지가 다시 나타난다.

---

## 11.5 실행

```
python3 worker.py
```

정상이라면 메시지가 없을 때 다음과 비슷한 로그가 반복된다.

```
[2026-04-06 10:10:00] No messages available
```

---

## 11.6 systemd 등록

```
sudovi /etc/systemd/system/sqs-worker.service
```

내용

```
[Unit]
Description=SQS Worker Service
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/sqs-worker
ExecStart=/usr/bin/python3 /home/ec2-user/sqs-worker/worker.py
Restart=always

[Install]
WantedBy=multi-user.target
```

적용

```
sudo systemctl daemon-reload
sudo systemctl enable sqs-worker
sudo systemctlstart sqs-worker
sudo systemctl status sqs-worker
```

로그 확인

```
journalctl-u sqs-worker-f
```

---

# 12. ALB 구성

## 12.1 Target Group 생성

```
EC2 → Target Groups → Create target group
```

설정

```
Target type: Instances
Protocol: HTTP
Port: 80
Health check path: /
```

Web EC2 등록

---

## 12.2 ALB 생성

```
EC2 → Load Balancers → Create Application Load Balancer
```

설정

```
Scheme: Internet-facing
Listener: HTTP 80
Subnets: Public Subnet 2개 이상
Security Group: ALB SG
Target Group: 앞에서 생성한 Web TG
```

생성 후 ALB DNS 이름 확인

예

```
myapp-alb-123456.ap-northeast-2.elb.amazonaws.com
```

---

# 13. Web 서버 Auto Scaling Group 구성

---

## 13.1 Launch Template 생성

```
EC2 → Launch Templates → Create launch template
```

설정

* AMI: Web EC2와 동일

* Instance type: t3.micro

* IAM Role: WebServerSQSRole

* Security Group: Web EC2 SG

User Data에 애플리케이션 자동 설치 스크립트를 넣으면 더 좋다.

예시 User Data

```
#!/bin/bash
dnf update -y
dnf install -y python3 python3-pip
pip3 install flask boto3

mkdir -p /home/ec2-user/sqs-web

cat > /home/ec2-user/sqs-web/app.py<< 'EOF'
from flask import Flask, request, jsonify, render_template_string
import boto3
import json
import os
from datetime import datetime

app = Flask(__name__)

# --- 설정 (환경 변수 사용 권장) ---
REGION = "ap-northeast-2"
# AWS 콘솔에서 복사한 실제 URL로 교체하세요.
QUEUE_URL = os.getenv("SQS_QUEUE_URL", "https://sqs.ap-northeast-2.amazonaws.com/계정ID/app-task-queue")

# Boto3 클라이언트 초기화
# 로컬 테스트 시에는 AWS CLI 설정을 따르거나 액세스 키를 주입해야 합니다.
sqs = boto3.client("sqs", region_name=REGION)

@app.route("/")
def index():
    # 간단한 HTML 템플릿 (가독성을 위해 멀티라인 문자열 사용)
    return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head><title>SQS Async Task Demo</title></head>
        <body>
            <h1>SQS 비동기 작업 데모</h1>
            <p>메시지를 입력하면 SQS 큐로 전송됩니다.</p>
            <form action="/submit" method="post">
                <input type="text" name="task_name" placeholder="작업명 입력" required />
                <button type="submit">큐로 전송</button>
            </form>
        </body>
        </html>
    """)

@app.route("/submit", methods=["POST"])
def submit():
    # 1. 입력값 검증
    task_name = request.form.get("task_name")
    if not task_name:
        return jsonify({"error": "task_name이 누락되었습니다."}), 400

    # 2. 메시지 본문 생성
    message_body = {
        "task_name": task_name,
        "requested_at": datetime.utcnow().isoformat() + "Z", # UTC 명시
        "source": "web-app"
    }

    try:
        # 3. SQS 메시지 전송
        response = sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(message_body)
        )
        
        # 4. 결과 반환
        return jsonify({
            "status": "success",
            "message": "메시지가 성공적으로 큐에 담겼습니다.",
            "details": {
                "task_name": task_name,
                "message_id": response.get("MessageId"),
                "md5": response.get("MD5OfMessageBody")
            }
        }), 200

    except Exception as e:
        # AWS 연결 오류 또는 권한 오류 발생 시 처리
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    # 포트 80은 리눅스에서 root 권한이 필요할 수 있습니다. 
    # 로컬 테스트라면 5000번 등을 권장합니다.
    app.run(host="0.0.0.0", port=80, debug=True)
EOF

cat > /etc/systemd/system/sqs-web.service<< 'EOF'
[Unit]
Description=Flask SQS Web App
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/sqs-web
ExecStart=/usr/bin/python3 /home/ec2-user/sqs-web/app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable sqs-web
systemctl start sqs-web
```

---

## 13.2 Auto Scaling Group 생성

설정 예시

```
Desired capacity: 2
Minimum capacity: 2
Maximum capacity: 4
Subnets: Private 또는 Public 2개 AZ
Attach to existing load balancer: Web Target Group 선택
```

이 구성으로 웹 계층은 다중 AZ 기반으로 확장 가능해진다.

---

# 14. 동작 확인

## 14.1 ALB 접속

브라우저에서 다음 접속

```
http://ALB-DNS
```

입력창에 작업명 입력

예

```
order-1001
```

전송 버튼 클릭

---

## 14.2 응답 확인

정상이라면 브라우저에서 JSON 응답 확인 가능

예

```
{
  "message":"Task submitted successfully",
  "message_id":"xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "task_name":"order-1001"
}
```

중요한 점은

이 시점에서 실제 작업이 끝난 것이 아니라 **작업이 큐에 성공적으로 접수되었다는 것**이다.

즉, 사용자 응답 속도는 빨라지고 실제 무거운 작업은 뒤에서 처리하게 된다.

---

# 15. SQS 메시지 확인

SQS 콘솔에서 `app-task-queue` 선택 후 확인한다.

볼 수 있는 항목

* Available messages

* In flight messages

* Messages sent

* Messages received

* Messages deleted

설명

* **Available**: 아직 처리되지 않은 메시지

* **In flight**: Worker가 가져갔지만 아직 삭제되지 않은 메시지

* **Deleted**: 정상 처리 후 삭제된 메시지

---

# 16. Worker 로그 확인

Worker EC2 접속 후

```
journalctl -u sqs-worker -f
```

정상 처리 시 예시 로그

```
[2026-04-06 10:30:01] Processing task: order-1001
[2026-04-06 10:30:11] Completed task: order-1001
[2026-04-06 10:30:11] Message deleted successfully
```

이 로그 흐름은 아주 중요하다.

1. 메시지 수신

2. 작업 처리

3. 성공 시 삭제

이 3단계가 비동기 메시지 처리의 기본 패턴이다.

---

# 17. 실패 시나리오 실습

이번에는 일부 메시지를 실패시키고 DLQ로 이동하는 것을 확인해본다.

---

## 17.1 Worker 코드 수정

`worker.py`의 `process_task()` 함수 수정

```
def process_task(task_data):
task_name=task_data.get("task_name","unknown")
print(f"[{datetime.now()}] Processing task:{task_name}")

if "fail" intask_name:
raiseException("Intentional failure for DLQ test")

time.sleep(10)
print(f"[{datetime.now()}] Completed task:{task_name}")
```

서비스 재시작

```
sudo systemctl restart sqs-worker
```

---

## 17.2 실패 작업 전송

브라우저에서 다음 입력

```
fail-task-001
```

전송

---

## 17.3 동작 설명

이 메시지는 Worker가 받을 때마다 예외 발생

따라서 다음 흐름으로 동작한다.

1. 메시지 수신

2. 처리 실패

3. 메시지 삭제 안 함

4. Visibility Timeout 종료 후 다시 보임

5. 다시 수신 후 실패

6. 최대 수신 횟수 초과 시 DLQ 이동

즉, 메시지가 사라지는 것이 아니라

반복 실패 후 별도 보관소인 DLQ로 이동한다.

---

## 17.4 DLQ 확인

SQS 콘솔에서 `app-task-dlq` 확인

실패 메시지가 이동한 것을 볼 수 있다.

이 구조는 운영 환경에서 아주 중요하다.

왜냐하면 실패 메시지를 버리지 않고 보존하기 때문이다.

운영자는 DLQ를 보고

* 어떤 데이터가 실패했는지

* 왜 실패했는지

* 재처리가 필요한지

를 판단할 수 있다.

---

# 18. CloudWatch 모니터링

## 18.1 SQS 기본 지표 확인

SQS 큐 상세 화면 또는 CloudWatch에서 확인 가능

주요 지표

* ApproximateNumberOfMessagesVisible

* ApproximateNumberOfMessagesNotVisible

* NumberOfMessagesSent

* NumberOfMessagesReceived

* NumberOfMessagesDeleted

---

## 18.2 해석 포인트

### Visible 메시지가 계속 증가한다

의미

* Web 서버는 계속 메시지를 넣고 있음

* Worker 처리 속도가 느리거나 Worker 수가 부족함

대응

* Worker 인스턴스 수 증가

* 처리 로직 최적화

* 메시지 크기 또는 처리 시간 점검

### Not Visible 메시지가 계속 많다

의미

* Worker가 메시지를 가져갔지만 처리 중이거나 삭제하지 못하고 있음

대응

* Visibility Timeout 적절성 검토

* Worker 장애 여부 확인

* 코드 예외 처리 확인

### DLQ 메시지가 증가한다

의미

* 특정 유형 메시지가 반복 실패하고 있음

대응

* 실패 원인 분석

* 재처리 전략 수립

* Poison Message 대응 로직 도입

---

# 19. 아키텍처 모범사례 관점에서 정리

## 19.1 왜 이 구조가 좋은가

### 1) 웹 계층과 작업 계층 분리

웹 서버는 빠른 응답에 집중

Worker는 무거운 작업 처리에 집중

역할 분리가 명확해짐

### 2) 확장성 향상

요청이 많아지면

* 웹 서버는 ALB + ASG로 확장

* Worker도 별도로 수평 확장 가능

즉, 각 계층을 독립적으로 확장 가능

### 3) 장애 격리

Worker 장애가 나더라도

웹 서버가 즉시 죽는 구조가 아님

웹 서버는 일단 메시지를 큐에 넣고 응답 가능

### 4) 내구성 확보

SQS는 메시지를 안정적으로 저장하므로

일시적인 Worker 장애 시에도 메시지 유실 가능성이 낮다.

### 5) 운영 관측성 향상

CloudWatch, DLQ를 통해

병목 구간과 실패 구간을 파악하기 쉬움

---

# 20. 실습 후 확장 과제

---

## 20.1 Worker Auto Scaling 적용

CloudWatch 경보를 기반으로

큐 메시지 수가 많아지면 Worker 인스턴스를 자동으로 늘리도록 구성 가능

예

* SQS Visible Messages > 20

* Worker ASG Scale Out

이 구조는 실제 운영 환경에서 자주 사용된다.

---

## 20.2 결과 저장소 추가

Worker 처리 결과를 다음 중 하나에 저장하도록 확장 가능

* Amazon RDS

* DynamoDB

* S3

예시 시나리오

* 주문 처리 결과를 RDS 저장

* 이미지 처리 결과를 S3 저장

* 이벤트 로그를 DynamoDB 저장

---

## 20.3 SNS 연계

작업 완료 후 SNS로 알림을 보내도록 확장 가능

예

* 이메일 발송

* 운영자 알림

* 후속 시스템 이벤트 전달

---

## 20.4 Lambda Consumer 구조로 변경

EC2 Worker 대신 Lambda가 SQS를 소비하게 만들 수도 있다.

이 경우 장점

* 서버 운영 부담 감소

* 이벤트 기반 자동 확장

* 관리 포인트 축소

---