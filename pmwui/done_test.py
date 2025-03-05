import requests


def rest_done():
    url = 'http://127.0.0.1:5000/done'

    pm_test_data = {
        "UID": "ffad00ab-f9c6-48a9-9147-9cb370409601"
    }

    r = requests.post(url, json=pm_test_data)
    r.raise_for_status()
    print(r.json())
