import unittest
from hearing import Hearing, Conflict


class HearingTests(unittest.TestCase):
    def setUp(self):
        self.h = Hearing('speaker', 'synthetic original')

    def test_initially_private(self):
        self.assertEqual(self.h.public_view(), {'epoch': 0, 'published': False})

    def test_explicit_publication(self):
        self.h.publish('speaker', 0, 1)
        self.assertEqual(self.h.public_view()['testimony'], 'synthetic original')
        self.assertNotIn('narrator', self.h.public_view())

    def test_editor_cannot_publish_or_correct_or_withdraw(self):
        for operation in (lambda: self.h.publish('editor', 0, 1),
                          lambda: self.h.correct('editor', 'fake', 0),
                          lambda: self.h.withdraw('editor', 0)):
            with self.assertRaises(PermissionError):
                operation()
        self.assertEqual(self.h.epoch, 0)

    def test_two_interpretations_are_preserved_and_selected(self):
        self.h.submit_interpretation('e1', 'a', 1, 'reading one')
        self.h.submit_interpretation('e2', 'b', 1, 'reading two')
        self.h.publish('speaker', 0, 1, ['b'])
        self.assertEqual(self.h.public_view()['interpretations'],
                         [{'id': 'b', 'text': 'reading two'}])
        self.assertEqual(len(self.h.narrator_history('speaker')['interpretations']), 2)

    def test_private_submission_does_not_change_public_view(self):
        self.h.publish('speaker', 0, 1)
        old = self.h.public_view()
        self.h.submit_interpretation('editor', 'a', 1, 'private draft')
        self.assertEqual(old, self.h.public_view())

    def test_withdrawal_rejects_stale_publish(self):
        self.h.publish('speaker', 0, 1)
        old_epoch = self.h.epoch
        self.h.withdraw('speaker', old_epoch)
        with self.assertRaises(Conflict):
            self.h.publish('speaker', old_epoch, 1)
        self.assertFalse(self.h.public_view()['published'])

    def test_offline_draft_after_withdrawal_remains_private(self):
        self.h.publish('speaker', 0, 1)
        self.h.withdraw('speaker', 1)
        self.h.submit_interpretation('offline-editor', 'a', 1, 'offline reading')
        self.assertEqual(self.h.public_view(), {'epoch': 2, 'published': False})

    def test_new_explicit_publication_after_withdrawal(self):
        self.h.publish('speaker', 0, 1)
        self.h.withdraw('speaker', 1)
        self.h.publish('speaker', 2, 1)
        self.assertTrue(self.h.public_view()['published'])

    def test_correction_unpublishes_and_keeps_history(self):
        self.h.publish('speaker', 0, 1)
        self.h.correct('speaker', 'synthetic correction', 1)
        self.assertFalse(self.h.public_view()['published'])
        self.assertEqual(self.h.narrator_history('speaker')['testimonies'],
                         ('synthetic original', 'synthetic correction'))
        self.h.publish('speaker', 2, 2)
        self.assertEqual(self.h.public_view()['testimony'], 'synthetic correction')

    def test_old_interpretation_cannot_attach_to_corrected_publication(self):
        self.h.submit_interpretation('editor', 'a', 1, 'old reading')
        self.h.correct('speaker', 'correction', 0)
        with self.assertRaises(Conflict):
            self.h.publish('speaker', 1, 2, ['a'])
        self.assertFalse(self.h.public_view()['published'])
        self.assertEqual(self.h.epoch, 1)

    def test_competing_correction_rejected(self):
        self.h.correct('speaker', 'first', 0)
        with self.assertRaises(Conflict):
            self.h.correct('speaker', 'stale', 0)
        self.assertEqual(self.h.revision, 2)

    def test_retry_draft_is_idempotent_but_conflict_rejected(self):
        self.h.submit_interpretation('editor', 'a', 1, 'draft')
        self.h.submit_interpretation('editor', 'a', 1, 'draft')
        with self.assertRaises(Conflict):
            self.h.submit_interpretation('editor', 'a', 1, 'rewritten')
        self.assertEqual(len(self.h.narrator_history('speaker')['interpretations']), 1)

    def test_private_history_not_available_to_editor(self):
        with self.assertRaises(PermissionError):
            self.h.narrator_history('editor')

    def test_previous_public_copy_not_erased_by_withdrawal(self):
        self.h.publish('speaker', 0, 1)
        old = self.h.public_view()
        self.h.withdraw('speaker', 1)
        self.assertFalse(self.h.public_view()['published'])
        self.assertEqual(old['testimony'], 'synthetic original')

    def test_unknown_revision_rejected(self):
        with self.assertRaises(Conflict):
            self.h.submit_interpretation('editor', 'a', 2, 'future')
        with self.assertRaises(Conflict):
            self.h.publish('speaker', 0, 2)
        self.assertEqual(self.h.epoch, 0)
