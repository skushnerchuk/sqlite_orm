from sqlite_orm.database import SQLiteDataBase
from sqlite_orm.columns import Column, ForeignKey
from sqlite_orm import BaseModel


class Category(BaseModel):
    __table_name__ = 'categories'

    id = Column('INTEGER', primary_key=True, autoincrement=True)
    name = Column('varchar(100)', not_null=True, default_value='New category')


class Product(BaseModel):
    __table_name__ = 'products'

    id = Column('INTEGER', primary_key=True, autoincrement=True)
    name = Column('varchar(100)', not_null=True, default_value='OK')
    category = Column('INTEGER', foreign_key=ForeignKey(Category, Category.id), not_null=True)


db = SQLiteDataBase('data.db')

# В данной реализации важен порядок регистрации моделей
# Если таблица имеет внешний ключ на другую, то та, на которую ссылаются,
# должна быть зарегистрирована раньше
db.register_model(Category, True)
db.register_model(Product, True)

id = Category.query.insert(name='Новая категория').execute().last_id
Product.query.insert(name='New product', category=id).execute()
db.commit()

product = Product.query.select().first()
print('id={}'.format(product(Product.id)))
print('name={}'.format(product(Product.name)))
print('category={}'.format(product(Category.name)))
product = Product.query.select().first()
Product.query.update(name='1234567890').filter(Product.id == product(Product.id)).execute()
db.commit()
