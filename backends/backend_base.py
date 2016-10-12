

class Backend(object):

    def __init__(self, *args, **kwargs):
        pass

    def get_cache(self, key):
        raise NotImplementedError()

    def set_cache(self, key, value):
        raise NotImplementedError()

    def set_cache_and_expire(self, key, value, expiration):
        raise NotImplementedError()

    def invalidate_key(self, key):
        raise NotImplementedError()


class BackendException(Exception):
    pass
