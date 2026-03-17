import os

# API Management Toggles
API_CONFIG = {
    "EXA_ENABLED": True,
    "GUARDIAN_ENABLED": False, # Deprecated in Agent-6
    "NEWSDATA_ENABLED": False  # Deprecated in Agent-6
}

# Domains for formal news and research
NEWS_DOMAINS = [
    # Authorities
    "unodc.org",
    "polarisproject.org",
    "ctdatacollaborative.org",
    "hrw.org",
    "ijm.org",
    "ilo.org",
    "thorn.org",
    # Global News
    "reuters.com",
    "apnews.com",
    "theguardian.com",
    "bbc.com",
    "cnn.com",
    "aljazeera.com"
]

# Domains for social media monitoring
SOCIAL_DOMAINS = [
    "x.com"
]
