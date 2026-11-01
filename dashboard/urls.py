from django.urls import include, path

from dashboard.views import (
    PriceAlertCreateView,
    PriceAlertDeleteView,
    PriceAlertListView,
    ShareCreateView,
    ShareDeleteView,
    ShareDetailView,
    ShareListView,
    ShareUpdateView,
    WatchlistAddView,
    WatchlistListView,
    WatchlistRemoveView,
)

app_name = "dashboard"

urlpatterns = [
    path("", ShareListView.as_view(), name="index"),
    path("<int:pk>", ShareDetailView.as_view(), name="detail"),
    path("create", ShareCreateView.as_view(), name="create"),
    path("update/<int:pk>", ShareUpdateView.as_view(), name="update"),
    path("delete/<int:pk>", ShareDeleteView.as_view(), name="delete"),
    path("watchlist/", WatchlistListView.as_view(), name="watchlist"),
    path(
        "watchlist/add/<int:pk>/",
        WatchlistAddView.as_view(),
        name="watchlist_add",
    ),
    path(
        "watchlist/remove/<int:pk>/",
        WatchlistRemoveView.as_view(),
        name="watchlist_remove",
    ),
    path("alerts/", PriceAlertListView.as_view(), name="alerts"),
    path(
        "alerts/create/",
        PriceAlertCreateView.as_view(),
        name="alerts_create",
    ),
    path(
        "alerts/delete/<int:pk>/",
        PriceAlertDeleteView.as_view(),
        name="alerts_delete",
    ),
    path("api/", include("dashboard.api.urls")),
]
