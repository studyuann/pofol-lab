---
title: "2장 리소스 계층 구조와 IAM"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Google 클라우드 핵심 서비스"]
is_public: true
draft: false
---

# 2장. 리소스 계층 구조와 IAM

### 1. 장 개요

앞 장에서 Organization, Folder, Project라는 계층 구조를 살펴봤다면, 이번 장에서는 그 구조가 실제 운영에서 왜 중요한지, 특히 **권한 상속**과 **프로젝트 중심 운영** 관점에서 이해하는 데 초점을 둔다.

AWS를 먼저 학습한 경우에는 보통 다음과 같은 감각이 이미 형성되어 있다.

* IAM User, Group, Role, Policy 개념을 알고 있음

* Account 단위로 권한 경계를 나누는 방식에 익숙함

* EC2 Role, AssumeRole, Policy Attachment 같은 개념을 사용해본 경험이 있음

하지만 GCP에서는 권한을 이해할 때 생각의 순서가 다소 다르다.

먼저 **어느 리소스 범위에 권한을 줄 것인지**를 본다.

그 다음 **누구에게 줄 것인지**를 본다.

마지막으로 **어떤 역할(Role)을 줄 것인지**를 결정한다.

즉, GCP IAM은 단순히 “사용자에게 권한을 준다”는 방식으로 이해하기보다, **리소스 계층 구조 안의 특정 범위에 어떤 Principal을 어떤 Role로 바인딩하는가**라는 관점으로 이해하는 것이 더 정확하다.

---

### 2. 학습 목표

* GCP 리소스 계층 구조와 IAM의 관계를 설명할 수 있음

* Principal, Role, Permission, Policy Binding 개념을 설명할 수 있음

* Basic Role, Predefined Role, Custom Role의 차이를 설명할 수 있음

* Service Account의 목적과 사용 이유를 설명할 수 있음

* 권한 상속 구조가 어떻게 동작하는지 설명할 수 있음

* AWS IAM과 GCP IAM의 차이를 비교할 수 있음

* 프로젝트 수준에서 적절한 권한 부여 실습을 수행할 수 있음

---

### 3. 핵심 키워드

* Resource Hierarchy

* Organization

* Folder

* Project

* Principal

* Role

* Permission

* Policy Binding

* Inheritance

* Service Account

* Least Privilege

---

## 4. 왜 GCP에서 IAM이 중요한가

클라우드에서 IAM은 단순한 로그인 기능이 아니다. IAM은 **누가 무엇을 할 수 있는가를 결정하는 핵심 통제 지점**이다.

예를 들어 다음과 같은 질문은 모두 IAM과 직접 연결된다.

* 누가 VM을 생성할 수 있는가

* 누가 Cloud Storage 버킷의 객체를 읽을 수 있는가

* 누가 로그를 조회할 수 있는가

* 애플리케이션은 어떤 권한으로 Secret을 읽는가

* 특정 팀은 어느 프로젝트까지만 접근해야 하는가

즉, IAM은 보안 기능이면서 동시에 운영 기능이다. 권한을 잘못 설계하면 보안 사고가 발생할 수 있고, 반대로 권한을 지나치게 제한하면 운영 업무 자체가 진행되지 않을 수 있다.

GCP에서도 IAM은 매우 중요하다.

비슷한 부분은 다음과 같다.

* 사용자나 서비스에 권한을 준다는 점

* 역할 기반 접근 제어가 중요하다는 점

* 최소 권한 원칙이 중요하다는 점

* 사람 계정과 시스템 계정을 구분해야 한다는 점

반면 다른 부분은 다음과 같다.

* Project 중심으로 권한을 보는 경우가 많다는 점

* Organization, Folder, Project 상속 구조가 강하게 작동한다는 점

* 정책 문서를 길게 설계하는 느낌보다, **리소스에 대해 Role Binding을 부여하는 감각**이 더 강하다는 점

* Service Account가 워크로드 권한 부여의 핵심이라는 점

결국 GCP IAM은 “정책 문서를 작성하는 기능”으로 접근하기보다, **특정 리소스 범위에 대해 Principal과 Role을 연결하는 구조**로 이해하는 편이 훨씬 빠르다.

---

## 5. GCP 리소스 계층 구조 다시 보기

GCP의 리소스 계층 구조는 다음과 같다.

* Organization
  + Folder
    - Project
      * Resource

이 구조는 단순히 리소스를 보기 좋게 정리하기 위한 것이 아니다. GCP에서는 **IAM 권한과 조직 정책이 이 구조를 따라 적용되고 상속될 수 있기 때문**에 매우 중요하다.

예를 들어 다음과 같은 상황을 생각해볼 수 있다.

* Organization 레벨에서 특정 팀에 Viewer 역할을 부여함

* 그러면 그 하위 Folder와 Project에도 그 권한이 영향을 줄 수 있음

* Folder 레벨에서 부여한 권한은 그 아래 여러 Project에 적용될 수 있음

* Project 레벨의 권한은 일반적으로 해당 Project 내부 리소스에 영향을 줌

따라서 “무슨 권한을 줄 것인가”만큼이나 “**어디에 줄 것인가**”가 중요하다.

같은 `Viewer` 권한이라도

* Organization에 주는 것

* Folder에 주는 것

* Project에 주는 것

은 범위가 완전히 다르다.

이 점은 AWS에서 어느 Account, 어느 OU, 어느 리소스 경계에 정책을 적용하느냐가 중요한 것과 유사하지만, GCP는 계층 상속 구조가 콘솔과 정책 조회 결과에서 더 직접적으로 드러나는 편이다.

즉, GCP IAM을 이해할 때는 역할의 종류만 보는 것이 아니라, **권한이 걸리는 범위와 그 범위가 상위/하위 구조에서 어떤 의미를 가지는지**를 함께 봐야 한다.

---

## 6. GCP IAM의 핵심 구성 요소

GCP IAM을 이해하려면 먼저 네 가지 개념을 구분해야 한다.

* Principal

* Permission

* Role

* Policy Binding

이 네 가지가 연결되어 실제 권한 부여가 이루어진다.

---

### 6.1 Principal이란 무엇인가

Principal은 권한을 부여받는 주체다.

즉, “누가 권한을 받는가”에서의 **누구**에 해당한다.

대표적인 Principal 예시는 다음과 같다.

* Google 계정 사용자

* Google 그룹

* 서비스 계정(Service Account)

* 도메인

* 전체 인증 사용자

* 전체 사용자(익명 포함)

예를 들어 다음과 같은 형식이 사용된다.

* `user:alice@example.com`

* `group:dev-team@example.com`

* `serviceAccount:web-sa@my-project.iam.gserviceaccount.com`

즉, Principal은 사람일 수도 있고, 그룹일 수도 있으며, 애플리케이션이나 워크로드를 대표하는 서비스 계정일 수도 있다.

AWS에서도 Principal이라는 표현이 정책 문서에 등장하지만, 학습 초반에는 보통 User, Group, Role 중심으로 생각하는 경우가 많다. 반면 GCP에서는 Principal이라는 표현을 더 직접적으로 자주 사용하게 된다.

따라서 GCP IAM은 다음과 같은 구조로 이해하면 명확하다.

* 어떤 Principal에게

* 어떤 Role을

* 어느 리소스 범위에 줄 것인가

---

### 6.2 Permission이란 무엇인가

Permission은 실제로 수행 가능한 **개별 작업 단위**다.

예를 들어 다음과 같은 동작 하나하나가 Permission에 해당한다.

* VM 조회

* VM 생성

* 버킷 객체 조회

* 버킷 객체 업로드

* 방화벽 규칙 수정

* 로그 읽기

GCP의 Permission 이름은 보통 서비스 이름과 동작이 결합된 형태를 가진다.

예시:

* `compute.instances.get`

* `compute.instances.create`

* `storage.objects.get`

* `storage.objects.create`

Permission은 권한의 최소 단위라고 볼 수 있다. 그러나 실제 운영에서는 Permission을 하나씩 직접 부여하는 경우는 드물다. 그 이유는 Permission이 지나치게 세밀하기 때문이다.

실제 운영에서는 여러 Permission을 묶어 놓은 Role을 부여한다. 따라서 Permission은 **실행 가능한 세부 동작**, Role은 **그 동작들의 묶음**으로 이해하면 된다.

---

### 6.3 Role이란 무엇인가

Role은 여러 Permission을 묶어 놓은 집합이다.

실제 권한 부여는 대부분 Permission 단위가 아니라 Role 단위로 이루어진다. 예를 들어 다음과 같은 역할이 있다.

* Compute Engine Viewer

* Storage Object Viewer

* Logging Viewer

* Compute Admin

* Storage Admin

각 Role 안에는 해당 업무를 수행하는 데 필요한 Permission들이 포함되어 있다.

Role이 중요한 이유는 실무에서 권한을 업무 기준으로 설계하기 때문이다. 일반적으로 다음과 같은 순서로 생각한다.

1. 이 사용자가 어떤 업무를 수행하는가

2. 그 업무에 어떤 동작이 필요한가

3. 그 동작을 포함하는 Role이 무엇인가

4. 그 Role을 어느 범위에 부여할 것인가

예를 들어 어떤 운영 담당자가 해야 할 일이 다음 정도라고 하자.

* VM 조회

* VM 시작 및 중지

* 로그 조회

이 경우 프로젝트 전체 `Editor` 를 부여하는 것은 지나치게 넓을 수 있다. 대신 필요한 서비스의 적절한 Role만 조합해서 부여하는 편이 더 안전하고 정확하다.

즉, GCP IAM에서 Role은 사용자 이름에 따라 정하는 것이 아니라, **업무 목적에 맞추어 선택하는 권한 단위**라고 보면 된다.

---

### 6.4 Policy Binding이란 무엇인가

Policy Binding은 **어떤 Principal에게 어떤 Role을 어떤 리소스 범위에 부여하는 연결 정보**다.

쉽게 말하면 다음 세 가지를 묶는 구조다.

* 누구에게

* 어떤 역할을

* 어느 범위에

예를 들어 다음과 같은 경우 하나의 Binding이 된다.

* `alice@example.com` 에게

* `roles/viewer` 를

* 특정 Project에 부여

이 개념은 GCP IAM을 이해하는 데 매우 중요하다.

GCP IAM을 한 문장으로 정리하면 다음과 같다.

**GCP IAM은 리소스에 대해 Principal과 Role을 Binding하는 구조다.**

AWS에서는 정책을 사용자, 그룹, 역할에 부착하는 감각이 강하게 느껴지는 반면, GCP에서는 특정 리소스 범위에 대해 Principal과 Role을 연결하는 감각이 더 강하다.

따라서 GCP 콘솔과 CLI를 사용할 때도 “정책 문서 작성”보다 “Binding 추가”라는 방식으로 인식하는 것이 자연스럽다.

---

## 7. Role의 종류

GCP의 Role은 크게 세 가지로 나눌 수 있다.

* Basic Role

* Predefined Role

* Custom Role

이 세 가지는 범위와 정밀도 측면에서 차이가 있다.

---

### 7.1 Basic Role

Basic Role은 프로젝트 수준에서 오래전부터 제공되던 넓은 범위의 기본 역할이다.

대표적인 예시는 다음과 같다.

* Viewer

* Editor

* Owner

각 역할의 의미는 다음과 같다.

### Viewer

읽기 중심 권한이다.

리소스를 조회하고 상태를 확인할 수 있다.

### Editor

많은 리소스를 생성하고 수정할 수 있는 광범위한 쓰기 권한이다.

### Owner

프로젝트에 대한 매우 넓은 관리 권한을 가진다. 경우에 따라 IAM 관리와 같은 강한 권한까지 포함될 수 있다.

Basic Role은 이해하기는 쉽고, 실습 환경에서는 편의상 사용할 수 있다. 그러나 범위가 매우 넓기 때문에 실제 운영에서는 신중하게 사용해야 한다.

예를 들어 `Editor` 는 단순히 특정 서비스 하나만 수정할 수 있는 것이 아니라, 프로젝트 전반에 걸쳐 예상보다 넓은 수정 권한을 가질 수 있다. 따라서 최소 권한 원칙을 적용하려는 환경에서는 적절하지 않은 경우가 많다.

AWS에서 `AdministratorAccess` 같은 광범위한 권한을 무분별하게 부여하는 것이 위험한 것과 비슷한 맥락으로 이해하면 된다.

즉, Basic Role은 구조를 빠르게 이해하는 데는 도움이 되지만, 실무 권한 설계의 기본 선택지는 아니다.

---

### 7.2 Predefined Role

Predefined Role은 Google이 서비스별로 미리 정의해 둔 역할이다.

실무에서는 이 역할군을 가장 자주 사용한다.

예를 들어 다음과 같은 Role이 있다.

* `roles/compute.viewer`

* `roles/compute.instanceAdmin.v1`

* `roles/storage.objectViewer`

* `roles/storage.admin`

* `roles/logging.viewer`

Predefined Role의 장점은 다음과 같다.

* 서비스 단위로 세분화되어 있음

* Basic Role보다 훨씬 정밀함

* 최소 권한 원칙 적용이 쉬움

* Google이 관리하므로 권한 체계 변화에 대응하기 좋음

예를 들어 어떤 운영자가 다음 권한만 필요하다고 하자.

* VM 조회

* VM 시작 및 중지

* 로그 조회

이 경우 프로젝트 전체 `Editor` 를 부여하는 대신, Compute 관련 Role과 Logging 관련 Role을 조합하는 편이 더 적절하다.

즉, GCP의 권한 설계에서는 보통

* Basic Role보다

* Predefined Role을 우선 검토하고

* 필요한 것만 선택하여 부여하는 방식

으로 접근하는 것이 일반적이다.

---

### 7.3 Custom Role

Custom Role은 조직이나 프로젝트에서 직접 정의하는 사용자 지정 역할이다.

이 역할은 Predefined Role만으로 원하는 권한 수준을 정확히 맞추기 어려울 때 사용한다.

예를 들어 어떤 운영자에게

* VM 조회

* VM 시작

* VM 중지

권한만 주고 싶고, 삭제는 허용하지 않으려 한다고 하자. 그런데 기존 Predefined Role이 이 요구보다 넓다면, 필요한 Permission만 묶어서 Custom Role을 만들 수 있다.

Custom Role의 장점은 다음과 같다.

* 최소 권한 원칙을 매우 정밀하게 적용할 수 있음

* 조직 표준 역할 체계를 직접 설계할 수 있음

반면 단점도 있다.

* 설계와 유지관리가 번거로움

* 권한 구조를 직접 검토해야 함

* 서비스 Permission 변화에 따라 주기적 점검이 필요할 수 있음

처음 IAM을 학습할 때는 Basic Role과 Predefined Role의 차이와 의미를 먼저 이해하는 것이 중요하다. Custom Role은 **Predefined Role만으로 필요한 권한 범위를 정확히 맞추기 어려운 경우에 사용하는 정밀 권한 설계 도구**라고 이해하면 된다.

---

## 8. 권한 상속(Inheritance)

GCP IAM의 핵심 중 하나는 **권한 상속**이다.

상위 계층에서 부여한 권한은 하위 계층에 영향을 줄 수 있다.

예를 들어 Organization에 Viewer를 부여하면, 그 하위 Folder와 Project에도 그 영향이 갈 수 있다. 마찬가지로 Folder에 부여한 Role은 그 아래 여러 Project에 상속될 수 있다.

이 구조가 중요한 이유는 관리 편의성과 보안 범위가 동시에 연결되기 때문이다.

상위에 권한을 주면 관리가 편해질 수 있다. 예를 들어 어떤 부서 전체에 공통 권한을 한 번에 부여하기 좋다. 하지만 상위에 권한을 줄수록 그 범위는 넓어진다. 따라서 원래는 일부 프로젝트에만 접근해야 하는 사용자가 상위 권한 상속 때문에 더 많은 리소스를 볼 수 있게 될 수도 있다.

따라서 GCP IAM에서는 다음 원칙이 중요하다.

* 가능한 한 필요한 범위에만 권한을 부여한다

* 상위 계층 권한 부여는 신중하게 사용한다

* 처음에는 Project 단위 권한부터 이해한다

* 상위로 갈수록 범위가 넓어진다는 점을 항상 의식한다

실제 교육과 실습에서는 Organization이나 Folder보다 **Project 단위 권한 부여**부터 이해하는 편이 가장 직관적이다. 그 다음 상위 계층으로 올라가며 “이 권한이 더 넓은 범위에 상속될 수 있다”는 개념을 연결하면 이해가 쉬워진다.

---

## 9. Service Account란 무엇인가

Service Account는 사람이 사용하는 계정이 아니라, **애플리케이션이나 워크로드가 사용하는 계정**이다.

예를 들어 다음과 같은 경우에 사용한다.

* VM이 Cloud Storage에 접근해야 할 때

* 애플리케이션이 Secret을 읽어야 할 때

* 배치 작업이 Pub/Sub나 BigQuery에 접근해야 할 때

* 서버 애플리케이션이 GCP API를 호출해야 할 때

즉, 사람 사용자가 브라우저나 콘솔에 로그인하는 용도의 계정이 아니라, 프로그램이 GCP 리소스에 접근할 때 사용하는 ID다.

Service Account가 필요한 이유는 사람 계정의 자격증명을 애플리케이션 내부에 넣는 것이 매우 위험하기 때문이다. 대신 워크로드 전용 계정을 만들고, 그 계정에 필요한 권한만 부여하면 보안상 훨씬 안전하다.

AWS에서는 EC2에 IAM Role을 연결하고, 애플리케이션이 그 Role 권한으로 AWS API를 호출하는 방식이 익숙하다. GCP에서는 비슷한 목적을 Service Account가 수행한다.

따라서 학습 단계에서는 다음처럼 비교하면 이해하기 쉽다.

* AWS EC2 Role ↔ GCP Service Account

완전히 동일한 개념은 아니지만, **워크로드에 권한을 부여한다**는 목적에서는 매우 유사한 감각으로 이해할 수 있다.

---

### 9.1 Service Account의 사용 방식

Service Account는 보통 다음 흐름으로 사용한다.

1. Service Account 생성

2. 필요한 Role 부여

3. VM 또는 서비스에 연결

4. 애플리케이션이 해당 계정 권한으로 GCP API 접근

예를 들어 웹 서버 VM이 Cloud Storage 버킷에서 파일을 읽어야 한다면 다음과 같이 구성한다.

1. `web-vm-sa` 와 같은 Service Account 생성

2. `Storage Object Viewer` 역할 부여

3. 해당 VM에 Service Account 연결

4. VM 내부 애플리케이션이 그 권한으로 버킷 객체 읽기 수행

여기서 중요한 점은 Service Account 자체가 자동으로 권한을 가지는 것이 아니라는 것이다. 정확히는 **Service Account라는 Principal에 Role을 부여하는 것**이다.

즉, 사람 사용자와 서비스 계정은 용도는 다르지만, IAM 구조 안에서는 둘 다 Principal이라는 공통된 틀 안에서 다뤄진다.

---

### 9.2 서비스 계정 키 파일은 신중하게 사용

Service Account는 JSON 키 파일을 발급하여 외부 환경에서 사용할 수도 있다. 그러나 키 파일은 장기 자격증명에 해당하므로 유출 시 위험하다.

따라서 가능하다면 다음과 같은 방식이 더 바람직하다.

* GCP VM에 Service Account 직접 연결

* 관리형 서비스에 Service Account 연결

* 키 파일 없이 동적으로 자격증명 사용

* 짧은 수명 자격증명 활용

실습 과정에서는 키 파일이 눈에 보이기 때문에 동작 원리를 설명하기에는 편리할 수 있다. 하지만 실제 운영에서는 **키 파일을 제한적으로 사용하는** 이 더 안전하다.

즉, 가능하면 키 없는 방식, 직접 연결 방식, 관리형 자격증명 방식을 우선 고려해야 한다.

---

## 10. AWS IAM과 GCP IAM 비교

AWS를 먼저 학습한 경우에는 GCP IAM을 AWS와 비교하며 이해하는 것이 효과적이다.

---

### 10.1 운영 단위 차이

### AWS

* Account가 강한 운영 경계

* 계정 단위로 IAM 설계를 나누는 경우가 많음

### GCP

* Project가 실질 운영 경계

* Organization / Folder / Project 구조에서 권한 상속을 고려함

즉, AWS에서는 “어느 계정인가”가 매우 중요하고, GCP에서는 “어느 프로젝트인가”가 매우 중요하다.

---

### 10.2 권한 부여 방식의 체감 차이

### AWS

* Policy 문서를 작성하거나 부착하는 감각이 강함

* User / Group / Role 중심으로 생각하는 경우가 많음

### GCP

* Principal에 Role을 Binding하는 감각이 강함

* Resource Hierarchy에 따라 범위를 먼저 생각해야 함

즉, AWS는 정책 부착의 감각이 강하고, GCP는 **리소스 범위에 대한 Binding**의 감각이 더 강하다.

---

### 10.3 워크로드 권한 부여 비교

### AWS

* IAM Role for EC2

* AssumeRole

* IRSA(IAM Roles for Service Accounts) (EKS 환경)

### GCP

* Service Account

* Workload Identity 계열 방식

* VM 또는 서비스에 Service Account 연결

즉, 애플리케이션이나 워크로드에 권한을 부여하는 방식은 두 클라우드 모두 중요하지만, GCP에서는 Service Account가 중심에 있다고 보면 된다.

---

### 10.4 최소 권한 원칙 적용 방식

두 클라우드 모두 최소 권한 원칙이 중요하다. 다만 GCP에서는 일반적으로 다음 순서로 접근한다.

1. Basic Role은 가능한 피한다

2. Predefined Role을 먼저 검토한다

3. 필요하면 Custom Role을 고려한다

즉, 넓은 권한부터 부여하는 것이 아니라, 필요한 권한만 정밀하게 찾는 방향으로 설계하는 것이 바람직하다.

---

## 11. 실습 1: 현재 프로젝트의 IAM 확인

이 실습은 **프로젝트 수준에서 누가 어떤 권한을 가지고 있는지 확인하는 실습**이다.

IAM을 처음 학습할 때는 Organization이나 Folder보다 Project 단위부터 보는 것이 가장 이해하기 쉽다. GCP에서 실제 운영의 중심 경계도 Project이기 때문이다.

---

### 11.1 실습 목표

* 프로젝트 수준 IAM 바인딩을 확인함

* 어떤 Principal에 어떤 Role이 부여되어 있는지 확인함

* GCP IAM이 프로젝트 중심으로 어떻게 보이는지 이해함

---

### 11.2 콘솔 실습

1. Google Cloud Console에 접속한다.

2. 현재 선택된 프로젝트를 확인한다.

3. 좌측 메뉴에서 **IAM 및 관리자(IAM & Admin)** 로 이동한다.

4. **IAM** 메뉴를 선택한다.

5. 현재 프로젝트에 바인딩된 사용자, 그룹, 서비스 계정 목록을 확인한다.

확인할 항목은 다음과 같다.

* 어떤 이메일 계정이 등록되어 있는지

* 어떤 Role이 부여되어 있는지

* Owner, Editor, Viewer 같은 기본 역할이 있는지

* 서비스 계정이 이미 존재하는지

이 화면은 “누가 어떤 권한을 이 프로젝트에서 가지고 있는가”를 가장 직관적으로 보여준다. 즉, GCP IAM의 Binding 결과를 콘솔에서 확인하는 대표적인 화면이라고 볼 수 있다.

---

## 12. 실습 2: Cloud Shell에서 IAM 정책 조회

이제 콘솔이 아니라 CLI에서 프로젝트 IAM 정책을 확인해본다.

---

### 12.1 현재 프로젝트 확인

```
gcloud config get-value project
```

이 명령은 현재 CLI가 어느 프로젝트를 대상으로 동작할지를 확인하는 명령이다.

프로젝트가 잘못 설정되어 있으면 IAM 조회 결과도 엉뚱한 프로젝트 기준으로 출력될 수 있다. 따라서 IAM 관련 명령을 실행하기 전에는 현재 프로젝트부터 확인하는 습관이 중요하다.

---

### 12.2 프로젝트 IAM 정책 조회

```
gcloud projects get-iam-policy [PROJECT_ID]
```

이 명령은 해당 프로젝트에 설정된 IAM 정책을 조회한다.

명령의 의미는 다음과 같다.

* `gcloud projects get-iam-policy`

  프로젝트에 연결된 IAM 정책 전체를 가져오는 명령이다.

* `[PROJECT_ID]`

  실제 프로젝트 ID로 바꾸어 사용해야 한다.

예시:

```
gcloud projects get-iam-policy my-gcp-project
```

처음 이 결과를 보면 내용이 길고 복잡하게 느껴질 수 있다. 그러나 핵심은 크게 두 가지다.

* `role`

* `members`

즉,

* 어떤 역할이 존재하는가

* 그 역할에 어떤 멤버가 연결되어 있는가

이 두 가지를 중심으로 읽으면 된다.

---

### 12.3 JSON 형식으로 보기

```
gcloud projects get-iam-policy [PROJECT_ID] --format=json
```

이 명령은 프로젝트 IAM 정책을 JSON 형식으로 출력한다.

---

## 13. 실습 3: 사용자에게 프로젝트 Viewer 권한 부여

이 실습은 특정 사용자에게 프로젝트 수준의 읽기 권한을 부여하는 방법을 확인하는 과정이다.

이 작업은 교육 환경의 권한 범위에 따라 가능 여부가 달라질 수 있다. 따라서 관리자 권한이 있는 환경에서 수행하는 것이 적절하다.

---

### 13.1 콘솔에서 수행

1. **IAM** 메뉴로 이동한다.

2. **액세스 권한 부여(Grant Access)** 를 클릭한다.

3. 새 Principal을 입력한다.

4. Role을 선택한다.

5. `Viewer` 또는 적절한 읽기 전용 Role을 선택한다.

6. 저장한다.

이 실습에서는 Viewer를 사용해도 되지만, 실제 운영에서는 프로젝트 전체 Viewer 대신 더 좁은 범위의 Predefined Role을 사용하는 것이 더 적절할 수 있다.

---

### 13.2 CLI로 수행

```
gcloud projects add-iam-policy-binding [PROJECT_ID] \
--member="user:user1@example.com" \
--role="roles/viewer"
```

각 항목의 의미는 다음과 같다.

* `gcloud projects add-iam-policy-binding`

  프로젝트 IAM 정책에 새로운 Binding을 추가하는 명령이다.

* `[PROJECT_ID]`

  권한을 부여할 대상 프로젝트 ID다.

* `--member`

  권한을 받을 Principal을 지정한다.

* `user:user1@example.com`

  이메일 사용자 계정에 권한을 부여한다는 의미다.

* `--role="roles/viewer"`

  Viewer 역할을 부여한다.

이 명령은 단순히 “사용자를 추가한다”기보다, 정확히는 **프로젝트 정책에 Principal-Role Binding을 추가하는 작업**이다.

---

## 14. 실습 4: Service Account 생성과 확인

이 실습에서는 워크로드용 계정인 Service Account를 생성하고, 해당 계정에 권한을 부여하는 과정을 살펴본다.

---

### 14.1 Service Account 생성

```
gcloud iam service-accounts create web-sa \
--display-name="web service account"
```

각 부분의 의미는 다음과 같다.

* `gcloud iam service-accounts create`

  새 서비스 계정을 생성하는 명령이다.

* `web-sa`

  서비스 계정 이름의 기본 식별자다.

* `--display-name`

  콘솔에서 사람이 보기 쉬운 표시 이름이다.

이 명령을 실행하면 보통 다음과 비슷한 형태의 서비스 계정이 생성된다.

```
web-sa@[PROJECT_ID].iam.gserviceaccount.com
```

즉,

* 앞부분 `web-sa` 는 서비스 계정 이름

* 가운데 `[PROJECT_ID]` 는 프로젝트 ID

* 뒤의 `iam.gserviceaccount.com` 은 서비스 계정 도메인 형식

이 이메일 형태 자체가 Service Account Principal이라고 이해하면 된다.

---

### 14.2 Service Account 목록 조회

```
gcloud iam service-accounts list
```

이 명령은 현재 프로젝트에 존재하는 서비스 계정 목록을 조회한다.

확인할 항목은 다음과 같다.

* 이메일 주소

* 표시 이름

* 어떤 서비스 계정들이 생성되어 있는지

즉, 프로젝트 안에서 어떤 워크로드용 계정이 존재하는지를 확인하는 기본 명령이다.

---

### 14.3 Service Account에 권한 부여

예를 들어 Cloud Storage 객체 조회 권한을 부여하려면 다음과 같이 할 수 있다.

```
gcloud projects add-iam-policy-binding [PROJECT_ID] \
--member="serviceAccount:web-sa@[PROJECT_ID].iam.gserviceaccount.com" \
--role="roles/storage.objectViewer"
```

이 명령의 의미는 다음과 같다.

* `--member="serviceAccount:..."`

  사용자 계정이 아니라 서비스 계정을 Principal로 지정한다.

* `roles/storage.objectViewer`

  Cloud Storage 객체를 읽을 수 있는 역할이다.

이 명령은 Service Account에 “로그인 권한”을 주는 것이 아니다. 정확히는 **해당 Service Account가 프로젝트 범위에서 Cloud Storage 객체를 읽을 수 있도록 Role을 부여하는 것**이다.

---

## 15. 실습 5: VM에 Service Account 연결 개념 이해

이 단계는 다음 장의 Compute Engine과도 이어지지만, 여기서 개념을 먼저 정리해두면 이후 실습이 훨씬 자연스럽다.

흐름은 다음과 같다.

1. Service Account 생성

2. 필요한 Role 부여

3. VM 생성 시 해당 Service Account 지정

4. VM 내부 애플리케이션이 별도 키 없이 GCP API 접근

이 구조는 AWS에서

* IAM Role 생성

* 정책 부여

* EC2 인스턴스 프로파일 연결

* 애플리케이션이 임시 자격증명 사용

하는 흐름과 거의 같은 목적을 가진다.

즉, 워크로드가 사람 계정이 아니라 **자신에게 연결된 ID와 권한으로 클라우드 API를 호출한다**는 점이 핵심이다.

---

## 16. 최소 권한 원칙 적용 가이드

IAM에서 가장 중요한 운영 원칙은 **최소 권한 원칙(Least Privilege)** 이다.

최소 권한 원칙이란 사용자가 업무를 수행하는 데 필요한 만큼만 권한을 부여하고, 그 이상의 권한은 주지 않는 것을 의미한다.

---

### 16.1 잘못된 방식의 예

다음과 같은 방식은 편해 보일 수 있지만, 운영과 보안 측면에서 바람직하지 않다.

* 모든 사용자에게 Editor 부여

* 프로젝트마다 Owner를 다수 부여

* 서비스 계정에 Admin 권한 부여

* 테스트 편의 때문에 광범위 권한을 계속 유지

---

### 16.2 바람직한 방식

보다 적절한 방식은 다음과 같다.

* 읽기 전용 사용자는 Viewer 또는 세부 Viewer 역할 사용

* 운영자는 필요한 서비스별 Role만 부여

* 워크로드에는 Service Account 사용

* 가능하면 Basic Role 대신 Predefined Role 사용

* 꼭 필요한 경우에만 Custom Role 검토

즉, “일단 넓게 주고 나중에 줄이는 방식”보다, 처음부터 필요한 범위를 가능한 좁게 잡는 것이 바람직하다.

---

## 17. 자주 나오는 질문

### 질문 1. GCP에는 AWS의 IAM User 같은 개념이 없는가

AWS처럼 독립적인 IAM User 객체를 만들어 사용하는 감각과는 다르다. GCP에서는 Google 계정, 그룹, 서비스 계정 등이 Principal로 사용되고, 여기에 Role을 부여하는 방식으로 이해하면 된다.

---

### 질문 2. Viewer, Editor, Owner만 알면 충분한가

초기 개념 이해에는 도움이 된다. 하지만 실제 운영에서는 이 역할들이 너무 넓을 수 있다. 따라서 실무에서는 Predefined Role 중심으로 권한을 설계하는 것이 일반적이다.

---

### 질문 3. Service Account는 사람 계정인가

아니다. Service Account는 워크로드용 계정이다. 애플리케이션, VM, 서비스가 GCP 리소스에 접근할 때 사용하는 ID다.

---

### 질문 4. 권한은 Organization에 주는 것이 좋은가, Project에 주는 것이 좋은가

상황에 따라 다르다. 다만 교육과 초기 운영 이해 단계에서는 Project 단위부터 이해하는 것이 가장 직관적이다. 상위 계층 권한은 범위가 넓어지기 때문에 더 신중하게 설계해야 한다.

---

## 18. 장 요약

이 장에서는 GCP에서 리소스 구조와 권한 모델이 어떻게 연결되는지를 살펴보았다.

핵심 내용은 다음과 같다.

* GCP는 Organization → Folder → Project 구조로 리소스를 관리한다.

* IAM은 Principal, Role, Permission, Policy Binding 개념으로 이해할 수 있다.

* Permission은 개별 작업 단위이고, Role은 여러 Permission의 묶음이다.

* 실제 권한 부여는 Principal에 Role을 Binding하는 방식으로 이루어진다.

* Role은 Basic, Predefined, Custom으로 구분할 수 있다.

* Service Account는 워크로드가 사용하는 계정이다.

* 권한은 상위 계층에서 하위 계층으로 상속될 수 있다.

* 실제 운영에서는 최소 권한 원칙을 지키는 것이 매우 중요하다.

* AWS 경험자라면 IAM Role과 Service Account를 비교하여 이해하면 전체 구조를 더 쉽게 받아들일 수 있다.