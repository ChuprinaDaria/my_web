from django.urls import path
from . import views

app_name = 'consultant'

urlpatterns = [
    # Головна сторінка чату
    path('', views.consultant_chat, name='chat'),
    
    # API endpoints
    path('api/start-session/', views.start_chat_session, name='start_session'),
    path('api/send-message/', views.send_message, name='send_message'),
    path('api/chat-history/<uuid:session_id>/', views.get_chat_history, name='chat_history'),
    path('api/rate-chat/', views.rate_chat, name='rate_chat'),
    path('api/stats/', views.consultant_stats, name='stats'),
]
