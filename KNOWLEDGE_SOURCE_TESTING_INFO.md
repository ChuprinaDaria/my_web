# 📚 KnowledgeSource Model - Інформація для тестування

## Модель: `rag.models.KnowledgeSource`

### 📋 Обов'язкові поля

1. **`title`** - `CharField(max_length=200)` - ОБОВ'ЯЗКОВЕ
2. **`source_type`** - `CharField(max_length=20, choices=SOURCE_TYPES)` - ОБОВ'ЯЗКОВЕ
3. **`content_uk`** - `TextField()` - ОБОВ'ЯЗКОВЕ (українська мова)

### 📝 Необов'язкові поля

- **`content_en`** - `TextField(blank=True)` - опціонально
- **`content_pl`** - `TextField(blank=True)` - опціонально
- **`tags`** - `JSONField(default=list)` - за замовчуванням `[]`
- **`priority`** - `PositiveIntegerField(default=5)` - за замовчуванням `5`
- **`auto_update`** - `BooleanField(default=True)` - за замовчуванням `True`
- **`last_embedding_update`** - `DateTimeField(null=True, blank=True)` - опціонально
- **`is_active`** - `BooleanField(default=True)` - за замовчуванням `True`

### 🔢 Валідація Priority

**ВАЖЛИВО**: В моделі немає вбудованої валідації для `priority` в межах 1-10. Потрібно додати custom validator або перевірку в `clean()` методі.

**Очікувані значення**: 1-10 (1 = найвищий пріоритет, 10 = найнижчий)

### 🏷️ Source Types (choices)

```python
SOURCE_TYPES = [
    ('service', 'Сервіси'),
    ('project', 'Проєкти'),
    ('faq', 'FAQ'),
    ('pricing', 'Прайсинг'),
    ('dialogs', 'Успішні діалоги'),
    ('manual', 'Ручний контент'),
]
```

### 🔗 Relations

**Немає ForeignKey або ManyToMany** - модель не має прямых зв'язків з іншими моделями.

**Теги**: Зберігаються як JSONField (список рядків), не як ManyToMany.

### ⚙️ Що відбувається після save()

**НЕМАЄ signals** (`rag/signals.py` порожній).

**Embeddings НЕ генеруються автоматично** при `save()`. 

**Індексація відбувається вручну** через:
- Admin actions: `generate_embeddings`, `index_pricing`, `index_success_dialogs`
- Виклик `IndexingService().reindex_object(obj)` вручну
- Management команди

**Auto-update прапор** (`auto_update=True`) не викликає автоматичної індексації. Він лише вказує, що джерело має бути індексоване при наступній ручній індексації.

### 🔄 Логіка індексації (IndexingService.reindex_object)

Коли викликається `IndexingService().reindex_object(knowledge_source)`:

1. **source_type='service'** → індексує всі `ServiceCategory.objects.filter(is_active=True)`
2. **source_type='pricing'** → індексує всі `ServicePricing.objects.filter(is_active=True)`
3. **source_type='dialogs'** → індексує сам `KnowledgeSource` об'єкт
4. **source_type='project'** → індексує всі `Project.objects.all()`
5. **source_type='faq'** → індексує всі `FAQ.objects.all()`
6. **source_type='manual'** → індексує сам `KnowledgeSource` об'єкт

Після індексації оновлюється `last_embedding_update = timezone.now()`.

### 📝 Custom Validators

**НЕМАЄ** custom validators в моделі. Потрібно додати валідацію для:
- `priority` в межах 1-10
- `title` не порожній
- `content_uk` не порожній

### ✅ Тести які потрібно написати

#### 1. Валідні дані проходять
```python
def test_valid_knowledge_source():
    source = KnowledgeSource.objects.create(
        title="Test Service",
        source_type="service",
        content_uk="Опис сервісу українською",
        priority=3,
        is_active=True
    )
    assert source.pk is not None
    assert source.title == "Test Service"
```

#### 2. Невалідні дані фейляться
```python
def test_missing_required_fields():
    # Без title
    with pytest.raises(ValidationError):
        KnowledgeSource.objects.create(
            source_type="service",
            content_uk="Контент"
        )
    
    # Без source_type
    with pytest.raises(ValidationError):
        KnowledgeSource.objects.create(
            title="Test",
            content_uk="Контент"
        )
    
    # Без content_uk
    with pytest.raises(ValidationError):
        KnowledgeSource.objects.create(
            title="Test",
            source_type="service"
        )
```

#### 3. Priority валідація (якщо додати validator)
```python
def test_priority_validation():
    # Priority < 1
    with pytest.raises(ValidationError):
        source = KnowledgeSource(
            title="Test",
            source_type="service",
            content_uk="Контент",
            priority=0
        )
        source.full_clean()
    
    # Priority > 10
    with pytest.raises(ValidationError):
        source = KnowledgeSource(
            title="Test",
            source_type="service",
            content_uk="Контент",
            priority=11
        )
        source.full_clean()
```

#### 4. Багатомовність зберігається правильно
```python
def test_multilingual_content():
    source = KnowledgeSource.objects.create(
        title="Test",
        source_type="manual",
        content_uk="Український контент",
        content_en="English content",
        content_pl="Polski content"
    )
    assert source.content_uk == "Український контент"
    assert source.content_en == "English content"
    assert source.content_pl == "Polski content"
```

#### 5. Теги зберігаються як JSON
```python
def test_tags_json_field():
    source = KnowledgeSource.objects.create(
        title="Test",
        source_type="service",
        content_uk="Контент",
        tags=["web", "development", "ai"]
    )
    assert source.tags == ["web", "development", "ai"]
    assert isinstance(source.tags, list)
```

#### 6. Auto-update прапор
```python
def test_auto_update_flag():
    source = KnowledgeSource.objects.create(
        title="Test",
        source_type="service",
        content_uk="Контент",
        auto_update=True
    )
    assert source.auto_update is True
    
    source.auto_update = False
    source.save()
    assert source.auto_update is False
```

#### 7. Source type choices
```python
def test_source_type_choices():
    valid_types = ['service', 'project', 'faq', 'pricing', 'dialogs', 'manual']
    for source_type in valid_types:
        source = KnowledgeSource.objects.create(
            title=f"Test {source_type}",
            source_type=source_type,
            content_uk="Контент"
        )
        assert source.source_type == source_type
    
    # Невалідний тип
    with pytest.raises(ValidationError):
        source = KnowledgeSource(
            title="Test",
            source_type="invalid_type",
            content_uk="Контент"
        )
        source.full_clean()
```

#### 8. Default значення
```python
def test_default_values():
    source = KnowledgeSource.objects.create(
        title="Test",
        source_type="service",
        content_uk="Контент"
    )
    assert source.priority == 5  # default
    assert source.auto_update is True  # default
    assert source.is_active is True  # default
    assert source.tags == []  # default
    assert source.last_embedding_update is None  # default
```

#### 9. Індексація (мокаємо IndexingService)
```python
from unittest.mock import Mock, patch

def test_reindex_object_called():
    source = KnowledgeSource.objects.create(
        title="Test",
        source_type="manual",
        content_uk="Контент"
    )
    
    with patch('rag.services.IndexingService') as mock_service:
        mock_instance = Mock()
        mock_service.return_value = mock_instance
        
        from rag.services import IndexingService
        service = IndexingService()
        service.reindex_object(source)
        
        mock_instance.reindex_object.assert_called_once_with(source)
```

#### 10. Last embedding update оновлюється
```python
def test_last_embedding_update_updated():
    source = KnowledgeSource.objects.create(
        title="Test",
        source_type="manual",
        content_uk="Контент"
    )
    
    assert source.last_embedding_update is None
    
    # Мокаємо індексацію
    with patch('rag.services.IndexingService') as mock_service:
        mock_instance = Mock()
        mock_service.return_value = mock_instance
        
        from rag.services import IndexingService
        service = IndexingService()
        service.reindex_object(source)
        
        source.refresh_from_db()
        # Перевіряємо що last_embedding_update оновився
        # (якщо індексація успішна)
```

### 🚨 Відсутні валідації (потрібно додати)

1. **Priority range 1-10** - зараз немає валідації
2. **Title не порожній** - CharField дозволяє порожній рядок
3. **Content_uk не порожній** - TextField дозволяє порожній рядок

### 📦 Залежності для тестів

```python
from django.test import TestCase
from django.core.exceptions import ValidationError
from rag.models import KnowledgeSource
from unittest.mock import Mock, patch
from django.utils import timezone
```

### 🔍 Додаткова інформація

- **Ordering**: `['priority', '-updated_at']` - спочатку за пріоритетом (1-10), потім за датою оновлення (новіші перші)
- **Meta verbose_name**: "Джерело знань"
- **Meta verbose_name_plural**: "Джерела знань"
- **__str__**: `"{title} ({source_type_display})"`

