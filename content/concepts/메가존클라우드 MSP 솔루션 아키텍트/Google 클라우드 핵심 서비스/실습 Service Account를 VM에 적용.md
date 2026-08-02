---
title: "실습 Service Account를 VM에 적용"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Google 클라우드 핵심 서비스"]
is_public: true
draft: false
---

# 실습. Service Account를 VM에 적용

---

## 1단계: Cloud Storage 버킷 및 파일 준비

### **[Console]**

1. **Cloud Storage > 버킷** 메뉴로 이동한다.

2. **[만들기]** 클릭 후 버킷 이름 입력 (예: `practice-bucket-sunny-123`).

3. 다른 설정은 기본값으로 두고 **[만들기]** 완료.

4. 버킷 상세 화면에서 **[파일 업로드]** 클릭 후 아무 텍스트 파일(`test.txt`)이나 올린다.

### **[CLI]**

```
# 버킷 생성
gcloud storage buckets create gs://practice-bucket-$(date +%s)

# 파일 업로드
echo "CLI Test File" > test.txt
gcloud storage cp test.txt gs://[위에서생성한_버킷이름]/
```

---

## 2단계: 서비스 계정(SA) 생성 및 권한 부여

이 단계의 목적은 VM이 가질 '신분증'에 '읽기 권한'만 넣는 것이다.

### **[Console]**

1. **IAM 및 관리자 > 서비스 계정**으로 이동한다.

2. **[서비스 계정 만들기]** 클릭.
   * 이름: `gcs-reader-sa` 입력 후 [만들기 및 계속하기].

3. **역할 선택:** `Storage 객체 조회자` (Storage Object Viewer) 선택.

4. [완료] 클릭. (키 파일은 생성/다운로드하지 않는다!)

### **[CLI]**

```
# 서비스 계정 생성
gcloud iam service-accounts create gcs-reader-sa --display-name="GCS Reader SA"

# 권한(Role) 부여
gcloud projects add-iam-policy-binding [PROJECT_ID] \
    --member="serviceAccount:gcs-reader-sa@[PROJECT_ID].iam.gserviceaccount.com" \
    --role="roles/storage.objectViewer"
```

---

## 3단계: VM 생성 및 서비스 계정 할당

### **[Console]**

1. **Compute Engine > VM 인스턴스 > [인스턴스 만들기]** 클릭.

2. **네트워킹:** 외부 IP를 `없음`으로 설정 (보안상 IAP 접속 환경 조성).

3. **서비스 계정(중요):** 하단의 'ID 및 API 액세스' 섹션에서 방금 만든 `gcs-reader-sa`를 선택한다.

4. **액세스 범위:** `모든 Cloud API에 대한 전체 액세스 허용` 선택. (실제 권한은 SA가 가진 역할로 제어된다.)

5. [만들기] 클릭.

### **[CLI]**

```
gcloud compute instances create gcs-practice-vm \
    --zone=asia-northeast3-a \
    --no-address \
    --service-account="gcs-reader-sa@[PROJECT_ID].iam.gserviceaccount.com" \
    --scopes="https://www.googleapis.com/auth/cloud-platform"
```

---

## 4단계: 결과 확인 (VM 내부 실습)

### **[공통 확인 방법]**

IAP를 통해 접속한 후 권한을 확인한다.

1. **접속:**
   * **Console:** VM 목록 옆의 [SSH] 버튼 클릭 (IAP 자동 작동).
   * **CLI:** `gcloud compute ssh gcs-practice-vm --tunnel-through-iap`

2. **VM 내부에서 조회 테스트:**

   ```
   # 1. 현재 어떤 신분으로 인증되어 있는지 확인
   gcloud auth list
   # (결과에 gcs-reader-sa 이메일이 보여야 함)

   # 2. 버킷 목록 및 파일 내용 확인
   gcloud storage ls gs://[내_버킷_이름]/
   gcloud storage cat gs://[내_버킷_이름]/test.txt
   ```

---