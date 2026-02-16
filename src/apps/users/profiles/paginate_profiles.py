from rest_framework.pagination import CursorPagination

class CustomProfilePagination(CursorPagination):
    page_size = 20
    max_page_size  = 50
    page_size_query_param: str = "page_size"
    ordering: str = "-created_at"