from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, View, UpdateView

from .forms import ShareModelForm, PriceAlertForm
from .models import Share, Watchlist, PriceAlert
from .services.graph import get_graph
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

class WatchlistListView(IsUserAuthenticatedMixin, ListView):
    """Список наблюдения пользователя"""

    model = Watchlist
    template_name = "dashboard/watchlist_list.html"
    context_object_name = "watchlist"

    def get_queryset(self):
        return Watchlist.objects.filter(user=self.request.user).select_related(
            "share"
        )


class WatchlistAddView(IsUserAuthenticatedMixin, View):
    """Добавить акцию в список наблюдения"""

    def post(self, request, pk):
        share = get_object_or_404(Share, id=pk)
        Watchlist.objects.get_or_create(user=request.user, share=share)
        return redirect("dashboard:watchlist")


class WatchlistRemoveView(IsUserAuthenticatedMixin, DeleteView):
    """Удалить акцию из списка наблюдения"""

    model = Watchlist
    template_name = "dashboard/watchlist_confirm_delete.html"
    success_url = reverse_lazy("dashboard:watchlist")

    def get_queryset(self):
        return Watchlist.objects.filter(user=self.request.user)


class PriceAlertListView(IsUserAuthenticatedMixin, ListView):
    """Список оповещений о целевой цене"""

    model = PriceAlert
    template_name = "dashboard/pricealert_list.html"
    context_object_name = "alerts"

    def get_queryset(self):
        return PriceAlert.objects.filter(user=self.request.user).select_related(
            "share"
        )


class PriceAlertCreateView(IsUserAuthenticatedMixin, CreateView):
    """Создать оповещение о целевой цене"""

    model = PriceAlert
    form_class = PriceAlertForm
    template_name = "dashboard/pricealert_form.html"
    success_url = reverse_lazy("dashboard:alerts")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class PriceAlertDeleteView(IsUserAuthenticatedMixin, DeleteView):
    """Удалить оповещение о целевой цене"""

    model = PriceAlert
    template_name = "dashboard/pricealert_confirm_delete.html"
    success_url = reverse_lazy("dashboard:alerts")

    def get_queryset(self):
        return PriceAlert.objects.filter(user=self.request.user)
