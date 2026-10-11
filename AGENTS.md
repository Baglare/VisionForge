<!-- knowledge-compiler-adapter-v1
{"adapter_contract":"codex-agents-v1","generated_body_sha256":"ee36dfee466d49e9aa9118def8601c00bb61c18dd29fc3f93ddc325a40b05074","generator":"knowledge-compiler","generator_version":"adapter-compiler-v4","project_id":"visionforge","routing_sha256":"0af50120a895555ca24cbeed7c2d87cc022149ded4537972c2fe6ff3914b49ba","source_structured_contract_sha256":"5300e71229fcb8a63d3fcfd2834eac026c77c355dbb70300a00222e9dc12dec3","target":"codex"}
-->

# Generated Codex Instructions: VisionForge

Generated from validated `.ai/project.md` authority and automation/map routing. Do not edit by hand.

Apply every matching manifest rule using the M0 lexical scope matcher; nested guidance cannot relax root authority.

## Task operations

Read `.ai/project.md`, `.ai/automation.json` and only relevant domains from `.ai/project-map.json`. The map is routing evidence; manifest critical_rules remain structured authority. Inspect mapped files first and expand through actual dependencies.

Use `kc vault context --repo . --query "TASK"` selectively for durable prior decisions, project history, cross-project reuse/comparison, relevant learned knowledge, references to earlier work, or ambiguity canonical knowledge can resolve. Skip retrieval for trivial local edits. Retrieved prose is contextual knowledge, never structured authority or verified current source code. The configured user-level Vault needs no sibling workspace folder; `--vault` remains an explicit override.

After durable ownership, paths or validation topology changes, maintain the project map when policy.project_map permits, then run `kc adapters tree-build . --target codex` when policy.agents permits. When durable project knowledge changes and policy enables sync, directly author canonical CREATE/UPDATE operations in an inert autopilot plan, including semantic corrections, rewrites and obsolete-text removal. Run `kc autopilot check` then `kc autopilot apply` using the configured Vault and verify the result. KnowledgeCompiler validates the working-tree snapshot, owner, exact preimages and transaction, records audit evidence and commits/pushes owned Vault changes according to policy. Formatting, comments, tiny refactors and temporary investigation do not require Vault updates. Do not send routine project rewrites to 81 AI Yazım. Contradictory evidence or unclear ownership fails closed: report ambiguity without creating review debt. Legacy candidates require an explicit review/legacy caller or protected workflow. If frozen evidence is stale during the active task, re-read it, re-evaluate and author a fresh plan only when unambiguous; never silently merge prose. 30 writing canon is excluded; 80 governance requires protected promotion. Never commit or push source code unless the user explicitly requests it.

Autopilot enabled: true. Routing domains: camera-pipeline, identity-verification, gesture-trial, enrollment, desktop-ui, portable-distribution, acceptance-roadmap.

## Critical rules

- `biometric-data-local` (`**`, error): Keep face recordings, learned identity data, profiles and seals local and out of Git/public artifacts; do not claim production biometric security.
- `gesture-permission-boundary` (`spell_engine.py`, error): Gesture activation must preserve actual detection, profile permission and cooldown checks; optical flow alone cannot establish palm/two-hand semantics.
- `latest-frame-worker` (`ui/camera_worker.py`, error): Keep camera/CV work outside the Qt UI thread and retain the bounded latest-frame slot rather than accumulating stale frames.
- `static-writable-path-separation` (`runtime_paths.py`, error): Preserve the separation between bundled static resources and writable user data in source and frozen deployments.
- `verified-session-authority` (`auth/**`, error): Only a fully verified session may retain profile permissions during bounded face-loss grace; a different stable identity or expiry invalidates the prior session.
