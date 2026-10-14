SEED_PASSWORD = 'Test12345!'

SEED_USERS = [
    {'username': 'moderator', 'email': 'moderator@example.com', 'role': 'admin',
     'bio': 'Модератор SkillSwap.'},
    {'username': 'alice', 'email': 'alice@example.com', 'role': 'user',
     'bio': 'Backend-разработчик, люблю Python и Django.'},
    {'username': 'bob', 'email': 'bob@example.com', 'role': 'user',
     'bio': 'Дизайнер интерфейсов.'},
    {'username': 'carol', 'email': 'carol@example.com', 'role': 'user',
     'bio': 'Преподаю английский и немецкий.'},
    {'username': 'dave', 'email': 'dave@example.com', 'role': 'user',
     'bio': 'Играю на гитаре уже 10 лет.'},
]


def seed_users():
    from .models import User
    users = {}
    for data in SEED_USERS:
        user, created = User.objects.get_or_create(
            username=data['username'],
            defaults={'email': data['email'], 'role': data['role'], 'bio': data['bio']},
        )
        if created:
            user.set_password(SEED_PASSWORD)
            user.save()
        users[user.username] = user
    return users