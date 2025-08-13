from django.db import models

class Language(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.name

class Duration(models.Model):
    seconds = models.PositiveIntegerField(unique=True)
    def __str__(self): return f"{self.seconds} s"

class Level(models.Model):
    name = models.CharField(max_length=50, unique=True)
    def __str__(self): return self.name

class Text(models.Model):
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='texts')
    level = models.ForeignKey(
        Level,
        on_delete=models.SET_NULL,   # PROTECT o'rniga SET_NULL — o'chirishga ruxsat
        null=True, blank=True,
        related_name='texts'
    )
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField()


class Player(models.Model):
    name = models.CharField(max_length=120, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name

class PracticeRun(models.Model):
    player = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True)
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True)
    level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True, blank=True, related_name='runs')
    duration = models.ForeignKey(Duration, on_delete=models.SET_NULL, null=True, blank=True)
    final_score = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-final_score', '-created_at']

    def __str__(self):
        who = self.player.name if self.player else "Anon"
        lang = self.language.name if self.language else "—"
        lvl = self.level.name if self.level else "—"
        dur = f"{self.duration.seconds}s" if self.duration else "—"
        return f"{who} | {lang}/{lvl} | {dur} | {self.final_score} ball"
