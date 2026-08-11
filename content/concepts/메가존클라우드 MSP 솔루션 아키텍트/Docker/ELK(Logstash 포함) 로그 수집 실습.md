---
title: "ELK(Logstash 포함) 로그 수집 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Docker"]
is_public: true
draft: false
---

# **ELK(Logstash 포함) 로그 수집 실습**

👉 **Docker 컨테이너 로그 → 중앙 로그 시스템 → Kibana 시각화**

---

[![](https://camo.githubusercontent.com/17b7106ddb644fd66cbc46b698f4ff1926843dc8d76d020c66d5737e8be26365/68747470733a2f2f6c6f677a2e696f2f77702d636f6e74656e742f75706c6f6164732f323031372f30362f72656c6174696f6e736869702d6265747765656e2d66696c65626561742d616e642d6c6f6773746173682e706e67)](https://camo.githubusercontent.com/17b7106ddb644fd66cbc46b698f4ff1926843dc8d76d020c66d5737e8be26365/68747470733a2f2f6c6f677a2e696f2f77702d636f6e74656e742f75706c6f6164732f323031372f30362f72656c6174696f6e736869702d6265747765656e2d66696c65626561742d616e642d6c6f6773746173682e706e67)

# 컨테이너 로그 관리 실습 교안

---

## 1. 실습 개요

### 실습 목표

이 실습을 통해 수강생은 다음을 직접 확인한다.

* 컨테이너 로그의 **표준 출력(stdout/stderr) 기반 수집 원리**

* Docker 로그 드라이버의 한계

* **ELK Stack 기반 중앙 로그 수집 구조**

* Filebeat를 이용한 컨테이너 로그 수집

* Kibana를 통한 로그 조회 및 검색

---

## 2. 실습 전체 구조

```
[Web Container]
   │  stdout/stderr
   ▼
[Docker JSON Log File]
   │
   ▼
[Filebeat]
   │
   ▼
[Logstash]
   │
   ▼
[Elasticsearch]
   │
   ▼
[Kibana]
```

### 핵심 개념 정리

* 컨테이너는 **로그를 파일에 직접 쓰지 않는다**

* 로그는 **stdout/stderr → Docker 로그 드라이버**로 전달

* ELK는 로그를 **중앙에서 수집·검색·시각화**하는 시스템

---

## 3. 실습 환경

### 사전 조건

* OS: Ubuntu

* Docker / Docker Compose 설치 완료

* 포트 사용:
  + Elasticsearch: `9200`
  + Kibana: `5601`

### 사용 이미지

* `nginx:alpine`

* `elasticsearch:8.x`

* `logstash:8.x`

* `kibana:8.x`

* `filebeat:8.x`

---

## 4. 실습 1. 컨테이너 로그 특성 확인 (복습)

### 4-1. 로그를 출력하는 웹 컨테이너 실행

```
docker run -d \
  --name web-log \
  -p 8080:80 \
  nginx:alpine
```

접속:

```
curl http://127.0.0.1:8080
```

로그 확인:

```
docker logs web-log
```

### 확인 포인트

* 로그는 파일이 아니라 **docker logs 명령으로 조회**

* 컨테이너 삭제 시 로그도 함께 사라짐

---

## 5. 실습 2. ELK Stack 실행 (Docker Compose)

### 5-1. 디렉터리 구조

```
elk-lab/
├── docker-compose.yml
├── logstash/
│   └── pipeline.conf
└── filebeat/
    └── filebeat.yml
```

---

### 5-2. docker-compose.yml

```
services:
  # Elasticsearch: 512MB로 제한하여 VM 생존 확보
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.10.2
    container_name: elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - xpack.security.enrollment.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - 9200:9200

  # Logstash: 256MB로 최소화
  logstash:
    image: docker.elastic.co/logstash/logstash:8.10.2
    container_name: logstash
    environment:
      - "LS_JAVA_OPTS=-Xms256m -Xmx256m"
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline:ro
    depends_on:
      - elasticsearch

  # Kibana: 보안 체크를 강제로 건너뛰는 설정 추가
  kibana:
    image: docker.elastic.co/kibana/kibana:8.10.2
    container_name: kibana
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
      - XPACK_SECURITY_ENABLED=false
      - XPACK_ENROLLMENT_LOG_ENABLED=false
      - TELEMETRY_ENABLED=false # 불필요한 통신 차단 (성능)
    ports:
      - 5601:5601
    depends_on:
      - elasticsearch

  # Filebeat: root 권한으로 실행하여 로그 수집
  filebeat:
    image: docker.elastic.co/beats/filebeat:8.12.2
    container_name: filebeat
    user: root
    privileged: true # 권한이 더 필요할 경우 추가
    environment:
      - DOCKER_API_VERSION=1.44
    volumes:
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
    depends_on:
      - logstash
```

---

### 5-3. Logstash 파이프라인 설정

`logstash/pipeline.conf`

```
input {
  beats {
    port => 5044
    host => "0.0.0.0"
  }
}

filter {
  # 1. 메시지가 JSON 형태인 경우
  if [message] =~ /^\{/ {
    json {
      source => "message"
    }
  }
  # 2. Nginx 접속 로그 형태인 경우
  else if [container][name] =~ "web" {
    grok {
      match => { "message" => "%{COMBINEDAPACHELOG}" }
    }
    date {
      match => [ "timestamp", "dd/MMM/yyyy:HH:mm:ss Z" ]
      target => "@timestamp"
    }
  }
  # 3. 그 외 로그는 아래 mutate만 거치고 그대로 통과됩니다.

  mutate {
    remove_tag => ["_jsonparsefailure", "_grokparsefailure"]
  }
}

output {
  stdout { codec => rubydebug }
  elasticsearch {
    hosts => ["http://elasticsearch:9200"]
    index => "docker-logs-%{+YYYY.MM.dd}"
  }
}
```

---

### 5-4. ELK 실행

```
docker compose up -d
```

확인:

```
curl http://localhost:9200
curl http://localhost:5601
```

---

## 6. 실습 3. Filebeat로 Docker 로그 수집

### 6-1. Filebeat 설정 파일

`filebeat/filebeat.yml`

```
#filebeat.inputs:
#- type: container
#  paths:
#    - '/var/lib/docker/containers/*/*.log' # 도커 로그 위치

filebeat.autodiscover:
  providers:
    - type: docker
      api_version: "1.44"
      hints.enabled: true
      templates:
        - condition:
            and:
              - not.contains:
                  docker.container.name: "logstash"
              - not.contains:
                  docker.container.name: "elasticsearch"
              - not.contains:
                  docker.container.name: "kibana"
          config:
            - type: container
              paths:
                - "/var/lib/docker/containers/${data.docker.container.id}/*.log"

# 도커 엔진에서 컨테이너 이름, 이미지 정보 등을 자동으로 가져오는 설정
processors:
- add_docker_metadata:
    host: "unix:///var/run/docker.sock"
    match_fields: ["system.process.cgroup.id"]
    wait_for_seconds: 5

# 수집한 로그를 Logstash의 5044 포트로 전송
output.logstash:
  hosts: ["logstash:5044"]
```

---

### 6-2. Filebeat 컨테이너 실행

```
docker run -d \
  --name filebeat \
  --user=root \
  -v /var/lib/docker/containers:/var/lib/docker/containers:ro \
  -v ./filebeat/filebeat.yml:/usr/share/filebeat/filebeat.yml \
  --network elk-lab_default \
  docker.elastic.co/beats/filebeat:8.11.0
```

---

## 7. 실습 4. 로그 흐름 확인

### 7-1. 웹 요청 발생

```
curl http://127.0.0.1:8080
curl http://127.0.0.1:8080/notfound
```

---

### 7-2. Logstash 로그 확인

```
docker logs logstash
```

→ 로그 이벤트가 들어오는 것 확인

---

### 7-3. Elasticsearch 인덱스 확인

```
curl http://localhost:9200/_cat/indices?v
```

예상 출력:

```
container-logs-2026.02.10
```

---

## 8. 실습 5. Kibana에서 로그 조회

### 8-1. Kibana 접속

브라우저:

```
http://localhost:5601
```

---

### 8-2. Data View 생성

1. **Stack Management → Data Views**

2. Name: `container-logs-*`

3. Time field: `@timestamp`

4. Create

---

### 8-3. Discover 메뉴에서 로그 확인

검색 예시:

* 특정 컨테이너 로그

  ```
  container.name : "web-log"
  ```

* HTTP 상태 코드

  ```
  status : 404
  ```

---

## 9. 실습 핵심 정리

### 반드시 이해해야 할 포인트

* 컨테이너 로그는 **파일이 아닌 stdout/stderr**

* Docker는 로그를 **호스트 파일(JSON)** 로 저장

* Filebeat는 로그 파일을 읽는 **수집기**

* Logstash는 **가공/필터링**

* Elasticsearch는 **저장/검색**

* Kibana는 **시각화/UI**

---

## 10. 실습 종료 및 정리

```
docker rm -f web-log filebeat
docker compose down
```

---