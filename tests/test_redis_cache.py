from redis_cache.redis_cache import \
    RedisCache, RedisException, DEFAULT_EXPIRATION
from unittest import TestCase
from mock import Mock, patch
from inputs import SimpleObject
import collections
import pickle


class TestRedisCache(TestCase):
    """
    Test cases for redis_cache.py
    """

    def setUp(self):
        self.address = '10.10.10.10'
        self.port = 2345

    @patch('redis_cache.redis_cache.RedisClient')
    def test_cache_miss(self, mock_client_object):
        """
        Tests a cache miss
        """
        mock_client = Mock()
        # Simulates a cache miss
        mock_client.get.return_value = ''
        mock_client_object.return_value = mock_client
        redis_cache = RedisCache(self.address, self.port)

        # Create a function with the decorator
        @redis_cache.cache()
        def test_function(a):
            return a

        # Call that function
        test_param = 'input'
        function_response = test_function(test_param)

        mock_client_object.assert_called_once_with(self.address, self.port)
        expected_hash = str(hash('test_function' + test_param))
        mock_client.get.assert_called_once_with(expected_hash)
        mock_client.setex.assert_called_once_with(
            expected_hash, pickle.dumps(test_param), DEFAULT_EXPIRATION)

    @patch('redis_cache.redis_cache.RedisClient')
    def test_cache_miss_kwargs(self, mock_client_object):
        """
        Tests a cache miss against a function with kwargs
        """
        mock_client = Mock()
        # Simulates a cache miss
        mock_client.get.return_value = ''
        mock_client_object.return_value = mock_client
        redis_cache = RedisCache(self.address, self.port)

        # Create a function with the decorator
        @redis_cache.cache()
        def test_function(a, b, c=None, d=None):
            return a

        # Call that function
        test_a = 'input'
        test_b = 'b'
        test_c = True
        test_d = False
        function_response = test_function(test_a, test_b, c=test_c, d=test_d)

        mock_client_object.assert_called_once_with(self.address, self.port)
        expected_signature = \
            '%s,%s,c=%s,d=%s' % (test_a, test_b, str(test_c), str(test_d))
        expected_hash = str(hash('test_function' + expected_signature))
        mock_client.get.assert_called_once_with(expected_hash)
        mock_client.setex.assert_called_once_with(
            expected_hash, pickle.dumps(test_a), DEFAULT_EXPIRATION)

    @patch('redis_cache.redis_cache.RedisClient')
    def test_cache_miss_expiration(self, mock_client_object):
        """
        Tests a cache miss with an expiration given
        """
        test_param = 'cache hit test'
        ttl = 100
        mock_client = Mock()
        # Simulates a cache hit
        mock_client.get.return_value = ''
        mock_client_object.return_value = mock_client
        redis_cache = RedisCache(self.address, self.port)

        # Create a function with the decorator
        @redis_cache.cache(expiration=ttl)
        def test_function(a):
            return a

        # Call that function
        function_response = test_function(test_param)
        expected_hash = str(hash('test_function' + test_param))
        mock_client_object.assert_called_once_with(self.address, self.port)
        mock_client.get.assert_called_once_with(expected_hash)
        mock_client.setex.assert_called_once_with(
            expected_hash, pickle.dumps(test_param), ttl)
        self.assertEqual(mock_client.set.call_count, 0)

    @patch('redis_cache.redis_cache.RedisClient')
    def test_cache_hit(self, mock_client_object):
        """
        Tests a cache hit
        """
        test_param = 'cache hit test'
        mock_client = Mock()
        # Simulates a cache hit
        mock_client.get.return_value = pickle.dumps(test_param)
        mock_client_object.return_value = mock_client
        redis_cache = RedisCache(self.address, self.port)

        # Create a function with the decorator
        @redis_cache.cache()
        def test_function(a):
            return a

        # Call that function
        function_response = test_function(test_param)
        expected_hash = str(hash('test_function' + test_param))
        mock_client_object.assert_called_once_with(self.address, self.port)
        mock_client.get.assert_called_once_with(expected_hash)
        self.assertEqual(mock_client.set.call_count, 0)
        self.assertEqual(function_response, test_param)

    @patch('redis_cache.redis_cache.RedisClient')
    def test_redis_failure(self, mock_client_object):
        """
        Tests that the function gets ran as expected when Redis fails
        """
        test_param = 'cache hit test'
        mock_client = Mock()
        # Simulates a cache hit
        mock_client.get.side_effect = RedisException
        mock_client_object.return_value = mock_client
        redis_cache = RedisCache(self.address, self.port)

        # Create a function with the decorator
        @redis_cache.cache()
        def test_function(a):
            return a

        # Call that function
        function_response = test_function(test_param)
        expected_hash = str(hash('test_function' + test_param))
        mock_client_object.assert_called_once_with(self.address, self.port)
        mock_client.get.assert_called_once_with(expected_hash)
        self.assertEqual(mock_client.set.call_count, 0)
        self.assertEqual(function_response, test_param)

    @patch('redis_cache.redis_cache.RedisClient')
    def test_cache_custom_signature(self, mock_client_object):
        """
        Tests a cache hit with custom signature
        """
        test_param = 'cache hit test'
        mock_client = Mock()
        # Simulates a cache hit
        mock_client.get.return_value = pickle.dumps(test_param)
        mock_client_object.return_value = mock_client
        redis_cache = RedisCache(self.address, self.port)

        def test_signature_builder(*args, **kwargs):
            return "test"

        # Create a function with the decorator
        @redis_cache.cache(signature_generator=test_signature_builder)
        def test_function(a):
            return a

        # Call that function
        function_response = test_function(test_param)
        expected_hash = str(hash('test_function'+test_signature_builder()))
        mock_client_object.assert_called_once_with(self.address, self.port)
        mock_client.get.assert_called_once_with(expected_hash)
        self.assertEqual(mock_client.set.call_count, 0)
        self.assertEqual(function_response, test_param)

        # Test that the signature_generator must be callable
        @redis_cache.cache(signature_generator='not callable')
        def test_function_not_callable(a):
            return a

        with self.assertRaises(TypeError):
            test_function_not_callable(test_param)

    @patch('redis_cache.redis_cache.RedisClient')
    def test_simple_object(self, mock_client_object):
        """
        Tests caching of a simple Python object with pickling
        """
        mock_client = Mock()
        # Simulates a cache miss
        mock_client.get.return_value = ''
        mock_client_object.return_value = mock_client
        redis_cache = RedisCache(self.address, self.port)

        # Create a function with the decorator
        simple_obj = SimpleObject('test', 42)
        @redis_cache.cache()
        def test_function(a):
            return simple_obj

        # Call that function
        test_param = 'input'
        function_response = test_function(test_param)
        self.assertEqual(function_response, simple_obj)

        mock_client_object.assert_called_once_with(self.address, self.port)
        expected_hash = str(hash('test_function' + test_param))
        mock_client.get.assert_called_once_with(expected_hash)
        mock_client.set.assert_called_once_with(
            expected_hash, pickle.dumps(simple_obj))

        # Call that function, again, expecting a cache hit
        mock_client.get.return_value = pickle.dumps(simple_obj)
        function_response = test_function(test_param)
        self.assertEqual(function_response, simple_obj)

    @patch('redis_cache.redis_cache.RedisClient')
    def test_simple_object(self, mock_client_object):
        """
        Tests that the cache uses an object's __str__ method to generate
        the signature of an object if available
        """
        mock_client = Mock()
        # Simulates a cache miss
        mock_client.get.return_value = ''
        mock_client_object.return_value = mock_client
        redis_cache = RedisCache(self.address, self.port)

        class TestClass(object):
            def __init__(self, parameter):
                self.parameter = parameter

            @redis_cache.cache()
            def cache_this_method(self):
                return self.parameter

            def __str__(self):
                return "<TestClass object: parameter=%s>" % self.parameter

        param = 'some_param'
        test_class = TestClass(param)
        test_class.cache_this_method()
        mock_client_object.assert_called_once_with(self.address, self.port)
        expected_hash = str(hash('cache_this_method' + str(test_class)))
        mock_client.get.assert_called_once_with(expected_hash)

    @patch('redis_cache.redis_cache.RedisClient')
    def test_cache_on_class_without_str(self, mock_client_object):
        """
        Tests that the cache gets populated when invoking a method that takes a
        primitive type as argument on an object that does not implement a custom
        __str__ method.
        """

        mock_client = Mock()
        mock_client_object.return_value = mock_client
        redis_cache = RedisCache(self.address, self.port)

        class TestClass(object):
            def __init__(self):
                self.call_count = collections.defaultdict(int)

            @redis_cache.cache()
            def echo(self, parameter):
                self.call_count[parameter] += 1
                return parameter

        primitive_argument = 'cache hit test'
        complex_argument = SimpleObject('test', 42)

        for argument in primitive_argument, complex_argument:
            # on the first call, the cache is empty
            instance = TestClass()
            mock_client.get.return_value = ''
            instance1_return1 = instance.echo(argument)

            # after the first call, the cache is set, i.e. all the subsequent
            # calls will return the previously computed value from cache
            mock_client.get.return_value = pickle.dumps(argument)
            instance1_return2 = instance.echo(argument)
            instance1_return3 = instance.echo(argument)
            self.assertEqual(instance1_return1, argument)
            self.assertEqual(instance1_return2, argument)
            self.assertEqual(instance1_return3, argument)
            self.assertEqual(instance.call_count[argument], 1)

            # the cache should also be hit for calls to the same method on a new
            # but equivalent object
            equivalent_instance = TestClass()
            instance2_return1 = equivalent_instance.echo(argument)
            instance2_return2 = equivalent_instance.echo(argument)
            self.assertEqual(instance2_return1, argument)
            self.assertEqual(instance2_return2, argument)
            self.assertEqual(equivalent_instance.call_count[argument], 0)

    @patch('redis_cache.redis_cache.RedisClient')
    def test_cache_on_stateful_class_without_str(self, mock_client_object):
        """
        Tests that the cache gets populated when invoking a method on an object
        that is stateful and that doesn't implement a custom __str__ method.

        Some object are stateful, i.e. their methods will return different
        values at different times in the object's life-cycle. When the state of
        the object changes, we need to make sure that the cache doesn't return
        values for the previous state of the object.
        """
        mock_client = Mock()
        mock_client_object.return_value = mock_client
        redis_cache = RedisCache(self.address, self.port)

        class TestClass(object):
            def __init__(self):
                self.state = None

            @redis_cache.cache()
            def some_method(self):
                return self.state

        state1 = 'some simple type state'
        state2 = SimpleObject('some complex type state', 123)

        def cache_get(cache_key):
            if cache_key == '-5024234577788600450':
                return pickle.dumps(state1)
            if cache_key == '3969794880762558013':
                return pickle.dumps(state2)
            raise ValueError('called cache for hash: {}'.format(cache_key))

        mock_client.get.side_effect = cache_get

        # call the object in some initial state
        stateful_instance = TestClass()
        stateful_instance.state = state1
        return_value_for_state1 = stateful_instance.some_method()

        # mutate the state of the object and make sure that we don't hit the
        # cache for the previous state
        stateful_instance.state = state2
        return_value_for_state2 = stateful_instance.some_method()
        self.assertNotEqual(return_value_for_state1, return_value_for_state2)
