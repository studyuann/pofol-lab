---
title: "실습과제 ec2_func 패키지를 이용한 EC2 운영 자동화 스크립트 작성"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "클라우드 자동화를 위한 파이썬 프로그래밍", "4장 운영 자동화 스크립트 작성 기법"]
is_public: true
draft: false
---

# 실습과제: `ec2_func` 패키지를 이용한 EC2 운영 자동화 스크립트 작성

## 1. 과제 개요

이전 실습에서 작성한 `ec2_func` 패키지를 이용해서 EC2 인스턴스 운영 상태를 점검하는 최종 자동화 스크립트를 작성한다.

이번 과제의 핵심은 **패키지 재사용**이다.

---

## 2. 과제 목표

다음 기능을 수행하는 실행 스크립트를 작성해야 한다.

```
1. 명령행 옵션으로 profile, region, state, output 값을 입력받는다.
2. ec2_func 패키지에서 필요한 함수를 import한다.
3. 입력받은 profile, region 기준으로 EC2 클라이언트를 생성한다.
4. EC2 인스턴스 목록을 조회한다.
5. 사용자가 지정한 상태값에 따라 인스턴스를 필터링한다.
6. 필터링된 인스턴스 목록을 터미널에 표 형태로 출력한다.
7. 필터링된 인스턴스 목록을 CSV 파일로 저장한다.
8. 운영 점검 시작/종료 메시지를 출력한다.
```

---

## 3. 제공된 패키지

이미 아래와 같은 `ec2_func` 패키지를 가지고 있다.

```
실습 디렉터리/
├── ec2_func.py
└── ec2_daily_check.py
```

새로 작성할 파일은 다음이다.

```
ec2_daily_check.py
```

---

## 4. 사용할 수 있는 `ec2_func` 함수

`ec2_func` 패키지에는 다음 함수들이 이미 작성되어 있다고 가정한다.

```
create_ec2_client(profile, region)
get_instances(ec2)
filter_instance_by_state(instances, state)
extract_instance_info(reservations)
print_instance_table(instances)
save_to_csv(data, filename)
```

각 함수의 역할은 다음과 같다.

| 함수명 | 역할 |
| --- | --- |
| `create_ec2_client(profile, region)` | AWS 프로파일과 리전을 기준으로 EC2 클라이언트를 생성 |
| `get_instances(ec2)` | EC2 인스턴스 목록을 조회하고 `Reservations` 반환 |
| `filter_instance_by_state(instances, state)` | 인스턴스 상태값 기준으로 필터링 |
| `extract_instance_info(reservations)` | EC2 인스턴스 정보 중 CSV 저장에 필요한 항목 추출 |
| `print_instance_table(instances)` | EC2 인스턴스 목록을 터미널 표 형태로 출력 |
| `save_to_csv(data, filename)` | 추출된 인스턴스 정보를 CSV 파일로 저장 |

---

# 5. 작성해야 할 내용

## 5.1 실행 스크립트 파일 생성

아래 파일을 새로 만든다.

```
ec2_daily_check.py
```

이 파일은 `ec2_func` 패키지를 가져와서 사용하는 최종 실행 파일이다.

---

## 5.2 `ec2_func` 패키지 import

`ec2_func.py`가 같은 디렉터리에 있다면 다음과 같이 import한다.

```
from ec2_func import (
    create_ec2_client,
    get_instances,
    filter_instance_by_state,
    extract_instance_info,
    print_instance_table,
    save_to_csv
)
```

패키지 폴더 구조라면 구조에 맞게 import 경로를 사용한다.

예시:

```
from ec2_func.ec2_ops import (
    create_ec2_client,
    get_instances,
    filter_instance_by_state,
    extract_instance_info,
    print_instance_table,
    save_to_csv
)
```

---

## 5.3 명령행 옵션 구현

`argparse`를 이용해 다음 옵션을 입력받는다.

| 옵션 | 설명 | 기본값 |
| --- | --- | --- |
| `--profile` | 사용할 AWS CLI 프로파일 이름 | `default` |
| `--region` | 조회할 AWS 리전 | `ap-northeast-2` |
| `--state` | 조회할 인스턴스 상태 | `all` |
| `--output` | CSV 저장 파일명 | `ec2-daily-report.csv` |

* `-state` 옵션은 다음 값만 허용한다.

```
all
pending
running
stopping
stopped
shutting-down
terminated
```

---

## 5.4 운영 자동화 흐름 구현

`ec2_daily_check.py`는 아래 순서로 실행되어야 한다.

```
1. 명령행 옵션을 읽는다.
2. 운영 점검 시작 메시지를 출력한다.
3. EC2 클라이언트를 생성한다.
4. EC2 인스턴스 목록을 조회한다.
5. Reservations 구조를 인스턴스 리스트로 변환한다.
6. 상태 조건에 따라 인스턴스를 필터링한다.
7. 필터링된 인스턴스 목록을 터미널에 출력한다.
8. 필터링된 인스턴스 목록을 CSV 저장용 데이터로 변환한다.
9. CSV 파일로 저장한다.
10. 운영 점검 종료 메시지를 출력한다.
```

---

# 6. 구현 조건

## 6.1 패키지 함수 재작성 금지

이번 과제에서는 아래 함수들을 새로 작성하지 않는다.

```
create_ec2_client()
get_instances()
filter_instance_by_state()
extract_instance_info()
print_instance_table()
save_to_csv()
```

위 함수들은 반드시 `ec2_func`에서 import해서 사용한다.

---

## 6.2 최종 스크립트에서 작성해도 되는 함수

`ec2_daily_check.py`에서는 실행 흐름 제어를 위한 함수만 작성한다.

예시:

```
parse_args()
flatten_reservations()
main()
```

`flatten_reservations()`는 `get_instances()`의 반환값인 `Reservations` 구조를 단순 인스턴스 리스트로 변환하기 위해 작성해도 된다.

---

## 6.3 `Reservations` 구조 처리

`get_instances(ec2)` 함수가 반환하는 값은 보통 다음 구조다.

```
[
    {
        "Instances": [
            {
                "InstanceId": "i-0123456789abcdef0",
                "InstanceType": "t3.micro",
                "State": {
                    "Name": "running"
                }
            }
        ]
    }
]
```

하지만 `filter_instance_by_state()`와 `print_instance_table()`은 일반적으로 인스턴스 딕셔너리 리스트를 대상으로 동작한다.

따라서 최종 실행 스크립트에서는 다음처럼 구조를 변환해야 한다.

```
Reservations
    ↓
Instances 리스트
```

예시:

```
instances = flatten_reservations(reservations)
```

---

# 7. 실행 예시와 출력 예시

## 예시 1. 전체 인스턴스 조회

실행 명령:

```
python ec2_daily_check.py \
  --profile default \
  --region ap-northeast-2 \
  --state all \
  --output ec2-daily-report.csv
```

출력 예시:

```
[INFO] EC2 운영 점검을 시작함
[INFO] profile=default, region=ap-northeast-2, state=all
[INFO] EC2 인스턴스 조회 완료

NAME                InstanceId            InstanceType State       PrivateIp       PublicIp
----------------------------------------------------------------------------------------------------
web-server          i-0123456789abcdef0    t3.micro     running     10.0.1.10       3.35.100.10
db-server           i-0abcdef1234567890    t3.small     stopped     10.0.2.20       -
batch-server        i-0a1b2c3d4e5f67890    t3.micro     running     10.0.3.15       -

CSV 파일 저장 완료: ec2-daily-report.csv
[INFO] EC2 운영 점검 종료
```

---

## 예시 2. 실행 중인 인스턴스만 조회

실행 명령:

```
python ec2_daily_check.py \
  --profile default \
  --region ap-northeast-2 \
  --state running \
  --output running-report.csv
```

출력 예시:

```
[INFO] EC2 운영 점검을 시작함
[INFO] profile=default, region=ap-northeast-2, state=running
[INFO] EC2 인스턴스 조회 완료

NAME                InstanceId            InstanceType State       PrivateIp       PublicIp
----------------------------------------------------------------------------------------------------
web-server          i-0123456789abcdef0    t3.micro     running     10.0.1.10       3.35.100.10
batch-server        i-0a1b2c3d4e5f67890    t3.micro     running     10.0.3.15       -

CSV 파일 저장 완료: running-report.csv
[INFO] EC2 운영 점검 종료
```

---

## 예시 3. 중지된 인스턴스만 조회

실행 명령:

```
python ec2_daily_check.py \
  --profile default \
  --region ap-northeast-2 \
  --state stopped \
  --output stopped-report.csv
```

출력 예시:

```
[INFO] EC2 운영 점검을 시작함
[INFO] profile=default, region=ap-northeast-2, state=stopped
[INFO] EC2 인스턴스 조회 완료

NAME                InstanceId            InstanceType State       PrivateIp       PublicIp
----------------------------------------------------------------------------------------------------
db-server           i-0abcdef1234567890    t3.small     stopped     10.0.2.20       -

CSV 파일 저장 완료: stopped-report.csv
[INFO] EC2 운영 점검 종료
```

---

## 예시 4. 조회 결과가 없는 경우

실행 명령:

```
python ec2_daily_check.py \
  --profile default \
  --region ap-northeast-2 \
  --state terminated \
  --output terminated-report.csv
```

출력 예시:

```
[INFO] EC2 운영 점검을 시작함
[INFO] profile=default, region=ap-northeast-2, state=terminated
[INFO] EC2 인스턴스 조회 완료

조회된 인스턴스가 없음
저장할 데이터가 없음
[INFO] EC2 운영 점검 종료
```

---

## 예시 5. 잘못된 상태값 입력

실행 명령:

```
python ec2_daily_check.py --state start
```

출력 예시:

```
usage: ec2_daily_check.py [-h] [--profile PROFILE] [--region REGION]
                          [--state {all,pending,running,stopping,stopped,shutting-down,terminated}]
                          [--output OUTPUT]

ec2_daily_check.py: error: argument --state: invalid choice: 'start'
```

---

# 8. 제출

각 실행 예시 캡처후 업로드

---