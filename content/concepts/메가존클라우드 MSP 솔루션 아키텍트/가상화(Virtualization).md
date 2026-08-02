---
title: "가상화(Virtualization)"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트"]
is_public: true
draft: false
---

# 가상화(Virtualization)

## 1. 가상화(Virtualization)란 무엇인가?

### 1.1 정의

* 가상화(Virtualization)란

👉 **하나의 물리적 하드웨어 자원을 논리적으로 분할**하여

👉 **여러 개의 독립적인 실행 환경(가상 머신)** 을 동시에 운영하는 기술이다.

즉,

* 물리 서버 1대

* → 논리적으로 여러 대의 서버처럼 사용

* → 각 서버는 **독립적인 OS와 애플리케이션** 실행

---

### 1.2 가상화가 등장한 배경

| 문제점 (가상화 이전) | 설명 |
| --- | --- |
| 낮은 자원 활용률 | 서버 1대에 서비스 1개 → CPU 사용률 5~10% |
| 서버 증설 비용 | 서비스 증가 = 서버 구매 |
| 운영 복잡도 | 서버 수 증가 → 관리 포인트 증가 |
| 장애 대응 어려움 | 물리 서버 장애 시 복구 시간 길어짐 |

➡️ **하드웨어를 효율적으로 쓰기 위한 기술**로 가상화가 등장

---

## 2. 가상화의 핵심 개념

### 2.1 물리 머신(Host) vs 가상 머신(Guest)

| 구분 | 설명 |
| --- | --- |
| **Host (호스트)** | 실제 하드웨어가 설치된 물리 서버 |
| **Guest (게스트)** | 가상화 기술로 만들어진 논리적 서버 |
| **VM (Virtual Machine)** | Guest OS + 가상 하드웨어 |

> 💡 게스트는 **자신이 가상 환경이라는 사실을 모른다**
>
> → 실제 서버라고 인식하고 동작

---

### 2.2 하이퍼바이저(Hypervisor)

[![](https://www.researchgate.net/publication/335866538/figure/fig2/AS%3A882394324287494%401587390609903/Type-1-and-type-2-hypervisors.png)](https://www.researchgate.net/publication/335866538/figure/fig2/AS%3A882394324287494%401587390609903/Type-1-and-type-2-hypervisors.png)

**하이퍼바이저**는

👉 **물리 하드웨어와 가상 머신 사이에서 자원을 중재**하는 소프트웨어 계층이다.

역할:

* CPU 스케줄링

* 메모리 할당

* 디스크 I/O 중재

* 네트워크 가상화

---

## 3. 하이퍼바이저 유형

### 3.1 Type 1 (Bare-metal Hypervisor)

### 구조

```
[ Hardware ]
     ↓
[ Hypervisor ]
     ↓
[ VM1 | VM2 | VM3 ]
```

### 특징

* OS 없이 **하드웨어 위에 직접 설치**

* 성능 우수

* 안정성 높음

* 서버/클라우드 환경에 사용

### 예시

* KVM (Linux Kernel 기반)

* Xen

* ESXi

---

### 3.2 Type 2 (Hosted Hypervisor)

### 구조

```
[ Hardware ]
     ↓
[ Host OS ]
     ↓
[ Hypervisor ]
     ↓
[ VM ]
```

### 특징

* 일반 OS 위에서 실행

* 설치 간편

* 성능은 Type 1보다 낮음

* 개발/테스트/교육용

### 예시

* VirtualBox

* VMware Workstation

---

### 3.3 Type 1 vs Type 2 비교

| 구분 | Type 1 | Type 2 |
| --- | --- | --- |
| 설치 위치 | 하드웨어 위 | Host OS 위 |
| 성능 | 높음 | 상대적으로 낮음 |
| 안정성 | 매우 높음 | Host OS 의존 |
| 사용 환경 | 서버, 클라우드 | 개인 PC, 실습 |

---

## 4. 가상 머신 내부 구조

[![](https://www.researchgate.net/publication/270058181/figure/fig2/AS%3A670717515407370%401536922925442/Typical-Virtual-Machine-architecture-1.png)](https://www.researchgate.net/publication/270058181/figure/fig2/AS%3A670717515407370%401536922925442/Typical-Virtual-Machine-architecture-1.png)

가상 머신은 다음과 같은 **가상 하드웨어**를 가진다.

| 구성 요소 | 설명 |
| --- | --- |
| vCPU | 물리 CPU를 논리적으로 분할 |
| vMemory | 실제 RAM 일부를 할당 |
| vDisk | 파일 형태의 디스크 |
| vNIC | 가상 네트워크 인터페이스 |

> 💡 실제 하드웨어 접근은 **모두 하이퍼바이저를 통해 간접 처리**

---

## 5. 전가상화 vs 반가상화

### 5.1 전가상화 (Full Virtualization)

* Guest OS 수정 ❌

* 실제 하드웨어처럼 **완전한 가상 환경 제공**

* 성능 오버헤드 존재

예:

* 초기 VMware

* QEMU

---

### 5.2 반가상화 (Paravirtualization)

* Guest OS 수정 ⭕

* 하이퍼바이저와 **직접 통신**

* 성능 향상

예:

* Xen Paravirtualized Mode

---

## 6. 하드웨어 지원 가상화

현대 가상화의 핵심은 **CPU 가상화 지원 기능**이다.

| 제조사 | 기술 |
| --- | --- |
| Intel | VT-x |
| AMD | AMD-V |

### 효과

* CPU 명령어 트랩 감소

* VM 성능 대폭 향상

* 거의 네이티브 성능

---

## 1. 왜 KVM은 전가상화인가?

[![](https://d1.awsstatic.com/xen-kvm%281%29.1d05f32a1acafb6d1e20094b327c823666f599fa.png)](https://d1.awsstatic.com/xen-kvm%281%29.1d05f32a1acafb6d1e20094b327c823666f599fa.png)

### KVM의 기본 동작 방식

KVM(Kernel-based Virtual Machine)은 다음 조건을 만족합니다.

### ① Guest OS 수정이 필요 없음

* Linux, Windows, BSD 등 **기존 OS 그대로 실행**

* 커널 패치 ❌

* → **전가상화의 핵심 조건**

### ② CPU 하드웨어 가상화 기능 사용

* Intel VT-x

* AMD-V

➡️ CPU가 **게스트의 특권 명령어를 직접 처리**

➡️ 하이퍼바이저가 “완전한 가상 하드웨어” 제공

📌 이 구조는 **고전적인 전가상화 정의에 정확히 부합**

---

## 2. 그럼 왜 “반가상화”라고도 말하나?

이 부분이 **가장 많이 헷갈리는 포인트**입니다.

[![](https://projectacrn.github.io/latest/_images/virtio-hld-image71.png)](https://projectacrn.github.io/latest/_images/virtio-hld-image71.png)

### 핵심 원인: **Virtio 드라이버**

KVM에서는 성능을 높이기 위해

**반가상화 드라이버(Paravirtualized Driver)** 를 사용합니다.

### Virtio란?

* 디스크, 네트워크, 메모리 I/O용 **반가상화 장치 드라이버**

* Guest OS 내부에 드라이버 설치 ⭕

* 하이퍼바이저와 **직접 통신 경로 제공**

### 대표 예

* virtio-net (네트워크)

* virtio-blk / virtio-scsi (디스크)

* virtio-balloon (메모리)

---

## 3. 정리: “가상화 방식” vs “성능 최적화 방식”

| 구분 | 의미 |
| --- | --- |
| 가상화 방식 | VM을 **어떻게 실행시키는가** |
| I/O 처리 방식 | VM이 **하드웨어를 어떻게 쓰는가** |

👉 KVM은 이 둘을 **혼합**해서 사용

---

### 정확한 분류표

| 항목 | KVM |
| --- | --- |
| 가상화 방식 | ✅ 전가상화 |
| Guest OS 수정 | ❌ 불필요 |
| CPU 가상화 | VT-x / AMD-V |
| I/O 최적화 | Virtio (반가상화 드라이버) |
| 최종 분류 | **전가상화 + 반가상화 드라이버 병행** |

---

## 4. 정리

> **“KVM은 전가상화 하이퍼바이저이지만, 디스크·네트워크 성능 향상을 위해 반가상화 드라이버(Virtio)를 함께 사용한다.”**

---

## 5. Xen과 비교

| 항목 | KVM | Xen |
| --- | --- | --- |
| 기본 방식 | 전가상화 | 반가상화 |
| Guest OS 수정 | 필요 없음 | 필요(초기) |
| 하드웨어 가상화 | 필수 | 초기에는 없음 |
| 현재 운영 방식 | 전가상화 + Virtio | 전가상화(HVM) + PV 드라이버 |