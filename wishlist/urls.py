from django.urls.conf import include, path

from wishlist.views import WishListView, WishListItemDetailView, WishListItemImageViewSet

urlpatterns = [
    path('', WishListView.as_view(), name='wishlist'),
    path('<str:uuid>', WishListItemDetailView.as_view(), name='wishlist-item-detail'),
    path('<str:uuid>/image', WishListItemImageViewSet.as_view({ 'put': 'up' }),
         name='wishlist-item-image')
]
