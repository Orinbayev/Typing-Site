# typingapp/urls.py
app_name = "typingapp"
from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('register/', views.register_view, name='register'),
    path('login/',    views.login_view,    name='login'),
    path('logout/',   views.logout_view,   name='logout'),

    # Centers
    path('centers/', views.center_list, name='center_list'),
    path('centers/pick/<int:center_id>/', views.center_pick, name='center_pick'),

    # Leaderboard
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('leaderboard/<int:center_id>/', views.leaderboard_center, name='leaderboard_center'),

    # Typing flow
    path('languages/', views.select_language, name='select_language'),
    path('levels/<int:lang_id>/', views.select_level, name='select_level'),
    path('select-time/<int:lang_id>/<int:level_id>/', views.select_time, name='select_time'),
    path('typing/<int:lang_id>/<int:level_id>/<int:duration>/', views.typing_practice, name='typing_practice'),
    path('result/', views.result_view, name='result'),

    # Root
    path('', views.center_list, name='home'),
    path("contests/", views.contests_list, name="contests_list"),
    path("contests/<int:contest_id>/", views.contest_detail, name="contest_detail"),
    path("contests/<int:contest_id>/join/", views.contest_join, name="contest_join"),
    path("contests/<int:contest_id>/start/", views.contest_start, name="contest_start"),
    path("contests/<int:contest_id>/result/", views.contest_result, name="contest_result"),
    path("contests/<int:contest_id>/leaderboard/", views.contest_leaderboard, name="contest_leaderboard"),
]
