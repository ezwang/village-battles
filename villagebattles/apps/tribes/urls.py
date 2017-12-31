from django.urls import path

from . import views

urlpatterns = [
    path('', views.tribe, name="tribe"),
    path('<int:tribe_id>', views.tribe_info, name="tribe_info"),
]
