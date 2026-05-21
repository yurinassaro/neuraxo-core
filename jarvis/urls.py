from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.jarvis_chat, name='jarvis_chat'),
    path('reset/', views.jarvis_reset, name='jarvis_reset'),
]
