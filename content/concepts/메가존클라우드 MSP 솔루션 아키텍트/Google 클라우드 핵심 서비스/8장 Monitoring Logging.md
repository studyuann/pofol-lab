---
title: "8장 Monitoring Logging"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Google 클라우드 핵심 서비스"]
is_public: true
draft: false
---

# 8장. Monitoring / Logging

## 1. 장 개요

클라우드 운영에서 자주 겪는 문제는 대부분 다음 형태로 나타난다.

* 서버가 느려짐

* 웹 페이지 응답이 끊김

* 특정 시점부터 에러가 급증함

* DB 연결이 실패함

* 특정 인스턴스만 이상 동작함

* 로드밸런서는 정상처럼 보이는데 사용자 요청은 실패함

이때 필요한 것이 바로 **메트릭(metrics)** 과 **로그(logs)** 다.

* 메트릭은 “지금 상태가 어떤가”를 수치로 보여줌

* 로그는 “무슨 일이 있었는가”를 기록으로 보여줌

Google Cloud는 모니터링과 로그를 각각 별도 서비스로 제공하지만, 실제 운영에서는 둘을 함께 봐야 한다. Monitoring은 메트릭, 이벤트, 업타임을 관찰하고, Logging은 로그 데이터를 저장·검색·분석하며 Monitoring과도 연계된다.

---

## 2. 학습 목표

* Cloud Monitoring과 Cloud Logging의 역할 차이를 설명할 수 있음

* 메트릭과 로그의 차이를 설명할 수 있음

* AWS CloudWatch와 GCP Monitoring/Logging 구조를 비교할 수 있음

* VM, Load Balancer, Cloud SQL 같은 리소스의 기본 메트릭을 확인할 수 있음

* 로그 탐색기(Log Explorer)에서 로그를 검색할 수 있음

* 간단한 대시보드를 만들 수 있음

* 기본적인 경보 정책(Alerting Policy)의 목적을 설명할 수 있음

* 운영 문제를 메트릭과 로그를 조합해 추적하는 흐름을 설명할 수 있음

---

## 3. 핵심 키워드

* Cloud Monitoring

* Cloud Logging

* Metrics

* Logs

* Dashboard

* Alerting Policy

* Uptime Check

* Log Explorer

* Resource Type

* Query

* Incident

* Observability

---

# 4. 왜 모니터링과 로그가 중요한가

인프라를 만들었다고 해서 운영이 끝난 것은 아니다.

오히려 실제 운영은 그 다음부터 시작된다.

예를 들어 아래 같은 상황을 생각해보자.

* 웹 서버 CPU가 계속 90%를 넘음

* nginx 프로세스가 재시작됨

* 사용자가 특정 시간대에만 접속 실패를 겪음

* DB 연결 오류가 간헐적으로 발생함

* 로드밸런서 Health Check 실패가 늘어남

이런 문제를 알아내려면 두 가지가 필요하다.

## 4.1 메트릭

수치형 상태 데이터다.

예시

* CPU 사용률

* 메모리 사용률

* 디스크 I/O

* 네트워크 트래픽

* 응답 시간

* 에러율

## 4.2 로그

이벤트 기록 데이터다.

예시

* 시스템 부팅 로그

* 애플리케이션 에러 로그

* 웹 서버 접근 로그

* 감사 로그

* DB 에러 메시지

Cloud Monitoring은 시계열 메트릭과 업타임, 이벤트 관찰에 초점을 두고, Cloud Logging은 로그 저장, 검색, 분석, 라우팅을 담당한다.

---

# 5. Cloud Monitoring이란 무엇인가

Cloud Monitoring은 Google Cloud 리소스와 애플리케이션의 상태를 **메트릭 기반으로 관찰**하는 서비스다.

즉, Cloud Monitoring은 시스템·애플리케이션 메트릭, 이벤트, 업타임 정보를 수집해 관찰하게 해준다.

## 쉽게 이해하면

* AWS CloudWatch의 메트릭/알람/대시보드 영역과 유사

* CPU, 디스크, 네트워크, 응답 시간 같은 수치를 시간축으로 관찰

* 이상 징후를 임계값 기반으로 감지

* 대시보드와 알림으로 운영 상태를 시각화

## 주요 기능

* Metrics Explorer

* Dashboard

* Alerting Policy

* Uptime Check

* SLO/SLI 관련 기능

---

# 6. Cloud Logging이란 무엇인가

Cloud Logging은 로그 데이터를 수집하고 저장하고 검색하고 분석하는 서비스다.

Google 문서는 Cloud Logging이 로그 저장과 검색, 보기, 분석, 그리고 내보내기를 지원한다고 설명한다.

## 쉽게 이해하면

* AWS CloudWatch Logs와 Logs Insights 영역에 대응되는 감각

* 시스템 로그, 애플리케이션 로그, 감사 로그를 모아봄

* 특정 에러 메시지나 리소스 이벤트를 검색

* 문제 발생 시 원인을 추적

## 주요 기능

* Log Explorer

* Query 기반 검색

* 로그 라우터

* 로그 싱크

* 보관 및 라우팅

---

# 7. AWS CloudWatch와의 비교

AWS를 먼저 학습했다면 이 장은 아래 비교로 시작하면 좋다.

## AWS CloudWatch

* 메트릭

* 로그

* 알람

* 대시보드

* 이벤트 기반 운영

## GCP

* Cloud Monitoring

* Cloud Logging

즉, AWS에서는 CloudWatch라는 하나의 큰 이름 아래 메트릭과 로그를 함께 보는 반면,

GCP는 Monitoring과 Logging은 **논리적으로 구분된 서비스**이지만 실제 운영에서는 함께 사용한다.

---

# 8. 메트릭과 로그의 차이

## 8.1 메트릭

정량적 수치 데이터

예시

* CPU 72%

* 요청 수 초당 350

* 지연 시간 120ms

* 에러율 2.1%

### 특징

* 대시보드와 알림에 적합

* 임계값 기반 감시에 적합

* 시간에 따른 추세 분석에 적합

## 8.2 로그

이벤트 기록 데이터

예시

* `database connection failed`

* `nginx started`

* `permission denied`

* `health check failed`

### 특징

* 문제 원인 분석에 적합

* 특정 시점의 상세 상황 파악에 적합

* 필터링과 검색이 중요

## 운영 포인트

문제가 생기면 보통 아래 순서로 본다.

1. 메트릭으로 이상 징후 감지

2. 로그로 원인 파악

---

# 9. Monitoring에서 주로 보는 리소스

## 9.1 Compute Engine

* CPU 사용률

* 네트워크 입출력

* 디스크 사용량

* 인스턴스 상태

Google Compute Engine 메트릭은 Monitoring에 기본 통합되며, VM 인스턴스 리소스 타입 기준으로 확인할 수 있다.

## 9.2 Load Balancer

* 요청 수

* 지연 시간

* 백엔드 상태

* 헬스 체크 결과

로드밸런서 관련 메트릭도 Monitoring에서 제공되며, 부하 분산 서비스 상태를 추적하는 데 사용된다.

## 9.3 Cloud SQL

* CPU 사용률

* 메모리 사용률

* 스토리지 사용량

* 연결 수

* 응답 지연 관련 지표

Cloud SQL은 Monitoring과 통합되어 인스턴스 성능 지표를 제공한다.

## 9.4 Cloud Storage

* 접근 로그, 사용량 분석은 주로 로그/사용량 측면에서 봄

* 일부 모니터링 지표와 감사 로그를 함께 봄

---

# 10. Logging에서 주로 보는 로그 유형

Google Cloud는 로그를 리소스 유형과 로그 이름(logName) 기준으로 관리한다. Cloud Logging은 감사 로그, 플랫폼 로그, 애플리케이션 로그를 함께 수집할 수 있다.

## 대표 예시

* Compute Engine 시스템 로그

* 웹 애플리케이션 로그

* Cloud Audit Logs

* VPC 흐름 관련 로그(별도 활성화 시)

* Cloud SQL 로그

* 로드밸런서 관련 로그

---

# 11. 대시보드(Dashboard)

Cloud Monitoring은 대시보드를 만들어 여러 메트릭을 한 화면에서 볼 수 있게 한다. 즉, 사용자 정의 대시보드와 차트 구성한다.

## 왜 필요한가

운영자는 매번 개별 서비스 화면을 하나씩 들어가 보면 비효율적이다.

대시보드를 만들면 핵심 상태를 한 번에 볼 수 있다.

## 예시 구성

* 웹 서버 CPU

* 네트워크 트래픽

* 로드밸런서 요청 수

* Cloud SQL CPU

* 에러 로그 수

---

# 12. Alerting Policy

Alerting Policy는 특정 조건을 만족할 때 운영자에게 알려주는 규칙이다.

Cloud Monitoring은 메트릭 기반 알림 정책을 제공하고, 알림 채널과 조건을 함께 설정할 수 있다.

## 예시 조건

* CPU 사용률 80% 이상 5분 지속

* 인스턴스 다운

* 에러율 급증

* 특정 메트릭 임계값 초과

## 왜 중요한가

운영자는 항상 대시보드만 보고 있을 수 없다.

이상이 생겼을 때 먼저 알려주는 구조가 필요하다.

---

# 13. Uptime Check

Cloud Monitoring은 외부에서 특정 엔드포인트가 살아 있는지 확인하는 **Uptime Check** 기능을 제공한다.

## 언제 유용한가

* 웹사이트가 외부에서 실제로 열리는지 확인

* HTTP 엔드포인트 응답 상태 확인

* 단순 생존 감시

## 예시

* `http://EXTERNAL_IP`

* 서비스 도메인 URL

---

# 14. Log Explorer

Cloud Logging의 핵심 화면은 **Log Explorer** 다.

여기서 특정 리소스의 로그를 검색하고, 필터링하고, 시간 범위를 조정해 문제를 분석한다.

## 보통 사용하는 필터 기준

* Resource type

* 로그 이름

* 시간 범위

* 심각도(severity)

* 텍스트 검색어

## 예시

* 특정 VM의 로그만 보기

* ERROR 로그만 보기

* 최근 1시간 로그만 보기

* nginx, mysql, denied 같은 키워드 검색

---

# 15. 장 요약

* Cloud Monitoring은 메트릭, 이벤트, 업타임을 관찰하는 서비스다.

* Cloud Logging은 로그 저장, 검색, 분석, 내보내기를 담당한다.

* 메트릭은 상태를 수치로 보여주고, 로그는 이벤트를 기록으로 보여준다.

* AWS는 CloudWatch 하나로 묶어 이해하는 경우가 많고, GCP는 Monitoring과 Logging이 분리되어 보인다.

* 대시보드는 자주 보는 운영 지표를 한 화면에 모아준다.

* Alerting Policy는 이상 징후를 임계값 기반으로 알려준다.

* Log Explorer는 문제 원인을 추적하는 핵심 도구다.

* 운영에서는 메트릭과 로그를 함께 봐야 한다.