from django.urls import path

from . import views

urlpatterns = [
    path('create_village', views.create_village, name="create_village"),
    path('dashboard', views.dashboard, name="dashboard"),
]
