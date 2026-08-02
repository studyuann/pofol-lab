---
title: "실습 시작 스크립트(Startup Script)와 메타데이터(Metadata)를 활용"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Google 클라우드 핵심 서비스"]
is_public: true
draft: false
---

# 실습. 시작 스크립트(Startup Script)와 메타데이터(Metadata)를 활용

### 1. 시나리오

* **메타데이터**: `user_name`과 `bg_color`라는 키(Key)를 설정합니다.

* **시작 스크립트**: 부팅 시 메타데이터 서버에서 위 두 값을 읽어와 `index.html` 파일을 동적으로 생성합니다.

---

### 2. 시작 스크립트 작성 (코드)

VM 생성 시 '시작 스크립트' 란에 아래 내용을 복사하여 붙여넣습니다.

```
#!/bin/bash
# 1. 패키지 업데이트 및 Nginx 설치
apt-get update -y
apt-get install -y nginx

# 2. 메타데이터 서버에서 커스텀 값 가져오기
# -H "Metadata-Flavor: Google" 헤더는 GCP 메타데이터 호출 시 필수입니다.
USER_NAME=$(curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/attributes/user_name)
BG_COLOR=$(curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/attributes/bg_color)

# 3. 가져온 메타데이터를 사용하여 웹 페이지 생성
cat <<EOF > /var/www/html/index.html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>메타데이터 실습</title>
    <style>
        body { 
            font-family: "Malgun Gothic", sans-serif; 
            text-align: center; 
            margin-top: 100px; 
            background-color: ${BG_COLOR:-white}; 
        }
        .card {
            background: white;
            display: inline-block;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>안녕하세요, ${USER_NAME:-사용자}님! 👋</h1>
        <p>이 페이지는 VM <b>시작 스크립트</b>를 통해 생성되었습니다.</p>
        <p>설정된 배경색: <code>${BG_COLOR:-default}</code></p>
    </div>
</body>
</html>
EOF

# 4. Nginx 실행
systemctl restart nginx
```

---

### 3. VM 생성 시 설정 방법

1. **GCP 콘솔** > **Compute Engine** > **VM 인스턴스 만들기**로 이동합니다.

2. **관리(Management)** 섹션을 찾습니다.

3. **메타데이터(Metadata)** 항목에서 '항목 추가'를 눌러 다음 두 가지를 입력합니다.
   * 키: `user_name` / 값: `홍길동` (원하는 이름)
   * 키: `bg_color` / 값: `lightblue` (또는 `#ffcc00` 같은 색상 코드)

4. 바로 위 **자동화(Automation)** > **시작 스크립트(Startup script)** 박스에 위에서 작성한 쉘 스크립트 코드를 붙여넣습니다.

5. **만들기**를 클릭합니다.

---

### 4. 결과 확인 및 메타데이터의 장점

* **확인**: VM 생성이 완료된 후 **외부 IP**로 접속하면, 배경이 하늘색(lightblue)이고 "안녕하세요, 홍길동님!"이 적힌 페이지가 뜹니다.

* **실습 포인트 (수정해보기)**:
  1. 새로운 VM을 하나 더 만듭니다.
  2. **시작 스크립트는 똑같이** 넣습니다.
  3. **메타데이터 값만** `user_name: 김철수`, `bg_color: lightpink`로 바꿔서 만듭니다.
  4. 두 번째 VM의 IP로 접속하면 분홍색 배경의 김철수님 페이지가 뜹니다.

이 방식이 중요한 이유는 **"코드(스크립트)와 데이터(메타데이터)의 분리"** 때문입니다.

* 웹 서버를 설정하는 복잡한 로직은 스크립트(코드)에 한 번만 잘 짜두고,

* 서버마다 달라야 하는 정보(DB 접속 정보, 환경 이름, 사용자 설정 등)만 메타데이터로 관리하면 관리 효율성이 극대화됩니다.