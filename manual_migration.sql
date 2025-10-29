-- Міграція для додавання implementation_steps полів
-- Застосувати на сервері вручну

ALTER TABLE news_processedarticle 
ADD COLUMN implementation_steps_en JSONB DEFAULT '[]'::jsonb,
ADD COLUMN implementation_steps_pl JSONB DEFAULT '[]'::jsonb,
ADD COLUMN implementation_steps_uk JSONB DEFAULT '[]'::jsonb;

-- Оновити коментарі полів (опціонально)
COMMENT ON COLUMN news_processedarticle.implementation_steps_en IS 'Кроки впровадження (EN)';
COMMENT ON COLUMN news_processedarticle.implementation_steps_pl IS 'Кроки впровадження (PL)';
COMMENT ON COLUMN news_processedarticle.implementation_steps_uk IS 'Кроки впровадження (UK)';
