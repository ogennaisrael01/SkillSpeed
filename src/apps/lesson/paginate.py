from rest_framework.pagination import CursorPagination

class CustomLessonPagination(CursorPagination):
    page_size = 20
    max_page_size = 30
    page_size_query_param = "page_size"
    ordering = 'content_order'