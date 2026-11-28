# Purpose and protected outcomes
Synthetic design exercise, not a human-approved production specification. Source input: public CAL-02 in evaluation/calibration-v0.12.md at the foundation revision f209212205698ddb44ca5fc2675f52f31315ed4f.
- Keep testimony, narrator corrections and editors' interpretations distinct; do not treat interpretation as testimony.
- A withdrawal must stop the current authoritative public projection. Receiving an offline draft must not restore publication.
- A new public projection requires an explicit decision of the narrator, tied to current state and the current testimony revision. Old interpretations cannot silently be attached to a new correction.
- Preserve competing private interpretations without automatically publishing them. Only selected interpretations become public.
- Never claim complete deletion of copies already distributed or real authentication in this prototype.
## Scope and decisions
Use one synthetic testimony, one authoritative in-memory state machine, explicit compare-and-set epoch for narrator decisions, revision-linked immutable interpretation drafts. No database, distributed consensus, actual network, identity provider, or real personal data. The model allows an offline editor to submit a draft referring to a historical revision but does not sync private testimony back to the editor.
These are provisional implementation choices, not requirements for unrelated projects. A real service requires separate decisions on authorization, private draft retention, withdrawal scope, narrator/editor rights, conflicting consent, moderation, and the treatment of previously downloaded content.
