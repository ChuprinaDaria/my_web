from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Employee, Contract, WorkLog


class ContractInline(admin.TabularInline):
    model = Contract
    extra = 0
    fields = ('position', 'contract_type', 'start_date', 'salary_netto', 'salary_brutto')
    readonly_fields = ('generated_at',)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'email',
        'phone',
        'contracts_count',
        'created_at'
    )
    
    search_fields = ('full_name', 'email', 'phone')
    list_filter = ('created_at',)
    
    inlines = [ContractInline]
    
    fieldsets = (
        ('Основна інформація', {
            'fields': ('full_name', 'email', 'phone')
        }),
        ('Персональні дані (зашифровано)', {
            'fields': ('pesel', 'birth_date', 'address'),
            'classes': ('collapse',)
        }),
    )
    
    def contracts_count(self, obj):
        count = obj.contracts.count()
        return format_html(
            '<span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 10px;">{}</span>',
            count
        )
    contracts_count.short_description = '📄 Договорів'


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'position',
        'contract_type',
        'start_date',
        'salary_display',
        'status_badge',
        'actions_column'
    )
    
    list_filter = ('contract_type', 'start_date')
    search_fields = ('employee__full_name', 'position')
    
    readonly_fields = ('generated_at', 'pdf_file')
    
    fieldsets = (
        ('Працівник', {
            'fields': ('employee',)
        }),
        ('Умови праці', {
            'fields': ('position', 'contract_type', 'start_date', 'weekly_hours')
        }),
        ('Зарплата', {
            'fields': ('salary_netto', 'salary_brutto')
        }),
        ('Договір', {
            'fields': ('generated_at', 'pdf_file'),
            'classes': ('collapse',)
        }),
    )
    
    def salary_display(self, obj):
        return f"{obj.salary_netto} PLN (netto)"
    salary_display.short_description = '💰 Зарплата'
    
    def status_badge(self, obj):
        if obj.pdf_file:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 10px;">✅ Згенеровано</span>'
            )
        return format_html(
            '<span style="background: #dc3545; color: white; padding: 3px 8px; border-radius: 10px;">❌ Не згенеровано</span>'
        )
    status_badge.short_description = 'Статус'
    
    def actions_column(self, obj):
        if not obj.pdf_file:
            return format_html(
                '<a class="button" href="#">📄 Згенерувати договір</a>'
            )
        return format_html(
            '<a class="button" href="{}">📥 Завантажити PDF</a>',
            obj.pdf_file.url
        )
    actions_column.short_description = 'Дії'


@admin.register(WorkLog)
class WorkLogAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'hours_worked', 'comment')
    list_filter = ('date', 'employee')
    search_fields = ('employee__full_name',)
    date_hierarchy = 'date'
