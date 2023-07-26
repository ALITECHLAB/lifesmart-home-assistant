# lifesmart-home-assistant
how to setup lifesmart-integration


## System Info 

    Home Assistant 2023.7.2

    Supervisor 2023.07.1

    Operating System 10.3 

    Frontend 20230705.1 - latest


Added the following into configuration.yaml：

```
lifesmart:
  appkey: "your_appkey" 
  apptoken: "your_apptoken"
  usertoken: "your_usertoken" 
  userid: "your_userid"
  exclude:
    - "0011" # fill any value to omit
  exclude_agt:
    - "XXXX" #exlucde all devices in these smart stations
  ai_include_agt:
    - "XXXXXXXXX" # agt to be included for AI or Scene as a switch, fill any value to omit
  ai_include_me:
    - "xxxx" # me to be included for AI or Scene as a switch, fill any value to omit
  
```



## call service for Lifesmart: send_keys
```
me: "7725"
agt: AzXCXXAgvaBEDSEU1Xwz__w
ai: AI_IR_7725_1670533904
category: custom
brand: custom
keys: "[\"CS_1\"]"
  
```
