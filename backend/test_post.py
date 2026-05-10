import requests, tempfile
f = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
f.write(b'fakeimage')
f.flush()
resp = requests.post('http://127.0.0.1:8000/api/v1/analyze-trademark', files={'file': open(f.name,'rb')}, data={'top_k': 3, 'name': 'tmp'})
print(resp.status_code)
print(resp.text)
