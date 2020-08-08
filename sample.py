from types import MethodType, FunctionType, LambdaType

class MetaClass(type):
    def __new__(cls, name, bases, attr):
        def is_excutable(v):
            return isinstance(v, (MethodType, FunctionType, LambdaType))

        target = attr['target']

        for k, v in attr.items():
            if is_excutable(v) and getattr(v, '__flag', False):
                target.append((getattr(v, '__command'), v))

        klass = type.__new__(cls, name, bases, attr)
        klass.target = target
        return klass


def decorator(command=''):
    def decorate(func):
        setattr(func, '__flag', True)
        setattr(func, '__command', command)
        return func
    return decorate

class Klass(metaclass=MetaClass):
    target = []

    @decorator('command_name')
    def test_method(self):
        pass

print('Klass.target:', Klass.target)