import secrets
import time
from datetime import datetime, timezone, timedelta
from typing import Collection

import requests

from const import MIN_UNIT_COST, UA, DEFAULT_TIMEZONE, SEC_CH_UA, GB_UNIT_COST, SMS_UNIT_COST
from errors import UnexpectedUOMValue
from models import (
    UOM,
    TrafficType,
    AvailableForSaleUOM,
    Statuses,
    Emoji,
    Regions,
    Currency,
)


def create_order(
    number: str,
    auth_code: str,
    uom: UOM,
    traffic_type: TrafficType,
    volume: int,
    cost: int | None,
    region: Regions,
):
    refer = 'stock-exchange/my'
    min_oum_cost = get_min_oum_cost(uom)
    if not cost or volume * min_oum_cost > cost:
        cost = volume * min_oum_cost
    json = {
        "volume": {
            "value": volume,
            "uom": uom
        },
        "cost": {
            "amount": cost,
            "currency": Currency.RUB
        },
        "trafficType": traffic_type
    }
    return requests.put(
        f'https://{region}.t2.ru/api/subscribers/{number}/exchange/lots/created',
        json=json,
        headers=get_headers(auth_code, DEFAULT_TIMEZONE, SEC_CH_UA, UA, refer, region)
    ).json()


def update_order(
    number: str,
    auth_code: str,
    uom: UOM,
    volume: int,
    cost: int | None,
    order_id: str,
    emoji: list[Emoji | None],
    region: Regions,
):
    refer = 'stock-exchange/my'
    min_oum_cost = get_min_oum_cost(uom)
    if not cost or volume * min_oum_cost > cost:
        cost = volume * min_oum_cost
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
    auth_code: str,
    order_id: str,
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
        f'https://{region}.t2.ru/api/subscribers/{number}/exchange/lots?trafficType={traffic_type}'
        f'&volume={volume}&cost={cost}&offset={offset}&limit={limit}',
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


def get_available_for_sale_traffic(number: str, auth_code: str, region: Regions) -> AvailableForSaleUOM:
    """
    Получить количество доступного для продажи трафика в этом абонентском месяце.

    :param number: Номер телефона.
    :param auth_code: Код аутентификации.
    :param region: Регион.
    :return: Количество доступного для продажи трафика.
    """
    my_traffic = get_my_traffic(number, auth_code, region)['data']
    available_traffic = AvailableForSaleUOM()

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


def start_raise_my_orders(
    number: str,
    auth_code: str,
    traffic_type: TrafficType,
    volume: int,
    cost: int,
    raise_balance: int,
    frequency: int,
    region: Regions,
    lower_top: int = 10,
):
    """
    Запуск продвижения всех своих лотов.

    :param number: Номер телефона.
    :param auth_code: Код аутентификации.
    :param traffic_type: Тип трафика.
    :param volume: Количество единиц трафика в ордере.
    :param cost: Цена ордера.
    :param raise_balance: Баланс на продвижение. Этот параметр позволяет исключить большие потери на
    продвижение во время небольшого спроса, ведь каждый вывод в топ стоит 5р. Больше указанной суммы
    не будет потрачено.
    :param frequency: Периодичность продвижения и проверок, находится ли лот в топе.
    :param lower_top: Когда нет ордеров в топе на позиции выше, либо равных этому значению, создаст новый ордер.
    :param region: Регион.
    """
    if raise_balance <= 0:
        return

    active_orders = [
        order for order in get_my_active_orders(number, auth_code, traffic_type, region)
        if order['cost']['amount'] == cost
    ]
    if not active_orders:
        return
    active_orders_ids = [order['id'] for order in active_orders]
    for order in active_orders:
        if int(order['cost']['amount']) != cost:
            active_orders.remove(order)
            continue
        if not are_orders_at_top(number, auth_code, traffic_type, volume, cost, region, active_orders_ids, lower_top):
            order_id = order['id']
            print(f'Продвижение для: {order_id}')
            print(raise_order(number, auth_code, order_id, region).json())
            raise_balance -= 5
            if raise_balance <= 0:
                break
        else:
            active_orders.insert(0, order)
            active_orders_ids.insert(0, order['id'])
            print(f'Пока есть лот в топе.')
        time.sleep(frequency)
    start_raise_my_orders(number, auth_code, traffic_type, volume, cost, raise_balance, frequency, region, lower_top)


def start_making_sell_orders(
    number: str,
    auth_code: str,
    uom: UOM,
    traffic_type: TrafficType,
    volume: int,
    orders_count: int,
    emoji: list[Emoji | None],
    frequency: int,
    region: Regions,
    cost: float | None = None,
    lower_top: int = 10,

):
    available_traffic: int = get_available_for_sale_traffic(number, auth_code, region)[uom]
    """
    Запуск выставления новых ордеров, когда в топе нет других лотов абонента.

    :param number: Номер телефона.
    :param auth_code: Код аутентификации.
    :param uom: Название единицы трафика.
    :param traffic_type: Тип трафика.
    :param volume: Количество единиц трафика в ордере.
    :param orders_count: Количество ордеров.
    :param emoji: Emoji в ордере.
    :param frequency: Периодичность продвижения и проверок, находится ли какой-нибудь лот в топе.
    :param cost: Цена одного ордера.
    :param lower_top: Когда нет ордеров в топе на позиции выше, либо равных этому значению, создаст новый ордер.
    :param region: Регион.
    """
    if volume > available_traffic:
        print(f'Лот не выставлен. Доступно для продажи: {available_traffic}{uom}')
        return
    if (volume * orders_count) > available_traffic:
        orders_count = available_traffic // volume
    print(f'Доступно для продажи: {available_traffic}{uom}. Будет выставлено лотов: {orders_count} по {volume}{uom}')

    min_oum_cost = get_min_oum_cost(uom)
    if not cost or volume * min_oum_cost > cost:
        cost = int(volume * min_oum_cost)

    active_orders_ids = [order['id'] for order in get_my_active_orders(number, auth_code, traffic_type, region)]
    for _ in range(orders_count):
        while are_orders_at_top(number, auth_code, traffic_type, volume, cost, region, active_orders_ids, lower_top):
            print(f'Пока есть лот в топе.')
            time.sleep(frequency)
        order_id = create_order(number, auth_code, uom, traffic_type, volume, cost,  region)['data']['id']
        update_order(number, auth_code, uom, volume, cost, order_id, emoji, region)

        # Проверка, что ордер отображается в продаже. Между запросом и отображением в системе есть задержка, из-за неё,
        # при следующей итерации не будет учитываться предыдущий ордер, от чего спасает данная проверка.
        while not are_orders_at_top(number, auth_code, traffic_type, volume, cost, region, [order_id], lower_top):
            print('пока не появился')
            time.sleep(1)
        active_orders_ids.append(order_id)
        print(f'Создан ордер: {order_id}')


def get_min_oum_cost(uom: UOM) -> float | None:
    match uom:
        case UOM.MIN:
            return MIN_UNIT_COST
        case UOM.GB:
            return GB_UNIT_COST
        case UOM.SMS:
            return SMS_UNIT_COST
    raise UnexpectedUOMValue(uom)


def get_my_active_orders(
    number: str,
    auth_code: str,
    traffic_type: TrafficType,
    region: Regions,
):
    return [
        order for order in get_my_orders(number, auth_code, region).get('data')
        if order.get('status') == Statuses.ACTIVE and order.get('trafficType') == traffic_type
    ]


def are_orders_at_top(
    number: str,
    auth_code: str,
    traffic_type: TrafficType,
    volume: int,
    cost: int,
    region: Regions,
    orders_ids: Collection[str],
    lower_top: int = 10,
) -> bool:
    """
    Узнать находятся ли какие-нибудь из проверяемых ордеров в топе.

    :param number: Номер телефона.
    :param auth_code: Код аутентификации.
    :param traffic_type: Тип трафика.
    :param volume: Количество единиц трафика в ордере.
    :param cost: Цена ордера.
    :param region: Регион.
    :param orders_ids: Последовательность из id ордеров, которые будут искаться в топе.
    :param lower_top: Когда нет ордеров в топе на позиции выше, либо равных этому значению, вернёт False.
    :return: True, если хотя-бы один из проверяемых ордеров находится в топе.
    """
    actual_orders = get_orders(number, auth_code, traffic_type, volume, cost, region, limit=lower_top).get('data')
    return bool(set(orders_ids) & {o['id'] for o in actual_orders})
