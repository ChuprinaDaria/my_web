from django.conf import settings

def get_active_embedding_conf():
    provider = settings.RAG_SETTINGS.get("PROVIDER", "openai")
    models = settings.RAG_SETTINGS.get("EMBEDDING_MODELS", {})
    if provider not in models:
        raise KeyError(f"Embedding model config missing for provider '{provider}'")
    config = models[provider].copy()
    config["provider"] = provider
    return config
