from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination


class WishItemListPagination(LimitOffsetPagination):
    default_limit = 30
    limit_query_param = 'limit'
    offset_query_param = 'offset'
    max_limit = None


class WishListPagination(WishItemListPagination):
    default_limit = 20
