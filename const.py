import os
from typing import Final

AUTH_CODE: Final = os.environ.get('T2_AUTH_CODE') or str(input('Код авторизации: '))
DEFAULT_TIMEZONE: Final = 5
MIN_UNIT_COST: Final = 0.8
GB_UNIT_COST: Final = 15
SMS_UNIT_COST: Final = 15
SEC_CH_UA: Final = '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"'
UA: Final = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
)
