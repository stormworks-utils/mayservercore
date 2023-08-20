import requests
import json

with open('discord_chat_relay.json') as config:
    conf=json.load(config)

webhook=conf.get("webhook") or None
def handler(datatype, message):
    if datatype=='chat':
        if webhook:
            name=message['name']
            content=message['message']

            data = {"username": name, "content": content}
            requests.post(webhook, data)

    return {}