# Uncertain Order: synthetic project
## Input concept (authored for this demonstration)
An exhibit collects event records from clocks whose offsets are uncertain. Visitors should distinguish events that definitely precede others from events whose order cannot be determined. No central clock or network is required.
## Design and acceptance
- OUT-ORDER: treat each time as a closed interval of integer ticks; only claim A precedes B if A's latest time is strictly before B's earliest time. Touching or overlapping intervals are indeterminate. Reject reversed intervals.
- OUT-LOCAL: no network or external dependencies in the prototype. Input is already normalized to one tick unit; clock calibration is deliberately outside this milestone and must not be claimed solved.
## Method and responsibility
Use interval boundary cases and relation reversal as the product-specific quality checks. A single developer handles implementation and tests; independent review is required before claiming production readiness. No UI, data collection, format registry or extra agents at this stage. The next milestone is a partial-order representation; evaluate whether its edges preserve all definitely known ordering without inventing a total order.
## State and operations
Local prototype only; no GitHub repository was created for this example. No real exhibit data. Work in small reversible changes and verify before recording a pass. Preserve these requirements and use a separate proposal for changes to ordering semantics. Handoff context may be read on its own, without Engineering Forge. Real clock calibration, scalability and human comprehension remain untested.
