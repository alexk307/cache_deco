from redis_client import RedisClient


class RedisCache(object):
    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.redis_client = RedisClient(self.address, self.port)

    def cache(self, **options):
        """
        Cache decorator
        """
        def cache_inside(fn, **kwargs):
            def wrapper(*args, **kwargs):
                fn_name = fn.__name__
                signature = self._get_signature(args, **kwargs)
                fn_hash = str(hash(fn_name + signature))
                cache_request = self.redis_client.get(fn_hash)
                if cache_request is '':
                    # Cache miss
                    ret = fn(*args, **kwargs)
                    if 'expiration' in options:
                        self.redis_client.setex(
                            fn_hash, ret, options.get('expiration')
                        )
                    else:
                        self.redis_client.set(fn_hash, ret, **options)

                    # Add the hash to the fn_name and tags lookup tables
                    self.redis_client.sadd(fn_name, fn_hash)

                    if 'tags' in options:
                        tags = options.get('tags')
                        for tag in tags:
                            self.redis_client.sadd(tag, fn_hash)

                else:
                    # Cache hit
                    return cache_request
                return ret
            return wrapper
        return cache_inside

    def get_tag_cache(tag):
        return self.redis_client.smembers(tag)

    def reset_tag_cache(tag):
        caches = self.redis_client.smembers(tag)
        self.redis_client.delete(caches)
        self.redis_client.delete(tag)

    def get_function_cache(fn_name):
        self.get_tag_cache(fn_name)

    def reset_function_cache(fn_name):
        self.reset_tag_cache(fn_name)

    def get_function_instance_cache():
        raise NotImplemented()

    def reset_function_instance_cache():
        raise NotImplemented()

    def _get_signature(*args, **kwargs):
        """
        Gets the signature of the decorated method
        :return: arg1,...argn,kwarg1=kwarg1,...kwargn=kwargn
        """
        # Join regular arguments together with commas
        parsed_args = ",".join(map(lambda x: str(x), args[1]))
        # Join keyword arguments together with `=` and commas
        parsed_kwargs = ",".join(
            map(lambda x: '%s=%s' % (x, str(kwargs[x])), kwargs)
        )
        # Filter out empty params
        parsed = filter(
            lambda x: x != '', [parsed_args, parsed_kwargs]
        )
        return ','.join(parsed)
