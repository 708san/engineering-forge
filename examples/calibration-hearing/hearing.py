"""Synthetic in-memory hearing-record model. Caller identity must be verified externally."""
from dataclasses import dataclass


class Conflict(ValueError):
    pass


@dataclass(frozen=True)
class Interpretation:
    id: str
    editor: str
    revision: int
    text: str


class Hearing:
    """One testimony, single authoritative writer; no networking or persistence."""
    def __init__(self, narrator, text):
        self._require_text(narrator)
        self._require_text(text)
        self.narrator = narrator
        self._versions = [text]
        self._interpretations = {}
        self._epoch = 0
        self._published = None

    @staticmethod
    def _require_text(value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError('nonempty text required')

    @property
    def revision(self):
        return len(self._versions)

    @property
    def epoch(self):
        return self._epoch

    def _owner(self, actor):
        if actor != self.narrator:
            raise PermissionError('narrator decision required')

    def _current(self, expected_epoch):
        if type(expected_epoch) is not int or expected_epoch != self._epoch:
            raise Conflict('stale state; obtain current state before retrying')

    def correct(self, actor, text, expected_epoch):
        self._owner(actor)
        self._current(expected_epoch)
        self._require_text(text)
        self._versions.append(text)
        self._published = None
        self._epoch += 1

    def withdraw(self, actor, expected_epoch):
        self._owner(actor)
        self._current(expected_epoch)
        self._published = None
        self._epoch += 1

    def submit_interpretation(self, actor, id, revision, text):
        """Receive a private offline draft. Never publish by submission."""
        for value in (actor, id, text):
            self._require_text(value)
        if type(revision) is not int or not 1 <= revision <= self.revision:
            raise Conflict('unknown testimony revision')
        item = Interpretation(id, actor, revision, text)
        previous = self._interpretations.get(id)
        if previous is not None:
            if previous != item:
                raise Conflict('draft ID reused with different content')
            return  # exact retry is idempotent
        self._interpretations[id] = item

    def publish(self, actor, expected_epoch, revision, interpretation_ids=()):
        self._owner(actor)
        self._current(expected_epoch)
        if type(revision) is not int or revision != self.revision:
            raise Conflict('only the current testimony may be published')
        ids = tuple(interpretation_ids)
        if len(set(ids)) != len(ids):
            raise ValueError('duplicate interpretation')
        selected = []
        for id in ids:
            item = self._interpretations.get(id)
            if item is None or item.revision != revision:
                raise Conflict('interpretation missing or based on old testimony')
            selected.append(item)
        # Publication is explicit, scoped to the selected immutable items.
        self._epoch += 1
        self._published = (revision, tuple(selected), self._epoch)

    def public_view(self):
        """Return a fresh projection, never the private history or editor IDs."""
        if self._published is None:
            return {'epoch': self._epoch, 'published': False}
        revision, selected, epoch = self._published
        return {'epoch': epoch, 'published': True, 'revision': revision,
                'testimony': self._versions[revision - 1],
                'interpretations': [{'id': item.id, 'text': item.text}
                                    for item in selected]}

    def narrator_history(self, actor):
        self._owner(actor)
        return {'testimonies': tuple(self._versions),
                'interpretations': tuple(self._interpretations.values())}
