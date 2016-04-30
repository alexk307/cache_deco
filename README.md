# redis_cache
Implements high level function caching to Redis with a decorator


# Usage
```
from redis_cache import RedisCache
r = RedisCache('localhost', 6379)

@r.cache:
def my_method(a, b, c):
  return a ** b ** c
```
