import os
import secrets
from datetime import datetime, timezone, timedelta
from enum import StrEnum
import requests

AUTH_CODE = os.environ.get('T2_AUTH_CODE') or str(input('Код авторизации: '))

MIN_UNIT_COST = 0.8
SEC_CH_UA = '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'


class TrafficType(StrEnum):
    VOICE = 'voice'
    DATA = 'data'
    SMS = 'sms'


class Stuff(StrEnum):
    GB = 'gb'
    MIN = 'min'
    SMS = 'sms'


class Emoji(StrEnum):
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
    refer = 'my'
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
    return requests.put(
        f'https://ekt.t2.ru/api/subscribers/{number}/exchange/lots/created',
        json=json,
        headers=get_headers(auth_code, 5, SEC_CH_UA, UA, refer)
    ).json()


def update_order(
    number: str,
    order_id: str,
    auth_code: str,
    value: int,
    cost: int | None,
    emoji: list[Emoji | None],
):
    refer = 'my'
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
    return requests.patch(
        f'https://ekt.t2.ru/api/subscribers/{number}/exchange/lots/created/{order_id}',
        json=json,
        headers=get_headers(auth_code, 5, SEC_CH_UA, UA, refer)
    ).json()


def get_local_time(time_zone: int):
    time = datetime.now().astimezone(timezone(timedelta(hours=time_zone)))
    return time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + time.strftime('%z')


def get_headers(auth_code, time_zone: int, sec_ch_ua: str, ua: str, refer: str):
    return {
        'Accept': 'application/json, text/plain, */*',
        'accept-encoding': 'zstd',
        'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Authorization': auth_code,
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'priority': 'u=1, i',
        'referer': f'https://ekt.t2.ru/stock-exchange/{refer}',
        'sec-ch-ua': sec_ch_ua,
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': 'Windows',
        'tele2-user-agent': 'web',
        'user-agent': ua,
        'x-request-id': secrets.token_hex(20),
        'x-user-local-time': get_local_time(time_zone=time_zone),
    }
