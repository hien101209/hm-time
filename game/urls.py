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
    path("snake/", views.snake_game, name="snake"),
    path("snake/save/", views.save_snake_score, name="save_snake"),
    path("memory/", views.memory_game, name="memory"),
    path("memory/save/", views.save_memory_score, name="save_memory"),
    path("flappybird/", views.flappy_bird_game, name="flappybird"),
    path("flappybird/save/", views.save_flappy_score, name="save_flappy"),
    path("2048/", views.game_2048, name="game_2048"),
    path("2048/save/", views.save_2048_score, name="save_2048"),
    path("hangman/", views.hangman_game, name="hangman"),
    path("hangman/save/", views.save_hangman_score, name="save_hangman"),

]
