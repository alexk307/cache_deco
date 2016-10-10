from redis_cache.redis_cache import \
    RedisCache, RedisException, DEFAULT_EXPIRATION
from fakes import FakeRedisClient
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

    def test_cache_on_class_without_str_for_function_with_simple_args(self):
        """
        Tests a cache hit when invoking a method that takes a primitive type as
        argument on an object that does not implement a __str__ method
        """
        redis_cache = RedisCache(self.address, self.port)
        redis_cache.redis_client = FakeRedisClient()

        class TestClass(object):
            def __init__(self):
                self.call_count = collections.defaultdict(int)

            @redis_cache.cache()
            def echo(self, parameter):
                self.call_count[parameter] += 1
                return parameter

        primitive_argument = 'cache hit test'

        instance1 = TestClass()
        instance2 = TestClass()
        instance3 = TestClass()

        value1 = instance1.echo(primitive_argument)
        value2 = instance2.echo(primitive_argument)
        value3 = instance3.echo(primitive_argument)

        self.assertTrue(value1 == value2 == value3 == primitive_argument)
        self.assertEqual(instance1.call_count[primitive_argument], 1)
        self.assertEqual(instance2.call_count[primitive_argument], 0)
        self.assertEqual(instance3.call_count[primitive_argument], 0)

    def test_cache_on_class_without_str_for_function_with_complex_args(self):
        """
        Tests a cache hit when invoking a method that takes a complex type as
        argument on an object that does not implement a __str__ method
        """
        redis_cache = RedisCache(self.address, self.port)
        redis_cache.redis_client = FakeRedisClient()

        class TestClass(object):
            def __init__(self):
                self.some_method_call_count = collections.defaultdict(int)

            @redis_cache.cache()
            def some_method(self, parameter):
                self.some_method_call_count[parameter] += 1
                return parameter

        complex_argument = SimpleObject('test', 42)

        instance1 = TestClass()
        instance2 = TestClass()
        instance3 = TestClass()

        value1 = instance1.some_method(complex_argument)
        value2 = instance2.some_method(complex_argument)
        value3 = instance3.some_method(complex_argument)

        self.assertTrue(value1 == value2 == value3 == complex_argument)
        self.assertEqual(instance1.some_method_call_count[complex_argument], 1)
        self.assertEqual(instance2.some_method_call_count[complex_argument], 0)
        self.assertEqual(instance3.some_method_call_count[complex_argument], 0)

    def test_cache_on_stateful_class_without_str(self):
        """
        Tests a cache hit when invoking a method on a stateful object.
        """
        redis_cache = RedisCache(self.address, self.port)
        redis_cache.redis_client = FakeRedisClient()

        class TestClass(object):
            def __init__(self, state):
                self.state = state

            @redis_cache.cache()
            def some_method(self):
                return self.state

        state1 = 'some state'
        state2 = SimpleObject('foo', 2)

        state1_instance1 = TestClass(state1)
        state1_instance2 = TestClass(state1)
        state2_instance1 = TestClass(state2)
        state2_instance2 = TestClass(state2)

        value1 = state1_instance1.some_method()
        value2 = state1_instance1.some_method()
        value3 = state1_instance2.some_method()
        value4 = state2_instance1.some_method()
        value5 = state2_instance2.some_method()
        value6 = state2_instance1.some_method()

        self.assertTrue(value1 == value2 == value3 == state1)
        self.assertTrue(value4 == value5 == value6 == state2)
