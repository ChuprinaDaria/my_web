from django.core.management.base import BaseCommand
from django.db.models import Count
from news.models import RSSSource, NewsCategory


class Command(BaseCommand):
    help = 'Налаштування всіх RSS джерел одним файлом'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update',
            action='store_true',
            help='Оновити існуючі джерела'
        )
        
        parser.add_argument(
            '--deactivate-old',
            action='store_true',
            help='Деактивувати джерела не з цього списку'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Налаштування повної RSS системи LAZYSOFT')
        )
        
        # Спочатку створюємо категорії
        self.create_categories()
        
        # Потім додаємо всі RSS джерела
        self.create_rss_sources(options['update'])
        
        # Статистика
        self.show_statistics()
        
        if options['deactivate_old']:
            self.deactivate_unlisted_sources()

    def create_categories(self):
        """Створює всі категорії новин"""
        categories_data = [
            {
                "slug": "ai",
                "name_en": "AI & Machine Learning",
                "name_uk": "ШІ та машинне навчання", 
                "name_pl": "AI i uczenie maszynowe",
                "description_en": "Latest AI and machine learning news for business applications",
                "description_uk": "Останні новини ШІ та машинного навчання для бізнесу",
                "description_pl": "Najnowsze wiadomości AI i uczenia maszynowego dla biznesu",
                "icon": "🤖",
                "color": "#00D4FF",
                "cta_title_en": "Implement AI in Your Business",
                "cta_title_uk": "Впровадити ШІ у ваш бізнес",
                "cta_title_pl": "Wdrożyć AI w Twoim biznesie",
                "cta_description_en": "Transform your business with AI automation and intelligent solutions",
                "cta_description_uk": "Трансформуйте свій бізнес за допомогою ШІ автоматизації",
                "cta_description_pl": "Przekształć swój biznes dzięki automatyzacji AI",
                "cta_button_text_en": "Get AI Audit",
                "cta_button_text_uk": "Отримати AI аудит",
                "cta_button_text_pl": "Otrzymać audyt AI"
            },
            {
                "slug": "automation",
                "name_en": "Business Automation",
                "name_uk": "Автоматизація бізнесу",
                "name_pl": "Automatyzacja biznesu",
                "description_en": "Process automation, RPA, and workflow optimization news",
                "description_uk": "Автоматизація процесів, RPA та оптимізація робочих процесів",
                "description_pl": "Automatyzacja procesów, RPA i optymalizacja przepływów pracy",
                "icon": "⚡",
                "color": "#66FF00",
                "cta_title_en": "Automate Your Workflows",
                "cta_title_uk": "Автоматизувати робочі процеси",
                "cta_title_pl": "Zautomatyzować przepływy pracy",
                "cta_description_en": "Streamline operations with custom automation solutions",
                "cta_description_uk": "Оптимізуйте операції за допомогою автоматизації",
                "cta_description_pl": "Usprawniaj operacje dzięki automatyzacji",
                "cta_button_text_en": "Start Automation",
                "cta_button_text_uk": "Почати автоматизацію",
                "cta_button_text_pl": "Rozpocząć automatyzację"
            },
            {
                "slug": "crm",
                "name_en": "CRM & Customer Management",
                "name_uk": "CRM та управління клієнтами",
                "name_pl": "CRM i zarządzanie klientami",
                "description_en": "CRM systems, customer management, and sales automation",
                "description_uk": "CRM системи, управління клієнтами та автоматизація продажів",
                "description_pl": "Systemy CRM, zarządzanie klientami i automatyzacja sprzedaży",
                "icon": "👥",
                "color": "#FF6B35",
                "cta_title_en": "Optimize Your CRM",
                "cta_title_uk": "Оптимізувати CRM систему",
                "cta_title_pl": "Zoptymalizować system CRM"
            },
            {
                "slug": "seo",
                "name_en": "SEO & Digital Marketing",
                "name_uk": "SEO та цифровий маркетинг",
                "name_pl": "SEO i marketing cyfrowy",
                "description_en": "Search engine optimization and digital marketing strategies",
                "description_uk": "Оптимізація для пошукових систем та стратегії цифрового маркетингу",
                "description_pl": "Optymalizacja SEO i strategie marketingu cyfrowego",
                "icon": "📈",
                "color": "#9B59B6",
                "cta_title_en": "Boost Your SEO",
                "cta_title_uk": "Покращити SEO",
                "cta_title_pl": "Ulepszyć SEO"
            },
            {
                "slug": "social",
                "name_en": "Social Media Marketing",
                "name_uk": "Маркетинг у соціальних мережах",
                "name_pl": "Marketing w mediach społecznościowych",
                "description_en": "Social media marketing automation and strategies",
                "description_uk": "Автоматизація маркетингу в соціальних мережах",
                "description_pl": "Automatyzacja marketingu w mediach społecznościowych",
                "icon": "📱",
                "color": "#E91E63",
                "cta_title_en": "Automate Social Media",
                "cta_title_uk": "Автоматизувати соцмережі",
                "cta_title_pl": "Zautomatyzować media społecznościowe"
            },
            {
                "slug": "chatbots",
                "name_en": "Chatbots & Conversational AI",
                "name_uk": "Чат-боти та розмовний ШІ",
                "name_pl": "Chatboty i konwersacyjne AI",
                "description_en": "Chatbot development and conversational AI solutions",
                "description_uk": "Розробка чат-ботів та рішення розмовного ШІ",
                "description_pl": "Rozwój chatbotów i rozwiązania konwersacyjnego AI",
                "icon": "💬",
                "color": "#00BCD4",
                "cta_title_en": "Build Smart Chatbots",
                "cta_title_uk": "Створити розумні чат-боти",
                "cta_title_pl": "Stworzyć inteligentne chatboty"
            },
            {
                "slug": "ecommerce",
                "name_en": "E-commerce Development",
                "name_uk": "Розробка електронної комерції",
                "name_pl": "Rozwój e-commerce",
                "description_en": "E-commerce platforms, online stores, and digital commerce",
                "description_uk": "E-commerce платформи, онлайн-магазини та цифрова комерція",
                "description_pl": "Platformy e-commerce, sklepy internetowe i handel cyfrowy",
                "icon": "🛒",
                "color": "#FF9800",
                "cta_title_en": "Launch Your Online Store",
                "cta_title_uk": "Запустити онлайн-магазин",
                "cta_title_pl": "Uruchomić sklep internetowy"
            },
            {
                "slug": "fintech",
                "name_en": "Fintech Automation",
                "name_uk": "Фінтех автоматизація",
                "name_pl": "Automatyzacja fintech",
                "description_en": "Financial technology, payments, and banking automation",
                "description_uk": "Фінансові технології, платежі та автоматизація банкінгу",
                "description_pl": "Technologie finansowe, płatności i automatyzacja bankowa",
                "icon": "💰",
                "color": "#4CAF50",
                "cta_title_en": "Modernize Financial Operations",
                "cta_title_uk": "Модернізувати фінансові операції",
                "cta_title_pl": "Zmodernizować operacje finansowe"
            },
            {
                "slug": "corporate",
                "name_en": "Corporate & IT News",
                "name_uk": "Корпоративні та IT новини",
                "name_pl": "Wiadomości korporacyjne i IT",
                "description_en": "Corporate technology news and IT business updates",
                "description_uk": "Корпоративні технологічні новини та IT бізнес оновлення",
                "description_pl": "Wiadomości technologii korporacyjnych i aktualizacje biznesu IT",
                "icon": "🏢",
                "color": "#607D8B",
                "cta_title_en": "Enterprise IT Solutions",
                "cta_title_uk": "Корпоративні IT рішення",
                "cta_title_pl": "Rozwiązania IT dla przedsiębiorstw"
            },
            {
                "slug": "general",
                "name_en": "General Tech News",
                "name_uk": "Загальні технологічні новини",
                "name_pl": "Ogólne wiadomości technologiczne",
                "description_en": "General technology news and industry insights",
                "description_uk": "Загальні технологічні новини та галузеві інсайти",
                "description_pl": "Ogólne wiadomości technologiczne i spostrzeżenia branżowe",
                "icon": "🌐",
                "color": "#795548",
                "cta_title_en": "Stay Updated with Tech",
                "cta_title_uk": "Залишатися в курсі технологій",
                "cta_title_pl": "Być na bieżąco z technologią"
            }
        ]
        
        self.stdout.write('📂 Створення категорій...')
        created_categories = 0
        
        for cat_data in categories_data:
            category, created = NewsCategory.objects.get_or_create(
                slug=cat_data["slug"],
                defaults=cat_data
            )
            if created:
                created_categories += 1
                self.stdout.write(f"  ✅ {category.name_uk}")
            else:
                self.stdout.write(f"  ↻ {category.name_uk} (існує)")
        
        self.stdout.write(
            self.style.SUCCESS(f"📂 Створено {created_categories} нових категорій")
        )

    def create_rss_sources(self, update_existing=False):
        """Створює всі RSS джерела"""
        
        # 🎯 ВСІІ RSS ДЖЕРЕЛА В ОДНОМУ МІСЦІ
        all_rss_sources = [
            
            # === ENGLISH SOURCES ===
            
            # 🤖 AI & MACHINE LEARNING
            {"name": "VentureBeat AI", "url": "https://feeds.feedburner.com/venturebeat/SZYF", "language": "en", "category": "ai"},
            {"name": "MIT Technology Review", "url": "https://www.technologyreview.com/feed/", "language": "en", "category": "ai"},
            {"name": "AI Weekly", "url": "https://aiweekly.co/issues.rss", "language": "en", "category": "ai"},
            {"name": "Towards Data Science", "url": "https://towardsdatascience.com/feed", "language": "en", "category": "ai"},
            {"name": "Google AI Blog", "url": "https://ai.googleblog.com/feeds/posts/default", "language": "en", "category": "ai"},
            {"name": "Meta AI Blog", "url": "https://ai.meta.com/blog/rss/", "language": "en", "category": "ai"},
            {"name": "Microsoft AI Blog", "url": "https://blogs.microsoft.com/ai/feed/", "language": "en", "category": "ai"},
            {"name": "Amazon Science", "url": "https://www.amazon.science/blog/rss.xml", "language": "en", "category": "ai"},
            {"name": "Apple ML Journal", "url": "https://machinelearning.apple.com/rss.xml", "language": "en", "category": "ai"},
            {"name": "NVIDIA Developer", "url": "https://developer.nvidia.com/blog/feed", "language": "en", "category": "ai"},
            {"name": "Intel AI", "url": "https://www.intel.com/content/www/us/en/artificial-intelligence/rss.xml", "language": "en", "category": "ai"},
            {"name": "Nature ML", "url": "https://www.nature.com/natmachintell.rss", "language": "en", "category": "ai"},
            
            # ⚡ BUSINESS AUTOMATION
            {"name": "Process Excellence Network", "url": "https://www.processexcellencenetwork.com/rss-feeds", "language": "en", "category": "automation"},
            {"name": "UiPath Blog", "url": "https://uipath.com/blog/rss.xml", "language": "en", "category": "automation"},
            {"name": "Zapier Blog", "url": "https://zapier.com/blog/feeds/all.rss", "language": "en", "category": "automation"},
            {"name": "Make Blog", "url": "https://www.make.com/en/blog/rss.xml", "language": "en", "category": "automation"},
            {"name": "Notion Blog", "url": "https://www.notion.so/blog/rss.xml", "language": "en", "category": "automation"},
            {"name": "Google Developers", "url": "https://developers.googleblog.com/feeds/posts/default", "language": "en", "category": "automation"},
            {"name": "Meta Engineering", "url": "https://engineering.fb.com/feed/", "language": "en", "category": "automation"},
            {"name": "Microsoft Developer", "url": "https://devblogs.microsoft.com/feed/", "language": "en", "category": "automation"},
            {"name": "GitHub Blog", "url": "https://github.blog/feed/", "language": "en", "category": "automation"},
            {"name": "Stack Overflow Blog", "url": "https://stackoverflow.blog/feed/", "language": "en", "category": "automation"},
            {"name": "IEEE Spectrum Robotics", "url": "https://spectrum.ieee.org/robotics/feed", "language": "en", "category": "automation"},
            {"name": "Boston Dynamics", "url": "https://www.bostondynamics.com/blog.rss", "language": "en", "category": "automation"},
            {"name": "IBM Developer", "url": "https://developer.ibm.com/blogs/feed/", "language": "en", "category": "automation"},
            
            # 👥 CRM & CUSTOMER MANAGEMENT
            {"name": "Salesforce Blog", "url": "https://www.salesforce.com/resources/articles/feed/", "language": "en", "category": "crm"},
            {"name": "HubSpot Blog", "url": "https://blog.hubspot.com/rss.xml", "language": "en", "category": "crm"},
            {"name": "Nutshell CRM", "url": "https://nutshell.com/feed", "language": "en", "category": "crm"},
            {"name": "Salesforce Engineering", "url": "https://engineering.salesforce.com/feed", "language": "en", "category": "crm"},
            
            # 📈 SEO & DIGITAL MARKETING
            {"name": "Search Engine Land", "url": "https://searchengineland.com/feed", "language": "en", "category": "seo"},
            {"name": "Moz Blog", "url": "https://moz.com/blog/feed", "language": "en", "category": "seo"},
            {"name": "SEMrush Blog", "url": "https://semrush.com/blog/feed", "language": "en", "category": "seo"},
            {"name": "Content Marketing Institute", "url": "https://contentmarketinginstitute.com/feed/", "language": "en", "category": "seo"},
            {"name": "Google Search Central", "url": "https://developers.google.com/search/blog/feeds/posts/default", "language": "en", "category": "seo"},
            
            # 📱 SOCIAL MEDIA MARKETING
            {"name": "Social Media Examiner", "url": "https://socialmediaexaminer.com/feed/", "language": "en", "category": "social"},
            {"name": "Buffer Blog", "url": "https://feeds.feedburner.com/bufferapp", "language": "en", "category": "social"},
            {"name": "Meta for Business", "url": "https://www.facebook.com/business/news/rss", "language": "en", "category": "social"},
            {"name": "Mailchimp Blog", "url": "https://mailchimp.com/resources/feed/", "language": "en", "category": "social"},
            {"name": "ConvertKit Blog", "url": "https://convertkit.com/blog/feed", "language": "en", "category": "social"},
            
            # 💬 CHATBOTS & CONVERSATIONAL AI
            {"name": "Chatbots Life", "url": "https://chatbotslife.com/feed/", "language": "en", "category": "chatbots"},
            {"name": "Chatbots Magazine", "url": "https://chatbotsmagazine.com/feed", "language": "en", "category": "chatbots"},
            
            # 🛒 E-COMMERCE DEVELOPMENT
            {"name": "Practical Ecommerce", "url": "https://www.practicalecommerce.com/feed/", "language": "en", "category": "ecommerce"},
            {"name": "Shopify Blog", "url": "https://shopify.com/blog.rss", "language": "en", "category": "ecommerce"},
            {"name": "BigCommerce Blog", "url": "https://www.bigcommerce.com/blog/feed/", "language": "en", "category": "ecommerce"},
            
            # 💰 FINTECH AUTOMATION
            {"name": "Bank Automation News", "url": "https://bankautomationnews.com/feed", "language": "en", "category": "fintech"},
            {"name": "CoinDesk", "url": "https://feeds.feedburner.com/CoinDesk", "language": "en", "category": "fintech"},
            {"name": "TechCrunch Fintech", "url": "https://techcrunch.com/category/fintech/feed/", "language": "en", "category": "fintech"},
            {"name": "PaymentsSource", "url": "https://www.paymentssource.com/feed", "language": "en", "category": "fintech"},
            
            # 🏢 CORPORATE & IT NEWS
            {"name": "TechCrunch", "url": "https://techcrunch.com/feed/", "language": "en", "category": "corporate"},
            {"name": "CIO Magazine", "url": "https://cio.com/feed/", "language": "en", "category": "corporate"},
            {"name": "TechRepublic", "url": "https://www.techrepublic.com/rssfeeds/articles/", "language": "en", "category": "corporate"},
            {"name": "Google Cloud Blog", "url": "https://cloud.google.com/blog/rss", "language": "en", "category": "corporate"},
            {"name": "Microsoft Business", "url": "https://www.microsoft.com/en-us/microsoft-365/blog/feed/", "language": "en", "category": "corporate"},
            {"name": "AWS News", "url": "https://aws.amazon.com/blogs/aws/feed/", "language": "en", "category": "corporate"},
            {"name": "Tesla Blog", "url": "https://www.tesla.com/blog/rss", "language": "en", "category": "corporate"},
            
            # 🌐 GENERAL TECH NEWS
            {"name": "Wired Science", "url": "https://www.wired.com/feed/category/science/latest/rss", "language": "en", "category": "general"},
            {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index", "language": "en", "category": "general"},
            {"name": "Dev.to", "url": "https://dev.to/feed", "language": "en", "category": "general"},
            {"name": "Hacker News", "url": "https://hnrss.org/frontpage", "language": "en", "category": "general"},
            {"name": "Science Magazine", "url": "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science", "language": "en", "category": "general"},
            
            # === POLISH SOURCES ===
            
            # 🇵🇱 POLISH RSS SOURCES
            {"name": "PolsatNews Tech", "url": "https://www.polsatnews.pl/rss/technologie.xml", "language": "pl", "category": "general"},
            {"name": "PolsatNews Business", "url": "https://www.polsatnews.pl/rss/biznes.xml", "language": "pl", "category": "corporate"},
            {"name": "Bankier.pl", "url": "https://www.bankier.pl/rss", "language": "pl", "category": "fintech"},
            {"name": "WirtualneMedia", "url": "https://www.wirtualnemedia.pl/rss.html", "language": "pl", "category": "seo"},
            {"name": "WNP.pl", "url": "http://www.wnp.pl/rss/serwis_rss.xml", "language": "pl", "category": "automation"},
            
            # === UKRAINIAN SOURCES ===
            
            # 🇺🇦 UKRAINIAN RSS SOURCES  
            {"name": "DOU.UA Podcast", "url": "http://podcast.dou.ua/rss", "language": "uk", "category": "general"},
            # AIN.UA - потрібна перевірка працездатності
            # {"name": "AIN.UA", "url": "https://ain.ua/rss/", "language": "uk", "category": "corporate"},
        ]
        
        self.stdout.write('📡 Створення RSS джерел...')
        created_sources = 0
        updated_sources = 0
        
        for source_data in all_rss_sources:
            try:
                if update_existing:
                    source, created = RSSSource.objects.update_or_create(
                        url=source_data["url"],
                        defaults=source_data
                    )
                    if created:
                        created_sources += 1
                        self.stdout.write(f"  ✅ {source.name}")
                    else:
                        updated_sources += 1
                        self.stdout.write(f"  🔄 {source.name} (оновлено)")
                else:
                    source, created = RSSSource.objects.get_or_create(
                        url=source_data["url"],
                        defaults=source_data
                    )
                    if created:
                        created_sources += 1
                        self.stdout.write(f"  ✅ {source.name}")
                    else:
                        self.stdout.write(f"  ↻ {source.name} (існує)")
                        
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ❌ Помилка з {source_data['name']}: {e}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"📡 Створено {created_sources} нових джерел, "
                f"оновлено {updated_sources}"
            )
        )

    def show_statistics(self):
        """Показує статистику RSS джерел"""
        total_sources = RSSSource.objects.count()
        active_sources = RSSSource.objects.filter(is_active=True).count()
        
        self.stdout.write('\n📊 СТАТИСТИКА RSS СИСТЕМИ:')
        self.stdout.write('=' * 50)
        self.stdout.write(f"📚 Всього джерел: {total_sources}")
        self.stdout.write(f"✅ Активних: {active_sources}")
        self.stdout.write(f"❌ Неактивних: {total_sources - active_sources}")
        
        # По мовах
        self.stdout.write('\n🌍 РОЗПОДІЛ ПО МОВАХ:')
        languages = RSSSource.objects.values('language').annotate(
            count=Count('id')
        ).order_by('-count')
        
        for lang in languages:
            lang_name = {'en': '🇬🇧 Англійська', 'pl': '🇵🇱 Польська', 'uk': '🇺🇦 Українська'}
            self.stdout.write(f"  {lang_name.get(lang['language'], lang['language'])}: {lang['count']}")
        
        # По категоріях
        self.stdout.write('\n📂 ТОП КАТЕГОРІЇ:')
        categories = RSSSource.objects.values('category').annotate(
            count=Count('id')
        ).order_by('-count')
        
        category_icons = {
            'ai': '🤖', 'automation': '⚡', 'crm': '👥', 'seo': '📈',
            'social': '📱', 'chatbots': '💬', 'ecommerce': '🛒',
            'fintech': '💰', 'corporate': '🏢', 'general': '🌐'
        }
        
        for cat in categories:
            icon = category_icons.get(cat['category'], '📄')
            self.stdout.write(f"  {icon} {cat['category']}: {cat['count']} джерел")
        
        self.stdout.write('\n🎯 Система готова до парсингу!')
        self.stdout.write('Запустіть: python manage.py parse_rss --verbose')

    def deactivate_unlisted_sources(self):
        """Деактивує джерела не з цього списку"""
        # Тут можна додати логіку деактивації старих джерел
        pass