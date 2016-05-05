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
`expiration`: Number of seconds to keep the result in the cache

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
