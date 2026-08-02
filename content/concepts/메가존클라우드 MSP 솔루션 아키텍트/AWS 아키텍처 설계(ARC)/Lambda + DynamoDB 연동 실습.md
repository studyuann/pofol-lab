---
title: "Lambda + DynamoDB 연동 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 아키텍처 설계(ARC)"]
is_public: true
draft: false
---

# Lambda + DynamoDB 연동 실습

## 실습 목표

* DynamoDB 테이블 생성

* Lambda에서 DynamoDB 데이터 저장 (PUT)

* Lambda에서 DynamoDB 데이터 조회 (GET)

* API Gateway를 통한 CRUD 작업

---

## 실습 1: DynamoDB 테이블 생성

### 1.1 테이블 만들기

1. AWS Console에서 **DynamoDB** 서비스로 이동

2. **테이블 만들기** 클릭

3. 다음 정보 입력:
   * **테이블 이름**: `Users`
   * **파티션 키**: `userId` (문자열)
   * **테이블 설정**: 기본 설정 사용

4. **테이블 만들기** 클릭

5. 테이블 상태가 **활성**이 될 때까지 대기 (약 1분)

### 1.2 테이블 ARN 확인

1. 생성된 `Users` 테이블 클릭

2. **일반 정보** 탭에서 **ARN** 복사
   * 예: `arn:aws:dynamodb:ap-northeast-2:123456789012:table/Users`

3. 메모장에 저장 (나중에 IAM 권한 설정에 사용)

---

## 실습 2: Lambda 함수에 DynamoDB 권한 부여

### 2.1 IAM 역할 수정

1. **Lambda** 콘솔로 이동

2. `HelloWorldFunction` 함수 선택

3. **구성** 탭 → **권한** 클릭

4. **역할 이름** 클릭 (새 탭에서 IAM 콘솔 열림)

5. **권한 추가** → **인라인 정책 생성** 클릭

6. **JSON** 탭 선택

7. 다음 정책 입력:

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Scan",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:ap-northeast-2:*:table/Users"
    }
  ]
}
```

1. **정책 검토** 클릭

2. 정책 이름: `DynamoDBAccessPolicy`

3. **정책 생성** 클릭

---

## 실습 3: Lambda 함수 코드 작성

### 3.1 사용자 관리 API 코드

Lambda 함수의 코드를 다음으로 교체:

```
import json
import boto3
from decimal import Decimal
from datetime import datetime

# DynamoDB 클라이언트 초기화
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Users')

# Decimal을 JSON으로 변환하기 위한 헬퍼 클래스
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    print("Received event:", json.dumps(event))

    http_method = event.get('httpMethod')
    path = event.get('path', '')

    try:
        # 라우팅
        if http_method == 'POST' and path == '/users':
            return create_user(event)
        elif http_method == 'GET' and path == '/users':
            return get_all_users(event)
        elif http_method == 'GET' and path.startswith('/users/'):
            return get_user(event)
        elif http_method == 'PUT' and path.startswith('/users/'):
            return update_user(event)
        elif http_method == 'DELETE' and path.startswith('/users/'):
            return delete_user(event)
        else:
            return response(400, {'error': 'Unsupported route'})

    except Exception as e:
        print(f"Error: {str(e)}")
        return response(500, {'error': str(e)})

# 사용자 생성
def create_user(event):
    body = json.loads(event.get('body', '{}'))

    user_id = body.get('userId')
    name = body.get('name')
    email = body.get('email')

    if not user_id or not name or not email:
        return response(400, {'error': 'userId, name, email are required'})

    item = {
        'userId': user_id,
        'name': name,
        'email': email,
        'createdAt': datetime.now().isoformat()
    }

    table.put_item(Item=item)

    return response(201, {
        'message': 'User created successfully',
        'user': item
    })

# 모든 사용자 조회
def get_all_users(event):
    result = table.scan()
    users = result.get('Items', [])

    return response(200, {
        'count': len(users),
        'users': users
    })

# 특정 사용자 조회
def get_user(event):
    path = event.get('path', '')
    user_id = path.split('/')[-1]

    result = table.get_item(Key={'userId': user_id})

    if 'Item' not in result:
        return response(404, {'error': 'User not found'})

    return response(200, {'user': result['Item']})

# 사용자 정보 수정
def update_user(event):
    path = event.get('path', '')
    user_id = path.split('/')[-1]

    body = json.loads(event.get('body', '{}'))
    name = body.get('name')
    email = body.get('email')

    if not name and not email:
        return response(400, {'error': 'At least one field (name or email) is required'})

    # 업데이트할 필드 구성
    update_expression = "SET "
    expression_values = {}

    if name:
        update_expression += "name = :name, "
        expression_values[':name'] = name
    if email:
        update_expression += "email = :email, "
        expression_values[':email'] = email

    update_expression = update_expression.rstrip(', ')

    table.update_item(
        Key={'userId': user_id},
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_values
    )

    return response(200, {
        'message': 'User updated successfully',
        'userId': user_id
    })

# 사용자 삭제
def delete_user(event):
    path = event.get('path', '')
    user_id = path.split('/')[-1]

    table.delete_item(Key={'userId': user_id})

    return response(200, {
        'message': 'User deleted successfully',
        'userId': user_id
    })

# HTTP 응답 생성 헬퍼 함수
def response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }
```

**Deploy** 버튼 클릭하여 저장

---

## 실습 4: API Gateway 라우트 추가

### 4.1 /users 리소스 생성

1. API Gateway 콘솔에서 `HelloWorldAPI` 선택

2. **작업** → **리소스 생성** 클릭

3. 설정:
   * **리소스 이름**: `users`
   * **리소스 경로**: `/users`

4. **리소스 생성** 클릭

### 4.2 /users에 메서드 추가

### POST 메서드 (사용자 생성)

1. `/users` 리소스 선택

2. **작업** → **메서드 생성** → **POST**

3. 설정:
   * Lambda 프록시 통합 사용: ✅
   * Lambda 함수: `HelloWorldFunction`

4. **저장** → **확인**

### GET 메서드 (전체 조회)

1. `/users` 리소스 선택

2. **작업** → **메서드 생성** → **GET**

3. 동일하게 Lambda 연동

4. **저장** → **확인**

### 4.3 /users/{userId} 리소스 생성

1. `/users` 리소스 선택

2. **작업** → **리소스 생성**

3. 설정:
   * **리소스 이름**: `user`
   * **리소스 경로**: `{userId}` (중괄호 포함!)

4. **리소스 생성** 클릭

### 4.4 /{userId}에 메서드 추가

동일한 방법으로 다음 메서드 추가:

* **GET** (특정 사용자 조회)

* **PUT** (사용자 수정)

* **DELETE** (사용자 삭제)

모두 Lambda 프록시 통합으로 `HelloWorldFunction` 연결

### 4.5 CORS 활성화

1. `/users` 리소스 선택

2. **작업** → **CORS 활성화**

3. **CORS를 활성화하고 기존의 CORS 헤더를 대체** 클릭

4. `/{userId}` 리소스에도 동일하게 CORS 활성화

### 4.6 API 배포

1. **작업** → **API 배포**

2. 배포 스테이지: `dev`

3. **배포** 클릭

---

## 실습 5: API 테스트

### 5.1 사용자 생성 (POST)

```
curl -X POST https://YOUR-API-URL/dev/users \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "user001",
    "name": "홍길동",
    "email": "hong@example.com"
  }'
```

**기대 출력:**

```
{
  "message": "User created successfully",
  "user": {
    "userId": "user001",
    "name": "홍길동",
    "email": "hong@example.com",
    "createdAt": "2025-09-30T10:30:00.123456"
  }
}
```

### 5.2 추가 사용자 생성

```
# 사용자 2
curl -X POST https://YOUR-API-URL/dev/users \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "user002",
    "name": "김철수",
    "email": "kim@example.com"
  }'

# 사용자 3
curl -X POST https://YOUR-API-URL/dev/users \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "user003",
    "name": "이영희",
    "email": "lee@example.com"
  }'
```

### 5.3 전체 사용자 조회 (GET)

```
curl https://YOUR-API-URL/dev/users
```

**기대 출력:**

```
{
  "count": 3,
  "users": [
    {
      "userId": "user001",
      "name": "홍길동",
      "email": "hong@example.com",
      "createdAt": "2025-09-30T10:30:00.123456"
    },
    {
      "userId": "user002",
      "name": "김철수",
      "email": "kim@example.com",
      "createdAt": "2025-09-30T10:31:00.123456"
    },
    {
      "userId": "user003",
      "name": "이영희",
      "email": "lee@example.com",
      "createdAt": "2025-09-30T10:32:00.123456"
    }
  ]
}
```

### 5.4 특정 사용자 조회 (GET)

```
curl https://YOUR-API-URL/dev/users/user001
```

**기대 출력:**

```
{
  "user": {
    "userId": "user001",
    "name": "홍길동",
    "email": "hong@example.com",
    "createdAt": "2025-09-30T10:30:00.123456"
  }
}
```

### 5.5 사용자 정보 수정 (PUT)

```
curl -X PUT https://YOUR-API-URL/dev/users/user001 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "홍길동(수정)",
    "email": "newhong@example.com"
  }'
```

**기대 출력:**

```
{
  "message": "User updated successfully",
  "userId": "user001"
}
```

### 5.6 사용자 삭제 (DELETE)

```
curl -X DELETE https://YOUR-API-URL/dev/users/user003
```

**기대 출력:**

```
{
  "message": "User deleted successfully",
  "userId": "user003"
}
```

---

## 실습 6: DynamoDB 콘솔에서 확인

### 6.1 데이터 확인

1. DynamoDB 콘솔로 이동

2. `Users` 테이블 선택

3. **항목 탐색** 클릭

4. **Scan** 실행

5. 저장된 사용자 데이터 확인

### 6.2 수동으로 데이터 추가

1. **항목 생성** 클릭

2. JSON 형식으로 입력:

```
{
  "userId": "user999",
  "name": "테스트유저",
  "email": "test@example.com",
  "createdAt": "2025-09-30T12:00:00"
}
```

1. **항목 생성** 클릭

2. API로 조회해서 확인

---

## 실습 7: 에러 처리 테스트

### 7.1 필수 필드 누락

```
curl -X POST https://YOUR-API-URL/dev/users \
  -H "Content-Type: application/json" \
  -d '{"name": "홍길동"}'
```

**기대 출력:**

```
{
  "error": "userId, name, email are required"
}
```

### 7.2 존재하지 않는 사용자 조회

```
curl https://YOUR-API-URL/dev/users/nonexistent
```

**기대 출력:**

```
{
  "error": "User not found"
}
```

---

## 실습 8: CloudWatch 로그 확인

### 8.1 로그 보기

1. Lambda 콘솔에서 함수 선택

2. **모니터링** 탭

3. **CloudWatch에서 로그 보기** 클릭

4. 최근 로그 스트림 선택

5. 다음 항목 확인:
   * 요청 이벤트
   * DynamoDB 작업 로그
   * 에러 로그 (있다면)

---

## 🎯 주요 개념 정리

### DynamoDB 기본 용어

* **테이블(Table)**: 데이터를 저장하는 컬렉션

* **항목(Item)**: 하나의 레코드 (행)

* **속성(Attribute)**: 필드 (열)

* **파티션 키(Partition Key)**: 고유 식별자 (userId)

### DynamoDB 작업

* **PutItem**: 데이터 저장/덮어쓰기

* **GetItem**: 특정 항목 조회 (파티션 키로)

* **Scan**: 전체 테이블 스캔 (비효율적, 데이터 많으면 주의)

* **Query**: 조건으로 검색

* **UpdateItem**: 항목 수정

* **DeleteItem**: 항목 삭제

### Lambda에서 boto3 사용

```
import boto3

# DynamoDB 리소스 (추천)
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('테이블명')

# 또는 클라이언트 (저수준 API)
dynamodb = boto3.client('dynamodb')
```

---

## 🚀 추가 개선 사항

### 1. 페이지네이션 추가

대량 데이터 조회 시 필요:

```
def get_all_users(event):
    last_key = event.get('queryStringParameters', {}).get('lastKey')

    if last_key:
        result = table.scan(ExclusiveStartKey={'userId': last_key})
    else:
        result = table.scan(Limit=10)

    return response(200, {
        'users': result['Items'],
        'lastKey': result.get('LastEvaluatedKey')
    })
```

### 2. 입력 검증 강화

이메일 형식 검증:

```
import re

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None
```

### 3. 중복 체크

동일한 userId로 재생성 방지:

```
table.put_item(
    Item=item,
    ConditionExpression='attribute_not_exists(userId)'
)
```

---

## 정리

1. **DynamoDB 테이블 삭제**:
   * DynamoDB 콘솔 → Users 테이블 → 테이블 삭제

2. **Lambda 함수 권한 제거**:
   * IAM 콘솔 → 역할 → 인라인 정책 삭제

3. **API Gateway 리소스 삭제**:
   * /users 리소스 삭제 → API 재배포

---