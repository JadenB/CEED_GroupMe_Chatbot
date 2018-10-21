import MySQLdb
import os

CLOUDSQL_CONNECTION_NAME = os.environ.get('CLOUDSQL_CONNECTION_NAME')
CLOUDSQL_USER = os.environ.get('CLOUDSQL_USER')
CLOUDSQL_PASSWORD = os.environ.get('CLOUDSQL_PASSWORD')


class Database:
    def __init__(self):
        # When deployed to App Engine, the `SERVER_SOFTWARE` environment variable
        # will be set to 'Google App Engine/version'.
        if os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine/'):
            # Connect using the unix socket located at
            # /cloudsql/cloudsql-connection-name.
            cloudsql_unix_socket = os.path.join(
                '/cloudsql', CLOUDSQL_CONNECTION_NAME)

            self.db = MySQLdb.connect(
                unix_socket=cloudsql_unix_socket,
                user=CLOUDSQL_USER,
                passwd=CLOUDSQL_PASSWORD,
                db='data',
                charset='utf8mb4',
                use_unicode=True)

        # If the unix socket is unavailable, then try to connect using TCP. This
        # will work if you're running a local MySQL server or using the Cloud SQL
        # proxy, for example:
        #
        #   $ cloud_sql_proxy -instances=your-connection-name=tcp:3306
        #
        else:
            self.db = MySQLdb.connect(
                host='127.0.0.1', user=CLOUDSQL_USER, passwd=CLOUDSQL_PASSWORD, db='data',
                charset='utf8mb4',
                use_unicode=True)

    def fetch_bot_id_from_group(self, group_id):
        c = self.db.cursor()
        c.execute("""SELECT botID FROM groups WHERE groupID = %s""", (group_id,))
        if not c.rowcount:
            return None
        return c.fetchone()[0]

    def register_bot(self, group_id, group_name, bot_id):
        c = self.db.cursor()
        c.execute("""INSERT INTO groups (groupID, groupName, botID) VALUES (%s, %s, %s)""",
                  (str(group_id), str(group_name), str(bot_id)))
        self.db.commit()

    def register_command(self, command, response, image_url):
        """

        :rtype: bool
        """
        c = self.db.cursor()
        c.execute("""SELECT 1 FROM commands WHERE command = %s""", (command,))
        if c.rowcount > 0:
            return False

        if image_url is None:
            c.execute("""INSERT INTO commands (command, type, response, deletable) VALUES (%s, %s, %s, 1)""",
                      (command, 0, response))
        else:
            c.execute("""INSERT INTO commands (command, type, response, image, deletable) VALUES (%s, %s, %s, %s, 1)""",
                      (command, 1, response, image_url))
        self.db.commit()
        return True

    def delete_command(self, command):
        c = self.db.cursor()
        c.execute("""SELECT 1 FROM commands WHERE command = %s""", (command,))
        if not c.rowcount:
            return False

        c.execute("""DELETE FROM commands WHERE command = %s""", (command,))
        self.db.commit()
        return True

    def fetch_command_type(self, command):
        c = self.db.cursor()
        c.execute("""SELECT type FROM commands WHERE command = %s""", (command,))
        if not c.rowcount:
            return None
        else:
            return c.fetchone()[0]

    def fetch_command_level_required(self, command):
        c = self.db.cursor()
        c.execute("""SELECT levelRequired FROM commands WHERE command = %s""", (command,))
        if not c.rowcount:
            return 0
        else:
            return c.fetchone()[0]

    def fetch_command_data(self, command):
        # type: (str) -> [str]
        c = self.db.cursor()
        c.execute("""SELECT response, image FROM commands WHERE command = %s""", (command,))
        return c.fetchone()

    def incr_command_uses(self, command):
        c = self.db.cursor()
        c.execute("""UPDATE commands SET uses = uses + 1 WHERE command = %s""", (command,))
        self.db.commit()

    def update_command_desc(self, command, desc):
        c = self.db.cursor()
        c.execute("""SELECT 1 FROM commands WHERE command = %s""", (command,))
        if not c.rowcount:
            return False

        c = self.db.cursor()
        c.execute("""UPDATE commands SET description = %s WHERE command = %s""", (desc, command))
        self.db.commit()
        return True

    def fetch_command_list(self, result_count, page):
        offset = (page - 1) * result_count
        print offset
        c = self.db.cursor()
        c.execute("""SELECT command, description FROM commands ORDER BY command ASC LIMIT %s OFFSET %s"""
                  % (str(result_count), str(offset)))

        return c.fetchall()

    def incr_user_stats(self, user_id, user_name, group_id):
        c = self.db.cursor()
        c.execute("""SELECT 1 FROM users WHERE userID = %s AND groupID = %s""", (user_id, group_id))
        if not c.rowcount:
            c.execute("""INSERT INTO users (userGroup, userID, userName, groupID, score) VALUES (%s, %s, %s, %s, 1)""",
                      (user_id + group_id, user_id, user_name, group_id))
        else:
            c.execute("""UPDATE users SET score = score + 1, userName = %s WHERE userGroup = %s""",
                      (user_name, user_id + group_id))

        self.db.commit()
        return True

    def fetch_user_level(self, user_id):
        c = self.db.cursor()
        c.execute("""SELECT level FROM permissions WHERE userID = %s""", (user_id,))
        if not c.rowcount:
            return 0
        else:
            return c.fetchone()[0]

    def fetch_group_id_from_bot_id(self, bot_id):
        c = self.db.cursor()
        c.execute("""SELECT groupID FROM groups WHERE botID = %s""", (bot_id,))
        return c.fetchone()[0]

    def fetch_user_leaderboard(self, bot_id):
        group_id = self.fetch_group_id_from_bot_id(bot_id)

        c = self.db.cursor()
        c.execute("""SELECT userName, score FROM users WHERE groupID = %s ORDER BY score DESC LIMIT 10""", (group_id,))

        return c.fetchall()

    def check_command_can_be_deleted(self, command):
        c = self.db.cursor()
        c.execute("""SELECT deletable FROM commands WHERE command = %s""", (command,))

        if not c.rowcount:
            return True
        return c.fetchone()[0]

    def fetch_group_id_from_group_name(self, group_name):
        c = self.db.cursor()
        c.execute("""SELECT groupID FROM groups WHERE groupName = %s""", (group_name,))

        if not c.rowcount:
            return None
        return c.fetchone()[0]

    def deactivate_group(self, group_id):
        c = self.db.cursor()
        c.execute("""UPDATE groups SET active = FALSE WHERE groupID = %s""", (group_id,))
        self.db.commit()

    def fetch_active(self, group_id):
        c = self.db.cursor()
        c.execute("""SELECT groupID FROM groups WHERE active = TRUE AND groupID = %s""", (group_id,))

        if not c.rowcount:
            return False
        else:
            return True

    def activate_group(self, group_id):
        c = self.db.cursor()
        c.execute("""UPDATE groups SET active = TRUE WHERE groupID = %s""", (group_id,))
        self.db.commit()
