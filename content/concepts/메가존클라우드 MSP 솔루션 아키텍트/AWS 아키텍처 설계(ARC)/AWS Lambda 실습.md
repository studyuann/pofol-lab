---
title: "AWS Lambda 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 아키텍처 설계(ARC)"]
is_public: true
draft: false
---

# AWS Lambda 실습

---

# 1. 기본실습

# 실습 1. Lambda 함수 생성 및 테스트

## 실습 목표

* Lambda 함수 생성

* Python 코드 작성

* 테스트 이벤트 실행

* 실행 결과 확인

* CloudWatch Logs 확인

---

## 실습 구성

* Runtime: Python 3.x

* 함수 이름: `hello-lambda`

* 실행 방식: 수동 테스트 이벤트

* 확인 항목: 반환값, 실행 로그

---

## 1.1 Lambda 함수 생성

AWS 콘솔에서 다음 메뉴로 이동한다.

```
AWS Console → Lambda → Functions → Create function
```

생성 방식은 다음과 같이 선택한다.

```
Author from scratch
```

설정값 예시는 다음과 같다.

```
Function name: hello-lambda
Runtime: Python 3.12
Architecture: x86_64
Execution role: Create a new role with basic Lambda permissions
```

생성 버튼을 눌러 함수를 생성한다.

---

## 1.2 생성 직후 확인할 항목

함수를 생성하면 Lambda 화면에서 다음 항목을 먼저 확인한다.

* Function name

* Runtime

* Handler

* Memory

* Timeout

* Execution role

기본적으로 Handler는 보통 다음과 같이 설정된다.

```
lambda_function.lambda_handler
```

이 의미는 다음과 같다.

```
파일명: lambda_function.py
실행 함수명: lambda_handler
```

즉, Lambda는 업로드된 코드 중에서

`lambda_function.py` 파일 안에 있는

`lambda_handler()` 함수를 시작점으로 실행한다.

---

## 1.3 기본 코드 작성

Code 탭에서 기본 코드를 다음과 같이 수정한다.

```
deflambda_handler(event,context):
return {
'statusCode':200,
'body':'Hello Lambda'
    }
```

---

## 1.4 코드 설명

### `def lambda_handler(event, context):`

Lambda가 호출될 때 가장 먼저 실행하는 함수다.

* `event`
  + 호출 시 전달되는 입력 데이터
  + 테스트 이벤트, API 요청값, S3 이벤트 정보 등이 들어옴

* `context`
  + 함수 실행 환경 정보
  + 함수 이름, 요청 ID, 남은 실행 시간 등의 메타데이터를 포함함

처음 실습에서는 `event`, `context`를 직접 사용하지 않아도 됨.

하지만 Lambda 함수는 기본적으로 이 두 값을 입력으로 받는 구조라고 이해하면 된다.

---

### `return { 'statusCode': 200, 'body': 'Hello Lambda' }`

Lambda 함수의 실행 결과를 반환한다.

여기서 `statusCode`와 `body` 구조는 특히 **API Gateway 연동 시 자주 사용하는 형태**다.

* `statusCode`
  + HTTP 상태 코드처럼 사용
  + `200`이면 정상 처리 의미

* `body`
  + 실제 응답 본문
  + 문자열 형태로 내려가는 경우가 많음

지금은 단순 테스트지만, 이후 API Gateway와 연결하면 이 구조가 그대로 중요해진다.

---

## 1.5 Deploy 수행

코드를 수정한 뒤 반드시 배포해야 한다.

```
Deploy
```

Lambda 콘솔에서는 코드를 수정했다고 바로 실행 환경에 반영되지 않음.

**Deploy 버튼을 눌러야 현재 코드가 실제 실행 대상 버전으로 반영됨**.

수업 중 학생들이 가장 자주 하는 실수 중 하나가

코드만 바꾸고 Deploy를 누르지 않는 것임.

---

## 1.6 테스트 이벤트 생성

이제 함수를 직접 실행해 본다.

```
Test → Configure test event
```

이벤트 이름 예시

```
test1
```

이벤트 JSON은 다음과 같이 작성한다.

```
{}
```

처음 실습에서는 입력값이 필요 없으므로 빈 JSON 객체를 사용한다.

여기서 `{}` 는

**아무런 입력 데이터도 전달하지 않는 기본 테스트 요청**이라고 이해하면 된다.

생성 후 `Test` 버튼을 눌러 실행한다.

---

## 1.7 실행 결과 확인

실행이 성공하면 다음과 같은 형태의 결과를 확인할 수 있다.

```
{
  "statusCode":200,
  "body":"Hello Lambda"
}
```

추가로 다음 항목도 확인한다.

* Execution result: Succeeded

* Duration

* Billed duration

* Memory Size

* Max memory used

---

## 1.8 실행 결과 항목 설명

### Duration

실제 함수가 실행된 시간이다.

예를 들어 15ms가 표시되면

코드 실행이 0.015초 정도 걸렸다는 의미다.

---

### Billed duration

과금 기준이 되는 실행 시간이다.

Lambda는 아주 짧게 실행되어도

과금 계산 단위에 따라 청구 시간이 정해진다.

실습에서는 큰 비용이 발생하지 않지만,

운영 환경에서는 호출 횟수와 실행 시간이 누적되므로 중요하다.

---

### Memory Size

이 함수에 할당된 메모리 크기다.

예

```
128 MB
```

Lambda는 메모리를 늘리면 CPU 자원도 함께 증가하는 구조다.

즉, 메모리 설정은 단순히 RAM만 의미하는 것이 아니라

실행 성능에도 영향을 준다.

---

### Max memory used

실행 중 실제로 최대 얼마만큼의 메모리를 사용했는지 보여준다.

이 값이 Memory Size보다 매우 낮다면

메모리가 과하게 설정되었을 가능성이 있다.

반대로 너무 근접하면

메모리 부족 가능성을 점검해야 한다.

---

# 실습 2. 입력값(event) 처리

## 실습 목표

* 테스트 이벤트 값을 Lambda에서 읽기

* 입력값에 따라 다른 결과 반환

* event 객체 구조 이해

---

## 2.1 코드 수정

다음 코드로 변경한다.

```
deflambda_handler(event,context):
name=event.get('name','Guest')

return {
'statusCode':200,
'body':f'Hello{name}'
    }
```

Deploy를 다시 수행한다.

---

## 2.2 코드 설명

### `event.get('name', 'Guest')`

`event`는 딕셔너리 형태의 입력 데이터라고 보면 된다.

즉, 다음과 같은 JSON을 전달하면

```
{
  "name":"Alice"
}
```

Python 코드에서는 다음처럼 읽을 수 있다.

```
event['name']
```

하지만 이렇게 직접 접근하면

해당 키가 없을 때 에러가 발생할 수 있다.

그래서 실습에서는 다음 방식을 사용한다.

```
event.get('name','Guest')
```

이 방식의 의미는 다음과 같다.

* `name` 키가 있으면 그 값을 사용

* 없으면 기본값으로 `Guest` 사용

즉, 보다 안전한 방식이다.

---

## 2.3 테스트 이벤트 생성

다음 JSON으로 테스트 이벤트를 만든다.

```
{
  "name":"Cloud"
}
```

실행 결과 예시

```
{
  "statusCode":200,
  "body":"Hello Cloud"
}
```

---

## 2.4 입력값 없이 다시 테스트

이번에는 다음처럼 빈 이벤트로 실행한다.

```
{}
```

결과는 다음과 같이 나온다.

```
{
  "statusCode":200,
  "body":"Hello Guest"
}
```

이 실습을 통해

**입력값이 있을 때와 없을 때의 처리 방식**을 함께 확인할 수 있다.

---

# 실습 3. 로그 출력 및 CloudWatch Logs 확인

## 실습 목표

* print()를 이용한 로그 출력

* CloudWatch Logs에서 실행 로그 확인

* 문제 발생 시 로그 확인 습관 익히기

---

## 3.1 코드 수정

다음과 같이 수정한다.

```
deflambda_handler(event,context):
name=event.get('name','Guest')

print('=== Lambda function started ===')
print(f'event:{event}')
print(f'name:{name}')

return {
'statusCode':200,
'body':f'Hello{name}'
    }
```

Deploy를 수행한다.

---

## 3.2 코드 설명

### `print('=== Lambda function started ===')`

Lambda에서는 `print()`로 출력한 내용이

터미널에 보이는 것이 아니라 **CloudWatch Logs**로 전송된다.

즉, `print()`는 단순한 화면 출력이 아니라

운영 관점에서는 **로그 기록 도구** 역할을 한다.

---

### `print(f'event: {event}')`

실제로 Lambda가 어떤 입력값을 받았는지 확인하기 위한 로그다.

실무에서도 이벤트 구조를 처음 확인할 때

이 방식으로 전체 event를 출력해보는 경우가 많다.

단, 운영 환경에서는 민감정보가 포함될 수 있으므로

무분별한 전체 출력은 주의해야 한다.

---

## 3.3 테스트 실행

이벤트 예시

```
{
  "name":"Lambda"
}
```

실행 후 결과를 확인한다.

---

## 3.4 CloudWatch Logs 확인

Lambda 함수 화면에서 다음 메뉴를 선택한다.

```
Monitor → View CloudWatch logs
```

또는 CloudWatch 콘솔에서 직접 다음으로 이동해도 된다.

```
CloudWatch → Logs → Log groups → /aws/lambda/hello-lambda
```

로그 스트림을 열어보면 다음과 유사한 내용이 보인다.

```
START RequestId: ...
=== Lambda function started ===
event: {'name': 'Lambda'}
name: Lambda
END RequestId: ...
REPORT RequestId: ...
```

---

## 3.5 로그 항목 설명

### START

Lambda 실행 시작 지점이다.

각 요청마다 고유한 RequestId가 부여된다.

---

### END

Lambda 실행 종료 지점이다.

정상 종료 여부를 확인할 수 있다.

---

### REPORT

실행 시간, 메모리 사용량 등 요약 정보를 보여준다.

예를 들어 다음 값을 확인할 수 있다.

* Duration

* Billed Duration

* Memory Size

* Max Memory Used

* Init Duration

---

### Init Duration

콜드 스타트와 관련된 초기화 시간이 표시될 수 있다.

즉, Lambda 실행 환경이 처음 준비되면서 걸린 시간이다.

이 값이 보인다면

새로운 실행 환경이 준비되었다는 의미로 이해하면 된다.

---

# 실습 4. 오류 발생 및 로그 확인

## 실습 목표

* Lambda 오류 상황 확인

* 예외 발생 시 어떻게 표시되는지 확인

* CloudWatch Logs에서 에러 추적

---

## 4.1 코드 수정

다음 코드로 바꾼다.

```
deflambda_handler(event,context):
print('function started')

number=10/0

return {
'statusCode':200,
'body':str(number)
    }
```

Deploy 후 테스트를 수행한다.

---

## 4.2 예상 결과

실행은 실패한다.

에러 메시지 예시는 다음과 비슷하다.

```
{
  "errorMessage": "division by zero",
  "errorType": "ZeroDivisionError",
  ...
}
```

---

## 4.3 왜 실패하는가

다음 코드 때문이다.

```
number=10/0
```

0으로 나누기는 Python에서 허용되지 않음.

따라서 `ZeroDivisionError`가 발생한다.

이 실습은 일부러 에러를 만들어

**Lambda에서 실패가 어떻게 보이는지** 확인하기 위한 것이다.

---

## 4.4 CloudWatch Logs에서 에러 보기

로그를 열어보면 traceback 정보가 기록된다.

예시

```
[ERROR] ZeroDivisionError: division by zero
Traceback (most recent call last):
  File "/var/task/lambda_function.py", line 4, in lambda_handler
    number = 10 / 0
```

이 정보는 어느 파일, 몇 번째 줄에서 문제가 발생했는지 알려준다.

실무에서 Lambda 문제 해결의 핵심은

대부분 CloudWatch Logs 확인이다.

---

## 4.5 정상 코드로 복구

다음처럼 수정하여 정상 상태로 되돌린다.

```
deflambda_handler(event,context):
print('function started')

return {
'statusCode':200,
'body':'Lambda recovered'
    }
```

Deploy 후 다시 테스트한다.

# 실습 5. S3 이벤트 트리거 연동

## 실습 목표

* S3 파일 업로드 시 Lambda 자동 실행

* 이벤트 기반 서버리스 구조 이해

* event 내부의 S3 정보 확인

---

## 실습 구성

* S3 Bucket 생성

* Lambda 함수 생성 또는 기존 함수 사용

* S3 PUT 이벤트를 Lambda에 연결

* 파일 업로드 후 로그 확인

---

## 5.1 Lambda 코드 작성

다음 코드로 수정한다.

```
importjson

deflambda_handler(event,context):
print('S3 Event Received')
print(json.dumps(event,indent=2))

record=event['Records'][0]
bucket_name=record['s3']['bucket']['name']
object_key=record['s3']['object']['key']

return {
'statusCode':200,
'body':json.dumps({
'bucket':bucket_name,
'key':object_key
        })
    }
```

Deploy를 수행한다.

---

## 5.2 코드 설명

S3 이벤트는 일반 테스트 이벤트와 달리 구조가 조금 복잡하다.

중요한 경로는 다음이다.

```
event['Records'][0]['s3']['bucket']['name']
event['Records'][0]['s3']['object']['key']
```

이 의미는 다음과 같다.

* `Records`
  + 이벤트 목록

* `[0]`
  + 첫 번째 이벤트

* `s3.bucket.name`
  + 버킷 이름

* `s3.object.key`
  + 업로드된 객체 이름

S3 이벤트는 여러 건이 한 번에 올 수도 있으므로 `Records` 배열 형태를 사용한다.

---

## 5.3 S3 트리거 추가

Lambda 함수의 Trigger 추가 메뉴에서 S3를 선택한다.

설정 예시

```
Bucket: lambda-trigger-bucket-xxxxx
Event type: PUT
Prefix/Suffix: 비워도 됨
```

주의사항

* Lambda와 S3 간 권한/알림 구성이 자동 연결됨

* 같은 버킷에 Lambda가 다시 파일을 쓰는 구조라면 무한 호출 위험이 있음

---

## 5.4 파일 업로드 테스트

S3 버킷에 임의의 파일을 업로드한다.

예시 파일명

```
test.txt
```

업로드 후 Lambda 콘솔의 Monitor 또는 CloudWatch Logs에서 실행 로그를 확인한다.

로그에서 bucket name, object key가 출력되면 정상이다.

---

# 6. 정리

* Lambda는 코드를 이벤트 기반으로 실행하는 구조임

* `event`, `context`를 입력으로 받음

* 콘솔 테스트 이벤트로 손쉽게 검증 가능함

* `print()` 로그는 CloudWatch Logs에서 확인함

* S3와 연결하면 파일 업로드 기반 자동화가 가능함

---