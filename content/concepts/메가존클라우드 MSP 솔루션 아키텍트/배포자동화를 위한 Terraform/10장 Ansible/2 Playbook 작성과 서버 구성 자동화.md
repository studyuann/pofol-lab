---
title: "2 Playbook 작성과 서버 구성 자동화"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "배포자동화를 위한 Terraform", "10장 Ansible"]
is_public: true
draft: false
---

# 2. Playbook 작성과 서버 구성 자동화

## 2.1 Playbook의 필요성

제1장에서는 ad-hoc command를 이용해 여러 서버에 명령을 실행하는 방법을 살펴보았음.

ad-hoc command는 빠르게 테스트하거나 1회성 작업을 처리할 때 매우 유용함. 예를 들어 연결 확인, 패키지 1회 설치, 서비스 상태 점검 같은 작업은 ad-hoc command만으로도 충분히 수행할 수 있음.

하지만 실제 운영 환경에서는 단순 1회성 작업보다 **반복 가능하고, 재사용 가능하며, 순서가 있는 작업 절차**가 더 중요함.

예를 들어 웹서버를 구성한다고 가정하면 보통 다음 작업이 함께 필요함.

* 패키지 목록 갱신

* nginx 설치

* nginx 서비스 시작

* 자동 시작 등록

* index.html 파일 배포

이런 절차를 매번 ad-hoc command 여러 줄로 실행하면 다음과 같은 문제가 생김.

* 실행 순서를 사람이 기억해야 함

* 명령 일부가 누락될 수 있음

* 재사용이 불편함

* 작업 기록과 공유가 어려움

* 여러 단계 작업을 하나의 자동화 절차로 관리하기 어려움

이 문제를 해결하기 위해 사용하는 것이 **playbook**임.

playbook은 Ansible 작업을 YAML 형식으로 순서 있게 기술한 파일임.

즉, 사람이 한 줄씩 명령을 입력하는 것이 아니라, 서버가 어떤 상태가 되어야 하는지 문서처럼 정의해두고 반복 실행하는 방식임.

---

## 2.2 Playbook의 개념

playbook은 Ansible 자동화의 핵심 구성 요소임.

playbook 안에는 다음과 같은 내용이 들어감.

* 어떤 서버를 대상으로 할 것인지

* 관리자 권한이 필요한지

* 어떤 작업을 어떤 순서로 수행할 것인지

* 설치, 복사, 생성, 시작 같은 작업을 어떤 모듈로 처리할 것인지

playbook은 하나 이상의 **play**로 구성될 수 있고, 각 play는 하나 이상의 **task**를 가짐.

간단히 표현하면 다음과 같은 구조임.

```
Playbook
 └─ Play
     ├─ 대상 서버(hosts)
     ├─ 권한 상승 여부(become)
     └─ Tasks
         ├─ Task 1
         ├─ Task 2
         └─ Task 3
```

즉, playbook은 자동화 작업의 실행 계획서라고 볼 수 있음.

---

## 2.3 YAML 문법 기초

Ansible playbook은 YAML 형식으로 작성함.

따라서 YAML 문법을 정확히 이해하는 것이 매우 중요함.

YAML은 사람이 읽기 쉬운 데이터 표현 형식이지만, 들여쓰기 규칙이 엄격함.

특히 초보자가 가장 많이 실수하는 부분이 들여쓰기임.

### 2.3.1 YAML의 기본 규칙

### 1) `key: value` 형식 사용

YAML은 기본적으로 다음과 같은 구조를 사용함.

```
name: nginx
state: present
```

### 2) 리스트는 기호로 표현

여러 항목을 나열할 때는 `-`를 사용함.

```
packages:
  - vim
  - curl
  - git
```

### 3) 들여쓰기가 구조를 결정함

YAML은 중괄호 대신 들여쓰기로 계층 구조를 표현함.

```
tasks:
  - name: Install nginx
    ansible.builtin.apt:
      name: nginx
      state: present
```

위 예시에서 `name`, `ansible.builtin.apt`는 같은 task에 속함.

그리고 `name: nginx`, `state: present`는 `apt` 모듈의 인수임.

### 2.3.2 들여쓰기 주의점

YAML은 탭보다 **공백 들여쓰기**를 사용하는 것이 원칙임.

보통 2칸 또는 4칸 공백을 사용하지만, 한 파일 안에서는 일관되게 유지해야 함.

예를 들어 아래처럼 들여쓰기가 틀리면 오류가 발생함.

```
tasks:
- name: Install nginx
  ansible.builtin.apt:
    name: nginx
    state: present
```

형식에 따라 동작할 수는 있지만, 교육용이나 협업용 문서에서는 구조가 흐트러져 보이므로 권장되지 않음.

가장 안전한 습관은 `tasks:` 아래에서 각 task를 한 단계 더 들여쓰는 것임.

---

## 2.4 Playbook 기본 구조

가장 기본적인 playbook 구조는 다음과 같음.

```
---
- name: Example play
  hosts: web
  become: true

  tasks:
    - name: Install nginx
      ansible.builtin.apt:
        name: nginx
        state: present
```

이 구조를 항목별로 자세히 보면 다음과 같음.

### `---`

YAML 문서의 시작을 나타냄.

반드시 필요한 것은 아니지만, playbook의 시작을 명확히 하기 위해 보통 넣음.

### `name: Example play`

하나의 play를 정의함.

여기서 `name`은 사람이 읽기 쉬운 설명용 항목임.

playbook 실행 시 작업 흐름을 이해하는 데 도움이 됨.

### `hosts: web`

이 play가 어떤 서버를 대상으로 실행될지 지정함.

inventory에 정의된 `web` 그룹을 의미함.

### `become: true`

관리자 권한으로 작업하겠다는 의미임.

패키지 설치, 서비스 시작, 시스템 파일 변경은 보통 일반 사용자 권한으로 수행할 수 없으므로 자주 사용함.

### `tasks:`

실제 수행할 작업 목록이 들어가는 영역임.

### `name: Install nginx`

개별 task의 이름임.

실행 로그에 표시되므로, 작업 내용을 명확히 적는 것이 좋음.

### `ansible.builtin.apt`

사용할 모듈을 지정함.

여기서는 Ubuntu 계열 패키지 설치 모듈인 `apt`를 사용함.

---

## 2.5 첫 번째 Playbook 작성

이제 가장 간단한 playbook을 직접 작성해봄.

목표는 `web` 그룹 서버에 nginx를 설치하고 서비스를 시작하는 것임.

### 파일명

`install-nginx.yml`

### 내용

```
---
- name: Install nginx on web servers
  hosts: web
  become: true

  tasks:
    - name: Update apt cache
      ansible.builtin.apt:
        update_cache: true

    - name: Install nginx package
      ansible.builtin.apt:
        name: nginx
        state: present

    - name: Start nginx service
      ansible.builtin.service:
        name: nginx
        state: started
        enabled: true
```

### 각 task 설명

### `Update apt cache`

패키지 목록을 최신 상태로 갱신함.

Ubuntu에서 `apt update`와 유사한 역할을 수행함.

### `Install nginx package`

nginx 패키지가 설치된 상태를 보장함.

이미 설치되어 있다면 불필요한 재설치를 하지 않음.

### `Start nginx service`

nginx 서비스가 실행 중이어야 한다는 의미임.

`enabled: true`를 함께 사용해 부팅 후 자동 시작도 설정함.

---

## 2.6 Playbook 실행

작성한 playbook은 `ansible-playbook` 명령으로 실행함.

```
ansible-playbook -i inventory.ini install-nginx.yml
```

이 명령의 의미는 다음과 같음.

* `ansible-playbook` : playbook 실행 명령

* `i inventory.ini` : 사용할 inventory 파일 지정

* `install-nginx.yml` : 실행할 playbook 파일

정상 실행되면 다음과 비슷한 출력이 나타남.

```
PLAY [Install nginx on web servers] ****************************************

TASK [Update apt cache] ****************************************************
changed: [10.10.10.11]
changed: [10.10.10.12]

TASK [Install nginx package] ***********************************************
changed: [10.10.10.11]
changed: [10.10.10.12]

TASK [Start nginx service] *************************************************
changed: [10.10.10.11]
changed: [10.10.10.12]

PLAY RECAP ****************************************************************
10.10.10.11 : ok=3  changed=3  unreachable=0  failed=0
10.10.10.12 : ok=3  changed=3  unreachable=0  failed=0
```

---

## 2.7 실행 결과 해석

playbook 실행 결과는 매우 중요한 학습 포인트임.

단순히 성공 여부만 보는 것이 아니라, 각 상태가 어떤 의미인지 이해해야 함.

### `ok`

작업이 정상적으로 처리되었고, 원하는 상태였음을 의미함.

예를 들어 이미 nginx가 설치되어 있다면 `ok`로 표시될 수 있음.

### `changed`

작업 실행 결과 실제 변경이 발생했음을 의미함.

예를 들어 nginx가 설치되지 않은 서버에 새로 설치되었다면 `changed`가 출력됨.

### `unreachable`

SSH 연결 실패 등으로 대상 서버에 접속할 수 없음을 의미함.

### `failed`

작업 실행 자체가 실패했음을 의미함.

예를 들어 잘못된 패키지명, 권한 문제, 문법 오류 등이 있을 때 나타날 수 있음.

### `PLAY RECAP`

마지막 요약 영역에서는 서버별로 전체 실행 상태를 확인할 수 있음.

예:

```
10.10.10.11 : ok=3  changed=3  unreachable=0  failed=0
```

이 의미는 다음과 같음.

* 총 3개 task가 정상 처리되었음

* 그중 3개에서 실제 변경이 발생했음

* 접속 실패 없음

* 실행 실패 없음

---

## 2.8 멱등성 확인

Ansible playbook의 중요한 특성 중 하나는 멱등성임.

이를 직접 확인하기 위해 같은 playbook을 다시 한 번 실행함.

```
ansible-playbook -i inventory.ini install-nginx.yml
```

이미 nginx가 설치되어 있고 서비스가 시작된 상태라면, 두 번째 실행에서는 대부분 다음과 같이 보일 가능성이 큼.

```
TASK [Update apt cache] ****************************************************
ok: [10.10.10.11]
ok: [10.10.10.12]

TASK [Install nginx package] ***********************************************
ok: [10.10.10.11]
ok: [10.10.10.12]

TASK [Start nginx service] *************************************************
ok: [10.10.10.11]
ok: [10.10.10.12]
```

즉, playbook을 반복 실행하더라도 이미 원하는 상태이면 불필요한 변경이 일어나지 않음.

이 특성 덕분에 운영 자동화에서 playbook을 자신 있게 반복 실행할 수 있음.

---

## 2.9 주요 모듈 이해

Playbook은 결국 여러 모듈을 조합해 작성함.

이 장에서는 실습에서 자주 사용하는 기본 모듈들을 익힘.

### 2.9.1 `apt` 모듈

Ubuntu, Debian 계열에서 패키지 설치와 제거를 담당함.

주요 인수:

* `name` : 패키지명

* `state: present` : 설치 상태 보장

* `state: absent` : 제거 상태 보장

* `update_cache: true` : 패키지 목록 갱신

예시:

```
- name: Install vim
  ansible.builtin.apt:
    name: vim
    state: present
    update_cache: true
```

---

### 2.9.2 `service` 모듈

서비스 시작, 중지, 재시작, 자동 시작 설정을 담당함.

주요 인수:

* `name` : 서비스명

* `state: started` : 실행 중 상태

* `state: stopped` : 중지 상태

* `state: restarted` : 재시작 수행

* `enabled: true` : 부팅 후 자동 시작

예시:

```
- name: Ensure nginx is running
  ansible.builtin.service:
    name: nginx
    state: started
    enabled: true
```

---

### 2.9.3 `copy` 모듈

제어 노드에 있는 파일을 관리 대상 서버로 복사함.

주요 인수:

* `src` : 원본 파일 경로

* `dest` : 대상 서버 경로

* `mode` : 파일 권한

예시:

```
- name: Copy index file
  ansible.builtin.copy:
    src: index.html
    dest: /var/www/html/index.html
    mode: '0644'
```

---

### 2.9.4 `file` 모듈

파일, 디렉터리, 심볼릭 링크의 상태를 관리함.

주요 인수:

* `path` : 대상 경로

* `state: directory` : 디렉터리 생성 상태

* `state: touch` : 파일 생성

* `mode` : 권한 지정

예시:

```
- name: Create application directory
  ansible.builtin.file:
    path: /opt/myapp
    state: directory
    mode: '0755'
```

---

### 2.9.5 `user` 모듈

사용자 계정 생성과 관리에 사용함.

주요 인수:

* `name` : 사용자명

* `shell` : 로그인 셸

* `create_home: true` : 홈 디렉터리 생성

* `groups` : 그룹 지정

예시:

```
- name: Create deploy user
  ansible.builtin.user:
    name: deploy
    shell: /bin/bash
    create_home: true
```

---

### 2.9.6 `lineinfile` 모듈

파일 안의 특정 행을 찾아 수정하거나 추가할 때 사용함.

예시:

```
- name: Disable root login
  ansible.builtin.lineinfile:
    path: /etc/ssh/sshd_config
    regexp: '^PermitRootLogin'
    line: 'PermitRootLogin no'
```

이 모듈은 설정파일 전체를 교체하지 않고 특정 라인만 수정할 때 매우 유용함.

---

## 2.10 실습: 사용자 생성 Playbook

이제 `user` 모듈을 사용해 사용자 계정을 생성해봄.

### 파일명

`create-user.yml`

### 내용

```
---
- name: Create deploy user
  hosts: all
  become: true

  tasks:
    - name: Create deploy account
      ansible.builtin.user:
        name: deploy
        shell: /bin/bash
        create_home: true
```

### 실행

```
ansible-playbook -i inventory.ini create-user.yml
```

### 확인

```
ansible -i inventory.ini all -m command -a "id deploy"
```

이 결과를 통해 각 서버에 `deploy` 계정이 생성되었는지 확인할 수 있음.

---

## 2.11 실습: 디렉터리 생성 Playbook

이번에는 `file` 모듈을 사용해 디렉터리를 생성함.

### 파일명

`create-directory.yml`

### 내용

```
---
- name: Create application directory
  hosts: all
  become: true

  tasks:
    - name: Create /opt/myapp directory
      ansible.builtin.file:
        path: /opt/myapp
        state: directory
        mode: '0755'
```

### 실행

```
ansible-playbook -i inventory.ini create-directory.yml
```

### 확인

```
ansible -i inventory.ini all -m command -a "ls -ld /opt/myapp"
```

---

## 2.12 실습: 파일 복사 Playbook

이번에는 간단한 HTML 파일을 복사함.

### `index.html` 파일 작성

```
<html>
  <body>
    <h1>Ansible Web Server</h1>
    <p>This page was deployed by Ansible.</p>
  </body>
</html>
```

### Playbook 작성

파일명: `deploy-index.yml`

```
---
- name: Deploy index page
  hosts: web
  become: true

  tasks:
    - name: Copy index file
      ansible.builtin.copy:
        src: index.html
        dest: /var/www/html/index.html
        mode: '0644'
```

### 실행

```
ansible-playbook -i inventory.ini deploy-index.yml
```

### 확인

브라우저에서 웹서버 IP로 접속하거나, 다음 명령으로 확인할 수 있음.

```
ansible -i inventory.ini web -m command -a "cat /var/www/html/index.html"
```

---

## 2.13 변수의 필요성

지금까지 작성한 playbook은 동작은 하지만 값이 직접 코드 안에 들어가 있음.

예를 들어 패키지명, 사용자명, 디렉터리 경로가 모두 고정되어 있음.

이 상태에서는 다음과 같은 문제가 생길 수 있음.

* 비슷한 playbook을 환경마다 새로 만들어야 함

* 패키지명만 바뀌어도 파일을 수정해야 함

* 재사용성이 떨어짐

이 문제를 해결하기 위해 사용하는 것이 **변수(variable)** 임.

변수는 값을 이름으로 치환해서 playbook을 더 유연하게 만들 수 있게 해줌.

---

## 2.14 변수 사용

가장 간단한 방법은 play 안에 `vars:` 영역을 두고 변수를 선언하는 것임.

예시:

```
---
- name: Install multiple packages using variable
  hosts: web
  become: true

  vars:
    web_packages:
      - nginx
      - git
      - curl

  tasks:
    - name: Install packages
      ansible.builtin.apt:
        name: "{{ web_packages }}"
        state: present
        update_cache: true
```

여기서:

* `web_package` : 변수명

* `"{{ web_package }}"` : 변수 참조 구문

Ansible에서 변수 참조는 Jinja2 문법인 `{{ }}`를 사용함.

---

## 2.15 Facts 개념

Ansible은 관리 대상 서버의 다양한 시스템 정보를 자동으로 수집할 수 있음.

이 정보를 **facts**라고 함.

facts에는 다음과 같은 정보가 포함될 수 있음.

* 운영체제 종류

* 배포판 이름

* 호스트명

* IP 주소

* CPU 정보

* 메모리 정보

* 네트워크 인터페이스 정보

이 정보는 playbook 안에서 조건문, 변수 치환, 템플릿 작성 등에 활용할 수 있음.

---

## 2.16 Facts 확인

facts를 확인하려면 `setup` 모듈을 사용할 수 있음.

```
ansible -i inventory.ini all -m setup
```

출력이 매우 길기 때문에 특정 정보만 필터링해서 보는 것이 좋음.

예:

```
ansible -i inventory.ini all -m setup -a "filter=ansible_distribution*"
```

예상 출력:

```
10.10.10.11 | SUCCESS => {
    "ansible_facts": {
        "ansible_distribution": "Ubuntu",
        "ansible_distribution_major_version": "22",
        "ansible_distribution_version": "22.04"
    },
    "changed": false
}
```

이 결과를 통해 대상 서버가 어떤 운영체제인지 알 수 있음.

---

## 2.17 반복문 사용

실무에서는 패키지 1개만 설치하는 경우보다 여러 개를 함께 설치하는 경우가 더 많음.

이때 사용하는 것이 `loop`임.

예시:

```
---
- name: Install common packages
  hosts: all
  become: true

  tasks:
    - name: Install packages
      ansible.builtin.apt:
        name: "{{ item }}"
        state: present
      loop:
        - vim
        - curl
        - git
```

여기서 `item`은 반복 중 현재 항목을 의미함.

즉, 위 task는 다음 작업을 순서대로 수행하는 것과 같음.

* vim 설치

* curl 설치

* git 설치

하지만 코드는 훨씬 짧고 관리가 쉬움.

---

## 2.18 조건문 사용

Ansible은 모든 서버에 같은 작업을 수행할 수도 있지만, 특정 조건을 만족하는 서버에만 작업을 수행하도록 만들 수도 있음.

이때 사용하는 것이 `when` 조건문임.

예를 들어 Ubuntu 서버에서만 nginx를 설치하려면 다음처럼 작성할 수 있음.

```
---
- name: Install nginx only on Ubuntu
  hosts: all
  become: true

  tasks:
    - name: Install nginx package
      ansible.builtin.apt:
        name: nginx
        state: present
      when: ansible_distribution == "Ubuntu"
```

이 코드는 facts 정보 중 `ansible_distribution` 값이 `"Ubuntu"`일 때만 실행됨.

조건문은 이후 운영체제별 분기, 환경별 차등 설정, 특정 호스트 제외 처리 등에 매우 유용하게 쓰임.

---

## 2.19 실습: 변수, 반복문, 조건문 종합

### 파일명

`common-setup.yml`

### 내용

```
---
- name: Common package setup
  hosts: all
  become: true

  vars:
    common_packages:
      - vim
      - curl
      - git

  tasks:
    - name: Install common packages on Ubuntu
      ansible.builtin.apt:
        name: "{{ item }}"
        state: present
        update_cache: true
      loop: "{{ common_packages }}"
      when: ansible_distribution == "Ubuntu"
```

### 실행

```
ansible-playbook -i inventory.ini common-setup.yml
```

### 목적

이 실습을 통해 다음을 한 번에 경험할 수 있음.

* 변수 사용

* 리스트 변수 사용

* 반복문 적용

* 조건문 적용

* facts 활용

---

## 2.20 Playbook 작성 시 주의사항

Playbook 입문 단계에서 자주 발생하는 실수를 정리하면 다음과 같음.

### 2.20.1 들여쓰기 오류

YAML은 들여쓰기가 구조를 결정하므로, 공백 수가 틀리면 오류가 발생하기 쉬움.

### 2.20.2 모듈 인수 위치 오류

모듈 아래에 들어가야 할 항목이 task 수준에 잘못 들어가는 경우가 있음.

예를 들어 아래는 잘못된 예시임.

```
- name: Install nginx
  ansible.builtin.apt:
  name: nginx
  state: present
```

`name`, `state`가 `apt` 모듈 아래로 들여쓰기되지 않았기 때문에 오류가 발생함.

### 2.20.3 변수 참조 문법 오류

변수 참조 시 `{{ }}`를 빠뜨리거나 따옴표 처리 방식을 잘못 쓰는 경우가 있음.

### 2.20.4 대상 그룹 지정 실수

`hosts: web`로 실행해야 하는데 `hosts: all`로 해버리면 원하지 않는 서버까지 작업이 적용될 수 있음.

즉, playbook은 단순히 문법만 맞는다고 끝나는 것이 아니라, **대상 범위와 작업 의도까지 정확해야 함**.

---

## 2.21 장 정리

이 장에서는 Ansible playbook의 기본 구조와 작성 방법을 학습했음.

핵심 정리:

* ad-hoc command는 빠르지만, 반복 가능하고 구조적인 자동화에는 playbook이 적합함

* playbook은 YAML 형식으로 작성함

* `hosts`, `tasks`, `become`, `name`의 의미를 이해해야 함

* `apt`, `service`, `copy`, `file`, `user`, `lineinfile` 같은 주요 모듈을 사용할 수 있어야 함

* playbook 실행 결과에서 `ok`, `changed`, `failed`, `unreachable`를 해석할 수 있어야 함

* 멱등성 개념을 이해하고 반복 실행 결과를 확인해야 함

* 변수, facts, 반복문, 조건문을 활용하면 playbook의 재사용성과 유연성을 높일 수 있음

**playbook을 직접 작성하여 서버의 패키지, 서비스, 파일, 사용자, 디렉터리 상태를 자동으로 구성할 수 있어야 함**.