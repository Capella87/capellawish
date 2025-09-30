from django.urls.conf import include, path

from wishlist.views import WishListView

urlpatterns = [
    path('', WishListView.as_view(), name='wishlist')
]
