import requests

url = 'http://127.0.0.1:5000/gc'

pm_test_data = {

}

r = requests.post(url, json=pm_test_data)
r.raise_for_status()
print(r.json())