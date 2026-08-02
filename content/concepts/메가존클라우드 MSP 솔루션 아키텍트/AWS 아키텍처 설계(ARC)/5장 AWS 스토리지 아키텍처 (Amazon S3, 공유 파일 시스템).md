---
title: "5장 AWS 스토리지 아키텍처 (Amazon S3, 공유 파일 시스템)"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 아키텍처 설계(ARC)"]
is_public: true
draft: false
---

# 5장 AWS 스토리지 아키텍처 (Amazon S3, 공유 파일 시스템)

---

# 5.1 스토리지 서비스 개요

AWS에서 스토리지는 단순히 데이터를 저장하는 공간이 아니라, 아키텍처 전체의 성능, 확장성, 비용, 내구성에 직접 영향을 주는 핵심 구성요소임.

어떤 스토리지를 선택하느냐에 따라 애플리케이션 구조 자체가 달라질 수 있음.

예를 들어

* 운영체제 디스크 저장 → EBS

* 정적 파일 저장 → S3

* 여러 서버가 동시에 같은 파일 공유 → EFS

* Windows 파일 서버 → FSx for Windows File Server

* 고성능 Lustre 기반 분석 → FSx for Lustre

즉, 스토리지는 “파일을 어디에 둘까?” 수준의 문제가 아니라 **애플리케이션 요구사항에 맞는 저장 방식 선택 문제**라고 봐야 함.

---

# 5.2 AWS 스토리지 분류

AWS 스토리지는 크게 다음과 같이 나눌 수 있음.

| 분류 | 대표 서비스 | 설명 |
| --- | --- | --- |
| 객체 스토리지 | S3 | 파일을 객체 단위로 저장 |
| 블록 스토리지 | EBS | EC2에 연결하는 디스크 |
| 파일 스토리지 | EFS, FSx | 여러 서버가 공유하는 파일 시스템 |
| 아카이브 스토리지 | S3 Glacier | 장기 보관용 저비용 저장소 |

이 장에서는 커리큘럼에 맞게 **S3와 공유 파일 시스템(EFS 중심)**을 중점적으로 다룸.

---

# 5.3 Amazon S3 개요

Amazon S3는 **Simple Storage Service**의 약자이며, AWS의 대표적인 객체 스토리지 서비스임.

객체 스토리지라는 말은 데이터를 “디스크 블록”이나 “파일 시스템 트리”가 아니라

**객체(Object)** 단위로 저장한다는 뜻임.

S3의 구조

```
Bucket
 ├ Object 1
 ├ Object 2
 └ Object 3
```

여기서

* **Bucket** : 객체를 저장하는 논리적 컨테이너

* **Object** : 실제 저장되는 파일

* **Key** : 객체의 경로/이름 역할

* **Metadata** : 객체에 대한 부가 정보

예

```
s3://my-bucket/images/logo.png
```

의미

* `my-bucket` : 버킷 이름

* `images/logo.png` : 객체 키

---

# 5.4 S3의 특징

S3는 AWS에서 매우 자주 사용되는 서비스이며 다음과 같은 특징이 있음.

### 1. 매우 높은 내구성

S3는 객체를 여러 장비와 여러 시설에 분산 저장하여 매우 높은 내구성을 제공함.

### 2. 사실상 무제한 확장

데이터 양이 많아져도 별도 디스크 증설 작업 없이 저장 가능함.

### 3. HTTP 기반 접근

브라우저, SDK, CLI, 애플리케이션 등 다양한 방식으로 접근 가능함.

### 4. 정적 콘텐츠 저장에 적합

이미지, 동영상, HTML, CSS, JS 같은 정적 파일 저장에 매우 적합함.

### 5. 백업 및 로그 저장에 적합

애플리케이션 백업, 로그 보관, 아카이빙, 데이터 레이크 저장소로 자주 사용됨.

---

# 5.5 S3 기본 개념

S3를 이해할 때 반드시 알아야 할 개념이 있음.

---

## 5.5.1 Bucket

Bucket은 S3 객체를 저장하는 최상위 컨테이너임.

버킷 이름은 전 세계적으로 유일해야 함.

예

```
kyt-arc-bucket-2026
```

버킷 이름 규칙

* 중복 불가

* 소문자 사용 권장

* 공백 불가

* DNS 호환 형식 권장

버킷은 Region 단위로 생성되며, 버킷을 어느 리전에 만들지에 따라 데이터 저장 위치가 결정됨.

---

## 5.5.2 Object

S3에 저장되는 실제 데이터 단위임.

예

* 사진 파일

* 로그 파일

* 백업 파일

* HTML 파일

* 영상 파일

객체는 다음으로 구성됨.

* 데이터 본문

* Key

* Metadata

* Version ID (버전관리 사용 시)

---

## 5.5.3 Key

Key는 버킷 내부에서 객체를 식별하는 이름임.

폴더처럼 보이는 구조가 있어도 실제로는 디렉터리 개념이 아니라 문자열 경로임.

예

```
images/logo.png
logs/2026/03/16/app.log
backup/db/dump.sql
```

S3 콘솔에서는 이를 폴더처럼 보여주지만 실제로는 Key 값일 뿐임.

---

# 5.6 객체 스토리지와 파일 스토리지 차이

학생들이 가장 많이 헷갈리는 부분 중 하나가

**S3와 EFS를 둘 다 “파일 저장소”로 생각하는 것**임.

둘은 구조와 사용 방식이 다름.

| 항목 | S3 | EFS |
| --- | --- | --- |
| 저장 방식 | 객체 스토리지 | 파일 스토리지 |
| 접근 방식 | HTTP/HTTPS, API | NFS 마운트 |
| 여러 서버 공유 | 가능하나 파일 시스템처럼 쓰지 않음 | 가능 |
| 운영체제 마운트 | 일반 파일 시스템처럼 직접 사용 어려움 | 가능 |
| 대표 용도 | 정적 파일, 백업, 로그 | 공유 웹 콘텐츠, 공용 파일 저장 |

즉

* **S3는 API 기반 저장소**

* **EFS는 리눅스 공유 파일 시스템**

이라고 이해하면 됨.

---

# 5.7 S3 Storage Class

S3는 데이터 접근 빈도와 보관 목적에 따라 여러 저장 클래스를 제공함.

| Storage Class | 설명 |
| --- | --- |
| Standard | 자주 사용하는 데이터 |
| Intelligent-Tiering | 접근 패턴이 일정하지 않은 데이터 |
| Standard-IA | 드물게 접근하는 데이터 |
| One Zone-IA | 단일 AZ에 저장하는 저비용 클래스 |
| Glacier Instant Retrieval | 아카이브지만 즉시 조회 가능 |
| Glacier Flexible Retrieval | 장기 보관용 |
| Glacier Deep Archive | 가장 저렴한 장기 보관용 |

---

## 5.7.1 Storage Class 선택 기준

### S3 Standard

자주 읽고 쓰는 데이터에 적합함.

예

* 웹사이트 정적 파일

* 애플리케이션 업로드 파일

* 운영 로그의 최근 데이터

### S3 Standard-IA(Infrequent Access)

평소 자주 접근하지 않지만 필요 시 즉시 꺼내야 하는 데이터에 적합함.

예

* 월별 백업 파일

* 오래된 문서

### Glacier 계열

장기 보관이 목적이고 조회가 드문 데이터에 적합함.

예

* 법적 보관 자료

* 장기 백업

* 오래된 감사 로그

---

# 5.8 S3 보안

S3는 저장소 자체가 매우 단순해 보이지만 실제 운영에서는 보안 설정이 매우 중요함.

특히 잘못 설정하면 민감한 파일이 인터넷에 공개될 수 있음.

S3 보안 구성 요소

* Bucket Policy

* IAM Policy

* ACL

* Block Public Access

* Encryption

* Versioning

* Access Logging

---

## 5.8.1 Block Public Access

S3 보안에서 가장 먼저 봐야 하는 기능임.

버킷이나 객체가 실수로 공개되지 않도록 차단하는 기능임.

일반적으로는 **기본적으로 모두 활성화**해 두는 것이 좋음.

예외

* 정적 웹사이트 호스팅

* CloudFront OAC/OAI 연동 시 일부 정책 설정 필요

---

## 5.8.2 Bucket Policy

버킷 수준에서 접근 권한을 정의하는 정책임.

JSON 형식으로 작성함.

예시 구조

```
{
  "Version":"2012-10-17",
  "Statement": [
    {
      "Effect":"Allow",
      "Principal":"*",
      "Action":"s3:GetObject",
      "Resource":"arn:aws:s3:::example-bucket/*"
    }
  ]
}
```

이 예시는 모든 사용자가 버킷 내 객체를 읽을 수 있도록 허용하는 정책임.

운영 환경에서는 이렇게 전면 공개하는 방식은 매우 신중하게 사용해야 함.

---

## 5.8.3 IAM Policy와 S3

IAM Policy는 “누가 무엇을 할 수 있는가”를 정의함.

Bucket Policy는 “이 버킷이 누구를 허용할 것인가”를 정의함.

둘의 차이

* IAM Policy : 사용자/역할 중심

* Bucket Policy : 버킷 중심

실무에서는 두 정책이 함께 작동함.

---

## 5.8.4 S3 암호화

S3는 저장 데이터 암호화를 지원함.

대표 방식

* SSE-S3

* SSE-KMS

* SSE-C

### SSE-S3

AWS가 관리하는 키로 암호화함.

### SSE-KMS

AWS KMS 키를 사용해 더 정교하게 제어함.

---

# 5.9 S3 Versioning

Versioning은 객체의 이전 버전을 보관하는 기능임.

예를 들어 같은 이름의 파일을 다시 업로드해도 이전 버전이 보존됨.

장점

* 실수로 덮어쓴 파일 복구 가능

* 삭제된 객체 복구 가능

* 운영 안정성 향상

주의

* 버전 수가 많아지면 비용이 증가할 수 있음

---

# 5.10 S3 Lifecycle

Lifecycle은 객체를 시간 경과에 따라 자동으로 다른 Storage Class로 이동하거나 삭제하는 정책임.

예

* 30일 후 Standard-IA로 전환

* 90일 후 Glacier로 전환

* 365일 후 삭제

Lifecycle을 사용하는 이유

* 장기 보관 비용 절감

* 로그/백업 자동 정리

* 운영 자동화

---

# 5.11 S3 주요 사용 사례

### 1. 정적 웹사이트 저장소

HTML, CSS, JS, 이미지 파일 등을 저장함.

### 2. 애플리케이션 업로드 파일 저장

사용자가 업로드한 이미지, 문서, 첨부파일 저장.

### 3. 로그 저장소

ALB 로그, CloudTrail 로그, 애플리케이션 로그 저장.

### 4. 백업 저장소

DB 덤프, 스냅샷 export 파일, 설정 백업 등 저장.

### 5. 데이터 레이크 저장소

분석용 원본 데이터를 저장.

---

# 5.12 S3 정적 웹사이트 호스팅

S3는 정적 파일을 웹사이트처럼 제공할 수 있음.

즉, 서버 없이 HTML/CSS/JS 파일만으로 구성된 웹사이트를 만들 수 있음.

적합한 경우

* 회사 소개 페이지

* 실습용 정적 페이지

* 프론트엔드 정적 배포

* CloudFront 원본 저장소

제한사항

* 서버 사이드 코드 실행 불가

* PHP, Java, Node.js 백엔드는 직접 실행 못함

즉, S3 웹사이트 호스팅은 “파일 배포”이지 “애플리케이션 서버 운영”은 아님.

---

# 5.13 공유 파일 시스템 개요

S3가 객체 스토리지라면, EFS와 FSx는 **공유 파일 시스템**임.

여러 서버가 같은 파일 시스템을 동시에 사용해야 할 때 필요함.

예

* 여러 웹 서버가 같은 업로드 디렉터리 사용

* 여러 애플리케이션 서버가 공통 설정 파일 공유

* 리눅스 서버 간 공용 파일 저장

* 윈도우 SMB 공유 드라이브 운영

---

# 5.14 Amazon EFS 개요

Amazon EFS는 **Elastic File System**의 약자임.

리눅스 인스턴스에서 NFS(Network File System) 방식으로 마운트해서 사용하는 관리형 파일 스토리지임.

특징

* 여러 EC2가 동시에 마운트 가능

* 자동 확장

* 관리형 서비스

* Multi-AZ 내구성

* 리눅스 기반 워크로드에 적합

EFS는 운영체제 입장에서 일반 디렉터리처럼 보임.

즉, 애플리케이션이 로컬 파일 시스템을 쓰듯 접근할 수 있음.

---

# 5.15 EFS의 사용 사례

### 1. 웹 서버 공용 업로드 디렉터리

ALB 뒤에 여러 대의 EC2가 있을 때, 사용자 업로드 파일을 공용 저장소에 저장해야 함.

### 2. 콘텐츠 공유

여러 서버가 같은 정적 콘텐츠를 공유해야 할 때 사용함.

### 3. 애플리케이션 설정 공유

공용 설정 파일, 공용 템플릿 파일 저장.

### 4. 컨테이너 공유 스토리지

ECS/EKS 환경에서 공유 파일 저장소로 활용 가능함.

---

# 5.16 EFS와 EBS 비교

| 항목 | EBS | EFS |
| --- | --- | --- |
| 연결 방식 | 보통 한 인스턴스에 연결 | 여러 인스턴스 동시 연결 가능 |
| 저장 방식 | 블록 스토리지 | 파일 스토리지 |
| 접근 방식 | 디스크 | NFS 파일 시스템 |
| 대표 용도 | OS 디스크, 단일 서버 데이터 | 공유 파일 저장 |

즉

* **EBS는 한 서버용 디스크**

* **EFS는 여러 서버가 공유하는 파일 시스템**

으로 보면 됨.

---

# 5.17 Amazon FSx 개요

FSx는 특정 파일 시스템을 AWS 관리형으로 제공하는 서비스군임.

대표 서비스

* FSx for Windows File Server

* FSx for Lustre

* FSx for NetApp ONTAP

* FSx for OpenZFS

### FSx for Windows File Server

SMB 기반 윈도우 파일 공유가 필요할 때 사용함.

### FSx for Lustre

고성능 분석, HPC, 머신러닝 학습 데이터 처리에 적합함.

---

# 5.18 스토리지 선택 기준 정리

| 요구사항 | 적합한 서비스 |
| --- | --- |
| 정적 파일 저장 | S3 |
| 백업 및 로그 저장 | S3 |
| EC2 루트 디스크 | EBS |
| 여러 EC2 간 공유 디렉터리 | EFS |
| Windows 공유 폴더 | FSx for Windows File Server |
| 초고성능 분석 파일 시스템 | FSx for Lustre |

---

# 5.19 실습 1 : S3 버킷 생성 및 객체 업로드

실습 목표

* S3 버킷을 생성함

* 파일을 업로드함

* 객체 URL 구조를 이해함

* CLI로 객체를 조회함

---

## 5.19.1 버킷 생성

S3 콘솔 → Create bucket

설정 예

| 항목 | 값 |
| --- | --- |
| Bucket name | 이니셜-arc-s3-bucket-고유값 |
| Region | ap-northeast-2 |
| Block Public Access | 기본값 유지 |
| Versioning | 비활성 또는 필요 시 활성 |

주의

* 버킷 이름은 전 세계적으로 유일해야 함

* 이미 누군가 사용 중인 이름이면 생성 불가

예시 이름

```
kyt-arc-s3-bucket-20260316
```

---

## 5.19.2 파일 업로드

버킷 생성 후 `Upload`를 눌러 임의의 파일 1~2개 업로드함.

예

* sample.txt

* image.png

업로드가 끝나면 객체 목록에서 파일 이름과 크기, 수정 시간을 확인할 수 있음.

---

## 5.19.3 CLI로 버킷 목록 확인

```
aws s3ls
```

### 명령어 설명

### `aws s3`

S3 고수준 명령 그룹임.

버킷 목록 조회, 파일 업로드, 다운로드 등 자주 쓰는 기능을 간단하게 제공함.

### `ls`

리스트를 조회하는 명령임.

리눅스의 `ls`처럼 목록을 보여주는 역할을 함.

이 명령을 실행하면 현재 계정에서 접근 가능한 버킷 목록이 출력됨.

---

## 5.19.4 특정 버킷의 객체 목록 확인

```
aws s3ls s3://이니셜-arc-s3-bucket-고유값
```

예

```
aws s3ls s3://kyt-arc-s3-bucket-20260316
```

이 명령은 해당 버킷 안에 저장된 객체 목록을 조회함.

출력 예

```
2026-03-16 10:20:31       1240 sample.txt
2026-03-16 10:21:02      50231 image.png
```

---

# 5.20 실습 2 : CLI로 파일 업로드 및 다운로드

실습 목표

* AWS CLI를 사용해 객체를 업로드함

* 객체를 다운로드함

* `cp` 명령 구조를 익힘

---

## 5.20.1 파일 업로드

로컬 또는 CloudShell에 테스트 파일 생성

```
echo"hello s3" > sample.txt
```

이 명령은 현재 디렉터리에 `sample.txt` 파일을 만들고

그 안에 `hello s3` 문자열을 저장함.

업로드 명령

```
aws s3cp sample.txt s3://이니셜-arc-s3-bucket-고유값/
```

예

```
aws s3cp sample.txt s3://kyt-arc-s3-bucket-20260316/
```

### 명령어 설명

### `cp`

copy의 약자임.

로컬 ↔ S3, S3 ↔ 로컬, S3 ↔ S3 간 파일 복사에 사용함.

### `sample.txt`

업로드할 원본 파일임.

### `s3://.../`

대상 버킷 경로임.

즉, 이 명령은 로컬의 `sample.txt`를 S3 버킷 루트 경로에 업로드함.

---

## 5.20.2 파일 다운로드

```
aws s3 cp s3://이니셜-arc-s3-bucket-고유값/sample.txt ./downloaded.txt
```

예

```
aws s3 cp s3://kyt-arc-s3-bucket-20260316/sample.txt ./downloaded.txt
```

이 명령은 S3 객체를 현재 디렉터리에 `downloaded.txt`라는 이름으로 저장함.

확인

```
cat downloaded.txt
```

정상 동작 시

```
hello s3
```

가 출력됨.

---

# 5.21 실습 3 : S3 정적 웹사이트 호스팅

실습 목표

* HTML 파일을 업로드함

* S3 정적 웹사이트 기능을 활성화함

* 브라우저에서 페이지를 확인함

---

## 5.21.1 index.html 파일 생성

```
cat > index.html<<'EOF'
<h1>Welcome to S3 Static Website</h1>
EOF
```

이 명령은 `index.html` 파일을 생성하고 HTML 내용을 저장함.

---

## 5.21.2 파일 업로드

```
aws s3cp index.html s3://이니셜-arc-s3-bucket-고유값/
```

---

## 5.21.3 정적 웹사이트 활성화

S3 콘솔 → 버킷 선택 → Properties → Static website hosting

설정

| 항목 | 값 |
| --- | --- |
| Static website hosting | Enable |
| Hosting type | Host a static website |
| Index document | index.html |

---

## 5.21.4 공개 접근 정책 설정

정적 웹사이트는 외부 사용자가 HTML 파일을 읽어야 하므로 공개 정책이 필요함.

이때 Block Public Access 설정과 Bucket Policy가 함께 관련됨.

실습용 예시 Bucket Policy

```
{
  "Version":"2012-10-17",
  "Statement": [
    {
      "Sid":"PublicReadGetObject",
      "Effect":"Allow",
      "Principal":"*",
      "Action":"s3:GetObject",
      "Resource":"arn:aws:s3:::이니셜-arc-s3-bucket-고유값/*"
    }
  ]
}
```

주의

* 이 정책은 실습용 공개 읽기 예시임

* 운영 환경에서는 CloudFront를 앞단에 두고 더 안전하게 구성하는 것이 일반적임

---

## 5.21.5 웹사이트 접속 확인

Properties 탭의 Website endpoint 주소를 복사해 브라우저에서 접속함.

예시 형태

```
http://bucket-name.s3-website.ap-northeast-2.amazonaws.com
```

정상 동작 시

```
Welcome to S3 Static Website
```

가 표시됨.

---

# 5.22 실습 4 : EFS 생성 및 EC2 마운트

실습 목표

* EFS 파일 시스템을 생성함

* EC2에 NFS 방식으로 마운트함

* 공유 파일 시스템 개념을 확인함

---

## 5.22.1 사전 준비

필요 자원

* VPC

* Private 또는 Public Subnet의 EC2

* EC2가 EFS에 접근 가능한 보안 그룹

---

## 5.22.2 EFS 생성

EFS 콘솔 → Create file system

설정 예

| 항목 | 값 |
| --- | --- |
| Name | 이니셜-efs-share |
| VPC | 이니셜-vpc-main |
| Availability and durability | Regional |
| Performance mode | General Purpose |

생성 과정에서 각 AZ에 대한 Mount Target이 생성됨.

---

## 5.22.3 EFS 보안 그룹

EFS는 NFS 프로토콜을 사용하므로 **2049/TCP** 포트를 허용해야 함.

예시 규칙

| 방향 | 프로토콜 | 포트 | 소스 |
| --- | --- | --- | --- |
| Inbound | TCP | 2049 | EC2 보안 그룹 |

중요

* 보안상 `0.0.0.0/0`로 열지 않는 것이 좋음

* 가능하면 EC2의 보안 그룹을 소스로 지정하는 방식이 바람직함

---

## 5.22.4 EC2에 패키지 설치

Amazon Linux 계열에서 실행

```
sudo dnf install -y amazon-efs-utils
```

### 명령어 설명

### `amazon-efs-utils`

AWS EFS를 보다 쉽게 마운트할 수 있도록 도와주는 유틸리티 패키지임.

이 패키지를 설치하면 단순 NFS 마운트보다 편리하게 EFS 전용 방식으로 연결할 수 있음.

---

## 5.22.5 마운트 디렉터리 생성

```
sudo mkdir /efs
```

이 디렉터리는 EFS를 연결할 마운트 지점임.

---

## 5.22.6 EFS 마운트

```
sudo mount -t efs <EFS-파일시스템ID>:/ /efs
```

예

```
sudo mount -t efs fs-0abc123def4567890:/ /efs
```

### 명령어 설명

### `mount`

파일 시스템을 특정 디렉터리에 연결하는 명령임.

### `-t efs`

파일 시스템 유형을 EFS로 지정함.

### `fs-...:/`

EFS 파일 시스템 ID와 루트 경로를 의미함.

### `/efs`

마운트 대상 디렉터리임.

정상적으로 마운트되면 `/efs` 디렉터리가 EFS 저장소와 연결됨.

---

## 5.22.7 동작 확인

```
df -h
```

이 명령은 현재 마운트된 파일 시스템 목록을 보여줌.

여기서 EFS가 `/efs`에 연결되어 있는지 확인함.

테스트 파일 생성

```
echo "hello efs" | sudo tee /efs/test.txt
```

확인

```
cat /efs/test.txt
```

정상 동작 시

```
hello efs
```

가 출력됨.

---

# 5.23 EFS 활용 시나리오 설명

예를 들어 웹 서버가 2대 있다고 가정해보면

```
ALB
 ├ EC2-Web-1
 └ EC2-Web-2
```

이때 두 서버가 같은 업로드 디렉터리를 사용해야 하면 각 서버의 로컬 디스크를 쓰면 안 됨.

한 서버에 올린 파일이 다른 서버에는 없기 때문임.

이 문제를 해결하는 방식 중 하나가 EFS임.

```
ALB
 ├ EC2-Web-1 ─┐
 └ EC2-Web-2 ─┼─ EFS
```

즉, 두 서버가 같은 파일 시스템을 바라보게 만들어 업로드 파일을 공유할 수 있음.

---

# 5.24 스토리지 아키텍처 설계 포인트

### 1. 저장 방식부터 구분해야 함

* 객체 저장인가

* 블록 저장인가

* 파일 공유인가

### 2. 접근 패턴을 봐야 함

* 자주 읽는가

* 거의 안 읽는가

* 여러 서버가 동시에 접근하는가

### 3. 비용과 보관 기간을 고려해야 함

* 최근 데이터는 Standard

* 오래된 데이터는 IA/Glacier

* Lifecycle 자동화 고려

### 4. 보안 설정이 매우 중요함

* S3 Public Access 차단

* IAM 최소 권한

* EFS 보안 그룹 제한

* 암호화 활성화