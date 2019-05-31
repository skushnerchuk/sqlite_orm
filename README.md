### Элементарный пример реализации ORM для СУБД SQLite

Для разработки требуется python версии не ниже 3.6 

#### Примеры использования

Описание моделей данных
```python
class Category(BaseModel):

    __table_name__ = 'categories'

    id = Column('INTEGER', primary_key=True, autoincrement=True)
    name = Column('varchar(100)', not_null=True, default_value='New category')


class Product(BaseModel):

    __table_name__ = 'products'

    id = Column('INTEGER', primary_key=True, autoincrement=True)
    name = Column('varchar(100)', not_null=True, default_value='OK')
    category = Column('INTEGER', foreign_key=ForeignKey(Category, Category.id), not_null=True)
```

Выборка:
```python
products = Product.query.select().first()
products = Product.query.select().filter('{}.name LIKE "%Brand%"'.format(Product.table_name)).all()
```

Вставка и обновление
```python
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
```