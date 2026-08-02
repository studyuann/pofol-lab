---
title: "5장 Cloud Storage"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Google 클라우드 핵심 서비스"]
is_public: true
draft: false
---

# 5장. Cloud Storage

## 1. 장 개요

이 장에서는 Google Cloud의 객체 스토리지 서비스인 **Cloud Storage**를 학습한다.

Compute Engine이 서버를 실행하는 서비스였다면, Cloud Storage는 파일, 이미지, 백업, 로그, 정적 콘텐츠 같은 **비정형 데이터**를 저장하는 대표 서비스다. Google Cloud는 Cloud Storage를 관리형 비정형 데이터 저장 서비스로 설명한다.

AWS를 먼저 학습한 상태라면 보통 다음 감각이 익숙하다.

* S3 버킷을 생성한다

* 객체를 업로드하고 다운로드한다

* 정적 파일을 저장한다

* 권한은 IAM, Bucket Policy, ACL 등으로 제어한다

* Storage Class와 Lifecycle로 비용을 최적화한다

GCP에서도 큰 흐름은 비슷하지만, 다음 차이를 확실히 이해하는 것이 중요하다.

* 버킷 이름은 **전역적으로 고유**해야 한다.

* Cloud Storage는 객체를 버킷에 저장하며, 폴더는 필요하면 논리적으로 구성하는 개념이다.

* 스토리지 클래스는 Standard, Nearline, Coldline, Archive 등으로 구분한다.

* 비용 최적화를 위해 **Object Lifecycle Management**로 자동 전환/삭제를 설정할 수 있다.

* 접근 제어는 가능하면 **IAM 중심**, 특히 **Uniform bucket-level access**를 사용하는 것이 권장된다. Uniform bucket-level access를 켜면 ACL은 비활성화되고 버킷 수준 IAM만 사용한다.

* Google은 CLI 작업 시 `gsutil`보다 `gcloud storage` **명령 사용을 권장**한다.

즉, 이 장은 단순히 파일을 올리는 법을 배우는 장이 아니라,

**GCP에서 객체 데이터를 어떻게 저장하고, 어떤 보안 모델로 관리하고, 어떻게 비용을 최적화하는지**를 익히는 장이다.

---

## 2. 학습 목표

* Cloud Storage의 기본 개념을 설명할 수 있음

* 버킷과 객체의 차이를 설명할 수 있음

* Cloud Storage와 Amazon S3의 공통점과 차이를 설명할 수 있음

* 주요 Storage Class의 용도를 설명할 수 있음

* Object Lifecycle Management의 목적을 설명할 수 있음

* Uniform bucket-level access의 의미를 설명할 수 있음

* `gcloud storage` 명령으로 버킷 생성, 업로드, 조회, 다운로드를 수행할 수 있음

* 버킷에 IAM 기반 접근 제어를 적용할 수 있음

* 정적 파일 저장, 로그 저장, 백업 저장 시나리오를 설명할 수 있음

---

## 3. 핵심 키워드

* Cloud Storage

* Bucket

* Object

* Object Storage

* Storage Class

* Standard

* Nearline

* Coldline

* Archive

* Lifecycle

* Uniform bucket-level access

* IAM

* Public Access

* gcloud storage

* gsutil

---

# 4. Cloud Storage란 무엇인가

Cloud Storage는 Google Cloud의 **객체 스토리지 서비스**다.

Google 공식 문서는 객체를 “파일 형식에 상관없이 저장되는 변경 불가능한 데이터 조각”으로 설명하고, 이 객체들을 **버킷**이라는 컨테이너 안에 저장한다고 설명한다.

## 쉽게 이해하면

* AWS S3와 가장 직접적으로 대응되는 서비스

* 파일 저장소처럼 보이지만 실제로는 객체 단위 저장 구조

* 이미지, 백업, 로그, 업로드 파일, 정적 웹 자원 등에 매우 자주 사용됨

## 언제 사용하는가

* 애플리케이션 업로드 파일 저장

* 로그 및 백업 저장

* 정적 웹 자원 저장

* 데이터 분석용 파일 저장

* 장기 보관 아카이브 저장

---

# 5. 버킷과 객체

## 5.1 버킷이란 무엇인가

버킷은 객체를 담는 최상위 컨테이너다.

모든 객체는 반드시 어떤 버킷 안에 저장되어야 한다. Cloud Storage 문서도 버킷이 데이터를 담는 기본 컨테이너라고 설명한다.

### 특징

* 버킷 이름은 전역적으로 고유해야 함

* 위치(Location)와 기본 Storage Class를 가짐

* Lifecycle, 접근 제어, 버전 관리 같은 설정을 가질 수 있음

## 5.2 객체란 무엇인가

객체는 실제 저장되는 데이터다.

예시

* `index`

* `logo.png`

* `backup-2026-03-17.sql`

* `logs/app-2026-03-17.log`

### 특징

* 파일처럼 보이지만 내부적으로는 객체 단위 저장

* 객체는 변경 불가능(immutable) 데이터로 다뤄짐

* 같은 이름으로 다시 업로드하면 사실상 새 객체로 교체되는 감각으로 이해하면 됨

## 5.3 폴더는 실제 디렉터리인가

Cloud Storage는 필요하면 폴더처럼 보이도록 객체 이름을 구성할 수 있다고 설명한다. 즉, 전통적인 파일 시스템 디렉터리와 완전히 같은 개념으로 이해하면 안 된다.

예를 들어

* `images/logo.png`

* `backup/db/2026-03-17.sql`

같은 식으로 경로처럼 보이게 저장할 수 있다.

---

# 6. AWS S3와의 비교

## 6.1 공통점

* 버킷/객체 구조를 사용함

* 정적 파일, 백업, 로그 저장에 적합함

* 스토리지 클래스와 Lifecycle 관리가 가능함

* IAM 기반 접근 제어가 중요함

## 6.2 차이점

* GCP는 **Uniform bucket-level access**를 통해 ACL을 끄고 IAM 중심 관리로 단순화하는 방식을 강하게 권장한다.

* CLI 측면에서는 `gsutil`이 오래 쓰였지만 현재는 `gcloud storage` 사용이 권장된다.

* Storage Class 명칭과 비용 모델이 다르다.

---

# 7. 버킷 이름과 위치

## 7.1 버킷 이름

버킷 이름은 전역 네임스페이스 안에서 고유해야 한다. Google 공식 가이드도 버킷 생성 시 전역적으로 고유한 이름을 사용해야 한다고 설명한다.

### 실습에서 자주 쓰는 방식

고유 이름을 만들기 위해 아래처럼 접두어를 붙인다.

* `initial-storage-홍길동-20260317`

* `gcp-lab-abc123-storage`

* `myproj-static-20260317`

## 7.2 위치(Location)

버킷은 생성 시 위치를 가진다.

대표 개념

* Region

* Dual-region

* Multi-region

버킷 위치와 기본 Storage Class는 생성 시 중요한 속성이다.

---

# 8. Storage Class

Cloud Storage는 스토리지 클래스를 제공하고, 각 클래스는 접근 패턴과 비용 구조에 따라 적합한 용도가 다르다.

## 8.1 Standard

자주 접근하는 데이터에 적합하다.

### 예시

* 웹 애플리케이션 업로드 파일

* 정적 웹 자원

* 분석용 핫 데이터

* 자주 읽는 백업 파일

## 8.2 Nearline

한 달에 한 번 정도 이하로 접근하는 데이터에 적합하다.

### 예시

* 월 단위 백업

* 드물게 복구하는 파일

## 8.3 Coldline

더 드물게 접근하는 데이터에 적합하다.

### 예시

* 장기 보관 백업

* 분기 단위 아카이브

## 8.4 Archive

가장 장기 보관용에 가까운 클래스다.

### 예시

* 규제 보관 데이터

* 거의 접근하지 않는 장기 보존 데이터

---

# 9. Lifecycle 관리

Cloud Storage는 **Object Lifecycle Management** 기능을 제공하며, TTL 설정, 비최신 버전 유지, 스토리지 클래스 다운그레이드, 자동 삭제 같은 시나리오를 지원한다. 이 기능은 **버킷에 설정된 규칙**이 현재 및 미래 객체에 적용되는 방식이다.

## 9.1 왜 필요한가

사람이 일일이 오래된 파일을 정리하거나 클래스 변경을 하면 운영 비용이 커진다.

Lifecycle 규칙을 설정하면 자동으로 비용 최적화가 가능하다.

## 9.2 대표 시나리오

* 30일 후 Nearline으로 전환

* 90일 후 Coldline으로 전환

* 365일 후 삭제

* 이전 버전 객체를 일정 기간 후 삭제

---

# 10. 버전 관리

Cloud Storage는 객체 버전 관리 기능을 제공할 수 있다.

같은 이름으로 덮어쓸 가능성이 있는 파일, 복원 가능성이 필요한 파일에서 유용하다.

## 언제 유용한가

* 실수로 덮어쓴 파일 복구

* 배포 아티팩트 이력 관리

* 백업 파일 보존

버전 관리는 유용하지만 저장량 증가로 이어질 수 있으므로 Lifecycle과 함께 봐야 한다.

---

# 11. 접근 제어: IAM 중심으로 보기

Cloud Storage 접근 제어는 가능하면 **버킷 수준 IAM 중심**으로 이해하는 것이 좋다. Google은 Uniform bucket-level access 사용을 일반적으로 권장하며, 이 기능이 켜지면 버킷과 객체 ACL이 비활성화되고 버킷 수준 IAM만 사용된다. ACL 기반 노출 위험을 줄이고 접근 제어를 단순화한다.

## 11.1 Uniform bucket-level access

이 기능을 켜면 다음이 핵심이다.

* ACL 사용 중지

* 버킷 수준 IAM 권한만 사용

* 권한 관리 방식 단순화

* 일부 기능 사용을 위한 선행 조건이 되기도 함

## 11.2 왜 권장되는가

* 권한 모델이 단순해짐

* 객체별 ACL로 인한 의도치 않은 공개를 줄임

* IAM 중심 운영과 잘 맞음

---

# 12. gsutil과 gcloud storage

Cloud Storage를 명령행에서 다루는 도구로 오래전부터 `gsutil` 이 많이 쓰였지만, 현재 `gsutil` **이 권장 CLI가 아니며** `gcloud storage` **명령 사용을 권장**한다.

## 12.1 gsutil

* 전통적으로 많이 사용됨

* 자료와 예제가 많음

* 아직도 많이 보게 됨

## 12.2 gcloud storage

* 현재 권장되는 방식

* Google Cloud CLI 흐름과 더 일관적임

* 새로운 교육에서는 이쪽으로 가는 편이 좋음

---

# 13. 기본 실습 아키텍처

이번 장의 실습은 다음 흐름으로 구성하면 좋다.

* 고유한 버킷 생성

* 로컬 파일 생성

* 파일 업로드

* 버킷/객체 조회

* 파일 다운로드

* 버킷 IAM 확인

* Lifecycle 개념 확인

* 필요 시 공개 접근 테스트

---

# 14. 실습 1: 현재 프로젝트 확인

## 명령어

```
gcloud config get-value project
```

### 설명

Cloud Storage 버킷도 현재 프로젝트 기준으로 생성·관리된다.

버킷 이름은 전역 고유지만, 과금과 IAM 관리 등은 프로젝트와 연결된다.

---

# 15. 실습 2: 고유한 버킷 이름 변수 준비

버킷 이름은 전역적으로 고유해야 하므로 변수로 만드는 습관이 좋다.

## 명령어

```
PROJECT_ID=$(gcloud config get-value project)
BUCKET_NAME="${PROJECT_ID}-storage-$(date +%Y%m%d%H%M%S)"
echo$BUCKET_NAME
```

### 설명

* 현재 프로젝트 ID를 읽어옴

* 시간값을 붙여 고유한 버킷 이름을 만듦

* 이름 충돌 가능성을 낮춤

---

# 16. 실습 3: 버킷 생성

Google Cloud CLI 예제는 `gcloud storage buckets create` 명령으로 버킷을 생성하도록 안내하며, 예시로 `--uniform-bucket-level-access` 옵션을 함께 사용한다.

## 명령어

```
gcloud storage buckets create gs://$BUCKET_NAME \
--location=asia-northeast3 \
--default-storage-class=STANDARD \
--uniform-bucket-level-access
```

## 명령 설명

* `gcloud storage buckets create`

  새 버킷을 생성하는 명령이다.

* `gs://$BUCKET_NAME`

  생성할 버킷 이름이다. Cloud Storage 버킷은 `gs://` 스킴으로 표현한다.

* `--location=asia-northeast3`

  버킷 위치를 서울 리전으로 지정한다.

* `--default-storage-class=STANDARD`

  기본 스토리지 클래스를 Standard로 지정한다.

* `--uniform-bucket-level-access`

  Uniform bucket-level access를 활성화한다.

### 실습 포인트

이번 실습은 업로드 테스트가 목적이므로 Standard가 가장 직관적이다.

접근 제어는 IAM 중심으로 보기 위해 Uniform bucket-level access를 켠다.

---

# 17. 실습 4: 버킷 확인

## 버킷 목록 조회

```
gcloud storage ls
```

## 특정 버킷 상세 확인

```
gcloud storage buckets describe gs://$BUCKET_NAME
```

### 확인 포인트

* 위치가 `asia-northeast3` 인가

* 기본 스토리지 클래스가 `STANDARD` 인가

* Uniform bucket-level access 상태가 활성화되었는가

---

# 18. 실습 5: 업로드할 테스트 파일 만들기

## 명령어

```
mkdir -p ~/gcs-lab
cat > ~/gcs-lab/index<<'EOF'
<h1>Cloud Storage Lab</h1>
<p>This file was uploaded to Google Cloud Storage.</p>
EOF

echo "backup-data-$(date)" > ~/gcs-lab/backup.txt
ls -l ~/gcs-lab
```

### 설명

* HTML 파일과 일반 텍스트 파일을 준비한다.

* 이후 객체 업로드와 다운로드를 테스트한다.

---

# 19. 실습 6: 객체 업로드

## 단일 파일 업로드

```
gcloud storage cp ~/gcs-lab/index gs://$BUCKET_NAME/
```

## 추가 파일 업로드

```
gcloud storage cp ~/gcs-lab/backup.txt gs://$BUCKET_NAME/
```

## 폴더처럼 보이게 업로드

```
gcloud storage cp ~/gcs-lab/backup.txt gs://$BUCKET_NAME/backups/backup.txt
```

### 설명

* `gcloud storage cp` 는 로컬 파일을 버킷으로 업로드하거나 반대로 다운로드할 때 사용한다.

* `backups/backup.txt` 처럼 지정하면 폴더처럼 보이는 경로로 객체를 저장할 수 있다.

---

# 20. 실습 7: 객체 목록 조회

## 버킷 내용 조회

```
gcloud storage ls gs://$BUCKET_NAME
```

## 하위 경로까지 포함해 조회

```
gcloud storage ls --recursive gs://$BUCKET_NAME
```

### 기대 결과

* `index`

* `backup.txt`

* `backups/backup.txt`

---

# 21. 실습 8: 객체 다운로드

## 명령어

```
mkdir-p ~/gcs-download
gcloud storage cp gs://$BUCKET_NAME/index ~/gcs-download/
gcloud storage cp gs://$BUCKET_NAME/backups/backup.txt ~/gcs-download/
ls -l ~/gcs-download
```

### 설명

버킷 안의 객체를 로컬로 다운로드해서 파일이 정상적으로 저장되는지 확인한다.

---

# 22. 실습 9: gsutil도 함께 비교해보기

공식적으로는 `gcloud storage` 사용이 권장되지만, `gsutil` 도 여전히 많이 보인다. 공식 문서도 `gsutil` 은 권장 CLI가 아니라고 명시한다.

## 예시 명령

```
gsutills gs://$BUCKET_NAME
```

---

# 23. 실습 10: IAM 권한 확인

## 버킷 IAM 정책 조회

```
gcloud storage buckets get-iam-policy gs://$BUCKET_NAME
```

### 설명

버킷 수준에서 어떤 IAM 바인딩이 있는지 확인한다.

---

# 24. 실습 11: 공개 읽기 테스트용 IAM 부여 예시

> 이 실습은 교육 환경에서만 신중하게 사용해야 함
>
> 실습 후 반드시 원복하는 것이 좋음

Uniform bucket-level access 상태에서는 공개 읽기 같은 것도 IAM 역할로 부여한다.

## 명령어

```
gcloud storage buckets add-iam-policy-binding gs://$BUCKET_NAME \
--member=allUsers \
--role=roles/storage.objectViewer
```

### 설명

* `allUsers` 는 익명 사용자 전체를 의미한다.

* `roles/storage.objectViewer` 는 객체 읽기 권한이다.

* 버킷 자체 목록이 아니라 객체 읽기 권한 중심으로 이해하면 된다.

## 공개 URL 테스트

```
https://storage.googleapis.com/BUCKET_NAME/index
```

예시

```
https://storage.googleapis.com/my-bucket-name/index
```

### 실습 후 원복

```
gcloud storage buckets remove-iam-policy-binding gs://$BUCKET_NAME \
--member=allUsers \
--role=roles/storage.objectViewer
```

---

# 25. 실습 12: Lifecycle 규칙 파일 작성

Object Lifecycle Management는 버킷에 적용되는 규칙 집합이다. 현재와 미래 객체에 모두 적용될 수 있고, TTL·자동 삭제·클래스 전환 같은 용도로 사용한다.

## 예시 규칙

* 생성 후 30일이 지난 객체를 Nearline으로 전환

* 생성 후 365일이 지난 객체를 삭제

## 파일 작성

```
cat > lifecycle.json<<'EOF'
{
  "rule": [
    {
      "action": { "type": "SetStorageClass", "storageClass": "NEARLINE" },
      "condition": { "age": 30 }
    },
    {
      "action": { "type": "Delete" },
      "condition": { "age": 365 }
    }
  ]
}
EOF
```

### 설명

* `SetStorageClass` 는 객체 클래스를 변경한다.

* `Delete` 는 조건을 만족한 객체를 삭제한다.

* `age` 는 객체 생성 후 경과 일수다.

---

# 26. 실습 13: Lifecycle 적용

## 명령어

```
gcloud storage buckets update gs://$BUCKET_NAME \
--lifecycle-file=lifecycle.json
```

## 적용 결과 확인

```
gcloud storage buckets describe gs://$BUCKET_NAME
```

### 확인 포인트

버킷 상세 정보에 lifecycle 관련 설정이 반영되었는지 확인한다.

---

# 27. 실습 14: 버킷 삭제 전 객체 정리

버킷은 내부에 객체가 남아 있으면 삭제되지 않는 경우가 많으므로, 먼저 객체를 지우는 흐름을 익혀두는 것이 좋다.

## 객체 삭제

```
gcloud storage rm --recursive gs://$BUCKET_NAME/**
```

## 버킷 삭제

```
gcloud storage buckets delete gs://$BUCKET_NAME
```

---

# 28. 정적 파일 저장 시나리오 설명

Cloud Storage는 다음처럼 정적 파일 저장소로 자주 쓰인다.

* 이미지 업로드 저장소

* 웹 정적 자원(css/js/image) 저장소

* 배포 아티팩트 저장소

* 백업 파일 저장소

### AWS 비교

* S3를 정적 파일/백업 저장소로 쓰는 것과 동일한 감각

* 다만 공개 접근과 IAM 구조는 GCP 방식으로 다시 적응해야 함

---

# 29. 장 요약

* Cloud Storage는 비정형 데이터를 저장하는 객체 스토리지 서비스다.

* 데이터는 버킷 안에 객체 형태로 저장된다. 객체는 변경 불가능한 데이터 조각이다.

* 버킷 이름은 전역적으로 고유해야 한다.

* Storage Class는 접근 빈도와 보관 목적에 따라 선택한다.

* Lifecycle 규칙으로 클래스 전환과 자동 삭제를 설정할 수 있다.

* 접근 제어는 가능하면 IAM 중심, 특히 Uniform bucket-level access 기준으로 설명하는 것이 좋다.

* 명령행 도구는 `gsutil` 보다 `gcloud storage` 사용이 권장된다.