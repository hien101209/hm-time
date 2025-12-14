from django.db import models
from django.contrib.auth.models import User

class ClickerScore(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-score', 'created_at']

    def __str__(self):
        return f"{self.user.username} - {self.score}"

class ReactionScore(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    time_ms = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['time_ms', 'created_at']

    def __str__(self):
        return f"{self.user.username} - {self.time_ms}ms"
    
class GuessNumberScore(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    attempts = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['attempts', 'created_at']

    def __str__(self):
        return f"{self.user.username} - {self.attempts} lần"
