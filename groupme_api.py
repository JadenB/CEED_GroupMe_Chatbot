import urllib2
import json

import constants


def post_message(message, bot_id):
    # type: (str, str) -> null
    payload = {
        'bot_id': bot_id,
        'text': message
    }

    data = json.dumps(payload, encoding='utf8')

    request = urllib2.Request("https://api.groupme.com/v3/bots/post", data, {'Content-Type': 'application/json'})
    f = urllib2.urlopen(request)
    f.close()


def post_image(message, img_url, bot_id):
    # type: (str, str, str) -> null
    groupme_img_url = upload_image(img_url)

    payload = {
        'bot_id': bot_id,
        'text': message,
        'picture_url': groupme_img_url
    }

    data = json.dumps(payload, encoding='utf8')

    request = urllib2.Request("https://api.groupme.com/v3/bots/post", data, {'Content-Type': 'application/json'})
    f = urllib2.urlopen(request)
    f.close()


def upload_image(img_url):
    # type: (str) -> str
    try:
        image = urllib2.urlopen(img_url).read()
    except Exception:
        return None

    request = urllib2.Request('https://image.groupme.com/pictures', image)
    request.add_header('Content-Type', 'image/jpeg')
    request.add_header('X-Access-Token', constants.GROUPME_API_KEY)

    response = urllib2.urlopen(request)

    data = json.load(response)
    try:
        return data['payload']['picture_url']
    except Exception:
        return None
