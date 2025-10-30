# Google News Publisher Center & Reader Revenue Manager Setup

## 🔴 Проблема

На сторінці https://lazysoft.pl/news/ не з'являється форма підписки від Google News.

## 🔍 Діагностика

Код Reader Revenue Manager (RRM) є в шаблоні, але не працює. Можливі причини:

1. ❌ Сайт не верифікований в Google News Publisher Center
2. ❌ Product ID неправильний або не налаштований
3. ❌ Publication не схвалена Google

## ✅ Рішення: Налаштування Google News Publisher Center

### Крок 1: Реєстрація в Google News Publisher Center

1. Зайдіть на https://publishercenter.google.com/
2. Увійдіть з Google акаунтом власника сайту
3. Натисніть "Add publication" або "Додати публікацію"
4. Введіть URL: `https://lazysoft.pl`

### Крок 2: Верифікація власності сайту

Виберіть один з методів верифікації:

**Метод 1: HTML файл** (найпростіший)
1. Завантажте файл верифікації від Google
2. Помістіть його в `/static/` директорію
3. Перевірте доступ: `https://lazysoft.pl/static/google-verification-file.html`
4. Натисніть "Verify" в Publisher Center

**Метод 2: Meta tag** (вже є)
Код вже є в `base.html`:
```html
<meta name="google-site-verification" content="{{ GOOGLE_SITE_VERIFICATION }}" />
```
Просто додайте в `.env`:
```bash
GOOGLE_SITE_VERIFICATION=ваш_код_верифікації
```

**Метод 3: Google Analytics**
Якщо використовуєте Google Analytics, можна верифікувати через нього.

### Крок 3: Налаштування Publication

1. **Publication Name**: `LAZYSOFT Tech News`
2. **Publication Language**: Виберіть основну мову (en/uk/pl)
3. **Country**: Poland (PL)
4. **Content Type**: News
5. **RSS Feeds**:
   - Додайте: `https://lazysoft.pl/news-sitemap-uk.xml`
   - Додайте: `https://lazysoft.pl/news-sitemap-pl.xml`
   - Додайте: `https://lazysoft.pl/news-sitemap-en.xml`

### Крок 4: Reader Revenue Manager (Підписка)

1. В Publisher Center перейдіть в розділ **"Reader revenue"**
2. Натисніть **"Set up reader revenue"**
3. Виберіть тип: **"Newsletters"** або **"Subscriptions"**
4. Створіть **Product**:
   - Product name: "LAZYSOFT Daily Newsletter"
   - Product type: Free or Paid
   - Скопіюйте **Product ID** (виглядає як `CAoxx-XXXX:openaccess`)

### Крок 5: Оновити Product ID в коді

Замініть `CAown-DCDA:openaccess` на ваш реальний Product ID:

```javascript
isPartOfProductId: "ВАШ_РЕАЛЬНИЙ_PRODUCT_ID",
```

Файл: `core/templates/news/news_list.html` (рядок 40)

### Крок 6: Перевірка після деплою

1. Зайдіть на `https://lazysoft.pl/news/`
2. Відкрийте Developer Console (F12)
3. Подивіться на Console logs:

```
[RRM] Initializing Google News Reader Revenue Manager
[RRM] SWG_BASIC loaded successfully
[RRM] Initialized with config: {productId: "...", lang: "en", theme: "dark"}
[RRM] Container found, rendering subscribe button...
[RRM] Subscribe button rendered successfully
```

4. Якщо є помилки - вони будуть видимі в console

## 🧪 Тестування

### Локальне тестування

Створіть файл `test-rrm.html`:
```html
<!DOCTYPE html>
<html>
<head><title>Test RRM</title></head>
<body>
  <h1>Test Google RRM</h1>
  <div id="rrm-signup" style="border: 2px solid red; padding: 20px; min-height: 100px;"></div>

  <script async src="https://news.google.com/swg/js/v1/swg-basic.js"></script>
  <script>
    (self.SWG_BASIC = self.SWG_BASIC || []).push(basic => {
      basic.init({
        type: "Product",
        isPartOfType: ["Product"],
        isPartOfProductId: "YOUR_PRODUCT_ID_HERE",
        clientOptions: { theme: "dark", lang: "en" }
      });

      setTimeout(() => {
        basic.subscribeButton({
          container: document.getElementById('rrm-signup'),
          lang: "en",
          theme: "dark"
        });
      }, 1000);
    });
  </script>
</body>
</html>
```

## 📊 Альтернативні рішення

Якщо Google RRM не працює, можна використати:

### 1. Mailchimp Newsletter
```html
<form action="https://lazysoft.us21.list-manage.com/subscribe/post" method="POST">
  <input type="email" name="EMAIL" placeholder="Your email" required>
  <button type="submit">Subscribe</button>
</form>
```

### 2. Custom Newsletter форма
Створити свою систему підписки через Django + Celery + SendGrid/AWS SES

### 3. RSS Subscribe Button
```html
<a href="/news-sitemap-en.xml" class="rss-button">
  📰 Subscribe via RSS
</a>
```

## 🔗 Корисні посилання

- [Google Publisher Center](https://publishercenter.google.com/)
- [Reader Revenue Manager Docs](https://developers.google.com/news/subscribe)
- [Verify site ownership](https://support.google.com/webmasters/answer/9008080)
- [RRM Implementation Guide](https://developers.google.com/news/subscribe/extended-access)

## ⚙️ Зміни в коді

Додано debug logging для діагностики проблем:
- Логи завантаження SWG_BASIC
- Логи ініціалізації
- Логи рендерингу кнопки
- Error handling для всіх кроків

Перевіряйте Console в браузері для діагностики!

---

**Оновлено**: 2025-10-30
**Файл**: `core/templates/news/news_list.html`
**Статус**: Додано debug logging ✅
