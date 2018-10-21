from google.appengine.api import urlfetch
import json

import database
import constants


def create_bot(group_id):
    data = """{
        "bot" : {
            "name" : "Sherrytron 3000",
            "group_id" : %s,
            "callback_url" : %s,
            "avatar_url" : "https://i.groupme.com/600x600.jpeg.1fa4c61e57b543559e68529072ca757b"
        }
    }""" % (constants.CALLBACK_URL, group_id)

    response = urlfetch.fetch('https://api.groupme.com/v3/bots?token=' + constants.GROUPME_API_KEY,
                   data, urlfetch.POST, {'Content-Type': 'application/json'})

    content = json.loads(response.content)
    print response.content

    if content['meta']['code'] == 201:
        bot_info = content['response']['bot']
        db = database.Database()
        db.register_bot(bot_info['group_id'], bot_info['group_name'], bot_info['bot_id'])
    else:
        print 'bot already exists'

