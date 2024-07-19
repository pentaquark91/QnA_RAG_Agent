import requests
import json

url = 'http://localhost:5000/process'
openai_api_key = '####################################################'
slack_token = 'xoxb-7433210015799-7470589241248-RgBS0LRzpeDbjQNWeegOvYv6'
slack_channel = '#general'
questions = [
    "What is the name of the company?",
    "Who is the CEO of the company?",
    "What is their vacation policy?",
    "What is the termination policy?",
    "When is the next solar eclipse?"
]

files = {
    'pdf': open('handbook.pdf', 'rb'),
    'openai_api_key': (None, openai_api_key),
    'slack_token': (None, slack_token),
    'slack_channel': (None, slack_channel),
    'questions': (None, json.dumps(questions))
}

response = requests.post(url, files=files)

try:
    print(response.json())
except requests.exceptions.JSONDecodeError:
    print("Response content is not valid JSON")
    print(response.text)
