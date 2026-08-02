---
title: "2-5 파일 처리와 JSON 처리"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "클라우드 자동화를 위한 파이썬 프로그래밍", "2장 자동화 코드를 위한 파이썬 기초 문법"]
is_public: true
draft: false
---

# 2-5. 파일 처리와 JSON 처리

## 학습 목표

* 파일 처리의 의미를 설명할 수 있다.

* 텍스트 파일을 생성하고 내용을 저장할 수 있다.

* 텍스트 파일을 읽고 줄 단위로 처리할 수 있다.

* `with open()` 구문의 의미를 설명할 수 있다.

* JSON 형식의 의미를 설명할 수 있다.

* Python 딕셔너리와 JSON의 관계를 이해할 수 있다.

* `json.dump()`와 `json.load()`를 사용해 JSON 파일을 저장하고 읽을 수 있다.

* 자동화 코드에서 설정 파일과 결과 파일을 다루는 기본 구조를 작성할 수 있다.

---

## 주요 키워드

* 파일 처리

* open

* read

* write

* with

* encoding

* JSON

* json.dump

* json.load

* 설정 파일

* 결과 저장

---

## 1. 파일 처리가 왜 필요한가

자동화 코드에서는 실행 결과를 화면에만 보여주는 경우도 있지만, 실제로는 파일로 저장하는 경우가 매우 많다.

예를 들면 다음과 같은 경우가 있다.

* 조회한 인스턴스 목록을 텍스트 파일로 저장

* 로그 분석 결과를 파일로 저장

* 설정값을 JSON 파일로 분리

* 챗봇이 참고할 운영 정보를 텍스트 파일로 저장

* 실행 결과를 다음 단계에서 다시 사용하기 위해 파일로 남김

즉, 자동화 코드에서 파일 처리는 기본 기능에 가깝다.

---

## 2. 파일 열기: open()

파이썬에서 파일을 열 때는 `open()`을 사용한다.

기본 형태는 다음과 같다.

```
open("파일이름", "모드")
```

예를 들면 다음과 같다.

```
open("sample.txt", "w")
```

여기서 `"w"`는 쓰기 모드이다.

하지만 실제로는 `open()`만 단독으로 쓰기보다 `with open()` 구조를 많이 사용한다.

이유는 파일을 사용한 뒤 자동으로 닫아주기 때문이다.

---

## 3. with open() 구조

기본 구조는 다음과 같다.

```
with open("sample.txt", "w", encoding="utf-8") as file:
    file.write("hello\n")
```

이 구조를 해석하면 다음과 같다.

* `"sample.txt"` 파일을 연다.

* `"w"` 모드로 연다.

* `utf-8` 인코딩을 사용한다.

* 열린 파일을 `file`이라는 이름으로 사용한다.

* 들여쓰기된 코드가 끝나면 파일을 자동으로 닫는다.

자동화 코드에서는 이 방식이 표준처럼 사용된다.

---

## 4. 파일 모드 이해

파일을 열 때 사용하는 대표적인 모드는 다음과 같다.

### `"r"`

읽기 모드이다.

파일이 반드시 존재해야 한다.

### `"w"`

쓰기 모드이다.

파일이 없으면 새로 만들고, 파일이 있으면 기존 내용을 덮어쓴다.

### `"a"`

추가 모드이다.

기존 파일의 끝에 내용을 이어서 쓴다.

---

## 5. 텍스트 파일 쓰기

다음 코드는 텍스트 파일을 만들고 내용을 저장한다.

```
with open("sample.txt", "w", encoding="utf-8") as file:
    file.write("hello python\n")
    file.write("cloud automation\n")
```

실행 후 `sample.txt` 파일을 열어 보면 아래 내용이 저장되어 있다.

```
hello python
cloud automation
```

여기서 `\n`은 줄바꿈 문자이다.

이 문자가 없으면 한 줄에 이어서 써진다.

---

## 실습 1. 텍스트 파일 생성하기

파일명: `write_text.py`

```
with open("services.txt", "w", encoding="utf-8") as file:
    file.write("EC2\n")
    file.write("S3\n")
    file.write("IAM\n")
    file.write("Bedrock\n")

print("services.txt 파일 저장 완료")
```

### 확인할 내용

* 실행 후 `services.txt` 파일이 생성되는지 확인한다.

* 파일 안에 줄 단위로 데이터가 저장되는지 확인한다.

---

## 6. 텍스트 파일 읽기

이제 저장한 파일을 다시 읽어보자.

```
with open("sample.txt", "r", encoding="utf-8") as file:
    content = file.read()

print(content)
```

실행 결과

```
hello python
cloud automation
```

`read()`는 파일 전체 내용을 한 번에 문자열로 읽어온다.

---

## 7. 줄 단위로 읽기

로그 파일이나 목록 파일은 줄 단위로 읽는 경우가 많다.

이때는 반복문을 사용한다.

```
with open("sample.txt", "r", encoding="utf-8") as file:
    for line in file:
        print(line)
```

그런데 이 방식은 줄 끝에 줄바꿈 문자가 남아 있고 print() 함수에 의해 빈 줄이 추가된다.

그래서 보통 `strip()`을 함께 사용한다.

`strip()`은 문자열 양쪽 끝의 공백 문자, 줄바꿈 문자 등을 제거한다.

```
with open("sample.txt", "r", encoding="utf-8") as file:
    for line in file:
        print(line.strip())
```

실행 결과

```
hello python
cloud automation
```

`strip()`은 문자열 앞뒤의 공백과 줄바꿈을 제거한다.

---

## 실습 2. 파일 읽기

파일명: `read_text.py`

```
with open("services.txt", "r", encoding="utf-8") as file:
    for line in file:
        print(f"service: {line.strip()}")
```

### 확인할 내용

* 파일 내용을 한 줄씩 읽는지 확인한다.

* `strip()`을 사용했을 때 출력 형식이 깔끔해지는지 확인한다.

---

## 8. 파일에 결과를 저장하는 이유

자동화 코드에서는 화면 출력도 중요하지만, 결과를 파일로 남기는 것이 더 중요할 때가 많다.

예를 들면 다음과 같은 경우가 있다.

* 인스턴스 조회 결과를 보관

* 에러 목록을 텍스트 파일로 저장

* 로그 분석 결과를 나중에 다시 열어봄

* 다른 사람이 결과를 확인할 수 있도록 파일로 공유

즉, 파일 저장은 자동화 결과를 **휘발되지 않게 남기는 작업**이라고 볼 수 있다.

---

## 9. 추가 모드로 이어쓰기

기존 파일 뒤에 내용을 더 추가하려면 `"a"` 모드를 사용한다.

```
with open("history.txt", "a", encoding="utf-8") as file:
    file.write("first record\n")
```

한 번 더 실행하면 같은 파일 뒤에 다시 이어서 기록된다.

```
with open("history.txt", "a", encoding="utf-8") as file:
    file.write("second record\n")
```

이 방식은 로그를 남길 때 자주 사용된다.

---

## 실습 3. 실행 결과 이어쓰기

파일명: `append_text.py`

```
from datetime import datetime

now = datetime.now()

with open("run_history.txt", "a", encoding="utf-8") as file:
    file.write(f"프로그램 실행 시간: {now}\n")

print("실행 시간이 run_history.txt에 기록되었습니다.")
```

### 확인할 내용

* 여러 번 실행했을 때 내용이 누적되는지 확인한다.

* `"w"` 모드와 `"a"` 모드 차이를 확인한다.

---

# 10. JSON이란 무엇인가

JSON(JavaScript Object Notation)은 데이터를 저장하거나 전송할 때 사용하는 **경량의 데이터 교환 형식**으로 한다. 원래 자바스크립트 언어에서 파생되었으나, 현재는 언어와 관계없이 거의 모든 프로그래밍 환경에서 표준적으로 사용된다.

주요 특징과 구조는 다음과 같다.

### 1. JSON의 핵심 특징

* **텍스트 기반**: 사람이 읽고 쓰기 쉽고, 기계가 분석하고 생성하기에도 용이하다.

* **독립성**: 특정 프로그래밍 언어에 종속되지 않아, 서로 다른 언어로 작성된 시스템 간에 데이터를 주고받을 때 유리하다.

* **가독성**: XML과 같은 다른 형식에 비해 구조가 단순하여 데이터의 양이 상대적으로 적고 명확하다.

### 2. JSON의 기본 구조

JSON은 기본적으로 이름(Key)과 값(Value)의 쌍으로 이루어져 있으며, 두 가지 주요 구조를 가진다.

* **객체(Object)**: 중괄호 `{ }`로 감싸며, `key: value` 형태의 집합으로 한다.

* **배열(Array)**: 대괄호 `[ ]`로 감싸며, 값들의 순서 있는 목록으로 한다.

### 3. 사용 가능한 데이터 타입

JSON 내에서는 다음과 같은 데이터 형식을 사용할 수 있다.

* **숫자(Number)**: 정수 또는 실수

* **문자열(String)**: 반드시 큰따옴표(`" "`)를 사용해야 함

* **불리언(Boolean)**: `true` 또는 `false`

* **배열(Array)**: `[ ]`

* **객체(Object)**: `{ }`

* **널(Null)**: 빈 값을 의미하는 `null`

### 4. 활용 사례

* **웹 API**: 서버와 클라이언트(브라우저, 모바일 앱) 간에 데이터를 주고받을 때 가장 많이 사용된다.

* **설정 파일**: 프로그램의 환경 설정(예: `package.json`, `tsconfig.json`)을 정의할 때 사용된다.

* **NoSQL 데이터베이스**: MongoDB와 같은 데이터베이스는 데이터를 JSON과 유사한 형태로 저장한다.

JSON은 텍스트 기반 형식이며, 사람도 읽을 수 있고 프로그램도 다루기 쉽다.

예를 들어 아래는 JSON 형태의 데이터이다.

```
{
  "name": "홍길동",
  "age": 30,
  "isStudent": false,
  "hobbies": ["독서", "코딩"],
  "address": {
    "city": "서울",
    "zipcode": "12345"
  }
}
```

```
{
  "region": "ap-northeast-2",
  "profile": "lab",
  "service": "ec2"
}
```

파이썬 딕셔너리와 매우 비슷하게 생겼다.

실제로 JSON과 파이썬 딕셔너리는 매우 밀접한 관계가 있다.

---

## 11. Python 딕셔너리와 JSON의 관계

파이썬에서는 보통 JSON 데이터를 딕셔너리 형태로 다룬다.

예를 들어 파이썬 딕셔너리는 아래와 같다.

```
config = {
    "region": "ap-northeast-2",
    "profile": "lab",
    "service": "ec2"
}
```

이 딕셔너리를 JSON 파일로 저장할 수 있다.

그리고 다시 파일에서 읽으면 다시 딕셔너리로 가져올 수 있다.

즉,

* Python 안에서는 딕셔너리

* 파일로 저장할 때는 JSON

이라는 흐름으로 이해하면 된다.

---

## 12. json 모듈 가져오기

JSON을 다루기 위해서는 `json` 모듈을 가져와야 한다.

```
import json
```

이 모듈은 Python 표준 모듈이므로 별도 설치 없이 바로 사용할 수 있다.

---

## 13. JSON 파일 저장: json.dump()

파이썬 딕셔너리를 JSON 파일로 저장할 때는 `json.dump()`를 사용한다.

```
import json

config = {
    "region": "ap-northeast-2",
    "profile": "lab",
    "service": "ec2"
}

with open("config.json", "w", encoding="utf-8") as file:
    json.dump(config, file, ensure_ascii=False, indent=2)
```

여기서 중요한 옵션은 다음과 같다.

### `ensure_ascii=False`

한글이 깨지지 않도록 한다.

### `indent=2`

들여쓰기를 적용해 사람이 읽기 좋게 만든다.

실행 후 `config.json` 파일 내용은 아래처럼 저장된다.

```
{
  "region": "ap-northeast-2",
  "profile": "lab",
  "service": "ec2"
}
```

---

## 실습 4. JSON 파일 저장

파일명: `write_json.py`

```
import json

check_result = {
    "server_name": "web-01",
    "ip_address": "192.168.10.21",
    "status": "running",
    "cpu_usage": 37.5,
    "memory_usage": 68.2,
    "disk_usage": 54.8
}

with open("server_check.json", "w", encoding="utf-8") as file:
    json.dump(check_result, file, ensure_ascii=False, indent=2)

print("server_check.json 저장 완료")
```

### 확인할 내용

* `config.json` 파일이 생성되는지 확인한다.

* 파일 내용을 직접 열어 들여쓰기 구조를 확인한다.

---

## 14. JSON 파일 읽기: json.load()

JSON 파일을 다시 읽어올 때는 `json.load()`를 사용한다.

```
import json

with open("config.json", "r", encoding="utf-8") as file:
    config = json.load(file)

print(config)
print(config["region"])
print(config["profile"])
print(config["service"])
```

실행 결과 예시

```
{'region': 'ap-northeast-2', 'profile': 'lab', 'service': 'ec2'}
ap-northeast-2
lab
ec2
```

즉, JSON 파일을 읽으면 Python 딕셔너리로 돌아온다.

---

## 실습 5. JSON 파일 읽기

파일명: `read_json.py`

```
import json

with open("config.json", "r", encoding="utf-8") as file:
    config = json.load(file)

print(f"region: {config['region']}")
print(f"profile: {config['profile']}")
print(f"service: {config['service']}")
```

### 확인할 내용

* JSON 파일을 읽은 뒤 딕셔너리처럼 값을 꺼낼 수 있는지 확인한다.

* 설정 파일을 코드와 분리하는 방식에 익숙해진다.

---

## 15. 리스트가 포함된 JSON 구조

JSON은 딕셔너리만 저장하는 것이 아니라 리스트도 포함할 수 있다.

```
import json

config_data = {
    "region": "ap-northeast-2",
    "profile": "lab",
    "services": ["ec2", "s3", "iam"]
}

with open("lab_config.json", "w", encoding="utf-8") as file:
    json.dump(config_data, file, ensure_ascii=False, indent=2)
```

이 파일은 다음처럼 읽을 수 있다.

```
import json

with open("lab_config.json", "r", encoding="utf-8") as file:
    config = json.load(file)

print(config["region"])
for service in config["services"]:
    print(service)
```

즉, JSON 안에서도 리스트와 딕셔너리 구조가 함께 등장할 수 있다.

---

## 실습 6. 리스트 포함 JSON 처리

파일명: `json_list_example.py`

```
import json

config_data = {
    "region": "ap-northeast-2",
    "profile": "lab",
    "services": ["ec2", "s3", "iam", "bedrock"]
}

with open("lab_config.json", "w", encoding="utf-8") as file:
    json.dump(config_data, file, ensure_ascii=False, indent=2)

with open("lab_config.json", "r", encoding="utf-8") as file:
    loaded_config = json.load(file)

print(f"region: {loaded_config['region']}")
print(f"profile: {loaded_config['profile']}")

for service in loaded_config["services"]:
    print(f"service: {service}")
```

### 확인할 내용

* JSON 파일 안에 리스트를 넣을 수 있는지 확인한다.

* 읽은 뒤 반복문으로 처리할 수 있는지 확인한다.

---

## 16. 자동화 코드에서 설정 파일을 따로 두는 이유

자동화 코드에서는 아래 값들이 자주 바뀐다.

* 리전

* 프로필 이름

* 서비스 이름

* 대상 파일 이름

* 출력 파일 이름

이런 값을 코드 안에 직접 써도 되지만, 설정 파일로 따로 빼두면 더 편리하다.

예를 들어 코드 안에서 직접 쓰는 경우는 다음과 같다.

```
region = "ap-northeast-2"
profile = "lab"
```

하지만 설정 파일을 사용하면 아래처럼 바꿀 수 있다.

```
import json

with open("config.json", "r", encoding="utf-8") as file:
    config = json.load(file)

region = config["region"]
profile = config["profile"]
```

이렇게 하면 나중에 지역이나 프로필을 바꾸고 싶을 때 코드가 아니라 설정 파일만 수정하면 된다.

---

## 17. 자동화 스타일 설정 파일 실습

파일명: `config_reader.py`

### 먼저 `data/config.json` 파일 생성

```
{
  "region": "ap-northeast-2",
  "profile": "lab",
  "service": "ec2",
  "output_file": "result.txt"
}
```

### Python 코드

```
import json

with open("data/config.json", "r", encoding="utf-8") as file:
    config = json.load(file)

print("설정 파일 읽기 완료")
print(f"region: {config['region']}")
print(f"profile: {config['profile']}")
print(f"service: {config['service']}")
print(f"output file: {config['output_file']}")
```

설정값을 JSON 파일로 분리해두면 코드가 더 깔끔해진다.

---

## 18. 결과를 파일로 저장하는 자동화 스타일 예제

이제 간단한 자동화 결과를 파일로 저장해보자.

파일명: `data/save_report.py`

```
instances = [
    {"Name": "web-1", "State": "running"},
    {"Name": "db-1", "State": "stopped"},
    {"Name": "app-1", "State": "running"}
]

with open("data/instance_report.txt", "w", encoding="utf-8") as file:
    for instance in instances:
        line = f"name={instance['Name']}, state={instance['State']}\n"
        file.write(line)

print("instance_report.txt 저장 완료")
```

실행 후 `instance_report.txt` 파일에는 아래처럼 저장된다.

```
name=web-1, state=running
name=db-1, state=stopped
name=app-1, state=running
```

이 구조는 자동화 결과 보고서를 만들 때 많이 사용된다.

---

## 19. 로그 파일 읽기 스타일 예제

다음은 간단한 로그 파일을 줄 단위로 읽는 예제이다.

먼저 `data/app.log` 파일 내용이 아래와 같다고 가정하자.

```
INFO service started
ERROR database connection failed
INFO retry started
ERROR timeout occurred
```

Python 코드:

```
with open("data/app.log", "r", encoding="utf-8") as file:
    for line in file:
        if "ERROR" in line:
            print(line.strip())
```

실행 결과

```
ERROR database connection failed
ERROR timeout occurred
```

이 구조는 이후 로그 분석 자동화 실습의 가장 기본이 된다.

#### - `read()` : 전체 내용을 한 번에 읽기

파일의 데이터 전부를 메모리에 한꺼번에 올리는 방식으로 한다.

* **특징**: 파일 내용이 하나의 긴 문자열(String)로 반환된다.

* **장점**: 파일 크기가 작을 때 처리가 매우 빠르고 간편하다.

* **단점**: 파일 크기가 수 GB(기가바이트) 단위로 클 경우, 컴퓨터의 RAM(메모리)이 부족하여 프로그램이 멈추거나 **Memory Error**가 발생할 수 있다.

#### - 줄 단위 읽기 (`readline()` 또는 `for` 루프) : 한 줄씩 읽기

파일을 한 줄씩 순차적으로 읽어 들이는 방식으로 한다.

* **특징**: 현재 읽고 있는 줄만 메모리에 머물고, 처리가 끝나면 다음 줄로 넘어간다.

* **장점**: 파일 크기가 아무리 커도 메모리를 거의 차지하지 않아 매우 안전하다. 대용량 로그 파일을 분석할 때 필수적인 방식이다.

* **단점**: 파일 전체를 대상으로 하는 작업(예: 전체 텍스트 교체) 시에는 코드가 조금 더 복잡해질 수 있다.

---

## 20. 정리

* `with open()`으로 파일을 안전하게 열고 닫을 수 있다.

* `"w"`는 쓰기, `"r"`은 읽기, `"a"`는 추가 모드이다.

* `read()`는 파일 전체를 읽고, 반복문은 줄 단위로 읽을 때 사용한다.

* `strip()`은 줄바꿈과 공백을 제거할 때 유용하다.

* JSON은 설정 파일과 결과 파일에 많이 사용된다.

* Python에서는 JSON을 주로 딕셔너리와 리스트 구조로 다룬다.

* `json.dump()`는 저장, `json.load()`는 읽기에 사용한다.

* 자동화 코드에서는 설정값을 JSON 파일로 분리하고, 결과를 텍스트나 JSON 파일로 저장하는 구조가 자주 사용된다.