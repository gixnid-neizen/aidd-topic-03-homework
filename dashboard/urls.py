from django.urls import include, path

from dashboard.views import (
    ShareCreateView,
    ShareDeleteView,
    ShareDetailView,
    ShareListView,
    ShareUpdateView,
    notification_list,
    portfolio_detail,
    portfolio_list,
    share_price_history,
    strategy_list,
    strategy_toggle,
    watchlist_add_item,
    watchlist_list,
    watchlist_remove_item,
)

app_name = "dashboard"

urlpatterns = [
    path("", ShareListView.as_view(), name="index"),
    path("<int:pk>", ShareDetailView.as_view(), name="detail"),
    path("create", ShareCreateView.as_view(), name="create"),
    path("update/<int:pk>", ShareUpdateView.as_view(), name="update"),
    path("delete/<int:pk>", ShareDeleteView.as_view(), name="delete"),
    path("watchlists/", watchlist_list, name="watchlists"),
    path(
        "watchlists/<int:pk>/items/add/",
        watchlist_add_item,
        name="watchlist-add-item",
    ),
    path(
        "watchlist-items/<int:pk>/remove/",
        watchlist_remove_item,
        name="watchlist-remove-item",
    ),
    path("notifications/", notification_list, name="notifications"),
    path("portfolios/", portfolio_list, name="portfolios"),
    path(
        "portfolios/<int:pk>/",
        portfolio_detail,
        name="portfolio-detail",
    ),
    path("shares/<int:pk>/history/", share_price_history, name="price-history"),
    path("strategies/", strategy_list, name="strategies"),
    path(
        "strategies/<int:pk>/toggle/",
        strategy_toggle,
        name="strategy-toggle",
    ),
    path("api/", include("dashboard.api.urls")),
]
