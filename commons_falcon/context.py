import threading

__all__ = ('get_context', )
__ctx = None

def get_context():
    global __ctx 
    if __ctx is None:
        __ctx = threading.local()
    return __ctx