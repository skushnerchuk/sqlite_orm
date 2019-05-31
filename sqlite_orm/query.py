from sqlite3 import DatabaseError


from . columns import Column
from . utils import prepare_value


class IncorrectWhereOrderError(Exception):
    pass


class TableNotExistsError(Exception):
    pass


class ColumnNotExistsError(Exception):
    pass


class NotNullConstraintError(Exception):
    pass


class Row(object):
    """Класс - представление строки выборки"""

    def __init__(self, fields, table_name):
        self.__class__.__name__ = table_name + "_row"

        # Во избежание конфликта имен поля в выдачу попадают в формате
        # имя_таблицы.имя_поля
        for name, value in fields:
            setattr(self, name, value)

    def get_value(self, table, name):
        return getattr(self, '{}.{}'.format(table, name.name))


class Query:
    """Основной класс, служащий для работы с данными"""

    def __init__(self, cursor, model):
        self.cursor = cursor
        self.model = model
        self.sql = ''
        self.fields = []

    def select(self, fields=None):
        """Выборка данных"""
        table_name = self.model.table_name

        # Если список полей не пуст, формируем запрос только из них
        # Иначе в итог попадут все поля модели
        if fields:
            self.fields = ['{}.{}'.format(table_name, fld.name) for fld in fields]
        else:
            self.fields = ['{}.{}'.format(table_name, fld) for fld in self.model.get_column_names()]

        # Делаем автоматическое присоединение всех таблиц по внешним ключам модели
        fk_list = self.model.get_fk()
        joins = []
        for fk in fk_list:
            joined_table = fk[1].external_model.table_name
            # В запрос попадут все поля модели, привязанной по внешнему ключу
            self.fields.extend(['{}.{}'.format(joined_table, fld) for fld in fk[1].external_model.get_column_names()])
            joins.append(' LEFT JOIN {} ON {}.{} = {}.{}'.format(joined_table, table_name, fk[0], joined_table, fk[1].link_field.name))
        criteria = ', '.join(self.fields)
        self.sql = 'SELECT {} FROM {} {}'.format(criteria, self.model.table_name, ', '.join(joins))

        return self

    def filter(self, criteria):
        """
        Старт формирования условия. Если запрос должен содержать секцию WHERE - условия
        надо начинать строить этим методом
        """
        self.sql += " WHERE {} ".format(criteria)
        return self

    def and_(self, criteria):
        """Добавление условия И"""
        if 'WHERE' not in self.sql:
            raise IncorrectWhereOrderError()
        self.sql += " AND {}".format(criteria)
        return self

    def or_(self, criteria):
        """Добавление условия ИЛИ"""
        if 'WHERE' not in self.sql:
            raise IncorrectWhereOrderError()
        self.sql += " OR {}".format(criteria)
        return self

    def order_by(self, criteria):
        """Установка порядка сортировки"""
        self.sql += " ORDER BY {}".format(criteria)
        return self

    def all(self):
        self.exec()
        rows = self.cursor.fetchall()
        if not rows:
            return []
        # Если было указано ограничение по полям в SELECT, то выводим только их, иначе
        # все поля модели
        if isinstance(self.fields, list):
            return [Row(zip(self.fields, fields), self.model.table_name) for fields in rows]
        else:
            return [Row(zip(self.model.get_column_names(), fields), self.model.table_name) for fields in rows]

    def first(self):
        # Получение первой записи в наборе
        self.exec()
        if isinstance(self.fields, list):
            properties = self.fields
        else:
            properties = self.model.get_column_names()
        rows = self.cursor.fetchone()
        if rows:
            return Row(zip(properties, rows), self.model.table_name)
        return None

    def limit(self, criteria):
        """Установка ограничения количества записей"""
        self.sql += " LIMIT %s" % criteria
        return self

    def update(self, params):
        """
        Обновление записей
        В params задается словарь с указанием обновляемых данных, например:
        {
           Product.name: 'New product',
           Product.category: id
        }
        где Product - это модель типа BaseModel, после точки - имя поля модели типа Column
        Условия обновления следует задавать методом filter(). Если этот не будет вызван,
        обновятся все записи в таблице
        """
        pairs = []
        tablename = self.model.table_name
        for key, value in params.items():
            if not isinstance(key, Column):
                continue
            pairs.append('{}={}'.format(key.name, prepare_value(value)))
        self.sql = 'UPDATE {} SET {}'.format(tablename, ', '.join(pairs))
        return self

    def insert(self, params):
        """
        Добавление записи
        В params задается словарь с указанием данных, например:
        {
           Product.name: 'New product',
           Product.category: id
        }
        где Product - это модель типа BaseModel, после точки - имя поля модели типа Column
        """
        tablename = self.model.table_name
        fields = []
        values = []
        for key, value in params.items():
            if not isinstance(key, Column):
                continue
            fields.append(key.name)
            values.append(prepare_value(value))
        self.sql = 'INSERT INTO {} ({}) VALUES ({});'.format(
            tablename,
            ', '.join(fields),
            ', '.join(values)
        )
        return self

    def delete(self):
        """
        Удаление записей
        Условия удаления следует задавать методом filter(). Если этот не будет вызван,
        удалятся все записи в таблице
        """
        tablename = self.model.table_name
        self.sql = 'DELETE FROM {}'.format(tablename)
        return self

    def exec(self):
        """
        Выполнение сформированного запроса. Следует использовать после методов:
        update(), insert(), delete()
        Для выборки данных следует использовать методы all(), first()
        """
        try:
            self.cursor.execute(self.sql)
            return self
        except DatabaseError as ex:
            self.process_error(ex)

    @property
    def last_id(self):
        """
        Возвращает последнее значение автоинкрементного поля
        Удобно для мгновенного получения значения первичного ключа вставленной записи,
        если этот ключ - поле типа INTEGER с автоинкрементом
        """
        return self.cursor.execute('SELECT last_insert_rowid()').lastrowid

    @staticmethod
    def process_error(ex):
        """Базовая обработка ошибок"""
        msg = ex.args[0].lower()
        if 'no such table' in msg:
            raise TableNotExistsError(msg)
        if 'no such column' in msg:
            raise ColumnNotExistsError(msg)
        if 'not null constraint failed' in msg:
            raise NotNullConstraintError(msg)
        raise ex
