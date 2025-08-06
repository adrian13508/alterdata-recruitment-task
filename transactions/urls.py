from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.TransactionUploadView.as_view(), name='transaction-upload'),
    path('', views.TransactionListView.as_view(), name='transaction-list'),
    path('<uuid:transaction_id>/', views.TransactionDetailView.as_view(), name='transaction-detail'),
]