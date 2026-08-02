---
title: "CloudFormation ALB + AutoScaling 3Tier 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "AWS 아키텍처 설계(ARC)"]
is_public: true
draft: false
---

# CloudFormation ALB + AutoScaling 3Tier 실습

---

# 실습 목표

CloudFormation을 이용하여 **웹 서비스용 3-Tier Architecture를 자동으로 생성한다.**

다음 리소스를 자동으로 생성한다.

```
VPC
Public Subnet (2)
Private Subnet (2)
Internet Gateway
Route Table
Application Load Balancer
Target Group
Auto Scaling Group
EC2 Instance
```

---

# 1 CloudFormation Template 생성

파일 생성

```
three-tier-autoscaling.yaml
```

---

# 2 CloudFormation Template 작성

```
AWSTemplateFormatVersion: '2010-09-09'
Description: ALB + AutoScaling 3 Tier Architecture


Parameters:

  InstanceType:
    Type: String
    Default: t3.micro

  KeyName:
    Type: AWS::EC2::KeyPair::KeyName

  VpcCIDR:
    Type: String
    Default: 10.0.0.0/16


Resources:


# VPC

  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: !Ref VpcCIDR
      Tags:
        - Key: Name
          Value: 이니셜-vpc-cf


# Internet Gateway

  InternetGateway:
    Type: AWS::EC2::InternetGateway

  AttachGateway:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      VpcId: !Ref VPC
      InternetGatewayId: !Ref InternetGateway


# Public Subnet

  PublicSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.1.0/24
      AvailabilityZone: ap-northeast-2a

  PublicSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.2.0/24
      AvailabilityZone: ap-northeast-2c


# Security Group

  WebSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: web sg
      VpcId: !Ref VPC

      SecurityGroupIngress:

        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0


# Application Load Balancer

  LoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Name: 이니셜-alb-cf
      Subnets:
        - !Ref PublicSubnet1
        - !Ref PublicSubnet2
      SecurityGroups:
        - !Ref WebSecurityGroup


# Target Group

  TargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      Port: 80
      Protocol: HTTP
      VpcId: !Ref VPC


# Listener

  Listener:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      LoadBalancerArn: !Ref LoadBalancer
      Port: 80
      Protocol: HTTP

      DefaultActions:
        - Type: forward
          TargetGroupArn: !Ref TargetGroup


# Launch Template

  LaunchTemplate:

    Type: AWS::EC2::LaunchTemplate

    Properties:

      LaunchTemplateData:

        ImageId: ami-0bb8c0d387143b435

        InstanceType: !Ref InstanceType

        KeyName: !Ref KeyName

        SecurityGroupIds:
          - !Ref WebSecurityGroup

        UserData:

          Fn::Base64: |

            #!/bin/bash
            yum update -y
            yum install httpd -y
            systemctl start httpd
            systemctl enable httpd
            echo "CloudFormation Web Server" > /var/www/html/index


# Auto Scaling Group

  AutoScalingGroup:

    Type: AWS::AutoScaling::AutoScalingGroup

    Properties:

      VPCZoneIdentifier:

        - !Ref PublicSubnet1
        - !Ref PublicSubnet2

      LaunchTemplate:

        LaunchTemplateId: !Ref LaunchTemplate
        Version: !GetAtt LaunchTemplate.LatestVersionNumber

      MinSize: 1
      MaxSize: 4
      DesiredCapacity: 2

      TargetGroupARNs:
        - !Ref TargetGroup


Outputs:

  LoadBalancerDNS:

    Description: ALB DNS

    Value: !GetAtt LoadBalancer.DNSName
```

---

# 3 Stack 생성

콘솔 이동

```
CloudFormation
→ Stack 생성
```

Template 업로드

```
three-tier-autoscaling.yaml
```

Stack 이름

```
이니셜-stack-3tier
```

Parameter 입력

```
InstanceType : t3.micro
KeyName : 이니셜-key-ec2
```

Stack 생성

---

# 4 Stack 생성 확인

상태 확인

```
CREATE_COMPLETE
```

생성된 리소스

```
VPC
ALB
Auto Scaling
EC2
```

---

# 5 Web 서비스 접속

CloudFormation Output 확인

```
LoadBalancerDNS
```

브라우저 접속

```
http://ALB-DNS
```

웹 페이지 확인

```
CloudFormation Web Server
```

---

# 6 Auto Scaling 확인

EC2 콘솔 이동

```
Auto Scaling Group
```

확인 항목

```
Desired Capacity
Instances수업에서 설명하면 좋은 포인트
```

---

CloudFormation 장점

```
Infrastructure as Code
환경 재현 가능
자동 배포
대규모 인프라 관리
```

CloudFormation 흐름

```
Template 작성
        ↓
Stack 생성
        ↓
AWS 리소스 자동 생성
        ↓
Stack 삭제
        ↓
모든 리소스 자동 삭제
```

---