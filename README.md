# redis_cache [![Build Status](https://travis-ci.org/alexk307/redis_cache.svg?branch=master)](https://travis-ci.org/alexk307/redis_cache)
Implements high level function caching to Redis with a decorator

# Install
`pip install redis_cache_decorator`

# Usage

## Setup
```python
from redis_cache.redis_cache import RedisCache
r = RedisCache('localhost', 6379)
```

## Cache

```python
@r.cache()
def my_method(a, b, c):
  return a ** b ** c
```

### Options
`expiration`: Number of seconds to keep the result in the cache. Defaults to 60 seconds when not specified.

e.g.
```python
@r.cache(expiration=100)
def my_method():
  ...
```

`signature_generator`: Callable function that generates the signature to cache on. The default signature generator will be used if not specified.

e.g.

```python
def sig_gen(*args, **kwargs):
  return "?".join(args)
  
r.cache(signature_generator=sig_gen)
def my_method():
  ...
```

# Contributing
Please do!

# Tests
`nosetests`

# Note
When implementing the caching decorator on methods with objects as parameters, please be sure to override the `__str__` method on that object. The default behavior for most objects in Python is to return a string such as `<Object instance at 0x12345678>`. Since this is in the signature of the function, it will cache using that address in memory and will result in cache misses everytime that object is changed. This is especially apparent while caching class methods since the first paramter is always the object itself (`self`).
