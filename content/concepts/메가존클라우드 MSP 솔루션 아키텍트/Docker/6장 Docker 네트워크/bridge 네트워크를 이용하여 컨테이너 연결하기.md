---
title: "bridge 네트워크를 이용하여 컨테이너 연결하기"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Docker", "6장 Docker 네트워크"]
is_public: true
draft: false
---

# `bridge` 네트워크를 이용하여 컨테이너 연결하기

사용할 네트워크를 다음과 같이 생성합니다.

`$ docker network create -d bridge private  
private`

생성된 네트워크는 `docker network list` 명령어를 통해서 확인할 수 있습니다.

`$ docker network list  
NETWORK ID NAME DRIVER SCOPE  
71bf83fc2d7c bridge bridge local  
00c55e1a5560 host host local  
ceedb973ae73 none null local  
5bce335632dc private bridge local`

`PostgreSQL`과 `PgAdmin` 컨테이너를 생성합니다. 이 때, `PgAdmin` 컨테이너는 위에서 생성한 네트워크를 사용하여 생성합니다.

`# PostgreSQL DB 생성  
$ docker run --rm -d --name db -e POSTGRES_PASSWORD=mysecretpassword postgres:16.1-bullseye  
  
# PgAdmin Application 생성  
$ docker run --rm -d -p 80:80 --name pgadmin -e PGADMIN_DEFAULT_EMAIL=user@sample.com -e PGADMIN_DEFAULT_PASSWORD=SuperSecret --network private dpage/pgadmin4:latest`

다음 명령어를 통해서 `db` 컨테이너의 `network`별 IP 주소를 확인합니다.

`$ docker inspect db -f '{{range $k, $v := .NetworkSettings.Networks}}{{print $k}}={{println $v.IPAddress}}{{end}}'  
bridge=172.17.0.3`

`bridge` 네트워크에 할당된 `IP`를 이용하여 `PgAdmin`에서 연결을 시도합니다.

* `PgAdmin` 페이지에 접속합니다.
  + http://localhost:80

[![](https://matenduel.github.io/cloudwave-textbook/images/docker/pgadmin_1.png)](https://matenduel.github.io/cloudwave-textbook/images/docker/pgadmin_1.png)

* `Servers`를 클릭한 다음, 좌측 상단 `Object > Register > Server`를 클릭합니다.

[![](https://matenduel.github.io/cloudwave-textbook/images/docker/pgadmin_2.png)](https://matenduel.github.io/cloudwave-textbook/images/docker/pgadmin_2.png)

* `General` 탭에서 `Name`을 기입합니다.

* `Connection` 탭에서 접속할 `DB`서버 정보를 입력합니다.
  + host: `bridge` 네트워크에서 할당된 IP
  + Username: `postgres`
  + Password: 컨테이너 실행시 입력한 `POSTGRES_PASSWORD`

[![](https://matenduel.github.io/cloudwave-textbook/images/docker/pgadmin_3.png)](https://matenduel.github.io/cloudwave-textbook/images/docker/pgadmin_3.png)

* `DB` 연결에 실패한 것을 확인할 수 있습니다.

이번엔 위에서 생성한 `private` 네트워크를 `DB`에 연결한 이후, `private` 네트워크에서 할당된 `IP` 주소를 확인합니다.

`$ docker network connect private db  
  
$ docker inspect db -f '{{range $k, $v := .NetworkSettings.Networks}}{{print $k}}={{println $v.IPAddress}}{{end}}'  
bridge=172.17.0.3  
private=172.18.0.3`

해당 `IP`를 이용하여 `PgAdmin`에서 연결의 시도합니다.

[![](https://matenduel.github.io/cloudwave-textbook/images/docker/pgadmin_4.png)](https://matenduel.github.io/cloudwave-textbook/images/docker/pgadmin_4.png)

정상적으로 연결이 되는 것을 확인할 수 있습니다.

[![](https://matenduel.github.io/cloudwave-textbook/images/docker/pgadmin_5.png)](https://matenduel.github.io/cloudwave-textbook/images/docker/pgadmin_5.png)

### [연습] `alias`를 이용하여 `ip`없이 컨테이너 통신하기[#](https://matenduel.github.io/cloudwave-textbook/docs/01-intro/15-docker-cli-network/#%ec%97%b0%ec%8a%b5-alias%eb%a5%bc-%ec%9d%b4%ec%9a%a9%ed%95%98%ec%97%ac-ip%ec%97%86%ec%9d%b4-%ec%bb%a8%ed%85%8c%ec%9d%b4%eb%84%88-%ed%86%b5%ec%8b%a0%ed%95%98%ea%b8%b0)

다음과 같이 `ubuntu` 컨테이너를 생성하고 필요한 `Package`를 생성합니다.

`$ docker run --name main -itd ubuntu:22.04  
$ docker exec main /bin/bash -c "apt-get update && apt-get upgrade && apt-get install -y wget dnsutils"`

`nginx` 컨테이너를 다음과 같이 3개 생성합니다.

`$ docker run --rm -d --net private --net-alias web_app --name nginx1 nginx:latest  
$ docker run --rm -d --net private --net-alias web_app --name nginx2 nginx:latest  
$ docker run --rm -d --net private --net-alias web_app --net-alias ready --name nginx3 nginx:latest`

`main` 컨테이너에서 `web_app`에 대해 `dig`을 사용하면, 다음과 같이 `DNS` 질의에 대한 응답이 없는 것을 확인할 수 있습니다.

> `nslookup web_app`을 이용하여 확인해도 됩니다.

`$ docker exec main dig web_app  
  
; <<>> DiG 9.18.18-0ubuntu0.22.04.1-Ubuntu <<>> web_app  
;; global options: +cmd  
;; Got answer:  
;; ->>HEADER<<- opcode: QUERY, status: NXDOMAIN, id: 53782  
;; flags: qr rd ra; QUERY: 1, ANSWER: 0, AUTHORITY: 0, ADDITIONAL: 1  
  
;; OPT PSEUDOSECTION:  
; EDNS: version: 0, flags:; udp: 1232  
; COOKIE: bcdc7ef17f1d57fd (echoed)  
;; QUESTION SECTION:  
;web_app. IN A  
  
;; Query time: 5 msec  
;; SERVER: 127.0.0.11#53(127.0.0.11) (UDP)  
;; WHEN: Sat Dec 23 07:59:12 UTC 2023  
;; MSG SIZE rcvd: 48`

`main` 컨테이너에 `private` 네트워크를 다음과 같이 연결합니다.

`$ docker network connect --alias main private main  
$ docker inspect main -f "Alias:{{ println .NetworkSettings.Networks.private.Aliases }}IP:{{ println .NetworkSettings.Networks.private.IPAddress }}"  
Alias:[main 51c471535b96]  
IP:172.19.0.5`

다시 한번 `main` 서버에서 `dig`를 사용하면 3개 컨테이너의 `IP`가 반환된 것을 확인할 수 있습니다.

`$ docker exec main dig web_app  
  
; <<>> DiG 9.18.18-0ubuntu0.22.04.1-Ubuntu <<>> web_app  
;; global options: +cmd  
;; Got answer:  
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 43503  
;; flags: qr rd ra; QUERY: 1, ANSWER: 3, AUTHORITY: 0, ADDITIONAL: 0  
  
;; QUESTION SECTION:  
;web_app. IN A  
  
;; ANSWER SECTION:  
web_app. 600 IN A 172.19.0.4  
web_app. 600 IN A 172.19.0.2  
web_app. 600 IN A 172.19.0.3  
  
;; Query time: 0 msec  
;; SERVER: 127.0.0.11#53(127.0.0.11) (UDP)  
;; WHEN: Sat Dec 23 07:51:11 UTC 2023  
;; MSG SIZE rcvd: 94`

다음과 같이 `ping`을 사용할 때마다 응답하는 `IP`가 바뀌는 것을 볼 수 있습니다.

`$ docker exec main apt-get install -y iputils-ping  
$ docker exec main ping web_app  
PING web_app (172.19.0.2) 56(84) bytes of data.  
64 bytes from nginx1.private (172.19.0.2): icmp_seq=1 ttl=64 time=0.060 ms  
64 bytes from nginx1.private (172.19.0.2): icmp_seq=2 ttl=64 time=0.075 ms  
64 bytes from nginx1.private (172.19.0.2): icmp_seq=3 ttl=64 time=0.076 ms  
...  
$ docker exec main ping web_app  
PING web_app (172.19.0.4) 56(84) bytes of data.  
64 bytes from nginx3.private (172.19.0.4): icmp_seq=1 ttl=64 time=0.136 ms  
64 bytes from nginx3.private (172.19.0.4): icmp_seq=2 ttl=64 time=0.073 ms  
...`

### [실습] `DB`를 `alias`를 이용하여 연결하기

> 연습 문제(`bridge` 네트워크를 이용하여 컨테이너 연결하기)에서 `IP` 대신 `DNS`를 이용하세요

* `PostgreSQL`과 `PgAdmin` 컨테이너를 생성합니다

* `private` 네트워크를 `DB`에 연결하면서 `Alias`를 설정합니다.

* `PgAdmin`에서 `IP` 대신 `Alias`를 이용하여 `DB`에 연결합니다.