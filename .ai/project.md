---
{"critical_rules":[{"id":"biometric-data-local","kind":"sensitive-area","scope":"**","severity":"error","statement":"Keep face recordings, learned identity data, profiles and seals local and out of Git/public artifacts; do not claim production biometric security."},{"id":"gesture-permission-boundary","kind":"invariant","scope":"spell_engine.py","severity":"error","statement":"Gesture activation must preserve actual detection, profile permission and cooldown checks; optical flow alone cannot establish palm/two-hand semantics."},{"id":"latest-frame-worker","kind":"invariant","scope":"ui/camera_worker.py","severity":"error","statement":"Keep camera/CV work outside the Qt UI thread and retain the bounded latest-frame slot rather than accumulating stale frames."},{"id":"static-writable-path-separation","kind":"invariant","scope":"runtime_paths.py","severity":"error","statement":"Preserve the separation between bundled static resources and writable user data in source and frozen deployments."},{"id":"verified-session-authority","kind":"invariant","scope":"auth/**","severity":"error","statement":"Only a fully verified session may retain profile permissions during bounded face-loss grace; a different stable identity or expiry invalidates the prior session."}],"manifest_version":1,"project_id":"visionforge","project_name":"VisionForge","schema":"project-ai-manifest-v1"}
---
# Purpose

Local PySide6 desktop computer-vision and gesture interaction prototype using MediaPipe, OpenCV LBPH and QR guild-seal verification.

# Repository Map

- camera-pipeline: camera.py, vision_engine.py, ui/camera_worker.py, ui/frame_view.py
- identity-verification: auth, detectors, guild_profile.py, identity_health.py
- gesture-trial: tracking, spell_engine.py, trial_engine.py
- enrollment: enrollment, face_preprocessing.py
- desktop-ui: app.py, ui/main_window.py, ui_notifications.py, effects.py, settings_manager.py, system_status.py
- portable-distribution: runtime_paths.py, packaging, tools/build_windows.ps1, tools/verify_distribution.py
- acceptance-roadmap: tests, requirements.txt

# Architecture

app.py starts Qt; MainWindow owns page composition. CameraWorker runs camera and VisionEngine in a QThread with a single locked latest-frame slot. VisionEngine separates raw processing_frame from mirrored/overlay display_frame and coordinates detectors, verification, hand tracking, spells, trial and enrollment. runtime_paths.py separates bundled static assets from writable portable user data.

# Validation Notes

Use python -m unittest tests.test_verification_session for session changes and syntax checks on directly changed Python files. Camera, enrollment, GUI and frozen distribution acceptance are manual/explicit gates described in docs/MANUAL_TESTS.md and docs/PACKAGING.md.

# Sensitive Areas

Face gallery, LBPH models/labels, profiles and QR seals are local sensitive data; keep them out of Git and public screenshots. VerificationSession owns full verification and bounded grace state.

# Non-goals

Not a production biometric security product. Optical flow is not proof of an open palm or two detected hands. ArtifactHub does not run a live camera.
