# typingapp/models.py
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


# -------------------------
# O'quv markazi
# -------------------------
class Center(models.Model):
    name = models.CharField(max_length=150, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


# -------------------------
# Typing konfiguratsiyasi
# -------------------------
class Language(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:
        return self.name


class Duration(models.Model):
    seconds = models.PositiveIntegerField(unique=True)

    def __str__(self) -> str:
        return f"{self.seconds} s"


class Level(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.name


class Text(models.Model):
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name="texts")
    level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True, blank=True, related_name="texts")
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField()

    def __str__(self) -> str:
        if self.title:
            return self.title
        lang = self.language.name if self.language_id else "?"
        lvl = self.level.name if self.level_id else "-"
        return f"{lang} / {lvl}"


# -------------------------
# Foydalanuvchi profili
# -------------------------
class Player(models.Model):
    # MUHIM: OneToOne + CASCADE, NULL yo'q — yetim player bo'lmaydi.
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="player")
    # Ixtiyoriy ko'rinishdagi ism (reklama uchun), unique emas.
    name = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        # Reyting va admin ko'rinishida nik ko'rinsin
        return self.user.username


# -------------------------
# Mashq natijalari
# -------------------------
class PracticeRun(models.Model):
    # MUHIM: CASCADE — User/Player o'chsa, RUNlar ham o'chadi. "Anon" degan yetim yo'q.
    player   = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="runs")
    center   = models.ForeignKey(Center,   on_delete=models.SET_NULL, null=True, blank=True, related_name="runs")
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True)
    level    = models.ForeignKey(Level,    on_delete=models.SET_NULL, null=True, blank=True, related_name="runs")
    duration = models.ForeignKey(Duration, on_delete=models.SET_NULL, null=True, blank=True)

    # Aniqlik uchun Decimal — 2 ta kasr
    wpm         = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("0.00"))
    accuracy    = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))  # 0..100
    final_score = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal("0.00"))

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-final_score", "-created_at")
        indexes = [
            models.Index(fields=["-final_score", "-created_at"]),
            models.Index(fields=["center", "language", "level", "-final_score", "-created_at"]),
        ]

    def __str__(self) -> str:
        u = self.player.user.username if self.player_id else "—"
        lang = self.language.name if self.language_id else "—"
        lvl = self.level.name if self.level_id else "—"
        dur = f"{self.duration.seconds}s" if self.duration_id else "—"
        return f"{u} | {lang}/{lvl} | {dur} | {self.final_score}"


# -------------------------
# Avto-Player: yangi User yaratilsa, Player ham yaratiladi
# -------------------------
@receiver(post_save, sender=User)
def _auto_create_player(sender, instance, created, **kwargs):
    if created and not hasattr(instance, "player"):
        Player.objects.create(
            user=instance,
            name=(instance.get_full_name() or instance.username)
        )






class Contest(models.Model):
    DRAFT = "DRAFT"
    OPEN = "OPEN"         # ro'yxatdan o'tish (chek yuklash) bosqichi
    RUNNING = "RUNNING"   # typingga ruxsat (start_at..end_at)
    FINISHED = "FINISHED" # typing yopilgan, ko'rib chiqish
    SETTLED = "SETTLED"   # g'oliblar tasdiqlangan
    CANCELLED = "CANCELLED"
    STATUSES = [(s, s) for s in (DRAFT, OPEN, RUNNING, FINISHED, SETTLED, CANCELLED)]

    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    center = models.ForeignKey("typingapp.Center", on_delete=models.SET_NULL, null=True, blank=True)

    entry_fee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))  # UZS
    currency = models.CharField(max_length=3, default="UZS")

    start_at = models.DateTimeField()  # musobaqa boshlanishi (RUNNING oynasi)
    end_at   = models.DateTimeField()  # tugash

    # typing konfiguratsiyasi (hamma uchun bir xil)
    language = models.ForeignKey("typingapp.Language", on_delete=models.PROTECT)
    level    = models.ForeignKey("typingapp.Level", on_delete=models.PROTECT)
    duration = models.ForeignKey("typingapp.Duration", on_delete=models.PROTECT)

    attempts_per_user = models.PositiveIntegerField(default=0)  # 0 = cheksiz
    min_participants  = models.PositiveIntegerField(default=1)
    max_participants  = models.PositiveIntegerField(default=0)  # 0 = cheksiz

    prize1 = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("200000.00"))
    prize2 = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("100000.00"))
    prize3 = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("50000.00"))

    status = models.CharField(max_length=12, choices=STATUSES, default=DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self): return f"{self.title} [{self.status}]"

    def is_open_for_upload(self):
        return self.status in {self.OPEN, self.RUNNING} and timezone.now() < self.end_at

    def is_running(self):
        now = timezone.now()
        return self.status in {self.RUNNING} and self.start_at <= now <= self.end_at


class ContestEntry(models.Model):
    SUBMITTED = "SUBMITTED"  # chek yuklangan, ko'rikda
    APPROVED  = "APPROVED"   # to'lov tasdiqlandi → typingga ruxsat
    REJECTED  = "REJECTED"   # noto'g'ri chek
    REFUNDED  = "REFUNDED"
    STATUSES = [(s, s) for s in (SUBMITTED, APPROVED, REJECTED, REFUNDED)]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name="entries")

    # foydalanuvchi kontaktlari
    telegram = models.CharField(max_length=64, blank=True)
    phone    = models.CharField(max_length=32, blank=True)

    # to'lov dalili (screenshot/pdf)
    receipt = models.FileField(upload_to="receipts/%Y/%m/%d/")

    # admin moderatsiya
    status = models.CharField(max_length=10, choices=STATUSES, default=SUBMITTED)
    review_message = models.TextField(blank=True)  # rad etish sababi yoki tasdiq xabari
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    reviewed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("user", "contest"),)  # bitta musobaqaga bitta ariza
        ordering = ("-created_at",)

    def __str__(self): return f"{self.user.username} → {self.contest.title} [{self.status}]"


class ContestRun(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name="runs")
    user    = models.ForeignKey(User, on_delete=models.CASCADE)   # to'g'ridan user; Player ham bo'lishi mumkin
    center  = models.ForeignKey("typingapp.Center", on_delete=models.SET_NULL, null=True, blank=True)

    wpm         = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("0.00"))
    accuracy    = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    final_score = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal("0.00"))

    suspicious  = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.contest.title} | {self.user.username} | {self.final_score}"