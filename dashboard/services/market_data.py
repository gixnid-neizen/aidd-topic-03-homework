try:
    from tinkoff.invest import Client
    from config.settings import TINKOFF_TOKEN, logger

    _TINKOFF_AVAILABLE = True
except Exception:  # tinkoff-investments не установлен и/или токена нет
    Client = None
    logger = None
    TINKOFF_TOKEN = ""
    _TINKOFF_AVAILABLE = False


def get_last_data(share):
    """Возвращает [цена, время] или None, если Tinkoff API недоступен."""
    if not _TINKOFF_AVAILABLE or not TINKOFF_TOKEN:
        return None
    with Client(TINKOFF_TOKEN) as client:
        resp = client.market_data.get_last_prices(figi=[share.figi])
        resp = resp.last_prices.pop()
        logger.info(f"Get last data for share with id {share.id}")
        return [resp.price.units, resp.time]
