---
title: "8장 Amazon Bedrock 기본 이해"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "클라우드 자동화를 위한 파이썬 프로그래밍"]
is_public: true
draft: false
---

# 8장. Amazon Bedrock 기본 이해

## 장 개요

이 장에서는 Amazon Bedrock의 기본 개념을 이해하고, Python과 `boto3`를 사용해 Bedrock Runtime을 호출하는 방법을 학습한다.

생성형 AI 모델을 AWS 환경에서 호출하는 기본 흐름을 익히고, 이후 RAG 기반 문서 질의응답 챗봇 구현으로 확장할 수 있는 기초를 마련한다.

이 장의 핵심 흐름은 다음과 같다.

```
운영 데이터 준비
        ↓
프롬프트 구성
        ↓
Bedrock Runtime 호출
        ↓
모델 응답 수신
        ↓
자연어 요약 결과 생성
        ↓
RAG 챗봇 구현으로 확장
```

---

## 학습 목표

* Amazon Bedrock이 어떤 서비스인지 설명할 수 있다.

* Foundation Model의 의미를 설명할 수 있다.

* Bedrock Runtime의 역할을 설명할 수 있다.

* `bedrock` client와 `bedrock-runtime` client의 차이를 구분할 수 있다.

* Bedrock 모델 호출에 `modelId`가 필요한 이유를 설명할 수 있다.

* AWS CLI 프로필 기반으로 `boto3` Bedrock Runtime client를 생성할 수 있다.

* Converse API를 사용해 Bedrock 모델에 메시지를 전달할 수 있다.

* Bedrock 응답에서 생성된 텍스트만 추출할 수 있다.

* 운영 데이터를 프롬프트에 넣어 요약 결과를 생성할 수 있다.

* Bedrock 응답 결과를 파일로 저장할 수 있다.

* 일반 프롬프트 방식과 RAG 방식의 차이를 설명할 수 있다.

---

## 주요 키워드

* Amazon Bedrock

* Foundation Model

* Bedrock Runtime

* Model ID

* Converse API

* Prompt

* boto3

* RAG

* Knowledge Base

* RetrieveAndGenerate

---

# 8.1 Amazon Bedrock이란 무엇인가

## 1. Amazon Bedrock의 의미

Amazon Bedrock은   
AWS(Amazon Web Services)에서 제공하는 **생성형 AI 애플리케이션 구축 및 확장을 위한 완전관리형 서비스**이다.

생성형 AI를 사용하려면 일반적으로 다음과 같은 요소가 필요하다.

* 대규모 AI 모델

* 모델 실행 인프라

* GPU 자원

* 모델 API 서버

* 인증 및 권한 관리

* 보안 통제

* 애플리케이션 연동 코드

직접 AI 모델을 운영한다면 위 요소를 모두 구성해야 한다. 하지만 Bedrock을 사용하면 사용자는 모델 서버를 직접 운영하지 않고, AWS API를 통해 Foundation Model을 호출할 수 있다.

**파운데이션 모델**은 방대한 양의 광범위한 데이터를 바탕으로 학습되어, 하나의 모델로 다양한 하위 작업(Downstream Tasks)을 수행할 수 있는 기반이 되는 AI 모델을 의미한다. 언어모델(LLM), 이미지생성모델 등.  
  
즉, Bedrock은 다음과 같이 이해하면 된다.

```
AWS 환경에서 여러 생성형 AI 모델을 API로 사용할 수 있게 해주는 관리형 서비스
```

여기서 중요한 점은 Bedrock이 “하나의 모델 이름”이 아니라는 것이다. Bedrock은 여러 Foundation Model에 접근할 수 있게 해주는 플랫폼이다.

Bedrock을 사용하면 다음과 같은 작업을 할 수 있다.

* 텍스트 생성

* 문장 요약

* 질의응답

* 문서 기반 답변 생성

* 코드 생성 보조

* 이미지 생성

* 임베딩 생성

* RAG 챗봇 구성

이 장에서는 다음 두 가지 흐름에 집중한다.

```
1. Python 코드에서 Bedrock 모델 호출하기
2. 문서 기반 RAG 챗봇 구현을 위한 기본 구조 이해하기
```

---

## 2. Bedrock을 사용하는 이유

앞 장까지의 자동화 결과는 대부분 구조화된 데이터였다.

예를 들어 로그 분석 결과는 다음과 같은 형태일 수 있다.

```
상태코드별 요청 개수
200: 152
401: 5
403: 3
500: 12

가장 많이 발생한 경로: /api/items
```

이 데이터는 프로그램이 처리하기에는 좋다. 하지만 운영자가 바로 읽고 판단하기에는 다소 거칠다.

운영자는 보통 다음과 같은 형태의 설명을 원한다.

```
전체 요청 중 200 응답이 대부분이지만 500 오류가 12건 발생해 서버 측 오류를 확인할 필요가 있다.
401과 403 응답도 일부 확인되므로 인증 또는 권한 관련 요청도 함께 점검하는 것이 좋다.
우선 /api/items 경로와 관련된 애플리케이션 로그를 확인하는 것이 적절하다.
```

즉, Bedrock은 운영 자동화 결과를 사람이 읽기 쉬운 자연어 문장으로 바꾸는 데 사용할 수 있다.

이 과정에서는 Bedrock을 다음과 같은 역할로 이해한다.

```
운영 자동화 결과를 자연어로 설명해주는 AI 후처리 계층
```

---

## 3. Bedrock을 사용한 운영 자동화 예시

Bedrock은 다음과 같은 운영 자동화 흐름에 연결할 수 있다.

| 자동화 결과 | Bedrock 활용 |
| --- | --- |
| 로그 상태코드 집계 | 운영 요약 문장 생성 |
| ERROR 로그 목록 | 우선 점검 항목 정리 |
| EC2 인스턴스 상태 목록 | 현재 운영 상태 요약 |
| S3 업로드 결과 | 작업 완료 보고 문장 생성 |
| IAM 사용자/정책 조회 결과 | 보안 점검 요약 생성 |
| 운영 매뉴얼 문서 | 문서 기반 질의응답 챗봇 구성 |

처음에는 짧은 운영 데이터를 프롬프트에 직접 넣어 요약한다.

이후 문서가 많아지면 RAG 구조로 확장한다.

---

# 8.2 학습 범위

## Bedrock의 전체 기능

Bedrock에는 다양한 기능이 있다.

대표적으로 다음 기능들이 있다.

* Foundation Model 호출

* Converse API

* InvokeModel API

* Knowledge Base

* Guardrails

* Agents

* 모델 평가

모델 커스터마이징

├── 프롬프트 엔지니어링  
│ └── 사용자의 입력이나 지시문을 잘 설계해서 원하는 답변을 유도하는 방법.  
│ 모델 자체를 바꾸는 것이 아니라, 질문 방식과 맥락 제공 방식을 조정함.  
│  
├── 시스템 프롬프트 설계  
│ └── 모델의 역할, 답변 규칙, 금지 사항, 응답 형식을 사전에 지정하는 방법.  
│ 예: "제공된 운영 데이터만 근거로 답변한다", "추측하지 않는다".  
│  
├── RAG  
│ └── 외부 문서나 내부 지식을 검색해서 모델에게 함께 제공하는 방법.  
│ 모델이 모르는 최신 정보나 내부 문서를 근거로 답변하게 할 때 사용함.  
│  
├── Tool Calling / Function Calling  
│ └── 모델 또는 백엔드가 외부 도구, API, 함수를 호출해 실제 데이터를 가져오거나 작업을 수행하는 방식.  
│ 예: EC2 상태 조회, CloudWatch 지표 조회, 티켓 생성, DB 조회.  
│  
├── 파인튜닝  
│ └── 입력-출력 예시 데이터를 추가 학습시켜 모델의 응답 패턴을 특정 작업에 맞추는 방법.  
│ 답변 형식, 분류 기준, 문체, 반복 업무 패턴을 맞출 때 사용함.  
│  
├── Continued Pre-training  
│ └── 대량의 도메인 텍스트를 추가로 학습시켜 특정 분야의 언어와 개념에 더 익숙하게 만드는 방법.  
│ 전문 용어, 산업 문서, 내부 기술 문서 스타일을 익히게 할 때 사용함.  
│  
└── Guardrail / 출력 제어  
└── 모델이 부적절하거나 위험한 답변을 하지 않도록 제한 규칙을 두는 방법.  
개인정보, 보안 정보, 위험 작업, 금지 표현, 답변 범위를 제어할 때 사용함.

배치 추론

입력 데이터 여러 개 → 한 번에 모델 처리 → 결과 파일로 저장

이 장에서는 다음 범위만 다룬다.

```
1. Bedrock이 무엇인지 이해한다.
2. Bedrock Runtime이 무엇인지 이해한다.
3. boto3로 Bedrock Runtime client를 생성한다.
4. Converse API로 모델을 호출한다.
5. 운영 데이터를 프롬프트에 넣어 요약한다.
6. 이 구조가 RAG 챗봇으로 확장된다는 점을 이해한다.
```

---

# 8.3 Foundation Model과 Model ID 이해

## 1. Foundation Model이란 무엇인가

Foundation Model은 대규모 데이터로 미리 학습된 범용 AI 모델이다.

사용자는 이 모델을 처음부터 직접 학습시키지 않는다. 이미 준비된 모델을 선택하고, 입력을 전달해 결과를 받는다.

예를 들어 사용자가 다음 질문을 입력한다고 가정한다.

```
Amazon Bedrock을 쉽게 설명해줘.
```

모델은 이 입력을 바탕으로 다음과 같은 응답을 생성한다.

```
Amazon Bedrock은 AWS에서 제공하는 생성형 AI 서비스로, 사용자가 직접 모델 인프라를 운영하지 않고도 다양한 AI 모델을 API로 사용할 수 있게 해준다.
```

Bedrock은 여러 Foundation Model을 사용할 수 있도록 제공한다. 모델마다 지원하는 기능, 입력 형식, 리전, 비용, 성능이 다를 수 있다.

이 과정에서는 주로 텍스트 응답을 생성하는 모델을 사용한다.

---

## 2. Model ID가 필요한 이유

Bedrock 모델을 코드에서 호출할 때는 “Claude”, “Nova”, “Llama” 같은 이름으로 호출하지 않는다.

실제 코드에서는 `modelId` 값을 지정해야 한다.

예를 들어 다음과 같은 코드가 있다.

```
MODEL_ID = "수업에서 사용할 모델 ID"
```

그리고 모델 호출 시 다음과 같이 전달한다.

```
response = bedrock.converse(
    modelId=MODEL_ID,
    messages=[
        {
            "role": "user",
            "content": [
                {"text": "Amazon Bedrock을 설명해줘."}
            ]
        }
    ]
)
```

여기서 `modelId`는 실제로 어떤 모델을 호출할지 지정하는 값이다.

실습 계정과 리전에서 사용할 수 있는 모델 ID를 미리 정해두는 것이 좋다. 모델별 지원 여부는 리전에 따라 다를 수 있으므로, 실습 전 반드시 사용할 리전에서 모델 접근 가능 여부를 확인해야 한다.

---

## 3. Model ID와 Inference Profile ID 구분

Bedrock 모델 호출에는 모델을 식별하는 값이 필요하다.

이 값은 다음 두 형태 중 하나일 수 있다.

```
1. Foundation Model ID
2. Inference Profile ID
```

Foundation Model ID는 특정 Foundation Model 자체를 가리키는 값이다.

예시는 다음과 같다.

```
amazon.nova-lite-v1:0
```

Inference Profile ID는 리전별 또는 교차 리전 호출에 사용할 수 있는 추론 프로필 값이다.

예시는 다음과 같다.

```
apac.amazon.nova-lite-v1:0
```

Python 코드에서는 이 값을 `MODEL_ID` 변수에 넣고, Converse API 호출 시 `modelId` 인자로 전달한다.

```
MODEL_ID="apac.amazon.nova-lite-v1:0"

response=bedrock.converse(
modelId=MODEL_ID,
messages=[
        {
"role":"user",
"content": [
                {"text":"Amazon Bedrock을 설명해줘."}
            ]
        }
    ]
)
```

현재 AWS 계정과 리전에서 사용할 수 있는 Foundation Model ID는 다음 명령으로 확인한다.

```
aws bedrock list-foundation-models \
--region ap-northeast-2 \
--profile lab \
--query"modelSummaries[].modelId"
```

Inference Profile ID는 다음 명령으로 확인한다.

```
aws bedrock list-inference-profiles \
--region ap-northeast-2 \
--profile lab \
--query "inferenceProfileSummaries[].inferenceProfileId"
```

조회한 값 중 현재 실습 환경에서 접근 가능한 값을 `MODEL_ID`에 지정한다.

# 8.4 Bedrock Runtime 이해

## 1. Bedrock Runtime이란 무엇인가

Bedrock Runtime은 실제 모델 추론을 수행하는 API 영역이다.

Bedrock에는 모델 목록 조회, 모델 접근 관리, Knowledge Base 관리 같은 제어 기능도 있고, 실제 모델을 호출하는 Runtime 기능도 있다.

Python에서 모델에게 질문을 보내고 답변을 받을 때 사용하는 것은 `bedrock-runtime`이다.

예를 들어 다음 코드는 Bedrock Runtime client를 생성한다.

```
import boto3

client = boto3.client("bedrock-runtime")
```

AWS CLI 프로필과 리전을 명확히 지정하기 위해 다음 형태를 사용할 수 있다.

```
import boto3

session = boto3.Session(profile_name="lab")
bedrock = session.client("bedrock-runtime",region_name="ap-northeast-2")
```

---

## 2. `bedrock` client와 `bedrock-runtime` client 차이

`bedrock`과 `bedrock-runtime`은 이름이 비슷하지만 역할이 다르다.

| 구분 | 역할 | 예시 |
| --- | --- | --- |
| `bedrock` | 모델 목록 조회, 모델 접근 관리 등 제어 작업 | 모델 목록 확인 |
| `bedrock-runtime` | 실제 모델 호출, 추론 실행 | 질문을 보내고 답변 받기 |

CLI 명령으로 보면 다음과 같이 구분할 수 있다.

```
aws bedrock list-foundation-models
```

이 명령은 모델 목록을 조회한다. 즉, 제어 작업이다.

반면 Python에서 모델에게 질문을 보낼 때는 다음과 같이 `bedrock-runtime` client를 만든다.

```
bedrock = session.client("bedrock-runtime",region_name="ap-northeast-2")
```

정리하면 다음과 같다.

```
모델을 조회하거나 관리할 때는 bedrock
모델을 실제 호출할 때는 bedrock-runtime
```

---

# 8.5 Converse API 이해

## 1. Converse API란 무엇인가

Converse API는 메시지 기반으로 Bedrock 모델을 호출하는 API이다.

기본 구조는 다음과 같다.

```
response = bedrock.converse(
    modelId=MODEL_ID,
    messages=[
        {
            "role": "user",
            "content": [
                {"text": "질문 내용"}
            ]
        }
    ]
)
```

Converse API는 메시지를 지원하는 모델에 대해 비교적 일관된 인터페이스를 제공한다. 따라서 모델별 요청 body 차이를 줄이고, 여러 모델에 대해 비슷한 코드 구조를 사용할 수 있다.

`invoke_model`을 사용하면 모델마다 요청 body 구조를 따로 익혀야 할 수 있다. 반면 `converse`는 메시지 기반 구조를 사용하므로 기초 실습에서 더 적합하다.

---

## 2. Converse API 기본 구조

Converse API 호출에는 다음 요소가 들어간다.

| 요소 | 의미 |
| --- | --- |
| `modelId` | 호출할 Bedrock 모델 ID |
| `messages` | 모델에게 전달할 메시지 목록 |
| `role` | 메시지를 보낸 주체 |
| `content` | 메시지 내용 목록 |
| `text` | 실제 텍스트 입력 |
| `inferenceConfig` | 응답 생성 옵션 |

예시는 다음과 같다.

```
response = bedrock.converse(
    modelId=MODEL_ID,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "text": "Amazon Bedrock을 쉽게 설명해줘."
                }
            ]
        }
    ],
    inferenceConfig={
        "maxTokens": 300,
        "temperature": 0.2
    }
)
```

---

## 3. `messages` 구조 이해

`messages`는 대화 메시지를 담는 배열이다.

```
messages=[
    {
        "role": "user",
        "content": [
            {
                "text": "Amazon Bedrock을 쉽게 설명해줘."
            }
        ]
    }
]
```

이 구조를 풀어보면 다음과 같다.

```
"role": "user"
```

사용자가 입력한 메시지라는 의미다.

```
"content": [
    {
        "text": "Amazon Bedrock을 쉽게 설명해줘."
    }
]
```

메시지의 실제 내용이다.

`content`가 배열인 이유는 모델에 따라 텍스트 외에 이미지 같은 다른 입력 형식을 함께 다룰 수 있기 때문이다. 하지만 여기에서는 텍스트만 사용한다.

---

## 4. `inferenceConfig` 이해

`inferenceConfig`는 모델 응답 생성 방식을 제어한다.

```
inferenceConfig={
    "maxTokens": 300,
    "temperature": 0.2
}
```

주요 항목은 다음과 같다.

| 항목 | 의미 |
| --- | --- |
| `maxTokens` | 모델이 생성할 최대 토큰 수 |
| `temperature` | 응답의 다양성 정도 |

`maxTokens`는 응답 길이를 제한한다. 값이 너무 작으면 답변이 중간에 끊길 수 있고, 값이 너무 크면 필요 이상으로 긴 응답이 생성될 수 있다.

`temperature`는 응답의 다양성을 조절한다.

값이 낮을수록 더 안정적이고 일관된 답변이 생성된다.

값이 높을수록 더 다양한 표현이 나올 수 있지만, 운영 보고나 점검 요약에서는 불필요한 추측이 늘어날 수 있다.

운영 데이터 요약에서는 보통 낮은 값을 사용하는 것이 좋다.

```
"temperature": 0.2
```

이 값은 모델이 너무 창의적으로 답하기보다, 입력 데이터에 근거해 안정적으로 답하도록 유도하기 위한 설정이다.

---

# 8.6 Bedrock 사용 전 준비사항

## 1. AWS CLI 프로필 확인

```
aws configure list-profiles
```

```
aws sts get-caller-identity --profile lab
```

---

## 2. boto3 설치 확인

```
pip show boto3
```

버전을 확인한다.

```
python -c "import boto3; print(boto3.__version__)"
```

---

## 3. Bedrock 모델 접근 권한 확인

Bedrock 모델 호출은 다음 조건을 확인해야 한다.

```
1. AWS 계정에서 Bedrock 사용이 가능한가
2. 사용할 리전에서 해당 모델이 지원되는가
3. 해당 모델에 대한 접근 권한이 있는가
4. IAM 사용자 또는 역할에 Bedrock 호출 권한이 있는가
```

실습용 최소 권한 예시는 다음과 같다.

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowBedrockInvoke",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "*"
    }
  ]
}
```

### 정책 설명

```
"Action": [
  "bedrock:InvokeModel"
]
```

Bedrock 모델 추론 호출을 허용한다.

```
"Resource": "*"
```

실습에서는 단순화를 위해 모든 리소스를 대상으로 허용한다.

운영 환경에서는 특정 모델 ARN으로 제한하는 것이 좋다.

---

# 8.7 실습 1: Bedrock Runtime client 생성하기

## 1. 실습 목표

이 실습에서는 Python 코드에서 Bedrock Runtime client를 생성한다.

아직 모델을 호출하지 않는다. 먼저 Bedrock Runtime에 접근할 수 있는 기본 client 객체를 만드는 것이 목표다.

---

## 2. 실습 파일 생성

파일명은 다음과 같이 만든다.

```
touch bedrock_client_test.py
```

---

## 3. 코드 작성

파일명: `bedrock_client_test.py`

```
import boto3

PROFILE_NAME = "lab"
REGION_NAME = "ap-northeast-2"

def get_bedrock_client():
    session = boto3.Session(profile_name=PROFILE_NAME)
    return session.client("bedrock-runtime", region_name=REGION_NAME)

bedrock = get_bedrock_client()

print("Bedrock Runtime client 생성 완료")
print(bedrock)
```

---

## 4. 실행

```
python bedrock_client_test.py
```

예상 출력은 다음과 비슷하다.

```
Bedrock Runtime client 생성 완료
<botocore.client.BedrockRuntime object at 0x...>
```

이 출력이 나오면 Bedrock Runtime client 객체 생성은 성공한 것이다.

아직 모델 호출은 하지 않았으므로, 이 단계에서는 모델 접근 권한 오류가 발생하지 않을 수도 있다.

# 8.8 실습 2: Converse API로 첫 모델 호출하기

## 1. 실습 목표

이번 실습에서는 Bedrock 모델에 간단한 질문을 보내고 응답을 받는다.

이 실습은 이후 RAG 챗봇 구현의 가장 기본이 된다.

RAG 챗봇도 결국 마지막에는 모델에게 질문과 문서 내용을 전달해 답변을 생성한다.

---

## 2. 실습 코드

파일명: `bedrock_converse_basic.py`

```
import boto3
from botocore.exceptions import ClientError

PROFILE_NAME = "lab"
REGION_NAME = "ap-northeast-2"

# 수업에서 사용할 모델 ID로 변경한다.
MODEL_ID = "apac.amazon.nova-lite-v1:0"

def get_bedrock_client():
    session = boto3.Session(profile_name=PROFILE_NAME)
    return session.client("bedrock-runtime", region_name=REGION_NAME)

def ask_bedrock(message):
    bedrock = get_bedrock_client()

    response = bedrock.converse(
        modelId=MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": message
                    }
                ]
            }
        ],
        inferenceConfig={
            "maxTokens": 300,
            "temperature": 0.2
        }
    )

    result_text = response["output"]["message"]["content"][0]["text"]
    return result_text

try:
    result = ask_bedrock("Amazon Bedrock을 한 문단으로 쉽게 설명해줘.")

    print("===== Bedrock 응답 =====")
    print(result)

except ClientError as e:
    print("AWS ClientError 발생")
    print(e.response["Error"]["Code"])
    print(e.response["Error"]["Message"])

except Exception as e:
    print("알 수 없는 오류 발생")
    print(e)
```

---

## 3. 코드 설명

```
from botocore.exceptions import ClientError
```

AWS API 호출 중 발생하는 오류를 처리하기 위해 `ClientError`를 가져온다.

예를 들어 권한 부족, 모델 접근 불가, 잘못된 모델 ID 등의 오류를 확인할 수 있다.

```
MODEL_ID = "수업에서 사용할 모델 추론 ID"
```

aws bedrock list-inference-profiles

호출할 Bedrock 모델 ID를 지정한다.

이 값은 실습 시점에 사용할 모델로 변경해야 한다.

```
def ask_bedrock(message):
```

사용자 메시지를 Bedrock에 전달하고 응답 텍스트를 반환하는 함수다.

```
response = bedrock.converse(...)
```

Bedrock Converse API를 호출한다.

```
messages=[
    {
        "role": "user",
        "content": [
            {
                "text": message
            }
        ]
    }
]
```

사용자 메시지를 전달한다.

`role`은 메시지를 보낸 주체를 의미한다.

여기서는 사용자가 질문하는 상황이므로 `"user"`를 사용한다.

```
inferenceConfig={
    "maxTokens": 300,
    "temperature": 0.2
}
```

모델 응답 생성 방식을 제어한다.

`maxTokens`는 응답의 최대 길이를 제한한다.

`temperature`는 응답의 다양성을 조절한다.

운영 요약이나 보고 문장 생성에서는 보통 낮은 값을 사용하는 것이 좋다.

```
result_text = response["output"]["message"]["content"][0]["text"]
```

Bedrock 응답 중 실제 생성된 텍스트만 추출한다.

Converse API 응답은 단순 문자열이 아니라 JSON 구조로 반환된다. 따라서 필요한 위치에서 텍스트를 꺼내야 한다.

---

## 4. 실행

```
python bedrock_converse_basic.py
```

예상 출력 예시는 다음과 같다.

```
===== Bedrock 응답 =====
Amazon Bedrock은 AWS에서 제공하는 생성형 AI 서비스로, 사용자가 직접 AI 모델 인프라를 운영하지 않고도 다양한 Foundation Model을 API로 호출해 애플리케이션에 활용할 수 있게 해준다.
```

실제 응답 문장은 사용하는 모델과 설정에 따라 달라질 수 있다.

## 5. Converse API 응답 구조 확인하기

Converse API를 호출하면 응답은 단순 문자열이 아니라 딕셔너리 형태로 반환된다.

따라서 처음 실습할 때는 응답 전체 구조를 한 번 출력해보는 것이 좋다.

파일명: `bedrock_converse_response_debug.py`

```
import json
import boto3
from botocore.exceptions import ClientError

# 설정 정보
PROFILE_NAME = "lab"
REGION_NAME = "ap-northeast-2"
# 서울 리전에서 Nova Lite 사용 시 권장되는 추론 프로필 ID
MODEL_ID = "apac.amazon.nova-lite-v1:0"

def get_bedrock_client():
    """Boto3 세션 및 Bedrock Runtime 클라이언트 생성"""
    session = boto3.Session(profile_name=PROFILE_NAME)
    return session.client("bedrock-runtime", region_name=REGION_NAME)

def main():
    bedrock = get_bedrock_client()

    # Converse API를 사용한 모델 호출
    try:
        response = bedrock.converse(
            modelId=MODEL_ID,
            messages=[
                {
                    "role": "user",
                    "content": [{"text": "Amazon Bedrock을 한 문장으로 설명해줘."}]
                }
            ],
            inferenceConfig={
                "maxTokens": 200,
                "temperature": 0.2
            }
        )

        # 응답 출력
        print("===== 모델 응답 결과 =====")
        response_text = response['output']['message']['content'][0]['text']
        print(response_text)
        
        # 상세 구조 확인이 필요한 경우 주석 해제
        # print(json.dumps(response, indent=2, ensure_ascii=False))

    except ClientError as e:
        print(f"AWS ClientError 발생: {e.response['Error']['Code']}")
        print(f"상세 메시지: {e.response['Error']['Message']}")
    except Exception as e:
        print(f"알 수 없는 오류 발생: {e}")

if __name__ == "__main__":
    main()
```

실행 명령은 다음과 같다.

```
python bedrock_converse_response_debug.py
```

이 코드에서 중요한 부분은 다음이다.

```
print(json.dumps(response,indent=2,ensure_ascii=False))
```

`json.dumps()`는 Python 딕셔너리를 JSON 문자열처럼 보기 좋게 변환한다.

`indent=2`는 들여쓰기를 2칸으로 지정한다.

`ensure_ascii=False`는 한글이 유니코드 이스케이프 형태로 출력되지 않도록 한다.

---

## 8.8.6 응답 텍스트 추출 위치 이해

Converse API 응답에서 실제 생성 텍스트는 다음 위치에 있다.

```
response["output"]["message"]["content"][0]["text"]
```

이 구조를 단계별로 풀어보면 다음과 같다.

```
response["output"]
```

모델 출력 정보가 들어 있다.

```
response["output"]["message"]
```

모델이 생성한 메시지가 들어 있다.

```
response["output"]["message"]["content"]
```

메시지 내용 목록이 들어 있다.

```
response["output"]["message"]["content"][0]
```

첫 번째 응답 content를 가져온다.

```
response["output"]["message"]["content"][0]["text"]
```

최종 생성 텍스트만 가져온다.

따라서 응답 텍스트만 출력하려면 다음과 같이 작성한다.

```
result_text=response["output"]["message"]["content"][0]["text"]
print(result_text)
```

---

## 8.8.7 토큰 사용량 확인하기

Bedrock 응답에는 토큰 사용량 정보가 포함될 수 있다.

토큰은 모델이 입력과 출력을 처리하는 기본 단위이다.

응답에서 다음 값을 확인할 수 있다.

```
usage=response.get("usage", {})
print(usage)
```

예시는 다음과 같다.

```
{
"inputTokens":42,
"outputTokens":60,
"totalTokens":102
}
```

각 항목의 의미는 다음과 같다.

| 항목 | 의미 |
| --- | --- |
| `inputTokens` | 모델에 전달한 입력 토큰 수 |
| `outputTokens` | 모델이 생성한 출력 토큰 수 |
| `totalTokens` | 입력과 출력 토큰의 합계 |

운영 환경에서는 토큰 수가 비용과 응답 속도에 영향을 줄 수 있다.

따라서 프롬프트에 불필요하게 긴 데이터를 넣지 않는 것이 좋다.

---

# 8.9 프롬프트 설계 기초

## 1. 프롬프트란 무엇인가

프롬프트는 모델에게 전달하는 입력 문장이다.

단순히 질문만 쓰는 것이 아니라, 모델이 어떤 방식으로 답해야 하는지 지시하는 역할을 한다.

예를 들어 다음 프롬프트는 너무 막연하다.

```
이 로그를 설명해줘.
```

이렇게 작성하면 모델이 어떤 관점에서, 얼마나 길게, 어떤 형식으로 답해야 하는지 알기 어렵다.

운영 자동화에서는 다음 요소를 포함하는 것이 좋다.

```
1. 역할
2. 입력 데이터
3. 출력 형식
4. 제한 조건
5. 추측 금지 조건
```

---

## 2. 좋지 않은 프롬프트 예시

```
아래 내용을 요약해줘.

500 에러 12건
401 에러 5건
/api/items 요청 많음
```

이 프롬프트는 동작할 수는 있다.

하지만 운영 보고용으로는 부족하다.

문제점은 다음과 같다.

```
1. 어떤 역할로 답해야 하는지 불명확하다.
2. 몇 문장으로 답할지 정해져 있지 않다.
3. 원인을 추측해도 되는지 제한이 없다.
4. 우선 확인 항목을 포함해야 하는지 알 수 없다.
```

---

## 3. 개선된 프롬프트 예시

```
너는 AWS 운영 지원 도우미다.
아래 로그 분석 결과를 운영자 관점에서 3문장 이내로 요약해라.

조건:
- 제공된 정보만 사용해라.
- 원인을 단정하지 마라.
- 마지막 문장에는 우선 확인할 항목을 포함해라.

[로그 분석 결과]
상태코드별 요청 개수
200: 152
401: 5
403: 3
500: 12

가장 많이 발생한 경로: /api/items
```

이 프롬프트는 훨씬 명확하다.

모델에게 다음 정보를 전달하고 있다.

| 구성 요소 | 내용 |
| --- | --- |
| 역할 | AWS 운영 지원 도우미 |
| 관점 | 운영자 관점 |
| 길이 | 3문장 이내 |
| 제한 | 제공된 정보만 사용 |
| 금지 | 원인 단정 금지 |
| 포함할 내용 | 우선 확인 항목 |

---

# 8.10 실습 3: 운영 데이터 요약 프롬프트 만들기

## 1. 실습 목표

이번 실습에서는 로그 분석 결과를 프롬프트에 넣어 Bedrock에 전달할 준비를 한다.

아직 Bedrock을 호출하지 않고, 먼저 프롬프트 문자열을 만드는 구조를 확인한다.

---

## 2. 실습 코드

파일명: `bedrock_prompt_basic.py`

```
def build_prompt(log_summary):
    return f"""
너는 AWS 운영 지원 도우미다.
아래 로그 분석 결과를 운영자 관점에서 3문장 이내로 요약해라.

조건:
- 제공된 정보만 사용해라.
- 원인을 단정하지 마라.
- 마지막 문장에는 우선 확인할 항목을 포함해라.

[로그 분석 결과]
{log_summary}
"""

log_summary = """
상태코드별 요청 개수
200: 152
401: 5
403: 3
500: 12

가장 많이 발생한 경로: /api/items
"""

prompt = build_prompt(log_summary)

print("===== 생성된 프롬프트 =====")
print(prompt)
```

---

## 3. 코드 설명

```
def build_prompt(log_summary):
```

로그 분석 결과를 입력받아 프롬프트 문자열을 생성하는 함수다.

```
return f"""
...
{log_summary}
"""
```

Python f-string을 사용한다.

`{log_summary}` 위치에 로그 분석 결과 문자열이 삽입된다.

```
log_summary = """
...
"""
```

앞 장에서 생성한 로그 분석 결과라고 가정한다.

실제 수업에서는 파일에서 읽어오거나, 로그 분석 코드의 결과를 변수로 전달할 수도 있다.

---

## 4. 실행

```
python bedrock_prompt_basic.py
```

출력 예시는 다음과 같다.

```
===== 생성된 프롬프트 =====

너는 AWS 운영 지원 도우미다.
아래 로그 분석 결과를 운영자 관점에서 3문장 이내로 요약해라.

조건:
- 제공된 정보만 사용해라.
- 원인을 단정하지 마라.
- 마지막 문장에는 우선 확인할 항목을 포함해라.

[로그 분석 결과]

상태코드별 요청 개수
200: 152
401: 5
403: 3
500: 12

가장 많이 발생한 경로: /api/items
```

---

# 8.11 실습 4: 로그 분석 결과를 Bedrock으로 요약하기

## 1. 실습 목표

이번 실습에서는 로그 분석 결과를 Bedrock에 전달하고, 운영자용 요약 문장을 생성한다.

이 실습이 8장의 핵심이다.

여기서 배우는 흐름은 다음 장의 RAG 챗봇에서도 그대로 사용된다.

```
입력 데이터 준비
        ↓
프롬프트 생성
        ↓
Bedrock 호출
        ↓
응답 텍스트 추출
        ↓
결과 출력
```

---

## 2. 실습 코드

파일명: `bedrock_log_summary.py`

```
import boto3
from botocore.exceptions import ClientError

PROFILE_NAME = "lab"
REGION_NAME = "ap-northeast-2"

# 수업에서 사용할 모델 ID로 변경한다.
MODEL_ID = "수업에서 사용할 모델 ID"

def get_bedrock_client():
    session = boto3.Session(profile_name=PROFILE_NAME)
    return session.client("bedrock-runtime", region_name=REGION_NAME)

def build_prompt(log_summary):
    return f"""
너는 AWS 운영 지원 도우미다.
아래 로그 분석 결과를 운영자 관점에서 3문장 이내로 요약해라.

조건:
- 제공된 정보만 사용해라.
- 원인을 단정하지 마라.
- 마지막 문장에는 우선 확인할 항목을 포함해라.

[로그 분석 결과]
{log_summary}
"""

def summarize_log(log_summary):
    bedrock = get_bedrock_client()

    response = bedrock.converse(
        modelId=MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": build_prompt(log_summary)
                    }
                ]
            }
        ],
        inferenceConfig={
            "maxTokens": 400,
            "temperature": 0.2
        }
    )

    result_text = response["output"]["message"]["content"][0]["text"]
    return result_text

log_summary = """
상태코드별 요청 개수
200: 152
401: 5
403: 3
500: 12

가장 많이 발생한 경로: /api/items
"""

try:
    result = summarize_log(log_summary)

    print("===== Bedrock 요약 결과 =====")
    print(result)

except ClientError as e:
    print("AWS ClientError 발생")
    print(e.response["Error"]["Code"])
    print(e.response["Error"]["Message"])

except Exception as e:
    print("알 수 없는 오류 발생")
    print(e)
```

---

## 3. 코드 흐름 설명

전체 흐름은 다음과 같다.

```
log_summary 변수에 로그 분석 결과 저장
        ↓
build_prompt() 함수로 프롬프트 생성
        ↓
summarize_log() 함수에서 Bedrock 호출
        ↓
응답 JSON에서 텍스트 추출
        ↓
화면에 출력
```

---

## 4. 주요 코드 설명

```
def summarize_log(log_summary):
```

로그 분석 결과를 입력받아 Bedrock으로 요약 결과를 생성하는 함수다.

```
bedrock = get_bedrock_client()
```

Bedrock Runtime client를 생성한다.

```
response = bedrock.converse(...)
```

Converse API를 호출한다.

```
"text": build_prompt(log_summary)
```

단순 질문 문장을 보내는 것이 아니라, 로그 분석 결과가 포함된 프롬프트 전체를 전달한다.

```
result_text = response["output"]["message"]["content"][0]["text"]
```

Bedrock 응답에서 실제 생성 텍스트만 추출한다.

---

## 5. 예상 결과

실행 명령은 다음과 같다.

```
python bedrock_log_summary.py
```

예상 출력 예시는 다음과 같다.

```
===== Bedrock 요약 결과 =====
전체 요청 중 200 응답이 대부분이지만 500 오류가 12건 발생해 서버 측 오류를 확인할 필요가 있다.
401과 403 응답도 일부 확인되므로 인증 또는 권한 관련 요청도 함께 점검하는 것이 좋다.
우선 /api/items 경로와 관련된 애플리케이션 로그 및 최근 배포 이력을 확인하는 것이 적절하다.
```

실제 응답은 모델과 실행 시점에 따라 달라질 수 있다.

---

# 8.12 실습 5: Bedrock 요약 결과를 파일로 저장하기

## 1. 실습 목표

운영 자동화에서 AI 응답은 화면에 출력하고 끝나지 않는다.

보통 다음과 같이 후속 작업에 사용한다.

* 보고서 초안 저장

* 장애 점검 결과 기록

* 이메일 본문으로 사용

* Slack 알림 메시지로 사용

* 챗봇 응답 로그로 저장

이번 실습에서는 Bedrock 응답 결과를 텍스트 파일로 저장한다.

---

## 2. 실습 코드

파일명: `bedrock_log_summary_save.py`

```
import boto3
from botocore.exceptions import ClientError

PROFILE_NAME = "lab"
REGION_NAME = "ap-northeast-2"

# 수업에서 사용할 모델 ID로 변경한다.
MODEL_ID = "수업에서 사용할 모델 ID"

def get_bedrock_client():
    session = boto3.Session(profile_name=PROFILE_NAME)
    return session.client("bedrock-runtime", region_name=REGION_NAME)

def build_prompt(log_summary):
    return f"""
너는 AWS 운영 지원 도우미다.
아래 로그 분석 결과를 운영자 관점에서 3문장 이내로 요약해라.

조건:
- 제공된 정보만 사용해라.
- 원인을 단정하지 마라.
- 마지막 문장에는 우선 확인할 항목을 포함해라.

[로그 분석 결과]
{log_summary}
"""

def summarize_log(log_summary):
    bedrock = get_bedrock_client()

    response = bedrock.converse(
        modelId=MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": build_prompt(log_summary)
                    }
                ]
            }
        ],
        inferenceConfig={
            "maxTokens": 400,
            "temperature": 0.2
        }
    )

    result_text = response["output"]["message"]["content"][0]["text"]
    return result_text

def save_text_result(text, filename):
    with open(filename, "w", encoding="utf-8") as file:
        file.write(text)

def main():
    log_summary = """
상태코드별 요청 개수
200: 152
401: 5
403: 3
500: 12

가장 많이 발생한 경로: /api/items
"""

    result = summarize_log(log_summary)

    print("===== Bedrock 요약 결과 =====")
    print(result)

    save_text_result(result, "bedrock_summary.txt")
    print("bedrock_summary.txt 저장 완료")

try:
    main()

except ClientError as e:
    print("AWS ClientError 발생")
    print(e.response["Error"]["Code"])
    print(e.response["Error"]["Message"])

except Exception as e:
    print("알 수 없는 오류 발생")
    print(e)
```

---

## 3. 코드 설명

```
def save_text_result(text,filename):
```

문자열과 파일명을 입력받아 텍스트 파일로 저장하는 함수다.

```
with open(filename, "w" ,encoding="utf-8") as file:
```

파일을 쓰기 모드로 연다.

`encoding="utf-8"`을 지정해야 한글이 깨지지 않는다.

```
file.write(text)
```

Bedrock에서 생성한 요약 문장을 파일에 기록한다.

```
save_text_result(result,"bedrock_summary.txt")
```

요약 결과를 `bedrock_summary.txt` 파일로 저장한다.

---

## 4. 실행

```
python bedrock_log_summary_save.py
```

실행 후 파일을 확인한다.

```
cat bedrock_summary.txt
```

Windows PowerShell에서는 다음 명령을 사용할 수 있다.

```
Get-Contentbedrock_summary.txt
```

---

# 8.13 일반 프롬프트 방식과 RAG 방식

## 1. 일반 프롬프트 방식

지금까지는 사용자가 직접 데이터를 프롬프트에 넣었다.

예를 들어 다음 정보를 직접 프롬프트에 포함했다.

```
상태코드별 요청 개수
200: 152
401: 5
403: 3
500: 12

가장 많이 발생한 경로: /api/items
```

이 방식은 간단한 데이터에는 적합하다.

하지만 문서가 많아지면 문제가 생긴다.

예를 들어 다음과 같은 문서가 있다고 가정한다.

```
운영 매뉴얼 20개
장애 대응 절차서 10개
보안 점검 가이드 5개
서비스 FAQ 30개
```

이 모든 문서를 프롬프트에 직접 넣을 수는 없다.

문서가 많을 때는 먼저 질문과 관련 있는 문서를 찾아야 한다.

---

## 2. RAG란 무엇인가

RAG는 Retrieval Augmented Generation의 약자다.

한국어로 표현하면 검색 증강 생성이라고 할 수 있다.

RAG의 핵심 흐름은 다음과 같다.

```
사용자 질문 입력
        ↓
관련 문서 검색
        ↓
검색된 문서를 프롬프트에 포함
        ↓
Bedrock 모델 호출
        ↓
문서 기반 답변 생성
```

즉, RAG는 모델이 혼자 기억에 의존해서 답하는 구조가 아니다.

먼저 관련 문서를 검색하고, 그 문서 내용을 근거로 답변을 생성한다.

---

## 3. 일반 프롬프트 방식과 RAG 방식 비교

| 구분 | 일반 프롬프트 방식 | RAG 방식 |
| --- | --- | --- |
| 입력 데이터 | 사용자가 직접 입력 | 사용자 질문 |
| 문서 검색 | 없음 | 질문과 관련된 문서 자동 검색 |
| 문서가 많을 때 | 직접 넣기 어려움 | 필요한 문서만 찾아 사용 |
| 답변 근거 | 불명확할 수 있음 | 검색된 문서 기반 |
| 사용 예 | 짧은 요약, 단순 질문 | 운영 매뉴얼 Q&A, 장애 대응 챗봇 |
| 적합한 챗봇 | 일반 대화형 챗봇 | 문서 기반 업무 챗봇 |

이 과정에서 구현할 챗봇은 RAG 방식에 가깝다.

---

# 8.14 Bedrock Knowledge Base와 RAG

## 1. Knowledge Base의 역할

Bedrock Knowledge Base는 RAG 구현을 쉽게 해주는 관리형 기능이다.

직접 벡터 데이터베이스를 구성하고, 임베딩을 생성하고, 검색 코드를 모두 작성하지 않아도 된다.

일반적인 구성 흐름은 다음과 같다.

```
운영 문서 준비
        ↓
S3에 문서 업로드
        ↓
Bedrock Knowledge Base 생성
        ↓
Data Source 동기화
        ↓
사용자 질문 입력
        ↓
관련 문서 검색
        ↓
Bedrock 모델로 답변 생성
```

---

## 2. Knowledge Base를 사용하는 이유

문서 기반 챗봇을 직접 만들려면 보통 다음 작업이 필요하다.

```
1. 문서를 작은 단위로 분할한다.
2. 각 문서를 임베딩 벡터로 변환한다.
3. 벡터 데이터베이스에 저장한다.
4. 사용자 질문도 임베딩으로 변환한다.
5. 질문과 유사한 문서를 검색한다.
6. 검색된 문서를 프롬프트에 넣는다.
7. 모델을 호출해 답변을 생성한다.
```

Bedrock Knowledge Bases를 사용하면 이 중 많은 부분을 관리형 기능으로 처리할 수 있다.

따라서 이 과정에서는 직접 벡터 데이터베이스를 구성하기보다, Bedrock Knowledge Base를 이용해 RAG 챗봇을 구현한다.

---

## 3. RetrieveAndGenerate 개념

Knowledge Base를 코드에서 사용할 때는 `retrieve_and_generate` 흐름을 사용할 수 있다.

개념적으로는 다음과 같다.

```
사용자 질문
        ↓
retrieve
        ↓
관련 문서 검색
        ↓
generate
        ↓
모델 답변 생성
```

즉, `retrieve_and_generate`는 이름 그대로 검색과 생성을 함께 수행하는 방식이다.

이 장에서는 `retrieve_and_generate`를 직접 구현하지 않는다.

다음 장에서 RAG 챗봇을 만들 때 사용한다.

---

# 8.15 invoke\_model

Bedrock에는 `invoke_model` API도 있다.

`invoke_model`은 모델을 호출하는 기본 방식 중 하나다.

하지만 이 장에서는 `invoke_model`을 깊게 다루지 않는다.

이유는 다음과 같다.

```
invoke_model은 모델별 요청 body 형식이 다를 수 있다.
```

예를 들어 어떤 모델은 `prompt` 필드를 사용하고, 어떤 모델은 `messages` 구조를 사용하며, 어떤 모델은 별도의 파라미터 형식을 요구할 수 있다.

---

# 8.16 정리

이 장에서는 Amazon Bedrock을 이용해 생성형 AI 모델을 호출하는 기본 흐름을 학습했다.

핵심 내용은 다음과 같다.

* Amazon Bedrock은 AWS에서 Foundation Model을 API로 호출할 수 있게 해주는 관리형 생성형 AI 서비스이다.

* Bedrock Runtime은 실제 모델 추론을 수행하는 API 계층이다.

* Python에서는 `boto3`의 `bedrock-runtime` client를 사용해 Bedrock 모델을 호출한다.

* 이 과정에서는 모델별 요청 형식 차이를 줄이기 위해 Converse API를 중심으로 실습한다.

* Converse API는 메시지 기반으로 모델을 호출하는 방식이다.

* 모델 호출에는 `modelId`가 필요하다.

* 실습 전에는 AWS CLI 프로필, 리전, 모델 접근 권한, IAM 권한을 확인해야 한다.

* 운영 데이터는 프롬프트에 포함해 자연어 요약 문장으로 변환할 수 있다.

* Bedrock 응답은 파일로 저장해 보고서, 알림, 챗봇 응답 등에 활용할 수 있다.

* RAG는 질문과 관련된 문서를 먼저 검색하고, 검색된 문서를 바탕으로 답변을 생성하는 방식이다.