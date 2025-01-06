from enum import StrEnum

from pydantic import BaseModel


class Regions(StrEnum):
    EKT = 'EKT'


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


class AvailableForSaleOum(BaseModel):
    min: int = 0
    gb: int = 0
    sms: int = 0
