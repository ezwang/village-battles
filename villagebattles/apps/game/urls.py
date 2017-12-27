from django.urls import path

from . import views

urlpatterns = [
    path('create_village', views.create_village, name="create_village"),
    path('dashboard', views.dashboard, name="dashboard"),
    path('village/<int:village_id>', views.village, name="village"),
    path('map', views.map, name="map"),
    path('map/<int:x>-<int:y>', views.map, name="map_coords"),
]
