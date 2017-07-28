from unittest import TestCase

from query_serializer import RawQueryFilter


class TestRawQueryFilter(TestCase):
    def test_construct(self):
        class RqfTest(RawQueryFilter):
            def __init__(self):
                self.methods = ('empty_method', 'returns_something')

            def empty_method(self):
                return self.not_used()

            def returns_something(self):
                return ('some_string', [0])

        f = RqfTest()
        expected_string, expected_params = f.returns_something()
        expected_string = 'where {expected_string}'.format(
            expected_string=expected_string)
        self.assertEqual((expected_string, expected_params),
                         f.construct_filter())
