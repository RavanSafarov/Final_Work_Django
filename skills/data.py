DEFAULT_CATEGORIES = [
    'Programming', 'Design', 'Languages', 'Marketing', 'Music',
    'Photography', 'Business', 'Mathematics', 'Other',
]

SEED_OFFERS = [
    {'title': 'Python for beginners', 'category': 'Programming', 'level': 'beginner',
     'format': 'online', 'duration': '1 час', 'author': 'alice', 'status': 'published',
     'description': 'Основы Python: переменные, циклы, функции.'},
    {'title': 'Django from scratch', 'category': 'Programming', 'level': 'intermediate',
     'format': 'online', 'duration': '2 часа', 'author': 'alice', 'status': 'published',
     'description': 'Модели, views, шаблоны и формы на практике.'},
    {'title': 'UI design in Figma', 'category': 'Design', 'level': 'beginner',
     'format': 'offline', 'duration': '90 минут', 'author': 'bob', 'status': 'published',
     'description': 'Компоненты, сетки и прототипы в Figma.'},
    {'title': 'Conversational English', 'category': 'Languages', 'level': 'intermediate',
     'format': 'online', 'duration': '1 час', 'author': 'carol', 'status': 'published',
     'description': 'Разговорная практика и разбор типичных ошибок.'},
    {'title': 'German A1', 'category': 'Languages', 'level': 'beginner',
     'format': 'offline', 'duration': '1 час', 'author': 'carol', 'status': 'published',
     'description': 'Алфавит, базовая грамматика и первые фразы.'},
    {'title': 'Guitar basics', 'category': 'Music', 'level': 'beginner',
     'format': 'offline', 'duration': '45 минут', 'author': 'dave', 'status': 'published',
     'description': 'Аккорды, ритм и первая песня.'},
    {'title': 'SQL for analysts', 'category': 'Programming', 'level': 'advanced',
     'format': 'online', 'duration': '2 часа', 'author': 'alice', 'status': 'pending',
     'description': 'JOIN, подзапросы и оконные функции.'},
    {'title': 'Photography for beginners', 'category': 'Photography', 'level': 'beginner',
     'format': 'offline', 'duration': '2 часа', 'author': 'dave', 'status': 'draft',
     'description': 'Экспозиция, композиция и работа со светом.'},
]


SEED_REVIEWS = [
    {'offer': 'Python for beginners', 'user': 'bob', 'rating': 5, 'comment': 'Очень понятно объясняет!'},
    {'offer': 'Python for beginners', 'user': 'carol', 'rating': 4, 'comment': 'Хороший темп, много примеров.'},
    {'offer': 'Django from scratch', 'user': 'dave', 'rating': 5, 'comment': 'Наконец понял, как работают формы.'},
    {'offer': 'UI design in Figma', 'user': 'alice', 'rating': 3, 'comment': 'Нормально, хотелось больше практики.'},
    {'offer': 'Conversational English', 'user': 'alice', 'rating': 4, 'comment': 'Полезная практика.'},
    {'offer': 'Guitar basics', 'user': 'carol', 'rating': 5, 'comment': 'Отличный преподаватель.'},
]


def seed():

    from accounts.data import seed_users, SEED_PASSWORD
    from .models import Category, SkillOffer, SessionRequest, Review

    users = seed_users()

    for name in DEFAULT_CATEGORIES:
        Category.objects.get_or_create(name=name)

    offers = {}
    for data in SEED_OFFERS:
        offer, _ = SkillOffer.objects.get_or_create(
            title=data['title'],
            defaults={
                'description': data['description'],
                'category': Category.objects.get(name=data['category']),
                'level': data['level'],
                'format': data['format'],
                'duration': data['duration'],
                'author': users[data['author']],
                'status': data['status'],
            },
        )
        offers[offer.title] = offer

    for data in SEED_REVIEWS:
        offer = offers[data['offer']]
        student = users[data['user']]
        SessionRequest.objects.get_or_create(
            offer=offer, student=student, teacher=offer.author,
            status=SessionRequest.Status.COMPLETED,
        )
        Review.objects.get_or_create(
            offer=offer, user=student,
            defaults={'rating': data['rating'], 'comment': data['comment']},
        )

    print(f'Готово: {len(users)} пользователей, {len(offers)} предложений, '
          f'{len(SEED_REVIEWS)} отзывов. Пароль тестовых юзеров: {SEED_PASSWORD}')