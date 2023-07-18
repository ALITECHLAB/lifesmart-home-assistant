
import pprint
import ruamel.yaml
import json
import requests
import time
class lifesmart :
    
    EMAIL =     "ENTER_YOUR_LIFESMART_ACOUNT_EMAIL"
    PASSWORD =  "LIFESMART_ACOUNT_PASSWORD"
    APP_KEY =   "GET_FROM_LIFESMART_WEBSITE_APP_KEY"
    APP_TOKEN = "GET_FROM_LIFESMART_WEBSITE_APP_TOKEN"

    # http://www.ilifesmart.com/open/login#/open/login








    USER_ID =   ""
    TOKEN =     ""
    RGN =       ""


    yaml = ruamel.yaml.YAML()
    yaml.preserve_quotes = True
    yaml.explicit_start = True
    
    def __init__(self):
        print("init")




    def get_token(self):

        url = "https://api.ilifesmart.com/app/auth.login"

        payload = json.dumps({
        # accuont user email  
        "uid": self.EMAIL,
        # account password
        "pwd":self.PASSWORD,
        # app-key from www.ilifesmar.com/open
        "appkey": self.APP_KEY
        })
        headers = {
        'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        time.sleep(3) # 10 second delay
        self.TOKEN = response.json()["token"]
        self.USER_ID = response.json()["userid"]
        self.RGN = response.json()["rgn"]
        print("HHHHHHHHHHHHH")
        print(self.TOKEN)
        print(response.text)
        return response.text

    def get_user_token(self):
        """ function to request user token """
        url = "https://api.ilifesmart.com/app/auth.do_auth"

        payload = json.dumps({
        # user-id from lifesmart-app or from response token tool
        "userid": self.USER_ID,
        # from response lifesmart-tool-get-token.py
        "token": self.TOKEN,
        # from website
        "appkey":self.APP_KEY,
        #  from response lifesmart-tool-get-token.py
        "rgn": self.RGN
        })
        headers = {
        'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        time.sleep(3)
        print(response.text)
        print(self.USER_ID)
        print(self.TOKEN)
        print(self.APP_KEY)
        print(self.RGN)
        self.USER_TOKEN = response.json()["usertoken"]
        print("HHHHHHHHHHHHH")

        return response

    def read_yaml(self):
        """ A function to read YAML file"""
        with open('data.yml') as f:
            config = self.yaml.load(f)
    
        return config
    
    def write_yaml(data):
        """ A function to write YAML file"""
        with open('data.yml', 'W') as f:
           self.yaml.dump(data, f)
            
    def fill_data(self):
        
        with open('template.yml') as f:
            doc = self.yaml.load(f)

        doc["lifesmart"]["appkey"] = self.APP_KEY
        doc["lifesmart"]["apptoken"] = self.APP_TOKEN
        doc["lifesmart"]["usertoken"] = self.USER_TOKEN
        doc["lifesmart"]["userid"] = self.USER_ID
        with open('data.yml', 'w') as f:
            self.yaml.dump(doc, f) 
            
        
if __name__ == "__main__":
    
    # read the config yaml
    life = lifesmart()
    my_config = life.read_yaml()
    life.get_token()
    life.get_user_token()
    life.fill_data()
    pprint.pprint(my_config)
    
 
