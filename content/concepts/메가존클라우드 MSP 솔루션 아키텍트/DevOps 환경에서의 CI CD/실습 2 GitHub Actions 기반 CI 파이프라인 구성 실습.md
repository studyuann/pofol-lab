---
title: "실습 2 GitHub Actions 기반 CI 파이프라인 구성 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "DevOps 환경에서의 CI CD"]
is_public: true
draft: false
---

# 실습 2. GitHub Actions 기반 CI 파이프라인 구성 실습

---

# 1. 실습 목표

1. push 시 워크플로우 실행

2. Python 코드 자동 실행

3. Python 테스트 자동화

4. 결과 파일 생성

5. 아티팩트 업로드

6. 브랜치별 실행 분기

7. Secret 사용

8. EC2 자동 배포

---

# 2. 실습 환경

## 준비물

* GitHub 계정

* Git 설치

* Python 3 설치

* VS Code 또는 편집기

* GitHub Repository 1개

* EC2 1대 SSH 접속 가능 상태 배포 실습 시 사용

---

# 3. 실습 1 가장 기본적인 GitHub Actions 실행

## 3.1 실습 폴더 생성

```
mkdir github-actions-python-lab
cd github-actions-python-lab
git init
```

---

## 3.2 README 파일 생성

```
echo "# github-actions-python-lab" > README.md
```

---

## 3.3 워크플로우 디렉터리 생성

```
mkdir -p .github/workflows
```

---

## 3.4 첫 번째 워크플로우 작성

```
vi .github/workflows/01-basic.yml
```

```
name: 01 Basic Workflow

on:
  push:
    branches:
      - main

jobs:
  hello:
    runs-on: ubuntu-latest

    steps:
      - name: 저장소 코드 가져오기
        uses: actions/checkout@v4

      - name: 메시지 출력
        run: echo "GitHub Actions Python Basic Workflow Running"

      - name: 현재 디렉터리 확인
        run: pwd

      - name: 파일 목록 확인
        run: ls -al
```

---

## 3.5 GitHub에 업로드

```
git add .
git commit -m "add basic workflow"
git branch -M main
git remote add origin https://github.com/계정명/github-actions-python-lab.git
git push -u origin main
```

---

## 3.6 확인

GitHub 저장소에서 아래 메뉴 이동

```
Actions
```

실행된 워크플로우를 확인한다.

---

# 4. 실습 2 Python 코드 자동 실행

## 4.1 Python 파일 생성

```
vi app.py
```

```
print("Hello from Python GitHub Actions")
```

---

## 4.2 워크플로우 작성

```
vi .github/workflows/02-python-run.yml
```

```
name: 02 Python Run Workflow

on:
  push:
    branches:
      - main

jobs:
  run-python:
    runs-on: ubuntu-latest

    steps:
      - name: 저장소 코드 가져오기
        uses: actions/checkout@v4

      - name: Python 설치
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Python 버전 확인
        run: python --version

      - name: Python 파일 실행
        run: python app.py
```

---

## 4.3 업로드 및 실행 확인

```
git add .
git commit -m "add python run workflow"
git push
```

---

# 5. 실습 3 Python 테스트 자동화

## 5.1 테스트용 코드 작성

### calc.py

```
vi calc.py
```

```
def add(a, b):
    return a + b
```

---

### test\_calc.py

```
vi test_calc.py
```

```
from calc import add

def test_add():
    assert add(2, 3) == 5
```

---

## 5.2 pytest 설치 파일 작성

```
vi requirements.txt
```

```
pytest
```

---

## 5.3 테스트 워크플로우 작성

```
vi .github/workflows/03-python-test.yml
```

```
name: 03 Python Test Workflow

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: 저장소 코드 가져오기
        uses: actions/checkout@v4

      - name: Python 설치
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: pip 업그레이드
        run: python -m pip install --upgrade pip

      - name: 패키지 설치
        run: pip install -r requirements.txt

      - name: 테스트 실행
        run: pytest
```

---

## 5.4 업로드

```
git add .
git commit -m "add python test workflow"
git push
```

---

# 6. 실습 4 결과 파일 생성하기

## 6.1 결과 파일 생성 스크립트 작성

```
vi generate_report.py
```

```
from datetime import datetime

with open("report.txt", "w", encoding="utf-8") as f:
    f.write("GitHub Actions Report\n")
    f.write(f"Generated at: {datetime.now()}\n")

print("report.txt 생성 완료")
```

---

## 6.2 워크플로우 작성

```
vi .github/workflows/04-generate-report.yml
```

```
name: 04 Generate Report Workflow

on:
  push:
    branches:
      - main

jobs:
  generate-report:
    runs-on: ubuntu-latest

    steps:
      - name: 저장소 코드 가져오기
        uses: actions/checkout@v4

      - name: Python 설치
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: 리포트 파일 생성
        run: python generate_report.py

      - name: 생성 결과 확인
        run: cat report.txt
```

---

# 7. 실습 5 아티팩트 업로드

## 7.1 워크플로우 수정

```
vi .github/workflows/05-upload-artifact.yml
```

```
name: 05 Upload Artifact Workflow

on:
  push:
    branches:
      - main

jobs:
  upload-artifact:
    runs-on: ubuntu-latest

    steps:
      - name: 저장소 코드 가져오기
        uses: actions/checkout@v4

      - name: Python 설치
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: 리포트 생성
        run: python generate_report.py

      - name: 리포트 파일 업로드
        uses: actions/upload-artifact@v4
        with:
          name: python-report
          path: report.txt
```

---

## 7.2 확인

실행된 워크플로우 상세 화면에서 **Artifacts** 영역 확인

---

# 8. 실습 6 브랜치별 실행 분기

## 8.1 워크플로우 작성

```
vi .github/workflows/06-branch.yml
```

```
name: 06 Branch Workflow

on:
  push:
    branches:
      - main
      - dev

jobs:
  branch-check:
    runs-on: ubuntu-latest

    steps:
      - name: 브랜치 이름 출력
        run: echo "Current branch is ${{ github.ref_name }}"

      - name: main 브랜치일 때만 실행
        if: github.ref_name == 'main'
        run: echo "This is main branch"

      - name: dev 브랜치일 때만 실행
        if: github.ref_name == 'dev'
        run: echo "This is dev branch"
```

---

## 8.2 dev 브랜치 생성 후 테스트

```
git checkout -b dev
echo "dev test" >> README.md
git add .
git commit -m "test dev workflow"
git push -u origin dev
```

---

# 9. 실습 7 Secret 사용

## 9.1 GitHub Secret 등록

GitHub 저장소에서 아래 경로 이동

```
Settings → Secrets and variables → Actions → New repository secret
```

예시 등록

```
SECRET_MESSAGE = hello-github-secret
```

---

## 9.2 Python 파일 작성

```
vi secret_app.py
```

```
import os

secret_value = os.getenv("SECRET_MESSAGE")

if secret_value:
    print("SECRET_MESSAGE 값 읽기 성공")
else:
    print("SECRET_MESSAGE 값 없음")
```

---

## 9.3 워크플로우 작성

```
vi .github/workflows/07-secret.yml
```

```
name: 07 Secret Workflow

on:
  push:
    branches:
      - main

jobs:
  use-secret:
    runs-on: ubuntu-latest

    steps:
      - name: 저장소 코드 가져오기
        uses: actions/checkout@v4

      - name: Python 설치
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Secret 사용 실행
        env:
          SECRET_MESSAGE: ${{ secrets.SECRET_MESSAGE }}
        run: python secret_app.py
```

---

# 10. 실습 8 EC2 자동 배포

이 실습은 **GitHub Actions에서 Python 파일을 EC2로 복사하고 원격 실행**하는 방식으로 진행한다.

---

## 10.1 EC2 준비

EC2에 Python 설치 확인

```
python3 --version
```

없으면 설치

### Ubuntu

```
sudo apt update
sudo apt install -y python3
```

### Amazon Linux

```
sudo dnf install -y python3
```

---

## 10.2 배포 대상 파일 작성

```
vi deploy_app.py
```

```
print("EC2 deployed python application running")
```

---

## 10.3 GitHub Secrets 등록

다음 값을 저장소 Secret에 등록

```
EC2_HOST
EC2_USER
EC2_KEY
```

예

* `EC2_HOST` : 퍼블릭 IP 또는 도메인

* `EC2_USER` : ubuntu 또는 ec2-user

* `EC2_KEY` : pem 파일 전체 내용

---

## 10.4 배포 워크플로우 작성

```
vi .github/workflows/08-deploy-ec2.yml
```

```
name: 08 Deploy to EC2

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: 저장소 코드 가져오기
        uses: actions/checkout@v4

      - name: SSH 키 파일 생성
        run: |
          echo "${{ secrets.EC2_KEY }}" > private_key.pem
          chmod 600 private_key.pem

      - name: EC2 접속 테스트
        run: |
          ssh -o StrictHostKeyChecking=no -i private_key.pem ${{ secrets.EC2_USER }}@${{ secrets.EC2_HOST }} "echo connected"

      - name: 파일 전송
        run: |
          scp -o StrictHostKeyChecking=no -i private_key.pem deploy_app.py ${{ secrets.EC2_USER }}@${{ secrets.EC2_HOST }}:/home/${{ secrets.EC2_USER }}/

      - name: 원격 실행
        run: |
          ssh -o StrictHostKeyChecking=no -i private_key.pem ${{ secrets.EC2_USER }}@${{ secrets.EC2_HOST }} "python3 /home/${{ secrets.EC2_USER }}/deploy_app.py"
```

---

# 11. 실습 9 requirements 설치 후 Flask 실행으로 확장

단순 Python 파일 실행이 아니라 웹 애플리케이션으로 확장하는 단계다.

---

## 11.1 Flask 애플리케이션 작성

```
vi flask_app.py
```

```
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello from Flask GitHub Actions"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

---

## 11.2 requirements.txt 수정

```
pytest
flask
```

---

## 11.3 EC2에서 실행 명령 변경 예시

```
      - name: 원격 배포 및 실행
        run: |
          ssh -o StrictHostKeyChecking=no -i private_key.pem ${{ secrets.EC2_USER }}@${{ secrets.EC2_HOST }} "
            pip3 install flask &&
            nohup python3 /home/${{ secrets.EC2_USER }}/flask_app.py > app.log 2>&1 &
          "
```

---

---

# 12. 실습용 최종 디렉터리 예시

```
github-actions-python-lab/
├── .github/
│   └── workflows/
│       ├── 01-basic.yml
│       ├── 02-python-run.yml
│       ├── 03-python-test.yml
│       ├── 04-generate-report.yml
│       ├── 05-upload-artifact.yml
│       ├── 06-branch.yml
│       ├── 07-secret.yml
│       └── 08-deploy-ec2.yml
├── README.md
├── app.py
├── calc.py
├── test_calc.py
├── generate_report.py
├── secret_app.py
├── deploy_app.py
├── flask_app.py
└── requirements.txt
```

---