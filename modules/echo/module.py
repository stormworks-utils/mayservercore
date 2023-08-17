import requests
def handler(datatype, message):
    if datatype=='chat':
        target=message['webhook']
        name=message['name']
        content=message['message']

        data = {"username": name, "content": content}
        requests.post(target, data)

    return {}