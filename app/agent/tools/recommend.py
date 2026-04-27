"""Recommendation lookup."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.agent.tools._base import Tool, ToolError, ToolExecutionContext, ToolResult


CategoryT = Literal[
    "generic", "clothes", "movies", "news", "courses", "cars", "electronics", "places"
]


class RecommendInput(BaseModel):
    category: CategoryT = Field(
        "generic", description="Recommendation domain. Use 'generic' if unsure."
    )
    query: str = Field("", description="Free-text query or context (brand, mood, season, etc.).")
    user_id: str = Field("anon", description="User identifier for personalisation.")
    top_k: int = Field(5, ge=1, le=20, description="How many items to return.")


class RecommendOutput(BaseModel):
    items: list[dict[str, Any]]
    category: CategoryT


class RecommendTool(Tool):
    name = "recommend"
    description = (
        "Recommend items from a catalogue. Choose the most specific category "
        "available (clothes, movies, news, courses, cars, electronics, places); "
        "if no category fits, use 'generic' for the unified recommender."
    )
    input_schema = RecommendInput
    output_schema = RecommendOutput

    def _run(self, ctx: ToolExecutionContext, args: RecommendInput) -> ToolResult:
        items: list[dict[str, Any]] = []
        try:
            if args.category == "clothes":
                from app.streamlit_chatbot.handlers.clothes import recommend_clothes

                items = recommend_clothes(age=None, query=args.query, top_k=args.top_k) or []
            elif args.category == "movies":
                from app.streamlit_chatbot.handlers.movies import recommend_movies

                items = recommend_movies(query=args.query, top_n=args.top_k) or []
            elif args.category == "news":
                from app.streamlit_chatbot.handlers.news import recommend_news

                items = recommend_news(query=args.query, top_n=args.top_k) or []
            elif args.category == "courses":
                from app.streamlit_chatbot.handlers.courses import recommend_courses

                items = recommend_courses(query=args.query, limit=args.top_k) or []
            elif args.category == "cars":
                from app.streamlit_chatbot.handlers.cars import recommend_cars

                items = recommend_cars(args.query) or []
            elif args.category == "electronics":
                from app.streamlit_chatbot.handlers.electronics import recommend_electronics

                domain = "phones"
                q = args.query.lower()
                if "laptop" in q:
                    domain = "laptops"
                elif "headphone" in q or "earbud" in q:
                    domain = "headphones"
                items = recommend_electronics(domain=domain, query=args.query, limit=args.top_k) or []
            elif args.category == "places":
                from app.streamlit_chatbot.handlers.places import recommend_places

                items = recommend_places(query=args.query, places_api_key=None) or []
            else:
                from app.models.recommender.predict import recommend as generic_recommend

                items = generic_recommend(user_id=args.user_id, top_k=args.top_k) or []
        except Exception as exc:
            raise ToolError(f"recommend({args.category}) failed: {exc}") from exc

        out = RecommendOutput(items=items[: args.top_k], category=args.category)
        summary = f"category={args.category} items={len(out.items)}"
        return ToolResult(summary=summary, data=out.model_dump())
