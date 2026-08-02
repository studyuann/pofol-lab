---
title: "실습 GCP API Gateway + Cloud Run + Firestore 조합으로 간단"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Google 쿠버네티스 아키텍처 설계 및 구축"]
is_public: true
draft: false
---

# **실습. GCP API Gateway + Cloud Run + Firestore** 조합으로 간단한 **서버리스 메모 API 생성**

# 1. 실습 목표

* Firestore 데이터베이스를 생성한다.

* Cloud Run에 Node.js 기반 REST API를 배포한다.

* API Gateway를 생성해 Cloud Run 앞단에 둔다.

* API Key를 이용해 Gateway를 통해서만 API를 호출해본다.

* Firestore에 데이터가 저장되는지 확인한다.

---

# 2. 실습 시나리오

간단한 메모 API를 만든다.

구현할 기능은 다음과 같다.

* `GET /health` : 상태 확인

* `POST /notes` : 메모 등록

* `GET /notes` : 메모 목록 조회

* `GET /notes/{id}` : 메모 단건 조회

* `DELETE /notes/{id}` : 메모 삭제

데이터는 Firestore의 `notes` 컬렉션에 저장한다.

---

# 3. 사전 준비

## 3-1. 준비 항목

* GCP 프로젝트 1개

* 과금 계정 연결

* 로컬 PC에 `gcloud` 설치 및 인증 완료

* Node.js 20 이상 권장

* 작업용 터미널

## 3-2. 사용할 리전 예시

* Cloud Run: `asia-northeast3` (서울)

* Firestore: 가까운 리전으로 선택  
  Firestore는 데이터베이스 생성 시 데이터 액세스 모드와 리전을 선택한다. Native mode가 새 앱에 권장된다.

---

# 4. 전체 아키텍처

```
[사용자]
   │
   ▼
[API Gateway]
   │
   ▼
[Cloud Run - notes-api]
   │
   ▼
[Firestore Native mode]
```

---

# 5. 실습용 환경 변수 설정

먼저 프로젝트 값을 변수로 잡아두고 진행한다.

```
export PROJECT_ID="YOUR_PROJECT_ID"
export REGION="asia-northeast3"
export SERVICE_NAME="notes-api"
export API_ID="notes-api"
export API_CONFIG_ID="notes-api-config-v1"
export GATEWAY_ID="notes-api-gateway"
```

현재 프로젝트 설정도 맞춘다.

```
gcloud config set project $PROJECT_ID
```

설정 확인:

```
gcloud config list project
```

이 명령은 현재 gcloud 기본 프로젝트가 어디로 설정되어 있는지 보여준다.

이 값이 틀리면 Cloud Run, API Gateway, Firestore가 엉뚱한 프로젝트에 생성될 수 있으므로 먼저 확인하는 습관이 중요하다.

---

# 6. 필요한 API 활성화

실습에 필요한 주요 API를 활성화한다.

```
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  apigateway.googleapis.com \
  servicemanagement.googleapis.com \
  servicecontrol.googleapis.com \
  firestore.googleapis.com
```

API Gateway는 개발 환경 구성 시 필요한 Google 서비스 활성화를 요구한다. Cloud Run 배포도 Cloud Run Admin API, Cloud Build, Artifact Registry 사용 흐름과 연결된다.

---

# 7. Firestore 데이터베이스 생성

## 7-1. 콘솔에서 생성

1. GCP 콘솔 접속

2. **Firestore** 검색

3. **Create database** 클릭

4. **Firestore in Native mode** 선택

5. 보안 규칙은 서버 앱 실습 기준으로 기본값 또는 제한적 설정 선택

6. 리전 선택

7. 생성 완료

Firestore 데이터베이스는 콘솔에서 만들 수 있고, 생성 시 데이터 액세스 모드와 리전을 선택한다. Firestore Native mode는 새 애플리케이션에 권장된다.

## 7-2. 왜 Native mode를 쓰는가

이번 실습은 모바일/웹 연계가 아니라도 **서버 애플리케이션에서 문서 기반 NoSQL 저장소를 빠르게 사용하는 목적**에 잘 맞는다. Firestore Native mode는 자동 확장, 고성능, 애플리케이션 개발 편의성을 위해 제공된다.

---

# 8. 실습 코드 작성

## 8-1. 프로젝트 디렉터리 생성

```
mkdir gcp-serverless-notes-lab
cd gcp-serverless-notes-lab
```

## 8-2. 파일 구조

```
gcp-serverless-notes-lab/
├─ package.json
├─ index.js
└─ openapi.yaml
```

---

# 9. Cloud Run 백엔드 코드 작성

## 9-1. package.json

```
{
  "name":"notes-api",
  "version":"1.0.0",
  "description":"Serverless Notes API with Cloud Run and Firestore",
  "main":"index.js",
  "scripts": {
    "start":"node index.js"
  },
  "dependencies": {
    "@google-cloud/firestore":"^7.11.0",
    "express":"^4.21.2"
  }
}
```

### 설명

* `express`  
  HTTP 요청을 쉽게 처리하기 위한 웹 프레임워크다.

* `@google-cloud/firestore`  
  Firestore 서버 클라이언트 라이브러리다.

* `start`  
  Cloud Run은 컨테이너가 시작될 때 애플리케이션을 실행해야 하므로 시작 명령이 필요하다.

Firestore는 서버 클라이언트 라이브러리를 제공하며, Cloud Run에서는 ADC를 통해 인증을 자동 감지할 수 있다.

---

## 9-2. index.js

```
const express = require("express");
const { Firestore, FieldValue } = require("@google-cloud/firestore");

const app = express();
app.use(express.json());

const firestore = new Firestore();
const collection = firestore.collection("notes");

const PORT = process.env.PORT || 8080;

app.get("/health", async (req, res) => {
  res.status(200).json({
    status: "ok",
    service: "notes-api",
    timestamp: new Date().toISOString(),
  });
});

app.post("/notes", async (req, res) => {
  try {
    const { title, content, author } = req.body;

    if (!title || !content) {
      return res.status(400).json({
        message: "title과 content는 필수값이다.",
      });
    }

    const docRef = await collection.add({
      title,
      content,
      author: author || "anonymous",
      createdAt: FieldValue.serverTimestamp(),
      updatedAt: FieldValue.serverTimestamp(),
    });

    const savedDoc = await docRef.get();

    return res.status(201).json({
      id: docRef.id,
      ...savedDoc.data(),
    });
  } catch (error) {
    console.error("POST /notes error:", error);
    return res.status(500).json({
      message: "메모 등록 중 오류 발생",
      error: error.message,
    });
  }
});

app.get("/notes", async (req, res) => {
  try {
    const snapshot = await collection.orderBy("createdAt", "desc").get();

    const notes = snapshot.docs.map((doc) => ({
      id: doc.id,
      ...doc.data(),
    }));

    return res.status(200).json(notes);
  } catch (error) {
    console.error("GET /notes error:", error);
    return res.status(500).json({
      message: "메모 목록 조회 중 오류 발생",
      error: error.message,
    });
  }
});

app.get("/notes/:id", async (req, res) => {
  try {
    const docRef = collection.doc(req.params.id);
    const doc = await docRef.get();

    if (!doc.exists) {
      return res.status(404).json({
        message: "해당 메모가 존재하지 않음",
      });
    }

    return res.status(200).json({
      id: doc.id,
      ...doc.data(),
    });
  } catch (error) {
    console.error("GET /notes/:id error:", error);
    return res.status(500).json({
      message: "메모 단건 조회 중 오류 발생",
      error: error.message,
    });
  }
});

app.delete("/notes/:id", async (req, res) => {
  try {
    const docRef = collection.doc(req.params.id);
    const doc = await docRef.get();

    if (!doc.exists) {
      return res.status(404).json({
        message: "삭제할 메모가 존재하지 않음",
      });
    }

    await docRef.delete();

    return res.status(200).json({
      message: "메모 삭제 완료",
      id: req.params.id,
    });
  } catch (error) {
    console.error("DELETE /notes/:id error:", error);
    return res.status(500).json({
      message: "메모 삭제 중 오류 발생",
      error: error.message,
    });
  }
});

app.listen(PORT, "0.0.0.0", () => {
  console.log(`notes-api listening on port ${PORT}`);
});
```

### 설명

### `const firestore = new Firestore();`

이 코드는 Firestore 클라이언트를 생성한다.

Cloud Run 환경에서는 보통 별도의 키 파일을 코드에 넣지 않는다. Cloud Run 서비스 계정 권한이 있으면 ADC를 통해 인증이 처리된다.

### `FieldValue.serverTimestamp()`

문서 생성 시점을 Firestore 서버 시간이 기록하게 한다.

클라이언트 PC 시간이 아니라 서버 기준 시간이 들어가므로 정렬과 감사 기록에 유리하다.

### `collection.orderBy("createdAt", "desc")`

최신 메모가 위로 오도록 정렬한다.

### 예외 처리

모든 주요 API에 `try/catch`를 넣었다.

실습에서는 에러 원인을 빨리 찾는 것이 중요하므로 `console.error()`로 로그를 남긴다. Cloud Run 로그에서 바로 확인 가능하다.

---

# 10. Cloud Run 서비스 계정 권한 부여

## 10-1. 전용 서비스 계정 생성

```
gcloud iam service-accounts create notes-api-sa \
--display-name="Notes API Service Account"
```

## 10-2. Firestore 권한 부여

```
gcloud projects add-iam-policy-binding $PROJECT_ID \
--member="serviceAccount:notes-api-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
--role="roles/datastore.user"
```

Cloud Run에서 Google Cloud 서비스에 연결할 때는 서비스 ID와 ADC를 사용하며, Firestore 사용을 위해 `roles/datastore.user` 같은 적절한 IAM 역할 부여가 일반적이다.

---

# 11. Cloud Run에 배포

## 11-1. 소스 코드에서 바로 배포

```
gcloud run deploy $SERVICE_NAME \
--source . \
--region $REGION \
--allow-unauthenticated \
--service-account notes-api-sa@${PROJECT_ID}.iam.gserviceaccount.com
```

### 설명

* `--source .`  
  현재 디렉터리의 소스 코드를 업로드해서 Cloud Build가 빌드 후 Cloud Run에 배포한다.

* `--region $REGION`  
  배포 리전 지정

* `--allow-unauthenticated`  
  인증 없는 HTTP 접근 허용  
  API Gateway 연결 테스트를 빠르게 하기 위해 허용한다.

* `--service-account`  
  런타임에 사용할 서비스 계정 지정

Cloud Run은 소스에서 바로 Node.js 서비스를 배포할 수 있다.

## 11-2. 서비스 URL 확인

```
gcloud run services describe $SERVICE_NAME \
--region $REGION \
--format="value(status.url)"
```

출력 예시:

```
https://notes-api-xxxxx-an.a.run.app
```

이 URL은 뒤에서 OpenAPI 문서에 넣는다.

---

# 12. Cloud Run 직접 테스트

Cloud Run URL을 변수로 저장한다.

```
export RUN_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format="value(status.url)")
echo $RUN_URL
```

## 12-1. 상태 확인

```
curl $RUN_URL/health
```

## 12-2. 메모 등록

```
curl -X POST $RUN_URL/notes \
-H "Content-Type: application/json" \
-d'{
    "title": "첫 번째 메모",
    "content": "Cloud Run과 Firestore 연결 테스트",
    "author": "kyt"
  }'
```

## 12-3. 목록 조회

```
curl $RUN_URL/notes
```

여기까지 성공하면 **Cloud Run ↔ Firestore** 구간은 정상이다.

---

# 13. API Gateway용 OpenAPI 문서 작성

이제 API Gateway가 어떤 경로를 어떤 백엔드로 보낼지 정의한다.

## 13-1. openapi.yaml

아래 파일에서 `YOUR_PROJECT_ID`와 `YOUR_CLOUD_RUN_URL`은 실제 값으로 바꾼다.

```
swagger: "2.0"
info:
  title: "notes-api"
  description: "Notes API Gateway for Cloud Run backend"
  version: "1.0.0"

host: "notes-api-gateway"
schemes:
  - "https"
produces:
  - "application/json"

securityDefinitions:
  api_key:
    type: "apiKey" 
    name: "x-api-key"
    in: "header"

security:
  - api_key: []

paths:
  /health:
    get:
      operationId: "healthCheck"
      x-google-backend:
        address: "YOUR_CLOUD_RUN_URL"
        disable_auth: true
      responses:
        "200":
          description: "OK"

  /notes:
    get:
      operationId: "listNotes"
      x-google-backend:
        address: "YOUR_CLOUD_RUN_URL/notes"
        disable_auth: true
      responses:
        "200":
          description: "OK"

    post:
      operationId: "createNote"
      x-google-backend:
        address: "YOUR_CLOUD_RUN_URL/notes"
        disable_auth: true
      parameters:
        - in: "body"
          name: "body"
          required: true
          schema:
            type: "object"
            properties:
              title:
                type: "string"
              content:
                type: "string"
              author:
                type: "string"
      responses:
        "201":
          description: "Created"

  /notes/{id}:
    get:
      operationId: "getNote"
      x-google-backend:
        address: "YOUR_CLOUD_RUN_URL"
        path_translation: "APPEND_PATH_TO_ADDRESS" # 경로 변수 전달을 위해 추가
        disable_auth: true
      parameters:
        - name: "id"
          in: "path"
          required: true
          type: "string"
      responses:
        "200":
          description: "OK"

    delete:
      operationId: "deleteNote"
      x-google-backend:
        address: "YOUR_CLOUD_RUN_URL"
        path_translation: "APPEND_PATH_TO_ADDRESS"
        disable_auth: true
      parameters:
        - name: "id"
          in: "path"
          required: true
          type: "string"
      responses:
        "200":
          description: "Deleted"
```

---

## 13-2. 파일 값 치환

리눅스/맥/Git Bash 기준:

```
sed "s|YOUR_CLOUD_RUN_URL|$RUN_URL|g" openapi.yaml > openapi-final.yaml
```

확인:

```
cat openapi-final.yaml
```

---

## 13-3. 중요한 설정 설명

### `securityDefinitions`

```
securityDefinitions:
  api_key:
    type:"apiKey"
    name:"x-api-key"
    in:"header"
```

이 부분은 API Gateway가 `x-api-key` 헤더를 요구하게 만드는 설정이다.

API Gateway는 API Key 사용을 지원한다.

### `security`

```
security:
  - api_key: []
```

모든 경로에 기본적으로 API Key 요구 사항을 적용한다.

### `x-google-backend`

```
x-google-backend:
  address: YOUR_CLOUD_RUN_URL
  disable_auth: true
```

API Gateway가 실제 요청을 전달할 Cloud Run 백엔드 주소다.

`x-google-backend`에서 `jwt_audience`나 `disable_auth` 중 하나를 설정할 수 있다. 설정하지 않으면 `address`에 맞춰 기본 동작이 정해진다. 이번 실습은 단순화를 위해 `disable_auth: true`를 사용한다.

---

# 14. API Gateway 리소스 생성

## 14-1. API 생성

```
gcloud api-gateway apis create $API_ID
```

## 14-2. API Config 생성

```
gcloud api-gateway api-configs create $API_CONFIG_ID \
--api=$API_ID \
--openapi-spec=openapi-final.yaml \
--project=$PROJECT_ID
```

API config는 OpenAPI 스펙을 업로드해서 생성한다. 새 스펙을 업로드할 때마다 새로운 API config가 만들어진다.

## 14-3. Gateway 배포

Gateway 배포할 수 있는 리전이 정해져 있음. 다음 명령으로 확인할 수 있다.

```
ACCESS_TOKEN=$(gcloud auth print-access-token)

curl -s \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  "https://apigateway.googleapis.com/v1/projects/PROJECT_ID/locations"
```

확인된 리전을 —location에 사용해야함.

```
gcloud api-gateway gateways create $GATEWAY_ID \
--api=$API_ID \
--api-config=$API_CONFIG_ID \
--location=$REGION \
--project=$PROJECT_ID
```

API Gateway와 Cloud Run 연동 흐름은 **Cloud Run 배포 → OpenAPI 작성 → API config 생성 → Gateway 배포** 순서로 진행한다.

---

# 15. Gateway URL 확인

```
gcloud api-gateway gateways describe $GATEWAY_ID \
--location=$REGION \
--format="value(defaultHostname)"
```

출력 예시:

```
notes-api-gateway-xxxxx.an.gateway.dev
```

변수로 저장:

```
export GATEWAY_HOST=$(gcloud api-gateway gateways describe $GATEWAY_ID \
  --location=$REGION \
  --format="value(defaultHostname)")

echo $GATEWAY_HOST
```

---

# 16. API Key 생성

## 16-1. API Key 생성

```
gcloud services api-keys create \
--display-name="notes-api-key"
```

목록 조회:

```
gcloud services api-keys list
```

생성된 Key 문자열은 콘솔 또는 명령 결과에서 확인한다.

예시:

```
export API_KEY="YOUR_API_KEY_VALUE"
```

## 16-2. API Key 사용 제한 설정

생성한 API key를 API Gateway 서비스에서만 사용할 수 있도록 제한한다.

```
gcloud services api-keys update API_KEY \
--api-target=service=apigateway.googleapis.com
```

API Gateway는 API Key를 통해 요청한 프로젝트를 식별하고, 키가 없거나 유효하지 않으면 요청을 거부할 수 있다. 다만 API Key만 단독으로 쓰는 것은 민감한 API 보호에 충분하지 않을 수 있다.

---

# 17. API Gateway를 통해 호출

## 17-1. 상태 확인

```
curl -H "x-api-key:$API_KEY" \
  https://$GATEWAY_HOST/health
```

## 17-2. 메모 등록

```
curl-X POST https://$GATEWAY_HOST/notes \
-H"Content-Type: application/json" \
-H"x-api-key:$API_KEY" \
-d'{
    "title": "Gateway 경유 메모",
    "content": "API Gateway를 통해 Cloud Run 호출 성공",
    "author": "kyt"
  }'
```

## 17-3. 목록 조회

```
curl -H "x-api-key:$API_KEY" \
  https://$GATEWAY_HOST/notes
```

## 17-4. 단건 조회

```
curl -H "x-api-key:$API_KEY" \
  https://$GATEWAY_HOST/notes/문서ID
```

## 17-5. 삭제

```
curl -X DELETE \
-H "x-api-key:$API_KEY" \
  https://$GATEWAY_HOST/notes/문서ID
```

---

# 18. Firestore에서 데이터 확인

1. 콘솔에서 **Firestore** 이동

2. `notes` 컬렉션 확인

3. 문서가 생성되었는지 확인

4. `title`, `content`, `author`, `createdAt` 필드 확인

이 단계에서 **API Gateway → Cloud Run → Firestore** 전체 체인이 정상 동작했는지 눈으로 검증할 수 있다.

---

# 19. Cloud Run 로그 확인

문제 발생 시 가장 먼저 볼 곳은 Cloud Run 로그다.

```
gcloud run services logs read$SERVICE_NAME \
--region$REGION
```

또는 콘솔에서:

* Cloud Run

* 서비스 선택

* 로그 탭 확인

`console.error()`로 남긴 메시지가 그대로 보이면 디버깅이 훨씬 쉬워진다.

---

# 20. 자주 발생하는 오류와 점검 포인트

## 20-1. Firestore 관련 권한 오류

증상 예시:

* `7 PERMISSION_DENIED`

* `Missing or insufficient permissions`

점검:

* Cloud Run 서비스 계정이 맞는지 확인

* `roles/datastore.user` 권한이 부여되었는지 확인

```
gcloud projects get-iam-policy$PROJECT_ID \
--flatten="bindings[].members" \
--format="table(bindings.role, bindings.members)" \
--filter="bindings.members:notes-api-sa@${PROJECT_ID}.iam.gserviceaccount.com"
```

Cloud Run에서 Firestore를 쓰려면 서비스 계정에 적절한 IAM 역할이 필요하다.

---

## 20-2. Gateway 호출 시 401 또는 403

점검:

* `x-api-key` 헤더를 넣었는지 확인

* API Key 값이 정확한지 확인

* API Gateway 배포가 완료되었는지 확인

---

## 20-3. Gateway 호출 시 404

점검:

* `openapi-final.yaml`의 경로가 실제 코드 경로와 일치하는지 확인

* `/notes`, `/notes/{id}`, `/health` 오타 확인

* Gateway가 새 config를 보고 있는지 확인

---

## 20-4. Gateway 호출 시 500

점검:

* Cloud Run 백엔드 URL이 `openapi-final.yaml`에 정확히 들어갔는지 확인

* Firestore 권한 문제인지 Cloud Run 로그에서 확인

* 코드 오류인지 로그에서 stack trace 확인

---

# 21. 보안 관점에서 꼭 알아둘 점

이번 실습은 **학습용 단순 구성**이다.

즉,

* Cloud Run은 `--allow-unauthenticated`로 배포했음

* API Gateway는 API Key로 접근을 제어했음

이 방식은 Gateway 연동 실습에는 편하지만, **Cloud Run 원본 URL도 직접 호출될 수 있음**.

실무에서는 다음을 추가로 고려하는 편이 좋다.

* Cloud Run 직접 접근 제한

* API Gateway 뒤에서만 접근되도록 구성

* API Key만이 아니라 IAM/JWT/OIDC 등 추가 인증 적용

* WAF, rate limit, 모니터링 연계

API Gateway는 API Key 외에도 다른 인증 방식 구성을 지원하며, API Key만 단독으로 쓰는 것은 민감한 API 보호에 충분하지 않을 수 있다.

---

# 22. 실습 완료 후 정리

## 22-1. Gateway 삭제

```
gcloud api-gateway gateways delete $GATEWAY_ID \
--location=$REGION
```

## 22-2. API Config 삭제

```
gcloud api-gateway api-configs delete $API_CONFIG_ID \
--api=$API_ID
```

## 22-3. API 삭제

```
gcloud api-gateway apis delete $API_ID
```

## 22-4. Cloud Run 삭제

```
gcloud run services delete $SERVICE_NAME \
--region=$REGION
```

## 22-5. 서비스 계정 삭제

```
gcloud iam service-accounts delete \
  notes-api-sa@${PROJECT_ID}.iam.gserviceaccount.com
```

Firestore 데이터베이스는 별도 비용과 데이터 보존 여부를 고려해서 콘솔에서 삭제 여부를 결정하면 된다. Firestore 데이터베이스는 생성·삭제를 별도로 관리한다.

---

# 23. 실습 정리

이 실습으로 확인한 핵심은 다음과 같다.

* **Cloud Run**은 서버 없이 컨테이너 API를 운영할 수 있는 서버리스 실행 환경

* **Firestore**는 문서형 NoSQL 데이터 저장소

* **API Gateway**는 외부 클라이언트가 접근하는 표준 진입점

* 세 서비스를 조합하면 **백엔드 서버를 직접 운영하지 않고도 REST API 서비스**를 만들 수 있음