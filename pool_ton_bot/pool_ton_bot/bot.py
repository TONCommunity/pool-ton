import logging

import telegram

import config
from pool_ton_bot import db, routes

logging.basicConfig(
    format='[%(asctime)s.%(msecs)02d] %(message)s',
    datefmt='%H:%M:%S',
    level=logging.ERROR,
#    filename='errors.log'
)
logging.getLogger("requests").setLevel(logging.FATAL)
logging.getLogger("tornado").setLevel(logging.FATAL)
logger = logging.getLogger(__name__)


class MQBot(telegram.bot.Bot):
    def __init__(self, *args, is_queued_def=True, mqueue=None, **kwargs):
        super(MQBot, self).__init__(*args, **kwargs)
        self._is_messages_queued_default = is_queued_def
        self._msg_queue = mqueue

    def __del__(self):
        try:
            self._msg_queue.stop()
        except Exception as e:
            print(e)
        super(MQBot, self).__del__()

    @telegram.ext.messagequeue.queuedmessage
    def send_message(self, *args, **kwargs):
        try:
            return super(MQBot, self).send_message(*args, **kwargs)
        except telegram.error.Unauthorized:
            db.Users.objects(_id=args[0]).update_one(active=False)
            logger.warning(f'{args[0]} inactive now')
        except telegram.error.BadRequest as e:
            if 'Reply message not found' in e.message:
                del kwargs['reply_to_message_id']
                self.send_message(*args, **kwargs)
            if 'Chat not found' in e.message:
                db.Users.objects(_id=args[0]).update_one(
                    active=False
                )
                logger.warning(f'User {args[0]} inactive now')
            else:
                logger.warning(f'Update "{kwargs}" caused error "{e}"')
        except Exception as e:
            logger.warning(f'Update "{kwargs}" caused error "{e}"')

    @telegram.ext.messagequeue.queuedmessage
    def edit_message_text(self, *args, **kwargs):
        try:
            return super(MQBot, self).edit_message_text(*args, **kwargs)
        except telegram.error.Unauthorized:
            db.Users.objects(_id=args[0]).update_one(set__active=False)
        except telegram.error.BadRequest as e:
            if 'Message is not modified: ' not in e.message:
                logger.warning(f'Update "{kwargs}" caused error "{e}"')
        except Exception as e:
            logger.warning(f'Update "{kwargs}" caused error "{e}"')


class Bot:
    def __init__(self):
        message_queue = telegram.ext.messagequeue.MessageQueue(
            all_burst_limit=29,
            all_time_limit_ms=1017
        )
        request = telegram.bot.Request(con_pool_size=26)
        self.updater = telegram.ext.Updater(
            bot=MQBot(config.BOT_TOKEN, request=request, mqueue=message_queue),
            workers=24,
            request_kwargs={'read_timeout': 5, 'connect_timeout': 5},
            use_context=True
        )

    def __del__(self):
        self.updater.stop()

    def add_jobs(self):
        pass

    def add_handlers(self):
        self.updater.dispatcher.add_handler(
            telegram.ext.MessageHandler(
                telegram.ext.Filters.text,
                routes.message  # добавить еще фильтры
            )
        )
        self.updater.dispatcher.add_handler(
            telegram.ext.CommandHandler(
                config.SUPPORTED_COMMANDS,
                routes.command
            )
        )
        self.updater.dispatcher.add_handler(
            telegram.ext.CallbackQueryHandler(
                routes.callback_query
            )
        )
        self.updater.dispatcher.add_error_handler(
            routes.error
        )

    def start(self):
        if config.WEBHOOK:
            self.updater.start_webhook(
                listen=config.WEBHOOK_IP,
                port=config.WEBHOOK_PORT,
                url_path=config.BOT_TOKEN,
                key=config.WEBHOOK_SSL_PRIVATE,
                cert=config.WEBHOOK_SSL_PUB,
                webhook_url=config.WEBHOOK_URL
            )
        else:
            self.updater.start_polling()
        self.updater.idle()
