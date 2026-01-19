# trips/migrations/0002_add_friendship_models.py

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('trips', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Friendship',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('confirmed', models.BooleanField(default=False)),
                ('friend', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='friends_of', to='auth.user')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='friends', to='auth.user')),
            ],
            options={
                'ordering': ['-created_at'],
                'unique_together': {('user', 'friend')},
            },
        ),
        migrations.CreateModel(
            name='FriendRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_accepted', models.BooleanField(default=False)),
                ('from_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_requests', to='auth.user')),
                ('to_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_requests', to='auth.user')),
            ],
            options={
                'ordering': ['-created_at'],
                'unique_together': {('from_user', 'to_user')},
            },
        ),
    ]