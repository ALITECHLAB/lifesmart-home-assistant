# lifesmart-home-assistant
how to setup lifesmart-integration

[![Watch the video](https://img.youtube.com/vi/s3JuIvKdzmE/maxresdefault.jpg)](https://youtu.be/s3JuIvKdzmE)

## Watch the video https://www.youtube.com/watch?v=s3JuIvKdzmE


## System Info 

    Home Assistant 2023.8.1
    Supervisor 2023.07.1
    Operating System 10.4
    Frontend 20230802.0 - latest


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
