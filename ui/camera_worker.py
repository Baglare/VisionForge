"""Kamera okuma ve VisionEngine işleme döngüsünü Qt thread dışında yürütür."""

from __future__ import annotations

from collections import deque
import queue
import threading
import time
import traceback

import cv2
from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtGui import QImage

from vision_engine import VisionEngine


class CameraWorker(QObject):
    """Kamerayı okur, kareleri işler ve UI thread'ine sonuç gönderir."""

    frame_ready = Signal(object, object)
    error = Signal(str)
    finished = Signal()

    def __init__(self, source: int = 0) -> None:
        super().__init__()
        self.source = source
        self._running = False
        self._action_queue: queue.Queue[object] = queue.Queue()
        self._engine: VisionEngine | None = None
        self._capture = None
        self._system_items_payload: list[dict] = []
        self._last_frame_emit_time: float | None = None
        self._latest_frame_lock = threading.Lock()
        self._latest_frame: tuple[QImage, dict] | None = None
        self._performance_samples = {
            key: deque(maxlen=60)
            for key in ("camera_read_ms", "qt_conversion_ms", "pipeline_total_ms", "ui_emit_interval_ms")
        }

    def request_action(self, action) -> None:
        """UI thread'inden gelen aksiyonu güvenli kuyruğa ekler."""
        if action:
            self._action_queue.put(action)

    def stop(self) -> None:
        """Worker döngüsünü durdurur."""
        self._running = False

    def start(self) -> None:
        """Kamera ve VisionEngine döngüsünü başlatır."""
        if self._running:
            return

        self._running = True
        try:
            self._engine = VisionEngine()
            self._refresh_system_items_cache()
            self._capture = cv2.VideoCapture(self.source)
            self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self._capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            if not self._capture.isOpened():
                self.error.emit("Kamera açılamadı. Kamera bağlı ve başka uygulamada kullanılmıyor olmalı.")
                return

            capture_width = int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            capture_height = int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f"capture_width={capture_width}")
            print(f"capture_height={capture_height}")

            while self._running:
                frame_started = time.perf_counter()
                self._drain_actions()
                stage_started = time.perf_counter()
                success, frame = self._capture.read()
                self._append_performance("camera_read_ms", stage_started)
                if not success or frame is None:
                    self.error.emit("Kameradan görüntü alınamadı.")
                    break

                result = self._engine.process_frame(frame)
                stage_started = time.perf_counter()
                image = self._to_qimage(result.display_frame)
                self._append_performance("qt_conversion_ms", stage_started)
                payload = self._payload_from_result(result)
                self._append_performance("pipeline_total_ms", frame_started)
                emit_time = time.perf_counter()
                if self._last_frame_emit_time is not None:
                    self._performance_samples["ui_emit_interval_ms"].append(
                        (emit_time - self._last_frame_emit_time) * 1000.0
                    )
                self._last_frame_emit_time = emit_time
                payload["debug_info"].update(self._performance_debug_info())
                self._publish_frame(image, payload)
                QThread.msleep(1)
        except Exception:
            self.error.emit(traceback.format_exc())
        finally:
            self._cleanup()
            self.finished.emit()

    def _drain_actions(self) -> None:
        """Bekleyen UI aksiyonlarını engine'e uygular."""
        if self._engine is None:
            return
        while True:
            try:
                action = self._action_queue.get_nowait()
            except queue.Empty:
                return
            self._engine.handle_action(action)

    def _cleanup(self) -> None:
        """Kamera ve dedektör kaynaklarını kapatır."""
        if self._capture is not None:
            self._capture.release()
            self._capture = None
        if self._engine is not None:
            self._engine.close()
            self._engine = None
        with self._latest_frame_lock:
            self._latest_frame = None
        self._running = False

    def _publish_frame(self, image: QImage, payload: dict) -> None:
        """Ana UI için yalnızca en güncel kareyi saklar."""
        with self._latest_frame_lock:
            self._latest_frame = (image, payload)
        self.frame_ready.emit(image, payload)

    def take_latest_frame(self) -> tuple[QImage, dict] | None:
        """UI thread'inin göstereceği en güncel güvenli kareyi atomik olarak alır."""
        with self._latest_frame_lock:
            latest = self._latest_frame
            self._latest_frame = None
            return latest

    def _to_qimage(self, frame) -> QImage:
        """BGR OpenCV karesini QImage formatına çevirir."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channels = rgb.shape
        bytes_per_line = channels * width
        return QImage(rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).copy()

    def _append_performance(self, key: str, started_at: float) -> None:
        self._performance_samples[key].append((time.perf_counter() - started_at) * 1000.0)

    def _performance_average(self, key: str) -> float:
        samples = self._performance_samples[key]
        return sum(samples) / len(samples) if samples else 0.0

    def _performance_debug_info(self) -> dict:
        return {
            "perf_camera_read_ms": f"{self._performance_average('camera_read_ms'):.2f} ms",
            "perf_qt_conversion_ms": f"{self._performance_average('qt_conversion_ms'):.2f} ms",
            "perf_pipeline_total_ms": f"{self._performance_average('pipeline_total_ms'):.2f} ms",
            "perf_ui_emit_interval_ms": f"{self._performance_average('ui_emit_interval_ms'):.2f} ms",
        }

    def _refresh_system_items_cache(self) -> None:
        """Dosya tabanlı sistem durumunu worker başlangıcında yalnızca bir kez okur."""
        if self._engine is None:
            self._system_items_payload = []
            return
        self._system_items_payload = [
            {
                "label": item.label,
                "status": item.status_text,
                "required": item.required,
                "hint": item.hint,
            }
            for item in self._engine.system_status_items()
        ]

    def _payload_from_result(self, result) -> dict:
        """VisionEngineResult nesnesini sade Qt payload sözlüğüne çevirir."""
        profile = result.active_profile
        spell = result.spell_result
        trial = result.trial_status
        enrollment = result.enrollment_status
        return {
            "username": getattr(profile, "username", "-"),
            "rank": getattr(profile, "rank", "-"),
            "guild_name": getattr(profile, "guild_name", "-"),
            "verification_status": result.verification_status,
            "session_state": result.session_state,
            "grace_remaining_seconds": result.grace_remaining_seconds,
            "allowed_spells": result.allowed_spells,
            "status_text": result.status_text,
            "hand_status_text": result.hand_status_text,
            "active_spell": getattr(spell, "active_spell_name", None) or "Yok",
            "spell_status": getattr(spell, "status", "-") if spell is not None else "-",
            "cooldown": getattr(spell, "cooldown_remaining", 0.0) if spell is not None else 0.0,
            "prepare_progress": getattr(spell, "spell_prepare_progress", 0.0) if spell is not None else 0.0,
            "trial_state": getattr(trial, "state", "idle"),
            "trial_current_step": getattr(trial, "current_step", 0),
            "trial_required_spell": getattr(trial, "required_spell", None) or "-",
            "trial_completed_steps": list(getattr(trial, "completed_steps", []) or []),
            "trial_total_steps": getattr(trial, "total_steps", 3),
            "trial_is_completed": bool(getattr(trial, "is_completed", False)),
            "trial_progress": f"{getattr(trial, 'completed_count', 0)}/{getattr(trial, 'total_steps', 0)}",
            "trial_message": getattr(trial, "message", ""),
            "debug_info": result.debug_info,
            "notifications": [item.message for item in result.notifications],
            "settings": result.ui_settings,
            "system_items": self._system_items_payload,
            "spellbook_page": result.spellbook_page,
            "enrollment": enrollment,
        }
