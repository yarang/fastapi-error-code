"""
Trace context propagation for distributed tracing

Provides W3C Trace Context propagation:
- TraceContextPropagator: Extract and inject trace context
- traceparent header parsing and generation
- Cross-service tracing support
"""

from typing import Dict, Optional

from opentelemetry import trace, propagate, context
from opentelemetry.trace import SpanContext, get_current_span, set_span_in_context
from opentelemetry.propagators.textmap import Getter, Setter
from opentelemetry.sdk.trace import ReadableSpan


class TraceContextPropagator:
    """
    W3C Trace Context propagator for distributed tracing.

    Handles extraction and injection of trace context
    according to W3C Trace Context specification.
    """

    def __init__(self):
        """Initialize trace context propagator."""
        self._getter = DictGetter()
        self._setter = DictSetter()

    def extract(self, headers: Dict[str, str]) -> Optional[SpanContext]:
        """
        Extract trace context from headers.

        Args:
            headers: HTTP headers containing traceparent

        Returns:
            SpanContext if valid traceparent found, None otherwise
        """
        # First try to parse traceparent directly
        traceparent = headers.get("traceparent")
        if traceparent:
            return self.parse_traceparent(traceparent)

        # Fall back to OpenTelemetry propagator
        try:
            ctx = propagate.extract(headers, getter=self._getter)
            span = get_current_span(ctx)
            if span and span.context:
                return span.get_span_context()
        except Exception:
            pass
        return None

    def inject(self, headers: Dict[str, str]) -> None:
        """
        Inject trace context into headers.

        Args:
            headers: HTTP headers to inject traceparent into
        """
        # Get current span
        span = get_current_span()
        if span:
            # Get span context using get_span_context()
            span_context = span.get_span_context()
            if span_context and span_context.is_valid:
                # Generate traceparent from span context
                traceparent = self.generate_traceparent(span_context)
                headers["traceparent"] = traceparent

    def parse_traceparent(self, traceparent: str) -> Optional[SpanContext]:
        """
        Parse traceparent header value.

        Args:
            traceparent: traceparent header value (format: version-traceid-parentid-flags)

        Returns:
            SpanContext if valid, None otherwise
        """
        try:
            parts = traceparent.split("-")
            if len(parts) != 4:
                return None

            version, trace_id, span_id, flags = parts

            # Validate format
            if version != "00":
                return None

            if len(trace_id) != 32 or len(span_id) != 16:
                return None

            # Create span context from parsed values
            from opentelemetry.trace.span import SpanContext
            return SpanContext(
                trace_id=int(trace_id, 16),
                span_id=int(span_id, 16),
                is_remote=True
            )
        except (ValueError, AttributeError):
            return None

    def generate_traceparent(self, span_context: SpanContext) -> str:
        """
        Generate traceparent header value.

        Args:
            span_context: Span context to generate traceparent from

        Returns:
            traceparent header value
        """
        trace_id = format(span_context.trace_id, "032x")
        span_id = format(span_context.span_id, "016x")
        flags = "01" if span_context.is_valid else "00"

        return f"00-{trace_id}-{span_id}-{flags}"


class DictGetter(Getter):
    """Getter for extracting from dict-like objects."""

    def get(self, carrier: Dict[str, str], key: str) -> Optional[list]:
        """Get value from carrier."""
        value = carrier.get(key)
        if value is None:
            return None
        return [value]

    def keys(self, carrier: Dict[str, str]) -> list:
        """Get all keys from carrier."""
        return list(carrier.keys())


class DictSetter(Setter):
    """Setter for injecting into dict-like objects."""

    def set(self, carrier: Dict[str, str], key: str, value: str) -> None:
        """Set value in carrier."""
        carrier[key] = value
