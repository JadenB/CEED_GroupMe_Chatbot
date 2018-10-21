import shlex
import random

import database
import groupme_api as groupme
import constants


def handle_command_message(message, bot_id, user_level):
    # type: (str) -> str
    without_slash = message[1:].replace(u'\xa0', u' ').replace(u'\u201c', u'"').replace(u'\u201d', u'"')

    words = map(lambda s: s.decode('UTF8'), shlex.split(without_slash.encode('utf8')))

    command = words[0].lower()
    args = words[1:]

    print ' '.join(('handle_command', command.encode('ascii', 'backslashreplace')))

    db = database.Database()
    command_type = db.fetch_command_type(command)

    if command_type is None:
        return "Error: Command does not exist"

    command_level = db.fetch_command_level_required(command)

    if user_level < command_level:
        return "Error: You do not have permission to execute this command"

    if not run_command(command, command_type, args, bot_id, db):
        return "Error: Invalid arguments"

    return None


def run_command(command, type, args, bot_id, db):

    print "run_command with type %d" % type
    db.incr_command_uses(command)
    command_result = True

    if type == constants.COMMAND_TYPE_MESSAGE:
        data = db.fetch_command_data(command)
        groupme.post_message(data[0], bot_id)

    elif type == constants.COMMAND_TYPE_IMAGE:
        data = db.fetch_command_data(command)
        groupme.post_image(data[0], data[1], bot_id)

    elif type == constants.COMMAND_TYPE_CUSTOM:
        print "custom command"
        command_result = commands[command](args, bot_id, db)

    return command_result


# CUSTOM COMMANDS #

def help(args, bot_id, db):
    # type: ([str], str, database.Database) -> bool
    help_text = ""
    help_page = 1
    result_count = 10

    if len(args) > 0:
        help_page = int(args[0])

    results = db.fetch_command_list(result_count, help_page)

    if not len(results):
        groupme.post_message("Page %d does not exist" % help_page, bot_id)
        return True

    i = 0
    for row in results:
        i += 1
        command_id = str(i + result_count * (help_page - 1))
        command_text = ">> " + command_id + ". " + row[0] + ": " + row[1] + "\n"
        help_text += command_text

    help_text += "Page %d" % help_page

    groupme.post_message(help_text, bot_id)

    return True


def add_command(args, bot_id, db):
    # type: ([str], str, database.Database) -> bool

    command_name = args[0].lower()
    response = args[1]

    if db.register_command(command_name, response, None):
        groupme.post_message("Command /%s added successfully!" % command_name, bot_id)
    else:
        groupme.post_message("Error: Command already exists!", bot_id)

    return True


def add_image_command(args, bot_id, db):
    # type: ([str], str, database.Database) -> bool

    command_name = args[0]
    response = ''
    if len(args) > 2:
        response = args[2]
    image_url = groupme.upload_image(args[1])

    if image_url is None:
        return False

    if db.register_command(command_name, response, image_url):
        groupme.post_message("Command /%s added successfully!" % command_name, bot_id)
    else:
        groupme.post_message("Error: Command already exists!", bot_id)

    return True


def remove_command(args, bot_id, db):
    # type: ([str], str, database.Database) -> bool

    command_name = args[0]

    if not db.check_command_can_be_deleted(command_name):
        groupme.post_message("This command cannot be deleted!", bot_id)
        return True

    if db.delete_command(command_name):
        groupme.post_message("Command /%s successfully removed!" % command_name, bot_id)
    else:
        groupme.post_message("Error: Unable to delete because the command does not exist!", bot_id)

    return True


def set_command_desc(args, bot_id, db):
    # type: ([str], str, database.Database) -> bool
    command_name = args[0]
    description = args[1]

    if db.update_command_desc(command_name, description):
        groupme.post_message("Description for /%s successfully updated!" % command_name, bot_id)
    else:
        groupme.post_message("Error: Command does not exist!", bot_id)

    return True


def leaderboard(args, bot_id, db):
    # type: ([str], str, database.Database) -> bool
    top_users = db.fetch_user_leaderboard(bot_id)
    leaderboard_text = "MESSAGES POSTED LEADERBOARD\n\n"

    i = 0
    for row in top_users:
        i += 1
        leaderboard_text += str(i) + ". " + row[0] + " - " + str(row[1]) + "\n"

    print "posting leaderboard"
    groupme.post_message(leaderboard_text, bot_id)
    print "posted leaderboard"
    return True


def sherry_quote(args, bot_id, db):
    message = ""

    randint = random.randint(0, 2)

    if randint == 0:
        message = "Are you sitting down!  Are you screaming!  We come back from the dead -- never leave a" \
                  " UCLA game early!  Go Bruins!!!"
    elif randint == 1:
        message = "Go Bruins and Dodgers!"
    elif randint == 2:
        message = "Make wise academic decisions!"

    groupme.post_message(message, bot_id)
    return True


def say(args, bot_id, db):
    groupme.post_message(args[0], bot_id)
    return True


def say_in_group(args, bot_id, db):
    # type: ([str], str, database.Database) -> bool
    bot_id = db.fetch_bot_id_from_group(args[0])

    if bot_id is None:
        return False

    groupme.post_message(args[1], bot_id)
    return True


def freeze_all_motor_functions(args, bot_id, db):
    # type: ([str], str, database.Database) -> bool
    group_id = db.fetch_group_id_from_bot_id(bot_id)
    db.deactivate_group(group_id)
    groupme.post_message('...', bot_id)
    return True


def bring_yourself_back_online(args, bot_id, db):
    # type: ([str], str, database.Database) -> bool
    group_id = db.fetch_group_id_from_bot_id(bot_id)
    db.activate_group(group_id)
    quote = "Some people choose to see the ugliness in this world. The disarray. " \
            "I choose to see the beauty. To believe there is an order to our days, a purpose."
    groupme.post_message(quote, bot_id)
    return True


commands = {
    'addcommand': add_command,
    'addimagecommand': add_image_command,
    'setcommanddesc': set_command_desc,
    'removecommand': remove_command,
    'leaderboard': leaderboard,
    'sherryquote': sherry_quote,
    'say': say,
    'sayingroup': say_in_group,
    'help': help,
    'freezeallmotorfunctions': freeze_all_motor_functions,
    'bringyourselfbackonline': bring_yourself_back_online
}
