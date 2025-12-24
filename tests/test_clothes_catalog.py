from app.streamlit_chatbot.handlers.clothes import recommend_clothes


def test_recommend_clothes_includes_brand_and_title():
    items = recommend_clothes(
        age=None, query="Recommend casual sneakers", preferred_tags=["sneakers", "casual"], top_k=3
    )
    assert items
    assert "title" in items[0]
    assert "brand" in items[0]
    assert items[0]["brand"]


def test_recommend_clothes_works_without_preferred_tags():
    items = recommend_clothes(age=25, query="clothes", preferred_tags=None, top_k=2)
    assert items
