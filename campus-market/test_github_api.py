import requests
url = 'https://api.github.com/repos/sique1744-cyber/gdufs-exchange'
headers = {
    'Authorization': 'token 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',
    'Accept': 'application/vnd.github+json'
}
response = requests.get(url, headers=headers, timeout=20)
print(response.status_code)
print(response.text)
