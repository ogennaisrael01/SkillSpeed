from rest_framework.pagination import CursorPagination

class CustomSkillPagination(CursorPagination):
    page_size = 5
    max_page_size = 5
    page_size_query_param = "page_size"
    ordering = ("-created_at",)