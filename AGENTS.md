<!-- knowledge-compiler-adapter-v1
{"adapter_contract":"codex-agents-v1","generated_body_sha256":"bc9fbcfadbc2ce148a9460c6374431ca35e75fedbf8f2da78982b8bdd0f6a138","generator":"knowledge-compiler","generator_version":"adapter-compiler-v2","project_id":"visionforge","routing_sha256":"0af50120a895555ca24cbeed7c2d87cc022149ded4537972c2fe6ff3914b49ba","source_structured_contract_sha256":"5300e71229fcb8a63d3fcfd2834eac026c77c355dbb70300a00222e9dc12dec3","target":"codex"}
-->

# Generated Codex Instructions: VisionForge

Generated from validated `.ai/project.md` authority and automation/map routing. Do not edit by hand.

Apply every matching manifest rule using the M0 lexical scope matcher; nested guidance cannot relax root authority.

## Task operations

Read `.ai/project.md`, `.ai/automation.json` and only relevant domains from `.ai/project-map.json`. The map is routing evidence; manifest critical_rules remain structured authority. Inspect mapped files first and expand through actual dependencies.

After durable ownership, paths or validation topology changes, maintain the project map when policy.project_map permits, then run `kc adapters tree-build . --target codex` when policy.agents permits. When durable project knowledge changes and policy enables sync, author an inert autopilot plan, run `kc autopilot check` then `kc autopilot apply`. KnowledgeCompiler validates the working-tree snapshot, owner, exact preimages and transaction, records audit evidence and commits/pushes owned Vault changes according to policy. Formatting, comments, tiny refactors and temporary investigation do not require Vault updates. Ambiguity fails closed; 81 is exceptional manual fallback. 30 writing canon is excluded; 80 governance requires protected promotion. Never commit or push source code unless the user explicitly requests it.

Autopilot enabled: true. Routing domains: camera-pipeline, identity-verification, gesture-trial, enrollment, desktop-ui, portable-distribution, acceptance-roadmap.

## Critical rules

- `biometric-data-local` (`**`, error): Keep face recordings, learned identity data, profiles and seals local and out of Git/public artifacts; do not claim production biometric security.
- `gesture-permission-boundary` (`spell_engine.py`, error): Gesture activation must preserve actual detection, profile permission and cooldown checks; optical flow alone cannot establish palm/two-hand semantics.
- `latest-frame-worker` (`ui/camera_worker.py`, error): Keep camera/CV work outside the Qt UI thread and retain the bounded latest-frame slot rather than accumulating stale frames.
- `static-writable-path-separation` (`runtime_paths.py`, error): Preserve the separation between bundled static resources and writable user data in source and frozen deployments.
- `verified-session-authority` (`auth/**`, error): Only a fully verified session may retain profile permissions during bounded face-loss grace; a different stable identity or expiry invalidates the prior session.
