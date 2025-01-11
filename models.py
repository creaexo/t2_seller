from enum import StrEnum

from pydantic import BaseModel


class Regions(StrEnum):
    """Регион абонента"""
    EKT = 'ekt'


class Statuses(StrEnum):
    ACTIVE = 'active'
    BOUGHT = 'bought'
    EXPIRED = 'expired'
    REVOKED = 'revoked'
    ERROR = 'error'


class TrafficType(StrEnum):
    VOICE = 'voice'
    DATA = 'data'
    SMS = 'sms'


class UOM(StrEnum):
    GB = 'gb'
    MB = 'mb'
    MIN = 'min'
    SMS = 'sms'
    PCS = 'pcs'


class Emoji(StrEnum):
    DEVIL = 'devil'
    BOMB = 'bomb'
    CAT = 'cat'
    COOL = 'cool'
    RICH = 'rich'
    SCREAM = 'scream'
    TONGUE = 'tongue'
    ZIPPED = 'zipped'


class AvailableForSaleUOM(BaseModel):
    min: int = 0
    gb: int = 0
    sms: int = 0

    def __getitem__(self, item):
        return getattr(self, item)


class Currency(StrEnum):
    RUB = 'rub'
