# redis_cache ![](https://travis-ci.org/alexk307/redis_cache.svg?branch=master)
Implements high level function caching to Redis with a decorator


# Usage

## Setup
```python
from redis_cache import RedisCache
r = RedisCache('localhost', 6379)
```

## Cache indefinitely
```python
@r.cache()
def my_method(a, b, c):
  return a ** b ** c
```

<<<<<<< Updated upstream
## Cache with an expiration
```python
@r.cache(expiration=100)
def my_method(a, b, c):
  return a ** b ** c
```
