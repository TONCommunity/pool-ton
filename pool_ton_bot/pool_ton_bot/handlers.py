from uuid import uuid4
import json
import time
import subprocess
import os
import re
import io
from datetime import date

import telegram
from mongoengine.queryset.visitor import Q

import config
from pool_ton_bot import db, utils


class Default:
    def __init__(self, update, context):
        if update.effective_user.is_bot:
            return
        self.update, self.context = update, context
        try:
            self.user = db.Users.objects.get(_id=update.effective_user.id)
        except db.DoesNotExist:
            try:
                language = update.effective_user.language_code
                if language not in config.SUPPORTED_LANGUAGES:
                    raise AttributeError
            except AttributeError:
                language = 'en'
            self.user = db.Users(
                _id=update.effective_user.id, language=language,
                first_name=update.effective_user.first_name,
                username=update.effective_user.username,
                last_name=update.effective_user.last_name,
            )
            self.new_user()
        self.active_user()
        self.user.active = True
        self.messages, self.captions, self.strings, self.buttons = [{}] * 4
        header = f'{self.user.first_name} {self.user.last_name} @{self.user.username} ({self.user._id})'
        try:
            print(f'{self.user.language} {header}: {self.update.callback_query.data}')
        except AttributeError:
            print(f'{self.user.language} {header}: {self.update.effective_message.text}')

    def get_pool_list(self, is_public=False):
        if is_public:
            result = db.Pools.objects(pool_type='public')
        else:
            result = db.Pools.objects(
                Q(pool_type__ne='public') & (Q(_id__in=list(self.user.pools)) | Q(creator=self.user._id))
            )
        return result

    def get_pool_message(self, pool, is_public=False):
        keyboard = None
        pool_adr = pool.adrs['user_friendly']
        result = subprocess.getoutput(
            f'lite-client -C /root/ton-client.config -c "runmethod {pool_adr} config"'
        ).split('\n')[-1]
        raw_params = result[result.index('[') + 1:result.index(']')].strip()
        result = subprocess.getoutput(
            f'lite-client -C /root/ton-client.config -c "runmethod {pool_adr} grams"'
        ).split('\n')[-1]
        received = int(int(result[result.index('[') + 1:result.index(']')].strip()) / 1000000000)
        params = [int(p) for p in raw_params.split(' ')]
        time_left = params[0] + params[1] - int(time.time())
        time_left = 0 if time_left < 0 else time_left
        if params[2] == 0:
            destination_adr = self.message('NO_ADR')
        else:
            destination_adr = f'{params[2]}:{hex(params[3])[2:]}'
        total_amount, min_contribute, max_contribute = [int(v / 1000000000) for v in params[4:]]
        if self.user.pools.get(pool._id) in pool.requests:
            message = self.message('POOL_WAIT_APPROVE').format(
                pool_adr=pool.adrs['user_friendly']
            )
        elif self.user.pools.get(pool._id) not in pool.participants and pool.pool_type != 'public' and pool.creator != self.user._id:
            message = self.message('POOL_NEED_REQUEST').format(
                pool_type=pool.pool_type
            )
            keyboard = self.inline_buttons(
                self.button('REQUEST'),
                f'request new {pool._id} {self.user._id}'
            )
        else:
            if is_public or self.user._id == pool.creator:
                user_adr = self.message('NO_ADR')
            else:
                user_adr = self.user.pools[pool._id]
            if self.user._id == pool.creator:
                link = self.string('POOL_LINK').format(
                    pool_id=pool._id
                )
            else:
                link = self.message('ACCESS_ERROR')
            message = self.message('POOL_INFO').format(
                pool_description=pool['description'],
                pool_adr=pool.adrs['user_friendly'],
                collection_adr=pool.adrs['main'],
                time_left=time_left,
                destination_adr=destination_adr,
                total_amount=total_amount,
                min_contribute=min_contribute,
                max_contribute=max_contribute,
                received=received,
                user_adr=user_adr,
                link=link
            )
            is_admin = 1 if self.user._id == pool.creator else 0
            keyboard = self.inline_buttons(
                self.button('POOL_PARTICIPANTS'),
                f'pool_participants {pool._id} {is_admin}'
            )
        return message, keyboard

    def adr_status_checker(self, context):
        adr = self.user.temp_pool['adrs']['init']
        for i in range(5):
            os.system(config.LITE_CLIENT_COMMAND.format(
                pool_id=self.user.temp_pool['id'])
            )
            time.sleep(5)
            active_status = utils.adr_is_active(adr)
            if active_status:
                pool = db.Pools(
                    _id=self.user.temp_pool['id'], creator=self.user._id,
                    adrs=self.user.temp_pool['adrs'],
                    pool_type=self.user.temp_pool['type'],
                    description=self.user.temp_pool['data']['description']
                )
                pool.save()
                message = self.message('POOL_CREATE_SUCCESS').format(
                    link=self.string("POOL_LINK").format(pool_id=pool._id),
                    pool_adr=pool.adrs['user_friendly'],
                    collection_adr=pool.adrs['main']
                )
                self.context.bot.send_message(
                    text=message,
                    reply_markup=None,
                    parse_mode=telegram.ParseMode.HTML,
                    chat_id=self.user._id,
                    # message_id=self.update.callback_query.message.message_id,
                    # disable_web_page_preview=True
                )
                break

    def new_user(self):
        self.user.started_at = int(time.time())
        db.Stats.objects(_id=date.today()).update_one(
            add_to_set__new_users=self.user._id, upsert=True
        )

    def active_user(self):
        self.user.username = self.update.effective_user.username
        self.user.first_name = self.update.effective_user.first_name
        self.user.last_name = self.update.effective_user.last_name
        self.user.updated_at = int(time.time())
        db.Stats.objects(_id=date.today()).update_one(
            add_to_set__active_users=self.user._id, upsert=True
        )

    def pool_init(self):
        self.user.temp_pool['id'] = str(uuid4())
        raw_params = (
            f'{config.POOLS_DIR}/{self.user.temp_pool["id"]}',
            self.user.temp_pool['data']['workchain_id'],
            self.user.temp_pool['data']['total_amount'],
            self.user.temp_pool['data']['min_contribute'],
            self.user.temp_pool['data']['max_contribute'],
            self.user.temp_pool['data']['pool_lifetime'],
            len(self.user.temp_pool['data']['admins_pubkeys']),
            *self.user.temp_pool['data']['admins_pubkeys'],
            self.user.temp_pool['data'].get('lock_destination_adr'),
        )
        params = ' '.join((str(p) for p in raw_params if p or p==0))
        raw_result = subprocess.check_output(
            config.FIFT_COMMAND.format(filename='pool-init', params=params),
            shell=True
        ).decode('utf-8')
        adrs = [s.strip().split(' ')[-1] for s in raw_result.split('\n') if s and config.POOLS_DIR not in s]
        self.user.temp_pool['adrs'] = {
            'user_friendly': adrs[0],
            'init': adrs[1],
            'main': adrs[2]
        }
        message = self.message('POOL_DEPOSIT').format(
            amount=config.POOL_INIT_AMOUNT,
            adr=self.user.temp_pool['adrs']['init'],
        )
        keyboard = self.inline_buttons(
            self.button('POOL_DEPOSIT'), 'pool_deposit'
        )
        return message, keyboard

    def language_select_keyboard(self, is_start=False):
        keyboard = []
        for language, button_text in config.LANGUAGE_SELECTOR.items():
            callback_data = f'language {language}'
            button = telegram.InlineKeyboardButton(
                button_text,
                callback_data=callback_data
            )
            keyboard.append([button])
        if not is_start:
            back_button = telegram.InlineKeyboardButton(
                self.button('BACK'),
                callback_data='screen settings'
            )
            keyboard.append([back_button])
        return telegram.InlineKeyboardMarkup(keyboard)

    def pool_list_keyboard(self, page, last_page, is_public):
        if last_page < 2:
            return None
        if is_public:
            event = 'pool_info public'
        else:
            event = 'pool_info public'
        left_button = telegram.InlineKeyboardButton(
            self.button('LEFT_BUTTON'),
            callback_data=f'{event} {page-1 if page!=0 else last_page-1}'
        )
        middle_button = telegram.InlineKeyboardButton(
            f'{page+1}/{last_page}',
            callback_data=config.IGNORE_CALLBACK
        )
        right_button = telegram.InlineKeyboardButton(
            self.button('RIGHT_BUTTON'),
            callback_data=f'{event} {page+1 if page!=last_page-1 else 0}'
        )
        return telegram.InlineKeyboardMarkup([
            [left_button, middle_button, right_button]
        ])

    def main_reply_keyboard(self):
        keyboard = [
            [self.button('POOL_PUBLIC_LIST')],
            [self.button(name) for name in ('POOL_CREATE', 'POOL_LIST')],
            [self.button('SETTINGS')],
            [self.button('FEEDBACK')],
        ]
        return telegram.ReplyKeyboardMarkup(
            keyboard, one_time_keyboard=False, resize_keyboard=True
        )

    def string(self, string_name):
        if not self.strings:
            with open('constants/strings.json') as f:
                self.strings = json.loads(f.read())
        raw_string = self.strings[string_name]
        if isinstance(raw_string, list):
            result = '\n'.join(raw_string)
        else:
            result = raw_string
        return result

    def message(self, message_name, language=None):
        if not language:
            language = self.user.language
        if not self.messages:
            with open('constants/messages.json') as f:
                self.messages = json.loads(f.read())
        raw_message = self.messages[message_name][language]
        if isinstance(raw_message, list):
            result = '\n'.join(raw_message)
        else:
            result = raw_message
        return result

    def caption(self, caption_name):
        if not self.captions:
            with open('constants/captions.json') as f:
                self.captions = json.loads(f.read())
        raw_caption = self.captions[caption_name][self.user.language]
        if isinstance(raw_caption, list):
            result = '\n'.join(raw_caption)
        else:
            result = raw_caption
        return result

    def button(self, button_name, language=None):
        if not language:
            language = self.user.language
        if not self.buttons:
            with open('constants/buttons.json') as f:
                self.buttons = json.loads(f.read())
        return self.buttons[button_name][language]

    @staticmethod
    def inline_buttons(text, data):
        buttons = []
        if isinstance(text, str) and isinstance(data, str):
            text, data = [text], [data]
        for text, data in zip(text, data):
            buttons.append(
                [
                    telegram.InlineKeyboardButton(
                        text,
                        callback_data=data
                    )
                ]
            )
        return telegram.InlineKeyboardMarkup(buttons)

    @staticmethod
    def description_is_correct(raw_description):
        description = re.sub(r'[^А-Яа-яA-Za-z0-9\s]+', '', raw_description)
        if len(description) > 1024:
            result = False
        else:
            result = {'description': description}
        return result

    @staticmethod
    def workchain_is_correct(workchain_id):
        try:
            workchain_id = int(workchain_id)
            if workchain_id not in (0, -1):
                raise ValueError
        except ValueError:
            result = False
        else:
            result = {"workchain_id": workchain_id}
        return result

    @staticmethod
    def total_amount_is_correct(total_amount):
        try:
            total_amount = int(total_amount)
            if total_amount <= 1:
                raise ValueError
        except ValueError:
            result = False
        else:
            result = {'total_amount': total_amount}
        return result

    @staticmethod
    def min_contribute_is_correct(min_contribute, total_amount):
        try:
            min_contribute = int(min_contribute)
            if min_contribute >= total_amount:
                raise ValueError
        except ValueError:
            result = False
        else:
            result = {'min_contribute': min_contribute}
        return result

    @staticmethod
    def max_contribute_is_correct(max_contribute, total_amount, min_contribute):
        try:
            max_contribute = int(max_contribute)
            if max_contribute > total_amount or max_contribute < min_contribute:
                raise ValueError
        except ValueError:
            result = False
        else:
            result = {'max_contribute': max_contribute}
        return result

    @staticmethod
    def pool_lifetime_is_correct(pool_lifetime):
        pool_lifetime = int(pool_lifetime)
        try:
            if pool_lifetime < 0 or pool_lifetime > 31556926:
                raise ValueError
        except ValueError:
            result = False
        else:
            result = {'pool_lifetime': pool_lifetime}
        return result

    @staticmethod
    def admins_pubkeys_are_correct(adrs):
        for adr in adrs.split(' '):
            if not utils.adr_is_correct(adr):
                return False
        return {'admins_pubkeys': adrs.split(' ')}

    @staticmethod
    def lock_destination_adr_is_correct(adr):
        if utils.adr_is_correct(adr, is_base64=True):
            result = {'lock_destination_adr': adr}
        else:
            result = False
        return result


class Message(Default):
    def __init__(self, update, context):
        Default.__init__(self, update, context)
        self.text = self.update.effective_message.text.strip()
        self.text_selector = {
            self.button('POOL_CREATE'): self.pool_create_message,
            self.button('POOL_LIST'): self.pool_list_message,
            self.button('POOL_PUBLIC_LIST'): self.pool_list_message,
            self.button('SETTINGS'): self.settings_message,
            self.button('FEEDBACK'): self.feedback_message,
        }
        self.state_selector = {
            'input_wallet_address': self.input_wallet_address,
            'input_feedback': self.input_feedback,
            'input_reply': self.input_reply,
            'input_pool_data': self.input_pool_data
        }

    def pool_create_message(self):
        message = self.message('POOL_TYPE')
        keyboard = self.inline_buttons(
            [
                self.button('POOL_PUBLIC'),
                self.button('POOL_NONPUBLIC'),
                self.button('POOL_PRIVATE')
            ],
            [
                'pool_create public',
                'pool_create nonpublic',
                'pool_create private'
            ]
        )
        self.user.temp_pool = {}
        self.update.message.reply_html(
            message,
            reply_markup=keyboard,
        )

    def pool_list_message(self):
        if self.button('POOL_PUBLIC_LIST') == self.text:
            is_public = True
        else:
            is_public = False
        pools = self.get_pool_list(is_public=is_public)
        keyboard = self.main_reply_keyboard()
        if pools:
            pool = pools[0]
            keyboard = self.pool_list_keyboard(
                0, len(pools), is_public=is_public
            )
            message, kb = self.get_pool_message(pool, is_public)
            keyboard = kb if kb else keyboard
        else:
            message = self.message('POOL_NOT_EXIST')
        self.update.message.reply_html(
            message,
            reply_markup=keyboard,
            disable_web_page_preview=True
        )

    def settings_message(self):
        message = self.message('SETTINGS')
        keyboard = self.inline_buttons(
            self.button('CHANGE_LANGUAGE'),
            'language set'
        )
        self.update.message.reply_html(
            message,
            reply_markup=keyboard,
            disable_web_page_preview=True
        )

    def feedback_message(self):
        self.user.state = 'input_feedback'
        message = self.message('FEEDBACK_INPUT')
        keyboard = self.inline_buttons(
            self.button('BACK'),
            'screen main_menu'
        )
        self.update.message.reply_html(
            message,
            reply_markup=keyboard,
            disable_web_page_preview=True
        )

    def input_feedback(self):
        self.user.state = 'main_menu'
        message = (
            f"Message from @{self.user.username} ({self.user._id})\n"
            f"{self.user.first_name} {self.user.last_name}:\n\n"
            f"{self.text}"
        )
        keyboard = self.inline_buttons(
            self.button('REPLY'),
            f"reply {self.user._id} {self.update.message.message_id}"
        )
        for admin in config.ADMINS:
            self.context.bot.send_message(
                admin, message, reply_markup=keyboard
            )
        self.update.message.reply_text(
            self.message('FEEDBACK_SENT'),
            reply_markup=self.main_reply_keyboard(),
            disable_web_page_preview=True
        )

    def input_reply(self):
        user_id, message_id = self.user.state.split(' ')[1:]
        keyboard = self.inline_buttons(
            self.button('REPLY'),
            f"reply {self.user._id} {self.update.message.message_id}"
        )
        self.context.bot.send_message(
            user_id,
            self.text,
            reply_markup=keyboard,
            parse_mode=telegram.ParseMode.HTML,
            reply_to_message_id=message_id

        )
        self.user.state = 'main_menu'
        self.update.message.reply_text(
            self.message('FEEDBACK_SENT'),
            reply_markup=self.main_reply_keyboard(),
            disable_web_page_preview=True
        )

    def input_wallet_address(self):
        pool_id, attempt = self.user.state.split(' ')[1:]
        adr = self.text
        pool = db.Pools.objects(_id=pool_id).get()
        self.user.state = 'main_menu'
        if adr in pool.requests:
            message = self.message('ADR_EXIST_IN_POOL')
        elif not utils.adr_is_correct(adr):
            message = self.message('ADR_INCORRECT')
        elif attempt == '0':
            self.user.state = f'input_wallet_address {pool_id} 1'
            message = self.message('ADR_REPEAT_INPUT')
        else:
            self.user.pools[pool_id] = adr
            if pool.pool_type == 'nonprivate':
                db.Pools.objects(
                    _id=pool_id
                ).update_one(add_to_set__participants=adr)
                message = self.message('REQUEST_AUTO_APPROVED').format(
                    pool_adr=pool.adrs['user_friendly']
                )
            else:
                db.Pools.objects(
                    _id=pool_id
                ).update_one(add_to_set__requests=adr)
                pool_creator_language = db.Users.objects(
                    _id=pool.creator
                ).get().language
                keyboard = self.inline_buttons(
                    [
                        self.button('APPROVE', pool_creator_language),
                        self.button('REJECT', pool_creator_language),
                    ],
                    [
                        f'request approve {pool_id} {self.user._id}',
                        f'request reject {pool_id} {self.user._id}'
                    ]
                )
                self.context.bot.send_message(
                    pool.creator,
                    self.message('REQUEST_NEW', pool_creator_language).format(
                        pool_adr=pool.adrs['user_friendly'],
                        username=self.user.username,
                        user_id=self.user._id,
                    ),
                    reply_markup=keyboard,
                )
                message = self.message('REQUEST_SENT').format(
                    pool_adr=pool.adrs['user_friendly']
                )
        self.update.message.reply_html(
            message,
        )

    def input_pool_data(self):
        step = int(self.user.state.split(' ')[1])
        selector = (
            (self.description_is_correct, self.message('INPUT_DESCRIPTION')),
            (self.workchain_is_correct, self.message('INPUT_WORKCHAIN')),
            (self.total_amount_is_correct, self.message('INPUT_TOTAL_AMOUNT')),
            (self.min_contribute_is_correct, self.message('INPUT_MIN_CONTRIBUTE')),
            (self.max_contribute_is_correct, self.message('INPUT_MAX_CONTRIBUTE')),
            (self.pool_lifetime_is_correct, self.message('INPUT_POOL_LIFETIME')),
            (self.admins_pubkeys_are_correct, self.message('INPUT_ADMINS_PUBKEYS')),
            (self.lock_destination_adr_is_correct, self.message('INPUT_LOCK_DESTINATION_ADR'))
        )
        params = [self.text]
        if step in (3, 4):
            params.append(self.user.temp_pool['data']['total_amount'])
        if step == 4:
            params.append(self.user.temp_pool['data']['min_contribute'])
        result = selector[step][0](*params)
        keyboard = self.main_reply_keyboard()
        if result:
            try:
                self.user.temp_pool['data'].update(result)
            except KeyError:
                self.user.temp_pool['data'] = result
            if step != len(selector) - 1:
                if step == len(selector) - 2:
                    keyboard = self.inline_buttons(
                        self.button('SKIP'), 'screen pool_data_sent'
                    )
                    message = selector[step + 1][1]
                self.user.state = f'input_pool_data {step + 1}'
                message = selector[step + 1][1]
            else:
                self.user.state = 'main_menu'
                message, keyboard = self.pool_init()
        else:
            message = self.message('VALUE_INCORRECT') + selector[step][1]
        self.update.message.reply_html(
            message,
            reply_markup=keyboard
        )

    def unknown_message(self):
        message = self.message('UNKNOWN_COMMAND')
        keyboard = self.main_reply_keyboard()
        self.update.message.reply_html(
            message,
            reply_markup=keyboard,
            disable_web_page_preview=True
        )


class Command(Default):
    def __init__(self, update, context):
        Default.__init__(self, update, context)

    def start(self):
        self.user.state = 'main_menu'
        self.update.message.reply_html(
            text=self.message('LANGUAGE_SELECT'),
            reply_markup=self.language_select_keyboard(is_start=True)
        )

    def pool(self):
        keyboard = self.main_reply_keyboard()
        pool_id = self.context.args[0]
        try:
            pool = db.Pools.objects(_id=pool_id).get()
        except db.DoesNotExist:
            message = self.message('POOL_INCORRECT_ID')
        else:
            message, kb = self.get_pool_message(pool)
            keyboard = kb if kb else keyboard
        self.update.message.reply_html(
            text=message,
            reply_markup=keyboard
        )


class Callback(Default):
    def __init__(self, update, context):
        Default.__init__(self, update, context)
        query_text = update.callback_query.data.strip()
        try:
            self.query, self.params = query_text.split(' ', 1)
        except ValueError:
            self.query = query_text
            self.params = None
        self.selector = {
            'reply': self.reply,
            'screen': self.screen,
            'language': self.language,
            'pool_info': self.pool_info,
            'pool_create': self.pool_create,
            'pool_deposit': self.pool_check_deposit,
            'request': self.pool_request,
            'pool_participants': self.pool_participants,
        }

    def pool_request(self):
        action, pool_id, user_id = self.params.split(' ')
        user_id = int(user_id)
        pool = db.Pools.objects(_id=pool_id).get()
        keyboard = None
        if action == 'new':
            if self.user._id in pool.requests:
                message = self.message('REQUEST_ALREADY_SENT').format(
                    pool_adr=pool.adrs['user_friendly']
                )
            else:
                self.user.state = f'input_wallet_address {pool._id} 0'
                message = self.message('ADR_INPUT')
                keyboard = self.inline_buttons(
                    self.button('BACK'),
                    'pool_info 0'
                )
        elif action in ('approve', 'reject'):
            user = db.Users.objects(_id=user_id).get()
            adr = user.pools[pool_id]
            user_language = user.language
            db.Pools.objects(
                _id=pool_id
            ).update_one(pull__requests=adr)
            if action == 'approve':
                db.Pools.objects(
                    _id=pool_id
                ).update_one(
                    add_to_set__participants=adr
                )
                message = self.message(
                    'REQUEST_APPROVED', user_language
                ).format(pool_adr=pool.adrs['user_friendly'])
            elif action == 'reject':
                db.Users.objects(_id=user_id).update_one(
                    **{f'unset__pools__{pool_id}': True}
                )
                message = self.message(
                    'REQUEST_REJECTED', user_language
                ).format(pool_adr=pool.adrs['user_friendly'])
            self.context.bot.send_message(
                user_id,
                message
            )
        self.context.bot.edit_message_text(
            text=message,
            reply_markup=keyboard,
            parse_mode=telegram.ParseMode.HTML,
            chat_id=self.user._id,
            message_id=self.update.callback_query.message.message_id,
        )

    def pool_info(self):
        pool_type, page = self.params.split(' ')
        is_public = True if pool_type == 'public' else False
        page = int(page)
        pools = self.get_pool_list(is_public=is_public)
        if pools and page < len(pools):
            self.user.state = 'main_menu'
            keyboard = self.pool_list_keyboard(
                page, len(pools), is_public=is_public
            )
            pool = pools[page]
            message, kb = self.get_pool_message(pool, is_public)
            keyboard = kb if kb else keyboard
        else:
            message = self.message('POOL_NOT_EXIST')
        self.context.bot.edit_message_text(
            text=message,
            reply_markup=keyboard,
            parse_mode=telegram.ParseMode.HTML,
            chat_id=self.user._id,
            message_id=self.update.callback_query.message.message_id,
        )

    def pool_check_deposit(self):
        adr = self.user.temp_pool['adrs']['init']
        paid_status = utils.balance_is_correct(adr)
        self.user.state = 'main_menu'
        if paid_status:
            message = self.message('POOL_DEPOSIT_SUCCESS')
            self.context.job_queue.run_once(
                self.adr_status_checker, 0
            )
            self.context.bot.edit_message_text(
                text=message,
                parse_mode=telegram.ParseMode.HTML,
                chat_id=self.user._id,
                message_id=self.update.callback_query.message.message_id,
                disable_web_page_preview=True
            )
        else:
            caption = self.caption('POOL_DEPOSIT_WAIT')
            self.context.bot.answer_callback_query(
                self.update.callback_query.id, text=caption
            )

    def pool_create(self):
        self.user.temp_pool['type'] = self.params
        self.user.state = 'input_pool_data 0'
        message = self.message('INPUT_DESCRIPTION')
        keyboard = None
        self.context.bot.edit_message_text(
            text=message,
            reply_markup=keyboard,
            parse_mode=telegram.ParseMode.HTML,
            chat_id=self.user._id,
            message_id=self.update.callback_query.message.message_id,
            disable_web_page_preview=True
        )

    def pool_participants(self):
        pool_id, is_admin = self.params.split(' ')
        pool = db.Pools.objects.get(_id=pool_id)
        if is_admin == '0':
            with open(config.USER_SCRIPTS, 'rb') as f:
                self.context.bot.send_document(
                    self.user._id,
                    f,
                    filename=config.USER_SCRIPTS,
                )
        elif pool.pool_type == 'public':
            with open(config.ADMIN_SCRIPTS, 'rb') as f:
                self.context.bot.send_document(
                    self.user._id,
                    f,
                    filename=config.ADMIN_SCRIPTS,
                )
        elif pool.participants:
            with open(config.ADMIN_SCRIPTS, 'rb') as f:
                self.context.bot.send_document(
                    self.user._id,
                    f,
                    filename=config.ADMIN_SCRIPTS,
                )
            params = f'{len(pool.participants)} {" ".join(pool.participants)}'
            message = self.message('POOL_PARTICIPANTS')
            with io.BytesIO(params.encode('utf-8')) as f:
                self.context.bot.send_document(
                    self.user._id,
                    f,
                    caption=message,
                    filename=f'{pool_id}.txt'
                )
        else:
            message = self.message('POOL_PARTICIPANTS_NO')
            self.context.bot.send_message(
                self.user._id,
                message,
                parse_mode=telegram.ParseMode.HTML,
                disable_web_page_preview=True
            )

    def ignore(self):
        self.context.bot.answer_callback_query(
            self.update.callback_query.id, text='None'
        )

    def language(self):
        language = self.params
        keyboard = self.language_select_keyboard()
        if language in config.SUPPORTED_LANGUAGES:
            self.user.language = language
            caption = self.caption('LANGUAGE_CHANGED')
            self.context.bot.send_message(
                self.user._id,
                self.message('START'),
                reply_markup=self.main_reply_keyboard(),
                parse_mode=telegram.ParseMode.HTML,
                disable_web_page_preview=True
            )
        else:
            caption = self.caption('LANGUAGE_SELECT')
        message = self.message('LANGUAGE_SELECT')
        self.context.bot.edit_message_text(
            text=message,
            reply_markup=keyboard,
            parse_mode=telegram.ParseMode.HTML,
            chat_id=self.user._id,
            message_id=self.update.callback_query.message.message_id,
            disable_web_page_preview=True
        )
        self.context.bot.answer_callback_query(
            self.update.callback_query.id, text=caption
        )

    def screen(self):
        screen_name = self.params
        if screen_name == 'main_menu':
            message = self.message('START')
            keyboard = None
        elif screen_name == 'settings':
            message = self.message('SETTINGS')
            keyboard = self.inline_buttons(
                self.button('CHANGE_LANGUAGE'),
                'language set'
            )
        elif screen_name == 'pool_data_sent':
            message, keyboard = self.pool_init()
        self.context.bot.edit_message_text(
            text=message,
            parse_mode=telegram.ParseMode.HTML,
            chat_id=self.user._id,
            message_id=self.update.callback_query.message.message_id,
            reply_markup=keyboard,
            disable_web_page_preview=True
        )

    def reply(self):
        user_id, message_id = self.params.split(' ')
        message = self.message('FEEDBACK_INPUT')
        keyboard = self.inline_buttons(
            self.button('BACK'), 'screen main_menu'
        )
        self.context.bot.send_message(
            self.user._id,
            message,
            reply_markup=keyboard,
            parse_mode=telegram.ParseMode.HTML
        )
        caption = self.caption('SUCCESS')
        self.user.state = f'input_reply {user_id} {message_id}'
        self.context.bot.answer_callback_query(
            self.update.callback_query.id,
            text=caption
        )
