import unittest

from auth.verification_session import VerificationSession, VerificationSessionState


class VerificationSessionTests(unittest.TestCase):
    def test_verified_user_lost_face_enters_grace_period(self):
        session = VerificationSession(grace_period_seconds=10.0)
        session.update(stable_face_label="baglare", full_verified_label="baglare", now=100.0)

        snapshot = session.update(stable_face_label=None, full_verified_label=None, now=101.0)

        self.assertEqual(snapshot.session_state, VerificationSessionState.GRACE_PERIOD.value)
        self.assertEqual(snapshot.verified_face_label, "baglare")
        self.assertTrue(snapshot.is_grace_active)
        self.assertAlmostEqual(snapshot.grace_remaining_seconds, 10.0)

    def test_same_user_returns_before_grace_expires(self):
        session = VerificationSession(grace_period_seconds=10.0)
        session.update(stable_face_label="baglare", full_verified_label="baglare", now=100.0)
        session.update(stable_face_label=None, full_verified_label=None, now=101.0)

        snapshot = session.update(stable_face_label="baglare", full_verified_label=None, now=105.0)

        self.assertEqual(snapshot.session_state, VerificationSessionState.VERIFIED.value)
        self.assertEqual(snapshot.verified_face_label, "baglare")
        self.assertFalse(snapshot.is_grace_active)

    def test_grace_period_expiry_resets_session_authority(self):
        session = VerificationSession(grace_period_seconds=10.0)
        session.update(stable_face_label="baglare", full_verified_label="baglare", now=100.0)
        session.update(stable_face_label=None, full_verified_label=None, now=101.0)

        snapshot = session.update(stable_face_label=None, full_verified_label=None, now=112.0)

        self.assertEqual(snapshot.session_state, VerificationSessionState.EXPIRED.value)
        self.assertIsNone(snapshot.verified_face_label)
        self.assertFalse(snapshot.is_grace_active)

    def test_other_registered_user_cancels_previous_session(self):
        session = VerificationSession(grace_period_seconds=10.0)
        session.update(stable_face_label="baglare", full_verified_label="baglare", now=100.0)

        snapshot = session.update(stable_face_label="other", full_verified_label=None, now=101.0)

        self.assertEqual(snapshot.session_state, VerificationSessionState.PENDING_SEAL.value)
        self.assertIsNone(snapshot.verified_face_label)

    def test_manual_reset_clears_grace_period(self):
        session = VerificationSession(grace_period_seconds=10.0)
        session.update(stable_face_label="baglare", full_verified_label="baglare", now=100.0)
        session.update(stable_face_label=None, full_verified_label=None, now=101.0)

        snapshot = session.reset()

        self.assertEqual(snapshot.session_state, VerificationSessionState.UNAUTHENTICATED.value)
        self.assertIsNone(snapshot.verified_face_label)
        self.assertFalse(snapshot.is_grace_active)

    def test_never_verified_user_does_not_get_grace_period(self):
        session = VerificationSession(grace_period_seconds=10.0)

        snapshot = session.update(stable_face_label="baglare", full_verified_label=None, now=100.0)

        self.assertEqual(snapshot.session_state, VerificationSessionState.PENDING_SEAL.value)
        self.assertIsNone(snapshot.verified_face_label)
        self.assertFalse(snapshot.is_grace_active)


if __name__ == "__main__":
    unittest.main()
