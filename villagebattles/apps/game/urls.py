from django.urls import path

from . import views

urlpatterns = [
    path('', views.start, name="start"),

    # Map
    path('map', views.map, name="map"),
    path('map/load', views.map_load, name="map_load"),
    path('map/coord', views.map_coord, name="map_coord"),

    # Info
    path('user/<int:user_id>', views.user, name="user"),
    path('report', views.report, name="report"),
    path('report/<int:report_id>', views.report, name="report_detailed"),

    # Village
    path('dashboard', views.dashboard, name="dashboard"),
    path('create_village', views.create_village, name="create_village"),
    path('village/<int:village_id>', views.village, name="village"),
    path('hq/<int:village_id>', views.hq, name="hq"),
    path('troops/cancel/<int:village_id>', views.troop_cancel, name="cancel_troops"),
    path('barracks/<int:village_id>', views.barracks, name="barracks"),
    path('stable/<int:village_id>', views.stable, name="stable"),
    path('workshop/<int:village_id>', views.workshop, name="workshop"),
    path('academy/<int:village_id>', views.academy, name="academy"),
    path('rally/<int:village_id>', views.rally, name="rally"),

    # Quest
    path('quest/<int:quest_id>', views.quest, name="quest"),
    path('quest/submit', views.quest_submit, name="submit_quest"),
]
