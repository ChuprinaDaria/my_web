import logging
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from django.utils import timezone
from django.db.models import Q, Count, Avg
from news.models import RawArticle, ProcessedArticle
from news.services.ai_processor.ai_processor_base import AINewsProcessor

logger = logging.getLogger(__name__)


@dataclass
class RelevanceAnalysis:
    """Результат аналізу релевантності статті для МСБ аудиторії"""
    article_id: int
    title: str
    relevance_score: int  # 1-10
    category_match: str
    target_audience: str  # 'ukraine', 'poland', 'uk', 'general'
    business_impact: str  # 'high', 'medium', 'low'
    implementation_complexity: str  # 'easy', 'medium', 'hard'
    cost_implications: str  # 'low-cost', 'medium-cost', 'high-cost'
    key_benefits: List[str]
    potential_concerns: List[str]
    confidence_level: float  # 0.0-1.0
    analysis_reasoning: str


class AudienceAnalyzer(AINewsProcessor):
    """
    AI аналізатор для селекції статей релевантних для МСБ аудиторії.
    Вибирає топ-5 найкращих статей щодня на основі:
    - Релевантності для малого/середнього бізнесу
    - Практичності впровадження  
    - Вартості рішень
    - Регіональної специфіки (Україна, Польща, Великобританія)
    """
    
    def __init__(self):
        super().__init__()
        
        # Профіль цільової аудиторії LAZYSOFT
        self.audience_profile = {
            "business_size": "small to medium business (1-50 employees)",
            "budget_range": "$100-$5000 monthly for tech solutions",
            "pain_points": [
                "limited budget for technology",
                "manual repetitive processes", 
                "time management challenges",
                "lack of technical expertise",
                "customer service bottlenecks",
                "marketing automation needs",
                "data management issues"
            ],
            "interests": [
                "business automation tools",
                "cost-effective AI solutions", 
                "CRM systems for small business",
                "social media automation",
                "customer service chatbots",
                "marketing automation",
                "productivity tools",
                "e-commerce solutions"
            ],
            "industries": [
                "accounting and bookkeeping",
                "beauty and wellness",
                "e-commerce and retail", 
                "professional services",
                "restaurants and hospitality",
                "real estate",
                "consulting",
                "creative agencies"
            ],
            "geographic_focus": [
                "Ukraine (Ukrainian market specifics)",
                "Poland (Polish business environment)", 
                "United Kingdom (UK regulations and practices)",
                "European Union (GDPR compliance, EU market)"
            ],
            "typical_search_queries": [
                "CRM for small business",
                "automation tools for SMB",
                "chatbot for customer service",
                "social media automation",
                "AI tools for business",
                "cost-effective business solutions"
            ]
        }
        
        # Критерії скорингу (вага кожного фактору)
        self.scoring_weights = {
            "business_relevance": 0.3,      # Наскільки релевантно для бізнесу
            "implementation_ease": 0.2,     # Легкість впровадження  
            "cost_accessibility": 0.2,      # Доступність за вартістю
            "practical_impact": 0.15,       # Практичний вплив на бізнес
            "regional_relevance": 0.1,      # Релевантність для регіону
            "trend_importance": 0.05        # Важливість тренду
        }
        
        logger.info("🎯 AudienceAnalyzer ініціалізовано для МСБ аудиторії")

    def analyze_article_relevance(self, raw_article: RawArticle) -> RelevanceAnalysis:
        """
        Аналізує релевантність статті для МСБ аудиторії
        
        Args:
            raw_article: Сира стаття для аналізу
            
        Returns:
            RelevanceAnalysis з детальною оцінкою
        """
        logger.info(f"🔍 Аналіз релевантності: {raw_article.title[:50]}...")
        
        try:
            # Підготовлюємо контент для аналізу
            content_for_analysis = f"""
            Title: {raw_article.title}
            Summary: {raw_article.summary or raw_article.content[:500]}
            Source: {raw_article.source.name}
            Category: {raw_article.source.category}
            """.strip()
            
            # AI промпт для аналізу релевантності
            analysis_prompt = self._build_analysis_prompt(content_for_analysis)
            
            # Викликаємо AI для аналізу
            ai_response = self._call_ai_model(analysis_prompt, max_tokens=800)
            
            # Парсимо відповідь AI
            analysis_data = self._parse_ai_analysis(ai_response)
            
            # Розраховуємо фінальний скор
            final_score = self._calculate_final_relevance_score(analysis_data)
            
            # Створюємо результат аналізу
            analysis = RelevanceAnalysis(
                article_id=raw_article.id,
                title=raw_article.title,
                relevance_score=final_score,
                category_match=analysis_data.get('category_match', 'general'),
                target_audience=analysis_data.get('target_audience', 'general'),
                business_impact=analysis_data.get('business_impact', 'medium'),
                implementation_complexity=analysis_data.get('implementation_complexity', 'medium'),
                cost_implications=analysis_data.get('cost_implications', 'medium-cost'),
                key_benefits=analysis_data.get('key_benefits', []),
                potential_concerns=analysis_data.get('potential_concerns', []),
                confidence_level=analysis_data.get('confidence_level', 0.7),
                analysis_reasoning=analysis_data.get('reasoning', '')
            )
            
            logger.info(f"✅ Аналіз завершено: скор {final_score}/10, категорія {analysis.category_match}")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Помилка аналізу релевантності: {e}")
            
            # Фолбек аналіз без AI
            return self._create_fallback_analysis(raw_article)

    def get_daily_top_articles(self, date: Optional[datetime.date] = None, limit: int = 5) -> List[Tuple[RawArticle, RelevanceAnalysis]]:
        """
        Отримує топ статті за день на основі релевантності для МСБ
        
        Args:
            date: Дата для аналізу (за замовчанням сьогодні)
            limit: Кількість статей для повернення
            
        Returns:
            Список кортежів (RawArticle, RelevanceAnalysis) відсортованих за релевантністю
        """
        if not date:
            date = timezone.now().date()
        
        logger.info(f"📊 Пошук топ-{limit} статей за {date}")
        
        # Отримуємо необроблені статті за день
        daily_articles = RawArticle.objects.filter(
            fetched_at__date=date,
            is_processed=False,
            is_duplicate=False
        ).select_related('source').order_by('-published_at')
        
        if not daily_articles.exists():
            logger.warning(f"⚠️ Немає статей за {date}")
            return []
        
        logger.info(f"📄 Знайдено {daily_articles.count()} статей для аналізу")
        
        # Аналізуємо кожну статтю
        analyzed_articles = []
        
        for article in daily_articles[:20]:  # Обмежуємо до 20 для швидкості
            try:
                analysis = self.analyze_article_relevance(article)
                analyzed_articles.append((article, analysis))
                
                logger.debug(f"📝 {article.title[:30]}... → скор {analysis.relevance_score}")
                
            except Exception as e:
                logger.error(f"❌ Помилка аналізу статті {article.id}: {e}")
                continue
        
        # Сортуємо за релевантністю (найвищий скор першим)
        analyzed_articles.sort(key=lambda x: x[1].relevance_score, reverse=True)
        
        # Повертаємо топ статті
        top_articles = analyzed_articles[:limit]
        
        logger.info(f"🎯 Вибрано топ-{len(top_articles)} статей:")
        for i, (article, analysis) in enumerate(top_articles, 1):
            logger.info(f"   {i}. [{analysis.relevance_score}/10] {article.title[:60]}...")
        
        return top_articles

    def _build_analysis_prompt(self, content: str) -> str:
        """Створює AI промпт для аналізу релевантності"""
        
        prompt = f"""
        Analyze this tech article for relevance to small-medium business (SMB) audience.

        ARTICLE CONTENT:
        {content}

        TARGET AUDIENCE PROFILE:
        - Business size: {self.audience_profile['business_size']}
        - Budget: {self.audience_profile['budget_range']}
        - Pain points: {', '.join(self.audience_profile['pain_points'][:5])}
        - Interests: {', '.join(self.audience_profile['interests'][:5])}
        - Industries: {', '.join(self.audience_profile['industries'][:4])}
        - Regions: Ukraine, Poland, UK, EU

        ANALYSIS CRITERIA:
        1. Business Relevance (1-10): How relevant is this for SMB operations?
        2. Implementation Ease (easy/medium/hard): How difficult to implement?
        3. Cost Accessibility (low-cost/medium-cost/high-cost): Affordable for SMB?
        4. Business Impact (high/medium/low): Potential impact on business results?
        5. Regional Relevance (ukraine/poland/uk/general): Most relevant region?

        OUTPUT FORMAT (JSON only, no additional text):
        {{
            "relevance_score": 7,
            "category_match": "automation",
            "target_audience": "ukraine", 
            "business_impact": "high",
            "implementation_complexity": "easy",
            "cost_implications": "low-cost",
            "key_benefits": ["saves time", "reduces costs", "improves efficiency"],
            "potential_concerns": ["requires training", "initial setup time"],
            "confidence_level": 0.8,
            "reasoning": "This article discusses affordable automation tools perfect for SMB with clear ROI and easy implementation."
        }}

        Respond with ONLY the JSON object, no additional text.
        """
        
        return prompt

    def _parse_ai_analysis(self, ai_response: str) -> Dict:
        """Парсить відповідь AI у структуровані дані"""
        try:
            # Очищаємо відповідь від markdown блоків
            cleaned_response = ai_response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            
            cleaned_response = cleaned_response.strip()
            
            # Парсимо JSON
            analysis_data = json.loads(cleaned_response)
            
            # Валідуємо та нормалізуємо дані
            analysis_data['relevance_score'] = max(1, min(10, int(analysis_data.get('relevance_score', 5))))
            analysis_data['confidence_level'] = max(0.0, min(1.0, float(analysis_data.get('confidence_level', 0.7))))
            
            # Забезпечуємо що списки існують
            analysis_data['key_benefits'] = analysis_data.get('key_benefits', [])[:5]  # Максимум 5
            analysis_data['potential_concerns'] = analysis_data.get('potential_concerns', [])[:3]  # Максимум 3
            
            return analysis_data
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"⚠️ Помилка парсингу AI відповіді: {e}")
            logger.debug(f"AI відповідь: {ai_response}")
            
            # Повертаємо дефолтні значення
            return {
                'relevance_score': 5,
                'category_match': 'general',
                'target_audience': 'general',
                'business_impact': 'medium',
                'implementation_complexity': 'medium',
                'cost_implications': 'medium-cost',
                'key_benefits': ['potential business value'],
                'potential_concerns': ['requires evaluation'],
                'confidence_level': 0.5,
                'reasoning': 'AI analysis failed, using default scoring'
            }

    def _calculate_final_relevance_score(self, analysis_data: Dict) -> int:
        """Розраховує фінальний скор релевантності з урахуванням всіх факторів"""
        
        base_score = analysis_data.get('relevance_score', 5)
        
        # Бонуси та штрафи
        adjustments = 0
        
        # Бонус за легке впровадження
        if analysis_data.get('implementation_complexity') == 'easy':
            adjustments += 1
        elif analysis_data.get('implementation_complexity') == 'hard':
            adjustments -= 1
        
        # Бонус за низьку вартість
        if analysis_data.get('cost_implications') == 'low-cost':
            adjustments += 1
        elif analysis_data.get('cost_implications') == 'high-cost':
            adjustments -= 1
        
        # Бонус за високий бізнес-вплив
        if analysis_data.get('business_impact') == 'high':
            adjustments += 1
        elif analysis_data.get('business_impact') == 'low':
            adjustments -= 1
        
        # Бонус за регіональну релевантність
        if analysis_data.get('target_audience') in ['ukraine', 'poland', 'uk']:
            adjustments += 0.5
        
        # Штраф за низьку впевненість AI
        confidence = analysis_data.get('confidence_level', 0.7)
        if confidence < 0.6:
            adjustments -= 1
        
        # Обчислюємо фінальний скор
        final_score = base_score + adjustments
        
        # Обмежуємо до діапазону 1-10
        return max(1, min(10, round(final_score)))

    def _create_fallback_analysis(self, raw_article: RawArticle) -> RelevanceAnalysis:
        """Створює фолбек аналіз якщо AI недоступний"""
        
        # Простий аналіз на основі ключових слів
        title_lower = raw_article.title.lower()
        content_lower = (raw_article.summary or raw_article.content or '').lower()
        
        # Ключові слова для МСБ
        smb_keywords = [
            'automation', 'crm', 'small business', 'startup', 'entrepreneur',
            'productivity', 'efficiency', 'cost-effective', 'affordable',
            'chatbot', 'ai tool', 'business tool', 'workflow'
        ]
        
        # Рахуємо співпадіння
        matches = sum(1 for keyword in smb_keywords if keyword in title_lower or keyword in content_lower)
        
        # Базовий скор на основі співпадінь
        base_score = min(10, max(3, matches + 3))
        
        # Категорія на основі джерела
        category_map = {
            'ai': 'automation',
            'automation': 'automation', 
            'crm': 'crm',
            'chatbots': 'chatbots',
            'ecommerce': 'ecommerce'
        }
        
        category = category_map.get(raw_article.source.category, 'general')
        
        return RelevanceAnalysis(
            article_id=raw_article.id,
            title=raw_article.title,
            relevance_score=base_score,
            category_match=category,
            target_audience='general',
            business_impact='medium',
            implementation_complexity='medium',
            cost_implications='medium-cost',
            key_benefits=['potential business value'],
            potential_concerns=['requires evaluation'],
            confidence_level=0.6,
            analysis_reasoning='Fallback analysis based on keyword matching'
        )

    def get_analysis_statistics(self) -> Dict:
        """Повертає статистику роботи аналізатора"""
        return {
            'audience_profile': self.audience_profile,
            'scoring_weights': self.scoring_weights,
            'total_analyzed': getattr(self, '_total_analyzed', 0),
            'avg_relevance_score': getattr(self, '_avg_score', 0)
        }