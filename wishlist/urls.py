from django.urls.conf import include, path

from wishlist.views import WishListView, WishListItemDetailView

urlpatterns = [
    path('', WishListView.as_view(), name='wishlist'),
    path('<str:uuid>', WishListItemDetailView.as_view(), name='wishlist-item-detail'),
]
