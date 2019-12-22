import traceback

import telegram.ext

from pool_ton_bot import handlers


@telegram.ext.dispatcher.run_async
def command(update, context):
    handler = handlers.Command(update, context)
    if context.args:
        handler.pool()
    else:
        handler.start()
    handler.user.save()


@telegram.ext.dispatcher.run_async
def message(update, context):
    handler = handlers.Message(update, context)
    try:
        handler.text_selector[handler.text]()
    except KeyError:
        state = handler.user.state.split(' ')[0]
        handler.state_selector.get(
            state, handler.unknown_message
        )()
    handler.user.save()


@telegram.ext.dispatcher.run_async
def callback_query(update, context):
    handler = handlers.Callback(update, context)
    try:
        handler.selector[handler.query]()
    except KeyError:
        handler.ignore()
    else:
        context.bot.answer_callback_query(
            update.callback_query.id, text='OK'
        )
    handler.user.save()


@telegram.ext.dispatcher.run_async
def work_checker(context):
    pass


@telegram.ext.dispatcher.run_async
def error(update, context):
    print(update)
