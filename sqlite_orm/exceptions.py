class IncorrectWhereOrderError(Exception):
    pass


class TableNotExistsError(Exception):
    pass


class ColumnNotExistsError(Exception):
    pass


class NotNullConstraintError(Exception):
    pass


class ConditionNotImplemented(Exception):
    pass


class IncorrectArgumentsError(Exception):
    pass
