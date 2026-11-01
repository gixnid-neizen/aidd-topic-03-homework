from django.contrib import admin

from dashboard.models import Share, Watchlist, PriceAlert


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


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ("user", "share", "added_at")
    list_filter = ("user",)
    search_fields = ("user__email", "share__ticker")


@admin.register(PriceAlert)
class PriceAlertAdmin(admin.ModelAdmin):
    list_display = ("user", "share", "target_price", "triggered", "created_at")
    list_filter = ("user", "triggered")
    search_fields = ("user__email", "share__ticker")
