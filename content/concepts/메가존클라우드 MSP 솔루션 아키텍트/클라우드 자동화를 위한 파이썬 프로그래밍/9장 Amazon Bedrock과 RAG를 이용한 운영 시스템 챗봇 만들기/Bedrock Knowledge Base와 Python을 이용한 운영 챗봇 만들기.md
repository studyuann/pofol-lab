---
title: "Bedrock Knowledge Base와 Python을 이용한 운영 챗봇 만들기"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "클라우드 자동화를 위한 파이썬 프로그래밍", "9장 Amazon Bedrock과 RAG를 이용한 운영 시스템 챗봇 만들기"]
is_public: true
draft: false
---

# Bedrock Knowledge Base와 Python을 이용한 운영 챗봇 만들기

---

## 개요

이미 생성된 Amazon Bedrock Knowledge Base를 Python에서 호출해 운영 챗봇을 만드는 방법을 학습한다.

운영 매뉴얼은 Amazon S3에 저장되어 있고, 해당 문서는 이미 Amazon Bedrock Knowledge Base에 동기화되어 있다고 가정한다.

따라서 이 교안에서는 다음 내용은 다루지 않는다.

```
S3 버킷 생성
운영 매뉴얼 업로드
Knowledge Base 생성
Knowledge Base 데이터 동기화
AWS 인증 설정
Python 가상환경 생성
```

이번 실습에서는 이미 생성된 **Knowledge Base ID**를 사용한다.

또한 AWS 리전은 서울 리전인 `ap-northeast-2`를 사용한다.

Python 코드는 Bedrock Knowledge Base에 질문을 보내고, Knowledge Base는 운영 매뉴얼에서 관련 문서를 검색한다. 이후 Bedrock 모델이 검색된 문서를 기반으로 답변을 생성한다.

실습 흐름은 다음과 같다.

```
필요 패키지 설치
↓
Knowledge Base ID와 모델 ARN 확인
↓
CLI 운영 챗봇 작성
↓
Knowledge Base에 질문 전송
↓
답변 출력
↓
출처 문서 출력
↓
Streamlit 웹 챗봇 작성
```

---

## 실습 전제 조건

이 교안은 다음 조건이 준비되어 있다고 가정한다.

| 항목 | 설명 |
| --- | --- |
| S3 운영 매뉴얼 | 운영 매뉴얼 문서가 S3에 업로드되어 있음 |
| Bedrock Knowledge Base | 운영 매뉴얼 기반 Knowledge Base가 이미 생성되어 있음 |
| Knowledge Base ID | 생성된 Knowledge Base ID를 알고 있음 |
| AWS 리전 | 서울 리전 `ap-northeast-2` 사용 |
| Bedrock 모델 | 서울 리전에서 사용 가능한 모델 사용 |
| Python 실행 환경 | Python 실행 가능 상태 |
| AWS 호출 권한 | Bedrock Knowledge Base 호출 권한이 이미 준비되어 있음 |

---

## 학습 목표

이 교안을 학습하면 다음을 수행할 수 있다.

* 기존 Knowledge Base ID를 이용해 Bedrock Knowledge Base에 질의할 수 있다.

* 서울 리전 `ap-northeast-2` 기준으로 Bedrock Agent Runtime 클라이언트를 생성할 수 있다.

* `retrieve_and_generate()` API의 기본 구조를 이해할 수 있다.

* CLI 기반 운영 챗봇을 구현할 수 있다.

* 답변과 함께 참조 문서 출처를 출력할 수 있다.

* Streamlit을 이용해 웹 기반 운영 챗봇을 만들 수 있다.

* 리전 오류, Knowledge Base ID 오류, 모델 ARN 오류, 권한 오류를 구분할 수 있다.

---

## 주요 키워드

| 키워드 | 설명 |
| --- | --- |
| Amazon Bedrock | AWS의 생성형 AI 서비스 |
| Knowledge Bases for Amazon Bedrock | 외부 문서를 검색해 모델 답변에 활용하는 RAG 기능 |
| Knowledge Base ID | 생성된 지식기반을 식별하는 고유 ID |
| RAG | Retrieval Augmented Generation. 문서 검색 후 답변 생성 |
| boto3 | Python에서 AWS 서비스를 호출하는 SDK |
| bedrock-agent-runtime | Knowledge Base 질의 실행에 사용하는 boto3 클라이언트 |
| retrieve\_and\_generate | Knowledge Base 검색과 답변 생성을 함께 수행하는 API |
| Citation | 답변 생성에 참고된 문서 출처 정보 |
| Model ARN | 답변 생성에 사용할 Bedrock 모델 ARN |
| ap-northeast-2 | AWS 서울 리전 코드 |
| Streamlit | Python으로 웹 UI를 구현하는 라이브러리 |

---

## 운영 매뉴얼 기반 챗봇이 필요한 이유

운영자는 장애나 문의가 발생했을 때 매뉴얼을 빠르게 찾아야 한다.

예를 들어 다음과 같은 상황이 있다.

```
웹 서버가 응답하지 않음
DB 연결 오류가 발생함
배포 후 500 오류가 증가함
디스크 사용률이 90%를 초과함
SSL 인증서 만료 알람이 발생함
백업 실패 알람이 발생함
```

이때 운영자는 보통 다음 문서를 찾는다.

```
웹 서버 장애 대응 매뉴얼
DB 연결 오류 점검 절차서
배포 실패 시 롤백 가이드
디스크 사용률 증가 대응 절차
SSL 인증서 갱신 절차
백업 실패 조치 가이드
장애 보고서 작성 양식
```

문서가 많아지면 원하는 내용을 찾는 데 시간이 오래 걸린다.

운영 매뉴얼 기반 챗봇은 이 문제를 줄여준다.

운영자가 자연어로 질문하면 챗봇이 Knowledge Base에서 관련 매뉴얼을 검색하고, 검색된 내용을 바탕으로 답변한다.

---

## 일반 챗봇과 운영 매뉴얼 기반 챗봇의 차이

| 구분 | 일반 챗봇 | 운영 매뉴얼 기반 챗봇 |
| --- | --- | --- |
| 답변 근거 | 모델의 일반 지식 | S3 기반 운영 매뉴얼 |
| 내부 절차 반영 | 어려움 | 가능 |
| 출처 확인 | 어려움 | 가능 |
| 최신 문서 반영 | 제한적 | Knowledge Base 동기화 후 반영 가능 |
| 운영 절차 안내 | 일반적 답변 가능성 높음 | 사내 매뉴얼 기준 답변 가능 |
| 장애 대응 적합성 | 제한적 | 높음 |

운영 환경에서는 답변의 창의성보다 정확성과 근거가 중요하다.

따라서 운영 챗봇은 다음 원칙을 가져야 한다.

```
운영 매뉴얼 기반으로 답변한다.
매뉴얼에 없는 내용은 추측하지 않는다.
답변에 사용한 출처 문서를 함께 보여준다.
위험한 명령어는 주의사항과 함께 안내한다.
운영자가 최종 판단하도록 구성한다.
```

---

## RAG 동작 구조

RAG는 Retrieval Augmented Generation의 약자이다.

뜻을 나누면 다음과 같다.

| 용어 | 의미 |
| --- | --- |
| Retrieval | 질문과 관련 있는 문서를 검색하는 과정 |
| Augmented | 검색된 문서를 모델 입력에 추가하는 과정 |
| Generation | 검색 문서를 참고해 최종 답변을 생성하는 과정 |

운영 챗봇의 동작 흐름은 다음과 같다.

```
사용자가 질문 입력
↓
Python 프로그램이 Bedrock Knowledge Base에 질문 전달
↓
Knowledge Base가 관련 운영 매뉴얼 검색
↓
검색된 문서 조각을 모델 입력에 추가
↓
Bedrock 모델이 검색 내용을 기반으로 답변 생성
↓
Python 프로그램이 답변과 출처 출력
```

Python 프로그램은 S3 문서를 직접 읽지 않는다.

Python 프로그램은 Knowledge Base ID를 이용해 Bedrock에 질문을 보낸다.

문서 검색, 벡터 검색, 답변 생성은 Bedrock이 처리한다.

---

## 실습 아키텍처

```
[운영자]
   |
   | 질문 입력
   v
[Python CLI 또는 Streamlit 앱]
   |
   | boto3
   v
[Bedrock Agent Runtime]
   |
   | retrieve_and_generate
   v
[Bedrock Knowledge Base]
   |
   | 관련 운영 매뉴얼 검색
   v
[검색된 문서 조각]
   |
   | 모델에 컨텍스트로 전달
   v
[서울 리전 Bedrock 모델]
   |
   | 답변 생성
   v
[Python 앱]
   |
   | 답변 및 출처 출력
   v
[운영자]
```

---

## 서울 리전 사용 기준

이번 실습에서는 AWS 리전을 서울 리전으로 고정한다.

```
AWS Region: ap-northeast-2
Region Name: Asia Pacific (Seoul)
```

Python 코드에서는 다음 값을 사용한다.

```
AWS_REGION = "ap-northeast-2"
```

서울 리전을 사용하는 이유는 다음과 같다.

| 항목 | 설명 |
| --- | --- |
| 리전 일관성 | Knowledge Base와 모델 호출 리전을 동일하게 맞출 수 있음 |
| 지연 시간 | 한국 사용자가 접근할 때 네트워크 지연을 줄일 수 있음 |
| 운영 정책 | 운영 문서와 AI 호출 리전을 서울로 통일하기 쉬움 |
| 장애 분석 | CloudTrail, CloudWatch 로그를 리전 기준으로 추적하기 쉬움 |

---

## 사용할 모델 ARN

이번 교안에서는 예시 모델로 **Anthropic Claude 3 Haiku** 형식의 ARN을 사용한다.

서울 리전 기준 모델 ARN 예시는 다음과 같다.

```
arn:aws:bedrock:ap-northeast-2::foundation-model/anthropic.claude-3-haiku-20240307-v1:0
```

Python 코드에서는 다음처럼 사용한다.

```
MODEL_ARN = "arn:aws:bedrock:ap-northeast-2::foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
```

실습 환경에서 해당 모델을 사용할 수 없으면 서울 리전에서 사용 가능한 다른 모델의 ARN으로 변경한다.

---

## 준비해야 할 값

실습 전에 다음 값을 준비한다.

```
AWS_REGION
KNOWLEDGE_BASE_ID
MODEL_ARN
```

예시 값은 다음과 같다.

```
AWS_REGION=ap-northeast-2
KNOWLEDGE_BASE_ID=ABCDEFGHIJ
MODEL_ARN=arn:aws:bedrock:ap-northeast-2::foundation-model/anthropic.claude-3-haiku-20240307-v1:0
```

`KNOWLEDGE_BASE_ID`는 본인의 실제 Knowledge Base ID로 변경해야 한다.

---

## 프로젝트 파일 구성

파일 수를 최소화하기 위해 다음 3개 파일만 사용한다.

```
kb-ops-chatbot/
├── requirements.txt
├── chatbot_cli.py
└── app.py
```

각 파일의 역할은 다음과 같다.

| 파일 | 역할 |
| --- | --- |
| `requirements.txt` | 필요한 Python 패키지 목록 |
| `chatbot_cli.py` | CLI 챗봇, Knowledge Base 호출, 출처 출력, 오류 처리를 모두 포함 |
| `app.py` | Streamlit 웹 챗봇 |

---

## 필요한 Python 패키지 설치

`requirements.txt` 파일을 만든다.

파일명: `requirements.txt`

```
boto3
streamlit
```

패키지를 설치한다.

```
pip install -r requirements.txt
```

명령어 설명은 다음과 같다.

| 명령어 | 설명 |
| --- | --- |
| `pip` | Python 패키지 설치 도구 |
| `install` | 패키지를 설치하겠다는 의미 |
| `-r requirements.txt` | 파일에 적힌 패키지 목록을 읽어 설치 |

설치 여부를 확인한다.

```
pip list
```

---

# CLI 운영 챗봇 만들기

## 코드 작성

파일명: `chatbot_cli.py`

```
import boto3
from botocore.exceptions import ClientError


# 서울 리전 사용
AWS_REGION = "ap-northeast-2"

# 본인의 Knowledge Base ID로 변경
KNOWLEDGE_BASE_ID = "본인의_KNOWLEDGE_BASE_ID"

# 서울 리전에서 사용 가능한 Bedrock 모델 ARN으로 변경 가능
MODEL_ARN = (
    "arn:aws:bedrock:ap-northeast-2::"
    "foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
)

# Knowledge Base에서 검색할 문서 조각 수
NUMBER_OF_RESULTS = 5


def create_client():
    """
    Bedrock Agent Runtime 클라이언트를 생성한다.

    Knowledge Base에 질문을 보내려면 일반 bedrock-runtime이 아니라
    bedrock-agent-runtime 클라이언트를 사용한다.
    """

    return boto3.client(
        service_name="bedrock-agent-runtime",
        region_name=AWS_REGION
    )


def build_ops_question(user_question):
    """
    운영 챗봇 답변 형식을 일정하게 만들기 위해 사용자 질문 앞에 지시문을 추가한다.
    """

    return f"""
너는 운영 매뉴얼 기반 운영 지원 챗봇이다.

답변 규칙:
1. 반드시 운영 매뉴얼에서 검색된 내용을 기반으로 답변한다.
2. 매뉴얼에 없는 내용은 추측하지 말고 "매뉴얼에서 확인되지 않음"이라고 답한다.
3. 장애 대응 질문이면 다음 형식으로 답한다.
   - 현상 요약
   - 1차 점검 항목
   - 조치 절차
   - 확인 명령어
   - 에스컬레이션 기준
4. 명령어가 필요한 경우 코드 블록으로 작성한다.
5. 위험한 작업은 실행 전 백업, 승인, 서비스 영향 여부를 함께 안내한다.

사용자 질문:
{user_question}
""".strip()


def retrieve_and_generate(question):
    """
    Knowledge Base에 질문을 보내고 응답 전체를 반환한다.
    """

    client = create_client()

    ops_question = build_ops_question(question)

    response = client.retrieve_and_generate(
        input={
            "text": ops_question
        },
        retrieveAndGenerateConfiguration={
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": KNOWLEDGE_BASE_ID,
                "modelArn": MODEL_ARN,
                "retrievalConfiguration": {
                    "vectorSearchConfiguration": {
                        "numberOfResults": NUMBER_OF_RESULTS
                    }
                }
            }
        }
    )

    return response


def extract_answer(response):
    """
    retrieve_and_generate 응답에서 최종 답변 텍스트만 추출한다.
    """

    return response.get("output", {}).get("text", "")


def extract_sources(response):
    """
    retrieve_and_generate 응답에서 출처 문서 정보를 추출한다.
    """

    sources = []

    citations = response.get("citations", [])

    for citation in citations:
        references = citation.get("retrievedReferences", [])

        for ref in references:
            content = ref.get("content", {})
            location = ref.get("location", {})

            source_text = content.get("text", "")

            sources.append({
                "text": source_text[:300],
                "location": location
            })

    return sources


def ask_knowledge_base(question):
    """
    사용자 질문을 Knowledge Base에 전달하고 답변과 출처를 반환한다.
    """

    try:
        response = retrieve_and_generate(question)

        answer = extract_answer(response)
        sources = extract_sources(response)

        if not answer:
            answer = "답변을 생성하지 못했음. 질문을 더 구체적으로 입력하거나 Knowledge Base 문서를 확인해야 함."

        return {
            "answer": answer,
            "sources": sources,
            "error": None
        }

    except ClientError as e:
        error_code = e.response["Error"].get("Code")
        error_message = e.response["Error"].get("Message")

        return {
            "answer": "",
            "sources": [],
            "error": (
                "AWS API 호출 중 오류가 발생했음\n"
                f"오류 코드: {error_code}\n"
                f"오류 메시지: {error_message}"
            )
        }

    except Exception as e:
        return {
            "answer": "",
            "sources": [],
            "error": f"예상하지 못한 오류가 발생했음: {e}"
        }


def print_sources(sources):
    """
    출처 문서를 화면에 출력한다.
    """

    if not sources:
        print("\n출처 문서 없음")
        return

    print("\n출처 문서")

    for index, source in enumerate(sources, start=1):
        print(f"\n[{index}]")

        location = source.get("location", {})
        print(f"location: {location}")

        text = source.get("text", "")
        if text:
            print("참조 내용 일부:")
            print(text)


def main():
    """
    CLI 챗봇의 메인 실행 함수이다.
    """

    print("운영 매뉴얼 챗봇")
    print("서울 리전 Amazon Bedrock Knowledge Base 기반으로 답변함")
    print("종료하려면 exit 또는 quit 입력")
    print("-" * 60)

    while True:
        question = input("\n질문> ").strip()

        if question.lower() in ["exit", "quit"]:
            print("챗봇을 종료함")
            break

        if not question:
            print("질문을 입력해야 함")
            continue

        result = ask_knowledge_base(question)

        if result["error"]:
            print("\n오류")
            print(result["error"])
            continue

        print("\n답변")
        print(result["answer"])

        print_sources(result["sources"])


if __name__ == "__main__":
    main()
```

---

## 코드 핵심 설명

### 1. 설정값

```
AWS_REGION = "ap-northeast-2"
```

서울 리전을 사용한다.

```
KNOWLEDGE_BASE_ID = "본인의_KNOWLEDGE_BASE_ID"
```

이미 생성된 Knowledge Base ID를 입력한다.

```
MODEL_ARN = (
    "arn:aws:bedrock:ap-northeast-2::"
    "foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
)
```

답변 생성에 사용할 모델 ARN이다.

모델 ARN의 리전도 `ap-northeast-2`로 맞춘다.

```
NUMBER_OF_RESULTS = 5
```

Knowledge Base에서 검색할 문서 조각 수이다.

값이 너무 작으면 필요한 문서를 못 찾을 수 있다.

값이 너무 크면 응답 시간이 길어지고 비용이 증가할 수 있다.

---

### 2. Bedrock 클라이언트 생성

```
def create_client():
    return boto3.client(
        service_name="bedrock-agent-runtime",
        region_name=AWS_REGION
    )
```

Knowledge Base에 질의할 때는 `bedrock-agent-runtime` 클라이언트를 사용한다.

`bedrock-runtime`은 일반 모델 호출에 사용하고, `bedrock-agent-runtime`은 Knowledge Base나 Agent 실행 계열 API를 호출할 때 사용한다.

---

### 3. 운영 챗봇용 질문 만들기

```
def build_ops_question(user_question):
```

사용자의 질문 앞에 운영 챗봇용 지시문을 붙인다.

이 함수는 답변 형식을 일정하게 만들기 위해 사용한다.

예를 들어 사용자가 다음처럼 질문했다고 하자.

```
DB 연결 오류가 나면 어떻게 해?
```

이 질문을 그대로 보내는 대신 다음 규칙을 함께 보낸다.

```
운영 매뉴얼 기반으로 답변한다.
매뉴얼에 없으면 추측하지 않는다.
장애 대응 질문이면 점검 항목, 조치 절차, 명령어, 에스컬레이션 기준으로 답한다.
```

이렇게 하면 답변이 운영 절차서에 가까운 형태로 생성된다.

---

### 4. Knowledge Base 질의

```
response = client.retrieve_and_generate(
    input={
        "text": ops_question
    },
    retrieveAndGenerateConfiguration={
        "type": "KNOWLEDGE_BASE",
        "knowledgeBaseConfiguration": {
            "knowledgeBaseId": KNOWLEDGE_BASE_ID,
            "modelArn": MODEL_ARN,
            "retrievalConfiguration": {
                "vectorSearchConfiguration": {
                    "numberOfResults": NUMBER_OF_RESULTS
                }
            }
        }
    }
)
```

이 코드가 핵심이다.

각 항목의 의미는 다음과 같다.

| 항목 | 설명 |
| --- | --- |
| `input.text` | 사용자 질문 |
| `type` | Knowledge Base 기반 질의임을 지정 |
| `knowledgeBaseId` | 사용할 Knowledge Base ID |
| `modelArn` | 답변 생성 모델 |
| `numberOfResults` | 검색할 문서 조각 수 |

---

### 5. 답변 추출

```
return response.get("output", {}).get("text", "")
```

응답에서 최종 답변을 추출한다.

`get()`을 사용하는 이유는 응답 구조가 예상과 다를 때 오류를 줄이기 위해서이다.

---

### 6. 출처 문서 추출

```
citations = response.get("citations", [])
```

`citations`는 답변에 사용된 출처 정보를 담고 있다.

```
references = citation.get("retrievedReferences", [])
```

검색된 참조 문서 목록을 가져온다.

```
content = ref.get("content", {})
location = ref.get("location", {})
```

참조 문서의 내용과 위치 정보를 가져온다.

```
source_text = content.get("text", "")
```

참조 문서 일부 텍스트를 가져온다.

```
"text": source_text[:300]
```

출처 문서 내용이 너무 길 수 있으므로 앞 300자만 출력한다.

---

### 7. 오류 처리

```
except ClientError as e:
```

AWS API 호출 중 발생한 오류를 처리한다.

대표적인 오류는 다음과 같다.

```
AccessDeniedException
ValidationException
ResourceNotFoundException
ThrottlingException
```

오류가 발생하면 코드와 메시지를 출력한다.

```
error_code = e.response["Error"].get("Code")
error_message = e.response["Error"].get("Message")
```

이렇게 하면 단순히 실패했다고 끝나는 것이 아니라, 권한 문제인지, 모델 ARN 문제인지, Knowledge Base ID 문제인지 확인할 수 있다.

---

## CLI 챗봇 실행

다음 명령어로 실행한다.

```
python chatbot_cli.py
```

실행 예시는 다음과 같다.

```
운영 매뉴얼 챗봇
서울 리전 Amazon Bedrock Knowledge Base 기반으로 답변함
종료하려면 exit 또는 quit 입력
------------------------------------------------------------

질문> 웹 서버가 응답하지 않을 때 1차 점검 절차를 알려줘.

답변
웹 서버가 응답하지 않을 때는 먼저 인스턴스 상태, 웹 서버 프로세스 상태, 포트 리스닝 상태, 최근 에러 로그를 확인한다...

출처 문서

[1]
location: {'type': 'S3', 's3Location': {'uri': 's3://ops-manual-bucket/web/web-server-troubleshooting.pdf'}}
참조 내용 일부:
웹 서버 장애 발생 시 1차 점검 항목은 인스턴스 상태, 프로세스 상태, 포트 리스닝 상태, 최근 에러 로그 확인이다...
```

---

## 실습 질문 예시

다음 질문을 사용해 테스트할 수 있다.

```
웹 서버가 응답하지 않을 때 1차 점검 절차를 알려줘.
Nginx가 502 Bad Gateway를 반환하면 무엇을 확인해야 해?
DB 연결 오류가 발생했을 때 확인해야 할 항목은?
디스크 사용률이 90%를 넘으면 어떻게 조치해야 해?
배포 실패 시 롤백 절차를 알려줘.
SSL 인증서 만료 알람이 발생하면 어떻게 대응해야 해?
백업 실패 알람이 발생했을 때 확인 순서를 알려줘.
로그인 API에서 500 오류가 반복되면 어떤 로그를 봐야 해?
장애 보고서에는 어떤 내용을 포함해야 해?
```

질문은 구체적으로 작성하는 것이 좋다.

좋은 질문 예시는 다음과 같다.

```
Nginx 502 오류 대응 절차를 알려줘.
```

좋지 않은 질문 예시는 다음과 같다.

```
안 돼. 어떻게 해?
```

이런 질문은 어떤 서비스가 안 되는지, 어떤 오류인지 알 수 없어 검색 정확도가 낮아질 수 있다.

---

# Streamlit 웹 챗봇 만들기

## 코드 작성

파일명: `app.py`

```
import boto3
import streamlit as st
from botocore.exceptions import ClientError


# 서울 리전 사용
AWS_REGION = "ap-northeast-2"

# 본인의 Knowledge Base ID로 변경
KNOWLEDGE_BASE_ID = "본인의_KNOWLEDGE_BASE_ID"

# 서울 리전에서 사용 가능한 Bedrock 모델 ARN으로 변경 가능
MODEL_ARN = (
    "arn:aws:bedrock:ap-northeast-2::"
    "foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
)

# Knowledge Base에서 검색할 문서 조각 수
NUMBER_OF_RESULTS = 5


def create_client():
    return boto3.client(
        service_name="bedrock-agent-runtime",
        region_name=AWS_REGION
    )


def build_ops_question(user_question):
    return f"""
너는 운영 매뉴얼 기반 운영 지원 챗봇이다.

답변 규칙:
1. 반드시 운영 매뉴얼에서 검색된 내용을 기반으로 답변한다.
2. 매뉴얼에 없는 내용은 추측하지 말고 "매뉴얼에서 확인되지 않음"이라고 답한다.
3. 장애 대응 질문이면 다음 형식으로 답한다.
   - 현상 요약
   - 1차 점검 항목
   - 조치 절차
   - 확인 명령어
   - 에스컬레이션 기준
4. 명령어가 필요한 경우 코드 블록으로 작성한다.
5. 위험한 작업은 실행 전 백업, 승인, 서비스 영향 여부를 함께 안내한다.

사용자 질문:
{user_question}
""".strip()


def retrieve_and_generate(question):
    client = create_client()

    ops_question = build_ops_question(question)

    response = client.retrieve_and_generate(
        input={
            "text": ops_question
        },
        retrieveAndGenerateConfiguration={
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": KNOWLEDGE_BASE_ID,
                "modelArn": MODEL_ARN,
                "retrievalConfiguration": {
                    "vectorSearchConfiguration": {
                        "numberOfResults": NUMBER_OF_RESULTS
                    }
                }
            }
        }
    )

    return response


def extract_answer(response):
    return response.get("output", {}).get("text", "")


def extract_sources(response):
    sources = []

    citations = response.get("citations", [])

    for citation in citations:
        references = citation.get("retrievedReferences", [])

        for ref in references:
            content = ref.get("content", {})
            location = ref.get("location", {})

            source_text = content.get("text", "")

            sources.append({
                "text": source_text[:300],
                "location": location
            })

    return sources


def ask_knowledge_base(question):
    try:
        response = retrieve_and_generate(question)

        answer = extract_answer(response)
        sources = extract_sources(response)

        if not answer:
            answer = "답변을 생성하지 못했음. 질문을 더 구체적으로 입력하거나 Knowledge Base 문서를 확인해야 함."

        return {
            "answer": answer,
            "sources": sources,
            "error": None
        }

    except ClientError as e:
        error_code = e.response["Error"].get("Code")
        error_message = e.response["Error"].get("Message")

        return {
            "answer": "",
            "sources": [],
            "error": (
                "AWS API 호출 중 오류가 발생했음\n\n"
                f"- 오류 코드: `{error_code}`\n"
                f"- 오류 메시지: `{error_message}`"
            )
        }

    except Exception as e:
        return {
            "answer": "",
            "sources": [],
            "error": f"예상하지 못한 오류가 발생했음: {e}"
        }


st.set_page_config(
    page_title="운영 매뉴얼 챗봇",
    page_icon="🛠️",
    layout="wide"
)

st.title("운영 매뉴얼 챗봇")
st.caption("서울 리전 Amazon Bedrock Knowledge Base 기반 운영 지원 챗봇")

st.sidebar.header("설정 정보")
st.sidebar.write(f"AWS Region: `{AWS_REGION}`")
st.sidebar.write(f"Knowledge Base ID: `{KNOWLEDGE_BASE_ID}`")
st.sidebar.write(f"검색 문서 수: `{NUMBER_OF_RESULTS}`")

if "messages" not in st.session_state:
    st.session_state.messages = []


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


question = st.chat_input(
    "운영 매뉴얼에 대해 질문하세요. 예: DB 연결 오류 발생 시 점검 절차는?"
)

if question:
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("운영 매뉴얼에서 관련 내용을 검색하는 중..."):
            result = ask_knowledge_base(question)

        if result["error"]:
            st.error(result["error"])
            answer = result["error"]
        else:
            answer = result["answer"]
            sources = result["sources"]

            st.markdown(answer)

            if sources:
                with st.expander("참조 문서 보기"):
                    for index, source in enumerate(sources, start=1):
                        st.markdown(f"### 출처 {index}")
                        st.json(source.get("location", {}))

                        text = source.get("text", "")
                        if text:
                            st.markdown("참조 내용 일부")
                            st.write(text)
            else:
                st.info("출처 문서 없음")

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })
```

---

## Streamlit 코드 설명

### 1. 페이지 설정

```
st.set_page_config(
    page_title="운영 매뉴얼 챗봇",
    page_icon="🛠️",
    layout="wide"
)
```

웹 페이지 기본 정보를 설정한다.

| 항목 | 설명 |
| --- | --- |
| `page_title` | 브라우저 탭에 표시될 제목 |
| `page_icon` | 브라우저 탭 아이콘 |
| `layout` | 화면 레이아웃 |

---

### 2. 사이드바 설정 정보 출력

```
st.sidebar.header("설정 정보")
st.sidebar.write(f"AWS Region: `{AWS_REGION}`")
st.sidebar.write(f"Knowledge Base ID: `{KNOWLEDGE_BASE_ID}`")
st.sidebar.write(f"검색 문서 수: `{NUMBER_OF_RESULTS}`")
```

왼쪽 사이드바에 현재 설정 정보를 출력한다.

교육 실습에서는 현재 어떤 리전과 Knowledge Base를 사용 중인지 눈으로 확인할 수 있어 유용하다.

운영 환경에서는 Knowledge Base ID 같은 내부 식별자를 숨기는 것이 더 안전할 수 있다.

---

### 3. 대화 이력 저장

```
if "messages" not in st.session_state:
    st.session_state.messages = []
```

`st.session_state`는 Streamlit 앱에서 상태를 유지할 때 사용한다.

여기서는 사용자 질문과 챗봇 답변을 저장한다.

---

### 4. 채팅 입력창

```
question = st.chat_input(
    "운영 매뉴얼에 대해 질문하세요. 예: DB 연결 오류 발생 시 점검 절차는?"
)
```

사용자가 질문을 입력할 수 있는 채팅 입력창을 만든다.

---

### 5. 사용자 메시지 출력

```
with st.chat_message("user"):
    st.markdown(question)
```

사용자의 질문을 채팅 UI 형태로 출력한다.

---

### 6. 챗봇 답변 출력

```
with st.chat_message("assistant"):
```

챗봇 답변 영역을 만든다.

```
with st.spinner("운영 매뉴얼에서 관련 내용을 검색하는 중..."):
```

Knowledge Base 호출 중 로딩 메시지를 보여준다.

```
result = ask_knowledge_base(question)
```

사용자 질문을 Knowledge Base에 전달한다.

---

### 7. 출처 문서 출력

```
with st.expander("참조 문서 보기"):
```

출처 문서를 접었다 펼 수 있는 영역으로 출력한다.

```
st.json(source.get("location", {}))
```

출처 위치 정보를 JSON 형태로 보여준다.

S3 기반 Knowledge Base라면 S3 URI가 표시될 수 있다.

---

## Streamlit 웹 챗봇 실행

다음 명령어로 실행한다.

```
streamlit run app.py
```

브라우저가 열리면 질문을 입력한다.

예시 질문은 다음과 같다.

```
웹 서버가 응답하지 않을 때 1차 점검 절차를 알려줘.
```

---

# 실행 테스트 순서

실습은 다음 순서로 진행한다.

```
1. requirements.txt 패키지 설치
2. chatbot_cli.py의 Knowledge Base ID 수정
3. chatbot_cli.py의 모델 ARN 확인
4. CLI 챗봇 실행
5. 질문 입력 후 답변 확인
6. 출처 문서 확인
7. app.py의 Knowledge Base ID 수정
8. app.py의 모델 ARN 확인
9. Streamlit 웹 챗봇 실행
10. 웹 화면에서 질문 테스트
```

실행 명령어는 다음과 같다.

```
pip install -r requirements.txt
```

```
python chatbot_cli.py
```

```
streamlit run app.py
```

---

# 자주 발생하는 오류와 해결 방법

## 1. 권한 부족 오류

오류 예시는 다음과 같다.

```
AccessDeniedException
```

의미는 현재 실행 환경에 Bedrock 호출 권한이 없다는 것이다.

확인할 권한은 다음과 같다.

```
bedrock:Retrieve
bedrock:RetrieveAndGenerate
```

---

## 2. 리전 불일치 오류

오류 상황은 다음과 같다.

```
Knowledge Base는 서울 리전에 있는데 Python 코드는 다른 리전을 호출함
모델 ARN은 다른 리전인데 클라이언트는 ap-northeast-2를 사용함
```

확인할 값은 다음과 같다.

```
AWS_REGION = "ap-northeast-2"
MODEL_ARN = "arn:aws:bedrock:ap-northeast-2::foundation-model/..."
```

---

## 3. Knowledge Base ID 오류

오류 상황은 다음과 같다.

```
Knowledge Base ID가 잘못됨
다른 리전에 있는 Knowledge Base ID를 사용함
접근 권한이 없는 Knowledge Base ID를 사용함
```

확인할 값은 다음과 같다.

```
KNOWLEDGE_BASE_ID = "본인의_KNOWLEDGE_BASE_ID"
```

서울 리전에 있는 Knowledge Base ID인지 확인한다.

---

## 4. 모델 접근 권한 오류

오류 예시는 다음과 같다.

```
The provided model identifier is invalid
Access to the model is not allowed
```

원인은 다음과 같을 수 있다.

```
서울 리전에서 해당 모델을 사용할 수 없음
Bedrock 모델 액세스가 활성화되지 않음
MODEL_ARN 오타
모델 ID가 잘못 입력됨
```

이 경우 서울 리전에서 사용 가능한 모델 ARN으로 변경해야 한다.

---

## 5. 답변이 부정확한 경우

원인은 다음과 같을 수 있다.

```
질문이 너무 모호함
운영 매뉴얼에 해당 내용이 없음
Knowledge Base 동기화가 최신 상태가 아님
문서 제목이나 문서 구조가 검색하기 어렵게 작성됨
검색 문서 수가 너무 적음
```

해결 방법은 다음과 같다.

```
질문을 더 구체적으로 작성한다.
운영 매뉴얼에 해당 절차가 있는지 확인한다.
Knowledge Base 데이터 동기화 상태를 확인한다.
numberOfResults 값을 5에서 8 또는 10으로 늘려본다.
매뉴얼 문서 제목과 본문 구조를 정리한다.
```

---

# 운영 챗봇 품질 개선 방법

운영 챗봇의 품질은 모델보다 매뉴얼 품질에 크게 영향을 받는다.

좋은 매뉴얼은 다음 특징을 가진다.

```
장애 유형별 제목이 명확함
증상, 원인, 점검, 조치가 분리되어 있음
명령어가 코드 블록으로 정리되어 있음
주의사항과 롤백 기준이 포함되어 있음
에스컬레이션 기준이 명확함
최신 수정일과 담당 팀이 표시되어 있음
```

운영 매뉴얼 예시는 다음 구조가 좋다.

```
# Nginx 502 Bad Gateway 대응 절차

## 증상
- 사용자가 웹 페이지 접속 시 502 Bad Gateway 오류를 확인함
- ALB Target Group 상태가 unhealthy로 표시될 수 있음

## 1차 점검
```bash
systemctl status nginx
systemctl status app
ss -lntp
curl -I http://localhost
```

## 주요 원인
- 애플리케이션 프로세스 중지
- Nginx upstream 설정 오류
- 포트 불일치
- 방화벽 또는 보안 그룹 문제

## 조치 절차
1. 애플리케이션 프로세스 상태를 확인한다.
2. 애플리케이션 로그에서 최근 오류를 확인한다.
3. Nginx 설정 파일 문법을 검사한다.
4. 필요 시 승인 후 서비스를 재시작한다.

## 재시작 명령
```bash
sudo systemctl restart nginx
sudo systemctl restart app
```

## 에스컬레이션 기준
- 10분 이상 복구되지 않음
- 동일 오류가 3회 이상 반복됨
- DB 연결 오류가 함께 발생함
```

이런 구조의 문서는 Knowledge Base가 검색하기 좋다.

---

# 운영 적용 시 보안 주의사항

운영 챗봇은 내부 운영 매뉴얼을 다룬다.

따라서 보안 주의사항이 중요하다.

| 항목 | 주의사항 |
| --- | --- |
| 코드 관리 | Access Key, Secret Key를 코드에 직접 저장하지 않음 |
| IAM 권한 | 최소 권한 원칙 적용 |
| 로그 | 사용자 질문과 답변에 민감 정보가 포함될 수 있음 |
| 출처 문서 | S3 URI가 노출되어도 되는지 확인 |
| 네트워크 | 사내망 또는 인증된 사용자만 접근하도록 제한 |
| 개인정보 | 사용자 ID, 전화번호, 계정 정보 입력 금지 안내 |
| 명령어 실행 | 챗봇은 명령어를 안내만 하고 자동 실행하지 않도록 구성 |
| 데이터 리전 | 서울 리전 사용 정책을 지키는지 확인 |

특히 운영 챗봇이 다음 정보를 출력하지 않도록 주의해야 한다.

```
비밀번호
Access Key
Secret Key
DB 접속 문자열
개인정보
내부망 IP 전체 목록
관리자 계정 정보
보안 취약점 상세 정보
```

---

# 실습 과제

## 과제 1. CLI 챗봇 실행 및 질문 테스트

요구사항은 다음과 같다.

```
chatbot_cli.py에서 Knowledge Base ID를 본인 값으로 수정한다.
서울 리전 모델 ARN을 확인한다.
CLI 챗봇을 실행한다.
운영 질문 3개 이상을 입력한다.
답변과 출처 문서를 확인한다.
```

실행 명령은 다음과 같다.

```
python chatbot_cli.py
```

질문 예시는 다음과 같다.

```
DB 연결 오류가 발생하면 어떤 순서로 확인해야 해?
```

---

## 과제 2. 검색 문서 수 변경 테스트

요구사항은 다음과 같다.

```
NUMBER_OF_RESULTS 값을 3으로 변경해본다.
동일한 질문을 실행한다.
NUMBER_OF_RESULTS 값을 8로 변경해본다.
동일한 질문을 다시 실행한다.
답변 품질과 출처 문서 차이를 비교한다.
```

수정할 코드는 다음과 같다.

```
NUMBER_OF_RESULTS = 3
```

또는 다음처럼 변경한다.

```
NUMBER_OF_RESULTS = 8
```

---

## 과제 3. 운영 답변 형식 수정

요구사항은 다음과 같다.

```
build_ops_question() 함수의 답변 규칙을 수정한다.
답변에 "주의사항" 항목을 추가한다.
답변에 "관련 담당팀" 항목을 추가한다.
수정 전후 답변 형식을 비교한다.
```

예시 규칙은 다음과 같다.

```
장애 대응 질문이면 다음 형식으로 답한다.
- 현상 요약
- 1차 점검 항목
- 조치 절차
- 확인 명령어
- 주의사항
- 에스컬레이션 기준
- 관련 담당팀
```

---

## 과제 4. Streamlit 웹 챗봇 실행

요구사항은 다음과 같다.

```
app.py에서 Knowledge Base ID를 본인 값으로 수정한다.
서울 리전 모델 ARN을 확인한다.
Streamlit 앱을 실행한다.
웹 브라우저에서 운영 질문을 입력한다.
출처 문서 보기 영역을 확인한다.
```

실행 명령은 다음과 같다.

```
streamlit run app.py
```

---

# 정리

```
Knowledge Base는 이미 생성되어 있다고 가정한다.
S3 운영 매뉴얼은 이미 Knowledge Base에 동기화되어 있다고 가정한다.
서울 리전 ap-northeast-2를 사용한다.
서울 리전에서 사용 가능한 Bedrock 모델 ARN을 사용한다.
Python에서는 boto3의 bedrock-agent-runtime 클라이언트를 사용한다.
retrieve_and_generate API로 Knowledge Base 검색과 답변 생성을 함께 수행한다.
CLI 챗봇은 chatbot_cli.py 하나로 구현한다.
웹 챗봇은 app.py 하나로 구현한다.
답변과 함께 출처 문서를 출력한다.
운영 챗봇은 추측 답변보다 매뉴얼 기반 답변과 출처 확인이 중요하다.
```

최종 파일 구성은 다음과 같다.

```
kb-ops-chatbot/
├── requirements.txt
├── chatbot_cli.py
└── app.py
```

### 과제 : FastAPI를 이용해서 챗봇 만들기