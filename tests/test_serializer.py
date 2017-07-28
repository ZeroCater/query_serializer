import sqlite3

from copy import deepcopy
from unittest import TestCase
from query_serializer import QuerySerializer
from tests import sqlite


class TestQuerySerializer(TestCase):
    def setUp(self):
        self.qs = QuerySerializer()
        sqlite.setup_database()

    def tearDown(self):
        sqlite.teardown_database()

    def test_update_deepest_matching_key(self):
        d = {}
        key = 'test'
        val = 1
        self.assertEqual(val, self.qs._update_deepest(d, key, val))

        d = {'test': {'test': {'test': None}}}
        returned_d = self.qs._update_deepest(d, 'test', val)
        self.assertEqual(1, returned_d.get('test').get('test').get('test'))

    def run_test_for_mapping(self,
                             obj,
                             is_object,
                             is_array,
                             use,
                             attr,
                             _next=False):
        self.assertEqual(obj['is_object'], is_object)
        self.assertEqual(obj['is_array'], is_array)
        self.assertEqual(obj['use'], use)
        self.assertEqual(obj['attr'], attr)
        if _next != False:
            self.assertEqual(obj['next'], _next)

    def test_construct_mapping_from_array_private(self):
        private = '_private'
        obj = self.qs._construct_mapping_from_array([private])
        self.run_test_for_mapping(obj, False, False, False, private, None)

    def test_construct_mapping_from_array_multi(self):
        arr = ['first', 'second']
        obj = self.qs._construct_mapping_from_array(arr)
        self.run_test_for_mapping(obj, True, False, True, 'first')
        self.run_test_for_mapping(
            obj.get('next'), False, False, True, 'second', None)

    def test_construct_mapping_from_array_throws_if_array_notation_not_on_first_level(
            self):
        arr = ['first', 'bad_array[]']
        with self.assertRaises(AssertionError):
            self.qs._construct_mapping_from_array(arr)

    def test_construct_mapping_from_array_with_array_string(self):
        arr_string = 'first[]'
        obj = self.qs._construct_mapping_from_array([arr_string])
        self.run_test_for_mapping(obj, False, True, True, 'first', None)

    def test_parse_column_no_splits(self):
        column = 'first_column'
        obj = self.qs._parse_column(column)
        self.run_test_for_mapping(obj, False, False, True, column, None)

    def test_parse_column_splits_with_double_underscore(self):
        column = 'first_part__second_part'
        obj = self.qs._parse_column(column)
        self.run_test_for_mapping(obj, True, False, True, 'first_part')
        self.run_test_for_mapping(
            obj.get('next'), False, False, True, 'second_part', None)

    def test_construct_dict_from_row(self):
        row = ['Jason', '137', 'ZeroCater', '1111', 'time_val', '_do_not_use']
        columns = [
            'name', 'organization__id', 'organization__name',
            'purchases[]__id', 'purchases[]__reciept__time', '_private'
        ]
        mappings = []
        for column in columns:
            mappings.append(self.qs._parse_column(column))
        returned = self.qs._construct_dict_from_row(row, mappings, {})
        expected = {
            columns[0]: row[0],
            'organization': {
                'id': row[1],
                'name': row[2]
            },
            'purchases': [{
                'id': row[3],
                'reciept': {
                    'time': row[4]
                }
            }]
        }
        self.assertEqual(expected, returned)

    def test_construct_dict_from_row_appends_arrays(self):
        first_row = [
            'Jason', '137', 'ZeroCater', '1111', 'time_val', '_do_not_use'
        ]
        second_row = [
            'Jason', '137', 'ZeroCater', '2222', '2nd_time_val', '_do_not_use'
        ]
        columns = [
            'name', 'organization__id', 'organization__name',
            'purchases[]__id', 'purchases[]__reciept__time', '_private'
        ]
        mappings = []
        for column in columns:
            mappings.append(self.qs._parse_column(column))
        expected = {
            columns[0]:
            first_row[0],
            'organization': {
                'id': first_row[1],
                'name': first_row[2]
            },
            'purchases': [{
                'id': first_row[3],
                'reciept': {
                    'time': first_row[4]
                }
            }, {
                'id': second_row[3],
                'reciept': {
                    'time': second_row[4]
                }
            }]
        }
        first_returned = self.qs._construct_dict_from_row(
            first_row, mappings, {})
        full_obj = self.qs._construct_dict_from_row(second_row, mappings,
                                                    first_returned)
        self.assertEqual(expected, full_obj)

    def test_is_dict_empty(self):
        not_empty_dict = {'test': 1}
        self.assertFalse(self.qs._is_dict_empty(not_empty_dict))

        empty_dict = {'test': {'empty': {'dict': None}}}
        self.assertTrue(self.qs._is_dict_empty(empty_dict))

    def test_remove_null_entries(self):
        has_null = {
            'id': 1,
            'array': [{
                'id': 2
            }, {
                'id': None
            }],
            'dict': {
                'id': 3,
                'empty_inner_dict': {}
            },
            'empty_dict': {}
        }
        expected = deepcopy(has_null)
        expected['array'] = [expected['array'][0]]
        expected['empty_dict'] = None
        expected['dict']['empty_inner_dict'] = None
        returned = self.qs._remove_null_entries(has_null)
        self.assertEqual(expected, returned)

    def test_serialize(self):
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
                'id': 1
            }, {
                'id': 2
            }]
        }

        qs = sqlite.SqliteCustomerPurchaseSerializer()
        self.assertEqual([expected], qs.serialize())
