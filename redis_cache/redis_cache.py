from redis_client import RedisClient, RedisException
import pickle

# Default expiration time for a cached object if not given in the decorator
DEFAULT_EXPIRATION = 60


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

                signature_generator = options.get(
                    'signature_generator',
                    self._default_signature_generator
                )

                if not hasattr(signature_generator, '__call__'):
                    raise TypeError(
                        "signature_generator must be a callable function"
                    )

                signature = signature_generator(args, **kwargs)

                fn_hash = str(hash(fn_name + signature))
                try:
                    cache_request = self.redis_client.get(fn_hash)
                    if cache_request is '':
                        # Cache miss
                        ret = fn(*args, **kwargs)
                        pickled_ret = pickle.dumps(ret)
                        self.redis_client.setex(
                            fn_hash, pickled_ret, options.get(
                                'expiration', DEFAULT_EXPIRATION)
                        )
                    else:
                        # Cache hit
                        return pickle.loads(cache_request)
                except RedisException:
                    # If Redis fails, just execute the function as normal
                    return fn(*args, **kwargs)
                return ret
            return wrapper
        return cache_inside

    def _default_signature_generator(*args, **kwargs):
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
