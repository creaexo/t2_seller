import secrets
from datetime import datetime, timezone, timedelta
from typing import NamedTuple, Literal

import requests

AUTH_CODE = str(input())

MIN_UNIT_COST = 0.8


Stuff = Literal['gb', 'min']


class Emoji(NamedTuple):
    DEVIL = 'devil'
    BOMB = 'bomb'
    CAT = 'cat'
    COOL = 'cool'
    RICH = 'rich'
    SCREAM = 'scream'
    TONGUE = 'tongue'
    ZIPPED = 'zipped'


def create_order(
    number: str,
    auth_code: str,
    value: int,
    cost: int | None,
    staff: Stuff,
):
    if not cost:
        cost = value * MIN_UNIT_COST
    json = {
        "volume": {
            "value": value,
            "uom": staff
        },
        "cost": {
            "amount": cost,
            "currency": "rub"
        },
        "trafficType": "voice"
    }
    r = requests.put(
        f'https://ekt.t2.ru/api/subscribers/{number}/exchange/lots/created',
        json=json,
        headers=get_headers(auth_code, 5, '', '')
    )
    return r.json()


def update_order(
    number: str,
    order_id: str,
    auth_code: str,
    value: int,
    cost: int | None,
    emoji: list[str | None]
):
    if not cost:
        cost = value * MIN_UNIT_COST
    json = {
        "showSellerName": True,
        "emojis": emoji,
        "cost": {
            "amount": cost,
            "currency": "rub"
        }
    }
    r = requests.patch(
        f'https://ekt.t2.ru/api/subscribers/{number}/exchange/lots/created/{order_id}',
        json=json,
        headers=get_headers(auth_code, 5, '', '')
    )
    return r.json()


def get_local_time(time_zone: int):
    time = datetime.now().astimezone(timezone(timedelta(hours=time_zone)))
    return time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + time.strftime('%z')


def get_headers(auth_code, time_zone: int, ua: str, browser: str):
    return {
        'Accept': 'application/json, text/plain, */*',
        'Authorization': auth_code,

        'Content-type': 'application/json',
        'referer': 'https://ekt.t2.ru/stock-exchange/my',
        'sec-ch-ua': browser,
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': 'Windows',
        'tele2-user-agent': 'web',
        'user-agent': ua,
        'x-request-id': secrets.token_hex(20),
        'x-user-local-time': get_local_time(time_zone=time_zone),
    }
