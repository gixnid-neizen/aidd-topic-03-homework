from django.db import models
from django.conf import settings


class Share(models.Model):
    """Акция"""

    figi = models.CharField(max_length=255, unique=True)
    isin = models.CharField(max_length=255)
    name = models.CharField(max_length=255, verbose_name="Наименование компании")
    ticker = models.CharField(max_length=10, unique=True, verbose_name="Тикер")
    currency = models.CharField(max_length=20, verbose_name="Валюта")
    uid = models.CharField(max_length=255, unique=True)
    last_price = models.FloatField(blank=True, null=True, verbose_name="Текущая цена")
    is_trend_high = models.BooleanField(
        blank=True, null=True, verbose_name="Растет цена"
    )
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return f"{self.ticker} ({self.name})"

    class Meta:
        verbose_name = "Акция"
        verbose_name_plural = "Акции"


class Watchlist(models.Model):
    """Персональный список наблюдения пользователя за акциями"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )
    share = models.ForeignKey(
        Share, on_delete=models.CASCADE, verbose_name="Акция"
    )
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="Добавлено")

    class Meta:
        verbose_name = "Список наблюдения"
        verbose_name_plural = "Списки наблюдения"
        unique_together = (("user", "share"),)

    def __str__(self):
        return f"{self.user} -> {self.share.ticker}"


class PriceAlert(models.Model):
    """Целевой уровень цены с уведомлением о достижении"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )
    share = models.ForeignKey(
        Share, on_delete=models.CASCADE, verbose_name="Акция"
    )
    target_price = models.FloatField(verbose_name="Целевая цена")
    triggered = models.BooleanField(default=False, verbose_name="Сработало")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    triggered_at = models.DateTimeField(
        blank=True, null=True, verbose_name="Сработало в"
    )

    class Meta:
        verbose_name = "Оповещение о цене"
        verbose_name_plural = "Оповещения о цене"

    def __str__(self):
        return f"{self.share.ticker} >= {self.target_price} ({self.user})"
