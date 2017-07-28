from collections import Mapping
from copy import deepcopy


class QuerySerializer(object):
    """
    This implements a way to perform raw queries and serialize the rows into an array of dictionaries. 
    
    As an example of the syntax it supports, imagine you returned a result like the following:

    id | name  | organization__id | organization__address__name | purchases[]__id
    ---+-------+-------------+------------------------+----------------
    1  | Jason | ZeroCater   | Main Address           | 5
    1  | Jason | ZeroCater   | Main Address           | 10

    This would serialize to:
    [
        {
            "id": 1, 
            "name": "Jason", 
            "organization": {
                "name": "ZeroCater", 
                "address": {"name": "Main Address"}
            }, 
            "purchases": [ {"id": 5}, {"id": 10} ]
         }
    ]

    Notes:
        - Array syntax is only supported at the top level.
        - Postgres allows up to 63 chars for a column name and will silently truncate if more than that. You have been warned.

    """

    def get_columns(self, cursor):
        raise NotImplementedError("Other classes implement this")

    def get_array_indicator(self):
        return '[]'

    def get_nested_key_seperator(self):
        return '__'

    def _parse_column(self, column):
        seperator = self.get_nested_key_seperator()
        parts = column.split(self.get_nested_key_seperator())
        return self._construct_mapping_from_array(parts)

    def _construct_mapping_from_array(self, parts):
        array_indicator = self.get_array_indicator()
        length = len(parts) - 1
        full_dict = {}
        for idx, part in enumerate(parts):
            this_part = {}
            this_part['is_object'] = True if not part.endswith(
                array_indicator) and idx < length else False
            this_part['is_array'] = part.endswith(array_indicator)
            if this_part['is_array'] and idx > 0:
                raise AssertionError(
                    "Arrays are only supported at the top level")
            this_part['use'] = not part.startswith("_")
            this_part['attr'] = part[:-2] if this_part['is_array'] else part
            this_part['next'] = {} if idx < length else None
            full_dict = self._update_deepest(full_dict, 'next', this_part)
        return full_dict

    def _update_deepest(self, d, key, value):
        if len(list(d.keys())) == 0:
            return value
        elif isinstance(d.get(key, None), Mapping):
            d[key] = self._update_deepest(d[key], key, value)
            return d
        else:
            d[key] = value
            return d

    def _construct_dict_from_row(self, row, mappings, existing_obj):
        full_obj = existing_obj
        constructed_arrays = []
        for idx, m in enumerate(mappings):
            row_value = row[idx]
            attr = m.get('attr')
            if not m.get('use'):
                continue
            elif not m.get('next'):
                full_obj[attr] = row_value
                continue
            elif m.get('is_object'):
                full_obj[attr] = self._construct_dict_from_row([row_value],
                                                               [m.get('next')],
                                                               full_obj.get(
                                                                   attr, {}))
            elif m.get('is_array'):
                val = full_obj.get(attr, [])
                if len(val) == 0 or (len(val) > 0
                                     and attr not in constructed_arrays):
                    val.append(
                        self._construct_dict_from_row([row_value],
                                                      [m.get('next')], {}))
                    constructed_arrays.append(attr)
                else:
                    new_dict = self._construct_dict_from_row(
                        [row_value], [m.get('next')], val[-1])
                    key = list(new_dict.keys())[0]
                    val[-1][key] = new_dict[key]
                full_obj[attr] = val
        return full_obj

    def _is_dict_empty(self, _dict):
        is_empty = True
        for key, value in _dict.items():
            if not is_empty:
                break
            if not value is None and not isinstance(value, Mapping):
                is_empty = False
            elif isinstance(value, Mapping):
                is_empty = self._is_dict_empty(value)
        return is_empty

    def _remove_null_entries(self, _dict, remove_if_empty=False):
        if remove_if_empty and self._is_dict_empty(_dict):
            return None
        for key in list(_dict.keys()):
            if isinstance(_dict[key], list):
                arr = _dict[key]
                arr = [e for e in arr if not self._is_dict_empty(e)]
                if len(arr) == 0:
                    arr = None
                _dict[key] = arr
            elif isinstance(_dict[key], Mapping):
                _dict[key] = self._remove_null_entries(
                    _dict[key], remove_if_empty=True)
        return _dict

    def get_query_and_params(self):
        raise NotImplementedError("Other classes implement this")

    def record_post_processing(self, record):
        """
        Allows the user to do something to post-process on a per-record basis.
        """
        return record

    def get_grouping_key(self, row):
        """
        Override to not use the default grouping key of the left most column
        """
        return row[0]

    def execute_query(self, query, params):
        raise NotImplementedError("Other classes implement this")

    def cursor_iterator(self, cursor):
        raise NotImplementedError("Other classes implement this")

    def serialize(self):
        query, params = self.get_query_and_params()
        cursor = self.execute_query(query, params)

        columns = self.get_columns(cursor)
        mappings = []
        for column in columns:
            mappings.append(self._parse_column(column))

        table_dict = {}
        for row in self.cursor_iterator(cursor):
            key = self.get_grouping_key(row)
            existing = table_dict.get(key, {})
            updated = self._construct_dict_from_row(row, mappings, existing)
            updated = self.record_post_processing(updated)
            table_dict[key] = updated

        records = list(table_dict.values())
        for idx, record in enumerate(records):
            records[idx] = self._remove_null_entries(record)
        return list(table_dict.values())
