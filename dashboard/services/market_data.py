from config.settings import TINKOFF_TOKEN, logger

try:
    from tinkoff.invest import Client
except ImportError:  # pragma: no cover - optional dependency for runtime-only features
    Client = None


def get_last_data(share):
    if not TINKOFF_TOKEN or Client is None:
        logger.warning("Tinkoff token or SDK is missing; market update skipped.")
        return None, None

    with Client(TINKOFF_TOKEN) as client:
        resp = client.market_data.get_last_prices(figi=[share.figi])
        if not resp.last_prices:
            return None, None
        last_price = resp.last_prices[0]
        logger.info("Get last data for share with id %s", share.id)
        return float(last_price.price.units or 0), last_price.time
