from django.contrib import admin

from dashboard.models import (
    InvestmentStrategy,
    Portfolio,
    PortfolioTrade,
    PriceAlertNotification,
    PriceHistory,
    Share,
    StrategyTrade,
    Watchlist,
    WatchlistItem,
)


@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    list_display = ("figi", "isin", "name", "ticker", "currency")
    search_fields = ("figi", "isin", "name", "ticker")
    fields = (
        "figi",
        "isin",
        "name",
        "ticker",
        "currency",
        "uid",
        "last_price",
        "is_trend_high",
    )


admin.site.register(
    (
        Watchlist,
        WatchlistItem,
        PriceAlertNotification,
        Portfolio,
        PortfolioTrade,
        PriceHistory,
        InvestmentStrategy,
        StrategyTrade,
    )
)
