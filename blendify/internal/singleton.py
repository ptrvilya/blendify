class Singleton(type):
    """An implementation of the singleton metaclass.
    This is a metaclass which allows only one instance of the class to exist.
    Useful to handle an object which should not be duplicated (such as Blender scene).
    """
    _instances = dict()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
            return cls._instances[cls]
        else:
            raise RuntimeError(f"Only one instance of class {cls.__name__} is allowed")
