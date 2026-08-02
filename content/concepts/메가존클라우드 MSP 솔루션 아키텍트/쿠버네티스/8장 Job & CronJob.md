---
title: "8장 Job & CronJob"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "쿠버네티스"]
is_public: true
draft: false
---

# 8장. Job & CronJob

---

# 1. Job

---

## 1.1 개념

Job은 **일회성 작업을 실행하기 위한 Kubernetes 리소스**다.

Deployment는 계속 실행되는 애플리케이션을 위한 리소스다.

반면 Job은 다음과 같은 작업에 사용된다.

* 데이터 마이그레이션

* 배치 처리

* 백업 작업

* 초기화 스크립트

* 대량 데이터 처리

작업이 성공적으로 종료되면 완료 상태가 되고 더 이상 실행되지 않는다.

---

## 1.2 Job 동작 흐름

```
Job 생성
  ↓
Pod 생성
  ↓
작업 수행
  ↓
성공(Exit 0)
  ↓
Job Completed
```

실패 시 설정된 조건에 따라 재시도한다.

---

## 1.3 Job 특징

* 완료 조건 지정 가능

* 병렬 실행 가능

* 실패 시 재시도 가능

* 완료 후 리소스 자동 삭제 가능

---

# 1.4 Job YAML 예제

```
apiVersion: batch/v1
kind: Job
metadata:
  name: hello-job
spec:
  completions: 1
  parallelism: 1
  backoffLimit: 4
  activeDeadlineSeconds: 100
  ttlSecondsAfterFinished: 30
  template:
    metadata:
      labels:
        app: hello-job
    spec:
      restartPolicy: OnFailure
      containers:
      - name: hello
        image: busybox:latest
        command: ["sh", "-c"]
        args:
          - echo "Hello Kubernetes Job"; sleep 5
```

---

# 1.5 Job 고유 옵션 설명

---

## completions

```
completions: 1
```

* 성공해야 할 총 작업 수

* 1이면 한 번 성공 시 완료

* 5이면 5번 성공해야 완료

---

## parallelism

```
parallelism: 1
```

* 동시에 실행할 Pod 수

* completions과 함께 동작

예:

```
completions: 5
parallelism: 2
```

→ 동시에 2개 실행

→ 총 5번 성공 시 완료

---

## backoffLimit

```
backoffLimit: 4
```

* 실패 시 재시도 횟수

* 초과하면 Job은 Failed 상태

---

## activeDeadlineSeconds

```
activeDeadlineSeconds: 100
```

* Job 전체 실행 최대 시간

* 초과 시 강제 종료

---

## ttlSecondsAfterFinished

```
ttlSecondsAfterFinished: 30
```

* 완료 후 자동 삭제 시간

* 클러스터 리소스 정리 목적

---

# 1.6 Job 실습

---

## 생성

```
kubectl apply -f job.yaml
```

---

## 상태 확인

```
kubectl get jobs
kubectl get pods
```

---

## 로그 확인

```
kubectl logs <pod-name>
```

---

## 병렬 Job 테스트

```
spec:
  completions: 5
  parallelism: 2
```

---

# 1.7 Job 운영 주의사항

1. restartPolicy는 Never 또는 OnFailure만 가능

2. 병렬 실행 시 외부 자원 충돌 가능

3. ttlSecondsAfterFinished 설정 권장

---

---

# 2. CronJob

---

## 2.1 개념

CronJob은 **정기적으로 Job을 실행하는 리소스**다.

Linux cron과 동일한 스케줄 문법을 사용한다.

CronJob은 직접 Pod을 만들지 않고,

내부적으로 Job을 생성한다.

---

## 2.2 동작 구조

```
CronJob
   ↓
(스케줄 도달)
   ↓
Job 생성
   ↓
Pod 실행
```

---

## 2.3 CronJob 특징

* 주기적 실행

* 동시 실행 제어 가능

* 성공/실패 Job 보관 개수 설정 가능

* 일시 중지 가능

---

# 2.4 CronJob YAML 예제

```
apiVersion: batch/v1
kind: CronJob
metadata:
  name: hello-cron
spec:
  schedule: "*/1 * * * *"
  concurrencyPolicy: Allow
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  suspend: false
  jobTemplate:
    spec:
      backoffLimit: 3
      template:
        spec:
          restartPolicy: OnFailure
          containers:
          - name: hello
            image: busybox
            command: ["sh", "-c"]
            args:
              - echo "Hello from CronJob"; date
```

---

# 2.5 CronJob 고유 옵션 설명

---

## schedule

```
"*/1 * * * *"
```

형식:

```
분 시 일 월 요일
```

예:

* `"0 2 * * *"` → 매일 새벽 2시

* `"*/5 * * * *"` → 5분마다

---

## concurrencyPolicy

| 값 | 의미 |
| --- | --- |
| Allow | 동시에 실행 허용 |
| Forbid | 이전 Job 완료 후 실행 |
| Replace | 기존 Job 종료 후 새 Job 실행 |

운영에서는 보통 Forbid 또는 Replace 사용.

---

## successfulJobsHistoryLimit

성공한 Job 보관 개수.

---

## failedJobsHistoryLimit

실패한 Job 보관 개수.

---

## suspend

```
suspend: true
```

* true → 실행 중지

* false → 정상 실행

---

## jobTemplate

CronJob이 생성할 Job 정의.

Job spec과 동일 구조.

---

# 2.6 CronJob 실습

---

## 생성

```
kubectl apply -f cronjob.yaml
```

---

## 확인

```
kubectl get cronjobs
kubectl get jobs
```

---

## 일시 중지

```
kubectl patch cronjob hello-cron -p '{"spec":{"suspend":true}}'
```

---

# 2.7 운영 주의사항

1. schedule 오타 매우 흔함

2. 클러스터 시간대 기준 실행

3. concurrencyPolicy 설정 필수

4. 장시간 작업은 겹치지 않도록 설계

---

# 3. Job vs CronJob 비교

| 항목 | Job | CronJob |
| --- | --- | --- |
| 실행 방식 | 1회 실행 | 주기적 실행 |
| 스케줄 | 없음 | cron 표현식 |
| 내부 구조 | Pod 실행 | Job 생성 |
| 동시 실행 제어 | 없음 | concurrencyPolicy |

---

# 핵심 정리

Job:

* 일회성 작업

* 병렬 실행 가능

* 재시도 설정 가능

CronJob:

* 주기적 실행

* 내부적으로 Job 생성

* 동시 실행 정책 중요

---