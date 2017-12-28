from django.urls import path

from . import views

urlpatterns = [
    # Map
    path('map', views.map, name="map"),
    path('map/load', views.map_load, name="map_load"),
    path('map/coord', views.map_coord, name="map_coord"),

    # Info
    path('user/<int:user_id>', views.user, name="user"),

    # Village
    path('dashboard', views.dashboard, name="dashboard"),
    path('create_village', views.create_village, name="create_village"),
    path('village/<int:village_id>', views.village, name="village"),
    path('hq/<int:village_id>', views.hq, name="hq"),
    path('barracks/<int:village_id>', views.barracks, name="barracks"),
    path('rally/<int:village_id>', views.rally, name="rally"),
]
