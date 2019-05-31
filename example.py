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
db.connect()

# В данной реализации важен порядок регистрации моделей
# Если таблица имеет внешний ключ на другую, то та, на которую ссылаются,
# должна быть зарегистрирована раньше
db.register_model(Category, True)
db.register_model(Product, True)


id = Category.query.insert(
    {
        Category.name: 'Новая категория'
    }
).exec().last_id

Product.query.insert(
    {
        Product.name: 'New product',
        Product.category: id
    }
).exec()

db.commit()

a = Product.query.select().first()

if a:
    id = a.get_value(Product.table_name, Product.id)
    Product.query.update(
        {
            Product.name: 'Brand new product',
        }
    ).filter('id={}'.format(id)).exec()
    db.commit()
