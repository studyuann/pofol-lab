---
title: "NFS 서비스"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "쿠버네티스", "11장 PV PVC StorageClass", "NFS 이용하기"]
is_public: true
draft: false
---

# **NFS 서비스**

[![](NFS%20%EC%84%9C%EB%B9%84%EC%8A%A4/image.png)](NFS%20%EC%84%9C%EB%B9%84%EC%8A%A4/image.png)

### 1. 개요

* **NFS (Network File System)**: 네트워크 상의 다른 컴퓨터와 파일을 공유할 수 있게 해주는 프로토콜입니다. 주로 Linux/Unix 환경에서 사용됩니다.

### 2. 실습 환경

* OS: Rocky Linux 8

* 실습 목표:

**NFS** 설정하여 Linux 간 파일 공유

---

### 3. **NFS 설정 실습**

### 3.1. NFS 서버 설치

1. **NFS 서버 설치**

   ```
   sudo dnf install -y nfs-utils
   ```

2. **NFS 서비스 시작 및 부팅 시 자동 시작 설정**

   ```
   sudo systemctl enable --now nfs-server
   ```

3. **방화벽 설정 (포트 2049 허용)**

   ```
   sudo firewall-cmd --permanent --add-service=nfs
   sudo firewall-cmd --reload
   ```

4. **NFS 공유 디렉토리 생성**

   예: `/srv/nfs_share` 디렉토리 생성

   ```
   sudo mkdir -p /srv/nfs_share
   sudo chown nfsnobody:nfsnobody /srv/nfs_share
   sudo chmod 755 /srv/nfs_share
   ```

5. **NFS 공유 설정**

   `/etc/exports` 파일에 공유할 디렉토리 추가

   ```
   echo "/srv/nfs_share *(rw,sync,no_root_squash)" | sudo tee -a /etc/exports
   ```

6. **NFS 설정 적용**

   ```
   sudo exportfs -r
   ```

### 3.2. 클라이언트에서 NFS 공유 마운트

1. **NFS 클라이언트 설치**

   ```
   sudo dnf install -y nfs-utils
   ```

2. **NFS 공유 디렉토리 마운트**

   ```
   sudo mount -t nfs <서버_IP>:/srv/nfs_share /mnt
   ```

3. **마운트된 공유 디렉토리 확인**

   ```
   df -h
   ```

4. **영구 마운트 설정 (옵션)**

   `/etc/fstab` 파일에 NFS 공유 디렉토리 추가

   ```
   <서버_IP>:/srv/nfs_share /mnt nfs defaults 0 0
   ```

### 3.3. NFS 서비스 확인

1. **서버에서 NFS 서비스 상태 확인**

   ```
   sudo systemctl status nfs-server
   ```

2. **클라이언트에서 NFS 공유 확인**

   ```
   showmount -e <서버_IP>
   ```