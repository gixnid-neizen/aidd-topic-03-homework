from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


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

    class Meta:
        verbose_name = "Акция"
        verbose_name_plural = "Акции"

    def __str__(self):
        return f"{self.ticker} — {self.name}"


class Watchlist(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="watchlists",
    )
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(fields=("user", "name"), name="unique_user_watchlist")
        ]

    def __str__(self):
        return self.name


class WatchlistItem(models.Model):
    ABOVE = "above"
    BELOW = "below"
    ALERT_DIRECTIONS = ((ABOVE, "At or above"), (BELOW, "At or below"))

    watchlist = models.ForeignKey(
        Watchlist, on_delete=models.CASCADE, related_name="items"
    )
    share = models.ForeignKey(
        Share, on_delete=models.CASCADE, related_name="watchlist_items"
    )
    target_price = models.DecimalField(
        max_digits=18, decimal_places=6, null=True, blank=True
    )
    direction = models.CharField(
        max_length=5, choices=ALERT_DIRECTIONS, default=ABOVE
    )
    is_triggered = models.BooleanField(default=False)
    last_triggered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("watchlist", "share"), name="unique_share_per_watchlist"
            ),
            models.CheckConstraint(
                check=Q(target_price__isnull=True) | Q(target_price__gt=0),
                name="watchlist_target_price_positive",
            ),
        ]

    def __str__(self):
        return f"{self.watchlist}: {self.share}"


class PriceAlertNotification(models.Model):
    item = models.ForeignKey(
        WatchlistItem, on_delete=models.CASCADE, related_name="notifications"
    )
    price = models.DecimalField(max_digits=18, decimal_places=6)
    triggered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-triggered_at",)


class Portfolio(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="portfolios",
    )
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(fields=("user", "name"), name="unique_user_portfolio")
        ]

    def __str__(self):
        return self.name


class PortfolioTrade(models.Model):
    BUY = "buy"
    SELL = "sell"
    SIDES = ((BUY, "Buy"), (SELL, "Sell"))

    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name="trades"
    )
    share = models.ForeignKey(
        Share, on_delete=models.PROTECT, related_name="portfolio_trades"
    )
    side = models.CharField(max_length=4, choices=SIDES)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=18, decimal_places=6)
    executed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("executed_at", "pk")
        constraints = [
            models.CheckConstraint(check=Q(quantity__gt=0), name="trade_quantity_positive"),
            models.CheckConstraint(check=Q(price__gt=0), name="trade_price_positive"),
        ]

    def __str__(self):
        return f"{self.get_side_display()} {self.quantity} {self.share.ticker}"


class PriceHistory(models.Model):
    share = models.ForeignKey(
        Share, on_delete=models.CASCADE, related_name="price_history"
    )
    price = models.DecimalField(max_digits=18, decimal_places=6)
    captured_at = models.DateTimeField()

    class Meta:
        ordering = ("captured_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("share", "captured_at"), name="unique_share_price_timestamp"
            ),
            models.CheckConstraint(check=Q(price__gt=0), name="history_price_positive"),
        ]

    def __str__(self):
        return f"{self.share.ticker} @ {self.captured_at}"


class InvestmentStrategy(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="investment_strategies",
    )
    name = models.CharField(max_length=100)
    share = models.ForeignKey(
        Share, on_delete=models.CASCADE, related_name="investment_strategies"
    )
    buy_below = models.DecimalField(
        max_digits=18, decimal_places=6, null=True, blank=True
    )
    sell_above = models.DecimalField(
        max_digits=18, decimal_places=6, null=True, blank=True
    )
    quantity = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=("user", "name"), name="unique_user_strategy_name"
            ),
            models.CheckConstraint(check=Q(quantity__gt=0), name="strategy_quantity_positive"),
            models.CheckConstraint(
                check=Q(buy_below__isnull=True) | Q(buy_below__gt=0),
                name="strategy_buy_price_positive",
            ),
            models.CheckConstraint(
                check=Q(sell_above__isnull=True) | Q(sell_above__gt=0),
                name="strategy_sell_price_positive",
            ),
        ]

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError({"quantity": "Quantity must be greater than zero."})
        if self.buy_below is None and self.sell_above is None:
            raise ValidationError("Set at least one buy or sell price condition.")
        if self.buy_below is not None and self.buy_below <= 0:
            raise ValidationError({"buy_below": "The buy price must be greater than zero."})
        if self.sell_above is not None and self.sell_above <= 0:
            raise ValidationError({"sell_above": "The sell price must be greater than zero."})
        if (
            self.buy_below is not None
            and self.sell_above is not None
            and self.buy_below >= self.sell_above
        ):
            raise ValidationError("The buy price must be lower than the sell price.")

    def __str__(self):
        return self.name


class StrategyTrade(models.Model):
    strategy = models.ForeignKey(
        InvestmentStrategy, on_delete=models.CASCADE, related_name="trades"
    )
    side = models.CharField(max_length=4, choices=PortfolioTrade.SIDES)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=18, decimal_places=6)
    executed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("executed_at", "pk")
        constraints = [
            models.CheckConstraint(
                check=Q(quantity__gt=0), name="strategy_trade_quantity_positive"
            ),
            models.CheckConstraint(
                check=Q(price__gt=0), name="strategy_trade_price_positive"
            ),
        ]
