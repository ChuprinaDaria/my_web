# news/signals.py

from django.db.models.signals import post_save, pre_delete, m2m_changed
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import F
from django.core.cache import cache
import logging

from .models import ProcessedArticle, AIProcessingLog, RawArticle, NewsCategory

logger = logging.getLogger(__name__)


# === СИГНАЛ для автоматичного призначення тегів ===

@receiver(post_save, sender=ProcessedArticle)
def auto_assign_tags_on_create(sender, instance, created, **kwargs):
    """Автоматично призначає теги після створення статті"""
    
    if not created:
        return  # Тільки для нових статей
    
    try:
        # Перевіряємо чи вже є теги (можливо призначені вручну)
        if instance.tags.exists():
            logger.info(f"Стаття {instance.uuid} вже має теги, пропускаємо автопризначення")
            return
        
        logger.info(f"Запускаємо автоматичне призначення тегів для статті {instance.uuid}")
        
        # Засікаємо час початку
        start_time = timezone.now()
        
        # Запускаємо автоматичне призначення тегів
        assigned_tags = instance.auto_assign_tags()
        
        # Рахуємо час обробки
        processing_time = (timezone.now() - start_time).total_seconds()
        
        # Логуємо результат
        if assigned_tags:
            logger.info(f"Призначено теги для статті {instance.uuid}: {assigned_tags}")
            
            # Створюємо лог процесу
            try:
                AIProcessingLog.objects.create(
                    article=instance.raw_article,
                    log_type='tag_assignment',
                    model_used='rule_based_auto',
                    processing_time=processing_time,
                    success=True,
                    input_data={
                        'content_length': len(instance.get_title() + instance.get_summary()),
                        'category': instance.category.slug if instance.category else None,
                        'rss_source': instance.raw_article.source.category
                    },
                    output_data={
                        'assigned_tags': assigned_tags,
                        'tags_count': len(assigned_tags)
                    }
                )
                logger.info(f"Створено AI лог для призначення тегів статті {instance.uuid}")
                
            except Exception as e:
                logger.warning(f"Не вдалося створити AI лог для статті {instance.uuid}: {e}")
        else:
            logger.warning(f"Не вдалося призначити жодного тегу для статті {instance.uuid}")
            
            # Логуємо невдачу
            try:
                AIProcessingLog.objects.create(
                    article=instance.raw_article,
                    log_type='tag_assignment',
                    model_used='rule_based_auto',
                    processing_time=processing_time,
                    success=False,
                    error_message="Не знайдено відповідних тегів для контенту",
                    input_data={
                        'content_length': len(instance.get_title() + instance.get_summary()),
                        'category': instance.category.slug if instance.category else None,
                    },
                    output_data={'assigned_tags': []}
                )
            except Exception as e:
                logger.warning(f"Не вдалося створити AI лог помилки для статті {instance.uuid}: {e}")
    
    except Exception as e:
        logger.error(f"Критична помилка при автопризначенні тегів для статті {instance.uuid}: {e}")

def enforce_image_policy(sender, instance, created, **kwargs):
    if instance.ai_image_url and not (instance.is_top_article and instance.full_content_parsed):
        ProcessedArticle.objects.filter(pk=instance.pk).update(ai_image_url='')
        
# === СИГНАЛ для оновлення статистики тегів ===

@receiver(m2m_changed, sender=ProcessedArticle.tags.through)
def update_tag_statistics(sender, instance, action, pk_set, **kwargs):
    """Оновлює статистику тегів при зміні зв'язків"""
    
    if action in ['post_add', 'post_remove', 'post_clear']:
        try:
            # Очищаємо кеш статистики тегів
            cache_key = f"tag_stats_{instance.uuid}"
            cache.delete(cache_key)
            
            # Оновлюємо глобальний кеш статистики тегів
            cache.delete('global_tag_statistics')
            
            logger.info(f"Оновлено статистику тегів для статті {instance.uuid}, дія: {action}")
            
        except Exception as e:
            logger.warning(f"Помилка при оновленні статистики тегів: {e}")


# === СИГНАЛ для збільшення лічильника переглядів ===

@receiver(post_save, sender=ProcessedArticle)
def update_article_metrics(sender, instance, created, **kwargs):
    """Оновлює метрики статті при збереженні"""
    
    if created:
        return  # Не потрібно для нових статей
    
    try:
        # Якщо стаття була опублікована
        if instance.status == 'published' and instance.published_at:
            
            # Оновлюємо час читання на основі контенту
            if not instance.reading_time or instance.reading_time == 5:  # Дефолтне значення
                instance.reading_time = instance.get_enhanced_reading_time()
                ProcessedArticle.objects.filter(uuid=instance.uuid).update(
                    reading_time=instance.reading_time
                )
            
            # Очищаємо кеші пов'язані зі статтею
            cache_keys_to_clear = [
                f"article_{instance.uuid}",
                f"article_content_{instance.uuid}",
                f"related_content_{instance.uuid}",
                "latest_articles",
                "top_articles",
                f"category_articles_{instance.category.slug if instance.category else 'all'}"
            ]
            
            cache.delete_many(cache_keys_to_clear)
            
    except Exception as e:
        logger.warning(f"Помилка при оновленні метрик статті {instance.uuid}: {e}")


# === СИГНАЛ для генерації соціальних постів ===

@receiver(post_save, sender=ProcessedArticle)
def auto_generate_social_posts(sender, instance, created, **kwargs):
    """Автоматично генерує пости для соцмереж при публікації топ-статей"""
    
    # Тільки для топ-статей які щойно опубліковані
    if (not created and 
        instance.status == 'published' and 
        instance.is_top_article and 
        instance.published_at):
        
        try:
            from .models import SocialMediaPost
            from .utils import generate_social_media_content
            
            # Платформи для автопостингу
            platforms = [
                ('telegram_uk', 'uk'),
                ('facebook_en', 'en'),
                ('linkedin_en', 'en'),
            ]
            
            for platform, language in platforms:
                # Перевіряємо чи вже існує пост для цієї платформи
                existing_post = SocialMediaPost.objects.filter(
                    article=instance,
                    platform=platform
                ).first()
                
                if not existing_post:
                    try:
                        # Генеруємо контент для соцмереж
                        social_content = generate_social_media_content(
                            article=instance,
                            platform=platform,
                            language=language
                        )
                        
                        # Створюємо пост
                        SocialMediaPost.objects.create(
                            article=instance,
                            platform=platform,
                            content=social_content['content'],
                            hashtags=social_content.get('hashtags', ''),
                            image_url=instance.ai_image_url,
                            status='draft',  # Створюємо як чернетку
                            scheduled_at=timezone.now() + timezone.timedelta(minutes=30)  # Запланувати на через 30 хв
                        )
                        
                        logger.info(f"Створено соціальний пост для {platform}: {instance.uuid}")
                        
                    except Exception as e:
                        logger.error(f"Помилка при створенні поста для {platform}: {e}")
            
        except Exception as e:
            logger.error(f"Помилка при автогенерації соціальних постів для статті {instance.uuid}: {e}")


# === СИГНАЛ для очищення кешу при видаленні ===

@receiver(pre_delete, sender=ProcessedArticle)
def clear_cache_on_delete(sender, instance, **kwargs):
    """Очищає кеш при видаленні статті"""
    
    try:
        # Очищаємо всі кеші пов'язані зі статтею
        cache_keys_to_clear = [
            f"article_{instance.uuid}",
            f"article_content_{instance.uuid}",
            f"related_content_{instance.uuid}",
            f"tag_stats_{instance.uuid}",
            "latest_articles",
            "top_articles",
            "global_tag_statistics",
            f"category_articles_{instance.category.slug if instance.category else 'all'}"
        ]
        
        cache.delete_many(cache_keys_to_clear)
        
        logger.info(f"Очищено кеш при видаленні статті {instance.uuid}")
        
    except Exception as e:
        logger.warning(f"Помилка при очищенні кешу для видаленої статті: {e}")


# === СИГНАЛ для оновлення статистики категорій ===

@receiver(post_save, sender=ProcessedArticle)
def update_category_statistics(sender, instance, created, **kwargs):
    """Оновлює статистику категорій"""
    
    if instance.category:
        try:
            # Очищаємо кеш статистики категорій
            cache.delete(f"category_stats_{instance.category.slug}")
            cache.delete("all_categories_stats")
            
            # Якщо стаття опублікована, оновлюємо лічильники
            if instance.status == 'published':
                cache_key = f"category_article_count_{instance.category.slug}"
                cache.delete(cache_key)
            
        except Exception as e:
            logger.warning(f"Помилка при оновленні статистики категорії: {e}")


# === ФУНКЦІЯ для ініціалізації сигналів ===

def connect_signals():
    """Підключає всі сигнали для модуля новин"""
    
    # Сигнали вже підключені через декоратори @receiver
    # Ця функція може бути використана для додаткової ініціалізації
    
    logger.info("Сигнали модуля новин підключено успішно")


# === ФУНКЦІЯ для відключення сигналів (для тестів) ===

def disconnect_signals():
    """Відключає сигнали для тестування"""
    
    from django.db.models.signals import post_save, pre_delete, m2m_changed
    
    # Відключаємо сигнали
    post_save.disconnect(auto_assign_tags_on_create, sender=ProcessedArticle)
    post_save.disconnect(update_article_metrics, sender=ProcessedArticle)
    post_save.disconnect(auto_generate_social_posts, sender=ProcessedArticle)
    post_save.disconnect(update_category_statistics, sender=ProcessedArticle)
    
    m2m_changed.disconnect(update_tag_statistics, sender=ProcessedArticle.tags.through)
    pre_delete.disconnect(clear_cache_on_delete, sender=ProcessedArticle)
    
    logger.info("Сигнали модуля новин відключено")


# === ДОДАТКОВІ УТИЛІТИ ===

class TagAssignmentError(Exception):
    """Кастомна помилка для призначення тегів"""
    pass


def manual_assign_tags_to_article(article_uuid, tag_slugs, user=None):
    """Ручне призначення тегів до статті з логуванням"""
    
    try:
        from django.apps import apps
        
        article = ProcessedArticle.objects.get(uuid=article_uuid)
        Tag = apps.get_model('core', 'Tag')
        
        # Знаходимо теги
        tags = Tag.objects.filter(slug__in=tag_slugs, is_active=True)
        
        if not tags.exists():
            raise TagAssignmentError(f"Не знайдено активних тегів з слагами: {tag_slugs}")
        
        # Призначаємо теги
        article.tags.set(tags)
        
        # Логуємо ручне призначення
        AIProcessingLog.objects.create(
            article=article.raw_article,
            log_type='tag_assignment',
            model_used='manual_assignment',
            processing_time=0.0,
            success=True,
            input_data={
                'requested_tags': tag_slugs,
                'assigned_by': user.username if user else 'system'
            },
            output_data={
                'assigned_tags': list(tags.values_list('slug', flat=True)),
                'tags_count': tags.count()
            }
        )
        
        logger.info(f"Ручно призначено теги {list(tags.values_list('slug', flat=True))} до статті {article_uuid}")
        
        return list(tags.values_list('slug', flat=True))
        
    except ProcessedArticle.DoesNotExist:
        raise TagAssignmentError(f"Стаття з UUID {article_uuid} не знайдена")
    except Exception as e:
        logger.error(f"Помилка при ручному призначенні тегів: {e}")
        raise TagAssignmentError(f"Помилка призначення тегів: {e}")


def get_tag_assignment_statistics(days=30):
    """Отримує статистику призначення тегів за останні N днів"""
    
    from datetime import timedelta
    from django.db.models import Count, Q
    
    try:
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Статистика AI логів призначення тегів
        tag_logs = AIProcessingLog.objects.filter(
            log_type='tag_assignment',
            created_at__gte=cutoff_date
        )
        
        stats = {
            'total_assignments': tag_logs.count(),
            'successful_assignments': tag_logs.filter(success=True).count(),
            'failed_assignments': tag_logs.filter(success=False).count(),
            'auto_assignments': tag_logs.filter(model_used='rule_based_auto').count(),
            'manual_assignments': tag_logs.filter(model_used='manual_assignment').count(),
            'avg_processing_time': tag_logs.aggregate(
                avg_time=timezone.models.Avg('processing_time')
            )['avg_time'] or 0,
        }
        
        # Додаємо відсоток успішності
        if stats['total_assignments'] > 0:
            stats['success_rate'] = (stats['successful_assignments'] / stats['total_assignments']) * 100
        else:
            stats['success_rate'] = 0
        
        return stats
        
    except Exception as e:
        logger.error(f"Помилка при отриманні статистики призначення тегів: {e}")
        return {
            'total_assignments': 0,
            'successful_assignments': 0,
            'failed_assignments': 0,
            'auto_assignments': 0,
            'manual_assignments': 0,
            'avg_processing_time': 0,
            'success_rate': 0,
            'error': str(e)
        }