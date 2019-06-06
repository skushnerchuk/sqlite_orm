from .exceptions import ConditionNotImplemented
from .utils import prepare_value


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

    def __eq__(self, value):
        tmp_value = prepare_value(value)
        if not value:
            return '{}.{} is NULL'.format(self.model.table_name, self.name)
        return '{}.{}'.format(self.model.table_name, self.name), '=', tmp_value

    def __ne__(self, value):
        tmp_value = prepare_value(value)
        if not value:
            return '{}.{} is not NULL'.format(self.model.table_name, self.name)
        return '{}.{}'.format(self.model.table_name, self.name), '!=', tmp_value

    def __lt__(self, value):
        if not value:
            raise ConditionNotImplemented()
        tmp_value = prepare_value(value)
        return '{}.{}'.format(self.model.table_name, self.name), '<', tmp_value

    def __le__(self, value):
        if not value:
            raise ConditionNotImplemented()
        tmp_value = prepare_value(value)
        return '{}.{}'.format(self.model.table_name, self.name), '<=', tmp_value

    def __gt__(self, value):
        if not value:
            raise ConditionNotImplemented()
        tmp_value = prepare_value(value)
        return '{}.{}'.format(self.model.table_name, self.name), '>', tmp_value

    def __ge__(self, value):
        if not value:
            raise ConditionNotImplemented()
        tmp_value = prepare_value(value)
        return '{}.{}'.format(self.model.table_name, self.name), '>=', tmp_value

    def like(self, value):
        if not isinstance(value, str):
            raise ConditionNotImplemented()
        tmp_value = '%{}%'.format(value)
        return '{}.{}'.format(self.model.table_name, self.name), ' LIKE ', tmp_value

    def not_like(self, value):
        if not isinstance(value, str):
            raise ConditionNotImplemented()
        tmp_value = '%{}%'.format(value)
        return '{}.{}'.format(self.model.table_name, self.name), ' NOT LIKE ', tmp_value
