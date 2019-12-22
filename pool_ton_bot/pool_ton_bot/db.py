from datetime import date

from mongoengine import *

import config


if config.DB_AUTH:
    connection = connect(
        host=('mongodb://{}:{}@{}/{}'.format(
            config.DB_LOGIN, config.DB_PASSWORD,
            config.DB_SERVER, config.DB_NAME)),
    )
else:
    connection = connect(config.DB_NAME)


class Users(Document):
    _id = IntField()
    username = StringField(default='')
    first_name = StringField(default='')
    last_name = StringField(default='')
    language = StringField(default='en')
    state = StringField(default='main_menu')
    active = BooleanField(default=True)
    pools = DictField(default={})
    started_at = IntField(default=0)
    updated_at = IntField(default=0)
    temp_pool = DictField(default={})


class Pools(Document):
    _id = StringField()
    creator = IntField()
    adrs = DictField()
    pool_type = StringField(default='public')
    participants = ListField(default=[])
    requests = ListField(default=[])
    description = StringField(default='default pool descritpion')


class Stats(Document):
    _id = DateTimeField(default=date.today())
    new_users = ListField(default=[])
    active_users = ListField(default=[])
