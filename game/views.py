from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import ClickerScore
from .models import ReactionScore
import random
from .models import GuessNumberScore

def game_list(request):
    games = [
    {
        "name": "Clicker Game",
        "desc": "Nhấn càng nhiều càng tốt",
        "url_name": "game:clicker"
    },
    {
        "name": "Reaction Game",
        "desc": "Test phản xạ",
        "url_name": "game:reaction"
    },
    {
        "name": "Guess Number",
        "desc": "Đoán số từ 1 đến 100",
        "url_name": "game:guess"
    },
    {
        "name": "Tic Tac Toe",
        "desc": "Caro 5x5 đấu với máy",
        "url_name": "game:tic_tac_toe"   # ✅ ĐÚNG namespace
    },
    {
        "name": "Chess",
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