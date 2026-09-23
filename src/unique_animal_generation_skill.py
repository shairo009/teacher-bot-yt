"""Permanent, fail-closed uniqueness service for the existing offline animal bot.

The checksummed append-only journal is authoritative; the readable JSON snapshot
is rebuilt after a crash. Never truncate history or retry an uncertain upload.
Only controlled, renderer-supported vocabulary is offered by the planner.
"""
from __future__ import annotations

from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import secrets
import subprocess
import tempfile


class DiversityError(RuntimeError):
    pass


class HistoryError(RuntimeError):
    pass


FIELDS = ('species', 'subspecies', 'age', 'size', 'body_appearance', 'color_pattern',
          'pose', 'action', 'expression', 'camera_angle', 'camera_movement',
          'environment', 'lighting', 'weather', 'props', 'animation', 'story',
          'composition', 'seed')
WEIGHTS = {'species': .20, 'body_appearance': .08, 'color_pattern': .06,
           'action': .18, 'environment': .18, 'camera_angle': .06,
           'camera_movement': .04, 'lighting': .04, 'composition': .10,
           'pose': .03, 'story': .03}
ALIASES = {'running': 'run', 'jogging': 'run', 'walking': 'walk', 'strolling': 'walk',
           'woodland': 'forest', 'woods': 'forest', 'woodlands': 'forest',
           'grassland': 'savanna', 'resting': 'rest', 'swimming': 'swim',
           'side angle': 'side', 'daytime': 'daylight'}


def canonical(value):
    if isinstance(value, dict):
        return {str(k): canonical(v) for k, v in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [canonical(v) for v in value]
    if isinstance(value, str):
        value = re.sub(r'\s+', ' ', value.replace('_', ' ').replace('-', ' ').strip().lower())
        return ALIASES.get(value, value)
    return value


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def fingerprint(plan):
    # Timestamp, labels, run IDs and seed cannot disguise an identical scene.
    return digest(canonical({k: plan[k] for k in FIELDS if k != 'seed'}))


def perceptual_hash(image):
    from PIL import Image
    pixels = list(image.convert('L').resize((9, 8), Image.Resampling.LANCZOS).tobytes())
    bits = [pixels[y * 9 + x] > pixels[y * 9 + x + 1] for y in range(8) for x in range(8)]
    return ''.join(format(sum(int(bits[i + j]) << j for j in range(4)), 'x') for i in range(0, 64, 4))


def file_fingerprint(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def similarity(a, b):
    a, b = canonical(a), canonical(b)
    return sum(weight for field, weight in WEIGHTS.items()
               if a.get(field) == b.get(field)) / sum(WEIGHTS.values())


def validate_plan(plan):
    if not isinstance(plan, dict) or any(k not in plan for k in FIELDS):
        raise ValueError('Incomplete generation plan')
    if type(plan['seed']) is not int or not 0 <= plan['seed'] < 2**63:
        raise ValueError('seed must be a nonnegative 63-bit integer')
    if any(not isinstance(plan[k], str) or not plan[k].strip() for k in FIELDS if k != 'seed'):
        raise ValueError('Plan dimensions must be nonempty strings')


def rejection(plan, records, threshold=.78, output_hash=None, visual_hashes=None):
    validate_plan(plan)
    if not math.isfinite(threshold) or not 0 < threshold <= 1:
        raise ValueError('similarity threshold must be in (0, 1]')
    p = canonical(plan)
    for record in records:
        old = record['plan']
        o = canonical(old)
        if fingerprint(plan) == record['fingerprint']:
            return 'duplicate content fingerprint'
        if plan['seed'] == old['seed']:
            return 'same seed'
        if all(p[k] == o[k] for k in ('species', 'action', 'environment')):
            return 'same animal/action/scene'
        if all(p[k] == o[k] for k in ('action', 'environment', 'camera_angle',
                                      'camera_movement', 'composition')):
            return 'same scene composition with cosmetic changes'
        score = similarity(plan, old)
        if score >= threshold:
            return f'semantic similarity {score:.3f} >= {threshold:.3f}'
        if output_hash and output_hash == record.get('output_hash'):
            return 'duplicate output fingerprint'
        if visual_hashes and record.get('visual_hashes'):
            prior = record['visual_hashes']
            if min(sum((int(a, 16) ^ int(b, 16)).bit_count() for a, b in zip(visual_hashes, order))
                   / len(visual_hashes) for order in (prior, list(reversed(prior)))) <= 10:
                return 'rendered sequence perceptually too similar'
    return None


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, path)
        if os.name == 'posix':
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextmanager
def file_lock(path):
    """Serialize cooperating local processes; CI also needs workflow concurrency."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as lock:
        if os.name == 'posix':
            import fcntl
            fcntl.flock(lock, fcntl.LOCK_EX)
        else:
            import msvcrt
            # Do not append one byte on every lock acquisition.
            if path.stat().st_size == 0:
                lock.write(b'0'); lock.flush()
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
        try:
            yield
        finally:
            if os.name == 'posix':
                fcntl.flock(lock, fcntl.LOCK_UN)
            else:
                lock.seek(0); msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)


TRANSITIONS = {'reserved': {'completed', 'failed'}, 'completed': {'publishing'},
               'publishing': {'published'}, 'published': set(), 'failed': set()}


def _valid_hex(value, length):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{' + str(length) + '}', value) is not None


def validate_record(record, previous=None):
    """Validate both live writes and journal replay; checksums alone are not a schema."""
    if not isinstance(record, dict) or not _valid_hex(record.get('id'), 32):
        raise ValueError('invalid reservation ID')
    validate_plan(record['plan'])
    if record.get('fingerprint') != fingerprint(record['plan']):
        raise ValueError('invalid fingerprint')
    status = record.get('status')
    if status not in TRANSITIONS:
        raise ValueError('invalid status')
    if not isinstance(record.get('generation_timestamp'), str):
        raise ValueError('missing generation timestamp')
    if previous is None:
        if status != 'reserved':
            raise ValueError('first event must reserve the generation')
    else:
        if status not in TRANSITIONS[previous['status']]:
            raise ValueError('invalid journal state transition')
        for key, value in previous.items():
            if key not in {'status', 'updated_at'} and record.get(key) != value:
                raise ValueError('immutable history value changed: ' + key)
    if status in {'completed', 'publishing', 'published'}:
        hashes = record.get('visual_hashes')
        if record.get('validated') is not True or not _valid_hex(record.get('output_hash'), 64):
            raise ValueError('unvalidated completed output')
        if not isinstance(hashes, list) or len(hashes) != 3 or not all(_valid_hex(h, 16) for h in hashes):
            raise ValueError('invalid rendered hashes')
    if status == 'published' and (not isinstance(record.get('video_id'), str) or not record['video_id'].strip()):
        raise ValueError('missing confirmed video ID')


class HistoryStore:
    """All read/check/write transactions take an OS lock, including concurrent runs.

    A damaged snapshot is recoverable from the complete journal. A damaged,
    missing (after initialization) or detectably truncated journal blocks work.
    Checksums detect accidental damage, not malicious rewriting. Loss/rollback
    of ALL ledger files together cannot be detected without an external backup.
    Pending/failed/uncertain records remain barriers, not completed generations.
    """
    def __init__(self, directory):
        self.directory = Path(directory)
        self.snapshot = self.directory / 'unique_animal_history.json'
        self.journal = self.directory / 'unique_animal_history.jsonl'
        self.marker = self.directory / 'unique_animal_history.initialized'
        self.lock = self.directory / 'unique_animal_history.lock'

    @contextmanager
    def transaction(self):
        with file_lock(self.lock):
            yield

    def _read(self):
        records, previous, events = {}, '0' * 64, 0
        heads = {0: previous}
        if not self.journal.exists():
            if self.marker.exists() or self.snapshot.exists():
                raise HistoryError('Missing uniqueness journal; restore it from git/backup, never reset')
            return [], previous, events
        try:
            raw = self.journal.read_bytes()
            if not raw or not raw.endswith(b'\n'):
                raise ValueError('empty or interrupted journal write')
            for line in raw.splitlines():
                event = json.loads(line)
                if not isinstance(event, dict) or type(event.get('sequence')) is not int:
                    raise ValueError('invalid journal event')
                check = event.pop('checksum')
                if check != digest(event) or event['previous'] != previous or event['sequence'] != events + 1:
                    raise ValueError('invalid journal checksum/sequence')
                record = event['record']
                if not isinstance(record, dict):
                    raise ValueError('invalid record')
                validate_record(record, records.get(record.get('id')))
                records[record['id']] = record
                previous, events = check, events + 1
                heads[events] = check
            if self.marker.exists():
                head = json.loads(self.marker.read_text())
                if (not isinstance(head, dict) or type(head.get('sequence')) is not int
                        or head['sequence'] not in heads or head.get('head') != heads[head['sequence']]):
                    raise ValueError('journal rolled back behind durable head')
        except (ValueError, KeyError, TypeError, OSError) as exc:
            raise HistoryError('Corrupt uniqueness journal/head; restore trusted history, refusing to forget') from exc
        return list(records.values()), previous, events

    def _snapshot(self, records, head, sequence):
        atomic_json(self.snapshot, {'version': 1, 'head': head, 'sequence': sequence,
                                   'species_usage': dict(Counter(r['plan']['species'] for r in records)),
                                   'records': records})
        atomic_json(self.marker, {'sequence': sequence, 'head': head})

    def records(self):
        with self.transaction():
            records, head, seq = self._read()
            if seq:
                self._snapshot(records, head, seq)
            return records

    def _append(self, record, records, head, seq):
        event = {'sequence': seq + 1, 'previous': head, 'record': record}
        event['checksum'] = digest(event)
        with self.journal.open('ab') as f:
            f.write((json.dumps(event, sort_keys=True, separators=(',', ':')) + '\n').encode())
            f.flush(); os.fsync(f.fileno())
        records = [r for r in records if r['id'] != record['id']] + [record]
        self._snapshot(records, event['checksum'], seq + 1)

    def reserve(self, plan, threshold=.78):
        # Detach mutable caller dictionaries before checks and durable writes.
        plan = json.loads(json.dumps(plan, allow_nan=False))
        with self.transaction():
            records, head, seq = self._read()
            reason = rejection(plan, records, threshold)
            if reason:
                raise DiversityError(reason)
            record = {'id': secrets.token_hex(16), 'plan': plan, 'fingerprint': fingerprint(plan),
                      'status': 'reserved', 'generation_timestamp': datetime.now(timezone.utc).isoformat()}
            self._append(record, records, head, seq)
            return record['id']

    def transition(self, identifier, status, threshold=.78, **values):
        if set(values) - {'validated', 'output_hash', 'visual_hashes', 'file', 'video_id', 'reason'}:
            raise HistoryError('Immutable generation identity cannot be overwritten')
        with self.transaction():
            records, head, seq = self._read()
            record = next((r for r in records if r['id'] == identifier), None)
            if record is None:
                raise HistoryError('Unknown generation reservation')
            if status not in TRANSITIONS[record['status']]:
                raise HistoryError(f'Unsafe state transition {record["status"]} -> {status}')
            if status == 'completed':
                if values.get('validated') is not True or not _valid_hex(values.get('output_hash'), 64):
                    raise HistoryError('Completion requires validation and actual output hash')
                hashes = values.get('visual_hashes', [])
                if not isinstance(hashes, list) or len(hashes) != 3 or not all(_valid_hex(h, 16) for h in hashes):
                    raise HistoryError('Completion requires three rendered perceptual hashes')
                reason = rejection(record['plan'], [r for r in records if r['id'] != identifier],
                                   threshold, values['output_hash'], hashes)
                if reason:
                    raise DiversityError(reason)
            if status == 'published' and not values.get('video_id'):
                raise HistoryError('Published requires a confirmed video ID')
            updated = {**record, **values, 'status': status,
                       'updated_at': datetime.now(timezone.utc).isoformat()}
            try:
                validate_record(updated, record)
            except (ValueError, KeyError, TypeError) as exc:
                raise HistoryError(str(exc)) from exc
            self._append(updated, records, head, seq)


def checkpoint_git(root, store):
    """Fail BEFORE upload unless intent is durably pushed on ephemeral CI runners."""
    if os.environ.get('UNIQUE_HISTORY_GIT') != '1':
        if os.environ.get('GITHUB_ACTIONS') == 'true':
            raise HistoryError('CI publishing requires UNIQUE_HISTORY_GIT=1')
        return
    paths = [str(p.relative_to(root)) for p in (store.journal, store.snapshot, store.marker)]
    def run(*args):
        return subprocess.run(['git', *args], cwd=root, check=True, capture_output=True, text=True, timeout=120)
    staged = run('diff', '--cached', '--name-only', '--relative').stdout.splitlines()
    if set(staged) - set(paths):
        raise HistoryError('Refusing to commit unrelated staged files during history checkpoint')
    run('add', '--', *paths)
    if run('diff', '--cached', '--name-only').stdout.strip():
        run('commit', '-m', 'Persist animal uniqueness checkpoint [skip ci]')
    run('pull', '--rebase', 'origin', 'main')
    run('push', 'origin', 'HEAD:main')


# Capability profiles, not a hard-coded five-animal rotation. New catalogue entries
# inherit safe class controls; uniqueness_profile overrides narrow species ecology.
PROFILES = {
    'quadruped': (['forest', 'savanna', 'mountain'], ['walk', 'run', 'rest']),
    'aquatic': (['ocean', 'reef', 'kelp'], ['swim', 'glide', 'hover']),
    'cephalopod': (['ocean', 'reef', 'kelp'], ['swim', 'glide', 'hover']),
    'crustacean': (['reef', 'beach', 'rockpool'], ['scuttle', 'rest', 'explore']),
    'reptile': (['desert', 'rocks', 'forest'], ['crawl', 'rest', 'explore']),
    'serpent': (['forest', 'desert', 'rocks'], ['slither', 'rest', 'explore']),
    'arachnid': (['desert', 'rocks', 'forest'], ['scuttle', 'rest', 'explore']),
    'insect': (['forest', 'meadow', 'garden'], ['crawl', 'rest', 'explore']),
    'bird': (['forest', 'meadow', 'mountain'], ['walk', 'rest', 'explore']),
    'amphibian': (['river', 'forest', 'rockpool'], ['crawl', 'rest', 'explore']),
}
SCENES = ('forest', 'savanna', 'mountain', 'ocean', 'reef', 'kelp', 'beach',
          'rockpool', 'desert', 'rocks', 'meadow', 'garden', 'river', 'snow', 'farm', 'indoor')


def profile_for(species):
    name = species['name'].lower()
    words = set(re.findall(r'[a-z]+', name))
    cls = species.get('class_type', 'quadruped')
    scenes, actions = PROFILES.get(cls, PROFILES['quadruped'])
    # Explicit aquatic taxonomy wins over misleading name fragments: seahorse
    # is not a horse, cowfish is not a cow and lionfish is not a lion.
    if cls == 'aquatic' or any(x in name for x in ('sea turtle', 'whale', 'dolphin', 'shark')):
        scenes, actions = PROFILES['aquatic']
    elif any(x in name for x in ('polar', 'arctic', 'snow leopard', 'penguin')):
        scenes = ['snow', 'mountain']
    elif cls == 'quadruped' and 'lion' in words:
        scenes = ['savanna', 'rocks']
    elif cls == 'quadruped' and 'tiger' in words:
        scenes = ['forest', 'river']
    elif 'leopard gecko' in name or 'redknee' in name:
        scenes = ['desert', 'rocks']
    elif cls in {'quadruped', 'bird'} and words.intersection({'cow', 'sheep', 'chicken', 'horse'}):
        scenes = ['farm', 'meadow']
    override = species.get('uniqueness_profile', {})
    scenes, actions = override.get('environments', scenes), override.get('actions', actions)
    if not scenes or not actions or any(s not in SCENES for s in scenes):
        raise ValueError('Invalid/unsupported species habitat profile')
    if any(a not in {'walk', 'run', 'rest', 'swim', 'glide', 'hover', 'scuttle', 'crawl', 'explore', 'slither'} for a in actions):
        raise ValueError('Unsupported action: add renderer capability before enabling it')
    return scenes, actions


class UniqueAnimalGenerationSkill:
    def __init__(self, store, threshold=None, max_retries=None):
        self.store = store
        self.threshold = float(threshold if threshold is not None else os.getenv('ANIMAL_SIMILARITY_THRESHOLD', '.78'))
        self.max_retries = int(max_retries if max_retries is not None else os.getenv('ANIMAL_UNIQUE_MAX_RETRIES', '48'))
        if not math.isfinite(self.threshold) or not 0 < self.threshold <= 1 or not 1 <= self.max_retries <= 10000:
            raise ValueError('Invalid diversity threshold/retry configuration')
        self.last_rejections = []

    def candidates(self, catalogue, records):
        counts = Counter(canonical(r['plan']['species']) for r in records)
        last_use = {canonical(r['plan']['species']): i for i, r in enumerate(records)}
        recent = records[-20:]
        ordered = sorted(catalogue, key=lambda s: (counts[canonical(s['name'])],
                          s.get('rotation_penalty', 0), last_use.get(canonical(s['name']), -1), s['name']))
        if not ordered:
            return
        # Each retry explores the next least-used species before cycling back.
        for attempt in range(self.max_retries):
            species = ordered[attempt % len(ordered)]
            scenes, actions = profile_for(species)
            def choose(field, options, offset=0):
                def prior_value(record):
                    value = record['plan'].get(field)
                    if field == 'color_pattern' and isinstance(value, str):
                        value = value.split('; ')[-1]
                    return canonical(value)
                ordered_values = sorted(options, key=lambda v: (
                    sum(prior_value(r) == canonical(v) for r in recent),
                    sum(prior_value(r) == canonical(v) for r in records), str(v)))
                return ordered_values[(attempt // len(ordered) + offset) % len(ordered_values)]
            environment = choose('environment', scenes)
            action = choose('action', actions)
            aquatic = environment in {'ocean', 'reef', 'kelp', 'rockpool'}
            color = species.get('body_colors') or species.get('accent') or 'natural species palette'
            plan = {
                'species': species['name'], 'subspecies': species.get('subspecies', species.get('breed', 'unspecified')),
                'age': 'adult', 'size': choose('size', ['standard', 'compact']),
                'body_appearance': species.get('morphology', species.get('class_type', 'natural anatomy')),
                'color_pattern': f'{color}; ' + choose('color_pattern', ['natural', 'warm natural', 'cool natural']),
                'pose': 'neutral resting' if action == 'rest' else 'locomotion',
                'action': action, 'expression': 'neutral species anatomy',
                'camera_angle': choose('camera_angle', ['side', 'front oblique', 'high angle', 'low angle'] if species.get('resolved_renderer') == '3d' else ['high angle']),
                'camera_movement': choose('camera_movement', ['static', 'tracking', 'orbit'] if species.get('resolved_renderer') == '3d' else ['static', 'tracking']),
                'environment': environment,
                'lighting': choose('lighting', ['daylight', 'sunrise', 'sunset', 'moonlight']),
                'weather': 'underwater' if aquatic else choose('weather', ['clear', 'cloudy', 'fog', 'wind']),
                'props': choose('props', ['rocks', 'plants']),
                'animation': action,
                'story': choose('story', ['enter traverse pause', 'pause traverse exit', 'traverse pause return']),
                'composition': choose('composition', ['left third', 'center', 'right third']),
                'seed': secrets.randbits(63),
            }
            # Among several controlled layouts minimize worst historical similarity.
            alternatives = []
            for scene in scenes:
                for behavior in actions:
                    variant = {**plan, 'environment': scene, 'action': behavior, 'animation': behavior,
                               'pose': 'neutral resting' if behavior == 'rest' else 'locomotion',
                               'weather': 'underwater' if scene in {'ocean', 'reef', 'kelp', 'rockpool'} else choose('weather', ['clear', 'cloudy', 'fog', 'wind'])}
                    reason = rejection(variant, records, self.threshold)
                    score = max((similarity(variant, r['plan']) for r in records), default=0)
                    recency = sum(r['plan']['environment'] == scene or r['plan']['action'] == behavior for r in recent)
                    alternatives.append((bool(reason), score, recency, variant))
            yield species, min(alternatives, key=lambda x: x[:3])[3]

    def select(self, catalogue, validator=None):
        records = self.store.records()
        self.last_rejections = []
        for species, plan in self.candidates(catalogue, records):
            reason = rejection(plan, records, self.threshold)
            if not reason and validator is not None:
                # Validator exceptions never mean success.
                try:
                    if not validator(apply_plan(species, plan)):
                        reason = 'existing visual guard rejected candidate'
                except Exception as exc:
                    reason = f'visual validation error: {exc}'
            if not reason:
                self.attempts_used = len(self.last_rejections) + 1
                return species, plan
            self.last_rejections.append(reason)
        raise DiversityError(f'No unique candidate after {len(self.last_rejections)} / {self.max_retries} attempts; '
                             + '; '.join(self.last_rejections[-5:] or ['no eligible species']))


def apply_plan(species, plan):
    validate_plan(plan)
    return {**species, 'unique_plan': plan, 'generation_seed': plan['seed']}
