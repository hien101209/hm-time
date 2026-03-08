from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import ClickerScore
from .models import ReactionScore
import random
from .models import GuessNumberScore, SnakeScore, MemoryScore, FlappyBirdScore, Game2048Score, HangmanScore

def game_list(request):
    games = [
    {
        "name": "Clicker Game",
        "emoji": "🖱️",
        "desc": "Nhấn càng nhiều càng tốt",
        "url_name": "game:clicker"
    },
    {
        "name": "Reaction Game",
        "emoji": "⚡",
        "desc": "Test phản xạ",
        "url_name": "game:reaction"
    },
    {
        "name": "Guess Number",
        "emoji": "🎯",
        "desc": "Đoán số từ 1 đến 100",
        "url_name": "game:guess"
    },
    {
        "name": "Snake",
        "emoji": "🐍",
        "desc": "Điều khiển rắn ăn mồi",
        "url_name": "game:snake"
    },
    {
        "name": "Memory Game",
        "emoji": "🧠",
        "desc": "Tìm cặp thẻ giống nhau",
        "url_name": "game:memory"
    },
    {
        "name": "Flappy Bird",
        "emoji": "🐦",
        "desc": "Vượt qua các ống",
        "url_name": "game:flappybird"
    },
    {
        "name": "2048",
        "emoji": "🎲",
        "desc": "Trò chơi ghép số hiện đại",
        "url_name": "game:game_2048"
    },
    {
        "name": "Hangman",
        "emoji": "🎬",
        "desc": "Đoán từ bị che giấu",
        "url_name": "game:hangman"
    },
    {
        "name": "Tic Tac Toe",
        "emoji": "❌",
        "desc": "Caro 5x5 đấu với máy",
        "url_name": "game:tic_tac_toe"   # ✅ ĐÚNG namespace
    },
    {
        "name": "Chess",
        "emoji": "♞",
        "desc": "Cờ vua",
        "url_name": "game:chess"
    },
]
    return render(request, "game/game_list.html", {"games": games})

@login_required
def clicker_game(request):
    top_scores = ClickerScore.objects.all()[:10]
    return render(request, "game/clicker.html", {
        "top_scores": top_scores
    })

@login_required
def save_score(request):
    if request.method == "POST":
        score = int(request.POST.get("score", 0))
        ClickerScore.objects.create(
            user=request.user,
            score=score
        )
        return JsonResponse({"status": "ok"})
    
@login_required
def reaction_game(request):
    top_scores = ReactionScore.objects.all()[:10]
    delay = random.randint(2000, 5000)  # ms
    return render(request, "game/reaction.html", {
        "top_scores": top_scores,
        "delay": delay
    })

@login_required
def save_reaction_score(request):
    if request.method == "POST":
        time_ms = int(request.POST.get("time_ms", 0))
        ReactionScore.objects.create(
            user=request.user,
            time_ms=time_ms
        )
        return JsonResponse({"status": "ok"})
    
@login_required
def guess_number(request):
    if "secret" not in request.session:
        request.session["secret"] = random.randint(1, 100)
        request.session["attempts"] = 0

    message = ""

    if request.method == "POST":
        guess = int(request.POST.get("guess"))
        request.session["attempts"] += 1

        if guess < request.session["secret"]:
            message = "📉 Số bạn đoán nhỏ hơn"
        elif guess > request.session["secret"]:
            message = "📈 Số bạn đoán lớn hơn"
        else:
            GuessNumberScore.objects.create(
                user=request.user,
                attempts=request.session["attempts"]
            )
            message = f"🎉 Chính xác! Bạn đoán {request.session['attempts']} lần"
            del request.session["secret"]
            del request.session["attempts"]

    top_scores = GuessNumberScore.objects.all()[:10]

    return render(request, "game/guess_number.html", {
        "message": message,
        "top_scores": top_scores
    })

@login_required
def tic_tac_toe(request):
    return render(request, "game/tic_tac_toe.html")


def chess(request):
    return render(request, "game/chess.html")

@login_required
def snake_game(request):
    top_scores = SnakeScore.objects.all()[:10]
    return render(request, "game/snake.html", {
        "top_scores": top_scores
    })

@login_required
def save_snake_score(request):
    if request.method == "POST":
        score = int(request.POST.get("score", 0))
        SnakeScore.objects.create(
            user=request.user,
            score=score
        )
        return JsonResponse({"status": "ok"})

@login_required
def memory_game(request):
    top_scores = MemoryScore.objects.all()[:10]
    return render(request, "game/memory.html", {
        "top_scores": top_scores
    })

@login_required
def save_memory_score(request):
    if request.method == "POST":
        score = int(request.POST.get("score", 0))
        time_seconds = int(request.POST.get("time", 0))
        MemoryScore.objects.create(
            user=request.user,
            score=score,
            time_seconds=time_seconds
        )
        return JsonResponse({"status": "ok"})

@login_required
def flappy_bird_game(request):
    top_scores = FlappyBirdScore.objects.all()[:10]
    return render(request, "game/flappybird.html", {
        "top_scores": top_scores
    })

@login_required
def save_flappy_score(request):
    if request.method == "POST":
        score = int(request.POST.get("score", 0))
        FlappyBirdScore.objects.create(
            user=request.user,
            score=score
        )
        return JsonResponse({"status": "ok"})

@login_required
def game_2048(request):
    top_scores = Game2048Score.objects.all()[:10]
    return render(request, "game/2048.html", {
        "top_scores": top_scores
    })

@login_required
def save_2048_score(request):
    if request.method == "POST":
        score = int(request.POST.get("score", 0))
        moves = int(request.POST.get("moves", 0))
        Game2048Score.objects.create(
            user=request.user,
            score=score,
            moves=moves
        )
        return JsonResponse({"status": "ok"})

@login_required
def hangman_game(request):
    words = ["PYTHON", "DJANGO", "JAVASCRIPT", "COMPUTER", "PROGRAMMING", "DATABASE", "NETWORK", "SECURITY", "ALGORITHM", "FUNCTION"]
    top_scores = HangmanScore.objects.all()[:10]
    
    if "hangman_word" not in request.session:
        request.session["hangman_word"] = random.choice(words)
        request.session["guessed_letters"] = []
        request.session["wrong_guesses"] = 0
        request.session["hangman_status"] = "playing"
    
    guessed_word = ''.join([letter if letter in request.session["guessed_letters"] else '_' for letter in request.session["hangman_word"]])
    
    if request.method == "POST":
        letter = request.POST.get("letter", "").upper()
        
        if letter and letter not in request.session["guessed_letters"]:
            request.session["guessed_letters"].append(letter)
            if letter not in request.session["hangman_word"]:
                request.session["wrong_guesses"] += 1
            
            guessed_word = ''.join([letter if letter in request.session["guessed_letters"] else '_' for letter in request.session["hangman_word"]])
            
            if guessed_word == request.session["hangman_word"]:
                request.session["hangman_status"] = "won"
                HangmanScore.objects.create(
                    user=request.user,
                    score=100 - (request.session["wrong_guesses"] * 10),
                    wins=1
                )
                del request.session["hangman_word"]
                del request.session["guessed_letters"]
                del request.session["wrong_guesses"]
                del request.session["hangman_status"]
            elif request.session["wrong_guesses"] >= 6:
                request.session["hangman_status"] = "lost"
                HangmanScore.objects.create(
                    user=request.user,
                    score=0,
                    losses=1
                )
                del request.session["hangman_word"]
                del request.session["guessed_letters"]
                del request.session["wrong_guesses"]
                del request.session["hangman_status"]
        
        request.session.modified = True
    
    guessed_word = ''.join([letter if letter in request.session["guessed_letters"] else '_' for letter in request.session["hangman_word"]])
    
    return render(request, "game/hangman.html", {
        "top_scores": top_scores,
        "guessed_word": guessed_word,
        "wrong_guesses": request.session["wrong_guesses"],
        "guessed_letters": request.session["guessed_letters"],
        "status": request.session["hangman_status"]
    })

@login_required
def save_hangman_score(request):
    if request.method == "POST":
        score = int(request.POST.get("score", 0))
        HangmanScore.objects.create(
            user=request.user,
            score=score
        )
        return JsonResponse({"status": "ok"})