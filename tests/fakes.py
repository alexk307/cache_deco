class FakeRedisClient(object):
    """
    In-memory fake implementation of RedisClient
    """
    def __init__(self):
        self._cache = {}

    def get(self, key):
        return self._cache.get(key, '')

    def set(self, key, value, **kwargs):
        self._cache[key] = value
        return ''

    def setex(self, key, value, expiration):
        self._cache[key] = value
        return ''
