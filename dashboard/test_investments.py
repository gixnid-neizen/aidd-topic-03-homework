from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from dashboard.models import (
    InvestmentStrategy,
    Portfolio,
    PortfolioTrade,
    PriceHistory,
    Share,
    StrategyTrade,
    Watchlist,
    WatchlistItem,
)
from dashboard.services.investments import (
    capture_share_price,
    evaluate_price_alerts,
    evaluate_strategies,
    execute_portfolio_trade,
    get_portfolio_summary,
    get_price_history_summary,
    get_strategy_summary,
)


class InvestmentFeatureTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="investor", email="investor@example.com", password="StrongPass123!"
        )
        self.share = Share.objects.create(
            figi="FIGI-1",
            isin="ISIN-1",
            name="Example Inc.",
            ticker="EXM",
            currency="usd",
            uid="UID-1",
            last_price=120,
        )

    def test_watchlist_alert_creates_one_notification_per_crossing(self):
        watchlist = Watchlist.objects.create(user=self.user, name="Targets")
        item = WatchlistItem.objects.create(
            watchlist=watchlist,
            share=self.share,
            target_price=Decimal("110"),
            direction=WatchlistItem.ABOVE,
        )

        evaluate_price_alerts(self.share, Decimal("111"))
        evaluate_price_alerts(self.share, Decimal("115"))
        self.assertEqual(item.notifications.count(), 1)

        evaluate_price_alerts(self.share, Decimal("100"))
        evaluate_price_alerts(self.share, Decimal("111"))
        self.assertEqual(item.notifications.count(), 2)

    def test_portfolio_trades_calculate_average_cost_and_profit(self):
        portfolio = Portfolio.objects.create(user=self.user, name="Long term")
        execute_portfolio_trade(
            portfolio, self.share, PortfolioTrade.BUY, 10, Decimal("100")
        )
        execute_portfolio_trade(
            portfolio, self.share, PortfolioTrade.SELL, 4, Decimal("130")
        )

        summary = get_portfolio_summary(portfolio)
        holding = summary["holdings"][0]
        self.assertEqual(holding["quantity"], 6)
        self.assertEqual(holding["average_price"], Decimal("100"))
        self.assertEqual(holding["current_value"], Decimal("720"))
        self.assertEqual(summary["realized_profit"], Decimal("120"))
        self.assertEqual(summary["unrealized_profit"], Decimal("120"))
        self.assertEqual(summary["total_profit"], Decimal("240"))

    def test_portfolio_rejects_sale_larger_than_position(self):
        portfolio = Portfolio.objects.create(user=self.user, name="Guard")
        with self.assertRaisesMessage(ValueError, "only 0 are held"):
            execute_portfolio_trade(
                portfolio, self.share, PortfolioTrade.SELL, 1, Decimal("100")
            )

    def test_price_history_upserts_duplicate_timestamp_and_calculates_change(self):
        timestamp = timezone.now() - timedelta(days=1)
        capture_share_price(self.share, Decimal("100"), timestamp)
        capture_share_price(self.share, Decimal("125"), timestamp)
        capture_share_price(self.share, Decimal("150"))

        self.assertEqual(PriceHistory.objects.filter(share=self.share).count(), 2)
        summary = get_price_history_summary(self.share, 30)
        self.assertEqual(summary["absolute_change"], Decimal("25"))
        self.assertEqual(summary["percentage_change"], Decimal("20"))

    def test_price_history_view_renders_selected_range(self):
        capture_share_price(self.share, Decimal("100"), timezone.now())
        response = self.client.get(
            reverse("dashboard:price-history", args=[self.share.pk]),
            {"days": "90"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "История цены")
        self.assertContains(response, "Абсолютное изменение")

    def test_strategy_only_trades_when_position_changes(self):
        strategy = InvestmentStrategy.objects.create(
            user=self.user,
            name="Buy low",
            share=self.share,
            buy_below=Decimal("100"),
            sell_above=Decimal("110"),
            quantity=3,
        )
        evaluate_strategies(self.share, Decimal("95"))
        evaluate_strategies(self.share, Decimal("90"))
        evaluate_strategies(self.share, Decimal("115"))
        evaluate_strategies(self.share, Decimal("120"))

        trades = list(strategy.trades.all())
        self.assertEqual([trade.side for trade in trades], ["buy", "sell"])
        self.assertEqual([trade.quantity for trade in trades], [3, 3])
        self.assertEqual(StrategyTrade.objects.filter(strategy=strategy).count(), 2)
        summary = get_strategy_summary(strategy)
        self.assertEqual(summary["quantity"], 0)
        self.assertEqual(summary["realized_profit"], Decimal("60"))
        self.assertEqual(summary["total_profit"], Decimal("60"))

    def test_feature_pages_are_user_scoped_and_render(self):
        self.client.force_login(self.user)
        watchlist = Watchlist.objects.create(user=self.user, name="Private")
        portfolio = Portfolio.objects.create(user=self.user, name="Private portfolio")

        self.assertEqual(self.client.get(reverse("dashboard:watchlists")).status_code, 200)
        self.assertEqual(self.client.get(reverse("dashboard:portfolios")).status_code, 200)
        self.assertEqual(
            self.client.get(
                reverse("dashboard:portfolio-detail", args=[portfolio.pk])
            ).status_code,
            200,
        )
        self.assertEqual(self.client.get(reverse("dashboard:strategies")).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("dashboard:notifications")).status_code, 200
        )
        self.assertEqual(
            self.client.get(
                reverse("dashboard:watchlist-add-item", args=[watchlist.pk])
            ).status_code,
            200,
        )

    def test_feature_views_persist_user_data(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("dashboard:watchlists"), {"name": "Growth"}
        )
        self.assertRedirects(response, reverse("dashboard:watchlists"))
        watchlist = Watchlist.objects.get(user=self.user, name="Growth")
        response = self.client.post(
            reverse("dashboard:watchlist-add-item", args=[watchlist.pk]),
            {
                "share": self.share.pk,
                "target_price": "125",
                "direction": WatchlistItem.ABOVE,
            },
        )
        self.assertRedirects(response, reverse("dashboard:watchlists"))
        self.assertTrue(watchlist.items.filter(share=self.share).exists())

        response = self.client.post(
            reverse("dashboard:portfolios"), {"name": "Demo"}
        )
        self.assertRedirects(response, reverse("dashboard:portfolios"))
        portfolio = Portfolio.objects.get(user=self.user, name="Demo")
        response = self.client.post(
            reverse("dashboard:portfolio-detail", args=[portfolio.pk]),
            {
                "share": self.share.pk,
                "side": PortfolioTrade.BUY,
                "quantity": "2",
                "price": "100",
            },
        )
        self.assertRedirects(
            response, reverse("dashboard:portfolio-detail", args=[portfolio.pk])
        )
        self.assertEqual(portfolio.trades.count(), 1)

    def test_private_portfolio_cannot_be_opened_by_another_user(self):
        other_user = get_user_model().objects.create_user(
            username="other", email="other@example.com", password="StrongPass123!"
        )
        portfolio = Portfolio.objects.create(user=other_user, name="Private")
        watchlist = Watchlist.objects.create(user=other_user, name="Private")
        self.client.force_login(self.user)
        self.assertEqual(
            self.client.get(
                reverse("dashboard:portfolio-detail", args=[portfolio.pk])
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(
                reverse("dashboard:watchlist-add-item", args=[watchlist.pk])
            ).status_code,
            404,
        )

    def test_strategy_form_rejects_overlapping_thresholds(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("dashboard:strategies"),
            {
                "name": "Invalid",
                "share": self.share.pk,
                "buy_below": "110",
                "sell_above": "100",
                "quantity": "1",
                "is_active": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(InvestmentStrategy.objects.filter(name="Invalid").exists())
