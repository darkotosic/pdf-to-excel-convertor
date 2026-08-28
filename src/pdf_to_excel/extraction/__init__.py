"""Extraction strategies that turn page geometry into logical tables."""

from .generic_ruled import extract_generic_ruled_tables, score_grid_candidate

__all__ = ["extract_generic_ruled_tables", "score_grid_candidate"]
