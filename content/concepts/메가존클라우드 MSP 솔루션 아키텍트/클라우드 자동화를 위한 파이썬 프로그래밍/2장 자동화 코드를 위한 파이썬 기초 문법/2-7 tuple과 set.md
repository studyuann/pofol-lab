---
title: "2-7 tuple과 set"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "클라우드 자동화를 위한 파이썬 프로그래밍", "2장 자동화 코드를 위한 파이썬 기초 문법"]
is_public: true
draft: false
---

# 2-7. tuple과 set

## 1. 학습 목표

`tuple`은 여러 값을 하나로 묶는 자료형이라는 점에서 `list`와 비슷하지만, 한 번 생성한 뒤 내부 값을 변경할 수 없다는 특징이 있다.

`set`은 여러 값을 저장할 수 있지만, 중복을 허용하지 않고 순서를 보장하지 않는 자료형이다.

클라우드 자동화 코드에서는 `dict`와 `list`를 가장 많이 사용하지만, `tuple`과 `set`도 자주 등장한다. 특히 함수 반환값, 반복문 언패킹, 중복 제거, 리소스 목록 비교에서 많이 사용된다.

---

# 2. tuple 자료형 이해

## 2.1 tuple이란?

`tuple`은 여러 개의 값을 하나로 묶어서 저장하는 자료형이다.

```
server= ("web-01","10.0.1.10","running")

print(server)
print(type(server))
```

실행 결과:

```
('web-01', '10.0.1.10', 'running')
<class 'tuple'>
```

위 코드에서 `server` 변수에는 세 개의 값이 들어 있다.

```
서버 이름: web-01
IP 주소: 10.0.1.10
상태: running
```

이처럼 여러 값을 하나로 묶을 때 tuple을 사용할 수 있다.

---

## 2.2 tuple 생성 방법

tuple은 소괄호 `()`를 사용해서 만든다.

```
numbers= (10,20,30)
print(numbers)
```

실행 결과:

```
(10, 20, 30)
```

문자열도 tuple에 저장할 수 있다.

```
regions= ("ap-northeast-2","us-east-1","us-west-2")

print(regions)
```

실행 결과:

```
('ap-northeast-2', 'us-east-1', 'us-west-2')
```

서로 다른 자료형도 함께 저장할 수 있다.

```
instance= ("i-0123456789abcdef0","running",2,True)

print(instance)
```

실행 결과:

```
('i-0123456789abcdef0', 'running', 2, True)
```

이 tuple은 다음과 같은 의미를 가진다고 볼 수 있다.

```
인스턴스 ID
상태
vCPU 개수
사용 가능 여부
```

---

## 2.3 tuple은 괄호 없이도 만들 수 있음

Python에서는 쉼표 `,`를 사용하면 괄호 없이도 tuple을 만들 수 있다.

```
server="web-01","10.0.1.10","running"

print(server)
print(type(server))
```

실행 결과:

```
('web-01', '10.0.1.10', 'running')
<class 'tuple'>
```

즉, tuple을 만드는 핵심은 소괄호가 아니라 **쉼표**다.

하지만 가독성을 위해 소괄호를 사용하는 것이 좋다.

```
server= ("web-01","10.0.1.10","running")
```

이 방식이 tuple이라는 사실을 더 쉽게 알 수 있다.

---

## 2.4 요소가 하나인 tuple 만들기

요소가 하나만 있는 tuple을 만들 때는 주의가 필요하다.

```
region= ("ap-northeast-2")

print(region)
print(type(region))
```

실행 결과:

```
ap-northeast-2
<class 'str'>
```

위 코드는 tuple이 아니다. 문자열을 소괄호로 감싼 것뿐이다.

요소가 하나인 tuple을 만들려면 반드시 쉼표를 붙여야 한다.

```
region= ("ap-northeast-2",)

print(region)
print(type(region))
```

실행 결과:

```
('ap-northeast-2',)
<class 'tuple'>
```

정리하면 다음과 같다.

```
value1= ("ap-northeast-2")
value2= ("ap-northeast-2",)

print(type(value1))
print(type(value2))
```

실행 결과:

```
<class 'str'>
<class 'tuple'>
```

---

# 3. tuple과 list 비교

## 3.1 list는 변경 가능함

`list`는 값을 추가하거나 수정하거나 삭제할 수 있다.

```
servers= ["web-01","web-02","db-01"]

servers[0]="web-main"

print(servers)
```

실행 결과:

```
['web-main', 'web-02', 'db-01']
```

`servers[0]`의 값이 `"web-01"`에서 `"web-main"`으로 변경됐다.

---

## 3.2 tuple은 변경할 수 없음

반면 tuple은 한 번 생성한 뒤 값을 수정할 수 없다.

```
server= ("web-01","10.0.1.10","running")

server[0]="web-main"
```

실행 결과:

```
TypeError: 'tuple' object does not support item assignment
```

tuple은 내부 값을 직접 바꿀 수 없다.

이런 특성을 **불변성**, 영어로는 **immutable**이라고 한다.

---

## 3.3 list와 tuple의 차이 정리

| 구분 | list | tuple |
| --- | --- | --- |
| 표기 | `[ ]` | `( )` |
| 값 변경 | 가능 | 불가능 |
| 요소 추가 | 가능 | 불가능 |
| 요소 삭제 | 가능 | 불가능 |
| 사용 목적 | 변하는 목록 관리 | 고정된 값 묶음 |
| 예시 | 서버 목록, 사용자 목록 | 좌표, 리전/ID 묶음, 함수 반환값 |

---

## 3.4 언제 tuple을 사용하는가?

tuple은 다음과 같은 상황에서 사용하기 좋다.

```
1. 값의 개수가 고정되어 있을 때
2. 값의 의미가 순서로 정해져 있을 때
3. 실행 중 변경되면 안 되는 값을 표현할 때
4. 함수에서 여러 값을 반환할 때
5. 딕셔너리의 key로 사용해야 할 때
```

예를 들어 인스턴스 하나의 요약 정보를 다음처럼 표현할 수 있다.

```
instance= ("i-aaa111","ap-northeast-2","running")
```

이 tuple은 다음 순서로 값이 들어 있다고 약속할 수 있다.

```
0번: 인스턴스 ID
1번: 리전
2번: 상태
```

하지만 값의 의미가 많아지면 tuple보다는 `dict`가 더 명확하다.

```
instance= {
"instance_id":"i-aaa111",
"region":"ap-northeast-2",
"state":"running"
}
```

클라우드 자동화 실무에서는 복잡한 리소스 정보에는 `dict`를 많이 사용하고, 간단한 고정 값 묶음에는 `tuple`을 사용한다.

---

# 4. tuple 인덱싱과 슬라이싱

## 4.1 인덱싱

tuple도 list처럼 인덱스를 사용해서 값을 꺼낼 수 있다.

```
server= ("web-01","10.0.1.10","running")

print(server[0])
print(server[1])
print(server[2])
```

실행 결과:

```
web-01
10.0.1.10
running
```

인덱스는 0부터 시작한다.

```
server[0] -> web-01
server[1] -> 10.0.1.10
server[2] -> running
```

---

## 4.2 음수 인덱스

음수 인덱스를 사용하면 뒤에서부터 값을 가져올 수 있다.

```
server= ("web-01","10.0.1.10","running")

print(server[-1])
print(server[-2])
```

실행 결과:

```
running
10.0.1.10
```

`server[-1]`은 마지막 요소를 의미한다.

---

## 4.3 슬라이싱

tuple도 범위를 지정해서 일부 값만 가져올 수 있다.

```
regions= ("ap-northeast-2","us-east-1","us-west-2","eu-west-1")

print(regions[0:2])
print(regions[1:3])
print(regions[:2])
print(regions[2:])
```

실행 결과:

```
('ap-northeast-2', 'us-east-1')
('us-east-1', 'us-west-2')
('ap-northeast-2', 'us-east-1')
('us-west-2', 'eu-west-1')
```

슬라이싱 결과도 tuple이다.

---

# 5. tuple 언패킹

## 5.1 언패킹이란?

언패킹은 tuple 안에 들어 있는 값을 각각의 변수로 나누어 담는 문법이다.

```
server= ("web-01","10.0.1.10","running")

name,ip,state=server

print(name)
print(ip)
print(state)
```

실행 결과:

```
web-01
10.0.1.10
running
```

`server` tuple 안에는 값이 3개 들어 있다.

왼쪽에도 변수 3개를 준비하면 각 값이 순서대로 대입된다.

```
name  <- web-01
ip    <- 10.0.1.10
state <- running
```

---

## 5.2 변수 개수가 맞지 않으면 오류 발생

tuple 안의 값 개수와 변수 개수가 다르면 오류가 발생한다.

```
server= ("web-01","10.0.1.10","running")

name,ip=server
```

실행 결과:

```
ValueError: too many values to unpack (expected 2)
```

값은 3개인데 받을 변수는 2개뿐이기 때문에 오류가 발생한다.

반대로 변수 개수가 더 많아도 오류가 발생한다.

```
server= ("web-01","10.0.1.10")

name,ip,state=server
```

실행 결과:

```
ValueError: not enough values to unpack (expected 3, got 2)
```

---

## 5.3 반복문에서 tuple 언패킹 사용

리스트 안에 tuple이 여러 개 들어 있는 구조를 보자.

```
servers= [
    ("web-01","10.0.1.10","running"),
    ("web-02","10.0.1.11","stopped"),
    ("db-01","10.0.2.10","running")
]
```

이 구조는 다음과 같이 이해할 수 있다.

```
전체 서버 목록: list
서버 하나의 정보: tuple
```

반복문에서 tuple 언패킹을 사용할 수 있다.

```
for name,ip,state in servers:
	print(name,ip,state)
```

실행 결과:

```
web-01 10.0.1.10 running
web-02 10.0.1.11 stopped
db-01 10.0.2.10 running
```

각 반복마다 tuple 하나가 꺼내지고, 그 tuple 안의 값이 `name`, `ip`, `state` 변수로 나뉘어 들어간다.

---

## 5.4 클라우드 자동화 예제: running 서버만 출력

```
servers= [
    ("web-01","10.0.1.10","running"),
    ("web-02","10.0.1.11","stopped"),
    ("db-01","10.0.2.10","running"),
    ("batch-01","10.0.3.10","terminated")
]

for name,ip,state in servers:
		if state == "running":
				print(f"{name} 서버는 실행 중입니다. IP 주소:{ip}")
```

실행 결과:

```
web-01 서버는 실행 중입니다. IP 주소: 10.0.1.10
db-01 서버는 실행 중입니다. IP 주소: 10.0.2.10
```

이 예제는 실제 클라우드 API를 호출하지는 않지만, 클라우드 리소스 목록을 처리하는 기본 구조와 유사하다.

---

# 6. 함수 반환값과 tuple

## 6.1 함수에서 여러 값 반환하기

Python 함수는 여러 값을 반환할 수 있다.

```
def get_server_info():
    # 함수 내부이므로 들여쓰기를 해야 함
    name = "web-01"
    ip = "10.0.1.10"
    state = "running"
    
    # 여러 값을 반환하면 튜플로 묶임
    return name, ip, state

# 함수 호출
result = get_server_info()

print(result)        # ('web-01', '10.0.1.10', 'running') 출력
print(type(result))  # <class 'tuple'> 출력
```

실행 결과:

```
('web-01', '10.0.1.10', 'running')
<class 'tuple'>
```

`return name, ip, state`는 실제로 tuple을 반환한다.

---

## 6.2 반환값 바로 언패킹하기

함수의 반환값을 바로 여러 변수에 나누어 받을 수 있다.

```
def get_server_info():
	name="web-01"
	ip="10.0.1.10"
	state="running"

	return name,ip,state

name,ip,state=get_server_info()

print(name)
print(ip)
print(state)
```

실행 결과:

```
web-01
10.0.1.10
running
```

자동화 코드에서 이런 패턴은 많이 사용된다.

```
project_id,region,zone=load_config()
instance_id,state=check_instance()
bucket_name,object_count=get_bucket_summary()
```

---

## 6.3 실습 예제: 서버 상태 점검 함수

```
def check_server(server_name):
    if server_name == "web-01":
        return server_name, "running"
    elif server_name == "web-02":
        return server_name, "stopped"
    else:
        return server_name, "unknown"

name, state = check_server("web-01")

print(f"서버 이름: {name}")
print(f"서버 상태: {state}")
```

실행 결과:

```
서버 이름: web-01
서버 상태: running
```

함수는 서버 이름과 상태를 함께 반환한다.

반환된 두 값은 tuple 형태이며, `name`, `state` 변수로 언패킹된다.

---

# 7. tuple을 딕셔너리 key로 사용하기

## 7.1 tuple은 dict key로 사용할 수 있음

딕셔너리의 key는 변경 불가능한 값이어야 한다.

tuple은 변경 불가능한 자료형이므로 딕셔너리 key로 사용할 수 있다.

```
instance_status= {
    ("ap-northeast-2","i-aaa111"):"running",
    ("ap-northeast-2","i-bbb222"):"stopped",
    ("us-east-1","i-ccc333"):"running"
}

print(instance_status[("ap-northeast-2","i-aaa111")])
```

실행 결과:

```
running
```

여기서 key는 리전과 인스턴스 ID를 묶은 tuple이다.

```
("ap-northeast-2","i-aaa111")
```

이 key는 다음 의미를 가진다.

```
ap-northeast-2 리전의 i-aaa111 인스턴스
```

---

## 7.2 list는 dict key로 사용할 수 없음

반면 list는 변경 가능한 자료형이므로 dict key로 사용할 수 없다.

```
instance_status= {
    ["ap-northeast-2","i-aaa111"]:"running"
}
```

실행 결과:

```
TypeError: unhashable type: 'list'
```

딕셔너리 key로 사용하려면 값이 변하지 않아야 한다.

list는 내부 값이 바뀔 수 있기 때문에 key로 사용할 수 없다.

---

# 8. tuple 주요 함수와 연산

## 8.1 len()

tuple의 요소 개수를 확인할 수 있다.

```
regions= ("ap-northeast-2","us-east-1","us-west-2")

print(len(regions))
```

실행 결과:

```
3
```

---

## 8.2 in 연산자

tuple 안에 특정 값이 있는지 확인할 수 있다.

```
regions= ("ap-northeast-2","us-east-1","us-west-2")

print("ap-northeast-2"inregions)
print("eu-west-1"inregions)
```

실행 결과:

```
True
False
```

---

## 8.3 count()

특정 값이 몇 번 등장하는지 확인한다.

```
states= ("running","stopped","running","terminated")

print(states.count("running"))
```

실행 결과:

```
2
```

---

## 8.4 index()

특정 값의 위치를 확인한다.

```
regions= ("ap-northeast-2","us-east-1","us-west-2")

print(regions.index("us-east-1"))
```

실행 결과:

```
1
```

`"us-east-1"`은 1번 인덱스에 있다.

---

# 9. set 자료형 이해

## 9.1 set이란?

`set`은 여러 값을 저장하는 자료형이다.

하지만 list나 tuple과 다르게 다음 특징이 있다.

```
1. 중복을 허용하지 않는다.
2. 순서를 보장하지 않는다.
3. 집합 연산을 사용할 수 있다.
```

set은 중괄호 `{}`를 사용해서 만든다.

```
regions= {"ap-northeast-2","us-east-1","us-west-2"}

print(regions)
print(type(regions))
```

실행 결과 예시:

```
{'us-west-2', 'ap-northeast-2', 'us-east-1'}
<class 'set'>
```

출력 순서는 작성한 순서와 다를 수 있다.

set은 순서가 중요한 자료형이 아니기 때문이다.

---

## 9.2 set은 중복을 제거함

set은 같은 값을 여러 번 넣어도 하나만 저장한다.

```
states= {"running","stopped","running","terminated","stopped"}

print(states)
```

실행 결과 예시:

```
{'terminated', 'running', 'stopped'}
```

`running`과 `stopped`가 여러 번 들어갔지만 결과에는 한 번씩만 남는다.

---

## 9.3 빈 set 만들기

빈 set을 만들 때는 `{}`를 사용하면 안 된다.

```
empty_value= {}

print(type(empty_value))
```

실행 결과:

```
<class 'dict'>
```

`{}`는 빈 딕셔너리다.

빈 set은 `set()`으로 만든다.

```
empty_set=set()

print(type(empty_set))
```

실행 결과:

```
<class 'set'>
```

---

# 10. set과 list 비교

## 10.1 list는 중복을 허용함

```
regions= ["ap-northeast-2","us-east-1","ap-northeast-2"]

print(regions)
```

실행 결과:

```
['ap-northeast-2', 'us-east-1', 'ap-northeast-2']
```

list는 같은 값이 여러 번 들어갈 수 있다.

---

## 10.2 set은 중복을 허용하지 않음

```
regions= {"ap-northeast-2","us-east-1","ap-northeast-2"}

print(regions)
```

실행 결과 예시:

```
{'us-east-1', 'ap-northeast-2'}
```

중복된 `"ap-northeast-2"`는 하나만 남는다.

---

## 10.3 list와 set의 차이 정리

| 구분 | list | set |
| --- | --- | --- |
| 표기 | `[ ]` | `{ }` |
| 중복 | 허용 | 허용하지 않음 |
| 순서 | 유지 | 보장하지 않음 |
| 인덱싱 | 가능 | 불가능 |
| 주요 용도 | 순서 있는 목록 | 중복 제거, 포함 여부 확인, 집합 비교 |
| 예시 | 서버 목록 출력 | 리전 중복 제거, 누락 리소스 비교 |

---

# 11. set 인덱싱 불가

set은 순서를 보장하지 않기 때문에 인덱스로 접근할 수 없다.

```
regions= {"ap-northeast-2","us-east-1","us-west-2"}

print(regions[0])
```

실행 결과:

```
TypeError: 'set' object is not subscriptable
```

list나 tuple은 순서가 있기 때문에 `regions[0]`처럼 접근할 수 있다.

하지만 set은 순서가 없으므로 0번, 1번 같은 개념이 없다.

---

# 12. set에 값 추가하기

## 12.1 add()

set에 값을 하나 추가할 때는 `add()`를 사용한다.

```
regions = {"ap-northeast-2", "us-east-1"}

regions.add("us-west-2")

print(regions)
```

실행 결과 예시:

```
{'ap-northeast-2', 'us-west-2', 'us-east-1'}
```

이미 있는 값을 추가해도 중복 저장되지 않는다.

```
regions= {"ap-northeast-2","us-east-1"}

regions.add("ap-northeast-2")

print(regions)
```

실행 결과 예시:

```
{'ap-northeast-2', 'us-east-1'}
```

---

## 12.2 update()

여러 값을 한 번에 추가할 때는 `update()`를 사용한다.

```
regions= {"ap-northeast-2"}

regions.update(["us-east-1","us-west-2","ap-northeast-2"])

print(regions)
```

실행 결과 예시:

```
{'us-east-1', 'us-west-2', 'ap-northeast-2'}
```

`update()`에는 list, tuple, set 같은 반복 가능한 객체를 전달할 수 있다.

---

# 13. set에서 값 삭제하기

## 13.1 remove()

`remove()`는 set에서 특정 값을 삭제한다.

```
regions= {"ap-northeast-2","us-east-1","us-west-2"}

regions.remove("us-east-1")

print(regions)
```

실행 결과 예시:

```
{'ap-northeast-2', 'us-west-2'}
```

하지만 존재하지 않는 값을 삭제하려고 하면 오류가 발생한다.

```
regions= {"ap-northeast-2","us-east-1"}

regions.remove("eu-west-1")
```

실행 결과:

```
KeyError: 'eu-west-1'
```

---

## 13.2 discard()

`discard()`도 값을 삭제한다.

하지만 값이 없어도 오류가 발생하지 않는다.

```
regions= {"ap-northeast-2","us-east-1"}

regions.discard("eu-west-1")

print(regions)
```

실행 결과 예시:

```
{'ap-northeast-2', 'us-east-1'}
```

자동화 코드에서는 오류를 피하기 위해 `discard()`를 사용하는 경우가 있다.

# 14. set을 이용한 중복 제거

## 14.1 list의 중복 제거

클라우드 자동화에서 리소스 목록을 수집하다 보면 같은 값이 여러 번 들어오는 경우가 있다.

```
regions= [
"ap-northeast-2",
"us-east-1",
"ap-northeast-2",
"us-west-2",
"us-east-1"
]

unique_regions=set(regions)

print(unique_regions)
```

실행 결과 예시:

```
{'us-west-2', 'ap-northeast-2', 'us-east-1'}
```

set으로 변환하면 중복이 제거된다.

---

## 14.2 다시 list로 변환하기

set은 순서를 보장하지 않는다.

중복을 제거한 뒤 다시 list로 바꿀 수 있다.

```
regions= [
"ap-northeast-2",
"us-east-1",
"ap-northeast-2",
"us-west-2",
"us-east-1"
]

unique_regions=list(set(regions))

print(unique_regions)
```

실행 결과 예시:

```
['us-west-2', 'ap-northeast-2', 'us-east-1']
```

다만 순서가 원래 list와 다를 수 있다.

---

## 14.3 순서를 유지하면서 중복 제거하기

Python 3.7 이상에서는 dict가 입력 순서를 유지한다.

이를 이용하면 순서를 유지하면서 중복을 제거할 수 있다.

```
regions= [
"ap-northeast-2",
"us-east-1",
"ap-northeast-2",
"us-west-2",
"us-east-1"
]

unique_regions=list(dict.fromkeys(regions))

print(unique_regions)
```

실행 결과:

```
['ap-northeast-2', 'us-east-1', 'us-west-2']
```

이 방식은 원래 등장한 순서를 유지하면서 중복을 제거한다.

---

# 15. set 집합 연산

set의 가장 중요한 장점은 집합 연산이다.

클라우드 자동화에서는 다음과 같은 상황에서 집합 연산이 유용하다.

```
1. 현재 존재하는 리소스와 필요한 리소스를 비교할 때
2. 누락된 보안 그룹 규칙을 찾을 때
3. 중복된 태그 값을 제거할 때
4. 서로 다른 계정의 리소스 차이를 비교할 때
5. 배포 전후 리소스 목록을 비교할 때
```

---

## 15.1 합집합

합집합은 두 set의 모든 값을 합친다.

중복 값은 하나만 남는다.

```
aws_regions= {"ap-northeast-2","us-east-1"}
gcp_regions= {"asia-northeast3","us-east1","us-east-1"}

all_regions=aws_regions|gcp_regions

print(all_regions)
```

실행 결과 예시:

```
{'us-east-1', 'asia-northeast3', 'ap-northeast-2', 'us-east1'}
```

`|` 연산자는 합집합을 의미한다.

메서드로도 작성할 수 있다.

```
all_regions=aws_regions.union(gcp_regions)

print(all_regions)
```

---

## 15.2 교집합

교집합은 두 set에 모두 존재하는 값만 구한다.

```
required_ports= {22,80,443}
open_ports= {80,443,3306}

common_ports=required_ports&open_ports

print(common_ports)
```

실행 결과:

```
{80, 443}
```

`22`는 `required_ports`에는 있지만 `open_ports`에는 없다.

`3306`은 `open_ports`에는 있지만 `required_ports`에는 없다.

두 set에 모두 있는 값은 `80`, `443`이다.

메서드로는 다음과 같이 작성한다.

```
common_ports=required_ports.intersection(open_ports)
```

---

## 15.3 차집합

차집합은 한 set에는 있지만 다른 set에는 없는 값을 구한다.

```
required_ports= {22,80,443}
open_ports= {80,443}

missing_ports=required_ports-open_ports

print(missing_ports)
```

실행 결과:

```
{22}
```

필요한 포트는 `{22, 80, 443}`인데 현재 열린 포트는 `{80, 443}`이다.

따라서 누락된 포트는 `{22}`다.

메서드로는 다음과 같이 작성한다.

```
missing_ports=required_ports.difference(open_ports)
```

---

## 15.4 대칭 차집합

대칭 차집합은 양쪽 set에서 서로 다른 값만 구한다.

즉, 공통으로 존재하는 값은 제외한다.

```
before= {"web-01","web-02","db-01"}
after= {"web-01","db-01","batch-01"}

changed=before^after

print(changed)
```

실행 결과:

```
{'web-02', 'batch-01'}
```

`web-01`과 `db-01`은 양쪽 모두에 있으므로 제외된다.

`web-02`는 이전에는 있었지만 이후에는 없다.

`batch-01`은 이전에는 없었지만 이후에 생겼다.

이 연산은 배포 전후의 리소스 차이를 빠르게 확인할 때 유용하다.

메서드로는 다음과 같이 작성한다.

```
changed=before.symmetric_difference(after)
```

---

## 15.5 집합 연산 정리

| 연산 | 기호 | 메서드 | 의미 |
| --- | --- | --- | --- |
| 합집합 | `A | B` | `A.union(B)` |
| 교집합 | `A & B` | `A.intersection(B)` | A와 B에 모두 있는 값 |
| 차집합 | `A - B` | `A.difference(B)` | A에는 있고 B에는 없는 값 |
| 대칭 차집합 | `A ^ B` | `A.symmetric_difference(B)` | A와 B에서 서로 다른 값 |

---

# 16. 클라우드 자동화 예제 1: 필요한 포트와 열린 포트 비교

## 16.1 문제 상황

웹 서버는 다음 포트가 필요하다고 가정한다.

```
22번: SSH 접속
80번: HTTP
443번: HTTPS
```

그런데 현재 보안 그룹에서 열린 포트가 다음과 같다고 가정한다.

```
80번
443번
```

이때 누락된 포트를 찾아야 한다.

---

## 16.2 코드

```
required_ports= {22,80,443}
current_open_ports= {80,443}

missing_ports=required_ports-current_open_ports

print("필요한 포트:",required_ports)
print("현재 열린 포트:",current_open_ports)
print("누락된 포트:",missing_ports)
```

실행 결과:

```
필요한 포트: {80, 443, 22}
현재 열린 포트: {80, 443}
누락된 포트: {22}
```

---

## 16.3 설명

```
missing_ports=required_ports-current_open_ports
```

이 코드는 필요한 포트 중에서 현재 열려 있지 않은 포트를 찾는다.

```
required_ports       -> 있어야 하는 포트
current_open_ports   -> 현재 설정된 포트
missing_ports        -> 추가해야 하는 포트
```

이런 방식은 실제 보안 그룹, 방화벽 규칙, 네트워크 ACL 점검 로직을 만들 때 사용할 수 있다.

---

# 17. 클라우드 자동화 예제 2: 현재 서버와 목표 서버 비교

## 17.1 문제 상황

현재 클라우드에 존재하는 서버 목록이 있다.

```
current_servers= {"web-01","web-02","db-01"}
```

목표 상태로 유지해야 하는 서버 목록이 있다.

```
desired_servers= {"web-01","db-01","batch-01"}
```

이때 다음을 구해야 한다.

```
1. 새로 생성해야 할 서버
2. 삭제 검토해야 할 서버
3. 유지되는 서버
```

---

## 17.2 코드

```
current_servers= {"web-01","web-02","db-01"}
desired_servers= {"web-01","db-01","batch-01"}

to_create=desired_servers-current_servers
to_delete=current_servers-desired_servers
unchanged=current_servers&desired_servers

print("생성해야 할 서버:",to_create)
print("삭제 검토 서버:",to_delete)
print("유지되는 서버:",unchanged)
```

실행 결과:

```
생성해야 할 서버: {'batch-01'}
삭제 검토 서버: {'web-02'}
유지되는 서버: {'web-01', 'db-01'}
```

---

## 17.3 설명

```
to_create=desired_servers-current_servers
```

목표 상태에는 있지만 현재는 없는 서버를 찾는다.

따라서 새로 생성해야 할 서버다.

```
to_delete=current_servers-desired_servers
```

현재는 있지만 목표 상태에는 없는 서버를 찾는다.

따라서 삭제하거나 정리할 후보가 된다.

```
unchanged=current_servers&desired_servers
```

현재 상태와 목표 상태에 모두 있는 서버를 찾는다.

따라서 유지되는 서버다.

이런 비교 방식은 IaC, 배포 자동화, 인벤토리 점검에서 자주 사용된다.

---

# 18. 클라우드 자동화 예제 3: 태그 키 누락 검사

## 18.1 문제 상황

클라우드 리소스에는 관리 목적의 태그가 필요하다.

필수 태그는 다음과 같다.

```
Name
Environment
Owner
CostCenter
```

어떤 인스턴스에 실제 설정된 태그는 다음과 같다고 가정한다.

```
Name
Environment
Owner
```

이 경우 `CostCenter` 태그가 누락되어 있다.

---

## 18.2 코드

```
required_tags = {"Name", "Environment", "Owner", "CostCenter"}
current_tags = {"Name", "Environment", "Owner"}

missing_tags = required_tags - current_tags

if missing_tags:
    print("누락된 태그가 있습니다.")
    print("누락 태그:", missing_tags)
else:
    print("필수 태그가 모두 설정되어 있습니다.")
```

실행 결과:

```
누락된 태그가 있습니다.
누락 태그: {'CostCenter'}
```

---

## 18.3 설명

```
ifmissing_tags:
```

set에 값이 하나라도 있으면 `True`로 처리된다.

set이 비어 있으면 `False`로 처리된다.

즉, 누락된 태그가 있으면 경고 메시지를 출력하고, 없으면 정상 메시지를 출력한다.

---

# 19. tuple과 set을 함께 사용하는 예제

## 19.1 문제 상황

여러 리전에 있는 인스턴스 목록이 있다.

각 인스턴스는 `(region, instance_id)` tuple로 표현한다.

```
current_instances= {
    ("ap-northeast-2","i-aaa111"),
    ("ap-northeast-2","i-bbb222"),
    ("us-east-1","i-ccc333")
}
```

목표 인스턴스 목록은 다음과 같다.

```
desired_instances= {
    ("ap-northeast-2","i-aaa111"),
    ("us-east-1","i-ccc333"),
    ("us-west-2","i-ddd444")
}
```

이때 생성해야 하는 인스턴스와 삭제 검토 인스턴스를 찾는다.

---

## 19.2 코드

```
current_instances = {
    ("ap-northeast-2", "i-aaa111"),
    ("ap-northeast-2", "i-bbb222"),
    ("us-east-1", "i-ccc333")
}

desired_instances = {
    ("ap-northeast-2", "i-aaa111"),
    ("us-east-1", "i-ccc333"),
    ("us-west-2", "i-ddd444")
}

to_create = desired_instances - current_instances
to_delete = current_instances - desired_instances

print("생성해야 할 인스턴스:")
for region, instance_id in to_create:
    print(f"- 리전: {region}, 인스턴스 ID: {instance_id}")

print("삭제 검토 인스턴스:")
for region, instance_id in to_delete:
    print(f"- 리전: {region}, 인스턴스 ID: {instance_id}")
```

실행 결과 예시:

```
생성해야 할 인스턴스:
- 리전: us-west-2, 인스턴스 ID: i-ddd444
삭제 검토 인스턴스:
- 리전: ap-northeast-2, 인스턴스 ID: i-bbb222
```

---

## 19.3 설명

이 예제에서는 set 안에 tuple을 넣었다.

```
{
    ("ap-northeast-2","i-aaa111"),
    ("ap-northeast-2","i-bbb222")
}
```

set은 중복을 제거하고 비교 연산을 하기 좋다.

tuple은 리전과 인스턴스 ID처럼 하나의 리소스를 식별하는 고정된 값 묶음을 표현하기 좋다.

따라서 `set + tuple` 조합은 리소스 비교 작업에 유용하다.

---

# 20. tuple과 set 사용 시 주의사항

## 20.1 tuple은 값 변경이 불가능함

```
server= ("web-01","running")

server[1]="stopped"
```

실행 결과:

```
TypeError: 'tuple' object does not support item assignment
```

상태 변경이 필요한 데이터라면 tuple보다 dict 또는 list를 사용하는 것이 적절하다.

```
server= {
"name":"web-01",
"state":"running"
}

server["state"]="stopped"

print(server)
```

실행 결과:

```
{'name': 'web-01', 'state': 'stopped'}
```

---

## 20.2 set은 순서가 없음

```
regions= {"ap-northeast-2","us-east-1","us-west-2"}

print(regions)
```

실행 결과는 실행 환경에 따라 순서가 다르게 보일 수 있다.

```
{'us-west-2', 'ap-northeast-2', 'us-east-1'}
```

따라서 순서가 중요한 데이터에는 set을 사용하지 않는 것이 좋다.

출력 순서를 맞추고 싶다면 `sorted()`를 사용할 수 있다.

```
regions= {"ap-northeast-2","us-east-1","us-west-2"}

forregioninsorted(regions):
print(region)
```

실행 결과:

```
ap-northeast-2
us-east-1
us-west-2
```

---

## 20.3 set 안에는 변경 가능한 자료형을 넣을 수 없음

set의 요소도 변경 불가능해야 한다.

따라서 tuple은 set 안에 넣을 수 있지만 list는 넣을 수 없다.

```
values= {
    ("web-01","running"),
    ("web-02","stopped")
}

print(values)
```

실행 가능하다.

하지만 list를 넣으면 오류가 발생한다.

```
values= {
    ["web-01","running"],
    ["web-02","stopped"]
}
```

실행 결과:

```
TypeError: unhashable type: 'list'
```

set은 내부적으로 값의 중복 여부를 빠르게 판단해야 한다.

이를 위해 set의 요소는 변경되지 않는 값이어야 한다.

---

# 21. 실습 문제

## 실습 1. tuple 생성과 언패킹

다음 정보를 tuple로 저장한 뒤 각각의 변수로 나누어 출력하시오.

```
서버 이름: web-01
IP 주소: 10.0.1.10
상태: running
```

요구사항:

```
1. server_info라는 tuple을 생성한다.
2. name, ip, state 변수로 언패킹한다.
3. f-string을 사용해서 출력한다.
```

예상 출력:

```
서버 이름: web-01
IP 주소: 10.0.1.10
상태: running
```

정답 예시:

```
server_info= ("web-01","10.0.1.10","running")

name,ip,state=server_info

print(f"서버 이름:{name}")
print(f"IP 주소:{ip}")
print(f"상태:{state}")
```

---

## 실습 2. running 상태 서버만 출력하기

다음 서버 목록에서 상태가 `running`인 서버만 출력하시오.

```
servers= [
    ("web-01","10.0.1.10","running"),
    ("web-02","10.0.1.11","stopped"),
    ("db-01","10.0.2.10","running"),
    ("batch-01","10.0.3.10","terminated")
]
```

예상 출력:

```
web-01 서버가 실행 중입니다. IP: 10.0.1.10
db-01 서버가 실행 중입니다. IP: 10.0.2.10
```

정답 예시:

```
servers= [
    ("web-01","10.0.1.10","running"),
    ("web-02","10.0.1.11","stopped"),
    ("db-01","10.0.2.10","running"),
    ("batch-01","10.0.3.10","terminated")
]

forname,ip,stateinservers:
ifstate=="running":
print(f"{name} 서버가 실행 중입니다. IP:{ip}")
```

---

## 실습 3. set으로 중복 리전 제거하기

다음 리전 목록에서 중복을 제거하시오.

```
regions= [
"ap-northeast-2",
"us-east-1",
"ap-northeast-2",
"us-west-2",
"us-east-1"
]
```

요구사항:

```
1. set을 사용해서 중복을 제거한다.
2. 결과를 출력한다.
```

정답 예시:

```
regions= [
"ap-northeast-2",
"us-east-1",
"ap-northeast-2",
"us-west-2",
"us-east-1"
]

unique_regions=set(regions)

print(unique_regions)
```

---

## 실습 4. 필요한 포트 중 누락된 포트 찾기

다음 조건을 보고 누락된 포트를 찾으시오.

```
required_ports= {22,80,443}
current_open_ports= {80,443}
```

예상 출력:

```
누락된 포트: {22}
```

정답 예시:

```
required_ports= {22,80,443}
current_open_ports= {80,443}

missing_ports=required_ports-current_open_ports

print(f"누락된 포트:{missing_ports}")
```

---

## 실습 5. 현재 서버와 목표 서버 비교하기

현재 서버 목록과 목표 서버 목록을 비교해서 생성해야 할 서버와 삭제 검토 서버를 출력하시오.

```
current_servers= {"web-01","web-02","db-01"}
desired_servers= {"web-01","db-01","batch-01"}
```

예상 출력:

```
생성해야 할 서버: {'batch-01'}
삭제 검토 서버: {'web-02'}
유지되는 서버: {'web-01', 'db-01'}
```

정답 예시:

```
current_servers= {"web-01","web-02","db-01"}
desired_servers= {"web-01","db-01","batch-01"}

to_create=desired_servers-current_servers
to_delete=current_servers-desired_servers
unchanged=current_servers&desired_servers

print(f"생성해야 할 서버:{to_create}")
print(f"삭제 검토 서버:{to_delete}")
print(f"유지되는 서버:{unchanged}")
```

---

# 22. 정리

## 22.1 tuple 정리

`tuple`은 여러 값을 하나로 묶는 자료형이다.

`list`와 비슷하지만 한 번 생성한 뒤 값을 변경할 수 없다.

주요 특징은 다음과 같다.

```
1. 소괄호 ()를 사용한다.
2. 값의 변경이 불가능하다.
3. 인덱싱과 슬라이싱이 가능하다.
4. 함수에서 여러 값을 반환할 때 자주 사용된다.
5. 언패킹 문법과 함께 자주 사용된다.
6. dict의 key 또는 set의 요소로 사용할 수 있다.
```

클라우드 자동화에서는 리전과 리소스 ID처럼 고정된 값 묶음을 표현할 때 사용할 수 있다.

```
resource_key= ("ap-northeast-2","i-aaa111")
```

---

## 22.2 set 정리

`set`은 중복을 허용하지 않는 자료형이다.

순서를 보장하지 않으며, 집합 연산에 강하다.

주요 특징은 다음과 같다.

```
1. 중괄호 {}를 사용한다.
2. 중복 값을 자동으로 제거한다.
3. 순서를 보장하지 않는다.
4. 인덱싱이 불가능하다.
5. 합집합, 교집합, 차집합, 대칭 차집합을 사용할 수 있다.
6. 리소스 목록 비교와 중복 제거에 유용하다.
```