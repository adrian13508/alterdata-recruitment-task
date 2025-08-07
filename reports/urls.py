from django.urls import path
from . import views

urlpatterns = [
    path('customer-summary/<uuid:customer_id>/', views.CustomerSummaryView.as_view(), name='customer-summary'),
    path('product-summary/<uuid:product_id>/', views.ProductSummaryView.as_view(), name='product-summary'),
    path('top-customers/', views.TopCustomersView.as_view(), name='top-customers'),
    path('top-products/', views.TopProductsView.as_view(), name='top-products'),
]