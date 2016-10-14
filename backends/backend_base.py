class Backend(object):
    """
    Generic backend base class. Provides an interface to use the cache
    with any backend
    """

    def __init__(self, *args, **kwargs):
        pass

    def get_cache(self, key):
        """
        Gets the given key from the cache backend
        :param key: The cache key to get
        :return: The value in the cache in the case of a cache hit,
        otherwise None
        """
        raise NotImplementedError()

    def set_cache(self, key, value):
        """
        Sets the given key/value pair in the cache backend
        :param key: The cache key
        :param value: The cache value
        :return: Response from cache backend
        """
        raise NotImplementedError()

    def set_cache_and_expire(self, key, value, expiration):
        """
        Sets the key/value pair in the cache backend with an expiration TTL
        :param key: The cache key
        :param value: The cache value
        :param expiration: The time to live (ttl) in seconds
        :return: Response from cache backend
        """
        raise NotImplementedError()

    def invalidate_key(self, key):
        """
        Removes the key from the cache
        :param key: The cache key
        :return: Response from cache Backend
        """
        raise NotImplementedError()


class BackendException(Exception):
    """
    Cache backend exception
    """
    pass
