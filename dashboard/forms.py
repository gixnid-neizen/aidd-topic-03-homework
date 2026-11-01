from django import forms

from .models import (
    InvestmentStrategy,
    Portfolio,
    PortfolioTrade,
    Share,
    Watchlist,
    WatchlistItem,
)


class ShareModelForm(forms.ModelForm):
    """Инструмент"""

    class Meta:
        model = Share
        fields = "__all__"


class WatchlistForm(forms.ModelForm):
    class Meta:
        model = Watchlist
        fields = ("name",)


class WatchlistItemForm(forms.ModelForm):
    target_price = forms.DecimalField(
        required=False, max_digits=18, decimal_places=6, min_value=0.000001
    )

    class Meta:
        model = WatchlistItem
        fields = ("share", "target_price", "direction")


class PortfolioForm(forms.ModelForm):
    class Meta:
        model = Portfolio
        fields = ("name",)


class PortfolioTradeForm(forms.Form):
    share = forms.ModelChoiceField(queryset=Share.objects.order_by("ticker"))
    side = forms.ChoiceField(choices=PortfolioTrade.SIDES)
    quantity = forms.IntegerField(min_value=1)
    price = forms.DecimalField(max_digits=18, decimal_places=6, min_value=0.000001)


class InvestmentStrategyForm(forms.ModelForm):
    quantity = forms.IntegerField(min_value=1)

    class Meta:
        model = InvestmentStrategy
        fields = ("name", "share", "buy_below", "sell_above", "quantity", "is_active")
