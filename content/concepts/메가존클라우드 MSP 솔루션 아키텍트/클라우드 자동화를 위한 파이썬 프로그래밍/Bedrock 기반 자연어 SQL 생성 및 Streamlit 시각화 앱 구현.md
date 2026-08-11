---
title: "Bedrock 기반 자연어 SQL 생성 및 Streamlit 시각화 앱 구현"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "클라우드 자동화를 위한 파이썬 프로그래밍"]
is_public: true
draft: false
---

# Bedrock 기반 자연어 SQL 생성 및 Streamlit 시각화 앱 구현

## Amazon Bedrock + Athena + Streamlit

---

# 1. 실습 개요

앞에서 준비한 S3와 Athena 환경을 기반으로 자연어 분석 앱을 구현한다.

사용자는 다음과 같이 한국어로 질문한다.

```
월별 매출 추이를 보여줘
```

앱은 이 질문을 Amazon Bedrock에 전달한다.

Bedrock은 질문을 Athena SQL로 변환한다.

Athena는 생성된 SQL을 실행해 S3 데이터를 조회한다.

Python은 Athena 결과 CSV를 읽어 pandas DataFrame으로 변환한다.

Streamlit은 결과를 표와 차트로 보여준다.

2부의 전체 흐름은 다음과 같다.

```
사용자 자연어 질문
        ↓
Streamlit 입력창
        ↓
Bedrock SQL 생성
        ↓
SQL 검증
        ↓
Athena 쿼리 실행
        ↓
S3 결과 CSV 읽기
        ↓
pandas DataFrame 변환
        ↓
Streamlit 표/차트 출력
```

---

# 2. 실습 목표

실습을 완료하면 다음을 수행할 수 있다.

| 항목 | 목표 |
| --- | --- |
| Bedrock | 자연어 질문을 Athena SQL로 변환할 수 있다 |
| boto3 | Python에서 Bedrock Runtime, Athena, S3를 호출할 수 있다 |
| SQL 검증 | 모델이 생성한 SQL을 실행 전에 검사할 수 있다 |
| Athena | Python 코드로 Athena 쿼리를 실행할 수 있다 |
| pandas | Athena 결과를 DataFrame으로 변환할 수 있다 |
| Streamlit | 자연어 기반 데이터 분석 웹 앱을 구현할 수 있다 |
| Plotly | 조회 결과를 차트로 시각화할 수 있다 |

---

# 3. 사전 조건

다음 상태가 준비되어 있어야 한다.

```
S3 버킷 생성 완료
ecommerce_sales.csv 업로드 완료
Athena 결과 저장 경로 생성 완료
Athena 데이터베이스 생성 완료
ecommerce_sales 테이블 생성 완료
Athena 조회 테스트 성공
Bedrock 모델 접근 권한 활성화 완료
```

서울 리전을 사용한다.

```
리전 이름: Asia Pacific (Seoul)
리전 코드: ap-northeast-2
```

---

# 4. Python 패키지 추가 설치

1부의 `requirements.txt`에 웹 화면과 차트 생성을 위한 패키지를 추가한다.

파일명: `requirements.txt`

```
boto3
pandas
streamlit
plotly
python-dotenv
```

각 패키지의 역할은 다음과 같다.

| 패키지 | 설명 |
| --- | --- |
| `boto3` | AWS 서비스를 Python에서 호출한다 |
| `pandas` | Athena 결과를 표 형태로 처리한다 |
| `streamlit` | 웹 기반 데이터 분석 화면을 만든다 |
| `plotly` | 차트를 생성한다 |
| `python-dotenv` | `.env` 파일의 환경 변수를 읽는다 |

패키지를 설치한다.

```
pip install -r requirements.txt
```

설치 확인은 다음 명령어로 할 수 있다.

```
pip list
```

예상 목록에 다음 패키지가 포함되어야 한다.

```
boto3
pandas
streamlit
plotly
python-dotenv
```

---

# 5. 환경 변수 파일 수정

2부에서는 Bedrock 모델 ID가 필요하다.

`.env` 파일에 다음 항목을 추가한다.

```
BEDROCK_MODEL_ID=서울리전에서_활성화한_모델_ID
```

예시는 다음과 같다.

```
AWS_REGION=ap-northeast-2
S3_BUCKET=nlp-s3-analytics-kim-123456789012
DATA_PREFIX=datasets/ecommerce_sales/
ATHENA_OUTPUT_PREFIX=athena-results/
ATHENA_DATABASE=nlp_s3_analytics_db
ATHENA_TABLE=ecommerce_sales
BEDROCK_MODEL_ID=amazon.nova-lite-v1:0
```

각 항목의 의미는 다음과 같다.

| 항목 | 설명 |
| --- | --- |
| `AWS_REGION` | 사용할 AWS 리전이다 |
| `S3_BUCKET` | 원천 데이터와 Athena 결과가 저장되는 버킷이다 |
| `DATA_PREFIX` | CSV 원천 데이터 경로이다 |
| `ATHENA_OUTPUT_PREFIX` | Athena 결과 저장 경로이다 |
| `ATHENA_DATABASE` | Athena 데이터베이스 이름이다 |
| `ATHENA_TABLE` | Athena 테이블 이름이다 |
| `BEDROCK_MODEL_ID` | Bedrock에서 사용할 모델 ID이다 |

`BEDROCK_MODEL_ID`는 학생 계정과 리전에 따라 다를 수 있다.

서울 리전에서 사용할 수 있는 모델을 확인한 뒤 `.env`에 입력한다.

확인 위치는 다음과 같다.

```
Amazon Bedrock 콘솔
→ 리전: 서울 ap-northeast-2
→ Model access
→ 사용 가능한 모델 확인
```

---

# 6. Athena 쿼리 실행 함수 작성

## 6.1 파일 역할

이 파일은 Python 코드에서 Athena SQL을 실행하고 결과를 DataFrame으로 반환하는 공통 함수를 제공한다.

파일명은 다음과 같다.

```
athena_utils.py
```

이 파일이 담당하는 작업은 다음과 같다.

```
.env 파일 읽기
Athena 클라이언트 생성
S3 클라이언트 생성
Athena 쿼리 실행
쿼리 상태 확인
S3에 저장된 Athena 결과 CSV 읽기
pandas DataFrame으로 변환
```

---

## 6.2 코드 작성

파일명: `athena_utils.py`

```
import os
import time
from io import StringIO
from dotenv import load_dotenv
import boto3
import pandas as pd

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
S3_BUCKET = os.getenv("S3_BUCKET")
ATHENA_OUTPUT_PREFIX = os.getenv("ATHENA_OUTPUT_PREFIX", "athena-results/")
ATHENA_DATABASE = os.getenv("ATHENA_DATABASE", "nlp_s3_analytics_db")

athena = boto3.client("athena", region_name=AWS_REGION)
s3 = boto3.client("s3", region_name=AWS_REGION)

def run_athena_query(sql: str) -> pd.DataFrame:
    if not S3_BUCKET:
        raise ValueError(".env 파일에 S3_BUCKET 값을 설정해야 한다.")

    output_location = f"s3://{S3_BUCKET}/{ATHENA_OUTPUT_PREFIX.strip('/')}/"

    response = athena.start_query_execution(
        QueryString=sql,
        QueryExecutionContext={"Database": ATHENA_DATABASE},
        ResultConfiguration={"OutputLocation": output_location}
    )

    query_execution_id = response["QueryExecutionId"]

    while True:
        status_response = athena.get_query_execution(QueryExecutionId=query_execution_id)
        state = status_response["QueryExecution"]["Status"]["State"]

        if state in ["SUCCEEDED", "FAILED", "CANCELLED"]:
            break

        time.sleep(1)

    if state != "SUCCEEDED":
        reason = status_response["QueryExecution"]["Status"].get("StateChangeReason", "Unknown")
        raise RuntimeError(f"Athena 쿼리 실패: {state}, 원인: {reason}")

    result_key = f"{ATHENA_OUTPUT_PREFIX.strip('/')}/{query_execution_id}.csv"
    obj = s3.get_object(Bucket=S3_BUCKET, Key=result_key)
    csv_text = obj["Body"].read().decode("utf-8")

    return pd.read_csv(StringIO(csv_text))
```

---

## 6.3 코드 설명

```
import os
```

환경 변수를 읽기 위해 사용한다.

---

```
import time
```

Athena 쿼리 상태를 일정 간격으로 확인할 때 사용한다.

---

```
from io import StringIO
```

문자열 형태의 CSV 데이터를 파일처럼 읽기 위해 사용한다.

Athena 결과는 S3에서 문자열로 읽어오므로, pandas가 CSV 파일처럼 처리할 수 있게 `StringIO`로 감싼다.

---

```
from dotenv import load_dotenv
```

`.env` 파일을 읽기 위해 사용한다.

---

```
import boto3
```

AWS 서비스 API를 호출하기 위해 사용한다.

---

```
import pandas as pd
```

Athena 결과 CSV를 DataFrame으로 변환하기 위해 사용한다.

---

```
load_dotenv()
```

현재 프로젝트 디렉터리에 있는 `.env` 파일을 읽는다.

---

```
AWS_REGION=os.getenv("AWS_REGION","ap-northeast-2")
```

`.env` 파일에서 AWS 리전을 읽는다.

값이 없으면 기본값으로 서울 리전인 `ap-northeast-2`를 사용한다.

---

```
S3_BUCKET=os.getenv("S3_BUCKET")
```

Athena 결과 CSV가 저장되는 S3 버킷 이름을 읽는다.

---

```
ATHENA_OUTPUT_PREFIX=os.getenv("ATHENA_OUTPUT_PREFIX","athena-results/")
```

Athena 결과 파일이 저장될 S3 prefix를 읽는다.

예시는 다음과 같다.

```
athena-results/
```

---

```
ATHENA_DATABASE=os.getenv("ATHENA_DATABASE","nlp_s3_analytics_db")
```

Athena에서 사용할 데이터베이스 이름을 읽는다.

---

```
athena=boto3.client("athena",region_name=AWS_REGION)
```

Athena 클라이언트를 생성한다.

이 클라이언트로 쿼리를 실행하고 쿼리 상태를 확인한다.

---

```
s3=boto3.client("s3",region_name=AWS_REGION)
```

S3 클라이언트를 생성한다.

이 클라이언트로 Athena 결과 CSV 파일을 읽는다.

---

```
def run_athena_query(sql:str) ->pd.DataFrame:
```

Athena 쿼리를 실행하고 결과를 DataFrame으로 반환하는 함수이다.

인자와 반환값은 다음과 같다.

| 구분 | 설명 |
| --- | --- |
| `sql` | Athena에서 실행할 SQL 문자열 |
| 반환값 | pandas DataFrame |

---

```
if not S3_BUCKET:
	raise ValueError(".env 파일에 S3_BUCKET 값을 설정해야 한다.")
```

S3 버킷 값이 비어 있는지 확인한다.

Athena 결과 저장 위치를 만들려면 S3 버킷 이름이 반드시 필요하다.

---

```
output_location=f"s3://{S3_BUCKET}/{ATHENA_OUTPUT_PREFIX.strip('/')}/"
```

Athena 결과 저장 위치를 만든다.

예시는 다음과 같다.

```
s3://nlp-s3-analytics-kim-123456789012/athena-results/
```

`strip('/')`은 앞뒤의 `/`를 제거한다.

이렇게 하면 경로에서 `/`가 중복되는 것을 방지할 수 있다.

---

```
response=athena.start_query_execution(...)
```

Athena 쿼리를 시작한다.

이 함수는 쿼리 결과 자체를 바로 반환하지 않는다.

대신 쿼리 실행 ID를 반환한다.

---

```
QueryString=sql
```

실행할 SQL 문장을 지정한다.

---

```
QueryExecutionContext={"Database":ATHENA_DATABASE}
```

쿼리를 실행할 Athena 데이터베이스를 지정한다.

---

```
ResultConfiguration={"OutputLocation":output_location}
```

Athena 쿼리 결과를 저장할 S3 경로를 지정한다.

---

```
query_execution_id=response["QueryExecutionId"]
```

실행한 쿼리의 고유 ID를 가져온다.

이 ID는 쿼리 상태 확인과 결과 파일 조회에 사용된다.

---

```
while True:
```

쿼리가 완료될 때까지 반복해서 상태를 확인한다.

---

```
status_response=athena.get_query_execution(QueryExecutionId=query_execution_id)
```

현재 쿼리 실행 상태를 조회한다.

---

```
state=status_response["QueryExecution"]["Status"]["State"]
```

쿼리 상태 값을 가져온다.

Athena 쿼리 상태는 대표적으로 다음과 같다.

| 상태 | 의미 |
| --- | --- |
| `QUEUED` | 대기 중 |
| `RUNNING` | 실행 중 |
| `SUCCEEDED` | 성공 |
| `FAILED` | 실패 |
| `CANCELLED` | 취소됨 |

---

```
if state in ["SUCCEEDED","FAILED","CANCELLED"]:
		break
```

쿼리가 성공, 실패, 취소 중 하나의 최종 상태가 되면 반복문을 종료한다.

---

```
time.sleep(1)
```

1초 기다린 뒤 다시 상태를 확인한다.

이 코드를 넣지 않으면 너무 짧은 시간에 API를 반복 호출하게 된다.

---

```
if state != "SUCCEEDED":
```

쿼리가 성공하지 않았다면 오류를 발생시킨다.

---

```
reason=status_response["QueryExecution"]["Status"].get("StateChangeReason","Unknown")
```

쿼리 실패 원인을 가져온다.

SQL 문법 오류, 테이블 없음, 권한 오류 등이 여기에 포함될 수 있다.

---

```
result_key=f"{ATHENA_OUTPUT_PREFIX.strip('/')}/{query_execution_id}.csv"
```

Athena 결과 CSV의 S3 객체 키를 만든다.

Athena는 보통 다음 형식으로 결과 파일을 저장한다.

```
athena-results/쿼리실행ID.csv
```

---

```
obj=s3.get_object(Bucket=S3_BUCKET,Key=result_key)
```

S3에서 Athena 결과 CSV 파일을 읽는다.

---

```
csv_text=obj["Body"].read().decode("utf-8")
```

S3 객체 본문을 읽고 UTF-8 문자열로 변환한다.

---

```
returnpd.read_csv(StringIO(csv_text))
```

CSV 문자열을 pandas DataFrame으로 변환해서 반환한다.

---

# 7. Bedrock으로 자연어 질문을 SQL로 변환

## 7.1 처리 방식

사용자는 다음과 같이 질문한다.

```
월별 매출 추이를 보여줘
```

Bedrock에는 질문만 전달하지 않는다.

테이블 구조와 SQL 생성 규칙을 함께 전달해야 한다.

Bedrock에 전달할 정보는 다음과 같다.

```
Athena 데이터베이스 이름
Athena 테이블 이름
컬럼 목록
각 컬럼의 의미
매출 계산식
SQL 작성 규칙
금지 SQL 명령어
출력 형식
```

이렇게 해야 모델이 다음처럼 Athena에서 실행 가능한 SQL을 생성할 수 있다.

```
SELECT
  date_format(order_date,'%Y-%m') AS order_month,
  SUM(quantity* unit_price- discount_amount) AS sales
FROM ecommerce_sales
GROUP BY date_format(order_date,'%Y-%m')
ORDER BY order_month;
```

---

## 7.2 파일 역할

파일명은 다음과 같다.

```
bedrock_sql_generator.py
```

이 파일은 다음 작업을 담당한다.

```
.env 파일 읽기
Bedrock Runtime 클라이언트 생성
테이블 스키마 프롬프트 정의
사용자 질문을 Bedrock에 전달
Bedrock 응답에서 SQL 추출
생성된 SQL 검증
최종 SQL 반환
```

---

## 7.3 코드 작성

파일명: `bedrock_sql_generator.py`

```
import os
import re
from dotenv import load_dotenv
import boto3

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID")
ATHENA_DATABASE = os.getenv("ATHENA_DATABASE", "nlp_s3_analytics_db")
ATHENA_TABLE = os.getenv("ATHENA_TABLE", "ecommerce_sales")

if not BEDROCK_MODEL_ID:
    raise ValueError(".env 파일에 BEDROCK_MODEL_ID 값을 설정해야 한다.")

bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)

TABLE_SCHEMA = f"""
데이터베이스: {ATHENA_DATABASE}
테이블: {ATHENA_TABLE}

컬럼:
- order_id string: 주문 ID
- order_date date: 주문일
- customer_id string: 고객 ID
- region string: 지역
- category string: 상품 카테고리
- product_name string: 상품명
- channel string: 판매 채널. web, mobile, store
- quantity int: 주문 수량
- unit_price int: 상품 단가
- discount_amount int: 할인 금액
- payment_method string: 결제 방식
- is_returned boolean: 반품 여부

매출 계산식:
(quantity * unit_price - discount_amount)

주의:
- Athena SQL 문법을 사용한다.
- SELECT 문만 생성한다.
- INSERT, UPDATE, DELETE, DROP, ALTER, CREATE 문은 절대 생성하지 않는다.
- 결과 행 수가 많을 수 있으면 LIMIT 100을 추가한다.
- SQL 외의 설명은 출력하지 않는다.
"""

def extract_sql(text: str) -> str:
    code_block = re.search(r"```sql\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if code_block:
        return code_block.group(1).strip()

    generic_block = re.search(r"```\s*(.*?)```", text, re.DOTALL)
    if generic_block:
        return generic_block.group(1).strip()

    return text.strip()

def validate_sql(sql: str) -> None:
    normalized = sql.strip().lower()

    if not normalized.startswith("select"):
        raise ValueError("SELECT 문만 실행할 수 있다.")

    forbidden_keywords = [
        "insert", "update", "delete", "drop", "alter", "create",
        "truncate", "merge", "grant", "revoke", "unload"
    ]

    for keyword in forbidden_keywords:
        if re.search(rf"\b{keyword}\b", normalized):
            raise ValueError(f"허용되지 않은 SQL 키워드가 포함되어 있다: {keyword}")

    if ATHENA_TABLE.lower() not in normalized:
        raise ValueError(f"허용된 테이블만 조회할 수 있다: {ATHENA_TABLE}")

def generate_sql_from_question(question: str) -> str:
    system_text = f"""
너는 AWS Athena SQL 생성기이다.
사용자의 한국어 질문을 보고 Athena에서 실행 가능한 SQL 하나만 생성한다.

{TABLE_SCHEMA}
"""

    user_text = f"""
사용자 질문:
{question}

SQL만 출력한다.
"""

    response = bedrock.converse(
        modelId=BEDROCK_MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [{"text": user_text}]
            }
        ],
        system=[
            {"text": system_text}
        ],
        inferenceConfig={
            "maxTokens": 800,
            "temperature": 0.0
        }
    )

    output_text = response["output"]["message"]["content"][0]["text"]
    sql = extract_sql(output_text)
    validate_sql(sql)

    return sql
```

---

# 8. Bedrock SQL 생성 코드 설명

## 8.1 모듈 가져오기

```
import os
```

환경 변수를 읽기 위해 사용한다.

```
import re
```

정규표현식을 사용하기 위해 가져온다.

Bedrock 응답에서 SQL 코드블록을 추출하거나 금지 키워드를 검사할 때 사용한다.

```
from dotenv import load_dotenv
```

`.env` 파일을 읽기 위해 사용한다.

```
import boto3
```

Bedrock Runtime API를 호출하기 위해 사용한다.

---

## 8.2 환경 변수 읽기

```
load_dotenv()
```

`.env` 파일을 읽어 환경 변수로 등록한다.

```
AWS_REGION=os.getenv("AWS_REGION","ap-northeast-2")
```

AWS 리전을 읽는다.

값이 없으면 서울 리전 `ap-northeast-2`를 기본값으로 사용한다.

```
BEDROCK_MODEL_ID=os.getenv("BEDROCK_MODEL_ID")
```

Bedrock에서 사용할 모델 ID를 읽는다.

예시는 다음과 같다.

```
amazon.nova-lite-v1:0
```

학생 계정마다 사용 가능한 모델이 다를 수 있으므로, `.env` 파일의 값을 실제 모델 ID로 수정해야 한다.

---

```
ATHENA_DATABASE=os.getenv("ATHENA_DATABASE","nlp_s3_analytics_db")
```

Athena 데이터베이스 이름을 읽는다.

```
ATHENA_TABLE=os.getenv("ATHENA_TABLE","ecommerce_sales")
```

Athena 테이블 이름을 읽는다.

---

## 8.3 Bedrock 모델 ID 검사

```
if not BEDROCK_MODEL_ID:
	raise ValueError(".env 파일에 BEDROCK_MODEL_ID 값을 설정해야 한다.")
```

모델 ID가 없으면 오류를 발생시킨다.

이 검사를 하지 않으면 Bedrock 호출 단계에서 더 복잡한 오류가 발생할 수 있다.

실습에서는 설정 문제를 빨리 찾기 위해 처음에 명확한 오류를 발생시키는 것이 좋다.

---

## 8.4 Bedrock Runtime 클라이언트 생성

```
bedrock=boto3.client("bedrock-runtime",region_name=AWS_REGION)
```

Bedrock Runtime 클라이언트를 생성한다.

Bedrock 서비스에는 여러 API가 있지만, 모델 호출은 `bedrock-runtime` 클라이언트로 수행한다.

---

## 8.5 테이블 스키마 프롬프트 작성

```
TABLE_SCHEMA=f"""
데이터베이스:{ATHENA_DATABASE}
테이블:{ATHENA_TABLE}

컬럼:
...
"""
```

이 문자열은 Bedrock에 전달할 테이블 설명이다.

자연어를 SQL로 바꾸려면 모델이 테이블 구조를 알아야 한다.

예를 들어 사용자가 다음과 같이 질문했다고 하자.

```
지역별 주문 건수를 알려줘
```

모델이 `region`이라는 컬럼이 지역을 의미한다는 사실을 알아야 다음과 같은 SQL을 만들 수 있다.

```
SELECT
  region,
COUNT(*) AS order_count
FROM ecommerce_sales
GROUP BY region
ORDER BY order_countDESC;
```

---

## 8.6 매출 계산식 제공

```
매출 계산식:
(quantity * unit_price - discount_amount)
```

사용자가 “매출”이라고 질문했을 때 어떤 계산식을 사용해야 하는지 알려준다.

이 설명이 없으면 모델이 다음처럼 잘못된 SQL을 만들 수 있다.

```
SELECT SUM(unit_price)AS sales
FROM ecommerce_sales;
```

위 SQL은 단가만 합산하므로 실제 매출 계산이 아니다.

이번 실습의 매출 계산식은 다음과 같다.

```
매출 = 수량 * 단가 - 할인금액
```

따라서 SQL에서는 다음 식을 사용한다.

```
quantity* unit_price- discount_amount
```

---

## 8.7 SQL 생성 규칙 제공

```
주의:
- Athena SQL 문법을 사용한다.
- SELECT 문만 생성한다.
- INSERT, UPDATE, DELETE, DROP, ALTER, CREATE 문은 절대 생성하지 않는다.
- 결과 행 수가 많을 수 있으면 LIMIT 100을 추가한다.
- SQL 외의 설명은 출력하지 않는다.
```

이 규칙은 모델이 SQL을 안전하고 실행 가능한 형태로 만들도록 유도한다.

특히 다음 문장이 중요하다.

```
SQL 외의 설명은 출력하지 않는다.
```

모델이 설명 문장을 함께 출력하면 Athena에서 바로 실행할 수 없다.

---

## 8.8 SQL 코드블록 추출 함수

```
def extract_sql(text:str) ->str:
```

Bedrock 응답에서 SQL만 추출하는 함수이다.

모델은 때때로 다음처럼 코드블록으로 SQL을 반환할 수 있다.

```
```sql
SELECT category, COUNT(*)
FROM ecommerce_sales
GROUP BY category;
```

```
이 경우 코드블록 표시인 ```sql 과 ``` 를 제거해야 한다.

---

```python id="yjf1rq"
code_block = re.search(r"```sql\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
```

```` ```sql ... ``` ```` 형태의 코드블록을 찾는다.

| 요소 | 의미 |
| --- | --- |
| `re.search()` | 문자열에서 패턴과 일치하는 부분을 찾는다 |
| `r"..."` | raw string이다. 정규표현식을 작성할 때 사용한다 |
| `.*?` | 가능한 짧게 임의의 문자를 찾는다 |
| `re.DOTALL` | 줄바꿈까지 포함해서 검색한다 |
| `re.IGNORECASE` | 대소문자를 구분하지 않는다 |

---

```
ifcode_block:
returncode_block.group(1).strip()
```

SQL 코드블록이 있으면 코드블록 내부 내용만 반환한다.

---

```
generic_block=re.search(r"```\s*(.*?)```",text,re.DOTALL)
```

`sql`이라는 언어 표시가 없는 일반 코드블록도 처리한다.

---

```
returntext.strip()
```

코드블록이 없으면 응답 전체를 SQL로 보고 앞뒤 공백만 제거한다.

# 9. SQL 검증 로직 이해

## 9.1 SQL 검증이 필요한 이유

Bedrock이 생성한 SQL을 바로 실행하면 위험할 수 있다.

예를 들어 사용자가 다음과 같이 입력할 수 있다.

```
테이블 삭제하는 SQL을 만들어줘
```

또는 모델이 의도하지 않게 다음과 같은 SQL을 만들 수 있다.

```
DROPTABLE ecommerce_sales;
```

따라서 모델이 생성한 SQL은 Athena에서 실행하기 전에 반드시 검증해야 한다.

이번 실습에서는 다음 규칙을 적용한다.

```
SELECT 문만 허용
위험 키워드 차단
허용된 테이블만 조회
```

---

## 9.2 validate\_sql 함수

```
def validate_sql(sql:str) -> None:
```

SQL 문자열을 검사하는 함수이다.

문제가 없으면 아무 값도 반환하지 않는다.

문제가 있으면 `ValueError`를 발생시킨다.

---

## 9.3 SQL 소문자 변환

```
normalized=sql.strip().lower()
```

검사를 쉽게 하기 위해 SQL을 소문자로 변환한다.

예를 들어 다음 SQL은

```
SELECT * FROM ecommerce_sales;
```

검사 단계에서는 다음처럼 바뀐다.

```
select * from ecommerce_sales;
```

---

## 9.4 SELECT 문만 허용

```
if not normalized.startswith("select"):
	raise ValueError("SELECT 문만 실행할 수 있다.")
```

SQL이 `select`로 시작하지 않으면 실행하지 않는다.

이번 실습에서는 조회만 허용한다.

데이터 변경, 테이블 삭제, 테이블 생성은 허용하지 않는다.

---

## 9.5 위험 키워드 목록

```
forbidden_keywords= [
"insert","update","delete","drop","alter","create",
"truncate","merge","grant","revoke","unload"
]
```

이 목록은 실행을 차단할 SQL 키워드이다.

| 키워드 | 위험성 |
| --- | --- |
| `insert` | 데이터를 추가할 수 있다 |
| `update` | 데이터를 변경할 수 있다 |
| `delete` | 데이터를 삭제할 수 있다 |
| `drop` | 테이블이나 데이터베이스를 삭제할 수 있다 |
| `alter` | 테이블 구조를 변경할 수 있다 |
| `create` | 새 테이블이나 데이터베이스를 만들 수 있다 |
| `truncate` | 테이블 데이터를 비울 수 있다 |
| `grant` | 권한을 부여할 수 있다 |
| `revoke` | 권한을 회수할 수 있다 |
| `unload` | 조회 결과를 외부 위치로 내보낼 수 있다 |

---

## 9.6 금지 키워드 검사

```
for keyword in forbidden_keywords:
	if re.search(rf"\b{keyword}\b",normalized):
		raise ValueError(f"허용되지 않은 SQL 키워드가 포함되어 있다:{keyword}")
```

이 코드는 SQL에 금지 키워드가 포함되어 있는지 검사한다.

`rf"\b{keyword}\b"`에서 `\b`는 단어 경계를 의미한다.

즉, `drop`이라는 단어가 독립적으로 등장하는지 확인한다.

---

## 9.7 허용 테이블 확인

```
if ATHENA_TABLE.lower() not in normalized:
	raise ValueError(f"허용된 테이블만 조회할 수 있다:{ATHENA_TABLE}")
```

이번 실습에서는 `ecommerce_sales` 테이블만 조회하도록 제한한다.

이 검증이 없으면 사용자가 다른 테이블이나 시스템 테이블을 조회하도록 유도할 수 있다.

---

# 10. CLI 테스트 프로그램 작성

## 10.1 파일 역할

파일명은 다음과 같다.

```
03_ask_cli.py
```

이 파일은 터미널에서 자연어 질문을 입력받아 다음 작업을 수행한다.

```
사용자 질문 입력
        ↓
Bedrock으로 SQL 생성
        ↓
생성된 SQL 출력
        ↓
Athena 쿼리 실행
        ↓
조회 결과 출력
```

Streamlit 앱을 만들기 전에 CLI에서 먼저 테스트하면 오류를 더 쉽게 찾을 수 있다.

---

## 10.2 코드 작성

파일명: `03_ask_cli.py`

```
from bedrock_sql_generator import generate_sql_from_question
from athena_utils import run_athena_query

question=input("질문 입력: ").strip()

sql=generate_sql_from_question(question)
print("\n[생성된 SQL]")
print(sql)

df=run_athena_query(sql)
print("\n[조회 결과]")
print(df)
```

---

## 10.3 코드 설명

```
frombedrock_sql_generatorimportgenerate_sql_from_question
```

`bedrock_sql_generator.py` 파일에서 자연어 질문을 SQL로 변환하는 함수를 가져온다.

---

```
fromathena_utilsimportrun_athena_query
```

`athena_utils.py` 파일에서 Athena 쿼리를 실행하는 함수를 가져온다.

---

```
question=input("질문 입력: ").strip()
```

터미널에서 사용자의 자연어 질문을 입력받는다.

`strip()`은 앞뒤 공백을 제거한다.

---

```
sql=generate_sql_from_question(question)
```

Bedrock을 호출해 자연어 질문을 SQL로 변환한다.

---

```
print("\n[생성된 SQL]")
print(sql)
```

모델이 생성한 SQL을 화면에 출력한다.

SQL이 올바르게 생성되었는지 확인하기 위한 단계이다.

---

```
df=run_athena_query(sql)
```

생성된 SQL을 Athena에서 실행한다.

결과는 pandas DataFrame으로 반환된다.

---

```
print("\n[조회 결과]")
print(df)
```

조회 결과를 터미널에 출력한다.

---

## 10.4 실행

다음 명령어를 실행한다.

```
python 03_ask_cli.py
```

질문을 입력한다.

```
질문 입력: 카테고리별 매출 TOP 5를 보여줘
```

예상 출력은 다음과 비슷하다.

```
[생성된 SQL]
SELECT
  category,
  SUM(quantity * unit_price - discount_amount) AS sales
FROM ecommerce_sales
GROUP BY category
ORDER BY sales DESC
LIMIT 5

[조회 결과]
  category     sales
0     전자기기  12345678
1       패션   3456789
2       도서   2345678
```

실제 결과는 샘플 데이터 내용에 따라 다를 수 있다.

---

# 11. Streamlit 시각화 앱 작성

## 11.1 파일 역할

파일명은 다음과 같다.

```
04_streamlit_app.py
```

이 파일은 웹 기반 자연어 분석 화면을 만든다.

앱에서 수행하는 작업은 다음과 같다.

```
자연어 질문 입력창 제공
차트 유형 선택 메뉴 제공
Bedrock으로 SQL 생성
생성된 SQL 출력
Athena 쿼리 실행
조회 결과 표 출력
조회 결과 차트 출력
오류 메시지 출력
```

---

## 11.2 코드 작성

파일명: `04_streamlit_app.py`

```
import streamlit as st
import plotly.express as px

from bedrock_sql_generator import generate_sql_from_question
from athena_utils import run_athena_query

st.set_page_config(
    page_title="자연어 기반 S3 데이터 분석",
    layout="wide"
)

st.title("자연어 기반 S3 데이터 분석 및 시각화")
st.caption("Amazon Bedrock + Amazon Athena + Amazon S3 + Streamlit")

examples = [
    "전체 매출 합계를 알려줘",
    "월별 매출 추이를 보여줘",
    "카테고리별 매출 TOP 5를 보여줘",
    "지역별 주문 건수를 알려줘",
    "반품률이 가장 높은 카테고리를 보여줘",
    "2026년 1월 일자별 매출을 보여줘"
]

question = st.text_input(
    "분석 질문",
    value=examples[0],
    placeholder="예: 카테고리별 매출 TOP 5를 보여줘"
)

chart_type = st.selectbox(
    "차트 유형",
    ["자동", "막대그래프", "선그래프", "파이차트", "차트 없음"]
)

run_button = st.button("분석 실행")

if run_button:
    try:
        with st.spinner("Bedrock으로 SQL 생성 중..."):
            sql = generate_sql_from_question(question)

        st.subheader("생성된 SQL")
        st.code(sql, language="sql")

        with st.spinner("Athena 쿼리 실행 중..."):
            df = run_athena_query(sql)

        st.subheader("조회 결과")
        st.dataframe(df, use_container_width=True)

        if df.empty:
            st.warning("조회 결과가 없다.")
        elif chart_type != "차트 없음":
            st.subheader("시각화")

            columns = list(df.columns)

            if len(columns) >= 2:
                x_col = columns[0]
                y_col = columns[1]

                if chart_type == "선그래프":
                    fig = px.line(df, x=x_col, y=y_col, markers=True)
                    st.plotly_chart(fig, use_container_width=True)
                elif chart_type == "파이차트":
                    fig = px.pie(df, names=x_col, values=y_col)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    # '자동' 또는 '막대그래프'인 경우
                    fig = px.bar(df, x=x_col, y=y_col)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("차트를 만들려면 최소 2개 컬럼이 필요하다.")

    except Exception as e:
        st.error(str(e))
```

---

# 12. Streamlit 코드 설명

## 12.1 Streamlit과 Plotly 가져오기

```
import streamlit as st
```

Streamlit 라이브러리를 가져온다.

`st`는 Streamlit 기능을 호출하기 위한 별칭이다.

---

```
import plotly.express as px
```

Plotly Express를 가져온다.

간단한 막대그래프, 선그래프, 파이차트를 만들 때 사용한다.

---

## 12.2 직접 작성한 함수 가져오기

```
from bedrock_sql_generator import generate_sql_from_question
```

자연어 질문을 SQL로 변환하는 함수를 가져온다.

---

```
from athena_utils import run_athena_query
```

Athena에서 SQL을 실행하고 결과를 DataFrame으로 가져오는 함수를 가져온다.

---

## 12.3 페이지 설정

```
st.set_page_config(
	page_title="자연어 기반 S3 데이터 분석",
	layout="wide"
)
```

Streamlit 페이지의 기본 설정이다.

| 옵션 | 설명 |
| --- | --- |
| `page_title` | 브라우저 탭에 표시될 제목 |
| `layout="wide"` | 화면을 넓게 사용 |

---

## 12.4 제목과 설명 출력

```
st.title("자연어 기반 S3 데이터 분석 및 시각화")
```

웹 페이지 상단에 큰 제목을 출력한다.

---

```
st.caption("Amazon Bedrock + Amazon Athena + Amazon S3 + Streamlit")
```

제목 아래에 작은 설명 문구를 출력한다.

---

## 12.5 예시 질문 목록

```
examples= [
	"전체 매출 합계를 알려줘",
	"월별 매출 추이를 보여줘",
	"카테고리별 매출 TOP 5를 보여줘",
	"지역별 주문 건수를 알려줘",
	"반품률이 가장 높은 카테고리를 보여줘",
	"2026년 1월 일자별 매출을 보여줘"
]
```

학생이 바로 테스트할 수 있는 예시 질문 목록이다.

예시 질문을 제공하면 학생이 어떤 질문을 입력해야 할지 쉽게 이해할 수 있다.

---

## 12.6 자연어 입력창

```
question=st.text_input(
		"분석 질문",
		value=examples[0],
		placeholder="예: 카테고리별 매출 TOP 5를 보여줘"
)
```

자연어 질문을 입력하는 텍스트 박스를 만든다.

| 옵션 | 설명 |
| --- | --- |
| `"분석 질문"` | 입력창의 라벨 |
| `value=examples[0]` | 기본 입력값 |
| `placeholder` | 입력 예시 안내 문구 |

---

## 12.7 차트 유형 선택

```
chart_type=st.selectbox(
"차트 유형",
    ["자동","막대그래프","선그래프","파이차트","차트 없음"]
)
```

차트 유형을 선택하는 드롭다운 메뉴를 만든다.

이번 실습에서는 `자동`도 막대그래프와 동일하게 처리된다.

| 선택값 | 동작 |
| --- | --- |
| `자동` | 기본적으로 막대그래프 출력 |
| `막대그래프` | 막대그래프 출력 |
| `선그래프` | 선그래프 출력 |
| `파이차트` | 파이차트 출력 |
| `차트 없음` | 표만 출력 |

---

## 12.8 분석 실행 버튼

```
run_button=st.button("분석 실행")
```

분석 실행 버튼을 만든다.

사용자가 이 버튼을 클릭하면 `run_button` 값이 `True`가 된다.

---

```
if run_button:
```

버튼이 눌렸을 때만 아래 분석 로직을 실행한다.

---

## 12.9 예외 처리 구조

```
try:
    ...
except Exceptionase:
		st.error(str(e))
```

분석 과정에서 오류가 발생하면 앱이 중단되지 않고 화면에 오류 메시지를 출력한다.

오류가 발생할 수 있는 대표 상황은 다음과 같다.

```
Bedrock 모델 ID가 잘못됨
Bedrock 모델 접근 권한이 없음
Athena SQL 문법 오류 발생
S3 결과 파일을 읽을 수 없음
.env 설정값이 누락됨
```

---

## 12.10 Bedrock SQL 생성

```
withst.spinner("Bedrock으로 SQL 생성 중..."):
sql=generate_sql_from_question(question)
```

`st.spinner()`는 작업이 진행 중임을 화면에 표시한다.

`generate_sql_from_question(question)`은 사용자의 자연어 질문을 Bedrock에 전달하고 SQL을 반환한다.

---

## 12.11 생성된 SQL 출력

```
st.subheader("생성된 SQL")
st.code(sql,language="sql")
```

생성된 SQL을 코드 블록 형태로 출력한다.

이 SQL을 보고 Bedrock이 어떤 쿼리를 만들었는지 확인할 수 있다.

---

## 12.12 Athena 쿼리 실행

```
with st.spinner("Athena 쿼리 실행 중..."):
	df=run_athena_query(sql)
```

생성된 SQL을 Athena에서 실행한다.

결과는 pandas DataFrame인 `df`에 저장된다.

---

## 12.13 조회 결과 출력

```
st.subheader("조회 결과")
st.dataframe(df,use_container_width=True)
```

조회 결과를 표 형태로 출력한다.

`use_container_width=True`는 표를 화면 너비에 맞게 표시한다.

---

## 12.14 결과가 비어 있는 경우 처리

```
if df.empty:
  st.warning("조회 결과가 없다.")
```

Athena 쿼리는 성공했지만 결과 행이 없을 수 있다.

이 경우 빈 차트를 만들지 않고 경고 메시지를 출력한다.

---

## 12.15 차트 출력 조건

```
elifchart_type != "차트 없음":
```

사용자가 `차트 없음`을 선택하지 않은 경우에만 차트를 출력한다.

---

## 12.16 차트에 사용할 컬럼 선택

```
columns=list(df.columns)

if len(columns) >= 2:
	x_col=columns[0]
	y_col=columns[1]
```

조회 결과에서 첫 번째 컬럼을 X축, 두 번째 컬럼을 Y축으로 사용한다.

예를 들어 결과가 다음과 같다면

| category | sales |
| --- | --- |
| 전자기기 | 12000000 |
| 패션 | 8000000 |

다음처럼 사용된다.

| 역할 | 컬럼 |
| --- | --- |
| X축 | `category` |
| Y축 | `sales` |

---

## 12.17 선그래프 출력

```
if chart_type=="선그래프":
	fig=px.line(df,x=x_col,y=y_col,markers=True)
	st.plotly_chart(fig,use_container_width=True)
```

선그래프는 시간 흐름에 따른 변화를 표현할 때 적합하다.

예시는 다음과 같다.

```
월별 매출 추이
일자별 주문 건수
주차별 반품률
```

---

## 12.18 파이차트 출력

```
elif chart_type=="파이차트":
	fig=px.pie(df,names=x_col,values=y_col)
	st.plotly_chart(fig,use_container_width=True)
```

파이차트는 비중을 표현할 때 적합하다.

예시는 다음과 같다.

```
지역별 주문 비중
카테고리별 매출 비중
판매 채널별 주문 비중
```

---

## 12.19 막대그래프 출력

```
else:
fig=px.bar(df,x=x_col,y=y_col)
st.plotly_chart(fig,use_container_width=True)
```

막대그래프는 그룹별 값을 비교할 때 적합하다.

예시는 다음과 같다.

```
카테고리별 매출
지역별 주문 건수
상품별 판매 수량
```

---

## 12.20 차트를 만들 수 없는 경우

```
else:
st.info("차트를 만들려면 최소 2개 컬럼이 필요하다.")
```

차트는 보통 X축과 Y축이 필요하다.

조회 결과 컬럼이 1개뿐이면 표는 출력할 수 있지만 차트 생성은 어렵다.

예를 들어 다음 결과는 컬럼이 1개뿐이다.

total\_sales

---

30000000

---

이런 경우에는 차트 대신 표로 확인한다.

# 13. Streamlit 앱 실행

다음 명령어로 앱을 실행한다.

```
streamlit run 04_streamlit_app.py
```

명령어 설명은 다음과 같다.

| 명령어 | 설명 |
| --- | --- |
| `streamlit run` | Streamlit 앱을 실행한다 |
| `04_streamlit_app.py` | 실행할 앱 파일 |

정상적으로 실행되면 브라우저가 열리고 다음과 같은 주소가 표시된다.

```
http://localhost:8501
```

브라우저가 자동으로 열리지 않으면 터미널에 표시된 URL을 직접 복사해서 브라우저에 붙여넣는다.

---

# 14. 앱 테스트

## 14.1 기본 질문 테스트

입력창에 다음 질문을 입력한다.

```
전체 매출 합계를 알려줘
```

차트 유형은 `차트 없음`을 선택해도 된다.

전체 매출 합계는 결과 컬럼이 1개일 가능성이 높기 때문에 표로 확인하는 것이 적합하다.

예상 SQL은 다음과 비슷하다.

```
SELECT
  SUM(quantity* unit_price- discount_amount) AS total_sales
FROM ecommerce_sales;
```

---

## 14.2 카테고리별 매출 테스트

질문을 다음과 같이 입력한다.

```
카테고리별 매출 TOP 5를 보여줘
```

차트 유형은 `막대그래프`를 선택한다.

예상 SQL은 다음과 비슷하다.

```
SELECT
  category,
  SUM(quantity* unit_price- discount_amount)AS sales
FROM ecommerce_sales
GROUP BY category
ORDER BY salesDESC
LIMIT 5;
```

화면에서 확인할 항목은 다음과 같다.

```
생성된 SQL
카테고리별 매출 표
카테고리별 매출 막대그래프
```

---

## 14.3 월별 매출 추이 테스트

질문을 다음과 같이 입력한다.

```
월별 매출 추이를 보여줘
```

차트 유형은 `선그래프`를 선택한다.

예상 SQL은 다음과 비슷하다.

```
SELECT
  date_format(order_date,'%Y-%m') AS order_month,
  SUM(quantity* unit_price- discount_amount) AS sales
FROM ecommerce_sales
GROUP BY date_format(order_date,'%Y-%m')
ORDER BY order_month;
```

선그래프는 시간 흐름에 따른 변화를 보기 좋다.

---

## 14.4 지역별 주문 건수 테스트

질문을 다음과 같이 입력한다.

```
지역별 주문 건수를 알려줘
```

차트 유형은 `막대그래프`를 선택한다.

예상 SQL은 다음과 비슷하다.

```
SELECT
  region,
COUNT(*) AS order_count
FROM ecommerce_sales
GROUP BY region
ORDER BY order_countDESC;
```

---

## 14.5 반품률 분석 테스트

질문을 다음과 같이 입력한다.

```
반품률이 가장 높은 카테고리 TOP 5를 보여줘
```

차트 유형은 `막대그래프`를 선택한다.

예상 SQL은 다음과 비슷하다.

```
SELECT
  category,
  SUM(CASEWHEN is_returned=trueTHEN1ELSE0END)*100.0/COUNT(*) AS return_rate
FROM ecommerce_sales
GROUP BY category
ORDER BY return_rateDESC
LIMIT5;
```

---

# 15. 실습 질문 예시

## 15.1 기본 집계 질문

```
전체 주문 건수를 알려줘
```

```
전체 매출 합계를 알려줘
```

```
전체 반품 건수를 알려줘
```

---

## 15.2 그룹별 집계 질문

```
카테고리별 매출을 보여줘
```

```
지역별 주문 건수를 알려줘
```

```
판매 채널별 매출을 비교해줘
```

```
결제 방식별 주문 건수를 보여줘
```

---

## 15.3 날짜 기반 분석 질문

```
월별 매출 추이를 보여줘
```

```
2026년 1월 일자별 매출을 보여줘
```

```
2026년 2월 카테고리별 매출을 보여줘
```

---

## 15.4 TOP N 분석 질문

```
매출이 높은 상품 TOP 10을 보여줘
```

```
주문 수량이 많은 카테고리 TOP 5를 알려줘
```

```
반품률이 가장 높은 카테고리 TOP 5를 보여줘
```

---

# 16. 예상 SQL 예시

## 16.1 전체 매출 합계

질문:

```
전체 매출 합계를 알려줘
```

예상 SQL:

```
SELECT
  SUM(quantity* unit_price- discount_amount) AS total_sales
FROM ecommerce_sales;
```

---

## 16.2 카테고리별 매출

질문:

```
카테고리별 매출을 보여줘
```

예상 SQL:

```
SELECT
  category,
  SUM(quantity* unit_price- discount_amount) AS sales
FROM ecommerce_sales
GROUP BY category
ORDER BY sales DESC;
```

---

## 16.3 월별 매출 추이

질문:

```
월별 매출 추이를 보여줘
```

예상 SQL:

```
SELECT
  date_format(order_date,'%Y-%m') AS order_month,
  SUM(quantity* unit_price- discount_amount) AS sales
FROM ecommerce_sales
GROUP BY date_format(order_date,'%Y-%m')
ORDER BY order_month;
```

---

## 16.4 반품률이 높은 카테고리

질문:

```
반품률이 가장 높은 카테고리 TOP 5를 보여줘
```

예상 SQL:

```
SELECT
  category,
  SUM(CASEWHEN is_returned=trueTHEN1ELSE0END)*100.0/COUNT(*) AS return_rate
FROM ecommerce_sales
GROUP BY category
ORDER BY return_rateDESC
LIMIT5;
```

---

# 17. 자주 발생하는 오류와 해결

## 17.1 Bedrock 모델 접근 오류

오류 예시는 다음과 같다.

```
AccessDeniedException
```

가능한 원인은 다음과 같다.

```
Bedrock 모델 접근 권한이 활성화되지 않음
BEDROCK_MODEL_ID 값이 잘못됨
서울 리전에서 해당 모델을 사용할 수 없음
IAM에 bedrock:InvokeModel 권한이 없음
```

해결 방법은 다음과 같다.

```
Amazon Bedrock 콘솔에서 Model access 확인
.env 파일의 BEDROCK_MODEL_ID 확인
AWS_REGION이 ap-northeast-2인지 확인
수업용 IAM 권한 확인
```

---

## 17.2 Bedrock 모델 ID 오류

오류 예시는 다음과 같다.

```
ValidationException: The provided model identifier is invalid
```

가능한 원인은 다음과 같다.

```
BEDROCK_MODEL_ID 오타
현재 리전에서 지원하지 않는 모델 ID 사용
모델 접근 권한이 없는 모델 사용
```

해결 방법은 다음과 같다.

```
Bedrock 콘솔에서 실제 모델 ID 확인
.env 파일 수정
터미널 또는 Streamlit 앱 재실행
```

---

## 17.3 Athena 쿼리 실패

오류 예시는 다음과 같다.

```
Athena 쿼리 실패: FAILED, 원인: ...
```

가능한 원인은 다음과 같다.

```
생성된 SQL 문법 오류
테이블 이름 오류
컬럼 이름 오류
Athena 결과 저장 S3 경로 오류
```

해결 방법은 다음과 같다.

```
Streamlit 화면의 생성된 SQL 확인
Athena Query editor에서 SQL 직접 실행
.env의 ATHENA_DATABASE, ATHENA_TABLE 값 확인
S3의 athena-results/ 경로 확인
```

---

## 17.4 SQL 검증 오류

오류 예시는 다음과 같다.

```
SELECT 문만 실행할 수 있다.
```

또는 다음과 같다.

```
허용되지 않은 SQL 키워드가 포함되어 있다: drop
```

가능한 원인은 다음과 같다.

```
모델이 SELECT가 아닌 SQL을 생성함
사용자 질문이 데이터 삭제나 생성과 관련됨
모델 응답에 설명 문장이 섞임
```

해결 방법은 다음과 같다.

```
질문을 조회 중심으로 다시 작성
프롬프트의 SQL만 출력한다 조건 강화
extract_sql 함수 확인
```

---

## 17.5 Streamlit 앱 실행 오류

오류 예시는 다음과 같다.

```
ModuleNotFoundError: No module named 'streamlit'
```

해결 방법은 다음과 같다.

```
pip install-r requirements.txt
```

가상환경이 활성화되어 있는지도 확인한다.

```
which python
which pip
```

Windows PowerShell에서는 다음 명령어를 사용한다.

```
wherepython
wherepip
```

---

# 18. 실습 과제

## 과제 1. 자연어 질문 실행 결과 정리

다음 질문을 Streamlit 앱에서 실행한다.

```
전체 매출 합계를 알려줘
카테고리별 매출 TOP 5를 보여줘
월별 매출 추이를 보여줘
지역별 주문 건수를 알려줘
반품률이 가장 높은 카테고리를 보여줘
```

제출 항목은 다음과 같다.

```
질문
생성된 SQL
조회 결과
차트 화면
```

---

## 과제 2. SQL 검증 로직 강화

`validate_sql()` 함수에 다음 기능을 추가한다.

```
세미콜론이 2개 이상이면 차단
information_schema 조회 차단
허용 컬럼 목록에 없는 컬럼 사용 시 차단
LIMIT이 없으면 자동으로 LIMIT 100 추가
```

---

## 과제 3. 차트 유형 자동 추천

현재 앱은 차트 유형을 사용자가 직접 선택한다.

이를 Bedrock이 자동 추천하도록 변경한다.

Bedrock 출력 형식을 다음 JSON 형태로 제한한다.

```
{
  "sql":"SELECT ...",
  "chart_type":"bar"
}
```

허용할 차트 유형은 다음과 같다.

```
bar
line
pie
table
```

---

## 과제 4. 데이터 컬럼 확장

샘플 데이터에 다음 컬럼을 추가한다.

```
age_group
gender
membership_level
delivery_status
```

추가 후 Athena 테이블도 수정하고 다음 질문을 분석한다.

```
멤버십 등급별 매출을 보여줘
연령대별 반품률을 보여줘
배송 상태별 주문 건수를 알려줘
```

---

# 19. 정리

Amazon Bedrock을 사용해 자연어 질문을 SQL로 변환하고, Athena 조회 결과를 Streamlit으로 시각화했다.

실습한 흐름은 다음과 같다.

```
자연어 질문 입력
        ↓
Bedrock SQL 생성
        ↓
SQL 검증
        ↓
Athena 쿼리 실행
        ↓
S3 결과 CSV 읽기
        ↓
pandas DataFrame 변환
        ↓
Streamlit 표/차트 출력
```

전체 실습을 완료하면 다음 구조를 구현한 것이다.

```
CSV 데이터 생성
→ S3 업로드
→ Athena 테이블 생성
→ Bedrock 자연어 SQL 생성
→ Athena 쿼리 실행
→ pandas DataFrame 변환
→ Streamlit 시각화
```

이 구조는 다음과 같은 실무 시스템으로 확장할 수 있다.

```
운영 로그 자연어 분석 도구
보안 이벤트 질의 시스템
클라우드 비용 분석 챗봇
S3 데이터 레이크 질의 인터페이스
관리자용 자연어 BI 대시보드
```

---

# 20. 실습 리소스 삭제

실습 후 비용 발생을 막기 위해 리소스를 삭제한다.

## 20.1 S3 객체 삭제

아래 명령어에서 버킷 이름은 본인 버킷명으로 변경한다.

```
aws s3rm s3://nlp-s3-analytics-kim-123456789012--recursive
```

명령어 설명은 다음과 같다.

| 명령어 | 설명 |
| --- | --- |
| `aws s3 rm` | S3 객체를 삭제한다 |
| `--recursive` | 버킷 안의 모든 객체를 재귀적으로 삭제한다 |

---

## 20.2 S3 버킷 삭제

버킷 안의 객체를 모두 삭제한 뒤 버킷을 삭제한다.

```
aws s3api delete-bucket \
--bucket nlp-s3-analytics-kim-123456789012 \
--region ap-northeast-2
```

버킷이 비어 있지 않으면 삭제가 실패한다.

---

## 20.3 Athena 테이블과 데이터베이스 삭제

Athena Query editor에서 실행한다.

```
DROP TABLE IF EXISTS nlp_s3_analytics_db.ecommerce_sales;
DROP DATABASE IF EXISTS nlp_s3_analytics_db;
```

---

## 20.4 로컬 실습 폴더 삭제

macOS 또는 Linux:

```
cd ..
rm -rf nlp-s3-bedrock-athena-lab
```

Windows PowerShell:

```
Remove-Item-Recurse-Force .\nlp-s3-bedrock-athena-lab
```