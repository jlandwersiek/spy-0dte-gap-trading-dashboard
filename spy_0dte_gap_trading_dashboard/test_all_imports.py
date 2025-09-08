# test_all_imports.py
print("Testing imports...")

try:
    # Test config
    from config import MIAMI_TZ, MOMENTUM_THRESHOLDS
    print("✅ Config imports work")
    
    # Test API clients
    from api.tradier_client import TradierAPI
    from api.yahoo_client import get_cached_yahoo_data
    print("✅ API imports work")
    
    # Test analyzers
    from analyzers.gap_analyzer import GapAnalyzer
    from analyzers.sector_analyzer import SectorAnalyzer
    from analyzers.internals_analyzer import InternalsAnalyzer
    from analyzers.technical_analyzer import TechnicalAnalyzer
    from analyzers.trend_analyzer import TrendAnalyzer
    print("✅ Analyzer imports work")
    
    # Test signals
    from signals.entry_signals import EntrySignalGenerator
    from signals.exit_signals import ExitSignalManager
    print("✅ Signal imports work")
    
    # Test UI
    from ui.components import display_data_sources_info
    from ui.breakdown_display import display_points_breakdown_ui
    from ui.exit_dashboard import display_exit_signals_ui
    print("✅ UI imports work")
    
    print("🎉 ALL IMPORTS SUCCESSFUL!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Check file paths and spelling")
