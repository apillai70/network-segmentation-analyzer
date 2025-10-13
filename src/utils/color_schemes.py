"""
Color schemes for visual distinction between actual and predicted flows
"""

# Actual (Current State) - Solid, vibrant colors
ACTUAL_COLORS = {
    'WEB_TIER': '#4CAF50',           # Green - solid
    'APP_TIER': '#2196F3',           # Blue - solid
    'DATA_TIER': '#FF9800',          # Orange - solid
    'MESSAGING_TIER': '#9C27B0',     # Purple - solid
    'CACHE_TIER': '#00BCD4',         # Cyan - solid
    'INFRASTRUCTURE': '#F44336',     # Red - solid
    'MANAGEMENT': '#FFEB3B',         # Yellow - solid
    'UNASSIGNED': '#607D8B',         # Gray - solid
    
    # Flow links
    'actual_flow': '#4CAF50',        # Green - solid
    'actual_flow_opacity': 0.8
}

# Predicted (Future State) - Lighter, semi-transparent
PREDICTED_COLORS = {
    'WEB_TIER': '#81C784',           # Light Green - 40% lighter
    'APP_TIER': '#64B5F6',           # Light Blue - 40% lighter
    'DATA_TIER': '#FFB74D',          # Light Orange - 40% lighter
    'MESSAGING_TIER': '#BA68C8',     # Light Purple - 40% lighter
    'CACHE_TIER': '#4DD0E1',         # Light Cyan - 40% lighter
    'INFRASTRUCTURE': '#E57373',     # Light Red - 40% lighter
    'MANAGEMENT': '#FFF176',         # Light Yellow - 40% lighter
    'UNASSIGNED': '#90A4AE',         # Light Gray - 40% lighter
    
    # Predicted flow links
    'predicted_flow': '#81C784',     # Light Green
    'predicted_flow_opacity': 0.4,   # Semi-transparent
    
    # Markov prediction confidence levels
    'high_confidence': '#81C784',    # Light Green (>70%)
    'medium_confidence': '#FFB74D',  # Light Orange (40-70%)
    'low_confidence': '#E57373'      # Light Red (<40%)
}

# Migration indicators
MIGRATION_COLORS = {
    'needs_migration': '#FF9800',    # Orange
    'migration_complete': '#4CAF50', # Green
    'migration_pending': '#FFC107',  # Amber
    'migration_blocked': '#F44336'   # Red
}

# Legend entries
LEGEND_CONFIG = {
    'actual': {
        'label': 'Current State (Actual)',
        'style': 'solid',
        'opacity': 1.0
    },
    'predicted': {
        'label': 'Future State (Predicted)',
        'style': 'dashed',
        'opacity': 0.6
    },
    'markov_high': {
        'label': 'Markov Prediction (High Confidence >70%)',
        'style': 'dotted',
        'opacity': 0.8
    },
    'markov_medium': {
        'label': 'Markov Prediction (Medium 40-70%)',
        'style': 'dotted',
        'opacity': 0.5
    },
    'markov_low': {
        'label': 'Markov Prediction (Low <40%)',
        'style': 'dotted',
        'opacity': 0.3
    }
}