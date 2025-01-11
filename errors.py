class UnexpectedUOMVolume(Exception):
    def __init__(self, value):
        super().__init__(f'Неожиданное значение UOM лота: {value}. Доступные значения UOM для лота: min, gb, sms.')
