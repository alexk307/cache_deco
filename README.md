# cache_deco [![Build Status](https://travis-ci.org/alexk307/redis_cache.svg?branch=master)](https://travis-ci.org/alexk307/cache_deco) [![Coverage Status](https://coveralls.io/repos/github/alexk307/redis_cache/badge.svg?branch=master)](https://coveralls.io/github/alexk307/redis_cache?branch=master)

Implements high level function caching to any backend with a decorator

# Install
`pip install redis_cache_decorator`

# Usage

## Setup
```python
from cache_deco import Cache
from backends.redis.redis_backend import RedisBackend
# Create your cache backend
redis = RedisBackend('localhost', 6379)
# Use this backend as your cache
c = Cache(redis)
```

## Cache

```python
@c.cache()
def my_method(a, b, c):
  return a ** b ** c
```

### Options
`expiration`: Number of seconds to keep the result in the cache. Defaults to 60 seconds when not specified.

e.g.
```python
@c.cache(expiration=100)
def my_method():
  ...
```

`signature_generator`: Callable function that generates the signature to cache on. The default signature generator will be used if not specified.

e.g.

```python
def sig_gen(*args, **kwargs):
  return "?".join(args)
  
@c.cache(signature_generator=sig_gen)
def my_method():
  ...
```

`invalidator`: Boolean to determine whether or not to return a cache invalidating function

e.g.
```python
@c.cache(invalidator=True)
def my_method():
    ...
```

Now when you call `my_method`, it will return two values. The first value is the cached return if a cache hit occurs, otherwise it's the return value from executing the function.
The second value is a callable function to invalidate the cache.

```python
return_value, invalidator = my_method()
```

To invalidate the cached return, just call the invalidator:

```python
invalidator()
```
# Custom Backends
You can use any backend for the cache by implementing the [base class](https://github.com/alexk307/cache_deco/blob/master/backends/backend_base.py)

# Contributing
Check for any open issues, or open one yourself! All contributions are appreciated.

# Tests
`nosetests`
