import urllib
import json
import webapp2
import logging

import database
import groupme_api as groupme
import bot_manager as chatbot
import commands
import constants


class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        self.response.write("""<table border="1px" style="font-family: sans-serif">""")

        groups = load_groups()

        for group in groups:
            self.response.write("""<tr><td style="vertical-align:middle"><p style="padding:10px">""" + group[1] +
                                """</p></td><td style="vertical-align:middle">""")

            self.response.write("""<form style="display:inline-block; vertical-align:middle"
            action="/addbot?group_id=%s" method="post"> <div><input type="submit" value="Add Bot">
            </div></form></td></tr>""" % group[0])

        self.response.write("</table>")

        logging.info('GET received')


class PostHandler(webapp2.RequestHandler):
    def post(self):
        json_string = self.request.body
        data = json.loads(json_string)

        if data['sender_type'] == 'user':
            user_id = data['user_id']
            db = database.Database()
            db.incr_user_stats(user_id, data['name'], data['group_id'])

            user_level = db.fetch_user_level(user_id)

            if (not db.fetch_active(data['group_id'])) and user_level < constants.PERMISSION_LEVEL_ADMIN:
                logging.info('Received POST but group is inactive')
                return

            bot_id = db.fetch_bot_id_from_group(data['group_id'])
            message = data['text']

            if message.startswith('/'):
                cmd_result = commands.handle_command_message(message, bot_id, user_level)
                if cmd_result is not None:
                    groupme.post_message(cmd_result, bot_id)
            
            logging.info('POST received')


class AddBot(webapp2.RequestHandler):
    def post(self):
        print "submit: " + self.request.get('group_id')
        chatbot.create_bot(self.request.get('group_id'))
        self.redirect('./')


app = webapp2.WSGIApplication([
    ('/', MainPage), ('/post', PostHandler), ('/addbot', AddBot)
], debug=True)


def load_groups():
    url = 'https://api.groupme.com/v3/groups?token=' + constants.GROUPME_API_KEY
    response = urllib.urlopen(url)
    data = json.load(response)

    groups = data['response']

    result = []

    for group in groups:
        result.append((group['group_id'], group['name']))

    return result

