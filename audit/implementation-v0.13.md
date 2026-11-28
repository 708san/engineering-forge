# v0.13-dev migration and implementation (self-review)
Parent before migration: 4439989e6cdc311b6364207e7d993be23a65d2ee. CI run 46089095752 reported success.
Original archive: development-harness-design-v0.6.zip. The following five files were restored and remote Git blob identities matched the original archive:
- schemas/record.schema.json 2b1783d7a81316adabf419618d5214a02c24d2d2
- schemas/project.schema.json 428152d5818dadffaa0fec7951edb2b7629b6951
- schemas/example-response-map.schema.json 97282779686881a583a3d090fe9d918150c58686
- fixtures/project.json b5c91990cf2e90db5ab6d4c2074f4154a838cb79
- fixtures/records.json 61f553f615f986109d9077a27b53aadad63c7ecf
Migration commit b6779c128afc2326cc5f1aa05fbb7096f1641d58. Original schemas not changed. Public synthetic fixtures only.
Added records CLI, 19 regression cases, package references and CI smoke. R21/R44 now have partial implementation, not full acceptance. Local schemas only; restricted declarative vocabulary; no external reference fetching, no execution of payloads, no authenticated authority. Unregistered extensions are preserved/unverified. Record inspection validates declared references and local body digest, not actual semantic truth, body anchors, baseline snapshot, managed output authenticity or Practice definitions. No automatic state changes. Full prior archive migration, independent audit, native hosts and comparative experiments still pending. New CI to be checked separately.
