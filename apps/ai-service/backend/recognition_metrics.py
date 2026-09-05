from collections import Counter
from threading import Lock


class RecognitionMetrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self._total_requests = 0
        self._matched_requests = 0
        self._confidence_sum = 0.0
        self._confidence_samples = 0
        self._failure_reasons: Counter[str] = Counter()
        self._labeled_results = 0
        self._false_positive_reports = 0

    def record_result(
        self,
        *,
        matched: bool,
        confidence: float = 0.0,
        error_code: str | None = None,
    ) -> None:
        with self._lock:
            self._total_requests += 1
            if matched:
                self._matched_requests += 1
            if confidence > 0:
                self._confidence_sum += confidence
                self._confidence_samples += 1
            if not matched:
                self._failure_reasons[error_code or "UNKNOWN"] += 1

    def record_feedback(self, *, false_positive: bool) -> None:
        with self._lock:
            self._labeled_results += 1
            if false_positive:
                self._false_positive_reports += 1

    def snapshot(self) -> dict:
        with self._lock:
            failed_requests = self._total_requests - self._matched_requests
            return {
                "total_requests": self._total_requests,
                "matched_requests": self._matched_requests,
                "failed_requests": failed_requests,
                "failure_rate": failed_requests / self._total_requests
                if self._total_requests
                else 0.0,
                "average_confidence": self._confidence_sum / self._confidence_samples
                if self._confidence_samples
                else 0.0,
                "failure_reasons": dict(self._failure_reasons),
                "labeled_results": self._labeled_results,
                "false_positive_reports": self._false_positive_reports,
                "false_positive_rate": self._false_positive_reports / self._labeled_results
                if self._labeled_results
                else 0.0,
            }
