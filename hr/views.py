from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, FileResponse
from django.views.decorators.http import require_http_methods
from .models import Employee, Contract, WorkLog


@staff_member_required
def dashboard(request):
    """HR Dashboard"""
    context = {
        'total_employees': Employee.objects.count(),
        'total_contracts': Contract.objects.count(),
        'recent_contracts': Contract.objects.select_related('employee').order_by('-created_at')[:5],
        'recent_work_logs': WorkLog.objects.select_related('employee').order_by('-date')[:5],
    }
    return render(request, 'hr/dashboard.html', context)


@staff_member_required
def employee_list(request):
    """Список працівників"""
    employees = Employee.objects.all()
    context = {
        'employees': employees
    }
    return render(request, 'hr/employee_list.html', context)


@staff_member_required
def employee_detail(request, pk):
    """Деталі працівника"""
    employee = get_object_or_404(Employee, pk=pk)
    contracts = employee.contracts.all()
    recent_work_logs = employee.work_logs.all()[:10]
    
    context = {
        'employee': employee,
        'contracts': contracts,
        'recent_work_logs': recent_work_logs,
    }
    return render(request, 'hr/employee_detail.html', context)


@staff_member_required
def generate_contract_pdf(request, contract_id):
    """Генерація PDF договору"""
    from .utils import generate_contract_pdf
    
    contract = get_object_or_404(Contract, id=contract_id)
    
    try:
        pdf_path = generate_contract_pdf(contract)
        messages.success(request, f'Договір для {contract.employee.full_name} успішно згенеровано!')
    except ValueError as e:
        messages.error(request, f'Помилка: {str(e)}')
    except Exception as e:
        messages.error(request, f'Помилка генерації PDF: {str(e)}')
    
    # Редірект на admin сторінку договору
    return redirect('admin:hr_contract_change', contract.id)
