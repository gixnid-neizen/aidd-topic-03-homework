from django import forms

from .models import Share, PriceAlert


class ShareModelForm(forms.ModelForm):
    """Инструмент"""

    class Meta:
        model = Share
        fields = "__all__"


class PriceAlertForm(forms.ModelForm):
    """Оповещение о целевой цене акции"""

    class Meta:
        model = PriceAlert
        fields = ("share", "target_price")
