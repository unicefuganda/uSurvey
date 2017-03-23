import re
from cacheops import cached_as
import pandas as pd
from django.db import connection
from django.db.models import Q

PDS_FETCH_CHUNKSIZE = 10000


def normalize_query(query_string,
                    findterms=re.compile(r'"([^"]+)"|(\S+)').findall,
                    normspace=re.compile(r'\s{2,}').sub):
    ''' Splits the query string in invidual keywords, getting rid of unecessary spaces
        and grouping quoted words together.
        Example:

        >>> normalize_query('  some random  words "with   quotes  " and   spaces')
        ['some', 'random', 'words', 'with quotes', 'and', 'spaces']
        see http://julienphalip.com/post/2825034077/adding-search-to-a-django-site-in-a-snap for more info
    '''
    return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(query_string)]


def _get_query(query_string, search_fields):
    ''' Returns a query, that is a combination of Q objects. That combination
        aims to search keywords within a model by testing the given search fields.
        see http://julienphalip.com/post/2825034077/adding-search-to-a-django-site-in-a-snap for more info
    '''
    query = None  # Query to search for every search term
    terms = normalize_query(query_string)
    for term in terms:
        or_query = None  # Query to search for a given term in each field
        for field_name in search_fields:
            q = Q(**{"%s__icontains" % field_name: term})
            if or_query is None:
                or_query = q
            else:
                or_query = or_query | q
        if query is None:
            query = or_query
        else:
            query = query & or_query
    return query


def get_filterset(objectset, query_string, search_fields):
    '''Returns a filterset by applying the query string each search field
    '''
    if query_string:
        query = _get_query(query_string, search_fields)
        return objectset.filter(query).distinct()
    return objectset.distinct()



def to_df(queryset, date_cols=[]):
    @cached_as(queryset)
    def _to_df(queryset, date_cols):
        df = pd.DataFrame()
        query, params = queryset.query.sql_with_params()
        pd_fetch = pd.io.sql.read_sql_query
        for chunk in pd_fetch(query, connection, params=params, parse_dates=date_cols, chunksize=PDS_FETCH_CHUNKSIZE):
            df = df.append(chunk, ignore_index=True)
        return df
    return _to_df(queryset, date_cols)
