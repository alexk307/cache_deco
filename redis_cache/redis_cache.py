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
        parsed_args = ",".join(map(_argument_to_string, args[1]))
        # Join keyword arguments together with `=` and commas
        parsed_kwargs = ",".join(
            map(lambda x: '%s=%s' % (x, str(kwargs[x])), kwargs)
        )
        # Filter out empty params
        parsed = filter(
            lambda x: x != '', [parsed_args, parsed_kwargs]
        )
        return ','.join(parsed)


def _argument_to_string(arg):
    if arg.__class__.__module__ == '__builtin__':
        return str(arg)

    # for backwards-compatibility: if the object defines a custom __str__ method
    # use it instead of the default approach based on the class-name
    string_representation = str(arg)
    if string_representation != object.__str__(arg):
        return string_representation

    try:
        instance_namespace = arg.__class__.__name__
        instance_state = sorted((field, _argument_to_string(value))
                                for field, value in vars(arg).items())
        return '{}_{}'.format(instance_namespace, instance_state)

    except TypeError:
        # some non-primitive types (e.g., defaultdict) don't have a __dict__ so
        # we need to have a fall-back
        return str(arg)
