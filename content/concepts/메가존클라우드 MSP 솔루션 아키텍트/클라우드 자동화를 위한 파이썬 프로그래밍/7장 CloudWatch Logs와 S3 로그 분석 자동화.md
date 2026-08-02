---
title: "7장 CloudWatch Logs와 S3 로그 분석 자동화"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "클라우드 자동화를 위한 파이썬 프로그래밍"]
is_public: true
draft: false
---

# 7장. CloudWatch Logs와 S3 로그 분석 자동화

## 1. 과정 개요

기존 실습에서는 `/var/log`, 애플리케이션 로그 파일, 웹 서버 로그 파일처럼 **로컬 서버에 존재하는 로그파일**을 대상으로 분석 자동화를 수행했다. 이번 단원에서는 로그 저장 위치가 로컬 디스크가 아니라 AWS 클라우드 서비스로 확장된 상황을 다룬다.

AWS 환경에서는 로그가 주로 다음 위치에 저장된다.

| 로그 저장 위치 | 대표 예시 | 분석 방식 |
| --- | --- | --- |
| CloudWatch Logs | EC2, Lambda, ECS, API Gateway, 애플리케이션 로그 | AWS CLI, Logs Insights, boto3 |
| Amazon S3 | ALB 로그, CloudTrail 로그, S3 Access Log, 애플리케이션 백업 로그 | AWS CLI 다운로드, Python 분석, Athena SQL 분석 |
| S3 + Athena | 대용량 로그 분석 | SQL 기반 서버리스 분석 |
| CloudWatch Logs + Lambda | 실시간 이벤트 처리 | 자동 탐지, 알림, 후속 조치 |

CloudWatch Logs는 로그 그룹과 로그 스트림 단위로 로그를 저장하며, `filter-log-events` 명령을 이용해 로그 그룹의 이벤트를 조회하거나 필터링할 수 있다.

S3에 저장된 로그는 객체 형태로 저장되므로, 로컬로 다운로드해서 분석하거나 Athena를 이용해 S3 객체를 직접 SQL로 조회할 수 있다.

---

# 2. 학습 목표

1. CloudWatch Logs의 로그 그룹과 로그 스트림 구조를 이해한다.

2. AWS CLI로 CloudWatch Logs를 조회하고 필터링한다.

3. CloudWatch Logs Insights 쿼리를 CLI에서 실행한다.

4. S3에 저장된 로그를 로컬로 내려받아 Python으로 분석한다.

5. Athena를 이용해 S3 로그를 SQL로 분석한다.

6. CloudWatch Logs와 S3 로그 분석을 스크립트로 자동화한다.

7. 로그 분석 결과를 CSV, JSON, 요약 리포트 형태로 저장한다.

---

# 3. 사전 준비

## 3.1 실습 환경

다음 환경을 기준으로 실습한다.

| 항목 | 내용 |
| --- | --- |
| 운영체제 | Linux, macOS, Windows WSL |
| 도구 | AWS CLI v2, Python 3.10 이상 |
| AWS 서비스 | CloudWatch Logs, S3, Athena |
| 권한 | CloudWatch Logs 조회 권한, S3 읽기 권한, Athena 실행 권한 |

## 3.2 필요한 IAM 권한

실습 계정에는 최소한 다음 권한이 필요하다.

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
        "logs:FilterLogEvents",
        "logs:StartQuery",
        "logs:GetQueryResults"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetObject"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "athena:StartQueryExecution",
        "athena:GetQueryExecution",
        "athena:GetQueryResults",
        "glue:GetDatabase",
        "glue:GetTable",
        "glue:CreateTable"
      ],
      "Resource": "*"
    }
  ]
}
```

### 설명

`logs:FilterLogEvents`는 CloudWatch Logs에서 조건에 맞는 로그 이벤트를 조회할 때 필요하다.

`logs:StartQuery`와 `logs:GetQueryResults`는 CloudWatch Logs Insights 쿼리를 실행하고 결과를 가져올 때 사용한다. `start-query`는 로그 그룹과 시간 범위, 쿼리 문자열을 지정해 Logs Insights 쿼리를 시작하는 명령이고, `get-query-results`는 실행된 쿼리 결과를 조회하는 명령이다.

---

# 4. CloudWatch Logs 기본 구조

## 4.1 로그 그룹

로그 그룹은 관련 로그를 모아두는 최상위 단위다.

예를 들면 다음과 같다.

```
/aws/lambda/my-function
/aws/ecs/my-service
/application/nginx
/application/springboot
```

로그 그룹은 보통 서비스, 애플리케이션, 환경 단위로 구성한다.

예시:

```
/application/prod/web
/application/dev/api
/aws/lambda/order-function
```

## 4.2 로그 스트림

로그 스트림은 로그 그룹 안에서 실제 로그 이벤트가 시간 순서대로 쌓이는 단위다.

예를 들어 Lambda 함수의 경우 실행 환경별로 로그 스트림이 생성된다.

```
2026/04/28/[$LATEST]abcdef123456
2026/04/28/[$LATEST]fedcba654321
```

## 4.3 로그 이벤트

로그 이벤트는 실제 로그 한 줄 또는 하나의 로그 메시지다.

예시:

```
{
  "timestamp": 1777358400000,
  "message": "ERROR Failed to connect database",
  "logStreamName": "app-server-01"
}
```

---

# 5. CloudWatch Logs 분석 실습

## 5.1 로그 그룹 목록 조회

```
aws logs describe-log-groups
```

### 명령어 설명

| 구성 요소 | 의미 |
| --- | --- |
| `aws` | AWS CLI 실행 명령 |
| `logs` | CloudWatch Logs 서비스를 대상으로 함 |
| `describe-log-groups` | 현재 계정과 리전에 있는 로그 그룹 목록을 조회함 |

### 보기 좋은 형태로 출력

```
aws logs describe-log-groups \
  --query "logGroups[*].[logGroupName,storedBytes,retentionInDays]" \
  --output table
```

### 옵션 설명

| 옵션 | 설명 |
| --- | --- |
| `--query` | AWS CLI 결과에서 필요한 필드만 추출한다. JMESPath 문법을 사용한다 |
| `logGroups[*]` | 모든 로그 그룹을 대상으로 한다 |
| `logGroupName` | 로그 그룹 이름 |
| `storedBytes` | 저장된 로그 용량 |
| `retentionInDays` | 로그 보존 기간 |
| `--output table` | 결과를 표 형태로 출력한다 |

---

## 5.2 특정 로그 그룹의 로그 스트림 조회

```
aws logs describe-log-streams \
  --log-group-name "/aws/lambda/my-function" \
  --order-by LastEventTime \
  --descending \
  --max-items 10
```

### 명령어 설명

| 옵션 | 설명 |
| --- | --- |
| `--log-group-name` | 조회할 로그 그룹 이름을 지정한다 |
| `--order-by LastEventTime` | 마지막 이벤트 시간을 기준으로 정렬한다 |
| `--descending` | 최신 로그 스트림이 위에 오도록 내림차순 정렬한다 |
| `--max-items 10` | 최대 10개만 조회한다 |

이 명령은 최근에 로그가 발생한 스트림을 빠르게 찾을 때 사용한다.

---

## 5.3 CloudWatch Logs에서 ERROR 로그 조회

```
aws logs filter-log-events \
  --log-group-name "/application/prod/web" \
  --filter-pattern "ERROR" \
  --start-time 1772722800000 \
  --end-time 1777993199000
  
  시간 범위 지정: --start-time과 --end-time 옵션을 사용한다. (단위: 밀리초(ms) Unix Epoch Time)  예) 2026년 3월 1일 ~ 2026년 4월 30일
```

### 명령어 설명

| 옵션 | 설명 |
| --- | --- |
| `filter-log-events` | CloudWatch Logs 이벤트를 조회하고 필터링한다 |
| `--log-group-name` | 조회 대상 로그 그룹을 지정한다 |
| `--filter-pattern "ERROR"` | 로그 메시지에서 `ERROR`라는 문자열이 포함된 이벤트만 조회한다 |
| `--start-time` | 조회 시작 시간을 Unix epoch milliseconds 형식으로 지정한다 |
| `--end-time` | 조회 종료 시간을 Unix epoch milliseconds 형식으로 지정한다 |

`filter-log-events`는 필터 패턴, 시간 범위, 로그 스트림 이름 등을 기준으로 CloudWatch Logs 이벤트를 조회할 수 있다.

---

## 5.4 현재 시간 기준 최근 1시간 로그 조회

Linux/macOS 기준:

```
START_TIME=$(date -u -d '1 hour ago' +%s000)
END_TIME=$(date -u +%s000)

aws logs filter-log-events \
  --log-group-name "/application/prod/web" \
  --filter-pattern "ERROR" \
  --start-time "$START_TIME" \
  --end-time "$END_TIME" \
  --query "events[*].[timestamp,logStreamName,message]" \
  --output table
```

macOS에서 `date -d`가 동작하지 않는 경우:

```
START_TIME=$(python3 -c 'import time; print(int((time.time()-3600)*1000))')
END_TIME=$(python3 -c 'import time; print(int(time.time()*1000))')
```

### 핵심 설명

CloudWatch Logs CLI에서 시간은 일반적으로 **밀리초 단위 epoch time**을 사용한다.

예를 들어 다음 값은 초 단위가 아니라 밀리초 단위다.

```
1777358400000
```

Python에서 현재 시간을 밀리초로 구하려면 다음처럼 작성한다.

```
import time

now_ms = int(time.time() * 1000)
```

`time.time()`은 현재 시간을 초 단위로 반환한다. CloudWatch Logs CLI에 넣기 위해 `1000`을 곱해 밀리초 단위로 변환한다.

---

# 6. CloudWatch Logs Insights 분석

## 6.1 Logs Insights 개념

CloudWatch Logs Insights는 CloudWatch Logs에 저장된 로그를 쿼리 언어로 분석하는 기능이다.

단순 문자열 검색은 `filter-log-events`로도 가능하지만, 다음과 같은 분석은 Logs Insights가 더 적합하다.

| 분석 목적 | 예시 |
| --- | --- |
| 에러 건수 집계 | 5분 단위 ERROR 개수 |
| 응답 시간 통계 | 평균, 최대, 백분위수 |
| 특정 필드 추출 | JSON 로그에서 statusCode 추출 |
| Top N 분석 | 가장 많이 실패한 API 경로 |
| 시간대별 추이 | 시간별 5xx 오류 추이 |

CloudWatch Logs Insights 쿼리 문법은 `fields`, `filter`, `sort`, `limit` 같은 명령을 사용하며, 다양한 함수, 산술/비교 연산, 정규식을 지원한다.

---

## 6.2 기본 쿼리

```
fields @timestamp, @message
| sort @timestamp desc
| limit 20
```

### 쿼리 설명

| 구문 | 의미 |
| --- | --- |
| `fields @timestamp, @message` | 출력할 필드를 지정한다 |
| `sort @timestamp desc` | 최신 로그가 먼저 나오도록 정렬한다 |
| `limit 20` | 최대 20건만 출력한다 |

---

## 6.3 ERROR 로그만 조회

```
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 50
```

### 설명

`filter`는 조건에 맞는 로그 이벤트만 남긴다. `filter` 명령은 하나 이상의 조건과 일치하는 로그 이벤트를 가져올 때 사용한다.

---

## 6.4 5분 단위 ERROR 건수 집계

```
fields @timestamp, @message
| filter @message like /ERROR/
| stats count(*) as error_count by bin(5m) as time_group
| sort time_group desc
```

### 설명

| 구문 | 의미 |
| --- | --- |
| `filter @message like /ERROR/` | 메시지에 ERROR가 포함된 로그만 선택한다 |
| `stats count(*)` | 선택된 로그 개수를 집계한다 |
| `as error_count` | 집계 결과 컬럼명을 `error_count`로 지정한다 |
| `by bin(5m)` | 5분 단위 시간 구간으로 묶는다 |
| `sort bin(5m) desc` | 최신 시간 구간이 먼저 나오도록 정렬한다 |

---

# 7. AWS CLI로 Logs Insights 자동 실행

## 7.1 쿼리 실행

```
aws logs start-query \
  --log-group-name "/application/prod/web" \
  --start-time 1772722800000 \
  --end-time 1777993199000 \
  --query-string 'fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 20'
```

### 중요 차이

`filter-log-events`의 `--start-time`, `--end-time`은 **밀리초 단위**를 사용한다.

반면 `start-query` 명령의 `--start-time`, `--end-time`은 **초 단위 Unix timestamp**를 사용한다.

`start-query`는 로그 그룹, 시간 범위, 쿼리 문자열을 지정해 CloudWatch Logs Insights 쿼리를 시작한다. ([AWS Documentation](https://docs.aws.amazon.com/cli/latest/reference/logs/start-query.html?utm_source=chatgpt.com))

실행 결과 예시:

```
{
  "queryId": "12345678-aaaa-bbbb-cccc-1234567890ab"
}
```

---

## 7.2 쿼리 결과 조회

```
aws logs get-query-results \
  --query-id "12345678-aaaa-bbbb-cccc-1234567890ab"
```

### 명령어 설명

| 옵션 | 설명 |
| --- | --- |
| `get-query-results` | 실행된 Logs Insights 쿼리 결과를 조회한다 |
| `--query-id` | `start-query` 실행 결과로 받은 쿼리 ID를 지정한다 |

`get-query-results`는 쿼리를 새로 실행하지 않고, 이미 시작된 쿼리의 결과를 반환한다.

---

## 7.3 자동화 스크립트 예제

파일명:

```
cw_error_report.sh
```

```
#!/bin/bash

LOG_GROUP="/application/prod/web"

START_TIME=$(python3 -c 'import time; print(int(time.time()) - 3600)')
END_TIME=$(python3 -c 'import time; print(int(time.time()))')

QUERY='fields @timestamp, @message
| filter @message like /ERROR/
| stats count(*) as error_count by bin(5m)
| sort bin(5m) desc'

QUERY_ID=$(aws logs start-query \
  --log-group-name "$LOG_GROUP" \
  --start-time "$START_TIME" \
  --end-time "$END_TIME" \
  --query-string "$QUERY" \
  --query 'queryId' \
  --output text)

echo "Query ID: $QUERY_ID"

sleep 5

aws logs get-query-results \
  --query-id "$QUERY_ID" \
  --output json > cloudwatch_error_report.json

echo "결과 저장 완료: cloudwatch_error_report.json"
```

### 스크립트 설명

```
LOG_GROUP="/application/prod/web"
```

분석할 CloudWatch Logs 로그 그룹 이름을 변수로 저장한다.

```
START_TIME=$(python3 -c 'import time; print(int(time.time()) - 3600)')
```

현재 시간에서 3600초, 즉 1시간을 뺀 값을 구한다. Logs Insights `start-query`는 초 단위 timestamp를 사용하므로 `time.time()` 결과를 정수로 변환한다.

```
QUERY='fields @timestamp, @message ...'
```

실행할 Logs Insights 쿼리를 변수에 저장한다. 여러 줄 문자열로 작성해도 Bash에서 하나의 변수로 처리된다.

```
QUERY_ID=$(aws logs start-query ...)
```

Logs Insights 쿼리를 시작하고, 결과로 반환되는 `queryId`만 추출한다.

```
--query 'queryId'
--output text
```

AWS CLI 결과 중 `queryId` 필드만 텍스트로 출력한다. 이렇게 하면 이후 명령에서 바로 변수로 사용할 수 있다.

```
sleep 5
```

Logs Insights 쿼리는 비동기 방식으로 실행된다. 즉, `start-query`를 실행했다고 해서 결과가 즉시 준비되는 것은 아니다. 간단한 실습에서는 5초 정도 대기한 뒤 결과를 조회한다.

```
aws logs get-query-results --query-id "$QUERY_ID"
```

앞에서 실행한 쿼리의 결과를 가져온다.

---

# 8. Python boto3로 CloudWatch Logs 분석 자동화

## 8.1 boto3 설치

```
pip install boto3
```

## 8.2 Python 예제

파일명:

```
cloudwatch_logs_analyzer.py
```

```
import time
import json
import boto3

LOG_GROUP = "/application/prod/web"

client = boto3.client("logs")

# 현재 시간에서 한 시간전으로 범위 설정
# start_time = int(time.time()) - 3600
# end_time = int(time.time())
# 예) 2026년 3월 1일 ~ 2026년 4월 30일
start_time = int(1772722800000)
end_time = int(1777993199000)

query = """
fields @timestamp, @message
| filter @message like /ERROR/
| stats count(*) as error_count by bin(5m) as time_window
| sort time_window desc
"""

response = client.start_query(
    logGroupName=LOG_GROUP,
    startTime=start_time,
    endTime=end_time,
    queryString=query
)

query_id = response["queryId"]
print(f"Query ID: {query_id}")

while True:
    result = client.get_query_results(queryId=query_id)
    status = result["status"]

    if status in ["Complete", "Failed", "Cancelled", "Timeout"]:
        break

    print("쿼리 실행 중...")
    time.sleep(2)

with open("cloudwatch_error_report.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("분석 결과 저장 완료: cloudwatch_error_report.json")
```

### 코드 설명

```
import boto3
```

AWS SDK for Python인 boto3를 불러온다.

```
client = boto3.client("logs")
```

CloudWatch Logs API를 호출하기 위한 클라이언트를 생성한다.

```
start_time = int(time.time()) - 3600
end_time = int(time.time())
```

최근 1시간 범위를 초 단위 Unix timestamp로 만든다.

```
response = client.start_query(...)
```

CloudWatch Logs Insights 쿼리를 실행한다.

```
query_id = response["queryId"]
```

쿼리 결과를 조회하기 위한 ID를 저장한다.

```
while True:
    result = client.get_query_results(queryId=query_id)
```

쿼리가 완료될 때까지 반복해서 상태를 확인한다.

```
if status in ["Complete", "Failed", "Cancelled", "Timeout"]:
    break
```

쿼리 상태가 종료 상태에 도달하면 반복을 종료한다.

---

# 9. S3에 저장된 로그 분석

## 9.1 S3 로그 분석 방식

S3에 저장된 로그는 보통 다음 방식으로 분석한다.

| 방식 | 특징 | 적합한 상황 |
| --- | --- | --- |
| AWS CLI로 다운로드 후 분석 | 단순하고 이해하기 쉬움 | 소규모 로그, 교육용 실습 |
| Python에서 S3 객체 직접 읽기 | 자동화에 적합 | 정기 리포트 생성 |
| Athena로 직접 조회 | 대용량 분석에 적합 | GB~TB 단위 로그 |
| Glue + Athena | 스키마 관리 가능 | 운영 환경 로그 분석 |

---

app\_access.log

```
2026-05-06T09:00:01Z INFO 192.168.10.11 GET / 200 1243 35
2026-05-06T09:00:03Z INFO 192.168.10.12 GET /index.html 200 2310 42
2026-05-06T09:00:05Z INFO 192.168.10.13 GET /login 200 1980 51
2026-05-06T09:00:08Z WARN 192.168.10.14 POST /login 401 512 73
2026-05-06T09:00:10Z INFO 192.168.10.15 GET /products 200 4521 64
2026-05-06T09:00:14Z INFO 192.168.10.16 GET /products/1001 200 3892 59
2026-05-06T09:00:18Z ERROR 192.168.10.21 GET /api/users 500 742 132
2026-05-06T09:00:22Z INFO 192.168.10.17 GET /cart 200 2210 45
2026-05-06T09:00:25Z WARN 192.168.10.18 POST /cart 403 620 81
2026-05-06T09:00:29Z INFO 192.168.10.19 POST /checkout 200 3180 120
2026-05-06T09:00:33Z ERROR 192.168.10.22 POST /api/orders 503 890 241
2026-05-06T09:00:38Z INFO 192.168.10.20 GET /mypage 200 2710 66
2026-05-06T09:00:42Z WARN 192.168.10.14 POST /login 401 512 70
2026-05-06T09:00:46Z INFO 192.168.10.23 GET /static/app.js 200 10240 28
2026-05-06T09:00:50Z INFO 192.168.10.24 GET /static/style.css 200 5120 25
2026-05-06T09:00:55Z ERROR 192.168.10.25 GET /api/products 502 760 187
2026-05-06T09:01:01Z INFO 192.168.10.26 GET /products 200 4410 62
2026-05-06T09:01:04Z INFO 192.168.10.27 GET /products/1002 200 3940 61
2026-05-06T09:01:09Z WARN 192.168.10.28 GET /admin 403 600 89
2026-05-06T09:01:13Z ERROR 192.168.10.29 POST /api/payment 504 910 520
2026-05-06T09:01:18Z INFO 192.168.10.30 GET /order/history 200 2760 77
2026-05-06T09:01:22Z INFO 192.168.10.31 GET /help 200 1988 44
2026-05-06T09:01:27Z WARN 192.168.10.32 POST /login 401 512 71
2026-05-06T09:01:31Z INFO 192.168.10.33 GET /search?q=keyboard 200 3660 93
2026-05-06T09:01:36Z ERROR 192.168.10.34 GET /api/recommendations 500 820 211
2026-05-06T09:01:41Z INFO 192.168.10.35 GET /products/1003 200 3990 58
2026-05-06T09:01:45Z INFO 192.168.10.36 POST /logout 200 810 31
2026-05-06T09:01:49Z WARN 192.168.10.37 GET /admin/users 403 610 95
2026-05-06T09:01:54Z ERROR 192.168.10.38 POST /api/orders 503 890 255
2026-05-06T09:01:59Z INFO 192.168.10.39 GET / 200 1250 34
```

## 9.2 S3 로그 파일 목록 조회

```
aws s3 ls s3://my-log-bucket/AWSLogs/ --recursive
```

### 명령어 설명

| 구성 요소 | 설명 |
| --- | --- |
| `aws s3 ls` | S3 버킷 또는 경로의 객체 목록을 조회한다 |
| `s3://my-log-bucket/AWSLogs/` | 조회할 S3 경로다 |
| `--recursive` | 하위 경로까지 재귀적으로 조회한다 |

---

## 9.3 S3 로그 다운로드

```
aws s3 cp s3://my-log-bucket/logs/app.log ./logs/app.log
```

### 설명

`aws s3 cp`는 로컬 파일과 S3 객체 사이, 또는 S3 객체와 S3 객체 사이에서 복사를 수행한다.

| 구성 요소 | 설명 |
| --- | --- |
| `aws s3 cp` | S3 객체를 복사한다 |
| `s3://my-log-bucket/logs/app.log` | 원본 S3 객체 경로다 |
| `./logs/app.log` | 로컬 저장 경로다 |

---

## 9.4 특정 디렉터리 전체 동기화

```
aws s3 sync s3://my-log-bucket/logs/ ./logs/
```

### 설명

`aws s3 sync`는 S3와 로컬 디렉터리 사이의 파일을 동기화한다.

| 옵션/인자 | 설명 |
| --- | --- |
| `s3://my-log-bucket/logs/` | 원본 S3 경로다 |
| `./logs/` | 로컬 대상 디렉터리다 |
| `sync` | 원본과 대상의 차이를 비교해 필요한 파일만 복사한다 |

---

## 9.5 압축 로그 다운로드 후 해제

S3 로그는 `.gz` 형태로 압축되어 저장되는 경우가 많다.

```
aws s3 sync s3://my-log-bucket/alb/AWSLogs/ ./alb-logs/ \
  --exclude "*" \
  --include "*.gz"
```

### 옵션 설명

| 옵션 | 설명 |
| --- | --- |
| `--exclude "*"` | 모든 파일을 우선 제외한다 |
| `--include "*.gz"` | 제외된 파일 중 `.gz` 확장자 파일만 다시 포함한다 |

압축 해제:

```
find ./alb-logs -name "*.gz" -exec gunzip -k {} \;
```

### 명령어 설명

| 구성 요소 | 설명 |
| --- | --- |
| `find ./alb-logs` | `./alb-logs` 디렉터리 아래에서 파일을 찾는다 |
| `-name "*.gz"` | `.gz` 확장자를 가진 파일만 찾는다 |
| `-exec gunzip -k {} \;` | 찾은 파일마다 `gunzip -k`를 실행한다 |
| `{}` | `find`가 찾은 파일 경로로 치환된다 |
| `-k` | 압축 파일을 삭제하지 않고 원본 `.gz`를 유지한다 |

---

# 10. Python으로 S3 로그 분석

## 10.1 로컬로 내려받은 로그 분석

예제 로그:

```
2026-04-28T10:00:01 INFO GET /index.html 200 120
2026-04-28T10:00:03 ERROR GET /api/users 500 532
2026-04-28T10:00:05 WARN POST /login 401 210
2026-04-28T10:00:07 ERROR POST /api/orders 503 621
```

Python 분석 코드:

```
from collections import Counter

log_file = "./logs/app.log"

status_counter = Counter()
error_lines = []

with open(log_file, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.strip().split()

        if len(parts) < 5:
            continue

        timestamp = parts[0]
        level = parts[1]
        method = parts[2]
        path = parts[3]
        status_code = parts[4]

        status_counter[status_code] += 1

        if level == "ERROR" or status_code.startswith("5"):
            error_lines.append(line.strip())

print("상태 코드별 건수")
for status, count in status_counter.items():
    print(status, count)

print("\n에러 로그")
for line in error_lines:
    print(line)
```

### 코드 설명

```
from collections import Counter
```

항목별 개수를 쉽게 세기 위해 `Counter`를 사용한다.

```
status_counter = Counter()
```

HTTP 상태 코드별 발생 횟수를 저장한다.

```
error_lines = []
```

에러로 판단한 로그 라인을 저장한다.

```
parts = line.strip().split()
```

로그 한 줄을 공백 기준으로 분리한다.

```
if len(parts) < 5:
    continue
```

로그 형식이 예상보다 짧으면 분석 대상에서 제외한다.

```
status_counter[status_code] += 1
```

상태 코드별 카운트를 1 증가시킨다.

```
if level == "ERROR" or status_code.startswith("5"):
```

로그 레벨이 `ERROR`이거나 HTTP 상태 코드가 `5xx`이면 장애성 로그로 판단한다.

---

## 10.2 boto3로 S3 객체 직접 읽기

```
import boto3
import gzip
from io import BytesIO

s3 = boto3.client("s3")

bucket = "my-log-bucket"
key = "logs/app.log.gz"

response = s3.get_object(Bucket=bucket, Key=key)
body = response["Body"].read()

with gzip.GzipFile(fileobj=BytesIO(body)) as gz:
    for line in gz:
        text = line.decode("utf-8").strip()

        if "ERROR" in text:
            print(text)
```

### 코드 설명

```
s3 = boto3.client("s3")
```

S3 API 호출을 위한 boto3 클라이언트를 생성한다.

```
response = s3.get_object(Bucket=bucket, Key=key)
```

S3 버킷에서 특정 객체를 가져온다.

```
body = response["Body"].read()
```

S3 객체의 본문 데이터를 바이트 형태로 읽는다.

```
with gzip.GzipFile(fileobj=BytesIO(body)) as gz:
```

S3에서 읽은 바이트 데이터를 gzip 압축 파일처럼 처리한다.

```
line.decode("utf-8").strip()
```

바이트 형태의 로그 라인을 문자열로 변환하고 양쪽 공백을 제거한다.

---

# 11. Athena로 S3 로그 분석

## 11.1 Athena를 사용하는 이유

S3에 저장된 로그가 수십 GB 이상이면 로컬로 다운로드해서 분석하는 방식은 비효율적이다. 이 경우 Athena를 사용하면 S3에 저장된 로그를 직접 SQL로 조회할 수 있다.

---

## 11.2 S3 서버 액세스 로그 테이블 생성 예시

```
CREATE EXTERNAL TABLE IF NOT EXISTS s3_access_logs (
  bucket_owner string,
  bucket string,
  request_datetime string,
  remote_ip string,
  requester string,
  request_id string,
  operation string,
  key string,
  request_uri_operation string,
  request_uri_key string,
  request_uri_http_version string,
  http_status string,
  error_code string,
  bytes_sent bigint,
  object_size bigint,
  total_time string,
  turn_around_time string,
  referrer string,
  user_agent string,
  version_id string,
  host_id string,
  signature_version string,
  cipher_suite string,
  authentication_type string,
  host_header string,
  tls_version string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.RegexSerDe'
WITH SERDEPROPERTIES (
  'input.regex' = '([^ ]*) ([^ ]*) \\[(.*?)\\] ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) "([^ ]*) (.*?) (- |[^ ]*)" ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) "([^"]*)" "([^"]*)" ?([^ ]*)? ?([^ ]*)? ?([^ ]*)? ?([^ ]*)? ?([^ ]*)? ?([^ ]*)? ?([^ ]*)?.*$'
)
LOCATION 's3://my-log-bucket/s3-access-logs/';
```

### 설명

| 구문 | 설명 |
| --- | --- |
| `CREATE EXTERNAL TABLE` | S3 데이터를 Athena 외부 테이블로 정의한다 |
| `s3_access_logs` | Athena에서 사용할 테이블 이름이다 |
| `ROW FORMAT SERDE` | 로그 한 줄을 컬럼으로 분리하는 방식을 지정한다 |
| `RegexSerDe` | 정규식을 이용해 비정형 로그를 컬럼으로 분리한다 |
| `LOCATION` | 실제 로그 파일이 저장된 S3 경로다 |

S3 서버 액세스 로그는 각 레코드가 하나의 요청을 나타내며 공백 구분 필드로 구성된다.

---

## 11.3 Athena 분석 쿼리 예시

### 5xx 오류 조회

```
SELECT
  request_datetime,
  remote_ip,
  operation,
  key,
  http_status,
  error_code
FROM s3_access_logs
WHERE http_status LIKE '5%'
ORDER BY request_datetime DESC
LIMIT 50;
```

### IP별 요청 건수

```
SELECT
  remote_ip,
  count(*) AS request_count
FROM s3_access_logs
GROUP BY remote_ip
ORDER BY request_count DESC
LIMIT 20;
```

### 특정 객체 접근 이력

```
SELECT
  request_datetime,
  remote_ip,
  requester,
  operation,
  key,
  http_status
FROM s3_access_logs
WHERE key = 'important/data.csv'
ORDER BY request_datetime DESC;
```

---

# 12. CloudTrail 로그가 S3에 저장된 경우

CloudTrail 로그는 AWS API 호출 이력을 분석할 때 사용한다. S3 버킷에 CloudTrail 로그가 저장되어 있다면 Athena로 직접 조회할 수 있다.

## 12.1 주요 분석 포인트

| 분석 목적 | 확인 항목 |
| --- | --- |
| 누가 리소스를 삭제했는가 | `eventName`, `userIdentity`, `sourceIPAddress` |
| 루트 계정 사용 여부 | `userIdentity.type = Root` |
| 권한 변경 이력 | `AttachRolePolicy`, `PutUserPolicy`, `CreateAccessKey` |
| S3 객체 접근 | `GetObject`, `PutObject`, `DeleteObject` |
| 실패한 API 호출 | `errorCode`, `errorMessage` |

## 12.2 CloudTrail 분석 쿼리 예시

```
SELECT
  eventtime,
  eventname,
  useridentity.arn,
  sourceipaddress,
  errorcode,
  errormessage
FROM cloudtrail_logs
WHERE eventname IN ('DeleteBucket', 'DeleteObject', 'PutBucketPolicy')
ORDER BY eventtime DESC
LIMIT 50;
```

---

# 13. 통합 자동화 시나리오

## 시나리오: 매일 아침 장애성 로그 요약 리포트 생성

### 요구사항

1. CloudWatch Logs에서 최근 24시간 ERROR 로그 수집

2. S3에 저장된 ALB 로그에서 5xx 응답 수집

3. 결과를 CSV로 저장

4. 요약 결과를 Markdown 리포트로 생성

---

## 13.1 디렉터리 구조

```
log-analysis-automation/
├── scripts/
│   ├── analyze_cloudwatch.py
│   ├── analyze_s3_logs.py
│   └── make_report.py
├── reports/
│   ├── cloudwatch_errors.csv
│   ├── s3_5xx_errors.csv
│   └── daily_report.md
└── README.md
```

---

## 13.2 CloudWatch 분석 스크립트

```
import time
import csv
import boto3

LOG_GROUP = "/application/prod/web"
OUTPUT_FILE = "reports/cloudwatch_errors.csv"

client = boto3.client("logs")

start_time = int(time.time()) - 86400
end_time = int(time.time())

query = """
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 1000
"""

response = client.start_query(
    logGroupName=LOG_GROUP,
    startTime=start_time,
    endTime=end_time,
    queryString=query
)

query_id = response["queryId"]

while True:
    result = client.get_query_results(queryId=query_id)

    if result["status"] == "Complete":
        break

    if result["status"] in ["Failed", "Cancelled", "Timeout"]:
        raise RuntimeError(f"쿼리 실패: {result['status']}")

    time.sleep(2)

rows = []

for item in result["results"]:
    row = {}

    for field in item:
        row[field["field"]] = field["value"]

    rows.append(row)

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["@timestamp", "@message"])
    writer.writeheader()

    for row in rows:
        writer.writerow({
            "@timestamp": row.get("@timestamp", ""),
            "@message": row.get("@message", "")
        })

print(f"CloudWatch 분석 결과 저장 완료: {OUTPUT_FILE}")
```

---

## 13.3 S3 로그 분석 스크립트

```
import boto3
import gzip
import csv
from io import BytesIO

BUCKET = "my-log-bucket"
PREFIX = "alb/AWSLogs/"
OUTPUT_FILE = "reports/s3_5xx_errors.csv"

s3 = boto3.client("s3")

response = s3.list_objects_v2(
    Bucket=BUCKET,
    Prefix=PREFIX
)

error_rows = []

for obj in response.get("Contents", []):
    key = obj["Key"]

    if not key.endswith(".gz"):
        continue

    s3_obj = s3.get_object(Bucket=BUCKET, Key=key)
    body = s3_obj["Body"].read()

    with gzip.GzipFile(fileobj=BytesIO(body)) as gz:
        for line in gz:
            text = line.decode("utf-8").strip()
            parts = text.split()

            if len(parts) < 9:
                continue

            status_code = parts[8]

            if status_code.startswith("5"):
                error_rows.append({
                    "s3_key": key,
                    "raw_log": text,
                    "status_code": status_code
                })

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["s3_key", "status_code", "raw_log"]
    )
    writer.writeheader()
    writer.writerows(error_rows)

print(f"S3 로그 분석 결과 저장 완료: {OUTPUT_FILE}")
```

---

## 13.4 Markdown 리포트 생성

```
import csv
from datetime import datetime

CW_FILE = "reports/cloudwatch_errors.csv"
S3_FILE = "reports/s3_5xx_errors.csv"
REPORT_FILE = "reports/daily_report.md"

def count_csv_rows(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return sum(1 for _ in reader)

cloudwatch_error_count = count_csv_rows(CW_FILE)
s3_5xx_count = count_csv_rows(S3_FILE)

now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

report = f"""# 일일 로그 분석 리포트

생성 시간: {now}

## 1. 요약

| 항목 | 건수 |
|---|---:|
| CloudWatch ERROR 로그 | {cloudwatch_error_count} |
| S3 5xx 로그 | {s3_5xx_count} |

## 2. 판단 기준

- CloudWatch Logs에서는 메시지에 `ERROR`가 포함된 로그를 장애성 로그로 분류함.
- S3 로그에서는 HTTP 상태 코드가 `5xx`인 로그를 서버 오류로 분류함.

## 3. 후속 조치

- ERROR 로그가 평소보다 증가했는지 확인한다.
- 5xx 응답이 특정 경로 또는 특정 IP에 집중되었는지 확인한다.
- 반복 발생하는 오류 메시지는 애플리케이션 로그와 인프라 메트릭을 함께 확인한다.
"""

with open(REPORT_FILE, "w", encoding="utf-8") as f:
    f.write(report)

print(f"리포트 생성 완료: {REPORT_FILE}")
```

---

# 14. cron으로 정기 실행

```
crontab -e
```

다음 내용을 추가한다.

```
0 8 * * * cd /home/ec2-user/log-analysis-automation && /usr/bin/python3 scripts/analyze_cloudwatch.py && /usr/bin/python3 scripts/analyze_s3_logs.py && /usr/bin/python3 scripts/make_report.py
```

### 설명

| 필드 | 값 | 의미 |
| --- | --- | --- |
| 분 | `0` | 정각에 실행 |
| 시 | `8` | 오전 8시에 실행 |
| 일 | `*` | 매일 실행 |
| 월 | `*` | 매월 실행 |
| 요일 | `*` | 모든 요일 실행 |

즉, 매일 오전 8시에 로그 분석 스크립트 3개를 순서대로 실행한다.

# 15. 정리

이번 단원에서는 로컬 파일 기반 로그 분석을 AWS 클라우드 로그 분석으로 확장했다.

핵심은 다음과 같다.

| 구분 | 핵심 내용 |
| --- | --- |
| CloudWatch Logs | 운영 중인 서비스 로그를 실시간에 가깝게 조회하고 분석한다 |
| Logs Insights | CloudWatch Logs를 쿼리 언어로 집계·필터링한다 |
| S3 로그 | 장기 보관 로그, 대용량 로그, 서비스 액세스 로그 분석에 사용한다 |
| Athena | S3에 저장된 로그를 다운로드하지 않고 SQL로 분석한다 |
| Python 자동화 | boto3를 사용해 로그 조회, 분석, 리포트 생성을 자동화한다 |
| 운영 자동화 | cron, Lambda, EventBridge 등을 이용해 정기 분석 구조로 확장한다 |

최종적으로 로그 분석 자동화는 단순히 로그를 찾는 작업이 아니라, **반복적인 장애 탐지, 보안 이벤트 확인, 운영 리포트 생성, 이상 징후 분석을 자동화하는 작업**으로 확장된다.