from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from django.shortcuts import render, get_object_or_404, redirect

from .data import DEFAULT_CATEGORIES
from .forms import SkillOfferForm, ReviewForm, CategoryForm
from .models import SkillOffer, Category, SessionRequest, Favorite, Review




def is_mod(user):
    return user.is_authenticated and (user.is_moderator or user.is_superuser)


def is_superadmin(user):
    return user.is_authenticated and (user.is_superuser or user.role == 'superadmin')


def access_denied(request):
    return render(request, 'skills/access_denied.html', status=403)


def not_found(request):
    return render(request, 'skills/not_found.html', status=404)




def ensure_default_categories():
    if not Category.objects.exists():
        for name in DEFAULT_CATEGORIES:
            Category.objects.create(name=name)


def published_offers():
    return (SkillOffer.objects.filter(status=SkillOffer.Status.PUBLISHED).select_related('author', 'category')
        .annotate(
            avg_rating=Avg('reviews__rating'),
            reviews_count=Count('reviews', distinct=True),
        ).order_by('-created_at')
    )


def _render_detail(request, offer, review_form=None):
    user = request.user
    stats = offer.reviews.aggregate(avg=Avg('rating'), count=Count('id'))

    context = {
        'offer': offer,
        'reviews': offer.reviews.select_related('user'),
        'avg_rating': round(stats['avg'] or 0, 2),
        'reviews_count': stats['count'],
        'completed_count': offer.requests.filter(status=SessionRequest.Status.COMPLETED).count(),
        'is_favorite': False,
        'has_active_request': False,
        'can_review': False,
        'can_manage': False,
    }

    if user.is_authenticated:
        context['can_manage'] = offer.author_id == user.id or is_mod(user)
        context['is_favorite'] = Favorite.objects.filter(user=user, offer=offer).exists()
        context['has_active_request'] = SessionRequest.objects.filter(
            offer=offer, student=user,
            status__in=[SessionRequest.Status.PENDING, SessionRequest.Status.ACCEPTED],
        ).exists()
        context['can_review'] = (
            offer.author_id != user.id
            and SessionRequest.objects.filter(
                offer=offer, student=user,
                status=SessionRequest.Status.COMPLETED).exists()
            and not Review.objects.filter(offer=offer, user=user).exists()
        )
        if context['can_review']:
            context['review_form'] = review_form or ReviewForm()

    return render(request, 'skills/offer_detail.html', context)




def offer_list(request):
    ensure_default_categories()
    offers = published_offers()

    category_id = request.GET.get('category')
    level = request.GET.get('level')
    fmt = request.GET.get('format')
    min_rating = request.GET.get('min_rating')
    search_query = request.GET.get('q')

    if category_id:
        offers = offers.filter(category_id=category_id)
    if level:
        offers = offers.filter(level=level)
    if fmt:
        offers = offers.filter(format=fmt)
    if min_rating and min_rating.isdigit():
        offers = offers.filter(avg_rating__gte=int(min_rating))
    if search_query:
        offers = offers.filter(title__icontains=search_query)

    return render(request, 'skills/offer_list.html', {
        'offers': offers,
        'categories': Category.objects.all(),
        'levels': SkillOffer.Level.choices,
        'formats': SkillOffer.Format.choices,
    })


def offer_detail(request, pk):
    offer = get_object_or_404(SkillOffer.objects.select_related('author', 'category'), pk=pk)


    if offer.status != SkillOffer.Status.PUBLISHED:
        user = request.user
        if not (user.is_authenticated and (offer.author_id == user.id or is_mod(user))):
            return not_found(request)

    return _render_detail(request, offer)


@login_required
def offer_create(request):
    if request.user.is_banned:
        messages.error(request, 'Ваш аккаунт заблокирован.')
        return redirect('home')

    ensure_default_categories()
    if request.method == 'POST':
        form = SkillOfferForm(request.POST, request.FILES)
        if form.is_valid():
            offer = form.save(commit=False)
            offer.author = request.user
            if 'draft' in request.POST:
                offer.status = SkillOffer.Status.DRAFT
                messages.info(request, 'Сохранено как черновик.')
            else:
                offer.status = SkillOffer.Status.PENDING
                messages.info(request, 'Предложение отправлено на модерацию.')
            offer.save()
            return redirect('my_offers')
    else:
        form = SkillOfferForm()
    return render(request, 'skills/offer_form.html', {'form': form})


@login_required
def offer_update(request, pk):
    offer = get_object_or_404(SkillOffer, pk=pk)
    moderator = is_mod(request.user)

    if offer.author_id != request.user.id and not moderator:
        return access_denied(request)

    if request.method == 'POST':
        form = SkillOfferForm(request.POST, request.FILES, instance=offer)
        if form.is_valid():
            offer = form.save(commit=False)
            if moderator:
                messages.success(request, 'Предложение обновлено.')
            elif 'draft' in request.POST and offer.status != SkillOffer.Status.PUBLISHED:
                offer.status = SkillOffer.Status.DRAFT
                messages.info(request, 'Сохранено как черновик.')
            else:
                offer.status = SkillOffer.Status.PENDING
                messages.info(request, 'Изменения отправлены на модерацию.')
            offer.save()
            return redirect('offer_detail', pk=offer.pk)
    else:
        form = SkillOfferForm(instance=offer)

    return render(request, 'skills/offer_form.html', {'form': form, 'offer': offer})


@login_required
def offer_delete(request, pk):
    if request.method != 'POST':
        return redirect('my_offers')

    offer = get_object_or_404(SkillOffer, pk=pk)
    if offer.author_id != request.user.id and not is_mod(request.user):
        return access_denied(request)
    offer.delete()
    messages.success(request, 'Предложение удалено.')
    return redirect('my_offers')




@login_required
def send_session_request(request, offer_id):
    if request.user.is_banned:
        messages.error(request, 'Ваш аккаунт заблокирован.')
        return redirect('home')
    if request.method != 'POST':
        return redirect('offer_detail', pk=offer_id)

    offer = get_object_or_404(SkillOffer, pk=offer_id,
                              status=SkillOffer.Status.PUBLISHED)

    if offer.author_id == request.user.id:
        messages.error(request, 'Нельзя отправить запрос на собственное предложение.')
        return redirect('offer_detail', pk=offer.pk)

    already_active = SessionRequest.objects.filter(
        offer=offer, student=request.user,
        status__in=[SessionRequest.Status.PENDING, SessionRequest.Status.ACCEPTED],
    ).exists()
    if already_active:
        messages.warning(request, 'У вас уже есть активный запрос на это предложение.')
        return redirect('offer_detail', pk=offer.pk)

    SessionRequest.objects.create(
        offer=offer, student=request.user, teacher=offer.author)
    messages.success(request, 'Запрос успешно отправлен!')
    return redirect('my_requests')



S = SessionRequest.Status
REQUEST_TRANSITIONS = {
    'accept':   ('teacher', {S.PENDING}, S.ACCEPTED),
    'reject':   ('teacher', {S.PENDING}, S.REJECTED),
    'cancel':   ('student', {S.PENDING, S.ACCEPTED}, S.CANCELLED),
    'complete': ('teacher', {S.ACCEPTED}, S.COMPLETED),
}


@login_required
def handle_session_request(request, request_id, action):
    if request.method != 'POST':
        return redirect('my_requests')

    session_req = get_object_or_404(SessionRequest, pk=request_id)

    rule = REQUEST_TRANSITIONS.get(action)
    if rule is None:
        return not_found(request)

    role, allowed_from, new_status = rule
    actor_id = session_req.teacher_id if role == 'teacher' else session_req.student_id
    if actor_id != request.user.id:
        return access_denied(request)

    if session_req.status not in allowed_from:
        messages.error(request, 'Это действие недоступно для текущего статуса запроса.')
        return redirect('my_requests')

    session_req.status = new_status
    session_req.save(update_fields=['status'])
    messages.success(request, f'Статус запроса: {session_req.get_status_display()}.')
    return redirect('my_requests')




@login_required
def toggle_favorite(request, offer_id):
    if request.method != 'POST':
        return redirect('offer_detail', pk=offer_id)

    offer = get_object_or_404(SkillOffer, pk=offer_id,status=SkillOffer.Status.PUBLISHED)
    favorite, created = Favorite.objects.get_or_create(user=request.user, offer=offer)
    if created:
        messages.success(request, 'Добавлено в избранное.')
    else:
        favorite.delete()
        messages.info(request, 'Удалено из избранного.')
    return redirect('offer_detail', pk=offer.pk)




@login_required
def review_create(request, offer_id):
    if request.method != 'POST':
        return redirect('offer_detail', pk=offer_id)

    offer = get_object_or_404(SkillOffer, pk=offer_id,status=SkillOffer.Status.PUBLISHED)

    if offer.author_id == request.user.id:
        return access_denied(request)
    if not SessionRequest.objects.filter(
            offer=offer, student=request.user,
            status=SessionRequest.Status.COMPLETED).exists():
        messages.error(request, 'Отзыв можно оставить только после завершённого занятия.')
        return redirect('offer_detail', pk=offer.pk)
    if Review.objects.filter(offer=offer, user=request.user).exists():
        messages.warning(request, 'Вы уже оставили отзыв на это предложение.')
        return redirect('offer_detail', pk=offer.pk)

    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.offer = offer
        review.user = request.user
        review.save()
        messages.success(request, 'Спасибо за отзыв!')
        return redirect('offer_detail', pk=offer.pk)

    return _render_detail(request, offer, review_form=form)


@login_required
def review_update(request, pk):
    review = get_object_or_404(Review, pk=pk, user=request.user)

    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, 'Отзыв обновлён.')
            return redirect('offer_detail', pk=review.offer_id)
    else:
        form = ReviewForm(instance=review)
    return render(request, 'skills/review_form.html', {'form': form, 'review': review})


@login_required
def review_delete(request, pk):
    review = get_object_or_404(Review, pk=pk)
    if review.user_id != request.user.id and not is_mod(request.user):
        return access_denied(request)
    if request.method != 'POST':
        return redirect('offer_detail', pk=review.offer_id)

    offer_id = review.offer_id
    review.delete()
    messages.success(request, 'Отзыв удалён.')
    return redirect('offer_detail', pk=offer_id)




@login_required
def moderation_list(request):
    if not is_mod(request.user):
        return access_denied(request)

    pending = (SkillOffer.objects
               .filter(status=SkillOffer.Status.PENDING)
               .select_related('author', 'category'))
    return render(request, 'skills/moderation.html', {'offers': pending})


@login_required
def moderate_offer(request, offer_id, action):
    if not is_mod(request.user):
        return access_denied(request)
    if request.method != 'POST':
        return redirect('moderation_list')

    offer = get_object_or_404(SkillOffer, pk=offer_id)

    if action == 'approve':
        offer.status = SkillOffer.Status.PUBLISHED
    elif action == 'reject':
        offer.status = SkillOffer.Status.REJECTED
    else:
        return not_found(request)

    offer.save(update_fields=['status'])
    messages.success(request, f'Предложение «{offer.title}»: {offer.get_status_display()}.')
    return redirect('moderation_list')


def popular_list(request):
    offers = published_offers().filter(avg_rating__gte=4).order_by('-avg_rating')
    return render(request, 'skills/offer_list.html', {
        'offers': offers, 'categories': Category.objects.all(),
        'levels': SkillOffer.Level.choices, 'formats': SkillOffer.Format.choices,
        'title': 'Popular'})


def category_list(request):
    categories = Category.objects.annotate(
        offers_count=Count('offers', filter=Q(offers__status='published')))
    return render(request, 'skills/category_list.html', {'categories': categories})


@login_required
def favorite_list(request):
    offers = published_offers().filter(favorite__user=request.user)
    return render(request, 'skills/offer_list.html', {
        'offers': offers, 'title': 'Favorites'})


@login_required
def my_offers(request):
    offers = (SkillOffer.objects.filter(author=request.user)
              .select_related('category')
              .annotate(avg_rating=Avg('reviews__rating')))
    return render(request, 'skills/my_offers.html', {'offers': offers})


@login_required
def my_requests(request):
    sent = (SessionRequest.objects.filter(student=request.user)
            .select_related('offer', 'teacher'))
    received = (SessionRequest.objects.filter(teacher=request.user)
                .select_related('offer', 'student'))
    return render(request, 'skills/my_requests.html', {'sent': sent, 'received': received})




@login_required
def category_manage(request, pk=None):
    if not is_superadmin(request.user):
        return access_denied(request)

    category = get_object_or_404(Category, pk=pk) if pk else None
    form = CategoryForm(request.POST or None, instance=category)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Категория сохранена.')
        return redirect('category_manage')
    return render(request, 'skills/category_manage.html', {
        'form': form, 'categories': Category.objects.all(), 'editing': category})


@login_required
def category_delete(request, pk):
    if not is_superadmin(request.user):
        return access_denied(request)
    if request.method != 'POST':
        return redirect('category_manage')

    category = get_object_or_404(Category, pk=pk)
    name = category.name
    offers_count = category.offers.count()
    category.delete()

    if offers_count:
        messages.success(
            request, f'Категория «{name}» удалена вместе с предложениями: {offers_count}.')
    else:
        messages.success(request, 'Категория удалена.')
    return redirect('category_manage')