import requests

url = "https://www.google.com/about/careers/applications/jobs/results/"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)

html = response.text

print(html)