"""Configuration settings for the SPY Dashboard"""
import pytz

# Time zones
MIAMI_TZ = pytz.timezone('US/Eastern')

# Trading windows
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 30
MARKET_CLOSE_HOUR = 16
PRIME_WINDOW_END_HOUR = 11
DANGER_ZONE_START_HOUR = 14
DANGER_ZONE_START_MINUTE = 30

# Analysis thresholds
MOMENTUM_THRESHOLDS = {
    'strong_divergence': 0.3,
    'moderate_divergence': 0.2,
    'strong_volume': 1.3,
    'moderate_volume': 1.1
}

DECISION_THRESHOLDS = {
    'strong_signal': 7.0,  # Lowered from 8
    'moderate_signal': 5.0  # Lowered from 6
}

# Sector symbols and weights
SECTOR_SYMBOLS = ['XLK', 'XLF', 'XLV', 'XLY', 'XLI', 'XLP', 'XLE', 'XLU', 'XLRE']
SECTOR_WEIGHTS = {
    'XLK': 0.25, 'XLF': 0.15, 'XLV': 0.15, 'XLY': 0.12, 'XLI': 0.10,
    'XLP': 0.08, 'XLE': 0.05, 'XLU': 0.05, 'XLRE': 0.05
}

SECTOR_NAMES = {
    'XLK': 'Technology', 'XLF': 'Financials', 'XLV': 'Healthcare',
    'XLY': 'Consumer Discretionary', 'XLI': 'Industrials', 'XLP': 'Consumer Staples',
    'XLE': 'Energy', 'XLU': 'Utilities', 'XLRE': 'Real Estate'
}


