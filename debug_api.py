import requests
import json

# 测试API响应格式
test_data = {"text": "测试文本\n# 标题", "target_format": "markdown"}
response = requests.post(
    'http://127.0.0.1:5000/api/convert-format',
    headers={'Content-Type': 'application/json'},
    json=test_data,
    timeout=5
)

print("Status Code:", response.status_code)
print("Response:", response.text)
if response.status_code == 200:
    data = response.json()
    print("Keys:", list(data.keys()))