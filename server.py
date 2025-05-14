import scratchattach as sa
import requests as r
import json
import base64
import random

GITHUB_API_KEY = os.getenv('GH_KEY')
REPO_OWNER = "kRxZykRxZy"
REPO_NAME = "Buildr-Database"
BRANCH = "main"
HEADERS = {
    "Authorization": f"token {GITHUB_API_KEY}",
    "Accept": "application/vnd.github+json"
}

def curl(db):
    return f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{db}'

def fetch(url):
    res = r.get(url, headers=HEADERS)
    return res.json()

def send(url, data):
    res = r.put(url, json=data, headers=HEADERS)
    return res.json()

def next_number(user):
    i = 0
    while True:
        i += 1
        url = curl(f"{user}/{i}.json")
        if 'content' in fetch(url):
            continue
        return i

def create_or_update_file(file_path, content, commit_message):
    response = fetch(curl(file_path))

    payload = {
        "message": commit_message,
        "content": base64.b64encode(content.encode()).decode(),
        "branch": BRANCH
    }

    if response.get("message") != "Not Found":
        payload["sha"] = response.get("sha")

    send(curl(file_path), payload)

session = sa.login('Dev-Server', os.getenv('SCRATCH_PS'))
cloud = session.connect_cloud("1174866960")
client = cloud.requests()

@client.request
def data(user):
    response = fetch(curl(f'{user}/data.json'))

    if 'content' in response:
        decoded_content = base64.b64decode(response['content']).decode()
        file_content = json.loads(decoded_content)
    else:
        file_content = {
            "username": user,
            "projects": 0,
            "followers": "",
            "following": "",
            "new-notifications": 0
        }
        create_or_update_file(f"{user}/data.json", json.dumps(file_content), "New User Creation")

        notif_data = {
            "notifications": "Welcome To Buildr, Here You Can Make And Play Online Platformers With Your Friends And Family!"
        }
        create_or_update_file(f'{user}/notifications.json', json.dumps(notif_data), "New Notifications")

        file_content["new-notifications"] += 1
        create_or_update_file(f'{user}/data.json', json.dumps(file_content), "Updated Notifications Count")

    return list(file_content.values())

@client.request
def notifications(user):
    res = fetch(curl(f'{user}/notifications.json'))
    if 'content' in res:
        decoded_content = base64.b64decode(res['content']).decode()
        notif_content = json.loads(decoded_content)

        res = fetch(curl(f'{user}/data.json'))
        decoded_data = base64.b64decode(res['content']).decode()
        user_data = json.loads(decoded_data)
        user_data["new-notifications"] = 0
        create_or_update_file(f'{user}/data.json', json.dumps(user_data), "Cleared Notifications Count")
        return list(notif_content.values())
    return "Error Occurred"

@client.request
def create(user, code):
    random_number = random.randint(100, 999)
    file_data = {
        "title": f"Untitled Project - {random_number}",
        "visibility": "Unshared",
        "code": code,
        "views": 0,
        "likes": 0,
        "favourites": 0
    }
    filename = '{user}/{next_number(user)}.json'
    create_or_update_file(filename, json.dumps(file_data), "New Project Created")
    return

@client.request
def update(user, code, name, id):
    res = fetch(curl(f'{user}/{id}.json'))

    if 'content' in res:
        decoded_content = base64.b64decode(res['content']).decode()
        file_content = json.loads(decoded_content)
        
    random_number = random.randint(100, 999)
    file_data = {
        "title": file_content["title"],
        "visibility": file_content["visibility"],
        "code": code,
        "views": file_content["views"],
        "likes": file_content["likes"], 
        "favourites": file_content["favourites"]
    }
    
    filename = f'{user}/{id}.json'
    create_or_update_file(filename, json.dumps(file_data), "New Project Updated")
    return "updated"
    
@client.request
def share(user, code, name, id):
    res = fetch(curl(f'{user}/{id}.json'))

    if 'content' in res:
        decoded_content = base64.b64decode(res['content']).decode()
        file_content = json.loads(decoded_content)

        if file_content.get("code") == code:
            file_content["title"] = name
            file_content["visibility"] = "Shared"
            file_content["views"] = file_content.get("views", 0) + 1
            file_content["likes"] = file_content.get("likes", 0)
            file_content["favourites"] = file_content.get("favourites", 0)
            create_or_update_file(f'{user}/{id}.json', json.dumps(file_content), "Project Shared")
            return "Project shared."
    return "Failed to share."

client.start()
