---
title: "Remote VPN 구성 실습"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "온프레미스 ICT 인프라구조", "VPN(Virtual Private Network)", "Remote VPN"]
is_public: true
draft: false
---

# Remote VPN 구성 실습

[![](Remote%20VPN%20%EA%B5%AC%EC%84%B1%20%EC%8B%A4%EC%8A%B5/image.png)](Remote%20VPN%20%EA%B5%AC%EC%84%B1%20%EC%8B%A4%EC%8A%B5/image.png)

### Cisco 7200라우터에 Remote VPN 서버 설정

```
aaa new-model
aaa authentication login AUTH local
aaa authorization network NET local 
username cisco password 0 cisco

crypto isakmp policy 1
 encryption aes
 hash sha 
 authentication pre-share
 group 2
 lifetime 3600
crypto isakmp keepalive 10

crypto isakmp client configuration group RA
 key cisco
 domain cisco.com
 pool POOL
 acl split
 save-password
 netmask 255.255.255.0

crypto isakmp profile ra-profile
   match identity group RA
   client authentication list AUTH
   isakmp authorization list NET
   client configuration address respond
   client configuration group RA
   virtual-template 1

crypto ipsec transform-set ra-ts esp-aes esp-sha-hmac 
 mode tunnel

crypto ipsec profile ipsecprof
 set security-association lifetime kilobytes disable
 set transform-set ra-ts 
 set isakmp-profile ra-profile

interface s1/0
 ip address 203.113.0.1 255.255.255.0
 no shutdown
!
interface f0/0
 description LAN
 ip address 192.168.10.254 255.255.255.0
 no shutdown

interface Virtual-Template1 type tunnel
 ip unnumbered f0/0
 tunnel source s1/0
 tunnel mode ipsec ipv4
 tunnel protection ipsec profile ipsecprof

ip local pool POOL 192.168.10.0 192.168.10.255
ip access-list extended split
 permit ip 192.168.10.0 0.0.0.255 any
```

### 우분투에 StrongSwan 설치하기

```
sudo apt update
sudo apt install strongswan strongswan-pki libcharon-extra-plugins
```

### 우분투에서 StrongSwan을 이용해서 접속하기 위한 설정

```
# /etc/IPsec.conf
version 2
config setup
        strictcrlpolicy=no
        charondebug="ike 4, knl 4, cfg 2"    #useful debugs

conn %default
        ikelifetime=1440m
        keylife=60m
        rekeymargin=3m
        keyingtries=1
        keyexchange=ikev1
        authby=xauthpsk

conn "ezvpn"
        keyexchange=ikev1
        ikelifetime=1440m
        keylife=60m
        aggressive=yes
        ike=aes-sha1-modp1024     #Phase1 parameters
        esp=aes-sha1              #Phase2 parameters
        xauth=client              #Xauth client mode 
        left=0.0.0.0              #local IP used to connect to IOS
        leftid=RA                 #IKEID (group name) used for IOS
        leftsourceip=%config      #apply received IP    
        leftauth=psk
        rightauth=psk
        leftauth2=xauth           #use PSK for group RA and Xauth for user cisco
        right=203.113.0.1         #gateway (IOS) IP 
        rightsubnet=192.168.10.0/24
        xauth_identity=cisco      #identity for Xauth, password in ipsec.secrets
        auto=add

#/etc/IPsec.secrets
203.113.0.1 : PSK "cisco"
cisco : XAUTH "cisco"
```

```
sudo ipsec stop
sudo ipsec start
sudo ipsec up ezvpn
```