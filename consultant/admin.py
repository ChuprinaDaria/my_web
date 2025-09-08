from django.contrib import admin
from .models import ChatSession, Message, ConsultantProfile, KnowledgeBase, ChatAnalytics


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'user', 'created_at', 'is_active', 'user_ip']
    list_filter = ['is_active', 'created_at', 'user']
    search_fields = ['session_id', 'user__username', 'user_ip']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['role', 'content_preview', 'chat_session', 'created_at', 'is_processed']
    list_filter = ['role', 'is_processed', 'created_at']
    search_fields = ['content', 'chat_session__session_id']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Повідомлення'


@admin.register(ConsultantProfile)
class ConsultantProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'priority', 'is_active', 'created_at']
    list_filter = ['is_active', 'category', 'priority', 'created_at']
    search_fields = ['title', 'content', 'tags']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-priority', '-created_at']


@admin.register(ChatAnalytics)
class ChatAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['chat_session', 'total_messages', 'satisfaction_rating', 'created_at']
    list_filter = ['satisfaction_rating', 'created_at']
    search_fields = ['chat_session__session_id', 'feedback']
    readonly_fields = ['created_at']
    ordering = ['-created_at']