from datetime import timedelta

from plotly.graph_objs import Scatter
from plotly.offline import plot

from config.settings import TINKOFF_TOKEN

try:
    from tinkoff.invest import CandleInterval, Client
    from tinkoff.invest.utils import now

    _TINKOFF_AVAILABLE = True
except Exception:  # tinkoff-investments не установлен и/или токена нет
    Client = None
    CandleInterval = None
    now = None
    _TINKOFF_AVAILABLE = False


def get_graph(share):
    """Возвращает HTML-блок графика или пустую строку, если Tinkoff API недоступен."""
    if not _TINKOFF_AVAILABLE or not TINKOFF_TOKEN:
        return ""
    with Client(TINKOFF_TOKEN) as client:
        x_data, y_data = [], []
        for candle in client.get_all_candles(
            figi=share.figi,
            from_=now() - timedelta(days=180),
            interval=CandleInterval.CANDLE_INTERVAL_DAY,
        ):
            x_data.append(candle.time.date())
            y_data.append(candle.close.units)
    plot_div = plot(
        [
            Scatter(
                x=x_data,
                y=y_data,
                mode="lines",
                name="test",
                opacity=0.8,
                marker_color="red",
            )
        ],
        output_type="div",
        show_link=False,
        link_text="",
    )
    return plot_div
