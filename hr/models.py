from django.db import models
from decimal import Decimal
from django.utils import timezone


class Employee(models.Model):
    """Працівник"""
    
    # Основна інформація
    full_name = models.CharField(max_length=200, verbose_name="ПІБ")
    pesel = models.CharField(max_length=11, verbose_name="PESEL")
    email = models.EmailField(verbose_name="Email")
    birth_date = models.DateField(verbose_name="Дата народження")
    address = models.TextField(verbose_name="Адреса")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Працівник"
        verbose_name_plural = "Працівники"
        ordering = ['full_name']
    
    def __str__(self):
        return self.full_name


class Contract(models.Model):
    """Умова праці / Договір"""
    
    TYPE_CHOICES = [
        ('umowa_o_prace', 'Umowa o pracę'),
        ('zlecenie', 'Zlecenie'),
        ('staz', 'Staż'),
    ]
    
    employee = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE, 
        related_name='contracts',
        verbose_name="Працівник"
    )
    
    # Умови праці
    position = models.CharField(max_length=200, verbose_name="Посада")
    start_date = models.DateField(verbose_name="Дата початку праці")
    contract_type = models.CharField(
        max_length=20, 
        choices=TYPE_CHOICES, 
        verbose_name="Тип умови"
    )
    weekly_hours = models.PositiveIntegerField(
        default=40, 
        verbose_name="Години праці на тиждень"
    )
    
    # Зарплата
    hourly_rate_brutto = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Ставка за годину (brutto PLN)"
    )
    salary_netto = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Зарплата нетто (PLN)"
    )
    salary_brutto = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Зарплата брутто (PLN)"
    )
    
    # Договір
    generated_at = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="Дата генерації договору"
    )
    pdf_file = models.FileField(
        upload_to='hr/contracts/', 
        null=True, 
        blank=True,
        verbose_name="PDF договору"
    )
    
    # Табель робочого часу
    timesheet_pdf = models.FileField(
        upload_to='hr/timesheets/', 
        null=True, 
        blank=True,
        verbose_name="PDF табелю"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Договір"
        verbose_name_plural = "Договори"
        ordering = ['-start_date']
    
    def calculate_total_salary(self):
        """Рахує загальну зарплату якщо є погодинна ставка"""
        if self.hourly_rate_brutto and self.weekly_hours:
            # Приблизно 4.33 тижні в місяці
            return self.hourly_rate_brutto * self.weekly_hours * Decimal('4.33')
        return self.salary_brutto or 0
    
    def calculate_hourly_rate(self):
        """Автоматично рахує ставку за годину з місячної зарплати"""
        if self.salary_brutto and self.weekly_hours:
            # salary_brutto / (weekly_hours * 4.33 тижнів в місяці)
            from decimal import Decimal
            monthly_hours = Decimal(self.weekly_hours) * Decimal('4.33')
            return self.salary_brutto / monthly_hours
        return None
    
    def save(self, *args, **kwargs):
        """Автоматично рахує ставку за годину якщо вона не вказана але є місячна зарплата"""
        if not self.hourly_rate_brutto and self.salary_brutto and self.weekly_hours:
            self.hourly_rate_brutto = self.calculate_hourly_rate()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.position} ({self.get_contract_type_display()})"


class WorkLog(models.Model):
    """Табель робочого часу"""
    
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='work_logs',
        verbose_name="Працівник"
    )
    
    date = models.DateField(verbose_name="Дата")
    hours_worked = models.DecimalField(
        max_digits=4, 
        decimal_places=2, 
        verbose_name="Годин відпрацьовано"
    )
    comment = models.TextField(blank=True, verbose_name="Коментар")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Запис табелю"
        verbose_name_plural = "Табель робочого часу"
        ordering = ['-date']
        unique_together = ['employee', 'date']
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.date} ({self.hours_worked}h)"
