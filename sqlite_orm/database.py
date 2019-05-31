import sqlite3

from . query import Query, Column
from . utils import prepare_value


class SQLiteDataBase:
    """Класс базы"""

    def __init__(self, db_name):
        """Для создания базы в памяти db_name должно быть :memory:"""
        self.db_name = db_name
        self.db = None
        self.cursor = None
        self.models = []

    def connect(self):
        """Подключение к базе данных. Если файл не существует - он будет создан"""
        self.db = sqlite3.connect(self.db_name)
        self.cursor = self.db.cursor()
        # Включаем работу с внешними ключами, иначе ON DELETE/UPDATE не будут работать
        self.cursor.execute('PRAGMA foreign_keys = ON')

    def register_model(self, model, create_on_register=False):
        """Регистрация модели данных"""
        for key, value in model.__dict__.items():
            # Создаем свойство name для каждого столбца, равного имени его переменной
            if isinstance(value, Column):
                value.name = key

        self.models.append(model)
        model.query = Query(self.cursor, model)
        # Если надо - создаем таблицу
        if create_on_register:
            self.create_table(model)

    @staticmethod
    def describe_column_as_sql(column):
        """
        Возврат описания столбца в SQL
        Используется для формирования SQL-запроса создания таблицы
        """
        sql = '{} {}'.format(column.name, column.type)
        if column.default_value:
            sql += ' DEFAULT {}'.format(prepare_value(column.default_value))
        if column.not_null:
            sql += ' NOT NULL'
        if column.primary_key:
            sql += ' PRIMARY KEY'
        if column.autoincrement:
            sql += ' AUTOINCREMENT'
        return sql

    @staticmethod
    def describe_fk_as_sql(name, fk):
        """
        Возврат описания внешнего ключа в SQL
        Используется для формирования SQL-запроса создания таблицы
        """
        sql = 'FOREIGN KEY ({}) REFERENCES {}({}) on update cascade on delete cascade'
        return sql.format(name, fk.external_model.table_name, fk.link_field.name)

    def create_table(self, model):
        """Создание таблицы по ее модели"""
        columns = [self.describe_column_as_sql(i) for i in model.get_columns()]

        fk = [self.describe_fk_as_sql(name, fk) for name, fk in model.get_fk()]
        columns.extend(fk)
        sql = 'CREATE TABLE IF NOT EXISTS {} ({})'.format(model.table_name, ', '.join(columns))
        self.cursor.execute(sql)

    def drop_table(self, table_name):
        """Удаление таблицы"""
        sql = "DROP table {}".format(table_name)
        self.cursor.execute(sql)

    def commit(self):
        """Коммит всех изменений в базу"""
        self.db.commit()

    def rollback(self):
        """Откат всех изменений"""
        self.db.rollback()
