import requests
url='http://127.0.0.1:8001/api/v1/upload'
try:
    r = requests.options(url, timeout=5)
    print('Status:', r.status_code)
    for k,v in r.headers.items():
        print(k+':', v)
except Exception as e:
    print('ERROR', e)
