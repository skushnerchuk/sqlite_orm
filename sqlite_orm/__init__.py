import inspect

from . utils import class_property
from . columns import Column, ForeignKey


class BaseModel:
    """Основной класс модели данных"""

    __table_name__ = ''

    @class_property
    def table_name(cls):
        """Имя таблицы. Если не задано явно, создается из имени класса"""
        if cls.__table_name__:
            return cls.__table_name__
        return cls.__name__.lower()

    @classmethod
    def get_column_names(cls):
        """Возврат имен полей модели"""
        members = inspect.getmembers(cls)
        return [column[0] for column in members if isinstance(column[1], Column)]

    @classmethod
    def get_columns(cls):
        """Получение столбцов модели"""
        members = inspect.getmembers(cls)
        return [column[1] for column in members if isinstance(column[1], Column)]

    @classmethod
    def get_fk(cls):
        """Получение всех внешних ключей модели"""
        return [(c.name, c.foreign_key) for c in cls.get_columns() if isinstance(c.foreign_key, ForeignKey)]
