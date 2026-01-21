"""
RAG Retrieval Metrics Module

Provides evaluation metrics for retrieval-augmented generation:
- Mean Reciprocal Rank (MRR)
- Recall@K
- Precision@K
- NDCG (Normalized Discounted Cumulative Gain)
- Hit Rate
- MAP (Mean Average Precision)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Represents a single retrieval result."""
    doc_id: str
    score: float
    rank: int
    text: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class QueryResult:
    """Represents results for a single query."""
    query_id: str
    query_text: str
    retrieved: List[RetrievalResult]
    relevant_ids: List[str]  # Ground truth relevant document IDs
    
    @property
    def retrieved_ids(self) -> List[str]:
        return [r.doc_id for r in self.retrieved]


@dataclass
class EvaluationReport:
    """Comprehensive evaluation report."""
    mrr: float
    recall_at_k: Dict[int, float]
    precision_at_k: Dict[int, float]
    ndcg_at_k: Dict[int, float]
    hit_rate_at_k: Dict[int, float]
    map_score: float
    num_queries: int
    avg_retrieved: float
    avg_relevant: float
    
    def to_dict(self) -> Dict:
        return {
            "mrr": self.mrr,
            "recall_at_k": self.recall_at_k,
            "precision_at_k": self.precision_at_k,
            "ndcg_at_k": self.ndcg_at_k,
            "hit_rate_at_k": self.hit_rate_at_k,
            "map": self.map_score,
            "num_queries": self.num_queries,
            "avg_retrieved": self.avg_retrieved,
            "avg_relevant": self.avg_relevant,
        }
    
    def summary(self) -> str:
        """Generate a human-readable summary."""
        lines = [
            "=" * 50,
            "RAG Retrieval Evaluation Report",
            "=" * 50,
            f"Number of queries: {self.num_queries}",
            f"Avg retrieved per query: {self.avg_retrieved:.2f}",
            f"Avg relevant per query: {self.avg_relevant:.2f}",
            "",
            f"MRR: {self.mrr:.4f}",
            f"MAP: {self.map_score:.4f}",
            "",
            "Recall@K:",
        ]
        for k, v in sorted(self.recall_at_k.items()):
            lines.append(f"  @{k}: {v:.4f}")
        
        lines.append("\nPrecision@K:")
        for k, v in sorted(self.precision_at_k.items()):
            lines.append(f"  @{k}: {v:.4f}")
        
        lines.append("\nNDCG@K:")
        for k, v in sorted(self.ndcg_at_k.items()):
            lines.append(f"  @{k}: {v:.4f}")
        
        lines.append("\nHit Rate@K:")
        for k, v in sorted(self.hit_rate_at_k.items()):
            lines.append(f"  @{k}: {v:.4f}")
        
        lines.append("=" * 50)
        return "\n".join(lines)


class RetrievalMetrics:
    """
    Calculates retrieval metrics for RAG evaluation.
    
    Usage:
        metrics = RetrievalMetrics(k_values=[1, 3, 5, 10])
        
        # Add query results
        metrics.add_result(
            query_id="q1",
            retrieved_ids=["d1", "d3", "d5"],
            relevant_ids=["d1", "d2", "d5"],
        )
        
        # Get evaluation report
        report = metrics.evaluate()
        print(report.summary())
    """
    
    def __init__(self, k_values: List[int] = None):
        self.k_values = k_values or [1, 3, 5, 10, 20]
        self.results: List[QueryResult] = []
    
    def add_result(
        self,
        query_id: str,
        retrieved_ids: List[str],
        relevant_ids: List[str],
        query_text: str = "",
        scores: Optional[List[float]] = None,
    ) -> None:
        """Add a query result for evaluation."""
        if scores is None:
            scores = [1.0 / (i + 1) for i in range(len(retrieved_ids))]
        
        retrieved = [
            RetrievalResult(
                doc_id=doc_id,
                score=scores[i] if i < len(scores) else 0.0,
                rank=i + 1,
            )
            for i, doc_id in enumerate(retrieved_ids)
        ]
        
        self.results.append(QueryResult(
            query_id=query_id,
            query_text=query_text,
            retrieved=retrieved,
            relevant_ids=relevant_ids,
        ))
    
    def clear(self) -> None:
        """Clear all results."""
        self.results = []
    
    # ========================================================================
    # Individual Metrics
    # ========================================================================
    
    def reciprocal_rank(self, result: QueryResult) -> float:
        """
        Calculate Reciprocal Rank for a single query.
        
        RR = 1 / rank of first relevant document
        """
        for i, doc_id in enumerate(result.retrieved_ids):
            if doc_id in result.relevant_ids:
                return 1.0 / (i + 1)
        return 0.0
    
    def mrr(self) -> float:
        """
        Calculate Mean Reciprocal Rank across all queries.
        
        MRR = (1/|Q|) * Σ RR(q)
        """
        if not self.results:
            return 0.0
        
        total_rr = sum(self.reciprocal_rank(r) for r in self.results)
        return total_rr / len(self.results)
    
    def recall_at_k(self, result: QueryResult, k: int) -> float:
        """
        Calculate Recall@K for a single query.
        
        Recall@K = |relevant ∩ retrieved@K| / |relevant|
        """
        if not result.relevant_ids:
            return 0.0
        
        retrieved_at_k = set(result.retrieved_ids[:k])
        relevant_set = set(result.relevant_ids)
        hits = len(retrieved_at_k & relevant_set)
        return hits / len(relevant_set)
    
    def precision_at_k(self, result: QueryResult, k: int) -> float:
        """
        Calculate Precision@K for a single query.
        
        Precision@K = |relevant ∩ retrieved@K| / K
        """
        retrieved_at_k = result.retrieved_ids[:k]
        if not retrieved_at_k:
            return 0.0
        
        relevant_set = set(result.relevant_ids)
        hits = sum(1 for doc_id in retrieved_at_k if doc_id in relevant_set)
        return hits / len(retrieved_at_k)
    
    def hit_at_k(self, result: QueryResult, k: int) -> bool:
        """
        Check if there's at least one relevant document in top-K.
        
        Hit@K = 1 if any relevant doc in top K, else 0
        """
        retrieved_at_k = set(result.retrieved_ids[:k])
        relevant_set = set(result.relevant_ids)
        return bool(retrieved_at_k & relevant_set)
    
    def dcg_at_k(self, result: QueryResult, k: int) -> float:
        """
        Calculate Discounted Cumulative Gain at K.
        
        DCG@K = Σ (rel_i / log2(i + 1))
        """
        relevant_set = set(result.relevant_ids)
        dcg = 0.0
        
        for i, doc_id in enumerate(result.retrieved_ids[:k]):
            rel = 1.0 if doc_id in relevant_set else 0.0
            dcg += rel / math.log2(i + 2)  # i+2 because log2(1) = 0
        
        return dcg
    
    def idcg_at_k(self, result: QueryResult, k: int) -> float:
        """
        Calculate Ideal DCG at K (best possible ranking).
        """
        # Ideal ranking: all relevant docs at the top
        num_relevant = min(len(result.relevant_ids), k)
        idcg = 0.0
        
        for i in range(num_relevant):
            idcg += 1.0 / math.log2(i + 2)
        
        return idcg
    
    def ndcg_at_k(self, result: QueryResult, k: int) -> float:
        """
        Calculate Normalized DCG at K.
        
        NDCG@K = DCG@K / IDCG@K
        """
        idcg = self.idcg_at_k(result, k)
        if idcg == 0:
            return 0.0
        
        dcg = self.dcg_at_k(result, k)
        return dcg / idcg
    
    def average_precision(self, result: QueryResult) -> float:
        """
        Calculate Average Precision for a single query.
        
        AP = (1/|relevant|) * Σ P@k * rel(k)
        """
        if not result.relevant_ids:
            return 0.0
        
        relevant_set = set(result.relevant_ids)
        num_relevant = 0
        sum_precision = 0.0
        
        for i, doc_id in enumerate(result.retrieved_ids):
            if doc_id in relevant_set:
                num_relevant += 1
                precision_at_i = num_relevant / (i + 1)
                sum_precision += precision_at_i
        
        return sum_precision / len(relevant_set) if relevant_set else 0.0
    
    def map_score(self) -> float:
        """
        Calculate Mean Average Precision across all queries.
        
        MAP = (1/|Q|) * Σ AP(q)
        """
        if not self.results:
            return 0.0
        
        total_ap = sum(self.average_precision(r) for r in self.results)
        return total_ap / len(self.results)
    
    # ========================================================================
    # Aggregate Evaluation
    # ========================================================================
    
    def evaluate(self) -> EvaluationReport:
        """
        Run full evaluation and return comprehensive report.
        """
        if not self.results:
            logger.warning("No results to evaluate")
            return EvaluationReport(
                mrr=0.0,
                recall_at_k={k: 0.0 for k in self.k_values},
                precision_at_k={k: 0.0 for k in self.k_values},
                ndcg_at_k={k: 0.0 for k in self.k_values},
                hit_rate_at_k={k: 0.0 for k in self.k_values},
                map_score=0.0,
                num_queries=0,
                avg_retrieved=0.0,
                avg_relevant=0.0,
            )
        
        n = len(self.results)
        
        # Calculate metrics for each K
        recall_at_k = {}
        precision_at_k = {}
        ndcg_at_k = {}
        hit_rate_at_k = {}
        
        for k in self.k_values:
            recall_at_k[k] = sum(self.recall_at_k(r, k) for r in self.results) / n
            precision_at_k[k] = sum(self.precision_at_k(r, k) for r in self.results) / n
            ndcg_at_k[k] = sum(self.ndcg_at_k(r, k) for r in self.results) / n
            hit_rate_at_k[k] = sum(1 for r in self.results if self.hit_at_k(r, k)) / n
        
        return EvaluationReport(
            mrr=self.mrr(),
            recall_at_k=recall_at_k,
            precision_at_k=precision_at_k,
            ndcg_at_k=ndcg_at_k,
            hit_rate_at_k=hit_rate_at_k,
            map_score=self.map_score(),
            num_queries=n,
            avg_retrieved=sum(len(r.retrieved) for r in self.results) / n,
            avg_relevant=sum(len(r.relevant_ids) for r in self.results) / n,
        )


class RAGEvaluator:
    """
    High-level RAG system evaluator.
    
    Evaluates both retrieval quality and generation quality.
    """
    
    def __init__(
        self,
        retriever_fn=None,
        k_values: List[int] = None,
    ):
        self.retriever_fn = retriever_fn
        self.metrics = RetrievalMetrics(k_values or [1, 3, 5, 10])
    
    def evaluate_retrieval(
        self,
        queries: List[str],
        ground_truth: Dict[str, List[str]],  # query -> relevant doc IDs
    ) -> EvaluationReport:
        """
        Evaluate retrieval performance on a set of queries.
        
        Args:
            queries: List of query strings
            ground_truth: Mapping from query to relevant document IDs
        
        Returns:
            EvaluationReport with all metrics
        """
        if not self.retriever_fn:
            raise ValueError("No retriever function provided")
        
        self.metrics.clear()
        
        for i, query in enumerate(queries):
            # Get retrieved documents
            try:
                results = self.retriever_fn(query)
                retrieved_ids = [r.get("id", r.get("doc_id", str(j))) 
                                for j, r in enumerate(results)]
                scores = [r.get("score", 1.0 / (j + 1)) 
                         for j, r in enumerate(results)]
            except Exception as e:
                logger.error(f"Retrieval failed for query {i}: {e}")
                retrieved_ids = []
                scores = []
            
            relevant_ids = ground_truth.get(query, [])
            
            self.metrics.add_result(
                query_id=f"q{i}",
                retrieved_ids=retrieved_ids,
                relevant_ids=relevant_ids,
                query_text=query,
                scores=scores,
            )
        
        return self.metrics.evaluate()
    
    def evaluate_from_results(
        self,
        results: List[Tuple[str, List[str], List[str]]],
    ) -> EvaluationReport:
        """
        Evaluate from pre-computed results.
        
        Args:
            results: List of (query, retrieved_ids, relevant_ids) tuples
        
        Returns:
            EvaluationReport
        """
        self.metrics.clear()
        
        for i, (query, retrieved_ids, relevant_ids) in enumerate(results):
            self.metrics.add_result(
                query_id=f"q{i}",
                retrieved_ids=retrieved_ids,
                relevant_ids=relevant_ids,
                query_text=query,
            )
        
        return self.metrics.evaluate()


# ============================================================================
# Convenience Functions
# ============================================================================

def calculate_mrr(
    retrieved_lists: List[List[str]],
    relevant_lists: List[List[str]],
) -> float:
    """
    Calculate MRR from lists of retrieved and relevant document IDs.
    
    Args:
        retrieved_lists: List of retrieved doc ID lists (one per query)
        relevant_lists: List of relevant doc ID lists (one per query)
    
    Returns:
        Mean Reciprocal Rank score
    """
    metrics = RetrievalMetrics()
    for i, (retrieved, relevant) in enumerate(zip(retrieved_lists, relevant_lists)):
        metrics.add_result(f"q{i}", retrieved, relevant)
    return metrics.mrr()


def calculate_recall_at_k(
    retrieved_lists: List[List[str]],
    relevant_lists: List[List[str]],
    k: int,
) -> float:
    """Calculate average Recall@K across all queries."""
    metrics = RetrievalMetrics(k_values=[k])
    for i, (retrieved, relevant) in enumerate(zip(retrieved_lists, relevant_lists)):
        metrics.add_result(f"q{i}", retrieved, relevant)
    report = metrics.evaluate()
    return report.recall_at_k[k]


def calculate_ndcg_at_k(
    retrieved_lists: List[List[str]],
    relevant_lists: List[List[str]],
    k: int,
) -> float:
    """Calculate average NDCG@K across all queries."""
    metrics = RetrievalMetrics(k_values=[k])
    for i, (retrieved, relevant) in enumerate(zip(retrieved_lists, relevant_lists)):
        metrics.add_result(f"q{i}", retrieved, relevant)
    report = metrics.evaluate()
    return report.ndcg_at_k[k]


def quick_evaluate(
    retrieved_lists: List[List[str]],
    relevant_lists: List[List[str]],
    k_values: List[int] = None,
) -> Dict:
    """
    Quick evaluation returning a dictionary of metrics.
    
    Args:
        retrieved_lists: Retrieved document IDs per query
        relevant_lists: Relevant document IDs per query
        k_values: K values to evaluate at
    
    Returns:
        Dictionary with all metrics
    """
    metrics = RetrievalMetrics(k_values or [1, 5, 10])
    for i, (retrieved, relevant) in enumerate(zip(retrieved_lists, relevant_lists)):
        metrics.add_result(f"q{i}", retrieved, relevant)
    return metrics.evaluate().to_dict()
