"""Statistical core of the A/B calculator.

Rules:
- No UI code here: no print, no streamlit.
- Functions return dataclasses, not text.
- All rates and effects are fractions (0.113), not percent (11.3).
"""
