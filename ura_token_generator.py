import requests
import json

headers = {'AccessKey': '1fa1d271-92db-46ef-8191-f8f277cefce1'} #this is by default
url = 'https://www.ura.gov.sg/uraDataService/insertNewToken.action' #Resource URL
r = requests.get(url, headers=headers)
token = r.json()["Result"]
with open("/home/rlrh1996/mysite/ura_token.json", "w") as f:
    json.dump(token, f)