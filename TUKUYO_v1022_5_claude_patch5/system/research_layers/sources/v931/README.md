# TUKUYO v931 — Audit Repair

Repairs the concrete v911–v920 audit failures D1/D2/D4/D5/D9/D10.

Key boundary: this package **does not** claim the 30-day test is complete or even restarted. `tools/wallclock30_anchor.py init` must be run on the long-lived host; it refuses reset and requires >=2 independent HTTP Date anchors.

The candidate expected by the external semantic promotion contract is published as:

`c6ce537a009ebaa9a49bfc286bcfd81b7f80884d08810a2ab7238524be1d059b`

Search causality is falsifiable: evidence-driven selection must beat reverse selection, a constant-order selector, and the median of 30 random three-mutation sequences. The mutation grammar deliberately cannot express the oracle's interaction rule, so its endpoint is not the oracle.
