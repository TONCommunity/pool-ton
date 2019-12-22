import requests

import config

from decimal import Decimal


def pretty_value(number, rounder=None):
    if number == 0:
        return 0
    if int(number) == number:
        number = int(number)
    elif rounder:
        try:
            number = round(number, rounder)
        except:
            pass
    return format(Decimal(str(number)).normalize(), 'f')


def adr_is_active(adr):
    r = requests.get(config.POOL_CHECK_API.format(adr=adr))
    status = r.json()['result']
    result = True if status == 'active' else False
    return result


def balance_is_correct(adr):
    r = requests.get(config.ADR_CHECK_API.format(adr=adr))
    try:
        balance = int(int(r.json()['result']['balance']) / 1000000000)
    except (KeyError, ValueError):
        result = False
    else:
        if balance >= config.POOL_INIT_AMOUNT:
            result = True
        else:
            result = False
    return result


def adr_is_correct(adr, is_base64=False):
    try:
        if not is_base64:
            if len(adr) != 66 or adr[:2] != '0x':
                raise ValueError('incorrect address')
            else:
                adr = f'-1:{adr[2:]}'
        else:
            if len(adr) != 48:
                raise ValueError
    except ValueError:
        result = False
    else:
        r = requests.get(config.ADR_CHECK_API.format(adr=adr))
        result = bool(r.json().get('result'))
    return result


def group(iterable, count, is_hex=False):
    """ Группировка элементов последовательности по count элементов """
    if is_hex:
        res = ['0x' + iterable[i:i + count] for i in
               range(0, len(iterable), count)]
    else:
        res = [iterable[i:i + count] for i in
               range(0, len(iterable), count)]
    return res
