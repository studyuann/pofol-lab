---
title: "3장 Docker 기본 명령어 (컨테이너 생명주기)"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Docker"]
is_public: true
draft: false
---

# 3장. Docker 기본 명령어 (컨테이너 생명주기)

---

## 3장 학습 목표

* Docker 명령어의 **대상(object)** 개념을 이해한다.

* `docker run`이 내부적으로 수행하는 작업을 **단계별로 설명**할 수 있다.

* 컨테이너의 **생성 → 실행 → 중지 → 삭제** 흐름을 명령어로 제어할 수 있다.

* 옵션에 따라 컨테이너 동작 방식이 **어떻게 달라지는지** 설명할 수 있다.

---

## 3.1 Docker 명령어 구조 이해

### 3.1.1 Docker 명령어의 기본 형식

```
docker <대상> <명령> [옵션]
```

### 대상(Object) 예시

* `container` (또는 생략)

* `image`

* `volume`

* `network`

예:

```
docker container ls
docker image ls
```

👉 실무에서는 `docker ps`, `docker images`처럼 **container/image는 생략**되는 경우가 많음

---

### 3.1.2 자주 사용하는 대상별 명령

| 대상 | 대표 명령 |
| --- | --- |
| container | run, ps, start, stop, rm |
| image | pull, ls, rm, inspect |
| volume | create, ls, inspect |
| network | ls, create |

---

## 3.2 docker run 완전 분해 (핵심)

> `docker run`은 단순 실행 명령이 아니다.
>
> * \*여러 단계가 한 번에 수행되는 “복합 명령”\*\*이다.

### 3.2.1 docker run 내부 동작 흐름

```
docker run ubuntu:22.04 bash
```

실제로 수행되는 단계:

1. 이미지 존재 여부 확인 (`docker images`)

2. 없으면 Registry에서 pull

3. 컨테이너 생성 (`docker create`)

4. 컨테이너 시작 (`docker start`)

5. 터미널 연결 (`docker attach`)

👉 즉,

```
docker run = pull + create + start + attach
```

---

### 3.2.2 docker create vs docker start

```
docker create ubuntu:22.04
docker start <컨테이너ID>
```

* `create` : 컨테이너 “틀”만 생성 (실행 ❌)

* `start` : 이미 만들어진 컨테이너 실행

👉 운영 환경에서는 **create / start를 분리**해서 쓰는 경우도 많음

---

## 3.3 컨테이너 목록 확인

### 3.3.1 실행 중인 컨테이너

```
docker ps
```

### 3.3.2 전체 컨테이너

```
docker ps -a
```

### 출력 컬럼 해설

* `CONTAINER ID` : 컨테이너 고유 ID

* `IMAGE` : 사용 중인 이미지

* `COMMAND` : PID 1로 실행 중인 명령

* `STATUS` : 실행/중지 상태

* `PORTS` : 포트 매핑 정보

* `NAMES` : 컨테이너 이름

---

## 3.4 컨테이너 실행 옵션 상세

### 3.4.1 -it 옵션

```
docker run -it ubuntu:22.04 bash
```

* `i` : 표준 입력 유지 (키보드 입력)

* `t` : 터미널 형태 출력

👉 쉘 기반 컨테이너는 거의 필수 옵션

---

### 3.4.2 -d 옵션 (백그라운드 실행)

```
docker run -d nginx
```

* `d` : detached mode

* 터미널을 점유하지 않음

* 서버형 컨테이너(웹/DB)에 필수

---

### 3.4.3 --name 옵션

```
docker run --name web01 nginx
```

* 사람이 기억하기 쉬운 이름 부여

* 이름 미지정 시 Docker가 랜덤 생성

👉 실무에서는 **반드시 name 지정** 권장

---

### 3.4.4 --rm 옵션

```
docker run --rm ubuntu echo "test"
```

* 컨테이너 종료 시 자동 삭제

* 테스트/일회성 작업에 적합

---

## 3.5 컨테이너 제어 명령

### 3.5.1 컨테이너 중지

```
docker stop <컨테이너ID|이름>
```

* SIGTERM → 일정 시간 후 SIGKILL

* 정상 종료를 유도

---

### 3.5.2 컨테이너 강제 종료

```
docker kill <컨테이너ID|이름>
```

* 즉시 SIGKILL

* 장애 상황에서만 사용

---

### 3.5.3 컨테이너 재시작

```
docker restart <컨테이너ID|이름>
```

---

## 3.6 컨테이너 삭제

### 3.6.1 중지된 컨테이너 삭제

```
docker rm <컨테이너ID>
```

### 3.6.2 실행 중 컨테이너 삭제

```
docker rm -f <컨테이너ID>
```

👉 `-f`는 stop + rm

---

## 3.7 컨테이너 내부 접근

### 3.7.1 docker attach

```
docker attach <컨테이너ID>
```

* STDOUT/STDIN에 직접 연결

* 쉘 종료 시 컨테이너도 종료될 수 있음

---

### 3.7.2 docker exec (권장)

```
docker exec -it <컨테이너ID> bash
```

* 실행 중인 컨테이너에 **새 프로세스**로 접속

* 운영 환경에서 표준 방식

👉 **attach보다 exec를 권장**

---

## 3.8 컨테이너 로그 확인

### 3.8.1 로그 조회

```
docker logs <컨테이너ID>
```

### 3.8.2 실시간 로그

```
docker logs -f <컨테이너ID>
```

---

## 3.9 컨테이너 상태 확인

### 3.9.1 상세 정보

```
docker inspect <컨테이너ID>
```

* JSON 형식

* 네트워크, 마운트, PID, 리소스 설정 확인 가능

---

### 3.9.2 리소스 사용량

```
docker stats
```

👉 CPU/메모리 실시간 확인

---

## 3.10 실습: 컨테이너 생명주기 전체 흐름

### 실습 시나리오

1. ubuntu 컨테이너 생성

2. bash 실행

3. 백그라운드 실행

4. exec로 접속

5. 로그 확인

6. 중지

7. 삭제

```
docker run -dit --name test01 ubuntu:22.04 bash
docker exec -it test01 bash
exit
docker stop test01
docker rm test01
```

---