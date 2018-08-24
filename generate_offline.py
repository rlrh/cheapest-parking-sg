import requests

url = 'https://www.carparkssg.com/offline'
output_file = "/home/rlrh1996/mysite/offline.html"
output_file2 = "/home/rlrh1996/mysite/static/offline.html"
r = requests.get(url, allow_redirects=True)
with open(output_file, 'wb') as f:
    f.write(r.content)
with open(output_file2, 'wb') as f:
    f.write(r.content)