---
title: "Windows를 Kubernetes 클라이언트로 설정"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "쿠버네티스", "2장 실습환경구축"]
is_public: true
draft: false
---

# **Windows를 Kubernetes 클라이언트로 설정**

현재 환경:

```
VM 3대
- Control Plane 1
- Worker 2
Windows PC → 클라이언트
```

목표:

> Windows에서 kubectl로 클러스터 제어

---

# 1️⃣ 사전 확인 사항

---

## 1.1 Windows 버전 확인

PowerShell 실행:

```
winver
```

Windows 10 21H2 이상 또는 Windows 11이면

winget 기본 포함.

---

## 1.2 winget 설치 여부 확인

```
winget --version
```

버전이 나오면 정상.

---

# 2️⃣ kubectl 설치 (winget)

---

## 2.1 kubectl 설치

PowerShell (관리자 권한 권장):

```
winget install -e --id Kubernetes.kubectl
```

설치 확인:

```
kubectl version --client
```

출력 예:

```
Client Version: v1.29.x
```

---

# 3️⃣ kubeconfig 복사

---

## 3.1 Control Plane에서 kubeconfig 확인

Control Plane VM에서:

```
cat ~/.kube/config
```

또는

```
sudo cat /etc/kubernetes/admin.conf
```

이 파일을 Windows로 복사한다.

방법:

* WinSCP

* scp

* 메모장 복사

* VSCode Remote

---

## 3.2 Windows에 저장 위치

Windows에서 다음 경로 생성:

```
C:\Users\사용자이름\.kube\
```

파일 저장:

```
C:\Users\사용자이름\.kube\config
```

---

# 4️⃣ kubeconfig 수정

---

기존 config에는 보통 이렇게 되어 있다.

```
server: https://127.0.0.1:6443
```

이 부분을 Control Plane VM의 IP로 변경한다.

예:

```
server: https://192.168.80.100:6443
```

⚠ 반드시 Control Plane 실제 IP 사용

---

# 5️⃣ 네트워크 확인

---

## 5.1 Control Plane에서 API Server 포트 확인

```
sudo netstat -ntlp | grep 6443
```

정상 출력되어야 함.

---

## 5.2 방화벽 확인 (Ubuntu 예시)

```
sudo ufw status
```

필요 시 허용:

```
sudo ufw allow 6443/tcp
```

---

## 5.3 Windows에서 포트 테스트

PowerShell:

```
Test-NetConnection 192.168.80.100 -Port 6443
```

TcpTestSucceeded: True → 정상

---

# 6️⃣ 연결 테스트

---

PowerShell에서:

```
kubectl get nodes
```

정상 출력 예:

```
NAME              STATUS   ROLES           AGE
control-plane     Ready    control-plane   3d
worker1           Ready    <none>          3d
worker2           Ready    <none>          3d
```

성공.

---

# 7️⃣ 정리

Windows를 클라이언트로 사용하려면:

1. winget으로 kubectl 설치

2. kubeconfig 복사

3. server 주소를 Control Plane IP로 변경

4. 6443 포트 오픈 확인

5. kubectl get nodes 테스트

---