from tasks.models import Subject, SubjectTheme, Task, TaskDifficulty, TaskSource

Task.objects.all().delete()
SubjectTheme.objects.all().delete()
Subject.objects.all().delete()
TaskSource.objects.all().delete()

source = TaskSource.objects.create(name='Shell seed', is_ai=False)

data = {
    'Математика': ['Алгебра', 'Геометрия'],
    'Физика': ['Механика', 'Электродинамика'],
}

difficulties = [TaskDifficulty.EASY, TaskDifficulty.MEDIUM, TaskDifficulty.HARD]

for subject_name, themes in data.items():
    subject = Subject.objects.create(name=subject_name)
    for theme_name in themes:
        theme = SubjectTheme.objects.create(name=theme_name, subject=subject)
        for difficulty in difficulties:
            Task.objects.bulk_create([
                Task(
                    subject=subject,
                    theme=theme,
                    question=f'[{subject_name} / {theme_name} / {difficulty}] Вопрос №{i}',
                    solution=f'Решение задачи №{i}',
                    correct_answer=str(i * 10),
                    difficulty=difficulty,
                    source=source,
                )
                for i in range(1, 11)
            ])

print(f'Предметов: {Subject.objects.count()}')    # 2
print(f'Тем: {SubjectTheme.objects.count()}')      # 4
print(f'Задач: {Task.objects.count()}')            # 120