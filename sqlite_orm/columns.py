class IncorrectForeignKey(Exception):
    """
    Исключение выбрасывается, если в качестве внешнего ключа передан объект
    не типа ForeignKey
    """
    pass


class ForeignKey:

    def __init__(self, model, field):

        self.external_model = model
        self.link_field = field


class Column:
    """Класс описывающий представление столбца таблицы"""

    def __init__(self, type, *args, **kwargs):
        self.type = type
        self.not_null = bool(kwargs.get('not_null'))
        self.default_value = kwargs.get('default_value')
        self.primary_key = bool(kwargs.get('primary_key'))
        self.autoincrement = bool(kwargs.get('autoincrement'))
        self.foreign_key = kwargs.get('foreign_key')

        if self.foreign_key and not isinstance(self.foreign_key, ForeignKey):
            raise IncorrectForeignKey()
