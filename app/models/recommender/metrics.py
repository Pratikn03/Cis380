"""
Recommender System Metrics Module

Provides evaluation metrics for recommendation systems:
- NDCG (Normalized Discounted Cumulative Gain)
- MAP (Mean Average Precision)
- MRR (Mean Reciprocal Rank)
- Hit Rate
- Coverage
- Diversity
- Novelty
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Union
import logging

logger = logging.getLogger(__name__)


@dataclass
class Recommendation:
    """A single recommendation item."""
    item_id: str
    score: float
    rank: int
    metadata: Dict = field(default_factory=dict)


@dataclass
class UserRecommendations:
    """Recommendations for a single user."""
    user_id: str
    recommendations: List[Recommendation]
    ground_truth: List[str]  # Relevant item IDs
    
    @property
    def recommended_ids(self) -> List[str]:
        return [r.item_id for r in self.recommendations]


@dataclass
class RecommenderMetrics:
    """Collection of recommender metrics."""
    ndcg_at_k: Dict[int, float]
    map_at_k: Dict[int, float]
    mrr: float
    hit_rate_at_k: Dict[int, float]
    precision_at_k: Dict[int, float]
    recall_at_k: Dict[int, float]
    coverage: float
    diversity: float
    novelty: float
    num_users: int
    
    def to_dict(self) -> Dict:
        return {
            "ndcg": self.ndcg_at_k,
            "map": self.map_at_k,
            "mrr": self.mrr,
            "hit_rate": self.hit_rate_at_k,
            "precision": self.precision_at_k,
            "recall": self.recall_at_k,
            "coverage": self.coverage,
            "diversity": self.diversity,
            "novelty": self.novelty,
            "num_users": self.num_users,
        }
    
    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            "=" * 50,
            "Recommender System Evaluation Report",
            "=" * 50,
            f"Number of users: {self.num_users}",
            f"MRR: {self.mrr:.4f}",
            f"Coverage: {self.coverage:.4f}",
            f"Diversity: {self.diversity:.4f}",
            f"Novelty: {self.novelty:.4f}",
            "",
            "NDCG@K:",
        ]
        for k, v in sorted(self.ndcg_at_k.items()):
            lines.append(f"  @{k}: {v:.4f}")
        
        lines.append("\nHit Rate@K:")
        for k, v in sorted(self.hit_rate_at_k.items()):
            lines.append(f"  @{k}: {v:.4f}")
        
        lines.append("\nPrecision@K:")
        for k, v in sorted(self.precision_at_k.items()):
            lines.append(f"  @{k}: {v:.4f}")
        
        lines.append("=" * 50)
        return "\n".join(lines)


class RankingMetrics:
    """
    Calculates ranking metrics for recommender evaluation.
    
    Usage:
        evaluator = RankingMetrics(k_values=[5, 10, 20])
        
        # Add user results
        evaluator.add_user(
            user_id="u1",
            recommended_ids=["i1", "i3", "i5", "i7", "i9"],
            relevant_ids=["i1", "i2", "i5"],
        )
        
        # Get metrics
        metrics = evaluator.evaluate()
        print(metrics.summary())
    """
    
    def __init__(
        self,
        k_values: List[int] = None,
        catalog_size: int = 0,
        item_popularity: Optional[Dict[str, int]] = None,
    ):
        self.k_values = k_values or [5, 10, 20]
        self.catalog_size = catalog_size
        self.item_popularity = item_popularity or {}
        self.results: List[UserRecommendations] = []
        self._all_recommended: Set[str] = set()
    
    def add_user(
        self,
        user_id: str,
        recommended_ids: List[str],
        relevant_ids: List[str],
        scores: Optional[List[float]] = None,
    ) -> None:
        """Add recommendations for a user."""
        if scores is None:
            scores = [1.0 / (i + 1) for i in range(len(recommended_ids))]
        
        recommendations = [
            Recommendation(
                item_id=item_id,
                score=scores[i] if i < len(scores) else 0.0,
                rank=i + 1,
            )
            for i, item_id in enumerate(recommended_ids)
        ]
        
        self.results.append(UserRecommendations(
            user_id=user_id,
            recommendations=recommendations,
            ground_truth=relevant_ids,
        ))
        
        self._all_recommended.update(recommended_ids)
    
    def clear(self) -> None:
        """Clear all results."""
        self.results = []
        self._all_recommended = set()
    
    # ========================================================================
    # Individual Metrics
    # ========================================================================
    
    def dcg_at_k(self, result: UserRecommendations, k: int) -> float:
        """
        Calculate Discounted Cumulative Gain at K.
        
        DCG@K = Σ (2^rel_i - 1) / log2(i + 1)
        
        Using binary relevance (rel = 1 if relevant, 0 otherwise).
        """
        relevant_set = set(result.ground_truth)
        dcg = 0.0
        
        for i, item_id in enumerate(result.recommended_ids[:k]):
            rel = 1.0 if item_id in relevant_set else 0.0
            # Using gain = 2^rel - 1 = 1 for binary relevance
            dcg += rel / math.log2(i + 2)  # i+2 because log2(1) = 0
        
        return dcg
    
    def idcg_at_k(self, result: UserRecommendations, k: int) -> float:
        """Calculate Ideal DCG at K."""
        num_relevant = min(len(result.ground_truth), k)
        idcg = 0.0
        
        for i in range(num_relevant):
            idcg += 1.0 / math.log2(i + 2)
        
        return idcg
    
    def ndcg_at_k(self, result: UserRecommendations, k: int) -> float:
        """
        Calculate Normalized DCG at K.
        
        NDCG@K = DCG@K / IDCG@K
        """
        idcg = self.idcg_at_k(result, k)
        if idcg == 0:
            return 0.0
        return self.dcg_at_k(result, k) / idcg
    
    def precision_at_k(self, result: UserRecommendations, k: int) -> float:
        """
        Calculate Precision at K.
        
        Precision@K = |relevant ∩ recommended@K| / K
        """
        recommended_at_k = result.recommended_ids[:k]
        if not recommended_at_k:
            return 0.0
        
        relevant_set = set(result.ground_truth)
        hits = sum(1 for item_id in recommended_at_k if item_id in relevant_set)
        return hits / k
    
    def recall_at_k(self, result: UserRecommendations, k: int) -> float:
        """
        Calculate Recall at K.
        
        Recall@K = |relevant ∩ recommended@K| / |relevant|
        """
        if not result.ground_truth:
            return 0.0
        
        recommended_at_k = set(result.recommended_ids[:k])
        relevant_set = set(result.ground_truth)
        hits = len(recommended_at_k & relevant_set)
        return hits / len(relevant_set)
    
    def hit_at_k(self, result: UserRecommendations, k: int) -> bool:
        """Check if any relevant item is in top K."""
        recommended_at_k = set(result.recommended_ids[:k])
        relevant_set = set(result.ground_truth)
        return bool(recommended_at_k & relevant_set)
    
    def reciprocal_rank(self, result: UserRecommendations) -> float:
        """Calculate Reciprocal Rank."""
        relevant_set = set(result.ground_truth)
        for i, item_id in enumerate(result.recommended_ids):
            if item_id in relevant_set:
                return 1.0 / (i + 1)
        return 0.0
    
    def average_precision(self, result: UserRecommendations) -> float:
        """Calculate Average Precision."""
        if not result.ground_truth:
            return 0.0
        
        relevant_set = set(result.ground_truth)
        num_relevant = 0
        sum_precision = 0.0
        
        for i, item_id in enumerate(result.recommended_ids):
            if item_id in relevant_set:
                num_relevant += 1
                precision_at_i = num_relevant / (i + 1)
                sum_precision += precision_at_i
        
        return sum_precision / len(relevant_set)
    
    # ========================================================================
    # Beyond-Accuracy Metrics
    # ========================================================================
    
    def coverage(self) -> float:
        """
        Calculate catalog coverage.
        
        Coverage = |unique recommended items| / |catalog|
        """
        if self.catalog_size == 0:
            return 0.0
        return len(self._all_recommended) / self.catalog_size
    
    def diversity(self) -> float:
        """
        Calculate intra-list diversity (average pairwise distance).
        
        For simplicity, using Jaccard distance based on co-occurrence.
        """
        if len(self.results) < 2:
            return 0.0
        
        total_diversity = 0.0
        count = 0
        
        for result in self.results:
            recs = result.recommended_ids
            if len(recs) < 2:
                continue
            
            # Pairwise uniqueness
            unique_pairs = 0
            total_pairs = 0
            
            for i in range(len(recs)):
                for j in range(i + 1, len(recs)):
                    total_pairs += 1
                    if recs[i] != recs[j]:
                        unique_pairs += 1
            
            if total_pairs > 0:
                total_diversity += unique_pairs / total_pairs
                count += 1
        
        return total_diversity / count if count > 0 else 0.0
    
    def novelty(self) -> float:
        """
        Calculate novelty (recommending less popular items).
        
        Novelty = (1/|U|) * Σ_u (1/|L_u|) * Σ_i∈L_u -log2(pop(i))
        
        Higher novelty = recommending less popular items.
        """
        if not self.item_popularity:
            return 0.0
        
        total_pop = sum(self.item_popularity.values())
        if total_pop == 0:
            return 0.0
        
        total_novelty = 0.0
        count = 0
        
        for result in self.results:
            if not result.recommended_ids:
                continue
            
            user_novelty = 0.0
            for item_id in result.recommended_ids:
                pop = self.item_popularity.get(item_id, 1)
                prob = pop / total_pop
                if prob > 0:
                    user_novelty += -math.log2(prob)
            
            total_novelty += user_novelty / len(result.recommended_ids)
            count += 1
        
        return total_novelty / count if count > 0 else 0.0
    
    # ========================================================================
    # Aggregate Evaluation
    # ========================================================================
    
    def evaluate(self) -> RecommenderMetrics:
        """Run full evaluation."""
        if not self.results:
            logger.warning("No results to evaluate")
            return RecommenderMetrics(
                ndcg_at_k={k: 0.0 for k in self.k_values},
                map_at_k={k: 0.0 for k in self.k_values},
                mrr=0.0,
                hit_rate_at_k={k: 0.0 for k in self.k_values},
                precision_at_k={k: 0.0 for k in self.k_values},
                recall_at_k={k: 0.0 for k in self.k_values},
                coverage=0.0,
                diversity=0.0,
                novelty=0.0,
                num_users=0,
            )
        
        n = len(self.results)
        
        # Ranking metrics at different K
        ndcg_at_k = {}
        hit_rate_at_k = {}
        precision_at_k = {}
        recall_at_k = {}
        map_at_k = {}
        
        for k in self.k_values:
            ndcg_at_k[k] = sum(self.ndcg_at_k(r, k) for r in self.results) / n
            hit_rate_at_k[k] = sum(1 for r in self.results if self.hit_at_k(r, k)) / n
            precision_at_k[k] = sum(self.precision_at_k(r, k) for r in self.results) / n
            recall_at_k[k] = sum(self.recall_at_k(r, k) for r in self.results) / n
            map_at_k[k] = sum(self.average_precision(r) for r in self.results) / n
        
        # Global metrics
        mrr = sum(self.reciprocal_rank(r) for r in self.results) / n
        
        return RecommenderMetrics(
            ndcg_at_k=ndcg_at_k,
            map_at_k=map_at_k,
            mrr=mrr,
            hit_rate_at_k=hit_rate_at_k,
            precision_at_k=precision_at_k,
            recall_at_k=recall_at_k,
            coverage=self.coverage(),
            diversity=self.diversity(),
            novelty=self.novelty(),
            num_users=n,
        )


class RecommenderEvaluator:
    """
    High-level evaluator for recommender systems.
    
    Supports batch evaluation and comparison.
    """
    
    def __init__(
        self,
        k_values: List[int] = None,
        catalog: Optional[List[str]] = None,
        item_popularity: Optional[Dict[str, int]] = None,
    ):
        self.k_values = k_values or [5, 10, 20]
        self.catalog = catalog or []
        self.item_popularity = item_popularity or {}
    
    def evaluate(
        self,
        recommendations: Dict[str, List[str]],  # user_id -> recommended items
        ground_truth: Dict[str, List[str]],     # user_id -> relevant items
        scores: Optional[Dict[str, List[float]]] = None,
    ) -> RecommenderMetrics:
        """
        Evaluate recommendations against ground truth.
        
        Args:
            recommendations: Dict mapping user_id to recommended item list
            ground_truth: Dict mapping user_id to relevant item list
            scores: Optional dict mapping user_id to recommendation scores
        
        Returns:
            RecommenderMetrics with all evaluation metrics
        """
        metrics = RankingMetrics(
            k_values=self.k_values,
            catalog_size=len(self.catalog),
            item_popularity=self.item_popularity,
        )
        
        for user_id, rec_items in recommendations.items():
            rel_items = ground_truth.get(user_id, [])
            user_scores = scores.get(user_id) if scores else None
            
            metrics.add_user(
                user_id=user_id,
                recommended_ids=rec_items,
                relevant_ids=rel_items,
                scores=user_scores,
            )
        
        return metrics.evaluate()
    
    def compare_models(
        self,
        model_recommendations: Dict[str, Dict[str, List[str]]],  # model -> user -> items
        ground_truth: Dict[str, List[str]],
    ) -> Dict[str, RecommenderMetrics]:
        """
        Compare multiple recommendation models.
        
        Args:
            model_recommendations: Dict mapping model name to recommendations
            ground_truth: Ground truth relevance
        
        Returns:
            Dict mapping model name to metrics
        """
        results = {}
        for model_name, recommendations in model_recommendations.items():
            results[model_name] = self.evaluate(recommendations, ground_truth)
        return results


# ============================================================================
# Convenience Functions
# ============================================================================

def calculate_ndcg(
    recommended: List[str],
    relevant: List[str],
    k: int,
) -> float:
    """Calculate NDCG@K for a single user."""
    metrics = RankingMetrics(k_values=[k])
    metrics.add_user("u", recommended, relevant)
    return metrics.ndcg_at_k(metrics.results[0], k)


def calculate_mrr(
    recommendations: Dict[str, List[str]],
    ground_truth: Dict[str, List[str]],
) -> float:
    """Calculate MRR across all users."""
    metrics = RankingMetrics()
    for user_id, rec_items in recommendations.items():
        rel_items = ground_truth.get(user_id, [])
        metrics.add_user(user_id, rec_items, rel_items)
    
    return sum(metrics.reciprocal_rank(r) for r in metrics.results) / len(metrics.results)


def calculate_hit_rate(
    recommendations: Dict[str, List[str]],
    ground_truth: Dict[str, List[str]],
    k: int,
) -> float:
    """Calculate Hit Rate@K across all users."""
    metrics = RankingMetrics(k_values=[k])
    for user_id, rec_items in recommendations.items():
        rel_items = ground_truth.get(user_id, [])
        metrics.add_user(user_id, rec_items, rel_items)
    
    report = metrics.evaluate()
    return report.hit_rate_at_k[k]


def quick_evaluate(
    recommendations: Dict[str, List[str]],
    ground_truth: Dict[str, List[str]],
    k_values: List[int] = None,
) -> Dict:
    """Quick evaluation returning dictionary of metrics."""
    evaluator = RecommenderEvaluator(k_values or [5, 10, 20])
    metrics = evaluator.evaluate(recommendations, ground_truth)
    return metrics.to_dict()
