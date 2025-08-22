import logging
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from django.utils import timezone
from news.services.ai_processor.ai_processor_base import AINewsProcessor
from news.models import RawArticle, ProcessedArticle

logger = logging.getLogger(__name__)


@dataclass
class EnhancedInsights:
    """Структура розширених LAZYSOFT інсайтів"""
    
    # Бізнес інсайти для 3 аудиторій
    business_insights: Dict[str, Dict]  # english_audience, polish_audience, ukrainian_audience
    
    # Ключові моменти
    key_takeaways: Dict[str, List[str]]  # english, polish, ukrainian
    
    # Цікавинки та факти
    interesting_facts: Dict[str, List[str]]  # english, polish, ukrainian
    
    # LAZYSOFT рекомендації
    lazysoft_recommendations: Dict[str, str]  # english, polish, ukrainian
    
    # Бізнес можливості
    business_opportunities: Dict[str, str]  # english, polish, ukrainian
    
    # Практичні кроки
    implementation_steps: Dict[str, List[str]]  # english, polish, ukrainian
    
    # ROI оцінка
    roi_assessment: Dict[str, str]  # potential_savings, implementation_cost, payback_period
    
    # Метадані
    confidence_score: float
    analysis_timestamp: str
    ai_model_used: str


class EnhancedAIAnalyzer(AINewsProcessor):
    """
    Розширений AI аналізатор для створення детальних LAZYSOFT інсайтів.
    Генерує тримовні бізнес-інсайти з перспективи LAZYSOFT для МСБ аудиторії.
    """
    
    def __init__(self):
        super().__init__()
        
        # LAZYSOFT brand voice та експертиза
        self.lazysoft_context = {
            "company_description": "LAZYSOFT - automation agency specializing in business process automation, AI integration, and custom software solutions for SMB",
            "expertise_areas": [
                "Business process automation",
                "AI chatbots and virtual assistants", 
                "CRM systems integration",
                "Social media automation",
                "Custom software development",
                "E-commerce automation",
                "Marketing automation workflows"
            ],
            "target_markets": {
                "ukraine": {
                    "market_context": "Growing tech market, focus on EU integration, remote work culture",
                    "typical_budget": "$200-2000 monthly for automation",
                    "pain_points": ["manual processes", "EU compliance", "remote team coordination"],
                    "opportunities": ["EU market access", "outsourcing services", "tech talent"]
                },
                "poland": {
                    "market_context": "Developed EU market, strong economy, technology adoption",
                    "typical_budget": "$500-5000 monthly for tech solutions", 
                    "pain_points": ["competition", "scaling challenges", "digital transformation"],
                    "opportunities": ["EU single market", "digital services", "fintech"]
                },
                "uk": {
                    "market_context": "Mature market, high tech adoption, post-Brexit adaptation",
                    "typical_budget": "$1000-10000 monthly for business tools",
                    "pain_points": ["regulatory changes", "talent shortage", "cost optimization"],
                    "opportunities": ["fintech innovation", "AI adoption", "global market access"]
                }
            },
            "brand_voice": {
                "tone": "Expert but approachable, practical, results-focused",
                "perspective": "From the trenches experience with real SMB challenges",
                "style": "Clear actionable insights with concrete examples"
            }
        }
        
        logger.info("🚀 Enhanced AI Analyzer ініціалізовано з LAZYSOFT контекстом")

    def analyze_full_article_with_insights(self, raw_article: RawArticle, full_content: Optional[str] = None) -> EnhancedInsights:
        """
        Створює розширені LAZYSOFT інсайти для статті
        
        Args:
            raw_article: Сира стаття
            full_content: Повний контент (якщо є з Full Article Parser)
            
        Returns:
            EnhancedInsights з детальними тримовними інсайтами
        """
        logger.info(f"🔍 Створення розширених інсайтів: {raw_article.title[:50]}...")
        
        try:
            # Підготовлюємо контент для аналізу
            content_to_analyze = full_content or raw_article.content or raw_article.summary
            
            if not content_to_analyze:
                logger.warning("⚠️ Немає контенту для аналізу")
                return self._create_fallback_insights(raw_article)
            
            # Створюємо тримовні інсайти
            insights_data = {}
            
            # Генеруємо інсайти для кожної мови/аудиторії
            for language, market in [('english', 'uk'), ('polish', 'poland'), ('ukrainian', 'ukraine')]:
                logger.info(f"📝 Генерація {language} інсайтів...")
                
                market_insights = self._generate_market_specific_insights(
                    raw_article, content_to_analyze, language, market
                )
                insights_data[language] = market_insights
            
            # Створюємо фінальні інсайти
            enhanced_insights = self._compile_enhanced_insights(insights_data, raw_article)
            
            logger.info("✅ Розширені інсайти створено успішно")
            return enhanced_insights
            
        except Exception as e:
            logger.error(f"❌ Помилка створення інсайтів: {e}")
            return self._create_fallback_insights(raw_article)

    def _generate_market_specific_insights(self, raw_article: RawArticle, content: str, language: str, market: str) -> Dict:
        """Генерує інсайти для конкретного ринку та мови"""
        
        market_context = self.lazysoft_context["target_markets"][market]
        
        # Промпт для генерації інсайтів
        insights_prompt = f"""
        As LAZYSOFT automation agency expert, analyze this tech article for {market.upper()} small-medium business market.

        ARTICLE:
        Title: {raw_article.title}
        Content: {content[:1500]}
        Source: {raw_article.source.name}

        LAZYSOFT CONTEXT:
        - We specialize in: {', '.join(self.lazysoft_context['expertise_areas'][:4])}
        - {market.title()} market: {market_context['market_context']}
        - Typical budget: {market_context['typical_budget']}
        - Key pain points: {', '.join(market_context['pain_points'])}

        OUTPUT in {language.upper()} language as JSON:
        {{
            "main_insight": "2-3 sentences about why this matters for {market} SMB",
            "practical_applications": [
                "specific use case 1",
                "specific use case 2", 
                "specific use case 3"
            ],
            "lazysoft_perspective": "How we at LAZYSOFT see this trend/technology fitting into SMB automation strategy",
            "implementation_steps": [
                "step 1: assess current state",
                "step 2: plan implementation",
                "step 3: execute and measure"
            ],
            "roi_estimate": "Potential savings/benefits with timeframe",
            "key_takeaways": [
                "takeaway 1",
                "takeaway 2",
                "takeaway 3"
            ],
            "interesting_facts": [
                "surprising fact 1",
                "industry insight 2"
            ],
            "business_opportunity": "Specific opportunity for {market} businesses",
            "lazysoft_recommendation": "Our specific recommendation as automation experts"
        }}

        Respond ONLY with JSON in {language} language.
        """
        
        try:
            # Викликаємо AI
            ai_response = self._call_ai_model(insights_prompt, max_tokens=1200)
            
            # Парсимо відповідь
            insights_data = self._parse_insights_response(ai_response, language)
            
            return insights_data
            
        except Exception as e:
            logger.error(f"❌ Помилка генерації {language} інсайтів: {e}")
            return self._create_fallback_market_insights(language, market)

    def _parse_insights_response(self, ai_response: str, language: str) -> Dict:
        """Парсить AI відповідь з інсайтами"""
        try:
            # Очищаємо від markdown
            cleaned_response = ai_response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            
            # Парсимо JSON
            insights_data = json.loads(cleaned_response.strip())
            
            # Валідуємо структуру
            required_fields = [
                'main_insight', 'practical_applications', 'lazysoft_perspective',
                'implementation_steps', 'roi_estimate', 'key_takeaways',
                'interesting_facts', 'business_opportunity', 'lazysoft_recommendation'
            ]
            
            for field in required_fields:
                if field not in insights_data:
                    insights_data[field] = f"Generated insight for {field}"
            
            # Обмежуємо довжину списків
            for list_field in ['practical_applications', 'implementation_steps', 'key_takeaways', 'interesting_facts']:
                if isinstance(insights_data[list_field], list):
                    insights_data[list_field] = insights_data[list_field][:5]  # Максимум 5 елементів
            
            return insights_data
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"⚠️ Помилка парсингу {language} інсайтів: {e}")
            return self._create_fallback_market_insights(language, 'general')

    def _compile_enhanced_insights(self, insights_data: Dict, raw_article: RawArticle) -> EnhancedInsights:
        """Компілює всі інсайти в фінальну структуру"""
        
        # Структуруємо бізнес інсайти
        business_insights = {}
        for lang_key, lang_name in [('english', 'english_audience'), ('polish', 'polish_audience'), ('ukrainian', 'ukrainian_audience')]:
            if lang_key in insights_data:
                business_insights[lang_name] = {
                    'main_insight': insights_data[lang_key].get('main_insight', ''),
                    'practical_applications': insights_data[lang_key].get('practical_applications', []),
                    'lazysoft_perspective': insights_data[lang_key].get('lazysoft_perspective', '')
                }
        
        # Збираємо ключові моменти
        key_takeaways = {}
        interesting_facts = {}
        lazysoft_recommendations = {}
        business_opportunities = {}
        implementation_steps = {}
        
        for lang_key, lang_short in [('english', 'english'), ('polish', 'polish'), ('ukrainian', 'ukrainian')]:
            if lang_key in insights_data:
                key_takeaways[lang_short] = insights_data[lang_key].get('key_takeaways', [])
                interesting_facts[lang_short] = insights_data[lang_key].get('interesting_facts', [])
                lazysoft_recommendations[lang_short] = insights_data[lang_key].get('lazysoft_recommendation', '')
                business_opportunities[lang_short] = insights_data[lang_key].get('business_opportunity', '')
                implementation_steps[lang_short] = insights_data[lang_key].get('implementation_steps', [])
        
        # ROI оцінка (беремо з англійської версії)
        english_data = insights_data.get('english', {})
        roi_assessment = {
            'potential_savings': english_data.get('roi_estimate', 'To be determined'),
            'implementation_cost': 'Depends on scope and requirements',
            'payback_period': 'Typically 3-12 months for automation projects'
        }
        
        return EnhancedInsights(
            business_insights=business_insights,
            key_takeaways=key_takeaways,
            interesting_facts=interesting_facts,
            lazysoft_recommendations=lazysoft_recommendations,
            business_opportunities=business_opportunities,
            implementation_steps=implementation_steps,
            roi_assessment=roi_assessment,
            confidence_score=0.8,  # Базовий скор впевненості
            analysis_timestamp=timezone.now().isoformat(),
            ai_model_used=self.preferred_model
        )

    def _create_fallback_insights(self, raw_article: RawArticle) -> EnhancedInsights:
        """Створює fallback інсайти якщо AI недоступний"""
        
        title = raw_article.title
        category = raw_article.source.category
        
        # Базові інсайти на основі категорії
        fallback_data = {
            'english_audience': {
                'main_insight': f"This {category} technology could benefit UK businesses through automation and efficiency improvements.",
                'practical_applications': ["Process automation", "Cost reduction", "Efficiency improvement"],
                'lazysoft_perspective': "At LAZYSOFT, we see this as an opportunity to help businesses streamline operations."
            },
            'polish_audience': {
                'main_insight': f"Ta technologia {category} może pomóc polskim firmom poprzez automatyzację i poprawę efektywności.",
                'practical_applications': ["Automatyzacja procesów", "Redukcja kosztów", "Poprawa wydajności"],
                'lazysoft_perspective': "W LAZYSOFT widzimy to jako możliwość pomocy firmom w usprawnieniu działań."
            },
            'ukrainian_audience': {
                'main_insight': f"Ця технологія {category} може допомогти українським компаніям через автоматизацію та покращення ефективності.",
                'practical_applications': ["Автоматизація процесів", "Зниження витрат", "Підвищення ефективності"],
                'lazysoft_perspective': "У LAZYSOFT ми бачимо це як можливість допомогти бізнесу оптимізувати операції."
            }
        }
        
        key_takeaways = {
            'english': ["Technology offers automation potential", "Could improve business efficiency", "Worth exploring for SMB"],
            'polish': ["Technologia oferuje potencjał automatyzacji", "Może poprawić efektywność biznesu", "Warto zbadać dla MŚP"],
            'ukrainian': ["Технологія пропонує потенціал автоматизації", "Може покращити ефективність бізнесу", "Варто вивчити для МСБ"]
        }
        
        return EnhancedInsights(
            business_insights=fallback_data,
            key_takeaways=key_takeaways,
            interesting_facts={'english': [f"Article from {raw_article.source.name}"], 'polish': [f"Artykuł z {raw_article.source.name}"], 'ukrainian': [f"Стаття з {raw_article.source.name}"]},
            lazysoft_recommendations={'english': "Contact LAZYSOFT for detailed analysis", 'polish': "Skontaktuj się z LAZYSOFT w celu szczegółowej analizy", 'ukrainian': "Зв'яжіться з LAZYSOFT для детального аналізу"},
            business_opportunities={'english': "Automation opportunity", 'polish': "Możliwość automatyzacji", 'ukrainian': "Можливість автоматизації"},
            implementation_steps={'english': ["Assess current state", "Plan implementation", "Execute"], 'polish': ["Oceń obecny stan", "Zaplanuj wdrożenie", "Wykonaj"], 'ukrainian': ["Оцінити поточний стан", "Спланувати впровадження", "Виконати"]},
            roi_assessment={'potential_savings': 'To be determined', 'implementation_cost': 'Varies by scope', 'payback_period': '6-12 months typically'},
            confidence_score=0.6,
            analysis_timestamp=timezone.now().isoformat(),
            ai_model_used='fallback'
        )

    def _create_fallback_market_insights(self, language: str, market: str) -> Dict:
        """Створює fallback інсайти для конкретного ринку"""
        
        templates = {
            'english': {
                'main_insight': f"This technology presents opportunities for {market} businesses to improve operations.",
                'practical_applications': ["Process automation", "Cost optimization", "Efficiency gains"],
                'lazysoft_perspective': "LAZYSOFT can help implement this technology for SMB clients.",
                'key_takeaways': ["Automation potential", "Business value", "Implementation considerations"],
                'business_opportunity': f"Market opportunity in {market} for automation services"
            },
            'polish': {
                'main_insight': f"Ta technologia stwarza możliwości dla firm w {market} do poprawy działań.",
                'practical_applications': ["Automatyzacja procesów", "Optymalizacja kosztów", "Wzrost wydajności"],
                'lazysoft_perspective': "LAZYSOFT może pomóc wdrożyć tę technologię dla klientów MŚP.",
                'key_takeaways': ["Potencjał automatyzacji", "Wartość biznesowa", "Kwestie wdrożenia"],
                'business_opportunity': f"Możliwość rynkowa w {market} dla usług automatyzacji"
            },
            'ukrainian': {
                'main_insight': f"Ця технологія відкриває можливості для бізнесу в {market} покращити операції.",
                'practical_applications': ["Автоматизація процесів", "Оптимізація витрат", "Підвищення ефективності"],
                'lazysoft_perspective': "LAZYSOFT може допомогти впровадити цю технологію для МСБ клієнтів.",
                'key_takeaways': ["Потенціал автоматизації", "Бізнес-цінність", "Питання впровадження"],
                'business_opportunity': f"Ринкова можливість в {market} для послуг автоматизації"
            }
        }
        
        return templates.get(language, templates['english'])