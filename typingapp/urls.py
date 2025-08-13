from django.urls import path
from . import views

urlpatterns = [
    path('', views.enter_name, name='enter_name'),
    path('languages/', views.select_language, name='select_language'),
    path('levels/<int:lang_id>/', views.select_level, name='select_level'),  # 1: til -> daraja
    path('select-time/<int:lang_id>/<int:level_id>/', views.select_time, name='select_time'),  # 2: daraja -> vaqt
    path('typing/<int:lang_id>/<int:level_id>/<int:duration>/', views.typing_practice, name='typing_practice'),  # 3: vaqt -> typing
    path('result/', views.result_view, name='result'),
    path('logout/', views.logout_player, name='logout'),
]
