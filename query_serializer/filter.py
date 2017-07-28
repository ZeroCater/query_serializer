class RawQueryFilter(object):
    """
    Used to construct the where clause of a query. 

    You should implement your own methods which return the following:
        - ('filter string', [filter]) or `self.not_used()` if the filter shouldn't be used.

    Then you set a self.method in __init__ with a list of the names of your methods.

    This is useful in QuerySerializer.get_query_and_params to dynamically set a filter by calling construct_filter.

    See the tests for an example.
    """

    def not_used(self):
        return (False, False)

    def construct_filter(self):
        all_querys = []
        all_query_params = []
        for method in self.methods:
            query, query_params = getattr(self, method)()
            if query:
                all_querys.append(query)
                all_query_params = all_query_params + query_params

        if len(all_querys) > 0:
            formatted_queries = 'where {placeholder}'.format(
                placeholder=' and '.join(all_querys))
            return (formatted_queries, all_query_params)
        return ('', [])
