# Query Serializer

[![CircleCI](https://circleci.com/gh/ZeroCater/query_serializer.svg?style=svg)](https://circleci.com/gh/ZeroCater/query_serializer)

## Motiviation

Here at ZeroCater we are heavy users of Django, which has a fantastic ORM. However, sometimes the generated query is not as effecient as it could be and advanced querying can be hard. This library gives the developer an option to use raw sql and serialize it into relatively complex dictionaries.

Taking this approach has proven to be easier to maintain then maintaining both the query itself and the serialization of it. That said, you should prefer to utilize Django's ORM before reaching for this.

## General Description

This implements a way to perform raw queries and serialize the rows into an array of dictionaries. 

As an example of the syntax it supports, imagine you returned a result like the following:

```
id | name  | organization__id | organization__address__name | purchases[]__id
---+-------+------------------+-----------------------------+----------------
1  | Jason | ZeroCater        | Main Address                | 5
1  | Jason | ZeroCater        | Main Address                | 10
```

This would serialize to:
```json
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
```

Notes:
    - Array syntax is only supported at the top level.
    - Postgres allows up to 63 chars for a column name and will silently truncate if more than that. You have been warned.
    - Sqlite should use `--` as the array indicator, instead of `[]`

## Usage

To use this library, you must inherit from QuerySerializer and implement at least:

- `execute_query` which should return a cursor
- `cursor_iterator` which should be a generator, yielding each row
- `get_columns` so it can parse the columns of your select statement
- `get_get_query_and_params` that returns the string query and params to be passed into execute query.

In addition, `get_array_indicator` is provided if your driver does not support `[]` in the column name. What it returns should be two characters long.

Here is an example using sqlite:

```python
import sqlite3
from query_serializer import QuerySerializer

class SqliteCustomerPurchaseSerializer(QuerySerializer):
    def get_array_indicator(self):
        return '--'

    def execute_query(self, query, params):
        conn = sqlite3.connect('test.db')
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor

    def cursor_iterator(self, cursor):
        for row in cursor.fetchall():
            yield row

    def get_columns(self, cursor):
        return [col[0] for col in cursor.description]

    def get_query_and_params(self):
        return query, []

results = SqliteCustomerPurchaseSerializer().serializer()
```

In addition, a `RawQueryFilter` class is provided to aid in constructing the where clause of a query. See the tests for usage examples.

## Compatibility

This library is compatible with all python versions listed in `tox.ini`

## Contributions

Contributions are welcome.

### Testing

Use `tox` to test. You may need to install it, which you can do via `pip install -r requirements.txt`

### Style guide

Please use `./format.sh` to style your code. This stops distracting arguments and wasted time.
