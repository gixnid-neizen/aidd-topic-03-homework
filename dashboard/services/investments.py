from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import Q, Sum
from django.utils import timezone

from dashboard.models import (
    InvestmentStrategy,
    Portfolio,
    PortfolioTrade,
    PriceAlertNotification,
    PriceHistory,
    StrategyTrade,
    WatchlistItem,
)


def _decimal(value):
    return Decimal(str(value))


def capture_share_price(share, price, captured_at=None):
    price = _decimal(price)
    if price <= 0:
        return None
    captured_at = captured_at or timezone.now()
    try:
        snapshot, _ = PriceHistory.objects.update_or_create(
            share=share,
            captured_at=captured_at,
            defaults={"price": price},
        )
    except IntegrityError:
        snapshot = PriceHistory.objects.get(share=share, captured_at=captured_at)
    return snapshot


def evaluate_price_alerts(share, price):
    price = _decimal(price)
    for item in WatchlistItem.objects.filter(
        share=share, target_price__isnull=False
    ).select_related("watchlist"):
        is_met = (
            price >= item.target_price
            if item.direction == WatchlistItem.ABOVE
            else price <= item.target_price
        )
        if not is_met:
            WatchlistItem.objects.filter(pk=item.pk, is_triggered=True).update(
                is_triggered=False
            )
            continue

        with transaction.atomic():
            changed = WatchlistItem.objects.filter(
                pk=item.pk, is_triggered=False
            ).update(is_triggered=True, last_triggered_at=timezone.now())
            if changed:
                PriceAlertNotification.objects.create(item=item, price=price)


def _strategy_position(strategy):
    totals = strategy.trades.aggregate(
        bought=Sum("quantity", filter=Q(side=PortfolioTrade.BUY)),
        sold=Sum("quantity", filter=Q(side=PortfolioTrade.SELL)),
    )
    return (totals["bought"] or 0) - (totals["sold"] or 0)


def evaluate_strategies(share, price):
    price = _decimal(price)
    with transaction.atomic():
        strategies = InvestmentStrategy.objects.select_for_update().filter(
            share=share, is_active=True
        )
        for strategy in strategies:
            held_quantity = _strategy_position(strategy)
            if held_quantity and strategy.sell_above and price >= strategy.sell_above:
                StrategyTrade.objects.create(
                    strategy=strategy,
                    side=PortfolioTrade.SELL,
                    quantity=held_quantity,
                    price=price,
                )
            elif (
                not held_quantity
                and strategy.buy_below
                and price <= strategy.buy_below
            ):
                StrategyTrade.objects.create(
                    strategy=strategy,
                    side=PortfolioTrade.BUY,
                    quantity=strategy.quantity,
                    price=price,
                )


def process_market_price(share, price, captured_at=None):
    snapshot = capture_share_price(share, price, captured_at)
    if snapshot is None:
        return None
    evaluate_price_alerts(share, snapshot.price)
    evaluate_strategies(share, snapshot.price)
    return snapshot


def execute_portfolio_trade(portfolio, share, side, quantity, price):
    original_quantity = _decimal(quantity)
    if original_quantity != original_quantity.to_integral_value():
        raise ValueError("Quantity must be a whole number.")
    quantity = int(original_quantity)
    price = _decimal(price)
    if quantity <= 0 or price <= 0:
        raise ValueError("Quantity and price must be greater than zero.")
    if side not in (PortfolioTrade.BUY, PortfolioTrade.SELL):
        raise ValueError("Trade side must be buy or sell.")

    with transaction.atomic():
        Portfolio.objects.select_for_update().get(pk=portfolio.pk)
        if side == PortfolioTrade.SELL:
            held = portfolio.trades.filter(share=share).aggregate(
                bought=Sum(
                    "quantity",
                    filter=Q(side=PortfolioTrade.BUY),
                ),
                sold=Sum(
                    "quantity",
                    filter=Q(side=PortfolioTrade.SELL),
                ),
            )
            available = (held["bought"] or 0) - (held["sold"] or 0)
            if quantity > available:
                raise ValueError(
                    f"Cannot sell {quantity} shares; only {available} are held."
                )
        return PortfolioTrade.objects.create(
            portfolio=portfolio,
            share=share,
            side=side,
            quantity=quantity,
            price=price,
        )


def get_portfolio_summary(portfolio):
    holdings = {}
    realized_profit = Decimal("0")
    for trade in portfolio.trades.select_related("share").order_by("executed_at", "pk"):
        holding = holdings.setdefault(
            trade.share_id,
            {
                "share": trade.share,
                "quantity": 0,
                "cost_basis": Decimal("0"),
                "realized_profit": Decimal("0"),
            },
        )
        if trade.side == PortfolioTrade.BUY:
            holding["quantity"] += trade.quantity
            holding["cost_basis"] += trade.price * trade.quantity
        else:
            average_cost = holding["cost_basis"] / holding["quantity"]
            holding["realized_profit"] += (
                trade.price - average_cost
            ) * trade.quantity
            holding["cost_basis"] -= average_cost * trade.quantity
            holding["quantity"] -= trade.quantity

    current_value = Decimal("0")
    invested_value = Decimal("0")
    priced_invested_value = Decimal("0")
    unpriced_positions = 0
    for holding in holdings.values():
        if not holding["quantity"]:
            continue
        share = holding["share"]
        holding["average_price"] = holding["cost_basis"] / holding["quantity"]
        holding["current_price"] = (
            _decimal(share.last_price) if share.last_price is not None else None
        )
        holding["current_value"] = (
            holding["current_price"] * holding["quantity"]
            if holding["current_price"] is not None
            else None
        )
        if holding["current_value"] is not None:
            current_value += holding["current_value"]
            priced_invested_value += holding["cost_basis"]
        else:
            unpriced_positions += 1
        invested_value += holding["cost_basis"]
        realized_profit += holding["realized_profit"]

    unrealized_profit = current_value - priced_invested_value
    return {
        "holdings": [item for item in holdings.values() if item["quantity"]],
        "current_value": current_value,
        "invested_value": invested_value,
        "priced_invested_value": priced_invested_value,
        "unpriced_positions": unpriced_positions,
        "unrealized_profit": unrealized_profit,
        "realized_profit": realized_profit,
        "total_profit": unrealized_profit + realized_profit,
    }


def get_price_history_summary(share, days=30):
    since = timezone.now() - timedelta(days=days)
    entries = list(share.price_history.filter(captured_at__gte=since))
    first_price = entries[0].price if entries else None
    last_price = entries[-1].price if entries else None
    absolute_change = (
        last_price - first_price
        if first_price is not None and last_price is not None
        else None
    )
    percentage_change = (
        absolute_change / first_price * 100
        if absolute_change is not None and first_price
        else None
    )
    return {
        "entries": entries,
        "first_price": first_price,
        "last_price": last_price,
        "absolute_change": absolute_change,
        "percentage_change": percentage_change,
    }


def get_strategy_summary(strategy):
    quantity = 0
    cost_basis = Decimal("0")
    realized_profit = Decimal("0")
    for trade in strategy.trades.order_by("executed_at", "pk"):
        if trade.side == PortfolioTrade.BUY:
            quantity += trade.quantity
            cost_basis += trade.price * trade.quantity
        elif quantity:
            average_price = cost_basis / quantity
            realized_profit += (trade.price - average_price) * trade.quantity
            cost_basis -= average_price * trade.quantity
            quantity -= trade.quantity

    current_price = (
        _decimal(strategy.share.last_price)
        if strategy.share.last_price is not None
        else None
    )
    current_value = (
        current_price * quantity if current_price is not None else None
    )
    unrealized_profit = (
        current_value - cost_basis
        if current_value is not None and quantity
        else Decimal("0")
    )
    return {
        "quantity": quantity,
        "current_value": current_value,
        "realized_profit": realized_profit,
        "unrealized_profit": unrealized_profit,
        "total_profit": realized_profit + unrealized_profit,
    }
