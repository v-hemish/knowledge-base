"""Service layer: import from submodules (e.g. ``app.services.guidance_service``)."""

# Avoid importing heavy modules here — ``app.retrieval.pipeline`` imports
# ``app.services.retrieval_pipeline_service``, and eager ``guidance_service`` would cycle.

__all__: list[str] = []
