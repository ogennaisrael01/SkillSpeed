from django.urls import path

from . import views

payment_urlpatterns = [
    path("child/<uuid:child_pk>/skill/<uuid:skill_pk>/purchase/", 
    view=views.PaymentView.as_view(), name="purchase"),
]