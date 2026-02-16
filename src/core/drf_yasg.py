from rest_framework import permissions

from drf_yasg.views import get_schema_view
from drf_yasg import openapi


def get_swagger_view():
    """" A function to get api swagger documatation"""
    schema_view = get_schema_view(
        openapi.Info(
            title="SKill Speed",
            description="African biggest innivation for children",
            contact=openapi.Contact(name="ogenna Israel", email="ogennaisrael@gmail.com"),
            license=openapi.License(name="BSC"),
            default_version="0.1.0"
        ),
        permission_classes=[permissions.AllowAny],
        public=True,
        
    )
    return schema_view