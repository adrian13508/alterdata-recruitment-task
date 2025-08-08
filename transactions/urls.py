from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.TransactionUploadView.as_view(), name='transaction-upload'),
    path('task/<str:task_id>/', views.TaskStatusView.as_view(), name='task-status'),
    path('', views.TransactionListView.as_view(), name='transaction-list'),
    path('<uuid:transaction_id>/', views.TransactionDetailView.as_view(), name='transaction-detail'),
]