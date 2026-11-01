from datetime import datetime, timedelta, timezone

from plotly.graph_objs import Scatter
from plotly.offline import plot

from config.settings import TINKOFF_TOKEN

try:
    from tinkoff.invest import CandleInterval, Client
except ImportError:  # pragma: no cover - optional dependency for runtime-only features
    CandleInterval = None
    Client = None


def get_graph(share):
    if not TINKOFF_TOKEN or Client is None or CandleInterval is None:
        return "<div>Данные по графику временно недоступны.</div>"

    try:
        with Client(TINKOFF_TOKEN) as client:
            x_data, y_data = [], []
            candles = client.market_data.get_all_candles(
                figi=share.figi,
                from_=datetime.now(timezone.utc) - timedelta(days=180),
                interval=CandleInterval.CANDLE_INTERVAL_DAY,
            )
            for candle in candles:
                x_data.append(candle.time.date())
                y_data.append(float(candle.close.units or 0))

        plot_div = plot(
            [
                Scatter(
                    x=x_data,
                    y=y_data,
                    mode="lines",
                    name=share.ticker,
                    opacity=0.8,
                    marker_color="red",
                )
            ],
            output_type="div",
            show_link=False,
            link_text="",
        )
        return plot_div
    except Exception:
        return "<div>Не удалось загрузить историю цен по акции.</div>"
