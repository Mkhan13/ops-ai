"""
Week 7: Cost Optimization & Feedback Loop Starter Template

Implement three systems:
1. CostAnalyzer - analyze and track query costs
2. OptimizationStrategy - optimize costs through caching, model selection, etc.
3. FeedbackLoop - collect and validate user corrections
"""

import json
import logging
from typing import Dict, List, Any
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# TASK 1: Implement CostAnalyzer
# ============================================================================


class CostAnalyzer:
    """Analyze and track query costs by component."""

    def __init__(self):
        """Initialize cost analyzer.

        TODO: Initialize empty query history list
        """
        self.query_history = []

    def record_query(self, query: Dict[str, Any]):
        """Record a query and its cost breakdown.

        TODO: Store query dict with fields:
        - query_text: the user's question
        - retrieval_cost: cost of retrieving documents
        - llm_cost: cost of LLM inference
        - tool_cost: cost of tool calls
        - error_cost: cost of retries/errors
        - total_cost: sum of above
        - timestamp: when query was run (use datetime.utcnow().isoformat())
        """
        retrieval_cost = query.get("retrieval_cost", 0.0)
        llm_cost = query.get("llm_cost", 0.0)
        tool_cost = query.get("tool_cost", 0.0)
        error_cost = query.get("error_cost", 0.0)
        total_cost = retrieval_cost + llm_cost + tool_cost + error_cost

        query_record = {
            "query_text": query.get("query_text", ""),
            "retrieval_cost": retrieval_cost,
            "llm_cost": llm_cost,
            "tool_cost": tool_cost,
            "error_cost": error_cost,
            "total_cost": total_cost,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.query_history.append(query_record)

    def get_cost_breakdown(self) -> Dict[str, Any]:
        """Get breakdown of costs by component.

        TODO: Calculate totals for all queries:
        - retrieval_total
        - llm_total
        - tool_total
        - error_total
        - total_daily (sum of all)
        - query_count

        Return dict with these totals
        """
        retrieval_total = 0.0
        llm_total = 0.0
        tool_total = 0.0
        error_total = 0.0

        for recorded_query in self.query_history:
            retrieval_total += recorded_query["retrieval_cost"]
            llm_total += recorded_query["llm_cost"]
            tool_total += recorded_query["tool_cost"]
            error_total += recorded_query["error_cost"]

        total_daily = retrieval_total + llm_total + tool_total + error_total

        return {
            "retrieval_total": retrieval_total,
            "llm_total": llm_total,
            "tool_total": tool_total,
            "error_total": error_total,
            "total_daily": total_daily,
            "query_count": len(self.query_history),
        }

    def identify_cost_spikes(self) -> List[Dict]:
        """Identify unusually expensive queries.

        TODO: Find statistical outliers:
        1. Calculate mean and standard deviation of query costs
        2. Find queries > mean + 2*stdev
        3. Return list of spike queries with details
        """
        if len(self.query_history) == 0:
            return []

        all_costs = []
        for recorded_query in self.query_history:
            all_costs.append(recorded_query["total_cost"])

        mean_cost = sum(all_costs) / len(all_costs)

        squared_differences = []
        for cost in all_costs:
            squared_differences.append((cost - mean_cost) ** 2)
        variance = sum(squared_differences) / len(squared_differences)
        stdev_cost = variance ** 0.5

        spike_threshold = mean_cost + 2 * stdev_cost

        spike_queries = []
        for recorded_query in self.query_history:
            if recorded_query["total_cost"] > spike_threshold:
                spike_queries.append(recorded_query)

        return spike_queries


# ============================================================================
# TASK 2: Implement OptimizationStrategy
# ============================================================================


class OptimizationStrategy:
    """Optimize agent costs through multiple strategies."""

    def __init__(self):
        """Initialize optimization strategy.

        TODO: Initialize cache and strategy tracking
        """
        self.cache = {}  # {query: response}
        self.strategies_applied = []

    def apply_caching(self, query: str, response: str) -> tuple:
        """Cache query responses.

        TODO: Implement caching
        1. If query in cache, return (True, cached_response)
        2. Otherwise, store in cache and return (False, response)

        Args:
            query: user's question
            response: LLM's answer

        Returns:
            (is_cached_hit, response)
        """
        if query in self.cache:
            cached_response = self.cache[query]
            return (True, cached_response)
        self.cache[query] = response
        return (False, response)

    def optimize_retrieval_count(self, num_docs: int) -> int:
        """Reduce number of documents retrieved.

        TODO: Reduce count intelligently
        - Input 15 docs → output 3 docs (top-k)
        - Reduces token cost

        Args:
            num_docs: original document count

        Returns:
            optimized document count
        """
        # TODO: implement
        return max(1, num_docs // 5)  # Simple: reduce by 5x

    def select_model_by_complexity(self, query: str) -> str:
        """Choose cheaper model for simple queries.

        TODO: Analyze query complexity
        - Simple queries ("What is X?") → gemini-1.5-flash (cheaper, faster)
        - Complex queries ("Analyze...", "Compare...", "Design...") → gemini-2.5-pro

        Args:
            query: user's question

        Returns:
            model name to use
        """
        complex_keywords = ["analyze", "compare", "design", "explain", "evaluate", "summarize"]

        query_lower = query.lower()

        for keyword in complex_keywords:
            if keyword in query_lower:
                return "gemini-2.5-pro"

        return "gemini-1.5-flash"

    def enable_response_compression(self, response: str) -> str:
        """Compress long responses while keeping essential info.

        TODO: Reduce response length
        1. Split into sentences
        2. Keep only first N essential sentences
        3. Return compressed response

        Args:
            response: original response

        Returns:
            compressed response
        """
        max_sentences = 3
        sentences = response.split(".")

        essential_sentences = []
        for sentence in sentences[:max_sentences]:
            trimmed_sentence = sentence.strip()
            if trimmed_sentence:
                essential_sentences.append(trimmed_sentence)

        response = ". ".join(essential_sentences)

        if response and not response.endswith("."):
            response += "."

        return response

    def get_optimization_impact(self) -> Dict[str, Any]:
        """Estimate cost savings from applied optimizations.

        TODO: Return impact analysis:
        - total_savings_pct: estimated % cost reduction
        - strategies_applied: list of which strategies used
        - breakdown: savings estimate per strategy
        """
        savings_per_strategy = {
            "caching": 30.0,
            "retrieval_count": 20.0,
            "model_selection": 25.0,
            "compression": 15.0,
        }

        breakdown = {}
        for strategy in self.strategies_applied:
            if strategy in savings_per_strategy:
                breakdown[strategy] = savings_per_strategy[strategy]

        total_savings_pct = sum(breakdown.values())

        return {
            "total_savings_pct": total_savings_pct,
            "strategies_applied": self.strategies_applied,
            "breakdown": breakdown,
        }


# ============================================================================
# TASK 3: Implement FeedbackLoop
# ============================================================================


class FeedbackLoop:
    """Collect and validate user corrections for continuous improvement."""

    def __init__(self):
        """Initialize feedback loop.

        TODO: Initialize corrections list and validation rules
        """
        self.corrections = []
        # Authority hierarchy for role-based validation
        self.authority = {
            "engineer": 1,
            "hr": 2,
            "finance": 2,
            "manager": 3,
            "executive": 4,
        }

    def submit_correction(
        self,
        original_query: str,
        original_answer: str,
        corrected_answer: str,
        user_role: str,
    ) -> Dict[str, Any]:
        """Submit a correction to the agent's answer.

        TODO: Validate and store correction
        1. Check user_role has sufficient authority
        2. Check corrected_answer is detailed enough (longer than original)
        3. Store in corrections list
        4. Return acceptance status

        Args:
            original_query: the question
            original_answer: agent's incorrect answer
            corrected_answer: user's correction
            user_role: user's role (for authority check)

        Returns:
            {"accepted": True/False, "reason": "..."}
        """
        user_authority_level = self.authority.get(user_role, 0)

        if user_authority_level < 2:
            return {"accepted": False, "reason": "Insufficient authority to submit corrections"}

        if len(corrected_answer) <= len(original_answer):
            return {"accepted": False, "reason": "Correction must be more detailed than the original answer"}

        correction_entry = {
            "original_query": original_query,
            "original_answer": original_answer,
            "corrected_answer": corrected_answer,
            "user_role": user_role,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.corrections.append(correction_entry)

        return {"accepted": True, "reason": "Correction accepted"}

    def validate_correction(self, index: int) -> bool:
        """Validate a stored correction is accurate.

        TODO: Check correction quality:
        1. User role has sufficient authority (manager+, i.e. level 3 or above)
        2. Correction is more detailed than original
        3. Correction makes sense

        Args:
            index: index into corrections list

        Returns:
            True if correction is valid, False otherwise
        """
        if index < 0 or index >= len(self.corrections):
            return False

        correction = self.corrections[index]

        user_authority_level = self.authority.get(correction["user_role"], 0)
        if user_authority_level < 3:
            return False

        if len(correction["corrected_answer"]) <= len(correction["original_answer"]):
            return False

        return True

    def get_feedback_metrics(self) -> Dict[str, Any]:
        """Compute metrics on feedback quality.

        TODO: Calculate:
        - total_corrections: number of corrections received
        - validation_rate: % of corrections that are valid
        - avg_correction_length: average length of corrections
        - top_error_patterns: most common mistakes corrected

        Returns:
            dict with feedback metrics
        """
        if len(self.corrections) == 0:
            return {
                "total_corrections": 0,
                "validation_rate": 0.0,
                "avg_correction_length": 0.0,
                "top_error_patterns": [],
            }

        valid_count = 0
        for index in range(len(self.corrections)):
            if self.validate_correction(index):
                valid_count += 1

        validation_rate = valid_count / len(self.corrections)

        total_length = 0
        for correction in self.corrections:
            total_length += len(correction["corrected_answer"])
        avg_correction_length = total_length / len(self.corrections)

        word_counts = {}
        for correction in self.corrections:
            words = correction["original_query"].lower().split()
            for word in words:
                if word not in word_counts:
                    word_counts[word] = 0
                word_counts[word] += 1

        sorted_words = sorted(word_counts, key=lambda word: word_counts[word], reverse=True)
        top_error_patterns = sorted_words[:5]

        return {
            "total_corrections": len(self.corrections),
            "validation_rate": validation_rate,
            "avg_correction_length": avg_correction_length,
            "top_error_patterns": top_error_patterns,
        }


if __name__ == "__main__":
    # Basic structure is provided below. Add your own test cases to verify your implementation.
    # Run with: python3 cost_optimization_starter.py

    # Test CostAnalyzer
    print("Testing CostAnalyzer")
    analyzer = CostAnalyzer()
    # TODO: record a query and verify get_cost_breakdown() returns correct totals
    analyzer.record_query({
        "query_text": "How many vacation days do engineers get per year?",
        "retrieval_cost": 0.0025,
        "llm_cost": 0.004,
        "tool_cost": 0.0015,
        "error_cost": 0.0,
    })
    analyzer.record_query({
        "query_text": "What is the reimbursement limit for team offsites?",
        "retrieval_cost": 0.003,
        "llm_cost": 0.008,
        "tool_cost": 0.002,
        "error_cost": 0.0005,
    })
    cheap_query_names = [
        "What is the sick leave policy?",
        "How do I submit an expense report?",
        "What is the hybrid work schedule?",
        "When is open enrollment for benefits?",
        "What is the laptop replacement policy?",
        "How do I request a software license?",
        "What is the performance review cycle?",
    ]
    for cheap_query_name in cheap_query_names:
        analyzer.record_query({
            "query_text": cheap_query_name,
            "retrieval_cost": 0.0012,
            "llm_cost": 0.0055,
            "tool_cost": 0.0008,
            "error_cost": 0.0,
        })
    analyzer.record_query({
        "query_text": "Analyze and summarize all HR, finance, and legal compliance policies company-wide.",
        "retrieval_cost": 0.12,
        "llm_cost": 0.48,
        "tool_cost": 0.06,
        "error_cost": 0.025,
    })

    cost_breakdown = analyzer.get_cost_breakdown()
    assert cost_breakdown["query_count"] == 10, "Should have 10 queries"
    assert round(cost_breakdown["retrieval_total"], 4) == round(0.0025 + 0.003 + 7 * 0.0012 + 0.12, 4), "Retrieval total mismatch"
    assert round(cost_breakdown["llm_total"], 4) == round(0.004 + 0.008 + 7 * 0.0055 + 0.48, 4), "LLM total mismatch"
    assert round(cost_breakdown["total_daily"], 4) == round(cost_breakdown["retrieval_total"] + cost_breakdown["llm_total"] + cost_breakdown["tool_total"] + cost_breakdown["error_total"], 4), "Daily total mismatch"
    print("  get_cost_breakdown: PASSED")

    cost_spikes = analyzer.identify_cost_spikes()
    assert len(cost_spikes) == 1, "Should detect 1 spike (the expensive query)"
    assert cost_spikes[0]["query_text"] == "Analyze and summarize all HR, finance, and legal compliance policies company-wide.", "Wrong spike detected"
    print("  identify_cost_spikes: PASSED")

    # Test OptimizationStrategy
    print("\nTesting OptimizationStrategy")
    optimizer = OptimizationStrategy()
    # TODO: test apply_caching, select_model_by_complexity, and optimize_retrieval_count

    first_result = optimizer.apply_caching("How many vacation days do engineers get per year?", "Engineers receive 15 vacation days per year.")
    assert first_result[0] == False, "First call should be a cache miss"
    print("  apply_caching (miss): PASSED")

    second_result = optimizer.apply_caching("How many vacation days do engineers get per year?", "Engineers receive 15 vacation days per year.")
    assert second_result[0] == True, "Second call should be a cache hit"
    assert second_result[1] == "Engineers receive 15 vacation days per year.", "Cached response should match"
    print("  apply_caching (hit): PASSED")

    simple_model = optimizer.select_model_by_complexity("When is open enrollment for benefits?")
    assert simple_model == "gemini-1.5-flash", "Simple query should use flash model"
    print("  select_model_by_complexity (simple): PASSED")

    complex_model = optimizer.select_model_by_complexity("Analyze the reimbursement limits across all employee levels.")
    assert complex_model == "gemini-2.5-pro", "Complex query should use pro model"
    print("  select_model_by_complexity (complex): PASSED")

    optimized_count = optimizer.optimize_retrieval_count(15)
    assert optimized_count == 3, "15 docs should reduce to 3"
    print("  optimize_retrieval_count: PASSED")

    long_response = "The hybrid work policy applies to all full-time employees. Engineers may work remotely up to three days per week. Employees must be on-site for team meetings and quarterly reviews. All remote work must be approved by a direct manager. Equipment for home offices is reimbursed up to $500 per year."
    compressed = optimizer.enable_response_compression(long_response)
    original_sentence_count = len([sentence for sentence in long_response.split(".") if sentence.strip()])
    compressed_sentence_count = len([sentence for sentence in compressed.split(".") if sentence.strip()])
    assert compressed_sentence_count <= 3, "Compressed response should have at most 3 sentences"
    assert original_sentence_count > compressed_sentence_count, "Compressed response should be shorter"
    print("  enable_response_compression: PASSED")

    optimizer.strategies_applied = ["caching", "model_selection"]
    impact = optimizer.get_optimization_impact()
    assert impact["total_savings_pct"] == 55.0, "Caching (30%) + model_selection (25%) should equal 55%"
    assert "caching" in impact["breakdown"], "Caching should appear in breakdown"
    print("  get_optimization_impact: PASSED")

    # Test FeedbackLoop
    print("\nTesting FeedbackLoop")
    feedback = FeedbackLoop()
    # TODO: submit corrections with different roles and verify accepted/rejected correctly

    engineer_result = feedback.submit_correction(
        original_query="How many remote days are engineers allowed per week?",
        original_answer="There is no specific limit on remote days.",
        corrected_answer="Engineers are allowed up to three remote days per week, subject to manager approval and team needs.",
        user_role="engineer",
    )
    assert engineer_result["accepted"] == False, "Engineer should not have authority to submit corrections"
    print("  submit_correction (engineer rejected): PASSED")

    manager_result = feedback.submit_correction(
        original_query="How many remote days are engineers allowed per week?",
        original_answer="There is no specific limit on remote days.",
        corrected_answer="Engineers are allowed up to three remote days per week, subject to manager approval and team needs.",
        user_role="manager",
    )
    assert manager_result["accepted"] == True, "Manager should be able to submit corrections"
    print("  submit_correction (manager accepted): PASSED")

    too_short_result = feedback.submit_correction(
        original_query="What is the laptop replacement policy?",
        original_answer="Laptops are replaced on a case by case basis.",
        corrected_answer="Ask IT.",
        user_role="executive",
    )
    assert too_short_result["accepted"] == False, "Short correction should be rejected"
    print("  submit_correction (too short rejected): PASSED")

    is_valid = feedback.validate_correction(0)
    assert is_valid == True, "Manager correction should be valid"
    print("  validate_correction: PASSED")

    metrics = feedback.get_feedback_metrics()
    assert metrics["total_corrections"] == 1, "Should have 1 accepted correction"
    assert metrics["validation_rate"] == 1.0, "All corrections should be valid"
    assert metrics["avg_correction_length"] > 0, "Average length should be positive"
    print("  get_feedback_metrics: PASSED")

    print("\nAll tests passed!")
