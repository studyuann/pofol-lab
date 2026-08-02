---
title: "프론트엔드, FastAPI, MariaDB, boto3를 이용한 로그인 기반 AWS 운영"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "클라우드 자동화를 위한 파이썬 프로그래밍", "5장 AWS 운영 보안 점검 자동화"]
is_public: true
draft: false
---

# 프론트엔드, FastAPI, MariaDB, boto3를 이용한 로그인 기반 AWS 운영 자동화

---

[![](%ED%94%84%EB%A1%A0%ED%8A%B8%EC%97%94%EB%93%9C,%20FastAPI,%20MariaDB,%20boto3%EB%A5%BC%20%EC%9D%B4%EC%9A%A9%ED%95%9C%20%EB%A1%9C%EA%B7%B8%EC%9D%B8%20%EA%B8%B0%EB%B0%98%20AWS%20%EC%9A%B4%EC%98%81%20/image.png)](%ED%94%84%EB%A1%A0%ED%8A%B8%EC%97%94%EB%93%9C,%20FastAPI,%20MariaDB,%20boto3%EB%A5%BC%20%EC%9D%B4%EC%9A%A9%ED%95%9C%20%EB%A1%9C%EA%B7%B8%EC%9D%B8%20%EA%B8%B0%EB%B0%98%20AWS%20%EC%9A%B4%EC%98%81%20/image.png)

## 1. 실습 주제

이번 실습은 **Python을 이용한 클라우드 서비스 운영 자동화**를 단순 스크립트 수준이 아니라, 실제 운영 도구에 가까운 구조로 구현하는 실습이다.

구현 목표는 다음과 같다.

```
로그인 사용자
  ↓
프론트엔드 랜딩페이지
  ↓
FastAPI 백엔드
  ↓
MariaDB 사용자 DB 조회
  ↓
JWT 인증
  ↓
사용자 role 확인
  ↓
IAM Role AssumeRole
  ↓
EC2 / S3 운영 자동화
```

이번 실습은 앞에서 만든 IAM Role 실습과 이어진다.

앞 실습에서 생성한 Role은 다음과 같다.

```
app-viewer-role
app-operator-role
app-admin-role
```

각 Role은 서로 다른 권한을 가진다.

| 로그인 사용자 role | IAM Role | 주요 권한 |
| --- | --- | --- |
| `viewer` | `app-viewer-role` | EC2/S3 조회 |
| `operator` | `app-operator-role` | EC2 조회, 시작, 중지 |
| `admin` | `app-admin-role` | EC2 운영 + S3 업로드 |

---

# 2. 실습 목표

이번 실습을 완료하면 다음 구조를 직접 구현할 수 있다.

```
1. MariaDB에 사용자 정보를 저장한다.
2. FastAPI에서 DB 기반 로그인 기능을 구현한다.
3. 비밀번호는 평문이 아니라 bcrypt 해시로 저장한다.
4. 로그인 성공 시 JWT Access Token을 발급한다.
5. 프론트엔드는 JWT를 localStorage에 저장한다.
6. 프론트엔드는 API 요청 시 Authorization 헤더에 JWT를 포함한다.
7. FastAPI는 JWT를 검증해 현재 로그인 사용자를 식별한다.
8. 사용자의 role에 따라 AWS IAM Role ARN을 선택한다.
9. FastAPI는 sts:AssumeRole을 호출해 임시 자격 증명을 발급받는다.
10. 임시 자격 증명으로 EC2와 S3를 제어한다.
11. 사용자 role별 권한 차이를 웹 화면에서 확인한다.
```

---

# 3. 실습 결과 화면 구성

최종 프론트엔드 화면은 다음 영역으로 구성한다.

```
[로그인 영역]
- 사용자 ID 입력
- 비밀번호 입력
- 로그인 버튼

[사용자 정보 영역]
- 현재 로그인 사용자
- 사용자 role
- 로그아웃 버튼

[EC2 운영 영역]
- EC2 인스턴스 목록 조회
- EC2 시작
- EC2 중지

[S3 운영 영역]
- S3 버킷 목록 조회
- 버킷 내 객체 목록 조회
- S3 파일 업로드

[결과 메시지 영역]
- API 응답 결과 출력
- 권한 오류 메시지 출력
```

---

# 4. 전체 아키텍처

```
Browser
  |
  | 1. 로그인 요청
  v
FastAPI /auth/login
  |
  | 2. MariaDB users 테이블 조회
  v
MariaDB
  |
  | 3. 비밀번호 검증 후 JWT 발급
  v
Browser localStorage
  |
  | 4. Authorization: Bearer <token>
  v
FastAPI 보호 API
  |
  | 5. JWT 검증
  | 6. 사용자 role 확인
  | 7. IAM Role ARN 선택
  v
AWS STS AssumeRole
  |
  | 8. 임시 자격 증명 발급
  v
boto3 EC2/S3 Client
  |
  | 9. EC2/S3 운영
  v
AWS Resources
```

---

# 5. 실습 전제

## 5.1 AWS Role 사전 준비

아래 IAM Role이 이미 존재해야 한다.

```
app-viewer-role
app-operator-role
app-admin-role
```

각 Role의 Trust Policy에는 현재 FastAPI를 실행하는 IAM Principal이 들어가 있어야 한다.

로컬 실습에서는 IAM User가 Principal이다.

예:

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "TrustLocalIamUser",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::471166314777:user/instructor"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

---

## 5.2 현재 AWS Profile 확인

```
aws sts get-caller-identity --profile instructor
```

예상 출력:

```
{
    "UserId": "AIDAxxxxxxxxxxxxx",
    "Account": "471166314777",
    "Arn": "arn:aws:iam::471166314777:user/instructor"
}
```

여기서 `Arn` 값이 IAM Role의 Trust Policy Principal과 일치해야 한다.

---

# 6. 프로젝트 디렉터리 구성

```
cloud-ops-web/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── auth.py
│   ├── aws_role.py
│   ├── ec2_service.py
│   ├── s3_service.py
│   ├── init_db.py
│   └── static/
│       ├── index
│       ├── app.js
│       └── style.css
└── requirements.txt
```

---

# 7. 패키지 설치

## 7.1 requirements.txt 작성

파일명: `requirements.txt`

```
fastapi
uvicorn
boto3
python-jose[cryptography]
python-multipart
sqlalchemy
pymysql
passlib[bcrypt]
```

---

## 7.2 패키지 설치

```
pip install -r requirements.txt
```

명령어 설명:

```
pip
  Python 패키지 관리 명령어다.

install
  패키지를 설치한다.

-r requirements.txt
  requirements.txt 파일에 작성된 패키지 목록을 한 번에 설치한다.
```

---

# 8. MariaDB 준비

## 8.1 MariaDB 접속

```
mysql -u root -p
```

---

## 8.2 데이터베이스 생성

```
CREATE DATABASE cloud_app
DEFAULT CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

설명:

```
CREATE DATABASE cloud_app
  cloud_app이라는 데이터베이스를 생성한다.

DEFAULT CHARACTER SET utf8mb4
  한글과 다양한 문자를 저장할 수 있는 문자셋을 사용한다.

COLLATE utf8mb4_unicode_ci
  문자열 비교와 정렬 규칙을 지정한다.
```

---

## 8.3 DB 사용자 생성

```
CREATE USER 'cloud_user'@'localhost' IDENTIFIED BY 'cloudpass123!';
```

---

## 8.4 권한 부여

```
GRANT ALL PRIVILEGES ON cloud_app.* TO 'cloud_user'@'localhost';
```

---

## 8.5 권한 반영

```
FLUSH PRIVILEGES;
```

---

## 8.6 접속 확인

```
mysql -u cloud_user -p cloud_app
```

비밀번호:

```
cloudpass123!
```

접속되면 DB 준비가 완료된 것이다.

---

# 9. DB 연결 설정

## 9.1 database.py 작성

파일명: `app/database.py`

```
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


DB_USER = "cloud_user"
DB_PASSWORD = "cloudpass123!"
DB_HOST = "localhost"
DB_PORT = 3306
DB_NAME = "cloud_app"


DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
)


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


Base = declarative_base()


def get_db():
    """
    FastAPI 요청마다 DB 세션을 생성하고 반환한다.

    yield를 사용하면 요청 처리 중에는 DB 세션을 유지하고,
    요청 처리가 끝난 뒤 finally 블록에서 세션을 닫을 수 있다.
    """

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
```

---

## 9.2 코드 설명

```
DATABASE_URL = "mysql+pymysql://..."
```

SQLAlchemy가 MariaDB에 접속할 때 사용하는 연결 문자열이다.

```
pool_pre_ping=True
```

DB 연결이 끊겼는지 미리 확인한다.

오래 열린 연결 때문에 발생하는 오류를 줄일 수 있다.

```
SessionLocal = sessionmaker(...)
```

DB 작업에 사용할 세션 생성기다.

FastAPI에서는 요청마다 DB 세션을 하나 생성해서 사용한다.

---

# 10. 사용자 모델 작성

## 10.1 models.py 작성

파일명: `app/models.py`

```
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func

from database import Base


class User(Base):
    """
    users 테이블과 연결되는 ORM 모델이다.

    이 클래스의 속성은 MariaDB users 테이블의 컬럼과 매핑된다.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    display_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
```

---

## 10.2 users 테이블 구조

이 모델은 MariaDB에 다음 테이블을 만든다.

```
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

비밀번호는 평문으로 저장하지 않는다.

반드시 해시값으로 저장한다.

```
나쁜 예:
password = viewer123

좋은 예:
password_hash = $2b$12$....
```

---

# 11. 응답 스키마 작성

## 11.1 schemas.py 작성

파일명: `app/schemas.py`

```
from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    username: str
    role: str
    display_name: str


class UserResponse(BaseModel):
    username: str
    role: str
    display_name: str


class ApiResponse(BaseModel):
    success: bool
    message: str
```

---

# 12. DB 초기화 및 실습 사용자 생성

## 12.1 init\_db.py 작성

파일명: `app/init_db.py`

```
from passlib.context import CryptContext

from database import Base, engine, SessionLocal
from models import User


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str):
    """
    평문 비밀번호를 bcrypt 해시로 변환한다.
    """

    return pwd_context.hash(password)


def create_tables():
    """
    SQLAlchemy 모델을 기준으로 DB 테이블을 생성한다.
    이미 테이블이 있으면 새로 만들지 않는다.
    """

    Base.metadata.create_all(bind=engine)


def create_user_if_not_exists(db, username, password, role, display_name):
    """
    사용자가 없으면 새로 생성한다.
    이미 존재하면 생성하지 않는다.
    """

    existing_user = db.query(User).filter(User.username == username).first()

    if existing_user:
        print(f"[안내] 이미 존재하는 사용자임: {username}")
        return

    user = User(
        username=username,
        password_hash=hash_password(password),
        role=role,
        display_name=display_name,
        is_active=True
    )

    db.add(user)
    db.commit()

    print(f"[생성 완료] 사용자 생성: {username} / role={role}")


def seed_users():
    """
    실습용 사용자 3명을 생성한다.

    viewer:
        조회 사용자

    operator:
        EC2 운영 사용자

    admin:
        관리자 사용자
    """

    db = SessionLocal()

    try:
        create_user_if_not_exists(
            db=db,
            username="viewer",
            password="viewer123",
            role="viewer",
            display_name="조회 사용자"
        )

        create_user_if_not_exists(
            db=db,
            username="operator",
            password="operator123",
            role="operator",
            display_name="운영 사용자"
        )

        create_user_if_not_exists(
            db=db,
            username="admin",
            password="admin123",
            role="admin",
            display_name="관리 사용자"
        )

    finally:
        db.close()


def main():
    create_tables()
    seed_users()
    print("DB 초기화 완료")


if __name__ == "__main__":
    main()
```

---

## 12.2 실행

`app` 디렉터리로 이동해서 실행한다.

```
cd cloud-ops-web/app
python init_db.py
```

예상 출력:

```
[생성 완료] 사용자 생성: viewer / role=viewer
[생성 완료] 사용자 생성: operator / role=operator
[생성 완료] 사용자 생성: admin / role=admin
DB 초기화 완료
```

이미 사용자가 있다면 다음처럼 출력될 수 있다.

```
[안내] 이미 존재하는 사용자임: viewer
[안내] 이미 존재하는 사용자임: operator
[안내] 이미 존재하는 사용자임: admin
DB 초기화 완료
```

---

## 12.3 DB 확인

```
mysql -u cloud_user -p cloud_app
```

```
SELECT id, username, role, display_name, is_active, created_at
FROM users;
```

예상 결과:

```
+----+----------+----------+---------------+-----------+---------------------+
| id | username | role     | display_name  | is_active | created_at          |
+----+----------+----------+---------------+-----------+---------------------+
|  1 | viewer   | viewer   | 조회 사용자    |         1 | 2026-04-29 10:00:00 |
|  2 | operator | operator | 운영 사용자    |         1 | 2026-04-29 10:00:00 |
|  3 | admin    | admin    | 관리 사용자    |         1 | 2026-04-29 10:00:00 |
+----+----------+----------+---------------+-----------+---------------------+
```

---

# 13. 인증 모듈 작성

## 13.1 auth.py 작성

파일명: `app/auth.py`

```
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import get_db
from models import User


SECRET_KEY = "change-this-secret-key-for-lab"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


def verify_password(plain_password: str, password_hash: str):
    """
    입력받은 평문 비밀번호와 DB에 저장된 해시 비밀번호를 비교한다.

    plain_password:
        사용자가 로그인 화면에 입력한 비밀번호

    password_hash:
        DB users 테이블에 저장된 bcrypt 해시값
    """

    return pwd_context.verify(plain_password, password_hash)


def get_user_by_username(db: Session, username: str):
    """
    username으로 사용자를 조회한다.
    사용자가 없으면 None을 반환한다.
    """

    return db.query(User).filter(User.username == username).first()


def authenticate_user(db: Session, username: str, password: str):
    """
    사용자 인증을 수행한다.

    처리 순서:
        1. username으로 DB에서 사용자 조회
        2. 사용자가 없으면 None 반환
        3. 비활성화 사용자면 None 반환
        4. 비밀번호 검증 실패 시 None 반환
        5. 성공 시 User 객체 반환
    """

    user = get_user_by_username(db, username)

    if user is None:
        return None

    if not user.is_active:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def create_access_token(data: dict):
    """
    JWT Access Token을 생성한다.

    data:
        토큰에 넣을 데이터다.
        이번 실습에서는 sub, role, display_name 값을 넣는다.

    exp:
        토큰 만료 시간이다.
    """

    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({
        "exp": expire
    })

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Authorization 헤더의 Bearer Token을 검증하고 현재 사용자를 반환한다.

    프론트엔드는 API 요청 시 다음 헤더를 보낸다.

        Authorization: Bearer <JWT_TOKEN>

    처리 순서:
        1. JWT 디코딩
        2. username 추출
        3. DB에서 사용자 조회
        4. 사용자 활성 여부 확인
        5. User 객체 반환
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보가 유효하지 않음",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        username = payload.get("sub")

        if username is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = get_user_by_username(db, username)

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 사용자임"
        )

    return user
```

---

## 13.2 핵심 설명

```
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
```

FastAPI에서 Bearer Token을 처리하기 위한 도구다.

요청 헤더에서 `Authorization: Bearer ...` 값을 읽는다.

```
jwt.encode(...)
```

사용자 정보를 담은 JWT를 생성한다.

```
jwt.decode(...)
```

클라이언트가 보낸 JWT가 유효한지 검증한다.

---

# 14. AWS AssumeRole 모듈 작성

## 14.1 aws\_role.py 작성

파일명: `app/aws_role.py`

```
import os

import boto3
from fastapi import HTTPException
from botocore.exceptions import ClientError


AWS_PROFILE = os.getenv("AWS_PROFILE", "instructor")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "ap-northeast-2")
AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID", "471166314777")


USER_ROLE_MAP = {
    "viewer": f"arn:aws:iam::{AWS_ACCOUNT_ID}:role/app-viewer-role",
    "operator": f"arn:aws:iam::{AWS_ACCOUNT_ID}:role/app-operator-role",
    "admin": f"arn:aws:iam::{AWS_ACCOUNT_ID}:role/app-admin-role"
}


def create_base_session():
    """
    AssumeRole을 호출하기 위한 기본 boto3 Session을 생성한다.

    로컬 실습:
        AWS_PROFILE 환경 변수 또는 기본값 instructor profile을 사용한다.

    EC2 배포:
        AWS_PROFILE을 제거하면 boto3 기본 인증 체인을 통해
        EC2 Instance Profile Role을 사용할 수 있다.
    """

    if AWS_PROFILE:
        return boto3.Session(
            profile_name=AWS_PROFILE,
            region_name=AWS_REGION
        )

    return boto3.Session(
        region_name=AWS_REGION
    )


def get_role_arn_for_user(user):
    """
    로그인 사용자의 role 값을 기준으로 IAM Role ARN을 선택한다.

    user.role 값:
        viewer
        operator
        admin
    """

    role_arn = USER_ROLE_MAP.get(user.role)

    if role_arn is None:
        raise HTTPException(
            status_code=403,
            detail=f"지원하지 않는 사용자 role임: {user.role}"
        )

    return role_arn


def assume_role_for_user(user):
    """
    로그인 사용자 role에 맞는 IAM Role을 AssumeRole 한다.

    이 함수는 로그인 사용자의 AWS 자격 증명을 사용하는 것이 아니다.
    FastAPI 서버가 가진 AWS 자격 증명으로 sts:AssumeRole을 호출한다.

    로컬 실습에서는 instructor profile이 AssumeRole을 호출한다.
    """

    role_arn = get_role_arn_for_user(user)

    session_name = f"app-{user.username}-{user.role}-session"

    base_session = create_base_session()
    sts_client = base_session.client("sts")

    try:
        response = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName=session_name
        )

        return response["Credentials"]

    except ClientError as e:
        error_code = e.response["Error"]["Code"]

        raise HTTPException(
            status_code=403,
            detail=f"AssumeRole 실패: {error_code}"
        )


def create_assumed_session(credentials):
    """
    STS AssumeRole로 발급받은 임시 자격 증명으로 boto3 Session을 생성한다.

    이 Session으로 만든 AWS 클라이언트는
    원래 IAM User 권한이 아니라 Assume한 Role 권한으로 동작한다.
    """

    return boto3.Session(
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
        region_name=AWS_REGION
    )


def get_assumed_session_for_user(user):
    """
    로그인 사용자 기준으로 AssumeRole을 수행하고,
    Role 권한이 적용된 boto3 Session을 반환한다.
    """

    credentials = assume_role_for_user(user)
    return create_assumed_session(credentials)
```

---

## 14.2 환경 변수 설정

Linux/macOS:

```
export AWS_PROFILE=instructor
export AWS_DEFAULT_REGION=ap-northeast-2
export AWS_ACCOUNT_ID=471166314777
```

Windows PowerShell:

```
$env:AWS_PROFILE="instructor"
$env:AWS_DEFAULT_REGION="ap-northeast-2"
$env:AWS_ACCOUNT_ID="471166314777"
```

---

# 15. EC2 서비스 모듈 작성

## 15.1 ec2\_service.py 작성

파일명: `app/ec2_service.py`

```
from fastapi import HTTPException
from botocore.exceptions import ClientError

from aws_role import AWS_REGION, get_assumed_session_for_user


def extract_name_tag(instance):
    """
    EC2 인스턴스의 Name 태그 값을 추출한다.
    Name 태그가 없으면 빈 문자열을 반환한다.
    """

    tags = instance.get("Tags", [])

    for tag in tags:
        if tag.get("Key") == "Name":
            return tag.get("Value", "")

    return ""


def list_instances(user):
    """
    로그인 사용자 권한에 맞는 IAM Role을 AssumeRole 한 뒤
    EC2 인스턴스 목록을 조회한다.
    """

    session = get_assumed_session_for_user(user)
    ec2_client = session.client("ec2", region_name=AWS_REGION)

    try:
        response = ec2_client.describe_instances()

        instances = []

        for reservation in response.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                instances.append({
                    "instance_id": instance.get("InstanceId"),
                    "name": extract_name_tag(instance),
                    "instance_type": instance.get("InstanceType"),
                    "state": instance.get("State", {}).get("Name"),
                    "private_ip": instance.get("PrivateIpAddress", ""),
                    "public_ip": instance.get("PublicIpAddress", "")
                })

        return instances

    except ClientError as e:
        raise HTTPException(
            status_code=403,
            detail=f"EC2 인스턴스 조회 실패: {e.response['Error']['Code']}"
        )


def start_instance(user, instance_id: str):
    """
    EC2 인스턴스를 시작한다.

    viewer Role은 ec2:StartInstances 권한이 없으므로 실패해야 정상이다.
    operator/admin Role은 성공할 수 있다.
    """

    session = get_assumed_session_for_user(user)
    ec2_client = session.client("ec2", region_name=AWS_REGION)

    try:
        ec2_client.start_instances(
            InstanceIds=[instance_id]
        )

        return {
            "success": True,
            "message": f"EC2 시작 요청 완료: {instance_id}"
        }

    except ClientError as e:
        raise HTTPException(
            status_code=403,
            detail=f"EC2 시작 실패: {e.response['Error']['Code']}"
        )


def stop_instance(user, instance_id: str):
    """
    EC2 인스턴스를 중지한다.

    viewer Role은 ec2:StopInstances 권한이 없으므로 실패해야 정상이다.
    operator/admin Role은 성공할 수 있다.
    """

    session = get_assumed_session_for_user(user)
    ec2_client = session.client("ec2", region_name=AWS_REGION)

    try:
        ec2_client.stop_instances(
            InstanceIds=[instance_id]
        )

        return {
            "success": True,
            "message": f"EC2 중지 요청 완료: {instance_id}"
        }

    except ClientError as e:
        raise HTTPException(
            status_code=403,
            detail=f"EC2 중지 실패: {e.response['Error']['Code']}"
        )
```

---

# 16. S3 서비스 모듈 작성

## 16.1 s3\_service.py 작성

파일명: `app/s3_service.py`

```
from fastapi import HTTPException, UploadFile
from botocore.exceptions import ClientError

from aws_role import get_assumed_session_for_user


def list_buckets(user):
    """
    로그인 사용자 권한에 맞는 IAM Role을 AssumeRole 한 뒤
    S3 버킷 목록을 조회한다.
    """

    session = get_assumed_session_for_user(user)
    s3_client = session.client("s3")

    try:
        response = s3_client.list_buckets()

        buckets = []

        for bucket in response.get("Buckets", []):
            buckets.append({
                "name": bucket["Name"],
                "creation_date": str(bucket["CreationDate"])
            })

        return buckets

    except ClientError as e:
        raise HTTPException(
            status_code=403,
            detail=f"S3 버킷 목록 조회 실패: {e.response['Error']['Code']}"
        )


def list_objects(user, bucket_name: str):
    """
    특정 S3 버킷의 객체 목록을 조회한다.
    """

    session = get_assumed_session_for_user(user)
    s3_client = session.client("s3")

    try:
        response = s3_client.list_objects_v2(
            Bucket=bucket_name
        )

        objects = []

        for obj in response.get("Contents", []):
            objects.append({
                "key": obj["Key"],
                "size": obj["Size"],
                "last_modified": str(obj["LastModified"])
            })

        return objects

    except ClientError as e:
        raise HTTPException(
            status_code=403,
            detail=f"S3 객체 목록 조회 실패: {e.response['Error']['Code']}"
        )


async def upload_file(user, bucket_name: str, file: UploadFile):
    """
    S3에 파일을 업로드한다.

    viewer/operator Role은 s3:PutObject 권한이 없으므로 실패해야 정상이다.
    admin Role은 성공할 수 있다.
    """

    session = get_assumed_session_for_user(user)
    s3_client = session.client("s3")

    object_key = f"uploads/{file.filename}"

    try:
        file_content = await file.read()

        s3_client.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=file_content
        )

        return {
            "success": True,
            "message": "S3 파일 업로드 완료",
            "bucket": bucket_name,
            "key": object_key
        }

    except ClientError as e:
        raise HTTPException(
            status_code=403,
            detail=f"S3 파일 업로드 실패: {e.response['Error']['Code']}"
        )
```

---

# 17. FastAPI 메인 애플리케이션 작성

## 17.1 main.py 작성

파일명: `app/main.py`

```
from fastapi import FastAPI, Depends, HTTPException, Form, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database import get_db
from auth import authenticate_user, create_access_token, get_current_user
from schemas import TokenResponse, UserResponse
from aws_role import assume_role_for_user, create_assumed_session
from ec2_service import list_instances, start_instance, stop_instance
from s3_service import list_buckets, list_objects, upload_file


app = FastAPI(
    title="Cloud Operations Automation API",
    description="FastAPI, MariaDB, boto3를 이용한 로그인 기반 AWS 운영 자동화 API",
    version="1.0.0"
)


app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


@app.get("/")
def index():
    """
    프론트엔드 랜딩페이지를 반환한다.
    """

    return FileResponse("static/index")


@app.post("/auth/login", response_model=TokenResponse)
def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    로그인 API다.

    요청 형식:
        application/x-www-form-urlencoded

    입력:
        username
        password

    처리:
        1. DB에서 사용자 조회
        2. 비밀번호 검증
        3. JWT Access Token 발급
    """

    user = authenticate_user(
        db=db,
        username=username,
        password=password
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="아이디 또는 비밀번호가 올바르지 않음"
        )

    token = create_access_token({
        "sub": user.username,
        "role": user.role,
        "display_name": user.display_name
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user.username,
        "role": user.role,
        "display_name": user.display_name
    }


@app.get("/me", response_model=UserResponse)
def me(current_user=Depends(get_current_user)):
    """
    현재 로그인 사용자 정보를 반환한다.
    JWT 인증이 필요한 API다.
    """

    return {
        "username": current_user.username,
        "role": current_user.role,
        "display_name": current_user.display_name
    }


@app.get("/aws/whoami")
def aws_whoami(current_user=Depends(get_current_user)):
    """
    로그인 사용자의 role에 맞는 IAM Role을 AssumeRole 한 뒤
    현재 AWS 인증 주체를 확인한다.

    이 API는 로그인 사용자 role과 IAM Role 매핑이 정상인지 확인하는 용도다.
    """

    credentials = assume_role_for_user(current_user)
    session = create_assumed_session(credentials)

    sts_client = session.client("sts")
    identity = sts_client.get_caller_identity()

    return {
        "login_user": {
            "username": current_user.username,
            "role": current_user.role,
            "display_name": current_user.display_name
        },
        "aws_identity": identity
    }


@app.get("/api/ec2/instances")
def api_list_instances(current_user=Depends(get_current_user)):
    """
    EC2 인스턴스 목록을 조회한다.
    """

    return {
        "items": list_instances(current_user)
    }


@app.post("/api/ec2/instances/{instance_id}/start")
def api_start_instance(
    instance_id: str,
    current_user=Depends(get_current_user)
):
    """
    EC2 인스턴스를 시작한다.
    """

    return start_instance(
        user=current_user,
        instance_id=instance_id
    )


@app.post("/api/ec2/instances/{instance_id}/stop")
def api_stop_instance(
    instance_id: str,
    current_user=Depends(get_current_user)
):
    """
    EC2 인스턴스를 중지한다.
    """

    return stop_instance(
        user=current_user,
        instance_id=instance_id
    )


@app.get("/api/s3/buckets")
def api_list_buckets(current_user=Depends(get_current_user)):
    """
    S3 버킷 목록을 조회한다.
    """

    return {
        "items": list_buckets(current_user)
    }


@app.get("/api/s3/buckets/{bucket_name}/objects")
def api_list_objects(
    bucket_name: str,
    current_user=Depends(get_current_user)
):
    """
    특정 S3 버킷의 객체 목록을 조회한다.
    """

    return {
        "items": list_objects(
            user=current_user,
            bucket_name=bucket_name
        )
    }


@app.post("/api/s3/buckets/{bucket_name}/upload")
async def api_upload_file(
    bucket_name: str,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user)
):
    """
    S3 버킷에 파일을 업로드한다.
    """

    return await upload_file(
        user=current_user,
        bucket_name=bucket_name,
        file=file
    )
```

---

# 18. FastAPI 실행

`app` 디렉터리에서 실행한다.

```
cd cloud-ops-web/app
uvicorn main:app --reload
```

브라우저에서 Swagger UI 접속:

```
http://127.0.0.1:8000/docs
```

프론트엔드 접속:

```
http://127.0.0.1:8000/
```

---

# 19. API 테스트 순서

## 19.1 로그인 테스트

Swagger 또는 curl로 테스트한다.

```
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=viewer&password=viewer123"
```

예상 응답:

```
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "username": "viewer",
  "role": "viewer",
  "display_name": "조회 사용자"
}
```

---

## 19.2 /me 테스트

```
curl http://127.0.0.1:8000/me \
  -H "Authorization: Bearer <access_token>"
```

예상 응답:

```
{
  "username": "viewer",
  "role": "viewer",
  "display_name": "조회 사용자"
}
```

---

## 19.3 AssumeRole 확인

```
curl http://127.0.0.1:8000/aws/whoami \
  -H "Authorization: Bearer <access_token>"
```

viewer 사용자라면 AWS ARN이 다음 형태로 나와야 한다.

```
arn:aws:sts::471166314777:assumed-role/app-viewer-role/app-viewer-viewer-session
```

operator 사용자라면 다음 형태로 나온다.

```
arn:aws:sts::471166314777:assumed-role/app-operator-role/app-operator-operator-session
```

---

# 20. 프론트엔드 작성

## 20.1 index 작성

파일명: `app/static/index`

```
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <title>Cloud Operations Automation</title>
  <link rel="stylesheet" href="/static/style.css" />
</head>
<body>
  <div class="container">
    <h1>Cloud Operations Automation</h1>
    <p class="subtitle">로그인 사용자 권한별 EC2 / S3 운영 자동화</p>

    <section id="login-section" class="card">
      <h2>로그인</h2>

      <div class="form-group">
        <label>Username</label>
        <input id="username" type="text" placeholder="viewer / operator / admin" />
      </div>

      <div class="form-group">
        <label>Password</label>
        <input id="password" type="password" placeholder="password" />
      </div>

      <button onclick="login()">로그인</button>

      <div class="hint">
        viewer / viewer123<br />
        operator / operator123<br />
        admin / admin123
      </div>
    </section>

    <section id="dashboard-section" class="card hidden">
      <h2>운영 대시보드</h2>

      <div class="user-box">
        <div>사용자: <strong id="current-user"></strong></div>
        <div>권한: <strong id="current-role"></strong></div>
        <button onclick="logout()">로그아웃</button>
      </div>

      <hr />

      <h3>AWS 인증 확인</h3>
      <button onclick="checkAwsWhoami()">AssumeRole 확인</button>

      <hr />

      <h3>EC2 운영</h3>
      <button onclick="loadInstances()">EC2 목록 조회</button>
      <div id="ec2-list" class="list-box"></div>

      <hr />

      <h3>S3 운영</h3>
      <button onclick="loadBuckets()">S3 버킷 목록 조회</button>
      <div id="bucket-list" class="list-box"></div>

      <div class="upload-box">
        <h4>S3 파일 업로드</h4>
        <input id="upload-bucket" type="text" placeholder="업로드할 버킷 이름" />
        <input id="upload-file" type="file" />
        <button onclick="uploadFile()">업로드</button>
      </div>

      <hr />

      <h3>API 결과</h3>
      <pre id="result-box"></pre>
    </section>
  </div>

  <script src="/static/app.js"></script>
</body>
</html>
```

---

## 20.2 style.css 작성

파일명: `app/static/style.css`

```
body {
  margin: 0;
  font-family: Arial, sans-serif;
  background: #f4f6f8;
  color: #222;
}

.container {
  max-width: 1100px;
  margin: 40px auto;
  padding: 0 20px;
}

h1 {
  margin-bottom: 5px;
}

.subtitle {
  color: #666;
  margin-bottom: 30px;
}

.card {
  background: white;
  border-radius: 10px;
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.hidden {
  display: none;
}

.form-group {
  margin-bottom: 15px;
}

label {
  display: block;
  margin-bottom: 6px;
  font-weight: bold;
}

input {
  padding: 10px;
  width: 300px;
  max-width: 100%;
  border: 1px solid #ccc;
  border-radius: 6px;
}

button {
  padding: 9px 14px;
  border: none;
  border-radius: 6px;
  background: #2563eb;
  color: white;
  cursor: pointer;
  margin: 4px;
}

button:hover {
  background: #1d4ed8;
}

button.danger {
  background: #dc2626;
}

button.danger:hover {
  background: #b91c1c;
}

.user-box {
  display: flex;
  gap: 20px;
  align-items: center;
  flex-wrap: wrap;
}

.hint {
  margin-top: 15px;
  color: #666;
  font-size: 14px;
}

.list-box {
  margin-top: 12px;
}

.item {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 12px;
  margin: 8px 0;
  background: #fafafa;
}

.item-title {
  font-weight: bold;
}

.item-meta {
  color: #555;
  font-size: 14px;
  margin-top: 4px;
}

.upload-box {
  margin-top: 20px;
}

#result-box {
  background: #111827;
  color: #d1d5db;
  padding: 15px;
  border-radius: 8px;
  min-height: 120px;
  overflow-x: auto;
}
```

---

## 20.3 app.js 작성

파일명: `app/static/app.js`

```
const API_BASE = "";

function getToken() {
  return localStorage.getItem("access_token");
}

function setResult(data) {
  const resultBox = document.getElementById("result-box");
  resultBox.textContent = JSON.stringify(data, null, 2);
}

function showDashboard(user) {
  document.getElementById("login-section").classList.add("hidden");
  document.getElementById("dashboard-section").classList.remove("hidden");

  document.getElementById("current-user").textContent = user.username;
  document.getElementById("current-role").textContent = user.role;
}

function showLogin() {
  document.getElementById("login-section").classList.remove("hidden");
  document.getElementById("dashboard-section").classList.add("hidden");
}

async function apiFetch(url, options = {}) {
  const token = getToken();

  const headers = options.headers || {};

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers: headers
  });

  const data = await response.json().catch(() => {
    return { message: "JSON 응답이 아님" };
  });

  if (!response.ok) {
    setResult({
      success: false,
      status: response.status,
      detail: data.detail || data
    });

    throw new Error(data.detail || "API 요청 실패");
  }

  return data;
}

async function login() {
  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;

  const formData = new URLSearchParams();
  formData.append("username", username);
  formData.append("password", password);

  try {
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded"
      },
      body: formData
    });

    const data = await response.json();

    if (!response.ok) {
      setResult(data);
      return;
    }

    localStorage.setItem("access_token", data.access_token);

    showDashboard({
      username: data.username,
      role: data.role
    });

    setResult({
      message: "로그인 성공",
      user: data
    });

  } catch (error) {
    setResult({
      success: false,
      message: error.message
    });
  }
}

function logout() {
  localStorage.removeItem("access_token");
  showLogin();
  setResult({
    message: "로그아웃 완료"
  });
}

async function loadMe() {
  try {
    const data = await apiFetch(`${API_BASE}/me`);
    showDashboard(data);
  } catch (error) {
    showLogin();
  }
}

async function checkAwsWhoami() {
  try {
    const data = await apiFetch(`${API_BASE}/aws/whoami`);
    setResult(data);
  } catch (error) {
    console.error(error);
  }
}

async function loadInstances() {
  try {
    const data = await apiFetch(`${API_BASE}/api/ec2/instances`);
    renderInstances(data.items);
    setResult(data);
  } catch (error) {
    console.error(error);
  }
}

function renderInstances(instances) {
  const container = document.getElementById("ec2-list");
  container.innerHTML = "";

  if (!instances || instances.length === 0) {
    container.innerHTML = "<p>조회된 EC2 인스턴스가 없음</p>";
    return;
  }

  instances.forEach(instance => {
    const div = document.createElement("div");
    div.className = "item";

    div.innerHTML = `
      <div class="item-title">${instance.instance_id}</div>
      <div class="item-meta">Name: ${instance.name || "-"}</div>
      <div class="item-meta">Type: ${instance.instance_type}</div>
      <div class="item-meta">State: ${instance.state}</div>
      <div class="item-meta">Private IP: ${instance.private_ip || "-"}</div>
      <div class="item-meta">Public IP: ${instance.public_ip || "-"}</div>
      <button onclick="startInstance('${instance.instance_id}')">Start</button>
      <button class="danger" onclick="stopInstance('${instance.instance_id}')">Stop</button>
    `;

    container.appendChild(div);
  });
}

async function startInstance(instanceId) {
  try {
    const data = await apiFetch(`${API_BASE}/api/ec2/instances/${instanceId}/start`, {
      method: "POST"
    });

    setResult(data);
    await loadInstances();

  } catch (error) {
    console.error(error);
  }
}

async function stopInstance(instanceId) {
  try {
    const data = await apiFetch(`${API_BASE}/api/ec2/instances/${instanceId}/stop`, {
      method: "POST"
    });

    setResult(data);
    await loadInstances();

  } catch (error) {
    console.error(error);
  }
}

async function loadBuckets() {
  try {
    const data = await apiFetch(`${API_BASE}/api/s3/buckets`);
    renderBuckets(data.items);
    setResult(data);
  } catch (error) {
    console.error(error);
  }
}

function renderBuckets(buckets) {
  const container = document.getElementById("bucket-list");
  container.innerHTML = "";

  if (!buckets || buckets.length === 0) {
    container.innerHTML = "<p>조회된 S3 버킷이 없음</p>";
    return;
  }

  buckets.forEach(bucket => {
    const div = document.createElement("div");
    div.className = "item";

    div.innerHTML = `
      <div class="item-title">${bucket.name}</div>
      <div class="item-meta">Created: ${bucket.creation_date}</div>
      <button onclick="loadObjects('${bucket.name}')">객체 목록 조회</button>
      <button onclick="selectUploadBucket('${bucket.name}')">업로드 버킷으로 선택</button>
      <div id="objects-${bucket.name}" class="list-box"></div>
    `;

    container.appendChild(div);
  });
}

function selectUploadBucket(bucketName) {
  document.getElementById("upload-bucket").value = bucketName;
}

async function loadObjects(bucketName) {
  try {
    const data = await apiFetch(`${API_BASE}/api/s3/buckets/${bucketName}/objects`);

    const container = document.getElementById(`objects-${bucketName}`);
    container.innerHTML = "";

    if (!data.items || data.items.length === 0) {
      container.innerHTML = "<p>객체가 없음</p>";
    } else {
      data.items.forEach(obj => {
        const p = document.createElement("p");
        p.textContent = `${obj.key} (${obj.size} bytes)`;
        container.appendChild(p);
      });
    }

    setResult(data);

  } catch (error) {
    console.error(error);
  }
}

async function uploadFile() {
  const bucketName = document.getElementById("upload-bucket").value;
  const fileInput = document.getElementById("upload-file");

  if (!bucketName) {
    setResult({
      success: false,
      message: "버킷 이름을 입력해야 함"
    });
    return;
  }

  if (!fileInput.files || fileInput.files.length === 0) {
    setResult({
      success: false,
      message: "업로드할 파일을 선택해야 함"
    });
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  try {
    const token = getToken();

    const response = await fetch(`${API_BASE}/api/s3/buckets/${bucketName}/upload`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`
      },
      body: formData
    });

    const data = await response.json();

    if (!response.ok) {
      setResult({
        success: false,
        status: response.status,
        detail: data.detail || data
      });
      return;
    }

    setResult(data);

  } catch (error) {
    setResult({
      success: false,
      message: error.message
    });
  }
}

window.addEventListener("load", () => {
  const token = getToken();

  if (token) {
    loadMe();
  } else {
    showLogin();
  }
});
```

---

# 21. 프론트엔드 테스트

브라우저 접속:

```
http://127.0.0.1:8000/
```

---

## 21.1 viewer 로그인

```
username: viewer
password: viewer123
```

테스트:

```
EC2 목록 조회 → 성공
EC2 Start → 실패
EC2 Stop → 실패
S3 버킷 목록 조회 → 성공
S3 업로드 → 실패
```

---

## 21.2 operator 로그인

```
username: operator
password: operator123
```

테스트:

```
EC2 목록 조회 → 성공
EC2 Start → 성공
EC2 Stop → 성공
S3 버킷 목록 조회 → 성공
S3 업로드 → 실패
```

---

## 21.3 admin 로그인

```
username: admin
password: admin123
```

테스트:

```
EC2 목록 조회 → 성공
EC2 Start → 성공
EC2 Stop → 성공
S3 버킷 목록 조회 → 성공
S3 업로드 → 성공
```

---

# 22. 권한 실패가 발생하는 이유

예를 들어 viewer 사용자가 EC2 Stop을 누르면 다음 흐름으로 처리된다.

```
viewer 로그인
  ↓
JWT에 role=viewer 포함
  ↓
FastAPI가 viewer 확인
  ↓
app-viewer-role AssumeRole
  ↓
ec2.stop_instances 호출
  ↓
app-viewer-role에는 ec2:StopInstances 권한 없음
  ↓
UnauthorizedOperation 발생
```

즉, 프론트엔드에서 버튼을 숨기지 않아도 AWS IAM Role이 최종적으로 권한을 막는다.

---

# 23. 수업 중 강조할 핵심 포인트

## 23.1 프론트엔드 버튼 제어는 보안이 아니다

프론트엔드에서 viewer 사용자에게 Stop 버튼을 숨길 수 있다.

하지만 사용자가 개발자 도구나 curl로 직접 API를 호출할 수 있으므로, 프론트엔드 제어만으로는 보안이 되지 않는다.

최종 권한 제어는 반드시 백엔드와 IAM Role에서 이루어져야 한다.

---

## 23.2 FastAPI는 AWS Access Key를 사용자에게 주지 않는다

브라우저에는 AWS Access Key가 전달되지 않는다.

브라우저는 JWT만 가지고 있다.

```
브라우저
  - JWT 보관
  - AWS Access Key 없음

FastAPI
  - AWS Profile 또는 Instance Role 사용
  - sts:AssumeRole 호출
  - 임시 자격 증명으로 AWS API 호출
```

---

## 23.3 AssumeRole 이후에는 Role 권한만 적용된다

학생 IAM User가 관리자 권한을 가지고 있어도, `app-viewer-role`을 AssumeRole하면 viewer 권한만 적용된다.

```
AssumeRole 이전:
  instructor IAM User 권한

AssumeRole 이후:
  app-viewer-role 권한
```

---

# 24. 실습 과제

## 과제 1. 사용자별 권한 차이 테스트

다음 사용자로 로그인하여 결과를 표로 정리한다.

```
viewer
operator
admin
```

테스트 항목:

```
1. EC2 목록 조회
2. EC2 시작
3. EC2 중지
4. S3 버킷 목록 조회
5. S3 객체 목록 조회
6. S3 파일 업로드
```

결과표 예시:

| 사용자 | EC2 조회 | EC2 시작 | EC2 중지 | S3 조회 | S3 업로드 |
| --- | --- | --- | --- | --- | --- |
| viewer | 성공 | 실패 | 실패 | 성공 | 실패 |
| operator | 성공 | 성공 | 성공 | 성공 | 실패 |
| admin | 성공 | 성공 | 성공 | 성공 | 성공 |

---

## 과제 2. 권한 실패 원인 분석

viewer 사용자가 EC2 Stop을 실행했을 때 실패하는 이유를 설명한다.

포함해야 할 내용:

```
1. 로그인 사용자의 role 값
2. USER_ROLE_MAP에서 선택된 IAM Role
3. AssumeRole 이후 AWS 인증 주체
4. 해당 Role에 없는 IAM 권한
5. 최종 오류 코드
```

---

## 과제 3. FastAPI API 하나 추가

다음 API 중 하나를 추가한다.

```
1. EC2 Reboot API
2. S3 객체 삭제 API
3. 현재 로그인 사용자의 AWS Role ARN 확인 API
```

예를 들어 EC2 Reboot API를 추가한다면 admin만 가능해야 한다.

---

# 25. 최종 정리

이번 실습의 핵심은 다음이다.

```
1. MariaDB는 로그인 사용자와 role을 저장한다.
2. FastAPI는 로그인 성공 시 JWT를 발급한다.
3. 프론트엔드는 JWT를 저장하고 API 요청 시 전달한다.
4. FastAPI는 JWT로 현재 사용자를 식별한다.
5. 사용자 role에 따라 IAM Role ARN을 선택한다.
6. FastAPI는 STS AssumeRole을 호출한다.
7. EC2/S3 API는 AssumeRole로 받은 임시 자격 증명으로 호출한다.
8. 권한 차이는 IAM Role의 Permission Policy로 결정된다.
```

이 실습은 단순히 Python 문법이나 boto3 사용법을 배우는 것이 아니라, **Python을 이용해 클라우드 운영 자동화 서비스를 구현하는 과정**이다.