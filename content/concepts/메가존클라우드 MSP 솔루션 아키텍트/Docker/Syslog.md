---
title: "Syslog"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Docker"]
is_public: true
draft: false
---

# Syslog

**Syslog(System Logging)** 는 리눅스/유닉스 계열 운영체제에서 **시스템과 응용프로그램이 발생시키는 로그 메시지를 표준 형식으로 수집·저장·전송하기 위한 로그 관리 체계**.

쉽게 말해 컴퓨터에서 일어나는 모든 사건을 기록하는 공식적인 일지 시스템.

운영체제, 네트워크 서비스(SSH, FTP, 웹서버 등), 사용자 프로그램, 보안 모듈까지 다양한 구성요소가 syslog 규칙에 따라 로그를 남김.

---

## 로그(Log)란 무엇인가?

로그는 시스템에서 발생하는 **이벤트 기록**.

예시:

* 사용자가 SSH로 로그인 시도

* 웹 서버에서 404 오류 발생

* 디스크 용량 부족 경고

* 서비스 시작/중지

* 프로그램 오류(에러, 예외)

이러한 정보가 **시간, 사용자, 프로세스, 원인, 결과** 등의 형태로 기록됨.

---

## 1. Syslog의 핵심 개념

Syslog는 단순히 “로그 파일 하나”가 아니라 **로그를 관리하는 체계**로써 다음과 같은 특징을 가짐.

### - 표준화된 형식

로그 메시지는 공통 구조를 가짐.

```
날짜 시간 호스트명 프로그램명[PID]: 메시지
```

예시:

```
Feb  7 10:15:23 server1 sshd[1234]: Failed password for root from 192.168.0.5
```

이 형식 덕분에 **자동 분석 도구**가 쉽게 해석할 수 있음.

---

## 2. Syslog 메시지의 기본 개념 (Facility / Severity)

### 1) Facility (어디서 나온 로그인가)

* 예: `auth`, `authpriv`, `kern`, `daemon`, `mail`, `cron`, `local0~local7` 등

### 2) Severity(Priority Level) (얼마나 심각한가)

낮을수록 심각함.(0이 가장 치명적).

| 숫자 | 이름 | 의미 |
| --- | --- | --- |
| 0 | emerg | 시스템 사용 불가 수준 |
| 1 | alert | 즉시 조치 필요 |
| 2 | crit | 치명적 오류 |
| 3 | err | 오류 |
| 4 | warning | 경고 |
| 5 | notice | 중요한 알림 |
| 6 | info | 정보 |
| 7 | debug | 디버그 |

### 3) Selector 형식 예시

* `authpriv.*` : authpriv facility의 모든 레벨

* `.info` : 모든 facility의 info 이상(통상 “이상”으로 동작)

* `mail.err` : mail facility의 err 레벨

---

## 3. Rocky Linux 9에서 로그 확인 (journalctl, /var/log)

## 3.1 journalctl 기본 사용법

### 1) 전체 로그 보기

```
journalctl
```

* **설명**: systemd 저널의 전체 로그를 시간순으로 출력함.

* **팁**: 페이지 출력(less)로 뜨며 `q`로 종료함.

### 2) 부팅 단위로 보기

```
journalctl -b
```

* **설명**: 현재 부팅 세션의 로그만 본다.

* 이전 부팅 로그는:

```
journalctl -b -1
```

* **설명**: `1`은 “바로 이전 부팅”을 의미한다.

### 3) 실시간 따라가기(tail -f 유사)

```
journalctl -f
```

* **설명**: 새로운 로그가 추가될 때마다 화면에 이어서 표시한다.

* 서비스 기동/장애 재현 중 모니터링에 유용하다.

### 4) 특정 서비스(Unit) 로그 보기

```
journalctl -u sshd
```

* **설명**: `sshd.service`의 로그만 필터링한다.

* 실시간으로 보려면:

```
journalctl -u sshd -f
```

### 5) 시간 범위로 검색

```
journalctl --since "2026-02-01" --until "2026-02-07 12:00"
```

* **설명**: 지정한 기간 로그만 조회한다.

### 6) 로그 레벨로 필터(중요 로그만)

```
journalctl -p err -b
```

* **설명**: 현재 부팅 세션(-b)에서 err 이상(심각도 높은) 로그만 출.

---

## 3.2 /var/log 텍스트 로그 확인

### 대표 파일(환경에 따라 조금씩 다름)

* `/var/log/messages` : 일반 시스템 메시지(많은 데몬 로그)

* `/var/log/secure` : 인증/보안 관련(SSH 로그인 등)

* `/var/log/cron` : cron 실행 내역

* `/var/log/maillog` : 메일 관련

조회 예시:

```
tail -n 50 /var/log/messages
```

* **설명**: 마지막 50줄만 출력.

실시간 모니터링:

```
tail -f /var/log/secure
```

* **설명**: 인증/SSH 테스트 중 로그인 시도가 찍히는지 확인 가능

키워드 검색:

```
grep -i "error" /var/log/messages
```

* **설명**: `i`는 대소문자 무시하고 검색.

---

## 4. rsyslog 설치/상태 확인/기동

### 1) 설치 확인

```
rpm -q rsyslog
```

* **설명**: 패키지 설치 여부와 버전을 확인.

없다면 설치:

```
sudo dnf -y install rsyslog
```

* **설명**
  + `dnf`: 패키지 관리자
  + `y`: 설치 확인 질문에 자동으로 yes

### 2) 서비스 상태 확인

```
systemctl status rsyslog
```

* **설명**: rsyslog 데몬의 실행 상태, 최근 로그, PID 등을 확인.

기동/재기동/자동시작:

```
sudo systemctl enable --now rsyslog
sudo systemctl restart rsyslog
```

* **설명**
  + `enable --now`: 부팅 시 자동 시작 등록 + 즉시 시작
  + `restart`: 설정 변경 후 재기동

---

## 5. rsyslog 설정 파일 구조 이해

### 1) 주요 설정 파일

* `/etc/rsyslog.conf` : 메인 설정

* `/etc/rsyslog.d/*.conf` : 추가 설정(권장: 커스텀은 여기에 분리)

설정 확인:

```
sudo ls -al /etc/rsyslog.conf /etc/rsyslog.d/
```

### 2) 기본 규칙(예시 개념)

rsyslog는 “어떤 로그(selector)”를 “어디(action)”로 보낼지 정의.

* selector: `facility.severity`

* action: 파일에 저장, 원격으로 전달, 특정 프로그램 실행 등

---

## 6. 실습 1: logger로 syslog 메시지 생성해보기

### 1) logger 명령으로 로그 남기기

```
logger "HELLO syslog from Rocky9"
```

* **설명**
  + `logger`: 커맨드라인에서 syslog 메시지를 보내는 도구
  + 기본 facility/priority로 로그가 기록됩니다.

확인:

```
tail -n 20 /var/log/messages
```

또는 저널:

```
journalctl -t logger -n 20
```

* **설명**
  + `t`: tag 기준 검색 (logger가 남긴 태그를 이용)

### 2) facility/priority 지정

```
logger -p local0.info "local0 info test"
logger -p authpriv.warning "authpriv warning test"
```

* **설명**
  + `p facility.level` 형식으로 지정
  + 실무에서 “앱별 local0~local7 할당” 패턴이 많음.

---

## 7. 실습 2: 특정 facility(local0) 로그를 별도 파일로 분리 저장

### 목표

`local0.*` 로그는 `/var/log/local0.log`에 저장되게 설정

### 1) 설정 파일 생성

```
sudo vi /etc/rsyslog.d/10-local0.conf
```

아래 내용 추가:

```
local0.*    /var/log/local0.log
```

* **설명**
  + `local0.*` : local0 facility의 모든 레벨
  + `/var/log/local0.log` : 저장 파일 경로

### 2) 문법 체크(권장)

```
sudo rsyslogd -N1
```

* **설명**
  + `N1`: 설정 파일 문법 검사 모드(실행하지 않고 검증)
  + 에러가 나오면 라인/모듈 문제를 먼저 해결해야 함.

### 3) rsyslog 재기동

```
sudo systemctl restart rsyslog
```

### 4) 테스트 로그 생성 및 확인

```
logger -p local0.info "local0 분리 저장 테스트"
sudo tail -n 20 /var/log/local0.log
```

---

## 8. 로그 회전(logrotate) 기본

### 1) 왜 필요한가?

로그는 계속 커지므로 저장공간이 부족해 짐.

logrotate는 “파일을 날짜/크기 기준으로 교체하고 압축”함.

### 2) rsyslog 기본 logrotate 정책 확인

```
sudo ls -al /etc/logrotate.d/
sudo cat /etc/logrotate.d/rsyslog
```

### 3) 우리가 만든 local0.log도 회전시키기

```
sudo vi /etc/logrotate.d/local0
```

예시 설정:

```
/var/log/local0.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 root root
    sharedscripts
    postrotate
        /bin/systemctl kill -s HUP rsyslog.service >/dev/null 2>&1 || true
    endscript
}
```

* **항목 설명(중요)**
  + `daily`: 매일 회전
  + `rotate 14`: 14개 보관(2주치)
  + `compress`: gzip 압축
  + `delaycompress`: 바로 전 회전본은 즉시 압축하지 않고 다음 회전에 압축(일부 앱 호환성)
  + `missingok`: 파일 없어도 에러 내지 않음
  + `notifempty`: 빈 로그면 회전 안 함
  + `create 0640 root root`: 새 로그 파일 권한/소유자 설정
  + `postrotate ...`: 회전 후 rsyslog에 HUP을 보내 파일 핸들 재오픈 유도

    (회전 후에도 계속 옛 파일에 쓰는 문제 예방)

강제 테스트:

```
sudo logrotate -f /etc/logrotate.d/local0
```

* **설명**
  + `f`: 조건 무시하고 강제 회전
  + 결과로 `.1`, `.gz` 파일 생성 여부를 확인합니다.

---

## 9. 원격 Syslog 구성 (서버/클라이언트)

> 중앙 로그 서버에 모으는 운영 형태를 가정합니다.
>
> 네트워크 정책 상 UDP 514 또는 TCP 514를 주로 사용합니다. (보안/신뢰성은 TCP 권장)

---

### 9.1 서버: rsyslog가 원격 수신하도록 설정

### 1) 수신 포트 열기(방화벽)

UDP 514 예시:

```
sudo firewall-cmd --add-port=514/udp --permanent
sudo firewall-cmd --reload
```

TCP 514도 쓸 경우:

```
sudo firewall-cmd --add-port=514/tcp --permanent
sudo firewall-cmd --reload
```

* **설명**
  + `-permanent`: 영구 적용(재부팅 후 유지)
  + `-reload`: 영구 설정을 런타임에 반영

### 2) rsyslog 수신 모듈 활성화

```
sudo vi /etc/rsyslog.d/20-remote-recv.conf
```

UDP 수신:

```
module(load="imudp")
input(type="imudp" port="514")
```

TCP 수신:

```
module(load="imtcp")
input(type="imtcp" port="514")
```

문법 체크:

```
sudo rsyslogd -N1
sudo systemctl restart rsyslog
```

### 3) 서버에서 수신 확인(포트 리스닝)

```
sudo ss -lpun | grep 514
sudo ss -lptn | grep 514
```

* **설명**
  + `ss -l`: listen 상태
  + `p`: 프로세스 정보
  + `u`: UDP, `t`: TCP, `n`: 숫자 출력

---

### 9.2 클라이언트: 원격 서버로 로그 전송

### 1) 전송 규칙 추가

```
sudo vi /etc/rsyslog.d/30-remote-send.conf
```

예시(모든 로그를 UDP로 전송):

```
*.*    @192.168.10.10:514
```

TCP로 전송(권장):

```
*.*    @@192.168.10.10:514
```

* **설명**
  + `@`: UDP
  + `@@`: TCP
  + `.*`: 모든 facility, 모든 severity

재기동:

```
sudo rsyslogd -N1
sudo systemctl restart rsyslog
```

### 2) 전송 테스트

클라이언트에서:

```
logger -p local0.info "REMOTE syslog test from client"
```

서버에서(예: /var/log/messages 또는 정책에 따라 저장 파일):

```
sudo tail -n 50 /var/log/messages
```

---