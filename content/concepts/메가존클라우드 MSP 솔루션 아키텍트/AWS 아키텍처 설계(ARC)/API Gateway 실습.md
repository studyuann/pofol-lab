---
title: "API Gateway 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 아키텍처 설계(ARC)"]
is_public: true
draft: false
---

# API Gateway 실습

## 1. 실습 목표

이 실습에서는 Amazon API Gateway를 사용해 HTTP 기반 API를 생성하고, 백엔드로 Lambda를 연결하여 간단한 서버리스 API를 구현한다.

실습을 통해 다음 내용을 익힌다.

* API Gateway의 역할 이해

* HTTP API 생성

* Lambda 함수 생성 및 연결

* GET 요청 처리

* Query String 전달 확인

* JSON 응답 반환

* CORS 설정 이해

* API 테스트 및 동작 확인

* CloudWatch 로그 확인

Amazon API Gateway는 REST API, HTTP API, WebSocket API를 제공하며, Lambda 같은 백엔드와 연동해 API를 만들고 배포하고 모니터링할 수 있다.

---

# 2. 전체 아키텍처

구조는 다음과 같다.

```
Client
  │
  │ HTTP Request
  ▼
Amazon API Gateway
  │
  │ Lambda Proxy Integration
  ▼
AWS Lambda
  │
  │ JSON Response
  ▼
Amazon API Gateway
  │
  ▼
Client
```

이 구조에서 API Gateway는 **API의 진입점** 역할을 한다.

Lambda는 실제 비즈니스 로직을 수행한다.

즉, 사용자는 API Gateway 주소로 요청을 보내고, API Gateway는 그 요청을 Lambda로 전달한 뒤,

Lambda의 응답을 다시 사용자에게 반환한다.

---

# 3. 준비

* AWS 계정

* API Gateway 접근 권한

* Lambda 생성 권한

* CloudWatch Logs 조회 권한

권한이 부족하면 다음 작업이 제한될 수 있다.

* API 생성

* Lambda 생성

* 로그 확인

* 테스트 호출

---

# 4. 실습 시나리오

```
1. Lambda 함수 생성
2. API Gateway HTTP API 생성
3. GET /hello 라우트 생성
4. Lambda와 통합
5. API 배포
6. 브라우저와 curl로 테스트
7. Query String 처리
8. CORS 설정
9. CloudWatch 로그 확인
```

---

# 5. API Gateway 핵심 개념

## 5.1 API Gateway란

API Gateway는 클라이언트 요청을 받아 백엔드 서비스로 전달하는 **API 프론트도어 서비스**다.

AWS 서비스, Lambda, HTTP 엔드포인트 등과 통합할 수 있음.

쉽게 말하면 다음과 같다.

```
사용자 요청을 받는 입구 = API Gateway
실제 처리 담당 = Lambda 또는 다른 백엔드
```

---

## 5.2 HTTP API와 REST API

API Gateway에는 대표적으로 다음 두 가지 HTTP 기반 API가 있다.

```
REST API
HTTP API
```

이번 실습에서는 **HTTP API**를 사용한다.

이유는 다음과 같다.

* 구성 단순함

* Lambda 연동이 쉬움

* 빠르게 실습 가능함

AWS 공식 문서 기준으로 REST API와 HTTP API는 지원 기능이 일부 다르며, 예를 들어 **Access logs to Amazon Data Firehose**, **Execution logs**, **X-Ray tracing** 등은 REST API에서 지원되고 HTTP API에서는 지원되지 않는 항목이 있음. 반면 기본적인 Lambda 연동과 CloudWatch metrics, Access logs는 둘 다 지원한다.

---

# 6. 실습 1. Lambda 함수 생성

## 6.1 Lambda 콘솔 이동

AWS Management Console에서 다음으로 이동한다.

```
Services → Lambda
```

---

## 6.2 함수 생성

다음을 선택한다.

```
Create function
```

옵션

```
Author from scratch
```

설정 예시

```
Function name: api-gateway-hello
Runtime: Python 3.12
Architecture: x86_64
Execution role: Create a new role with basic Lambda permissions
```

생성 완료 후 코드 편집 화면으로 이동한다.

---

## 6.3 Lambda 코드 작성

아래 코드를 입력한다.

```
import json

def lambda_handler(event, context):
    name = "world"

    query_params = event.get("queryStringParameters")
    if query_params and "name" in query_params:
        name = query_params["name"]

    response_body = {
        "message": f"Hello, {name}",
        "method": event.get("requestContext", {}).get("http", {}).get("method"),
        "path": event.get("rawPath")
    }

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(response_body)
    }
```

---

## 6.4 코드 설명

이 코드는 API Gateway에서 전달한 요청 정보를 받아 JSON 형태로 응답한다.

### `event`

```
event
```

`event`는 API Gateway가 Lambda로 전달하는 요청 데이터다.

여기에는 다음 정보가 포함될 수 있다.

* HTTP 메서드

* 경로

* 헤더

* Query String

* 요청 본문

* 요청 컨텍스트 정보

HTTP API에서 Lambda 프록시 통합을 사용하면 API Gateway가 요청 데이터를 Lambda에 전달하고, Lambda가 정해진 응답 형식으로 반환하면 API Gateway가 이를 HTTP 응답으로 변환한다.

---

### `queryStringParameters`

```
query_params = event.get("queryStringParameters")
```

이 값은 URL 뒤에 붙는 Query String 값을 의미한다.

예

```
...?name=aws
```

그러면 Lambda 안에서는 대략 다음처럼 들어온다.

```
{
  "queryStringParameters": {
    "name": "aws"
  }
}
```

---

### 응답 형식

Lambda 프록시 통합에서는 일반적으로 아래 형식으로 반환한다.

```
{
    "statusCode": 200,
    "headers": {
        "Content-Type": "application/json"
    },
    "body": "문자열"
}
```

중요한 점은 `body`가 **문자열**이어야 한다는 점이다.

그래서 Python 딕셔너리를 그대로 넣지 않고 다음처럼 변환한다.

```
json.dumps(response_body)
```

이 작업을 하지 않으면 API Gateway가 기대하는 형식과 달라질 수 있음.

---

## 6.5 Deploy

코드 입력 후 다음을 선택한다.

```
Deploy
```

---

## 6.6 Test 이벤트로 확인

Lambda 단독 테스트도 가능하다.

테스트 이벤트 예시

```
{
  "queryStringParameters": {
    "name": "lambda"
  },
  "requestContext": {
    "http": {
      "method": "GET"
    }
  },
  "rawPath": "/hello"
}
```

실행 결과 예시

```
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json"
  },
  "body": "{\"message\": \"Hello, lambda\", \"method\": \"GET\", \"path\": \"/hello\"}"
}
```

---

# 7. 실습 2. API Gateway HTTP API 생성

## 7.1 API Gateway 콘솔 이동

```
Services → API Gateway
```

---

## 7.2 API 생성

다음을 선택한다.

```
Create API
```

여러 API 유형 중에서 다음을 선택한다.

```
HTTP API
Build
```

---

## 7.3 통합 대상 설정

Integration type에서 다음을 선택한다.

```
Lambda
```

앞에서 만든 Lambda 함수 선택

```
api-gateway-hello
```

다음 단계로 이동한다.

---

## 7.4 라우트 설정

라우트는 "어떤 요청을 어떤 백엔드로 보낼 것인가"를 정의한다.

예시 설정

```
Method: GET
Resource path: /hello
```

즉 아래 요청을 처리하게 된다.

```
GET /hello
```

---

## 7.5 스테이지 생성

기본 Stage를 사용해도 된다.

예

```
$default
```

HTTP API는 기본 스테이지를 활용하면 빠르게 테스트 가능하다.

생성을 완료한다.

---

# 8. 실습 3. API 호출 테스트

API 생성이 끝나면 **Invoke URL**이 제공된다.

예시

```
https://abc123.execute-api.ap-northeast-2.amazonaws.com
```

실제 호출 URL은 다음처럼 된다.

```
https://abc123.execute-api.ap-northeast-2.amazonaws.com/hello
```

---

## 8.1 브라우저 테스트

브라우저 주소창에 입력한다.

```
https://abc123.execute-api.ap-northeast-2.amazonaws.com/hello
```

예상 응답

```
{"message":"Hello, world","method":"GET","path":"/hello"}
```

---

## 8.2 Query String 테스트

다음 주소로 호출한다.

```
https://abc123.execute-api.ap-northeast-2.amazonaws.com/hello?name=API
```

응답 예시

```
{"message":"Hello, API","method":"GET","path":"/hello"}
```

---

## 8.3 curl 테스트

터미널에서 다음 명령으로 확인할 수 있다.

```
curl https://abc123.execute-api.ap-northeast-2.amazonaws.com/hello
```

Query String 포함

```
curl "https://abc123.execute-api.ap-northeast-2.amazonaws.com/hello?name=cloud"
```

---

## 8.4 curl 명령 설명

### 기본 형식

```
curl URL
```

`curl`은 HTTP 요청을 보낼 수 있는 CLI 도구다.

API 테스트에서 가장 많이 사용한다.

---

### 따옴표를 쓰는 이유

```
curl "https://example.com/hello?name=cloud"
```

URL에 `?`, `&` 같은 문자가 들어가면 셸이 이를 특별하게 해석할 수 있다.

그래서 문자열 전체를 따옴표로 감싸는 습관이 좋다.

---

### 자세한 응답 보기

```
curl -i "https://abc123.execute-api.ap-northeast-2.amazonaws.com/hello?name=cloud"
```

* `i` 옵션은 응답 헤더까지 같이 보여준다.

예를 들어 다음과 같은 정보가 보일 수 있다.

```
HTTP/2 200
content-type: application/json
content-length: 57
...
```

---

# 9. 실습 4. POST 요청 확장

GET만 있으면 너무 단순하므로, POST 요청도 추가해볼 수 있다.

## 9.1 Lambda 코드 수정

아래처럼 수정한다.

```
import json

def lambda_handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method")
    path = event.get("rawPath")

    if method == "GET":
        name = "world"
        query_params = event.get("queryStringParameters")
        if query_params and "name" in query_params:
            name = query_params["name"]

        body = {
            "message": f"Hello, {name}",
            "method": method,
            "path": path
        }

    elif method == "POST":
        request_body = {}
        if event.get("body"):
            request_body = json.loads(event["body"])

        body = {
            "message": "POST request received",
            "input": request_body,
            "method": method,
            "path": path
        }

    else:
        body = {
            "message": "Unsupported method",
            "method": method,
            "path": path
        }

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }
```

---

## 9.2 POST 라우트 추가

API Gateway에서 라우트를 하나 더 추가한다.

```
POST /hello
```

통합 대상은 같은 Lambda 함수로 지정한다.

---

## 9.3 POST 요청 테스트

```
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"name":"aws","course":"apigateway"}' \
  https://abc123.execute-api.ap-northeast-2.amazonaws.com/hello
```

응답 예시

```
{
  "message": "POST request received",
  "input": {
    "name": "aws",
    "course": "apigateway"
  },
  "method": "POST",
  "path": "/hello"
}
```

---

## 9.4 `-X`, `-H`, `-d` 설명

### `-X POST`

```
-X POST
```

HTTP 메서드를 POST로 지정한다.

기본 `curl`은 GET 요청이다.

그래서 POST를 보내려면 명시하는 것이 좋다.

---

### `-H "Content-Type: application/json"`

```
-H "Content-Type: application/json"
```

HTTP Header를 추가한다.

여기서는 요청 본문이 JSON 형식임을 서버에 알려준다.

---

### `-d`

```
-d '{"name":"aws"}'
```

전송할 요청 본문(body)을 의미한다.

즉 실제 POST 데이터가 된다.

---

# 10. 실습 5. CORS(Cross Origin Resource Sharing) 설정

CORS는 브라우저에서 다른 도메인의 API를 호출할 때 필요한 보안 설정이다.

브라우저 기반 프론트엔드와 API를 연결할 때 자주 필요하다.

예를 들어 다음과 같은 상황이다.

```
프론트엔드: https://example.com
API: https://abc123.execute-api.ap-northeast-2.amazonaws.com
```

도메인이 다르므로 브라우저는 기본적으로 제한한다.

---

## 10.1 HTTP API에서 CORS 설정

API Gateway 콘솔에서 해당 HTTP API 선택 후 CORS 설정으로 이동한다.

예시 설정

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET,POST,OPTIONS
Access-Control-Allow-Headers: content-type
```

실습 단계에서는 `*`를 사용해도 되지만, 운영 환경에서는 필요한 도메인만 허용하는 것이 좋다.

---

## 10.2 CORS가 필요한 이유

브라우저는 같은 출처 정책(Same-Origin Policy)을 적용한다.

즉 다음이 다르면 다른 출처로 본다.

* 프로토콜

* 도메인

* 포트

이때 브라우저는 API가 외부 요청을 허용하는지 확인하기 위해 **preflight request**를 보낼 수 있다.

그 요청이 `OPTIONS` 메서드다.

그래서 CORS 설정이 잘못되면 다음과 같은 현상이 생긴다.

* 브라우저에서만 호출 실패

* Postman이나 curl에서는 정상

* 콘솔에 CORS 에러 출력

---

# 11. 실습 6. CloudWatch 로그 확인

API 호출이 안 되거나 Lambda에서 에러가 나면 로그를 확인해야 한다.

## 11.1 Lambda 로그 확인

경로

```
Lambda → 함수 선택 → Monitor → View CloudWatch logs
```

로그에 다음 항목을 추가해서 event 구조를 직접 확인해볼 수도 있다.

```
import json

def lambda_handler(event, context):
    print(json.dumps(event))
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "ok"})
    }
```

이렇게 하면 API Gateway가 Lambda로 어떤 형태의 요청을 전달하는지 바로 확인할 수 있다.

---

## 11.2 왜 로그가 중요한가

실습에서 가장 자주 발생하는 문제는 다음과 같다.

* 경로는 맞는데 Lambda 응답 형식이 잘못됨

* POST body 파싱 실패

* CORS 누락

* 권한 문제

* 잘못된 메서드 호출

이때 로그를 보면 문제 원인을 빨리 찾을 수 있음.

---

# 12. 실습 7. API Gateway 테스트 페이지 대신 실제 호출 구조 이해

많은 경우 콘솔 테스트에서는 되는데 브라우저에서는 안 되는 경우가 있다.

이유는 다음과 같다.

```
콘솔 테스트 = AWS 내부 테스트 도구
브라우저 호출 = 실제 HTTP 클라이언트 + CORS 영향 받음
```

그래서 반드시 다음 세 가지 방식으로 확인하는 습관이 좋다.

* 콘솔

* curl

* 브라우저

---

# 13. 자주 발생하는 오류와 원인

## 13.1 404 Not Found

원인

* 경로가 다름

* `/hello` 대신 `/` 호출

* 라우트 미생성

확인 포인트

```
GET /hello 라우트가 실제로 존재하는지 확인
```

---

## 13.2 500 Internal Server Error

원인

* Lambda 코드 오류

* JSON 파싱 실패

* 응답 형식 오류

확인 포인트

```
CloudWatch Logs 확인
```

---

## 13.3 CORS 에러

원인

* API Gateway CORS 미설정

* Allow-Origin 누락

* 브라우저 preflight 실패

확인 포인트

```
HTTP API의 CORS 설정 확인
```

---

## 13.4 Permission 에러

원인

* Lambda 실행 권한 문제

* API Gateway가 Lambda를 Invoke하지 못함

다만 콘솔에서 일반적인 Lambda 통합으로 생성하면 필요한 권한 연결이 자동으로 처리되는 경우가 많다.

---

# 14. 실습 정리

```
클라이언트가 API Gateway URL 호출
→ API Gateway가 요청을 수신
→ Lambda에 요청 전달
→ Lambda가 JSON 응답 생성
→ API Gateway가 HTTP 응답으로 반환
```

여기서 중요한 포인트는 다음이다.

* API Gateway는 API의 외부 진입점이다.

* Lambda 프록시 통합을 사용하면 요청 정보 전체를 Lambda에서 유연하게 처리할 수 있다.

* HTTP API는 빠르고 단순하게 서버리스 API를 실습하기 좋다.

* 브라우저 기반 연동에서는 CORS 설정이 매우 중요하다.

---