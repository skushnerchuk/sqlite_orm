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
product = Product.query.select(Product.id, Product.name, Category.name).filter(Product.id == 5).first()
id = a(Product.id) # or a.get(Product.id)
name = a(Product.name) # or a.get(Product.name)
category_name = a(Category.name) # or a.get(Category.name)
...
products = Product.query.select().filter(Product.id == 5).or_(Product.id == 4).or_(Product.id == 3).all()
for product in products:
    id = product(Product.id) # or a.get(Product.id)
    name = product(Product.name) # or a.get(Product.name)
    category_name = product(Category.name) # or a.get(Category.name)
```

Вставка и обновление
```python
id = Category.query.insert(name='Новая категория').execute().last_id
db.commit()
...
Product.query.update(name='New name', category=1).filter(Product.id == product(Product.id)).execute()
db.commit()
```
