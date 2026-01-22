"""
Explain recommendations.
"""


def explain_recommendation(user_id: str, item_id: str) -> str:
    return f"Recommended because you liked similar items to {item_id} or it aligns with your profile preferences."
