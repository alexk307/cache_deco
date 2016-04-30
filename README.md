# redis_cache
Implements high level function caching to Redis with a decorator


# Usage

## Setup
```
from redis_cache import RedisCache
r = RedisCache('localhost', 6379)
```

## Cache indefinitely
```
@r.cache():
def my_method(a, b, c):
  return a ** b ** c
```

## Cache with an expiration
```
@r.cache(expiration=100):
def my_method(a, b, c):
  return a ** b ** c
```
