from redis_client import RedisClient, RedisException
import functools
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
        return_invalidator = 'invalidator' in options
        def cache_inside(fn, **kwargs):
            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                fn_hash = self._generate_cache_key(fn, args, kwargs, **options)
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
                        cache_hit = pickle.loads(cache_request)
                        if return_invalidator:
                            return cache_hit, functools.partial(
                                self.invalidate_cache, fn_hash)
                        else:
                            return cache_hit
                except RedisException:
                    # If Redis fails, just execute the function as normal
                    if return_invalidator:
                        return fn(*args, **kwargs), None
                    else:
                        return fn(*args, **kwargs)
                if return_invalidator:
                    return \
                        ret, functools.partial(self.invalidate_cache, fn_hash)
                else:
                    return ret
            return wrapper
        return cache_inside

    def invalidate_cache(self, cache_key):
        self.redis_client.delete(cache_key)

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

    def _generate_cache_key(self, fn, fn_args=None, fn_kwargs=None, **options):
        signature_generator = options.get(
            'signature_generator',
            self._default_signature_generator)

        if not hasattr(signature_generator, '__call__'):
            raise TypeError(
                "signature_generator must be a callable function")

        fn_args = fn_args or []
        fn_kwargs = fn_kwargs or {}
        fn_name = fn.__name__
        signature = signature_generator(fn_args, **fn_kwargs)
        fn_hash = str(hash(fn_name + signature))
        return fn_hash


def _argument_to_string(arg):
    if arg.__class__.__module__ == '__builtin__':
        return str(arg)

    # for backwards-compatibility: if the object defines a custom __str__ method
    # use it instead of the default approach based on the class-name
    string_representation = str(arg)
    if string_representation != object.__str__(arg):
        return string_representation

    instance_namespace = arg.__class__.__name__
    try:
        # if the object has state, also include that in the cache key so that if
        # the object's state changes, we don't hit the cache for the old state
        # and risk returning an out-of-date value
        # note that we need to do this recursively in case the object's state is
        # made up of other stateful objects which could also change and require
        # us to invalidate the cache
        instance_state = sorted((field, _argument_to_string(value))
                                for field, value in vars(arg).items())
    except TypeError:
        # some non-primitive types (e.g., defaultdict) don't have a __dict__ so
        # we need to have a fall-back for the vars call above
        instance_state = string_representation

    return '{}_{}'.format(instance_namespace, instance_state)
