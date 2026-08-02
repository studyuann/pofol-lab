---
title: "Bedrock Agent를 Python 호출하기"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "클라우드 자동화를 위한 파이썬 프로그래밍", "9장 Amazon Bedrock과 RAG를 이용한 운영 시스템 챗봇 만들기"]
is_public: true
draft: false
---

# **Bedrock Agent를 Python 호출하기**

1. **터미널에서 실행하는 CLI 챗봇**

2. **FastAPI 백엔드로 만드는 챗봇 API**

Bedrock Agent는 Python에서 `bedrock-agent-runtime` 클라이언트의 `invoke_agent()` API로 호출한다.

---

# 1. 실습 폴더 구성

먼저 작업 폴더를 만든다.

```
mkdir bedrock-agent-chatbot
cd bedrock-agent-chatbot
```

최종 폴더 구조는 다음과 같다.

```
bedrock-agent-chatbot/
├── requirements.txt
├── .env
├── cli_chatbot.py
└── api_server.py
```

---

# 2. 패키지 설치

## `requirements.txt`

```
boto3
botocore
python-dotenv
fastapi
uvicorn
pydantic
```

설치한다.

```
pip install -r requirements.txt
```

---

# 3. 환경 변수 파일 작성

## `.env`

```
AWS_PROFILE=instructor
AWS_REGION=ap-northeast-2

BEDROCK_AGENT_ID=여기에_에이전트_ID
BEDROCK_AGENT_ALIAS_ID=여기에_에이전트_ALIAS_ID
```

예시는 다음과 같다.

```
AWS_PROFILE=instructor
AWS_REGION=ap-northeast-2

BEDROCK_AGENT_ID=ABCDEFGHIJ
BEDROCK_AGENT_ALIAS_ID=TSTALIASID
```

## 값 확인 방법

### Agent ID

Bedrock 콘솔에서 확인한다.

```
Amazon Bedrock
→ Agents
→ 생성한 Agent 선택
→ Agent overview
→ Agent ID 확인
```

### Agent Alias ID

Agent를 테스트하거나 애플리케이션에서 호출하려면 Alias가 필요하다.

콘솔에서 확인한다.

```
Amazon Bedrock
→ Agents
→ 생성한 Agent 선택
→ Aliases
→ Alias ID 확인
```

테스트용 Alias를 사용하면 보통 다음 값일 수 있다.

```
TSTALIASID
```

운영용 Alias를 따로 만들었다면 해당 Alias ID를 사용한다.

---

# 4. AWS 로그인 확인

실습에서 `aws login --profile` 또는 SSO 기반 임시 자격 증명을 사용하고 있다면 먼저 로그인한다.

```
aws sso login --profile instructor
```

또는 실습 환경에서 사용 중인 방식이 다음이라면 그대로 사용한다.

```
aws login --profile instructor
```

현재 인증이 정상인지 확인한다.

```
aws sts get-caller-identity --profile instructor
```

정상 출력 예시는 다음과 같다.

```
{
    "UserId": "AROAXXXXXXX:user",
    "Account": "123456789012",
    "Arn": "arn:aws:sts::123456789012:assumed-role/..."
}
```

---

# 5. CLI 챗봇 코드

## `cli_chatbot.py`

```
import os
import uuid
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv


load_dotenv()


AWS_PROFILE = os.getenv("AWS_PROFILE", "default")
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
AGENT_ID = os.getenv("BEDROCK_AGENT_ID")
AGENT_ALIAS_ID = os.getenv("BEDROCK_AGENT_ALIAS_ID")


def create_bedrock_agent_client():
    """
    Bedrock Agent Runtime 클라이언트를 생성한다.

    AWS_PROFILE 환경 변수가 있으면 해당 프로필을 사용한다.
    실습에서는 aws login --profile 또는 aws sso login --profile로
    발급받은 임시 자격 증명을 그대로 사용한다.
    """

    session = boto3.Session(
        profile_name=AWS_PROFILE,
        region_name=AWS_REGION
    )

    client = session.client("bedrock-agent-runtime")
    return client


def read_agent_response(response):
    """
    Bedrock Agent invoke_agent 응답에서 최종 답변 텍스트를 추출한다.

    invoke_agent()의 응답은 completion 이벤트 스트림 형태이다.
    각 event 안에 chunk가 있고, chunk 안의 bytes 값을 디코딩하면
    Agent가 생성한 답변 텍스트를 얻을 수 있다.
    """

    answer_parts = []

    for event in response.get("completion", []):
        if "chunk" in event:
            chunk = event["chunk"]
            byte_data = chunk.get("bytes")

            if byte_data:
                text = byte_data.decode("utf-8")
                answer_parts.append(text)

        elif "trace" in event:
            # trace는 Agent의 추론/도구 호출 과정을 확인할 때 사용 가능하다.
            # 기본 챗봇 출력에서는 생략한다.
            pass

    return "".join(answer_parts)


def ask_agent(client, session_id, question):
    """
    Bedrock Agent에게 질문을 전달하고 답변을 반환한다.

    session_id는 대화 세션을 구분하는 값이다.
    같은 session_id를 계속 사용하면 Agent가 이전 대화 맥락을 이어갈 수 있다.
    """

    response = client.invoke_agent(
        agentId=AGENT_ID,
        agentAliasId=AGENT_ALIAS_ID,
        sessionId=session_id,
        inputText=question
    )

    answer = read_agent_response(response)
    return answer


def validate_env():
    """
    필수 환경 변수가 설정되어 있는지 확인한다.
    """

    if not AGENT_ID:
        raise ValueError("BEDROCK_AGENT_ID 환경 변수가 설정되지 않았음")

    if not AGENT_ALIAS_ID:
        raise ValueError("BEDROCK_AGENT_ALIAS_ID 환경 변수가 설정되지 않았음")


def main():
    """
    터미널 기반 챗봇 실행 함수이다.

    사용자가 질문을 입력하면 Bedrock Agent를 호출하고,
    Agent의 답변을 화면에 출력한다.
    """

    try:
        validate_env()
        client = create_bedrock_agent_client()

        session_id = str(uuid.uuid4())

        print("====================================")
        print("Bedrock Agent 인프라 운영 챗봇")
        print("종료하려면 exit 또는 quit 입력")
        print("====================================")
        print(f"session_id: {session_id}")
        print()

        while True:
            question = input("사용자> ").strip()

            if question.lower() in ["exit", "quit"]:
                print("챗봇을 종료함")
                break

            if not question:
                continue

            try:
                answer = ask_agent(client, session_id, question)
                print()
                print("챗봇>")
                print(answer)
                print()

            except ClientError as e:
                print("AWS API 호출 중 오류 발생")
                print(e)

            except Exception as e:
                print("챗봇 처리 중 오류 발생")
                print(e)

    except NoCredentialsError:
        print("AWS 자격 증명을 찾을 수 없음")
        print("aws login --profile 또는 aws sso login --profile을 먼저 실행해야 함")

    except Exception as e:
        print("프로그램 시작 중 오류 발생")
        print(e)


if __name__ == "__main__":
    main()
```

---

# 6. CLI 챗봇 실행

```
python cli_chatbot.py
```

실행 후 질문을 입력한다.

```
사용자> test-svr 현재 상태 알려줘
```

예상 답변은 다음과 같다.

```
챗봇>
test-svr 인스턴스의 현재 상태는 running입니다.
인스턴스 ID는 i-0123456789abcdef0이고, Private IP는 10.0.1.10입니다.
```

통합 질문도 가능하다.

```
사용자> 지금 test-svr 상태는 어떻고, 정기 패치 일자는 언제야?
```

예상 답변은 다음과 같다.

```
챗봇>
test-svr 인스턴스의 현재 상태는 running입니다.

정기 패치 일정은 운영 매뉴얼 기준으로 매월 둘째 주 수요일 22:00입니다.
패치 전에는 백업 상태, 서비스 영향도, 인스턴스 상태를 사전에 확인하는 것이 좋습니다.
```

---

# 7. CLI 코드 설명

## 7.1 Bedrock Agent Runtime 클라이언트 생성

```
session = boto3.Session(
    profile_name=AWS_PROFILE,
    region_name=AWS_REGION
)

client = session.client("bedrock-agent-runtime")
```

`boto3.Session()`은 AWS API 호출에 사용할 인증 정보와 리전 정보를 담는 객체이다.

여기서는 `.env`에 지정한 값을 사용한다.

```
AWS_PROFILE=instructor
AWS_REGION=ap-northeast-2
```

따라서 코드는 내부적으로 다음 프로필을 사용한다.

```
--profile instructor
```

즉, CLI에서는 다음처럼 직접 프로필을 붙이지만,

```
aws ec2 describe-instances --profile instructor
```

Python 코드에서는 다음처럼 세션에 프로필을 지정한다.

```
boto3.Session(profile_name="instructor")
```

---

## 7.2 `invoke_agent()` 호출

```
response = client.invoke_agent(
    agentId=AGENT_ID,
    agentAliasId=AGENT_ALIAS_ID,
    sessionId=session_id,
    inputText=question
)
```

각 인자의 의미는 다음과 같다.

| 인자 | 의미 |
| --- | --- |
| `agentId` | 호출할 Bedrock Agent ID |
| `agentAliasId` | 호출할 Agent Alias ID |
| `sessionId` | 대화 세션 ID |
| `inputText` | 사용자가 입력한 질문 |

AWS 공식 예제에서도 Python Boto3로 Agent를 호출할 때 `agent_id`, `agent_alias_id`, `session_id`, `prompt`를 전달하는 구조를 사용한다. ([GitHub](https://github.com/awsdocs/aws-doc-sdk-examples/blob/main/python/example_code/bedrock-agent-runtime/bedrock_agent_runtime_wrapper.py?utm_source=chatgpt.com))

---

## 7.3 `sessionId`가 필요한 이유

```
session_id = str(uuid.uuid4())
```

`sessionId`는 하나의 대화를 구분하는 ID이다.

예를 들어 사용자가 처음에 이렇게 질문했다고 하자.

```
test-svr 상태 알려줘
```

그다음에 이렇게 물어볼 수 있다.

```
그 서버의 패치 일정도 알려줘
```

이때 같은 `sessionId`를 사용하면 Agent가 앞에서 말한 `test-svr`라는 문맥을 이어갈 수 있다.

---

## 7.4 응답 읽기

```
for event in response.get("completion", []):
    if "chunk" in event:
        chunk = event["chunk"]
        byte_data = chunk.get("bytes")

        if byte_data:
            text = byte_data.decode("utf-8")
            answer_parts.append(text)
```

`invoke_agent()` 응답은 단순 문자열이 아니라 이벤트 스트림 구조이다.

실제 답변 텍스트는 보통 다음 위치에 들어 있다.

```
response["completion"] → event → chunk → bytes
```

`bytes`는 바이트 데이터이므로 사람이 읽을 수 있는 문자열로 바꾸기 위해 다음 코드를 사용한다.

```
byte_data.decode("utf-8")
```

---

# 8. FastAPI 챗봇 API 코드

이번에는 프론트엔드와 연결할 수 있도록 FastAPI 백엔드 형태로 만든다.

## `api_server.py`

```
import os
import uuid
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


load_dotenv()


AWS_PROFILE = os.getenv("AWS_PROFILE", "default")
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
AGENT_ID = os.getenv("BEDROCK_AGENT_ID")
AGENT_ALIAS_ID = os.getenv("BEDROCK_AGENT_ALIAS_ID")


app = FastAPI(
    title="Bedrock Agent Chatbot API",
    description="Bedrock Agent를 호출하는 인프라 운영 챗봇 API",
    version="1.0.0"
)


class ChatRequest(BaseModel):
    """
    사용자의 질문 요청 형식이다.

    question:
        사용자가 입력한 질문

    session_id:
        대화 세션 ID이다.
        없으면 서버에서 새로 생성한다.
        같은 session_id를 계속 전달하면 대화 맥락을 유지할 수 있다.
    """

    question: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    """
    챗봇 응답 형식이다.

    session_id:
        현재 대화 세션 ID

    answer:
        Bedrock Agent가 생성한 답변
    """

    session_id: str
    answer: str


def create_bedrock_agent_client():
    """
    Bedrock Agent Runtime 클라이언트를 생성한다.
    """

    session = boto3.Session(
        profile_name=AWS_PROFILE,
        region_name=AWS_REGION
    )

    return session.client("bedrock-agent-runtime")


def validate_env():
    """
    필수 환경 변수를 확인한다.
    """

    if not AGENT_ID:
        raise RuntimeError("BEDROCK_AGENT_ID 환경 변수가 설정되지 않았음")

    if not AGENT_ALIAS_ID:
        raise RuntimeError("BEDROCK_AGENT_ALIAS_ID 환경 변수가 설정되지 않았음")


def read_agent_response(response):
    """
    Bedrock Agent 응답 이벤트 스트림에서 답변 텍스트를 추출한다.
    """

    answer_parts = []

    for event in response.get("completion", []):
        if "chunk" in event:
            chunk = event["chunk"]
            byte_data = chunk.get("bytes")

            if byte_data:
                answer_parts.append(byte_data.decode("utf-8"))

    return "".join(answer_parts)


def invoke_bedrock_agent(question, session_id):
    """
    Bedrock Agent를 호출하고 답변을 반환한다.
    """

    client = create_bedrock_agent_client()

    response = client.invoke_agent(
        agentId=AGENT_ID,
        agentAliasId=AGENT_ALIAS_ID,
        sessionId=session_id,
        inputText=question
    )

    return read_agent_response(response)


@app.get("/")
def root():
    """
    API 서버 상태 확인용 엔드포인트이다.
    """

    return {
        "message": "Bedrock Agent Chatbot API is running"
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    사용자의 질문을 받아 Bedrock Agent에 전달하고 답변을 반환한다.
    """

    try:
        validate_env()

        question = request.question.strip()

        if not question:
            raise HTTPException(
                status_code=400,
                detail="question 값이 비어 있음"
            )

        session_id = request.session_id or str(uuid.uuid4())

        answer = invoke_bedrock_agent(
            question=question,
            session_id=session_id
        )

        return ChatResponse(
            session_id=session_id,
            answer=answer
        )

    except HTTPException:
        raise

    except NoCredentialsError:
        raise HTTPException(
            status_code=500,
            detail="AWS 자격 증명을 찾을 수 없음"
        )

    except ClientError as e:
        raise HTTPException(
            status_code=500,
            detail=f"AWS API 호출 중 오류 발생: {str(e)}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"챗봇 처리 중 오류 발생: {str(e)}"
        )
```

---

# 9. FastAPI 서버 실행

```
uvicorn api_server:app --reload --host 127.0.0.1 --port 8000
```

브라우저에서 접속한다.

```
http://127.0.0.1:8000
```

정상 출력은 다음과 같다.

```
{
  "message": "Bedrock Agent Chatbot API is running"
}
```

Swagger UI는 다음 주소에서 확인한다.

```
http://127.0.0.1:8000/docs
```

---

# 10. FastAPI 챗봇 테스트

## 10.1 첫 질문

```
curl -X POST "http://127.0.0.1:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "test-svr 현재 상태 알려줘"
  }'
```

응답 예시는 다음과 같다.

```
{
  "session_id": "df4c9a7f-01d3-4c35-9e1a-9b53dfc66d21",
  "answer": "test-svr 인스턴스의 현재 상태는 running입니다..."
}
```

---

## 10.2 같은 세션으로 이어서 질문

위 응답에서 받은 `session_id`를 다시 사용한다.

```
curl -X POST "http://127.0.0.1:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "df4c9a7f-01d3-4c35-9e1a-9b53dfc66d21",
    "question": "그 서버의 정기 패치 일정도 알려줘"
  }'
```

같은 `session_id`를 전달하면 이전 대화 흐름을 이어가는 형태로 사용할 수 있다.

---

# 11. 프론트엔드에서 호출할 때의 요청 형식

프론트엔드는 `/chat` API로 다음 JSON을 보내면 된다.

```
{
  "question": "지금 test-svr 상태는 어떻고, 정기 패치 일자는 언제야?",
  "session_id": "선택값"
}
```

`session_id`가 없으면 서버가 새로 만든다.

응답은 다음 형식이다.

```
{
  "session_id": "대화 세션 ID",
  "answer": "챗봇 답변"
}
```

---

# 12. 필요한 IAM 권한

Python 코드가 Bedrock Agent를 호출하려면 실행 주체에 Agent 호출 권한이 있어야 한다.

최소 개념은 다음과 같다.

```
{
  "Effect": "Allow",
  "Action": [
    "bedrock:InvokeAgent"
  ],
  "Resource": "*"
}
```

실습에서는 리소스를 `*`로 둘 수 있지만, 실제 운영에서는 특정 Agent ARN으로 제한하는 것이 좋다.

예시는 다음과 같다.

```
{
  "Effect": "Allow",
  "Action": [
    "bedrock:InvokeAgent"
  ],
  "Resource": [
    "arn:aws:bedrock:ap-northeast-2:123456789012:agent-alias/ABCDEFGHIJ/*"
  ]
}
```

---

# 13. 실습 확인 질문

학생들이 아래 질문을 넣어보면 된다.

## EC2 상태 조회 질문

```
test-svr 현재 상태 알려줘
```

```
test-svr 지금 실행 중이야?
```

```
test-svr Private IP도 알려줘
```

## Knowledge Base 검색 질문

```
정기 패치 일자는 언제야?
```

```
장애 발생 시 1차 조치 절차는 뭐야?
```

```
서버 패치 전에 확인해야 할 항목은 뭐야?
```

## 통합 질문

```
지금 test-svr 상태는 어떻고, 정기 패치 일자는 언제야?
```

```
test-svr 상태 확인하고 패치 전 점검 항목도 알려줘
```

---

# 14. 자주 발생하는 오류

## 14.1 `AccessDeniedException`

예시:

```
User is not authorized to perform: bedrock:InvokeAgent
```

원인:

```
현재 AWS 프로필에 Bedrock Agent 호출 권한이 없음
```

해결:

```
IAM 사용자 또는 역할에 bedrock:InvokeAgent 권한 추가
```

---

## 14.2 `ResourceNotFoundException`

원인 후보:

```
Agent ID가 잘못됨
Agent Alias ID가 잘못됨
리전이 잘못됨
Agent가 Prepare되지 않았음
Alias가 생성되지 않았음
```

해결:

```
.env 파일의 AWS_REGION, BEDROCK_AGENT_ID, BEDROCK_AGENT_ALIAS_ID 확인
```

---

## 14.3 AWS 자격 증명 오류

예시:

```
Unable to locate credentials
```

해결:

```
aws sso login --profile instructor
```

또는 실습 환경에 맞게 다음을 실행한다.

```
aws login --profile instructor
```

그리고 `.env` 파일을 확인한다.

```
AWS_PROFILE=instructor
```

---

# 15. 정리

이번 코드의 핵심 흐름은 다음과 같다.

```
사용자 질문
   ↓
Python CLI 또는 FastAPI
   ↓
boto3 bedrock-agent-runtime 클라이언트
   ↓
invoke_agent()
   ↓
Bedrock Agent
   ├─ Lambda Action Group 호출
   └─ Knowledge Base 검색
   ↓
응답 이벤트 스트림
   ↓
chunk.bytes 디코딩
   ↓
사용자에게 답변 출력
```

이제 콘솔 테스트가 아니라 Python 애플리케이션에서 직접 Bedrock Agent 기반 챗봇을 호출할 수 있다.

### 과제 : FastAPI를 이용해 에이전트기반 운영 챗봇 만들기