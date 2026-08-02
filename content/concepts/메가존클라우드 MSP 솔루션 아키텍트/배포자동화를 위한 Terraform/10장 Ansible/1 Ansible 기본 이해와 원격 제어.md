---
title: "1 Ansible 기본 이해와 원격 제어"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "배포자동화를 위한 Terraform", "10장 Ansible"]
is_public: true
draft: false
---

# 1. Ansible 기본 이해와 원격 제어

## 1.1 Ansible 개요

Ansible은 여러 대의 서버를 일관된 방식으로 관리하기 위한 자동화 도구임.

서버 운영 환경에서는 동일한 작업을 여러 서버에 반복해서 수행해야 하는 경우가 매우 많음. 예를 들어 웹서버 3대에 동일한 패키지를 설치하고, 같은 설정파일을 배포하고, 서비스를 시작해야 하는 상황이 자주 발생함. 이런 작업을 사람이 직접 한 대씩 접속해서 처리하면 시간이 오래 걸리고, 설정 누락이나 오타 같은 실수가 발생하기 쉬움.

Ansible은 이러한 반복 작업을 자동화하기 위해 사용함.

관리 대상 서버에 직접 접속해서 명령을 수행하고, 패키지를 설치하고, 파일을 복사하고, 서비스를 제어하는 작업을 한 번에 처리할 수 있음. 단순히 명령을 여러 서버에 동시에 전달하는 수준을 넘어서, 서버가 **원하는 상태**가 되도록 관리하는 데 목적이 있음.

예를 들어 다음과 같은 상태를 만들고 싶다고 가정함.

* 모든 웹서버에 nginx가 설치되어 있어야 함

* nginx 서비스가 실행 중이어야 함

* 특정 index 파일이 배포되어 있어야 함

이때 Ansible은 “명령을 실행했다”는 수준이 아니라 “해당 서버가 원하는 상태가 되었는가”를 기준으로 동작함.

이 점이 단순 원격 명령 실행과 Ansible을 구분하는 핵심임.

---

## 1.2 자동화가 필요한 이유

서버 운영 업무에서 반복 작업은 매우 흔함.

대표적인 예시는 다음과 같음.

* 여러 서버에 동일 패키지 설치

* 사용자 계정 일괄 생성

* 설정파일 배포

* 로그 디렉터리 생성

* 서비스 시작 및 자동 시작 등록

* 보안 설정 일괄 반영

이런 작업을 수작업으로 수행하면 다음과 같은 문제가 생김.

### 1.2.1 반복 작업으로 인한 비효율

서버 수가 적을 때는 직접 접속해서 작업하는 것이 가능해 보일 수 있음.

하지만 서버가 5대, 10대, 20대로 늘어나면 같은 작업을 반복하는 데 많은 시간이 소모됨.

### 1.2.2 설정 불일치

한 서버에는 패키지를 설치했지만 다른 서버에는 빠뜨릴 수 있음.

어떤 서버는 설정파일을 수정했지만 어떤 서버는 이전 설정이 남아 있을 수도 있음.

이런 상태는 운영 표준을 깨뜨리고 장애 원인이 되기도 함.

### 1.2.3 작업 이력 추적 어려움

사람이 직접 명령을 입력하면 누가 언제 어떤 명령을 실행했는지 추적하기 어려움.

반면 자동화 도구를 사용하면 playbook이나 명령 기록을 통해 작업 내용을 비교적 명확하게 확인할 수 있음.

### 1.2.4 재현성 부족

한 번은 성공했지만 같은 작업을 다시 반복하려고 할 때, 이전 작업 순서를 정확히 기억하지 못하는 경우가 많음.

자동화는 이러한 문제를 줄이고 동일한 작업을 반복 가능하게 만듦.

---

## 1.3 Ansible의 특징

Ansible은 여러 자동화 도구 중에서도 비교적 배우기 쉽고 빠르게 적용할 수 있는 도구로 평가됨.

주요 특징은 다음과 같음.

### 1.3.1 Agentless 구조

Ansible은 관리 대상 서버에 별도 에이전트를 설치하지 않아도 됨.

보통 SSH를 이용해 대상 서버에 접속한 후 필요한 작업을 수행함.

즉, 제어 노드에만 Ansible이 설치되어 있으면 관리 대상 서버에는 SSH 접속만 가능하면 됨.

이 구조의 장점은 다음과 같음.

* 초기 구축이 비교적 단순함

* 대상 서버에 추가 소프트웨어를 설치하지 않아도 됨

* 운영 환경 부담이 적음

### 1.3.2 SSH 기반 동작

대부분의 리눅스 서버는 SSH를 통해 원격 접속이 가능함.

Ansible은 이 SSH를 기반으로 원격 명령 실행, 파일 복사, 패키지 설치, 서비스 제어를 수행함.

즉, Ansible은 완전히 새로운 통신 체계를 만드는 것이 아니라, 이미 서버 관리에서 널리 사용하는 SSH를 그대로 활용함.

### 1.3.3 YAML 기반 플레이북

Ansible은 자동화 작업을 YAML 형식의 playbook으로 작성함.

YAML은 사람이 읽기 쉬운 구조를 가지기 때문에 복잡한 스크립트 언어에 비해 가독성이 좋고 학습 진입장벽이 낮은 편임.

예를 들어 다음과 같은 형태로 작업을 기술함.

```
---
- name: Install nginx
  hosts: web
  become: true

  tasks:
    - name: Install nginx package
      ansible.builtin.apt:
        name: nginx
        state: present
```

이러한 형식 덕분에 자동화 흐름을 문서처럼 읽을 수 있음.

### 1.3.4 멱등성 기반 작업

Ansible의 중요한 특징 중 하나는 **멱등성(idempotence)** 개념임.

멱등성이란 같은 작업을 여러 번 실행해도 결과가 동일하게 유지되는 성질을 의미함.

예를 들어 nginx가 이미 설치되어 있는 서버에 다시 “nginx를 설치하라”는 playbook을 실행하더라도, 이미 원하는 상태라면 불필요한 재설치를 하지 않음.

이 점은 반복 실행이 잦은 운영 환경에서 매우 중요함.

---

## 1.4 Ansible의 기본 구성 요소

Ansible을 이해하려면 먼저 주요 구성 요소를 구분해야 함.

초기 단계에서는 아래 개념을 정확히 구분하는 것이 중요함.

### 1.4.1 Control Node

Ansible이 설치되어 있고, 명령을 실행하는 중심 서버 또는 작업 PC를 의미함.

이 노드에서 inventory를 읽고, 플레이북을 실행하고, 관리 대상 서버에 접속함.

일반적으로 실습 환경에서는 교육생의 리눅스 VM 또는 WSL 환경이 control node 역할을 맡음.

### 1.4.2 Managed Node

Ansible이 접속해서 작업을 수행할 대상 서버를 의미함.

보통 리눅스 서버이며, SSH 접속이 가능해야 함.

예를 들어 Ubuntu VM 2대가 있다면, 이 2대는 managed node가 됨.

### 1.4.3 Inventory

Ansible이 어느 서버를 대상으로 작업할지 정의하는 목록임.

호스트 주소, 그룹명, 접속 계정, SSH 키 경로 등을 담을 수 있음.

예를 들면 다음과 같음.

```
[web]
10.10.10.11
10.10.10.12

[app]
10.10.10.21
```

### 1.4.4 Module

Ansible이 실제 작업을 수행할 때 사용하는 기능 단위임.

예를 들어 다음과 같은 모듈이 있음.

* `ping` : 연결 확인

* `apt` : 패키지 설치

* `service` : 서비스 제어

* `copy` : 파일 복사

* `file` : 파일/디렉터리 상태 관리

즉, Ansible은 모듈을 조합해 작업을 수행함.

### 1.4.5 Playbook

자동화 절차를 YAML 형식으로 작성한 파일임.

여러 태스크를 순서대로 정의하여 반복 가능한 자동화 작업을 만들 수 있음.

---

## 1.5 Control Node와 Managed Node 구조

Ansible의 기본 구조는 다음과 같음.

```
[Control Node]
  ├─ Ansible 설치
  ├─ Inventory 보관
  ├─ Playbook 작성
  └─ SSH로 대상 서버 접속

        │
        │ SSH
        ▼

[Managed Node 1]
[Managed Node 2]
[Managed Node 3]
```

이 구조를 보면 알 수 있듯이, 제어 노드는 관리 대상 서버에 일괄적으로 접속하여 동일한 작업을 수행할 수 있음.

예를 들어 3대의 서버에 nginx를 설치해야 한다면, 제어 노드에서 Ansible 명령 한 줄 또는 playbook 실행 한 번으로 처리가 가능함.

여기서 중요한 점은, managed node에 Ansible 패키지가 반드시 설치되어 있을 필요는 없다는 점임.

대신 다음 조건은 충족되어야 함.

* SSH 접속 가능

* 원격 계정 사용 가능

* Python 실행 가능
  + 대부분의 일반적인 리눅스 서버는 Python을 기본 또는 쉽게 설치 가능한 형태로 제공함

---

## 1.6 실습 환경 준비

이 장에서는 실습 환경이 이미 준비되어 있다고 가정함.

실습에 필요한 기본 요소는 다음과 같음.

* 제어 노드 1대

* 관리 대상 서버 2대 이상

* SSH 키 파일

* 각 서버의 IP 주소

* Ansible 설치 완료

실습 디렉터리는 아래와 같은 구조로 구성함.

```
ansible-lab/
├─ inventory.ini
└─ playbooks/
```

실습을 위해 디렉터리를 생성함.

```
mkdir -p ~/ansible-lab/playbooks
cd ~/ansible-lab
```

---

## 1.7 Ansible 설치 및 버전 확인

Ansible 설치

Ansible은 일반적으로 **제어 노드(control node)** 에 설치한다.

즉, 관리 대상 서버에 설치하는 것이 아니라,

명령을 실행할 내 로컬 PC나 관리용 Linux 서버에 설치한다.

여기서는 학습용으로 많이 사용하는 Linux 환경 기준과 macOS 기준을 함께 정리한다.

Windows 사용자는 보통 WSL2 환경에서 설치하는 방식이 가장 무난하다.

---

## Linux에서 설치

배포판에 따라 방식이 조금 다를 수 있지만,

가장 무난한 방법은 Python 패키지 관리자 `pip`를 사용하는 것이다.

### Python 및 pip 확인

```
python3 --version
pip3 --version
```

Python 3와 pip가 준비되어 있어야 한다.

---

### pip로 Ansible 설치

```
pip3 install ansible
```

환경에 따라 `--user` 옵션을 함께 쓸 수도 있다.

```
pip3 install --user ansible
```

---

### 설치 확인

```
ansible --version
```

정상 설치되었다면 Ansible 버전, Python 버전 등의 정보가 출력된다.

---

## macOS에서 설치

macOS에서는 Homebrew를 쓰는 경우가 많다.

### Homebrew로 설치

```
brew install ansible
```

---

### 설치 확인

```
ansible --version
```

---

정상적으로 설치되어 있다면 다음과 비슷한 출력이 나타남.

```
ansible [core 2.x.x]
  config file = None
  configured module search path = ...
  ansible python module location = ...
  executable location = /usr/bin/ansible
  python version = 3.x.x
```

이 출력에서 확인할 수 있는 내용은 다음과 같음.

* Ansible 코어 버전

* 실행 파일 경로

* Python 버전

* 기본 설정 파일 위치

버전 확인은 단순 정보 조회처럼 보이지만, 실습 환경 문제를 진단할 때 매우 중요함.

특히 버전에 따라 모듈 동작 차이가 있을 수 있으므로, 교육 초반에 반드시 확인하는 것이 좋음.

---

## 1.8 SSH 접속 확인

Ansible은 기본적으로 SSH를 통해 관리 대상 서버에 접속하므로, 우선 사람이 직접 SSH 접속이 가능한지 확인하는 것이 좋음.

예시:

```
ssh -i ~/.ssh/lab.pem ubuntu@10.10.10.11
```

이 명령의 의미는 다음과 같음.

* `ssh` : 원격 서버 접속 명령

* `i ~/.ssh/lab.pem` : 사용할 개인키 파일 지정

* `ubuntu@10.10.10.11` : 원격 접속 계정과 대상 IP

정상적으로 접속되면 관리 대상 서버에 로그인됨.

이 단계에서 접속이 되지 않으면 Ansible도 정상 동작하지 않음.

SSH 접속이 실패하는 대표적인 원인은 다음과 같음.

* 잘못된 IP 주소

* 잘못된 사용자 계정

* SSH 키 파일 경로 오류

* 키 파일 권한 문제

* 방화벽 또는 보안그룹 문제

키 파일 권한이 너무 넓게 열려 있으면 SSH가 거부될 수 있음.

이 경우 다음 명령으로 권한을 조정함.

```
chmod 400 ~/.ssh/lab.pem
```

---

## 1.9 Inventory 작성

Ansible은 inventory를 통해 관리 대상 서버를 인식함.

이 장에서는 가장 기본적인 정적 inventory 파일을 작성함.

`inventory.ini` 파일을 아래처럼 작성함.

```
[web]
10.10.10.11 ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/lab.pem
10.10.10.12 ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/lab.pem
```

이 파일의 의미를 자세히 보면 다음과 같음.

### `[web]`

* `web`이라는 그룹을 정의함

* 이 그룹 아래에 속한 호스트들은 이후 `hosts: web` 또는 `ansible ... web ...` 형태로 지정 가능함

### `10.10.10.11`

* 관리 대상 서버의 IP 주소임

### `ansible_user=ubuntu`

* 접속 시 사용할 원격 계정을 의미함

* Ubuntu 이미지에서는 기본 계정이 `ubuntu`인 경우가 많음

### `ansible_ssh_private_key_file=~/.ssh/lab.pem`

* 접속에 사용할 개인키 파일 경로를 의미함

이처럼 inventory는 단순한 IP 목록이 아니라, 실제 접속에 필요한 정보를 함께 담을 수 있음.

---

## 1.10 Inventory 확인

작성한 inventory가 올바르게 인식되는지 확인하기 위해 다음 명령을 사용함.

```
ansible-inventory -i inventory.ini --list
```

이 명령은 inventory를 JSON 형태로 상세 출력함.

처음에는 다소 복잡해 보일 수 있지만, 그룹 구조와 호스트 목록이 제대로 들어갔는지 확인할 수 있음.

좀 더 시각적으로 간단히 확인하려면 다음 명령을 사용함.

```
ansible-inventory -i inventory.ini --graph
```

예상 출력 예시는 다음과 같음.

```
@all:
  |--@ungrouped:
  |--@web:
  |  |--10.10.10.11
  |  |--10.10.10.12
```

이 결과를 통해 다음을 확인할 수 있음.

* `web` 그룹이 생성되었는가

* 해당 그룹 아래에 서버가 포함되었는가

* inventory 문법 오류는 없는가

---

## 1.11 Ad-hoc Command 개요

Ansible에는 playbook 외에도 빠른 1회성 작업을 수행하는 방식이 있음.

이를 **ad-hoc command**라고 함.

ad-hoc command는 다음과 같은 상황에 유용함.

* 서버 연결 상태 확인

* 간단한 명령 실행

* 패키지 1회 설치

* 파일 존재 여부 점검

* 서비스 상태 빠른 확인

즉, playbook을 작성하기 전에 가볍게 테스트하거나, 운영 중 즉시 확인해야 하는 작업에 적합함.

기본 형식은 다음과 같음.

```
ansible -i inventory.ini 대상그룹 -m 모듈명 -a "모듈 인수"
```

여기서 각 요소의 의미는 다음과 같음.

* `ansible` : ad-hoc command 실행 명령

* `i inventory.ini` : 사용할 inventory 파일 지정

* `대상그룹` : `all`, `web`, 특정 호스트 등

* `m` : 사용할 모듈 지정

* `a` : 모듈에 전달할 인수 지정

---

## 1.12 연결 테스트: ping 모듈

가장 먼저 해볼 실습은 대상 서버와의 연결 확인임.

```
ansible -i inventory.ini all -m ping
```

이 명령에서:

* `all` : inventory에 등록된 모든 서버 대상

* `m ping` : ping 모듈 사용

여기서 ping은 일반 네트워크 ICMP ping과는 다름.

Ansible의 ping 모듈은 관리 대상 서버에 접속해서 Python 실행이 가능한지, Ansible 통신이 되는지를 확인하는 용도임.

정상 결과 예시는 다음과 같음.

```
10.10.10.11 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
10.10.10.12 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```

`SUCCESS`와 `"ping": "pong"`이 보이면 연결이 정상인 것임.

---

## 1.13 원격 명령 실행: command 모듈

이제 실제로 원격 명령을 실행해봄.

가장 기본적인 예로 호스트명을 확인함.

```
ansible -i inventory.ini all -m command -a "hostname"
```

이 명령은 inventory에 등록된 모든 서버에서 `hostname` 명령을 실행함.

예상 출력:

```
10.10.10.11 | CHANGED | rc=0 >>
web-01
10.10.10.12 | CHANGED | rc=0 >>
web-02
```

이 결과를 통해:

* 각 서버에 실제로 접속해서 명령이 수행되었는지

* 서버별로 다른 결과가 나오는지

* 대상 서버가 올바른지

확인할 수 있음.

### `command` 모듈 특징

`command` 모듈은 셸을 거치지 않고 명령을 실행함.

따라서 파이프(`|`), 리다이렉션(`>`), 변수 확장 같은 셸 문법은 기본적으로 사용할 수 없음.

즉, 단순 명령 실행에는 `command`가 더 안전하고 명확함.

---

## 1.14 원격 명령 실행: shell 모듈

셸 기능이 필요한 경우에는 `shell` 모듈을 사용함.

예:

```
ansible -i inventory.ini all -m shell -a "free -h | grep Mem"
```

이 명령은 각 서버의 메모리 정보를 출력함.

`shell` 모듈은 셸을 통해 명령을 실행하므로, 파이프나 리다이렉션 같은 기능 사용이 가능함.

다만 그만큼 예기치 않은 동작 가능성도 있으므로, 단순 명령에는 `command`, 셸 기능이 필요할 때만 `shell`을 쓰는 습관이 좋음.

---

## 1.15 권한 상승 옵션 `-b`

패키지 설치나 서비스 제어처럼 관리자 권한이 필요한 작업은 일반 사용자 권한으로 수행할 수 없음.

이때 사용하는 옵션이 `-b`임.

* `-b`는 `become`의 약자이며, 보통 sudo 권한 상승을 의미함.

예:

```
ansible -i inventory.ini web -m apt -a "name=nginx state=present update_cache=true" -b
```

이 명령은 `web` 그룹 서버에 대해 관리자 권한으로 nginx 패키지를 설치함.

옵션 의미를 자세히 보면:

* `web` : web 그룹 대상

* `m apt` : apt 모듈 사용

* `name=nginx` : nginx 패키지 지정

* `state=present` : 설치된 상태 보장

* `update_cache=true` : 패키지 목록 갱신

* `b` : sudo 권한으로 실행

---

## 1.16 서비스 제어: service 모듈

서비스 시작과 자동 시작 설정도 ad-hoc command로 가능함.

```
ansible -i inventory.ini web -m service -a "name=nginx state=started enabled=yes" -b
```

이 명령은 다음 의미를 가짐.

* nginx 서비스가 실행 중이어야 함

* 시스템 재부팅 후에도 자동 시작되도록 설정함

여기서 중요한 점은 Ansible이 단순히 `systemctl start nginx`를 실행하는 것이 아니라, 서비스가 **시작된 상태인지**를 기준으로 처리한다는 점임.

---

## 1.17 실습: 첫 번째 원격 제어 흐름

이 절에서는 제1장에서 배운 내용을 묶어 간단한 흐름으로 실습함.

### 실습 순서

### 1단계. 실습 디렉터리로 이동

```
cd ~/ansible-lab
```

### 2단계. inventory 확인

```
ansible-inventory -i inventory.ini --graph
```

### 3단계. 연결 테스트

```
ansible -i inventory.ini all -m ping
```

### 4단계. 호스트명 확인

```
ansible -i inventory.ini all -m command -a "hostname"
```

### 5단계. web 그룹에 nginx 설치

```
ansible -i inventory.ini web -m apt -a "name=nginx state=present update_cache=true" -b
```

### 6단계. nginx 서비스 시작

```
ansible -i inventory.ini web -m service -a "name=nginx state=started enabled=yes" -b
```

### 실습 목적

플레이북 작성 전 단계에서 Ansible이 어떻게 여러 서버를 원격 제어하는지 체감하는 데 목적이 있음.

* inventory로 대상 서버를 정의함

* Ansible 명령으로 여러 서버에 동시에 접속함

* 모듈을 통해 서버 상태를 변경함

* 관리자 권한이 필요한 작업은 `b`로 처리함

---

## 1.19 장 정리

이 장에서는 Ansible의 개념과 구조, 그리고 가장 기본적인 원격 제어 흐름을 학습했음.

핵심 정리:

* Ansible은 여러 서버를 일관되게 자동화하기 위한 도구임

* 관리 대상 서버에 에이전트를 설치하지 않고 SSH 기반으로 동작함

* control node와 managed node 구조를 사용함

* inventory를 통해 대상 서버를 정의함

* ad-hoc command로 연결 확인과 간단한 작업을 수행할 수 있음

* `ping`, `command`, `shell`, `apt`, `service` 모듈을 사용해 기본 원격 제어가 가능함

* 관리자 권한이 필요한 작업은 `-b` 옵션을 사용함

---