import secrets
import time
from datetime import datetime, timezone, timedelta

import requests

from const import MIN_UNIT_COST, UA, DEFAULT_TIMEZONE, SEC_CH_UA
from models import (
    UOM,
    TrafficType,
    AvailableForSaleOum,
    Statuses,
    Emoji,
    Regions,
)


def create_order(
    number: str,
    auth_code: str,
    value: int,
    cost: int | None,
    staff: UOM,
    traffic_type: TrafficType,
    region: Regions,
):
    refer = 'stock-exchange/my'
    if not cost:
        cost = value * MIN_UNIT_COST
    json = {
        "volume": {
            "value": value,
            "uom": staff
        },
        "cost": {
            "amount": cost,
            "currency": traffic_type
        },
        "trafficType": "voice"
    }
    return requests.put(
        f'https://{region}.t2.ru/api/subscribers/{number}/exchange/lots/created',
        json=json,
        headers=get_headers(auth_code, DEFAULT_TIMEZONE, SEC_CH_UA, UA, refer, region)
    ).json()


def update_order(
    number: str,
    order_id: str,
    auth_code: str,
    value: int,
    cost: int | None,
    emoji: list[Emoji | None],
    region: Regions,
):
    refer = 'stock-exchange/my'
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
        f'https://{region}.t2.ru/api/subscribers/{number}/exchange/lots/created/{order_id}',
        json=json,
        headers=get_headers(auth_code, DEFAULT_TIMEZONE, SEC_CH_UA, UA, refer, region)
    ).json()


def get_local_time(time_zone: int):
    time_ = datetime.now().astimezone(timezone(timedelta(hours=time_zone)))
    return time_.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + time_.strftime('%z')


def raise_order(
    number: str,
    order_id: str,
    auth_code: str,
    region: Regions,
):
    refer = 'stock-exchange/my'
    json = {'lotId': order_id}
    return requests.put(
        f'https://{region}.t2.ru/api/subscribers/{number}/exchange/lots/premium',
        json=json,
        headers=get_headers(auth_code, DEFAULT_TIMEZONE, SEC_CH_UA, UA, refer, region)
    )


def get_my_orders(
    number: str,
    auth_code: str,
    region: Regions,
):
    refer = 'stock-exchange/my'
    return requests.get(
        f'https://{region}.t2.ru/api/subscribers/{number}/exchange/lots/created',
        headers=get_headers(auth_code, DEFAULT_TIMEZONE, SEC_CH_UA, UA, refer, region)
    ).json()


def get_orders(
    number: str,
    auth_code: str,
    traffic_type: TrafficType,
    volume: int,
    cost: int,
    region: Regions,
    offset: int = 0,
    limit: int = 10,
):
    refer = 'internet'
    return requests.get(
        f'https://{region}.t2.ru/api/subscribers/{number}/exchange/lots?trafficType={traffic_type}&volume={volume}&cost={cost}&offset={offset}&limit={limit}',
        headers=get_headers(auth_code, DEFAULT_TIMEZONE, SEC_CH_UA, UA, refer, region)
    ).json()


def get_my_traffic(number: str, auth_code: str, region: Regions):
    """
    Получить весь трафик. Сумма доступного и недоступного для продажи трафика.

    :param number: Номер телефона
    :param auth_code: Код аутентификации
    :param region: Регион. Доступные значения хранятся в классе Regions
    :return: Весь трафик
    """
    refer = 'lk/remains'
    return requests.get(
        f'https://{region}.t2.ru/api/subscribers/{number}/site{region.upper()}/rests',
        headers=get_headers(auth_code, DEFAULT_TIMEZONE, SEC_CH_UA, UA, refer, region)
    ).json()


def get_headers(auth_code, time_zone: int, sec_ch_ua: str, ua: str, refer: str, region: Regions):
    return {
        'Accept': 'application/json, text/plain, */*',
        'accept-encoding': 'zstd',
        'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Authorization': auth_code,
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'priority': 'u=1, i',
        'referer': f'https://{region}.t2.ru/{refer}',
        'sec-ch-ua': sec_ch_ua,
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': 'Windows',
        'tele2-user-agent': 'web',
        'user-agent': ua,
        'x-request-id': secrets.token_hex(20),
        'x-user-local-time': get_local_time(time_zone=time_zone),
    }


def start_raise_my_orders(
    number: str, auth_code: str, traffic_type: TrafficType, raise_balance: int, frequency: int, region: Regions
):
    """
    Запуск продвижения всех своих лотов.

    :param number: Номер телефона
    :param auth_code: Код аутентификации
    :param traffic_type: Тип трафика
    :param raise_balance: Баланс на продвижение. Этот параметр позволяет исключить большие потери на
    продвижение во время небольшого спроса, ведь каждый вывод в топ стоит 5р. Больше указанной суммы
    не будет потрачено.
    :param frequency: Периодичность продвижения и проверок, находится ли лот в топе.
    :param region: Регион.
    """
    orders = get_my_orders(number, auth_code, region).get('data')
    active_orders = [
        order for order in orders
        if order.get('status') == Statuses.ACTIVE and order.get('trafficType') == traffic_type
    ]
    if not active_orders or raise_balance <= 0:
        return
    active_orders_ids = {order['id'] for order in active_orders}
    for order in active_orders:
        actual_orders = get_orders(
            number,
            auth_code,
            traffic_type,
            order.get('volume').get('value'),
            order.get('cost').get('amount'),
            region
        ).get('data')
        actual_orders_ids = {
            o.get('id') for o in actual_orders
        }
        if not (active_orders_ids & actual_orders_ids):
            order_id = order.get('id')
            print(f'Продвижение для: {order_id}')
            raise_order(number, order_id, auth_code, region)
            raise_balance -= 5
            if raise_balance <= 0:
                break
        else:
            active_orders.insert(0, order)
            print(f'Пока есть лот в топе.')
        time.sleep(frequency)
    start_raise_my_orders(number, auth_code, traffic_type, raise_balance, frequency, region)


def get_available_for_sale_traffic(number: str, auth_code: str, region: Regions) -> AvailableForSaleOum:
    """
    Получить количество доступного для продажи трафика в этом абонентском месяце.

    :param number: Номер телефона.
    :param auth_code: Код аутентификации.
    :param region: Регион.
    :return: Количество доступного для продажи трафика.
    """
    my_traffic = get_my_traffic(number, auth_code, region)['data']
    available_traffic = AvailableForSaleOum()

    for traffic in my_traffic['rests']:
        if traffic['rollover']:
            continue
        remain = int(traffic.get('remain'))
        match traffic.get('uom'):
            case 'min':
                available_traffic.min += remain
            case 'mb':
                available_traffic.gb += remain // 1024
            case 'pcs':
                available_traffic.sms += remain
    return available_traffic
