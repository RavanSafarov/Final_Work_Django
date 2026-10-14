from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count


from .forms import RegisterForm, LoginForm, UserProfileForm
from .models import User
from skills.models import SessionRequest, Favorite, SkillOffer, Review
from skills.views import is_mod, is_superadmin, access_denied, not_found


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
            )
            login(request, user)
            messages.success(request, 'Добро пожаловать в SkillSwap!')
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data['username_or_email'].strip()
            password = form.cleaned_data['password']

            username = identifier
            if '@' in identifier:
                found = User.objects.filter(email__iexact=identifier).first()
                if found:
                    username = found.username

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Вы вошли в аккаунт.')
                return redirect('home')
            form.add_error(None, 'Неверный username/email или пароль.')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    if request.method != 'POST':
        return redirect('home')
    logout(request)
    messages.info(request, 'Вы вышли из аккаунта.')
    return redirect('home')


@login_required
def profile_view(request):
    user = request.user

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль обновлён.')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user)

    context = {
        'form': form,
        'user_offers': SkillOffer.objects.filter(author=user).select_related('category'),
        'sent_requests': SessionRequest.objects.filter(student=user).select_related('offer', 'teacher'),
        'received_requests': SessionRequest.objects.filter(teacher=user).select_related('offer', 'student'),
        'favorites': Favorite.objects.filter(user=user).select_related('offer', 'offer__author'),
        'reviews': Review.objects.filter(offer__author=user).select_related('user', 'offer'),
    }
    return render(request, 'accounts/profile.html', context)


def public_profile_view(request, username):
    profile_user = get_object_or_404(User.objects.prefetch_related('offers__reviews'), username=username)
    offers = (SkillOffer.objects.filter(author=profile_user, status='published').select_related('category'))

    context = {
        'profile_user': profile_user,
        'offers': offers,
        'reviews': Review.objects.filter(offer__author=profile_user).select_related('user', 'offer'),
    }
    return render(request, 'accounts/public_profile.html', context)


def mentor_list(request):
    mentors = (User.objects.filter(offers__status='published').annotate(offers_count=Count('offers', distinct=True)).prefetch_related('offers__reviews'))
    return render(request, 'accounts/mentor_list.html', {'mentors': mentors})


def can_manage(actor, target):
    if target.pk == actor.pk:
        return False
    if target.is_superuser:
        return False
    if target.role == User.Role.SUPERADMIN:
        return False
    return True


@login_required
def user_list(request):
    if not is_mod(request.user):
        return access_denied(request)

    users = User.objects.exclude(pk=request.user.pk).order_by('username')
    return render(request, 'accounts/user_list.html', {'users': users})


@login_required
def toggle_ban(request, user_id):
    if not is_mod(request.user):
        return access_denied(request)
    if request.method != 'POST':
        return redirect('user_list')

    target = get_object_or_404(User, pk=user_id)
    if not can_manage(request.user, target):
        return access_denied(request)
    target.is_banned = not target.is_banned
    target.save(update_fields=['is_banned'])
    messages.success(
        request, f'{target.username}: ' + ('забанен.' if target.is_banned else 'разбанен.'))
    return redirect('user_list')


@login_required
def set_role(request, user_id, role):
    if not is_superadmin(request.user):
        return access_denied(request)
    if request.method != 'POST':
        return redirect('user_list')
    if role not in ('admin', 'user'):
        return not_found(request)

    target = get_object_or_404(User, pk=user_id)
    if not can_manage(request.user, target):
        return access_denied(request)
    target.role = role
    target.save(update_fields=['role'])
    messages.success(request, f'{target.username}: роль «{target.get_role_display()}».')
    return redirect('user_list')