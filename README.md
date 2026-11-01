# Investing Demo

## Local development

```bash
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

SQLite is used by default. To use PostgreSQL, set `USE_SQLITE=0` and the
`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, and
`POSTGRES_PORT` environment variables, then start `docker-compose.yml`.

## Market data and automatic features

Set `TINKOFF_TOKEN` in the environment and make the Tinkoff Invest SDK
available to Python to enable live prices and candles. Without the SDK/token,
the site remains usable but live price polling is skipped.

Start Redis, then run Celery Beat and a worker in separate terminals:

```bash
celery -A config beat
celery -A config worker -l info
```

Successful price updates are saved to history and drive watchlist alerts and
investment-strategy simulations.

## Application features

- Public share catalog and share details with price-history charts.
- Authenticated watchlists with above/below price alerts and an in-app
  notification feed.
- Virtual portfolios with simulated buys/sells, holdings, average acquisition
  price, valuation, profit/loss, and transaction history.
- Price-history periods (7/30/90/180/365 days) with absolute and percentage
  change calculations.
- Automated investment-strategy simulations, trade logs, and profit/loss
  summaries.
- Shares API: `/api/v1/shares/`.

Run tests with:

```bash
.venv/bin/python manage.py test
```
