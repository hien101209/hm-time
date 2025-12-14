from django.urls import path
from . import views

app_name = 'game'

urlpatterns = [
    path('', views.game_list, name='list'),
    path('clicker/', views.clicker_game, name='clicker'),
    path("clicker/save-score/", views.save_score, name="save_score"),
    path("reaction/", views.reaction_game, name="reaction"),
    path("reaction/save/", views.save_reaction_score, name="save_reaction"),
    path("guess/", views.guess_number, name="guess"),
    path("tic-tac-toe/", views.tic_tac_toe, name="tic_tac_toe"),
    path("chess/", views.chess, name="chess"),

]
