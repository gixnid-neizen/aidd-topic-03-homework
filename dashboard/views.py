from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, View, UpdateView
from plotly.graph_objs import Scatter
from plotly.offline import plot

from .forms import (
    InvestmentStrategyForm,
    PortfolioForm,
    PortfolioTradeForm,
    ShareModelForm,
    WatchlistForm,
    WatchlistItemForm,
)
from .models import (
    InvestmentStrategy,
    Portfolio,
    PriceAlertNotification,
    Share,
    Watchlist,
    WatchlistItem,
)
from .services.graph import get_graph
from .services.investments import (
    execute_portfolio_trade,
    get_portfolio_summary,
    get_price_history_summary,
    get_strategy_summary,
)
from django.contrib.auth.mixins import UserPassesTestMixin


class IsUserAuthenticatedMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated

    @staticmethod
    def handle_no_permission():
        return redirect("dashboard:index")


class ShareListView(ListView):
    """Список акций"""

    model = Share
    template_name = "dashboard/list.html"
    paginate_by = 100
    ordering = ["name"]


class ShareDetailView(View):
    @staticmethod
    def get(request, pk):
        share = get_object_or_404(Share, id=pk)

        return render(
            request,
            "dashboard/detail.html",
            {"plot_div": get_graph(share), "share": share},
        )


class ShareCreateView(IsUserAuthenticatedMixin, CreateView):
    """Добавление инструмента"""

    template_name = "dashboard/create.html"
    form_class = ShareModelForm
    success_url = reverse_lazy("dashboard:index")


class ShareUpdateView(IsUserAuthenticatedMixin, UpdateView):
    """Редактирование инструмента"""

    model = Share
    template_name = "dashboard/create.html"
    form_class = ShareModelForm
    success_url = reverse_lazy("dashboard:index")


class ShareDeleteView(IsUserAuthenticatedMixin, DeleteView):
    """Удаление задачи"""

    model = Share
    template_name = "dashboard/delete.html"
    success_url = reverse_lazy("dashboard:index")


@login_required
def watchlist_list(request):
    if request.method == "POST":
        form = WatchlistForm(request.POST)
        if form.is_valid():
            if request.user.watchlists.filter(name=form.cleaned_data["name"]).exists():
                form.add_error("name", "A watchlist with this name already exists.")
            else:
                watchlist = form.save(commit=False)
                watchlist.user = request.user
                watchlist.save()
                return redirect("dashboard:watchlists")
    else:
        form = WatchlistForm()
    return render(
        request,
        "dashboard/watchlists.html",
        {"watchlists": request.user.watchlists.prefetch_related("items__share"), "form": form},
    )


@login_required
def watchlist_add_item(request, pk):
    watchlist = get_object_or_404(Watchlist, pk=pk, user=request.user)
    if request.method == "POST":
        form = WatchlistItemForm(request.POST)
        if form.is_valid():
            if watchlist.items.filter(share=form.cleaned_data["share"]).exists():
                form.add_error("share", "This share is already in the watchlist.")
            else:
                item = form.save(commit=False)
                item.watchlist = watchlist
                item.save()
                return redirect("dashboard:watchlists")
    else:
        form = WatchlistItemForm()
    return render(
        request,
        "dashboard/watchlist_item_form.html",
        {"watchlist": watchlist, "form": form},
    )


@login_required
def watchlist_remove_item(request, pk):
    item = get_object_or_404(
        WatchlistItem, pk=pk, watchlist__user=request.user
    )
    if request.method == "POST":
        item.delete()
    return redirect("dashboard:watchlists")


@login_required
def notification_list(request):
    notifications = PriceAlertNotification.objects.filter(
        item__watchlist__user=request.user
    ).select_related("item__share", "item__watchlist")
    return render(
        request, "dashboard/notifications.html", {"notifications": notifications}
    )


@login_required
def portfolio_list(request):
    if request.method == "POST":
        form = PortfolioForm(request.POST)
        if form.is_valid():
            if request.user.portfolios.filter(name=form.cleaned_data["name"]).exists():
                form.add_error("name", "A portfolio with this name already exists.")
            else:
                portfolio = form.save(commit=False)
                portfolio.user = request.user
                portfolio.save()
                return redirect("dashboard:portfolios")
    else:
        form = PortfolioForm()
    return render(
        request,
        "dashboard/portfolios.html",
        {"portfolios": request.user.portfolios.all(), "form": form},
    )


@login_required
def portfolio_detail(request, pk):
    portfolio = get_object_or_404(Portfolio, pk=pk, user=request.user)
    form = PortfolioTradeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            execute_portfolio_trade(
                portfolio=portfolio,
                share=form.cleaned_data["share"],
                side=form.cleaned_data["side"],
                quantity=form.cleaned_data["quantity"],
                price=form.cleaned_data["price"],
            )
        except ValueError as error:
            form.add_error(None, str(error))
        else:
            messages.success(request, "Trade recorded.")
            return redirect("dashboard:portfolio-detail", pk=portfolio.pk)

    return render(
        request,
        "dashboard/portfolio_detail.html",
        {
            "portfolio": portfolio,
            "form": form,
            "summary": get_portfolio_summary(portfolio),
            "trades": portfolio.trades.select_related("share"),
        },
    )


def share_price_history(request, pk):
    share = get_object_or_404(Share, pk=pk)
    try:
        days = int(request.GET.get("days", 30))
    except (TypeError, ValueError):
        days = 30
    if days not in (7, 30, 90, 180, 365):
        days = 30
    summary = get_price_history_summary(share, days)
    summary["plot_div"] = plot(
        [
            Scatter(
                x=[entry.captured_at for entry in summary["entries"]],
                y=[float(entry.price) for entry in summary["entries"]],
                mode="lines",
                name=share.ticker,
            )
        ],
        output_type="div",
        show_link=False,
        link_text="",
    )
    return render(
        request,
        "dashboard/price_history.html",
        {"share": share, "days": days, **summary},
    )


@login_required
def strategy_list(request):
    if request.method == "POST":
        form = InvestmentStrategyForm(request.POST)
        if form.is_valid():
            if request.user.investment_strategies.filter(
                name=form.cleaned_data["name"]
            ).exists():
                form.add_error("name", "A strategy with this name already exists.")
            else:
                strategy = form.save(commit=False)
                strategy.user = request.user
                strategy.save()
                return redirect("dashboard:strategies")
    else:
        form = InvestmentStrategyForm()
    strategies = request.user.investment_strategies.select_related("share").prefetch_related(
        "trades"
    )
    strategy_data = [
        {"strategy": strategy, "summary": get_strategy_summary(strategy)}
        for strategy in strategies
    ]
    return render(
        request,
        "dashboard/strategies.html",
        {"strategies": strategy_data, "form": form},
    )


@login_required
def strategy_toggle(request, pk):
    strategy = get_object_or_404(InvestmentStrategy, pk=pk, user=request.user)
    if request.method == "POST":
        strategy.is_active = not strategy.is_active
        strategy.save(update_fields=("is_active",))
    return redirect("dashboard:strategies")
