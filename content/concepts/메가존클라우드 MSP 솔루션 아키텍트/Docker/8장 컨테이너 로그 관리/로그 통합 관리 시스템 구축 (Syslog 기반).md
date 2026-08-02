---
title: "로그 통합 관리 시스템 구축 (Syslog 기반)"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Docker", "8장 컨테이너 로그 관리"]
is_public: true
draft: false
---

# 로그 통합 관리 시스템 구축 (Syslog 기반)

## 1. 학습 개요

* **목표**: 도커의 `json-file` 로그를 유지하며 `rsyslog`를 통해 로컬 통합 관리 및 원격 전송 환경을 구축한다.

* **주요 개념**: Logging Driver, rsyslog imfile 모듈, 템플릿(Template), 원격 전송.

---

## 2. 시스템 아키텍처

1. **발생**: 컨테이너 표준 출력(stdout) → 도커 엔진 전달.

2. **저장**: `/var/lib/docker/containers/` 경로에 JSON 파일로 기록.

3. **수집**: `rsyslog`가 해당 경로의 파일을 실시간 감시(Tail).

4. **전송**: 설정된 포맷(Template)에 맞춰 로컬 저장 또는 원격 서버 전송.

---

## 3. [실습 1] 도커 컨테이너 설정 (태그 삽입)

로그에 컨테이너 이름을 명시하기 위해 실행 시 `tag` 옵션을 사용합니다.

### A. Docker Compose 방식

YAML

```
services:
  my-app:
    image: nginx:latest
    logging:
      driver: "json-file"
      options:
        tag: "{{.Name}}"
        max-size: "10m"
        max-file: "3"
```

### B. Docker Run 명령줄 방식

Bash

```
docker run -d \
  --name my-service \
  --log-opt tag="{{.Name}}" \
  alpine sh -c "while true; do echo 'Hello Notion Log'; sleep 5; done"
```

---

## 4. [실습 2] rsyslog 서버 설정 (로그 수집기)

### ① 권한 설정 (`/etc/rsyslog.conf`)

도커 로그 디렉토리 접근을 위해 `root` 권한으로 실행하도록 수정합니다.

1. `/etc/rsyslog.conf` 열기

2. 아래 두 줄을 찾아 `#`으로 주석 처리

Bash

```
# $PrivDropToUser syslog
# $PrivDropToGroup syslog
```

### ② 도커 전용 설정 파일 작성

`/etc/rsyslog.d/20-docker.conf` 파일을 생성하고 아래 내용을 입력합니다. (들여쓰기 주의)

```
# 1. 모듈 로드
module(load="imfile")

# 2. 로그 포맷 템플릿 정의
template(name="DockerFormat" type="list") {
    property(name="timestamp" dateFormat="rfc3339")
    constant(value=" [")
    property(name="syslogtag")
    constant(value="] ")
    property(name="msg")
    constant(value="\n")
}

# 3. 도커 JSON 로그 파일 읽기 설정
input(type="imfile"
      File="/var/lib/docker/containers/*/*.log"
      Tag="docker"
      Severity="info"
      Facility="local0")

# 4-1. 로컬 통합 로그 파일에 저장
local0.* action(type="omfile" File="/var/log/docker_combined.log" Template="DockerFormat")

# 4-2. [옵션] 원격 서버 전송 시 (주석 해제 후 사용)
# local0.* @192.168.1.100:514;DockerFormat

# 5. 처리 중단
& stop
```

---

## 5. [실습 3] 검증 및 확인

### 1. 설정 검사 및 재시작

Bash

```
# 문법 에러 체크
sudo rsyslogd -N1

# 서비스 재시작
sudo systemctl restart rsyslog
```

### 2. 로그 확인

```
# 로컬 통합 파일 실시간 모니터링
tail -f /var/log/docker_combined.log
```

---

## 6. 핵심 요약 및 트러블슈팅

|  |  |
| --- | --- |
| **문제 상황** | **원인 및 해결책** |
| **Permission Denied** | `PrivDrop` 설정 주석 처리 확인 및 상위 디렉토리 권한 체크 |
| **컨테이너 이름 미출력** | 컨테이너 실행 시 `--log-opt tag="{{.Name}}"` 적용 확인 |
| **로그 파일 미생성** | `rsyslogd -N1`로 문법 에러 유무 확인 |