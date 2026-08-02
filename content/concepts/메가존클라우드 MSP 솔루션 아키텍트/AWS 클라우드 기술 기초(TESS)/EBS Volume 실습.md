---
title: "EBS Volume 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 클라우드 기술 기초(TESS)"]
is_public: true
draft: false
---

# EBS Volume 실습

---

# 실습 목표

본 실습에서는 AWS EBS 스토리지의 주요 기능을 실습한다.

다음 내용을 학습한다.

* EBS Volume 용량 확장

* 신규 EBS Volume 생성 및 연결

* 파일 시스템 마운트

* EBS Snapshot 생성

* Snapshot 기반 Volume 복제

* Snapshot 리전 복제

* Snapshot Lifecycle Policy 설정

---

# 1. EBS Volume Size 확장

기존 Web Server의 루트 볼륨을 확장하는 실습이다.

---

# 1.1 EBS 볼륨 사이즈 수정

다음 인스턴스 선택

```
이니셜-ec2-web
```

다음 메뉴 이동

```
EC2 콘솔
→ 인스턴스
→ 이니셜-ec2-web
→ 스토리지
→ Volume ID
```

다음 메뉴 선택

```
작업
→ 볼륨 수정
```

볼륨 크기 변경

```
20 GiB
```

수정 버튼 클릭

---

# 1.2 Web Server 접속

SSH 접속

```
ssh web-server
```

확장된 디스크 확인

```
lsblk
```

예시

```
NAME        SIZE TYPE MOUNTPOINT
nvme0n1     20G  disk
└─nvme0n1p1  8G  part /
```

볼륨 크기는 늘어났지만 **파티션 크기는 아직 증가하지 않은 상태**이다.

---

# 1.3 파티션 확장

Xen 기반 인스턴스

```
sudo growpart /dev/xvda 1
```

Nitro 기반 인스턴스

```
sudo growpart /dev/nvme0n1 1
```

확인

```
lsblk
```

---

# 1.4 파일 시스템 확장

파일 시스템 확인

```
df -Th
```

---

## XFS 파일 시스템

```
sudo xfs_growfs -d /
```

---

## EXT 파일 시스템

```
sudo resize2fs /dev/xvda1
```

또는

```
sudo resize2fs /dev/nvme0n1p1
```

---

# 2. EBS Volume 생성 및 연결

---

# 2.1 신규 EBS Volume 생성

다음 메뉴 이동

```
EC2 콘솔
→ 볼륨
→ 볼륨 생성
```

설정

```
Volume Type : gp3
Size : 10 GiB
Availability Zone : ap-northeast-2a
```

생성 버튼 클릭

---

# 2.2 Web Server에 볼륨 연결

생성된 볼륨 선택

다음 메뉴 이동

```
작업
→ 볼륨 연결
```

설정

```
Instance : 이니셜-ec2-web
Device name : /dev/sdf
```

연결 버튼 클릭

---

# 2.3 Web Server 접속

```
ssh web-server
```

볼륨 확인

```
lsblk
```

예시

```
nvme0n1  8G
nvme1n1 10G
```

---

# 2.4 파일 시스템 생성

마운트 디렉터리 생성

```
sudo mkdir /data
```

파일 시스템 생성

```
sudo mkfs.xfs /dev/nvme1n1
```

마운트

```
sudo mount /dev/nvme1n1 /data
```

확인

```
lsblk
```

---

# 2.5 자동 마운트 설정

UUID 확인

```
sudo blkid
```

예시

```
/dev/nvme1n1: UUID="xxxxx"
```

fstab 설정

```
sudo vim /etc/fstab
```

추가

```
UUID=xxxxx   /data   xfs   defaults,noatime   1   1
```

마운트 테스트

```
sudo umount /data
```

```
sudo mount -a
```

---

# 3. EBS Snapshot 생성

---

# 3.1 Snapshot 생성

다음 인스턴스 선택

```
이니셜-ec2-web
```

다음 메뉴 이동

```
스토리지
→ Volume ID
→ 작업
→ 스냅샷 생성
```

설정

```
Description : 이니셜-snapshot-web
Tag : Name = 이니셜-snapshot-web
```

스냅샷 생성

---

# 3.2 Snapshot 기반 Volume 생성

다음 메뉴 이동

```
EC2
→ 스냅샷
→ 이니셜-snapshot-web
→ 작업
→ 스냅샷에서 볼륨 생성
```

설정

```
Availability Zone : ap-northeast-2c
Encryption : Enabled
Tag : Name = 이니셜-ebs-web
```

볼륨 생성

---

# 3.3 Bastion Server에 볼륨 연결

다음 메뉴 이동

```
볼륨
→ 이니셜-ebs-web
→ 작업
→ 볼륨 연결
```

설정

```
Instance : 이니셜-ec2-bastion
Device : /dev/sdf
```

---

# 3.4 파일 시스템 마운트

서버 접속 후 확인

```
lsblk
```

마운트 디렉터리 생성

```
sudo mkdir /web_directory
```

마운트

```
sudo mount /dev/nvme1n1p1 /web_directory
```

확인

```
lsblk
```

---

# 3.5 Web Server 데이터 확인

root 계정 전환

```
sudo su -
```

디렉터리 이동

```
cd /web_directory/
```

파일 확인

```
ls
```

Snapshot을 통해 **기존 서버의 데이터가 그대로 복제된 것을 확인할 수 있다.**

---

# 4. Snapshot 리전 복제

다음 메뉴 이동

```
EC2
→ 스냅샷
→ 이니셜-snapshot-web
→ 작업
→ 스냅샷 복사
```

설정

```
Destination Region : us-east-1
Encryption : Enabled
```

복사 실행

---

# 5. Snapshot Lifecycle Policy

Snapshot을 자동으로 생성하고 관리하기 위한 정책 설정이다.

---

# 5.1 Lifecycle Policy 생성

다음 메뉴 이동

```
EC2
→ 수명 주기 관리자
→ 사용자 지정 정책
→ EBS Snapshot 정책
```

---

# 5.2 대상 리소스 설정

Resource Type

```
Volume
```

Tag

```
Key : Name
Value : 이니셜-ebs-web
```

정책 설명

```
lifecycle for web server ebs
```

---

# 5.3 Snapshot 일정 설정

설정

```
Schedule Name : 이니셜-ebslc-web
Frequency : Daily
Interval : 24 hours
Start Time : 09:00
Retention Type : Count
Retention : 5
```

즉 **최대 5개의 Snapshot을 유지한다.**

정책 생성

---

# 정리

이번 실습에서 수행한 작업

1. EBS Volume 확장

2. 신규 Volume 생성

3. Volume 연결 및 마운트

4. Snapshot 생성

5. Snapshot 기반 Volume 복제

6. Snapshot 리전 복제

7. Lifecycle Policy 설정

EBS Snapshot은 다음과 같은 목적에 사용된다.

* 데이터 백업

* 장애 복구

* 리전 간 데이터 복제

* 서버 복제

---