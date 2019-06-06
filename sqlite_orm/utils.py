class ClassPropertyDescriptor:

    def __init__(self, fget, fset=None):
        self.fget = fget
        self.fset = fset

    def __get__(self, obj, class_=None):
        if class_ is None:
            class_ = type(obj)
        return self.fget.__get__(obj, class_)()

    def __set__(self, obj, value):
        if not self.fset:
            raise AttributeError("can't set attribute")
        type_ = type(obj)
        return self.fset.__get__(obj, type_)(value)

    def setter(self, func):
        if not isinstance(func, (classmethod, staticmethod)):
            func = classmethod(func)
        self.fset = func
        return self


def class_property(func):
    """Декоратор для создания свойств класса"""
    if not isinstance(func, (classmethod, staticmethod)):
        func = classmethod(func)

    return ClassPropertyDescriptor(func)


def prepare_value(val):
    """Подготовка значения для запроса."""
    if isinstance(val, str):
        return '"{}"'.format(val)
    elif not val:
        return 'NULL'
    return val
