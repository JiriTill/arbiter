"""
Service for calculating API costs.
"""

# OpenAI pricing (as of 2024)
# Rates per 1M tokens
PRICING = {
    'gpt-4o-mini': {'input': 0.15, 'output': 0.60},
    'text-embedding-3-small': {'input': 0.02, 'output': 0}
}

def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost in USD for a given model and token usage."""
    if model not in PRICING:
        return 0.0
        
    rates = PRICING[model]
    cost = (input_tokens * rates['input'] + output_tokens * rates['output']) / 1_000_000
    return cost
