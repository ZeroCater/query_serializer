import sqlite3

from copy import deepcopy
from unittest import TestCase

from query_serializer import RawQueryFilter, QuerySerializer
from tests import sqlite


class TestRawQueryFilterAndQuerySerializerTogether(TestCase):
    def setUp(self):
        class Rqf(RawQueryFilter):
            def __init__(self, params):
                self.methods = ('purchase', )
                self.params = params

            def purchase(self):
                purchase_id = self.params.get('purchase_id')
                if purchase_id:
                    return ('purchase.rowid = ?', [purchase_id])
                return self.not_used()

        class FilteredCustomerPurchaseSerializer(
                sqlite.SqliteCustomerPurchaseSerializer):
            def __init__(self, params):
                self.filter = Rqf(params)

            def get_query_and_params(self):
                query = sqlite.get_test_query()
                query += " {filter}"
                _filter, params = self.filter.construct_filter()
                return query.format(filter=_filter), params

        self.Serializer = FilteredCustomerPurchaseSerializer

        sqlite.setup_database()

    def tearDown(self):
        sqlite.teardown_database()

    def test_example_usage(self):
        expected = {
            'id': 1,
            'name': 'Jason',
            'organization': {
                'id': 1,
                'name': 'ZeroCater',
                'address': {
                    'name': 'Main Address'
                },
            },
            'purchases': [{
                'id': 2
            }]
        }
        serializer = self.Serializer({'purchase_id': 2})
        self.assertEqual([expected], serializer.serialize())
