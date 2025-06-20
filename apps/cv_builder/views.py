from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from .models import CVVersion, Experience, Education, Skill, CVTemplate
from .forms import CVVersionForm, ExperienceForm, EducationForm
from .services import generate_pdf_cv

@login_required
def cv_dashboard(request):
    """Главная страница управления CV"""
    cv_versions = CVVersion.objects.filter(user=request.user).order_by('-updated_at')
    experiences = Experience.objects.filter(user=request.user).order_by('-start_date')
    education = Education.objects.filter(user=request.user).order_by('-start_date')
    
    context = {
        'cv_versions': cv_versions,
        'experiences': experiences,
        'education': education,
    }
    return render(request, 'cv_builder/dashboard.html', context)

@login_required
def cv_version_create(request):
    """Создание новой версии CV"""
    if request.method == 'POST':
        form = CVVersionForm(request.POST, user=request.user)
        if form.is_valid():
            cv_version = form.save(commit=False)
            cv_version.user = request.user
            cv_version.save()
            form.save_m2m()
            messages.success(request, 'CV версия успешно создана!')
            return redirect('cv_builder:cv_version_detail', pk=cv_version.pk)
    else:
        form = CVVersionForm(user=request.user)
    
    return render(request, 'cv_builder/cv_version_form.html', {'form': form})

@login_required
def cv_version_detail(request, pk):
    """Детальный просмотр версии CV"""
    cv_version = get_object_or_404(CVVersion, pk=pk, user=request.user)
    return render(request, 'cv_builder/cv_version_detail.html', {'cv_version': cv_version})

@login_required
def cv_version_edit(request, pk):
    """Редактирование версии CV"""
    cv_version = get_object_or_404(CVVersion, pk=pk, user=request.user)
    if request.method == 'POST':
        form = CVVersionForm(request.POST, instance=cv_version, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'CV версия успешно обновлена!')
            return redirect('cv_builder:cv_version_detail', pk=cv_version.pk)
    else:
        form = CVVersionForm(instance=cv_version, user=request.user)
    
    return render(request, 'cv_builder/cv_version_form.html', {'form': form, 'cv_version': cv_version})

@login_required
def cv_export_pdf(request, pk):
    """Экспорт CV в PDF"""
    cv_version = get_object_or_404(CVVersion, pk=pk, user=request.user)
    try:
        pdf_file = generate_pdf_cv(cv_version)
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{cv_version.name}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f'Ошибка при генерации PDF: {str(e)}')
        return redirect('cv_builder:cv_version_detail', pk=pk)

@login_required
def experience_create(request):
    """Создание нового опыта работы"""
    if request.method == 'POST':
        form = ExperienceForm(request.POST)
        if form.is_valid():
            experience = form.save(commit=False)
            experience.user = request.user
            experience.save()
            form.save_m2m()
            messages.success(request, 'Опыт работы успешно добавлен!')
            return redirect('cv_builder:cv_dashboard')
    else:
        form = ExperienceForm()
    
    return render(request, 'cv_builder/experience_form.html', {'form': form})

@login_required
def education_create(request):
    """Создание нового образования"""
    if request.method == 'POST':
        form = EducationForm(request.POST)
        if form.is_valid():
            education = form.save(commit=False)
            education.user = request.user
            education.save()
            messages.success(request, 'Образование успешно добавлено!')
            return redirect('cv_builder:cv_dashboard')
    else:
        form = EducationForm()
    
    return render(request, 'cv_builder/education_form.html', {'form': form}) 