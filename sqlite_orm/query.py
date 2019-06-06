from sqlite3 import DatabaseError

from . columns import Column
from . exceptions import TableNotExistsError, ColumnNotExistsError, NotNullConstraintError, \
       IncorrectWhereOrderError, IncorrectArgumentsError


class Row(object):
    """Класс - представление строки выборки"""

    def __init__(self, fields, table_name):
        self.__class__.__name__ = table_name + "_row"

        # Во избежание конфликта имен поля в выдачу попадают в формате
        # имя_таблицы.имя_поля
        for name, value in fields:
            setattr(self, name, value)

    def get(self, item):
        if not isinstance(item, Column):
            raise IncorrectArgumentsError()
        attr_name = item.model.table_name + '_' + item.name
        return getattr(self, attr_name)

    def __call__(self, item):
        return self.get(item)


class Query:
    """Основной класс, служащий для работы с данными"""

    def __init__(self, cursor, model):
        self.cursor = cursor
        self.model = model
        self.sql = ''
        self.result_fields = []
        self.select_fields = []
        self.args = []

    @staticmethod
    def create_select_fields(table_name, fields):
        cleaned_fields = [fld for fld in fields if fld.model.table_name == table_name]
        pattern = '{tn}.{fn} as {tn}_{fn}'
        return [pattern.format(tn=table_name, fn=fld.name) for fld in cleaned_fields]

    def left_join(self, fk, fields):
        """
        Построение LEFT JOIN по указанному внешнему ключу
        :param fk: внешний ключ (объект ForeignKey)
        :param fields: список полей, переданный в метод select()
        """
        join_pattern = ' LEFT JOIN {} ON {}.{} = {}.{}'
        table_name = self.model.table_name
        joined_table = fk[1].external_model.table_name
        link_field = fk[1].link_field.name
        if fields:
            self.select_fields.extend(self.create_select_fields(joined_table, fields))
            self.result_fields.extend(['{}_{}'.format(joined_table, fld.name) for fld in fields if fld.model.table_name == joined_table])
        else:
            # В запрос попадут все поля модели, привязанной по внешнему ключу
            columns = fk[1].external_model.get_columns()
            self.select_fields.extend(self.create_select_fields(joined_table, columns))
            self.result_fields.extend(['{}_{}'.format(joined_table, fld.name) for fld in columns])
        return join_pattern.format(joined_table, table_name, fk[0], joined_table, link_field)

    def select(self, *fields):
        """Выборка данных"""
        self.args.clear()
        select_pattern = 'SELECT {} FROM {} {}'
        table_name = self.model.table_name
        # Если список полей не пуст, формируем запрос только из них
        # Иначе в итог попадут все поля модели
        if fields:
            # Это поля которые попадут в текст запроса
            self.select_fields = self.create_select_fields(table_name, fields)
            # Это поля по которым мы потом будем строить строки ответа
            self.result_fields = ['{}_{}'.format(table_name, fld.name) for fld in fields if fld.model.table_name == table_name]
        else:
            self.select_fields = self.create_select_fields(table_name, self.model.get_columns())
            self.result_fields = ['{}_{}'.format(table_name, fld) for fld in self.model.get_column_names()]
        # Делаем автоматическое присоединение всех таблиц по внешним ключам модели
        fk_list = self.model.get_fk()
        joins = []
        for fk in fk_list:
            joins.append(self.left_join(fk, fields))
        fields = ', '.join(self.select_fields)
        self.sql = select_pattern.format(fields, self.model.table_name, ', '.join(joins))
        return self

    def filter(self, *args):
        """
        Старт формирования условия. Если запрос должен содержать секцию WHERE - условия
        надо начинать строить этим методом
        """
        if len(args) > 1:
            raise IncorrectArgumentsError()
        self.sql += " WHERE {}{}?".format(args[0][0], args[0][1])
        self.args.append(args[0][2])
        return self

    def and_(self, *args):
        """Добавление условия И"""
        if 'WHERE' not in self.sql:
            raise IncorrectWhereOrderError()
        if len(args) > 1:
            raise IncorrectArgumentsError()
        self.sql += " AND {}{}?".format(args[0][0], args[0][1])
        self.args.append(args[0][2])
        return self

    def or_(self, *args):
        """Добавление условия ИЛИ"""
        if 'WHERE' not in self.sql:
            raise IncorrectWhereOrderError()
        if len(args) > 1:
            raise IncorrectArgumentsError()
        self.sql += " OR {}{}?".format(args[0][0], args[0][1])
        self.args.append(args[0][2])
        return self

    def order_by(self, criteria):
        """Установка порядка сортировки"""
        self.sql += " ORDER BY {}".format(criteria)
        return self

    def all(self):
        self.execute()
        rows = self.cursor.fetchall()
        if not rows:
            return []
        # Если было указано ограничение по полям в SELECT, то выводим только их, иначе
        # все поля модели
        if isinstance(self.result_fields, list):
            return [Row(zip(self.result_fields, fields), self.model.table_name) for fields in rows]
        else:
            return [Row(zip(self.model.get_column_names(), fields), self.model.table_name) for fields in rows]

    def first(self):
        # Получение первой записи в наборе
        self.execute()
        if isinstance(self.result_fields, list):
            properties = self.result_fields
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

    def update(self, *args, **kwargs):
        """
        Обновление записей
        """
        self.args.clear()
        tablename = self.model.table_name
        pairs = []
        for key, value in kwargs.items():
            pairs.append('{}=?'.format(key))
            self.args.append(value)
        self.sql = 'UPDATE {} SET {}'.format(tablename, ', '.join(pairs))
        return self

    def insert(self, *args, **kwargs):
        """
        Добавление записи
        """
        self.args.clear()
        tablename = self.model.table_name
        fields = []
        values = []
        for key, value in kwargs.items():
            fields.append(key)
            values.append('?')
            self.args.append(value)
        self.sql = 'INSERT INTO {} ({}) VALUES ({});'.format(tablename, ', '.join(fields), ', '.join(values))
        return self

    def delete(self):
        """
        Удаление записей
        Условия удаления следует задавать методом filter(). Если этот не будет вызван,
        удалятся все записи в таблице
        """
        self.args.clear()
        tablename = self.model.table_name
        self.sql = 'DELETE FROM {}'.format(tablename)
        return self

    def execute(self):
        """
        Выполнение сформированного запроса. Следует использовать после методов:
        update(), insert(), delete()
        Для выборки данных следует использовать методы all(), first()
        """
        try:
            self.cursor.execute(self.sql, tuple(self.args))
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
