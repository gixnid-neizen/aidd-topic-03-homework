from config.celery import app
from dashboard.models import Share
from dashboard.services.market_data import get_last_data
from dashboard.services.investments import process_market_price
from config.settings import logger


@app.task
def update_last_price():
    for share in Share.objects.all().iterator():
        try:
            last_price, captured_at = get_last_data(share)
            if last_price is None or captured_at is None or last_price <= 0:
                continue

            is_trend_high = (
                share.last_price is None or share.last_price <= last_price
            )
            Share.objects.filter(pk=share.pk).update(
                last_price=last_price, is_trend_high=is_trend_high
            )
            process_market_price(share, last_price, captured_at)
        except Exception as e:
            logger.exception("Could not update market data for share %s: %s", share.pk, e)
