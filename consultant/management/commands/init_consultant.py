from django.core.management.base import BaseCommand
from consultant.models import ConsultantProfile, KnowledgeBase


class Command(BaseCommand):
    help = 'Створює базовий профіль консультанта та початкові дані'

    def handle(self, *args, **options):
        # Створюємо профіль консультанта
        consultant, created = ConsultantProfile.objects.get_or_create(
            name="RAG Консультант",
            defaults={
                'description': 'Штучний інтелект для консультацій та допомоги',
                'avatar': '🫧',
                'is_active': True,
                'max_tokens': 4000,
                'temperature': 0.7,
                'system_prompt': 'Ти RAG консультант - штучний інтелект, який допомагає користувачам з різними питаннями. Відповідай корисними, точними та дружелюбними відповідями українською мовою.'
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Створено профіль консультанта: {consultant.name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠️ Профіль консультанта вже існує: {consultant.name}')
            )

        # Створюємо базові знання
        knowledge_items = [
            {
                'title': 'Що таке RAG?',
                'content': 'RAG (Retrieval-Augmented Generation) - це технологія, яка поєднує генеративні можливості штучного інтелекту з доступом до актуальної бази знань. Це дозволяє надавати точні та релевантні відповіді.',
                'category': 'AI',
                'tags': 'RAG, AI, машинне навчання',
                'priority': 10
            },
            {
                'title': 'Послуги Lazysoft',
                'content': 'Lazysoft надає послуги з автоматизації, розробки веб-додатків, створення ботів та інтеграції зі штучним інтелектом. Ми спеціалізуємося на сучасних технологіях та інноваційних рішеннях.',
                'category': 'Послуги',
                'tags': 'автоматизація, веб-розробка, боти, AI',
                'priority': 9
            },
            {
                'title': 'Як зв\'язатися з Lazysoft',
                'content': 'З нами можна зв\'язатися через контактну форму на сайті, email або соціальні мережі. Ми завжди готові обговорити ваш проект та запропонувати найкраще рішення.',
                'category': 'Контакти',
                'tags': 'контакти, підтримка, співпраця',
                'priority': 8
            }
        ]

        created_count = 0
        for item in knowledge_items:
            knowledge, created = KnowledgeBase.objects.get_or_create(
                title=item['title'],
                defaults={
                    'content': item['content'],
                    'category': item['category'],
                    'tags': item['tags'],
                    'priority': item['priority'],
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Створено знання: {knowledge.title}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'🎉 Ініціалізація завершена! Створено {created_count} нових записів знань.')
        )
