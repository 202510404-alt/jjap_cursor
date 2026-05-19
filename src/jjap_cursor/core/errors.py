"""Dedicated exceptions for Jjap-Cursor orchestration and AI layers."""


class PlanningError(Exception):
    """Raised when plan generation, JSON validation, or Gemini orchestration fails."""
