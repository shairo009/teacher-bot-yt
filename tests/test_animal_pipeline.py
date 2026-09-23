"""Offline regressions. Run: python -m unittest discover -s tests -v"""
from contextlib import ExitStack
import hashlib
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image
from src import animal_short_generator as pipeline
from src import animal_researcher as researcher
from src.animal_3d_renderer import (SUPPORTED_SPECIES, configure_species,
                                    render_animal_layer, build_rig, supports_species)
from src.generative_dragon_engine import (get_species_for_id, render_generative_frame,
                                         solve_forelimb_ik, solve_ik_2joint, solve_ik_3segment)
from src.sound_engine import generate_reel_audio
from src import quality_auditor as auditor
from src import unique_animal_generation_skill as unique


class HabitatProfileTests(unittest.TestCase):
    def test_aquatic_catalog_cannot_be_redirected_by_name_fragments(self):
        catalog = json.loads((pipeline.ROOT / 'data' / 'animal_encyclopedia.json').read_text())
        checked = 0
        for idx in range(len(catalog)):
            species = get_species_for_id(idx)
            if species.get('class_type') != 'aquatic':
                continue
            with self.subTest(species=species['name']):
                self.assertEqual(unique.profile_for(species), unique.PROFILES['aquatic'])
                checked += 1
        self.assertGreater(checked, 50)

    def test_seahorse_cowfish_and_lionfish_keep_aquatic_habitats(self):
        for name in ('PACIFIC SEAHORSE', 'LONGHORN COWFISH', 'RED LIONFISH', 'TIGER BARB'):
            with self.subTest(species=name):
                self.assertEqual(unique.profile_for({'name': name, 'class_type': 'aquatic'}),
                                 unique.PROFILES['aquatic'])

    def test_terrestrial_word_overrides_do_not_match_other_classes(self):
        for name, cls in (('HORSESHOE CRAB', 'crustacean'), ('ANTLION', 'insect'),
                          ('TIGER BEETLE', 'insect'), ('CHICKEN TURTLE', 'reptile')):
            with self.subTest(species=name):
                self.assertEqual(unique.profile_for({'name': name, 'class_type': cls}),
                                 unique.PROFILES[cls])
        for name, cls in (('DOMESTIC HORSE', 'quadruped'), ('DOMESTIC COW', 'quadruped'),
                          ('DOMESTIC CHICKEN', 'bird')):
            with self.subTest(species=name):
                self.assertEqual(unique.profile_for({'name': name, 'class_type': cls})[0],
                                 ['farm', 'meadow'])

    def test_seahorse_plan_has_underwater_weather_without_rewriting_history(self):
        with tempfile.TemporaryDirectory() as folder:
            store = unique.HistoryStore(folder)
            skill = unique.UniqueAnimalGenerationSkill(store, max_retries=1)
            species = configure_species(get_species_for_id(306))
            _, first = skill.select([species])
            self.assertIn(first['environment'], unique.PROFILES['aquatic'][0])
            self.assertEqual(first['weather'], 'underwater')
            store.reserve(first, skill.threshold)
            before = store.records()
            # The old plan remains a barrier even after the habitat repair.
            self.assertEqual(unique.rejection(first, before), 'duplicate content fingerprint')
            _, second = skill.select([species])
            self.assertNotEqual(first['environment'], second['environment'])
            self.assertEqual(second['weather'], 'underwater')
            self.assertEqual(store.records(), before)


class WorkflowTests(unittest.TestCase):
    """Local YAML/shell checks, not a substitute for GitHub Actions execution."""
    @classmethod
    def setUpClass(cls):
        import yaml
        cls.workflows = {}
        folder = Path(__file__).resolve().parents[1] / '.github' / 'workflows'
        for name in ('generate.yml', 'generate_real_draw.yml'):
            # BaseLoader keeps the YAML 1.2 key `on` rather than coercing it to True.
            cls.workflows[name] = yaml.load((folder / name).read_text(), Loader=yaml.BaseLoader)

    def jobs(self):
        for filename, workflow in self.workflows.items():
            for job in workflow['jobs'].values():
                yield filename, workflow, job

    def test_manual_previews_are_default_and_publishing_is_opt_in(self):
        for filename, workflow, job in self.jobs():
            with self.subTest(workflow=filename):
                option = workflow['on']['workflow_dispatch']['inputs']['dry_run']
                self.assertEqual(option['type'], 'boolean')
                self.assertEqual(option['default'], 'true')
                variable = ('ENABLE_ANIMAL_PUBLISH' if filename == 'generate.yml'
                            else 'ENABLE_REAL_DRAW_PUBLISH')
                self.assertEqual(job['if'], "${{ inputs.dry_run || vars." + variable + " == 'true' }}")
                self.assertEqual(workflow['concurrency']['cancel-in-progress'], 'false')

    def test_preview_credentials_are_not_injected(self):
        for filename, _, job in self.jobs():
            generation = next(s for s in job['steps'] if 'DRY_RUN' in s.get('env', {}))
            with self.subTest(workflow=filename):
                self.assertEqual(generation['env']['DRY_RUN'],
                                 "${{ inputs.dry_run && 'true' || 'false' }}")
                for secret in ('TOKEN_JSON', 'CLIENT_SECRETS_JSON'):
                    self.assertEqual(generation['env'][secret],
                                     "${{ !inputs.dry_run && secrets." + secret + " || '' }}")
                self.assertNotIn('secrets.', str(job.get('env', {})))

    def test_checkout_main_and_rebase_before_every_push(self):
        for filename, _, job in self.jobs():
            with self.subTest(workflow=filename):
                checkout = next(s for s in job['steps'] if s.get('uses', '').startswith('actions/checkout@'))
                self.assertEqual(checkout['with'], {'ref': 'main', 'fetch-depth': '0'})
                for step in job['steps']:
                    script = step.get('run', '')
                    if 'git push' in script:
                        self.assertIn('!inputs.dry_run', step['if'])
                        self.assertLess(script.index('git pull --rebase origin main'),
                                        script.index('git push origin HEAD:main'))

    def test_all_workflow_shell_blocks_parse(self):
        import re
        import subprocess
        for filename, _, job in self.jobs():
            for step in job['steps']:
                if 'run' not in step:
                    continue
                with self.subTest(workflow=filename, step=step['name']):
                    script = re.sub(r'\$\{\{.*?\}\}', 'TEST_VALUE', step['run'])
                    result = subprocess.run(['bash', '-n'], input=script, text=True,
                                            capture_output=True, timeout=5)
                    self.assertEqual(result.returncode, 0, result.stderr)

    def test_user_input_is_literal_and_preview_flags_are_present(self):
        import os
        import subprocess
        import sys
        # Shadow only the generation command with an argv recorder. No generator,
        # credentials, network, git, installer or workflow service is invoked.
        recorder = ('python() { "$TEST_PYTHON" -c '
                    "'import json,sys; print(json.dumps(sys.argv[1:]))' \"$@\"; }\n")
        for filename, _, job in self.jobs():
            step = next(s for s in job['steps'] if 'DRY_RUN' in s.get('env', {}))
            for dry_run in ('true', 'false'):
                with self.subTest(workflow=filename, dry_run=dry_run), tempfile.TemporaryDirectory() as folder:
                    hostile = 'Tiger $(exit 37); touch SHOULD_NOT_EXIST " spaced'
                    env = {'PATH': os.environ['PATH'], 'TEST_PYTHON': sys.executable,
                           'DRY_RUN': dry_run, 'ANIMAL_ID': hostile, 'TOPIC': hostile,
                           'DURATION': '3', 'RENDERER': '3d', 'QUALITY': 'standard'}
                    result = subprocess.run(['bash', '-euo', 'pipefail', '-c', recorder + step['run']],
                                            env=env, cwd=folder, text=True, capture_output=True, timeout=5)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    args = json.loads(result.stdout.strip().splitlines()[-1])
                    self.assertEqual(args.count(hostile), 1)
                    self.assertEqual('--dry-run' in args, dry_run == 'true')
                    if filename == 'generate.yml':
                        self.assertEqual('--no-research' in args, dry_run == 'true')
                    self.assertFalse((Path(folder) / 'SHOULD_NOT_EXIST').exists())

    def test_animal_durable_checkpoint_configuration(self):
        job = self.workflows['generate.yml']['jobs']['generate-animal-short']
        steps = job['steps']
        generate = next(s for s in steps if 'DRY_RUN' in s.get('env', {}))
        self.assertEqual(generate['env']['UNIQUE_HISTORY_GIT'], '1')
        identity = next(s for s in steps if s['name'] == 'Configure durable history commits')
        self.assertLess(steps.index(identity), steps.index(generate))
        self.assertIn('git config user.name', identity['run'])
        self.assertIn('!inputs.dry_run', identity['if'])
        save = next(s for s in steps if s['name'] == 'Save durable history and confirmed upload state')
        self.assertEqual(save['if'], '${{ always() && !inputs.dry_run }}')
        for suffix in ('json', 'jsonl', 'initialized'):
            self.assertIn('data/unique_animal_history.' + suffix, save['run'])

    def test_both_workflows_run_regressions_before_generation(self):
        for filename, _, job in self.jobs():
            with self.subTest(workflow=filename):
                steps = job['steps']
                check = next(s for s in steps if s.get('run') == 'python -m unittest discover -s tests -v')
                generate = next(s for s in steps if 'DRY_RUN' in s.get('env', {}))
                self.assertLess(steps.index(check), steps.index(generate))


class RendererTests(unittest.TestCase):
    def test_supported_rigs_are_nonempty_rgba(self):
        for name in SUPPORTED_SPECIES:
            with self.subTest(name=name):
                image = render_animal_layer({'name': name}, 1, (280, 180), 'draft')
                self.assertEqual(image.mode, 'RGBA')
                self.assertEqual(image.size, (280, 180))
                alpha = np.asarray(image)[..., 3]
                self.assertGreater(np.count_nonzero(alpha), 500)
                self.assertLess(np.count_nonzero(alpha), alpha.size*0.8)

    def test_unsupported_3d_refuses_generic_substitution(self):
        with self.assertRaisesRegex(ValueError, 'No 3D rig'):
            configure_species({'name': 'GIRAFFE', 'renderer': '3d'})
        self.assertEqual(configure_species({'name': 'GIRAFFE'})['resolved_renderer'], '2d')

    def test_explicit_2d_retained(self):
        self.assertEqual(configure_species({'name': 'TIGER', 'renderer': '2d'})['resolved_renderer'], '2d')

    def test_auto_3d_and_truthful_labels(self):
        result = configure_species(get_species_for_id(1))
        self.assertEqual(result['resolved_renderer'], '3d')
        self.assertEqual(result['file_name'], 'animal_3d_renderer.py')
        self.assertNotIn('JavaScript', result['yt_title'])

    def test_truthful_metadata_in_both_modes(self):
        for renderer in ('2d', '3d'):
            result = configure_species({**get_species_for_id(1), 'renderer': renderer})
            self.assertNotIn('JavaScript', result['yt_title'])
            self.assertNotIn('javascript', result['yt_tags'])
            self.assertIn('python', result['yt_tags'])
            self.assertIn(renderer, result['yt_title'].lower())

    def test_deterministic_out_of_order_sampling(self):
        a = render_animal_layer({'name': 'TIGER'}, 1, (240, 160), 'draft')
        render_animal_layer({'name': 'TIGER'}, 7, (240, 160), 'draft')
        b = render_animal_layer({'name': 'TIGER'}, 1, (240, 160), 'draft')
        self.assertEqual(a.tobytes(), b.tobytes())

    def test_camera_rotation_changes_depth_view(self):
        a = render_animal_layer({'name': 'TIGER'}, 1, (240, 160), 'draft', yaw=-0.8)
        b = render_animal_layer({'name': 'TIGER'}, 1, (240, 160), 'draft', yaw=0.8)
        self.assertNotEqual(a.tobytes(), b.tobytes())

    def test_rigs_animate(self):
        for kind in SUPPORTED_SPECIES.values():
            with self.subTest(kind=kind):
                a, b = build_rig(kind, 0), build_rig(kind, 1)
                self.assertEqual(len(a), len(b))
                self.assertTrue(any(not np.array_equal(p.center, q.center) for p, q in zip(a, b)))
                self.assertTrue(all(np.all(p.radii > 0) for p in a))

    def test_compositor_dimensions(self):
        image = render_generative_frame(get_species_for_id(1), 0, 30)
        self.assertEqual(image.mode, 'RGB')
        self.assertEqual(image.size, (1080, 1920))

    def test_invalid_frame_and_quality(self):
        with self.assertRaises(ValueError):
            render_generative_frame(get_species_for_id(1), 0, 0)
        with self.assertRaises(ValueError):
            render_animal_layer({'name': 'TIGER'}, 0, quality='unknown')

    def test_zero_distance_ik_is_finite(self):
        for solve in (solve_forelimb_ik, solve_ik_2joint):
            result = solve((0, 0), (0, 0), 10, 10, 1)
            self.assertTrue(all(math.isfinite(v) for point in result for v in point))
        result = solve_ik_3segment((0, 0), (0, 0), 10, 10, 10, 1)
        self.assertTrue(all(math.isfinite(v) for point in result for v in point))

    def test_invalid_ik_lengths(self):
        with self.assertRaises(ValueError):
            solve_forelimb_ik((0, 0), (0, 0), 0, 10, 1)


class GenericRendererTests(unittest.TestCase):
    """Exercise the catalog expansion, not just the five dedicated rigs."""
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parents[1] / 'data' / 'animal_encyclopedia.json'
        cls.catalog = json.loads(path.read_text())
        cls.profiles = {}
        for species in cls.catalog:
            cls.profiles.setdefault(species['morphology'], species)

    def rig(self, morphology, seconds=0):
        species = self.profiles[morphology]
        return build_rig(morphology, seconds, species)

    def test_all_687_catalog_rigs_have_finite_positive_geometry(self):
        self.assertEqual(len(self.catalog), 687)
        for species in self.catalog:
            with self.subTest(species=species['name']):
                self.assertTrue(supports_species(species))
                self.assertEqual(configure_species(species)['resolved_renderer'], '3d')
                parts = build_rig(species['morphology'], .7, species)
                self.assertTrue(parts)
                for part in parts:
                    self.assertTrue(np.isfinite(part.center).all())
                    self.assertTrue(np.isfinite(part.basis).all())
                    self.assertTrue(np.isfinite(part.radii).all())
                    self.assertTrue((part.radii > 0).all())
                    np.testing.assert_allclose(part.basis.T @ part.basis, np.eye(3), atol=1e-5)

    def test_every_morphology_animates_geometry_not_just_camera(self):
        for morph in self.profiles:
            with self.subTest(morphology=morph):
                a, b = self.rig(morph, 0), self.rig(morph, .73)
                self.assertEqual(len(a), len(b))
                self.assertTrue(any(not np.array_equal(p.center, q.center) or
                                    not np.array_equal(p.basis, q.basis) or
                                    not np.array_equal(p.radii, q.radii)
                                    for p, q in zip(a, b)))

    def test_each_morphology_renders_visible_rgba(self):
        for morph, species in self.profiles.items():
            with self.subTest(morphology=morph):
                image = render_animal_layer(species, .7, (240, 160), 'draft', yaw=-.35)
                self.assertEqual(image.mode, 'RGBA')
                self.assertGreater(np.count_nonzero(np.asarray(image)[..., 3] > 200), 150)

    def test_cephalopods_have_arms_not_quadruped_feet(self):
        for morph in ('octopus', 'squid', 'cuttlefish'):
            with self.subTest(morphology=morph):
                roles = [p.role for p in self.rig(morph)]
                self.assertEqual(roles.count('mantle'), 1)
                self.assertEqual(roles.count('arm'), 8*8)
                self.assertEqual(roles.count('tentacle'), 0 if morph == 'octopus' else 2*8)
                self.assertNotIn('foot', roles)
                self.assertNotIn('leg_upper', roles)

    def test_jellyfish_has_bell_tentacles_and_no_fish_parts(self):
        roles = [p.role for p in self.rig('jellyfish')]
        self.assertEqual(roles.count('bell'), 1)
        self.assertEqual(roles.count('tentacle'), 12*8)
        self.assertNotIn('fin', roles)
        self.assertNotIn('foot', roles)

    def test_dedicated_name_not_morphology_controls_rig_dispatch(self):
        for morph, exact in (('turtle', 'GREEN SEA TURTLE'),
                             ('spider', 'MEXICAN REDKNEE TARANTULA')):
            species = next(s for s in self.catalog if s['morphology'] == morph and s['name'] != exact)
            a = build_rig(morph, 0, species)
            b = build_rig(morph, 0, {'name': exact})
            self.assertNotEqual(len(a), len(b))
            self.assertTrue(any(p.role != 'body' for p in a))
            direct = build_rig(SUPPORTED_SPECIES[exact], 0)
            self.assertEqual(len(b), len(direct))
            for p, q in zip(b, direct):
                np.testing.assert_array_equal(p.center, q.center)

    def test_arthropod_limb_counts_and_claws(self):
        for morph, count in (('beetle', 6), ('spider', 8), ('scorpion', 8),
                             ('crab', 8), ('lobster', 8), ('shrimp', 10)):
            with self.subTest(morphology=morph):
                # Explicit non-dedicated metadata avoids the exact tarantula rig.
                roles = [p.role for p in build_rig(morph, 0, {'name': 'TEST', 'morphology': morph})]
                self.assertEqual(roles.count('leg_upper'), count)
                self.assertEqual(roles.count('leg_lower'), count)
                self.assertEqual(roles.count('claw'), 2 if morph in {'scorpion', 'crab', 'lobster'} else 0)

    def test_elephant_and_rhino_distinctive_anatomy(self):
        elephant = self.rig('elephant')
        self.assertEqual(sum(p.role == 'trunk' for p in elephant), 12)
        self.assertEqual(sum(p.role == 'tusk' for p in elephant), 2)
        horns = [p for p in self.rig('rhino') if p.role == 'nasal_horn']
        self.assertEqual(len(horns), 2)
        self.assertTrue(all(p.center[1] == 0 for p in horns))
        self.assertFalse(any(p.role == 'horn' for p in self.rig('rhino')))

    def test_marine_mammal_has_horizontal_flukes(self):
        flukes = [p for p in self.rig('marine_mammal') if p.role == 'fluke']
        self.assertEqual(len(flukes), 2)
        self.assertTrue(all(p.radii[1] > p.radii[2]*3 for p in flukes))

    def test_metadata_proportions_are_used_deterministically(self):
        species = {'name': 'TEST BIRD', 'morphology': 'bird'}
        a = build_rig('bird', .7, species)
        changed = {**species, 'bone_structure': {'skull': {'length': 42, 'width': 22}}}
        b = build_rig('bird', .7, changed)
        self.assertFalse(np.array_equal(a[0].radii, b[0].radii))
        first = render_animal_layer(changed, .7, (160, 120), 'draft')
        render_animal_layer(changed, 2, (160, 120), 'draft')
        self.assertEqual(first.tobytes(), render_animal_layer(changed, .7, (160, 120), 'draft').tobytes())

    def test_unknown_morphology_does_not_hide_behind_class(self):
        species = {'name': 'UNKNOWN', 'morphology': 'unknown_profile', 'class_type': 'quadruped'}
        self.assertFalse(supports_species(species))
        with self.assertRaises(ValueError):
            build_rig('unknown_profile', 0, species)
        with self.assertRaises(ValueError):
            configure_species({**species, 'renderer': '3d'})
        self.assertTrue(supports_species({'name': 'TEST', 'class_type': 'aquatic'}))
        self.assertTrue(supports_species({'name': 'TEST', 'morphology': ' Bird '}))
        self.assertFalse(supports_species({'morphology': 'bird'}))

    def test_nonfinite_motion_timestamp_fails_before_geometry(self):
        for timestamp in (float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                build_rig('bird', timestamp, self.profiles['bird'])


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.data = self.root/'data'
        self.data.mkdir()
        (self.data/'animal_encyclopedia.json').write_text(json.dumps([
            {'name': 'AFRICAN LION'}, {'name': 'TIGER'}]))
        self.stack = ExitStack()
        for name, path in {
            'ROOT': self.root, 'DATA_DIR': self.data, 'TMP_DIR': self.root/'tmp',
            'PROGRESS_FILE': self.data/'animal_progress.json',
            'HISTORY_FILE': self.data/'animal_history.json',
            'LAST_FRAME_FILE': self.data/'last_uploaded_frame.jpg',
            'RECENT_FRAMES_DIR': self.data/'recent_frames',
        }.items():
            self.stack.enter_context(patch.object(pipeline, name, path))
        self.stack.enter_context(patch.object(researcher, 'USED_FILE', self.data/'used_animals.json'))
        self.stack.enter_context(patch.object(unique, 'checkpoint_git'))
        self.stack.enter_context(patch.object(pipeline, '_has_upload_credentials', return_value=True))
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(self.stack.close)

    def write_json(self, name, value):
        (self.data/name).write_text(json.dumps(value))

    def snapshot(self, include_ledger=False):
        # Legacy uploaded-state must not advance on failed/unconfirmed work.
        # New production reservations are intentional durable safety barriers.
        return {str(p.relative_to(self.data)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.data.rglob('*') if p.is_file()
                and (include_ledger or (not p.name.startswith('unique_animal_history')
                                       and p.name != 'generation.lock'))}

    def fake_generation(self, dry_run=False, upload=None):
        frame = Image.new('RGB', (1080, 1920), (210, 150, 85))
        def encode(frames, output, audio):
            output.write_bytes(b'test-only-not-a-video')
        with patch.object(pipeline, 'render_generative_frame', return_value=frame), \
             patch.object(pipeline, 'verify_candidate_against_recent_buffer', return_value=(True, 100, 64)), \
             patch.object(pipeline, 'generate_reel_audio'), \
             patch.object(pipeline, '_encode_video', side_effect=encode), \
             patch.object(auditor, 'audit_video', return_value={
                 'passed': True, 'errors': [], 'metrics': {'visual_hashes': ['0'*16]*3}}), \
             patch.object(pipeline, '_upload_to_youtube', return_value=upload) as uploader:
            path = pipeline.generate(animal_id=1, duration=0.1, dry_run=dry_run,
                                     force_research=False, renderer='3d')
            if dry_run:
                uploader.assert_not_called()
            return path

    def test_unconfirmed_upload_keeps_legacy_state_and_blocks_retry(self):
        self.write_json('animal_progress.json', {'current_id': 42})
        before = self.snapshot()
        with self.assertRaisesRegex(pipeline.UploadUnconfirmedError, 'unconfirmed'):
            self.fake_generation(upload=None)
        self.assertEqual(len(list((self.root/'tmp').glob('reel_*/*.mp4'))), 1)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(unique.HistoryStore(self.data).records()[0]['status'], 'publishing')
        with self.assertRaisesRegex(RuntimeError, 'already used'):
            self.fake_generation(upload=None)

    def test_dry_run_never_uploads_or_changes_state(self):
        before = self.snapshot(include_ledger=True)
        self.fake_generation(dry_run=True)
        self.assertEqual(before, self.snapshot(include_ledger=True))
        records = unique.HistoryStore(self.root/'tmp'/'unique-preview-history').records()
        self.assertEqual(records[0]['status'], 'completed')

    def test_success_records_used_and_viewport_hash(self):
        self.fake_generation(upload='confirmed-test-id')
        self.assertTrue(researcher.is_already_used('TIGER'))
        history = json.loads(pipeline.HISTORY_FILE.read_text())
        self.assertEqual(history[-1]['dhash_scope'], pipeline.HASH_SCOPE)
        self.assertTrue(history[-1]['uploaded'])
        self.assertEqual(history[-1]['renderer'], '3d')
        self.assertTrue((pipeline.RECENT_FRAMES_DIR/'recent_0.jpg').exists())

    def test_new_reservation_does_not_reuse_or_delete_old_frames(self):
        folder = self.root/'tmp'/'reel_0001'/'frames'
        folder.mkdir(parents=True)
        (folder/'frame_0999.jpg').write_bytes(b'stale')
        (folder/'user-note.txt').write_text('keep')
        output = self.fake_generation(dry_run=True)
        self.assertEqual((folder/'frame_0999.jpg').read_bytes(), b'stale')
        self.assertTrue((folder/'user-note.txt').exists())
        self.assertNotEqual(output.parent, folder.parent)
        self.assertEqual(len(list((output.parent/'frames').glob('frame_*.jpg'))), 3)

    def test_registry_contributes_to_base_noun_guard(self):
        self.write_json('used_animals.json', {'used': ['volt_scorpion', 'african_lion']})
        self.assertIn('SCORPION', pipeline.get_used_base_nouns())
        self.assertIn('LION', pipeline.get_used_base_nouns())

    def test_forced_used_species_upload_is_rejected(self):
        self.write_json('used_animals.json', {'used': ['tiger']})
        with self.assertRaisesRegex(RuntimeError, 'already used'):
            pipeline.generate(animal_id=1, duration=0.1, force_research=False)

    def test_base_variant_upload_is_rejected(self):
        self.write_json('used_animals.json', {'used': ['white_tiger']})
        with self.assertRaisesRegex(RuntimeError, 'already used'):
            pipeline.generate(animal_id=1, duration=0.1, force_research=False)

    def test_exhausted_selection_has_no_unsafe_fallback(self):
        self.write_json('used_animals.json', {'used': ['white_tiger', 'african_lion']})
        with self.assertRaisesRegex(RuntimeError, 'No unused animal'):
            pipeline._find_next_unused_id(0)

    def test_render_verification_error_fails_closed(self):
        with patch.object(pipeline, 'render_generative_frame', side_effect=RuntimeError('render error')):
            self.assertEqual(pipeline.verify_candidate_against_recent_buffer({}), (False, 0, 0))

    def test_legacy_full_frame_hash_not_compared(self):
        image = Image.new('RGB', (1080, 1920), 'white')
        self.write_json('animal_history.json', [{'dhash': pipeline.compute_dhash(image)}])
        with patch.object(pipeline, 'render_generative_frame', return_value=image):
            self.assertTrue(pipeline.verify_candidate_against_recent_buffer({})[0])

    def test_matching_scoped_hash_rejected(self):
        image = Image.new('RGB', (1080, 1920), 'white')
        self.write_json('animal_history.json', [{'dhash': pipeline.compute_dhash(image.crop(pipeline.VIEWPORT_BOX)),
                                               'dhash_scope': pipeline.HASH_SCOPE}])
        with patch.object(pipeline, 'render_generative_frame', return_value=image):
            self.assertFalse(pipeline.verify_candidate_against_recent_buffer({})[0])

    def test_matching_recent_frame_rejected(self):
        image = Image.new('RGB', (1080, 1920), 'white')
        pipeline.RECENT_FRAMES_DIR.mkdir()
        image.save(pipeline.RECENT_FRAMES_DIR/'recent_0.jpg')
        with patch.object(pipeline, 'render_generative_frame', return_value=image):
            self.assertFalse(pipeline.verify_candidate_against_recent_buffer({})[0])

    def test_corrupt_recent_frame_fails_closed(self):
        pipeline.RECENT_FRAMES_DIR.mkdir()
        (pipeline.RECENT_FRAMES_DIR/'recent_0.jpg').write_bytes(b'broken')
        with patch.object(pipeline, 'render_generative_frame', return_value=Image.new('RGB', (1080, 1920))):
            self.assertFalse(pipeline.verify_candidate_against_recent_buffer({})[0])

    def test_invalid_hash_not_accepted_as_novel(self):
        self.assertEqual(pipeline.hamming_distance('invalid', '0000'), 0)

    def test_wrong_width_hashes_fail_closed(self):
        for invalid in ('f', 'f'*17, '-ffffffffffffffff', 'g'*16, None, 42):
            with self.subTest(invalid=invalid):
                self.assertEqual(pipeline.hamming_distance(invalid, '0'*16), 0)
        self.assertEqual(pipeline.hamming_distance('f'*16, '0'*16), 64)

    def test_corrupt_registry_blocks_upload_before_render(self):
        (self.data/'used_animals.json').write_text('{broken')
        before = self.snapshot()
        with patch.object(pipeline, 'render_generative_frame') as render, \
             patch.object(pipeline, '_upload_to_youtube') as upload:
            with self.assertRaisesRegex(RuntimeError, 'used_animals.json'):
                pipeline.generate(animal_id=1, duration=0.1, force_research=False)
            render.assert_not_called()
            upload.assert_not_called()
        self.assertEqual(before, self.snapshot())

    def test_invalid_registry_structure_blocks_mark_used(self):
        for value in ([], {}, {'used': 'tiger'}, {'used': [None]}, {'used': ['']}):
            with self.subTest(value=value):
                self.write_json('used_animals.json', value)
                before = self.snapshot()
                with self.assertRaisesRegex(RuntimeError, 'used_animals.json'):
                    researcher.mark_used('TIGER')
                self.assertEqual(before, self.snapshot())

    def test_registry_normalizes_existing_names(self):
        self.write_json('used_animals.json', {'used': ['TIGER', 'African Lion']})
        self.assertTrue(researcher.is_already_used('tiger'))
        self.assertIn('LION', pipeline.get_used_base_nouns())

    def test_corrupt_history_blocks_duplicate_guard_and_visual_guard(self):
        (self.data/'animal_history.json').write_text('{broken')
        with self.assertRaisesRegex(RuntimeError, 'animal_history.json'):
            pipeline.get_used_base_nouns()
        with patch.object(pipeline, 'render_generative_frame', return_value=Image.new('RGB', (1080, 1920))):
            self.assertEqual(pipeline.verify_candidate_against_recent_buffer({}), (False, 0, 0))

    def test_invalid_history_structure_is_rejected(self):
        for value in ({}, [None], [{'species': 123}]):
            with self.subTest(value=value):
                self.write_json('animal_history.json', value)
                with self.assertRaisesRegex(RuntimeError, 'animal_history.json'):
                    pipeline.get_used_base_nouns()

    def test_invalid_progress_is_rejected(self):
        for value in ([], {}, {'current_id': -1}, {'current_id': '1'}, {'current_id': True}):
            with self.subTest(value=value):
                self.write_json('animal_progress.json', value)
                with self.assertRaisesRegex(RuntimeError, 'animal_progress.json'):
                    pipeline.generate(animal_id=1, duration=0.1, dry_run=True, force_research=False)

    def test_unreadable_json_is_not_an_empty_first_run(self):
        with patch.object(Path, 'read_text', side_effect=PermissionError('blocked')):
            with self.assertRaisesRegex(RuntimeError, 'Cannot read state'):
                pipeline._load_json(pipeline.HISTORY_FILE, [])
            with self.assertRaisesRegex(RuntimeError, 'used_animals.json'):
                researcher._load_used()

    def test_ffmpeg_failure_does_not_upload_or_change_state(self):
        before = self.snapshot()
        with patch.object(pipeline, '_encode_video', side_effect=RuntimeError('ffmpeg failed')), \
             patch.object(pipeline, 'generate_reel_audio'), \
             patch.object(pipeline, 'verify_candidate_against_recent_buffer', return_value=(True, 100, 64)), \
             patch.object(pipeline, 'render_generative_frame', return_value=Image.new('RGB', (1080, 1920))), \
             patch.object(pipeline, '_upload_to_youtube') as upload:
            with self.assertRaisesRegex(RuntimeError, 'ffmpeg failed'):
                pipeline.generate(animal_id=1, duration=0.1, force_research=False)
            upload.assert_not_called()
        self.assertEqual(before, self.snapshot())

    def test_preview_cannot_point_at_production_or_ancestor(self):
        for folder in (self.data, self.data/'preview', self.root):
            with self.subTest(folder=folder), self.assertRaisesRegex(ValueError, 'isolated'):
                pipeline.generate(dry_run=True, history_dir=folder)

    def test_production_cannot_use_preview_ledger(self):
        with self.assertRaisesRegex(ValueError, 'permanent'):
            pipeline.generate(history_dir=self.root/'preview')

    def test_missing_credentials_stops_before_reserving_or_rendering(self):
        with patch.object(pipeline, '_has_upload_credentials', return_value=False), \
             patch.object(pipeline, 'render_generative_frame') as render:
            with self.assertRaisesRegex(RuntimeError, 'credentials missing'):
                pipeline.generate(animal_id=1, force_research=False)
            render.assert_not_called()
        self.assertFalse((self.data/'unique_animal_history.jsonl').exists())

    def test_preview_never_researches_even_without_no_research_flag(self):
        with patch.object(pipeline, 'research_animal') as research, \
             patch.object(pipeline, '_encode_video', side_effect=RuntimeError('stop before encode')):
            with self.assertRaisesRegex(RuntimeError, 'stop before encode'):
                pipeline.generate(animal_id=1, duration=.034, dry_run=True)
            research.assert_not_called()

    def test_audit_failure_never_uploads(self):
        def encode(frames, output, audio):
            output.write_bytes(b'not a video')
        with patch.object(pipeline, '_encode_video', side_effect=encode), \
             patch.object(pipeline, 'generate_reel_audio'), \
             patch.object(pipeline, 'verify_candidate_against_recent_buffer', return_value=(True, 100, 64)), \
             patch.object(pipeline, 'render_generative_frame', return_value=Image.new('RGB', (1080, 1920))), \
             patch.object(pipeline, '_upload_to_youtube') as upload:
            with self.assertRaises(unique.DiversityError):
                pipeline.generate(animal_id=1, duration=.1, force_research=False, max_retries=1)
            upload.assert_not_called()
        self.assertEqual(unique.HistoryStore(self.data).records()[0]['status'], 'failed')
        self.assertFalse(pipeline.HISTORY_FILE.exists())

    def test_preupload_checkpoint_failure_prevents_upload(self):
        def checkpoint(root, store):
            if any(r['status'] == 'publishing' for r in store.records()):
                raise unique.HistoryError('push failed')
        with patch.object(unique, 'checkpoint_git', side_effect=checkpoint), \
             patch.object(pipeline, '_upload_to_youtube') as upload:
            with self.assertRaisesRegex(unique.HistoryError, 'push failed'):
                self.fake_generation(upload=None)
            upload.assert_not_called()
        self.assertEqual(unique.HistoryStore(self.data).records()[0]['status'], 'publishing')

    def test_blank_upload_id_is_unconfirmed(self):
        before = self.snapshot()
        with self.assertRaises(pipeline.UploadUnconfirmedError):
            self.fake_generation(upload='   ')
        self.assertEqual(before, self.snapshot())
        self.assertEqual(unique.HistoryStore(self.data).records()[0]['status'], 'publishing')

    def test_video_changed_during_checkpoint_never_uploads(self):
        before = self.snapshot()
        def checkpoint(root, store):
            for record in store.records():
                if record['status'] == 'publishing':
                    (root/record['file']).write_bytes(b'changed after audit')
        with patch.object(unique, 'checkpoint_git', side_effect=checkpoint), \
             patch.object(pipeline, '_upload_to_youtube') as upload:
            with self.assertRaisesRegex(RuntimeError, 'changed before upload'):
                self.fake_generation()
            upload.assert_not_called()
        self.assertEqual(before, self.snapshot())
        self.assertEqual(unique.HistoryStore(self.data).records()[0]['status'], 'publishing')

    def test_cli_reports_unconfirmed_upload_as_failure(self):
        with patch.object(pipeline, 'generate', side_effect=pipeline.UploadUnconfirmedError('unconfirmed')), \
             patch('sys.argv', ['animal_short_generator.py']), patch('sys.stderr'):
            with self.assertRaises(SystemExit) as error:
                pipeline.main()
            self.assertEqual(error.exception.code, 1)

    def test_duration_rejected_before_any_render(self):
        for duration in (0, -1, float('nan'), float('inf'), 181):
            with self.subTest(duration=duration), self.assertRaises(ValueError):
                pipeline.generate(duration=duration, dry_run=True)

    def test_invalid_species_index(self):
        for animal_id in (-1, 2):
            with self.subTest(animal_id=animal_id), self.assertRaises(ValueError):
                pipeline.generate(animal_id=animal_id, dry_run=True)

    def test_audio_seed_is_deterministic_and_short_audio_safe(self):
        a, b = self.root/'a.wav', self.root/'b.wav'
        generate_reel_audio(a, 0.05, typing_events=10, seed=3)
        generate_reel_audio(b, 0.05, typing_events=10, seed=3)
        self.assertEqual(a.read_bytes(), b.read_bytes())


class UniquenessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = unique.HistoryStore(Path(self.temp.name))
        self.species = configure_species(get_species_for_id(1))
        self.skill = unique.UniqueAnimalGenerationSkill(self.store, max_retries=12)
        _, self.plan = self.skill.select([self.species])

    def complete(self, identifier, **overrides):
        values = dict(validated=True, output_hash='a'*64, visual_hashes=['0'*16]*3)
        values.update(overrides)
        self.store.transition(identifier, 'completed', **values)

    def test_empty_store_does_not_initialize_fake_history(self):
        self.assertEqual(self.store.records(), [])
        self.assertFalse(self.store.journal.exists())

    def test_successful_lifecycle_survives_restart(self):
        identifier = self.store.reserve(self.plan)
        self.complete(identifier)
        self.store.transition(identifier, 'publishing')
        self.store.transition(identifier, 'published', video_id='test-only-id')
        records = unique.HistoryStore(self.store.directory).records()
        self.assertEqual(records[0]['status'], 'published')
        self.assertEqual(len(self.store.journal.read_text().splitlines()), 4)

    def test_seed_and_aliases_do_not_hide_same_content(self):
        self.store.reserve(self.plan)
        variant = {**self.plan, 'seed': self.plan['seed'] + 1, 'action': 'walking', 'environment': 'woodland'}
        self.assertEqual(unique.fingerprint(variant), unique.fingerprint(self.plan))
        with self.assertRaises(unique.DiversityError):
            self.store.reserve(variant)

    def test_seed_cannot_be_reused_for_different_species(self):
        self.store.reserve(self.plan)
        variant = {**self.plan, 'species': 'GREEN SEA TURTLE', 'action': 'swim', 'environment': 'reef'}
        self.assertEqual(unique.rejection(variant, self.store.records()), 'same seed')

    def test_same_species_action_scene_cannot_be_disguised(self):
        self.store.reserve(self.plan)
        variant = {**self.plan, 'seed': self.plan['seed'] + 1, 'size': 'compact', 'lighting': 'moonlight'}
        self.assertEqual(unique.rejection(variant, self.store.records()), 'same animal/action/scene')

    def test_cosmetic_species_swap_is_not_new_scene(self):
        self.store.reserve(self.plan)
        variant = {**self.plan, 'seed': self.plan['seed'] + 1, 'species': 'AFRICAN LION'}
        self.assertIn('cosmetic', unique.rejection(variant, self.store.records()))

    def test_snapshot_is_rebuilt_from_journal(self):
        identifier = self.store.reserve(self.plan)
        self.store.snapshot.write_text('{broken')
        self.assertEqual(self.store.records()[0]['id'], identifier)
        self.assertEqual(json.loads(self.store.snapshot.read_text())['sequence'], 1)

    def test_missing_initialized_journal_blocks(self):
        self.store.reserve(self.plan)
        self.store.journal.unlink()
        with self.assertRaises(unique.HistoryError):
            self.store.records()

    def test_partial_append_blocks_instead_of_truncating(self):
        self.store.reserve(self.plan)
        raw = self.store.journal.read_bytes() + b'{partial'
        self.store.journal.write_bytes(raw)
        with self.assertRaises(unique.HistoryError):
            self.store.records()
        self.assertEqual(self.store.journal.read_bytes(), raw)

    def test_rollback_behind_head_blocks(self):
        identifier = self.store.reserve(self.plan)
        raw = self.store.journal.read_bytes()
        self.complete(identifier)
        self.store.journal.write_bytes(raw)
        with self.assertRaises(unique.HistoryError):
            self.store.records()

    def test_valid_append_before_snapshot_crash_recovers(self):
        self.store.reserve(self.plan)
        with patch.object(unique, 'atomic_json', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                self.store.transition(self.store.records()[0]['id'], 'failed', reason='test')
        # The above failure occurred while reading the snapshot, so append a
        # separate completed event with an intentionally failed snapshot write.
        identifier = self.store.records()[0]['id']
        with patch.object(self.store, '_snapshot', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                self.store.transition(identifier, 'failed', reason='test')
        self.assertEqual(self.store.records()[0]['status'], 'failed')

    def test_checksum_corruption_blocks(self):
        self.store.reserve(self.plan)
        raw = self.store.journal.read_text().replace('reserved', 'published')
        self.store.journal.write_text(raw)
        with self.assertRaises(unique.HistoryError):
            self.store.records()

    def test_valid_checksum_does_not_bypass_replay_schema(self):
        self.store.reserve(self.plan)
        event = json.loads(self.store.journal.read_text())
        event['record']['status'] = 'published'
        event.pop('checksum')
        event['checksum'] = unique.digest(event)
        self.store.journal.write_text(json.dumps(event) + '\n')
        with self.assertRaises(unique.HistoryError):
            self.store.records()

    def test_scalar_event_and_head_fail_closed(self):
        self.store.journal.write_text('[]\n')
        with self.assertRaises(unique.HistoryError):
            self.store.records()
        self.store.journal.unlink()
        self.store.reserve(self.plan)
        self.store.marker.write_text('[]')
        with self.assertRaises(unique.HistoryError):
            self.store.records()

    def test_completion_requires_true_validation_and_three_hashes(self):
        identifier = self.store.reserve(self.plan)
        for overrides in ({'validated': 'yes'}, {'visual_hashes': None}, {'visual_hashes': ['0']},
                          {'output_hash': None}, {'visual_hashes': [None]*3}):
            with self.subTest(overrides=overrides), self.assertRaises(unique.HistoryError):
                self.complete(identifier, **overrides)
        self.assertEqual(self.store.records()[0]['status'], 'reserved')

    def test_transition_cannot_rewrite_validated_output(self):
        identifier = self.store.reserve(self.plan)
        self.complete(identifier)
        with self.assertRaises(unique.HistoryError):
            self.store.transition(identifier, 'publishing', output_hash='b'*64)
        with self.assertRaises(unique.HistoryError):
            self.store.transition(identifier, 'published', video_id='id')

    def test_unknown_and_terminal_transitions_fail(self):
        with self.assertRaises(unique.HistoryError):
            self.store.transition('b'*32, 'failed')
        identifier = self.store.reserve(self.plan)
        self.store.transition(identifier, 'failed', reason='test')
        with self.assertRaises(unique.HistoryError):
            self.complete(identifier)

    def test_concurrent_same_plan_only_one_reservation(self):
        from concurrent.futures import ThreadPoolExecutor
        def reserve(_):
            try:
                return unique.HistoryStore(self.store.directory).reserve(self.plan)
            except unique.DiversityError:
                return None
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(reserve, range(8)))
        self.assertEqual(sum(r is not None for r in results), 1)
        self.assertEqual(len(self.store.records()), 1)

    def test_identical_output_hash_rejected_for_different_plan(self):
        first = self.store.reserve(self.plan)
        self.complete(first)
        species = configure_species(get_species_for_id(104))
        _, plan = self.skill.select([species])
        second = self.store.reserve(plan)
        with self.assertRaisesRegex(unique.DiversityError, 'output fingerprint'):
            self.complete(second, visual_hashes=['f'*16]*3)

    def test_similar_decoded_sequence_rejected(self):
        first = self.store.reserve(self.plan)
        self.complete(first)
        _, plan = self.skill.select([configure_species(get_species_for_id(104))])
        second = self.store.reserve(plan)
        with self.assertRaisesRegex(unique.DiversityError, 'perceptually'):
            self.complete(second, output_hash='b'*64)

    def test_planner_exhaustion_never_forces_candidate(self):
        skill = unique.UniqueAnimalGenerationSkill(self.store, max_retries=3)
        with self.assertRaises(unique.DiversityError):
            skill.select([self.species], validator=lambda _: False)
        self.assertEqual(len(skill.last_rejections), 3)
        with self.assertRaises(unique.DiversityError):
            skill.select([])

    def test_validator_error_is_not_success(self):
        def broken(_):
            raise RuntimeError('renderer broke')
        with self.assertRaises(unique.DiversityError):
            self.skill.select([self.species], validator=broken)
        self.assertIn('validation error', self.skill.last_rejections[0])

    def test_planner_simulation_has_unique_fingerprints_and_species_rotation(self):
        catalogue = [configure_species(get_species_for_id(i)) for i in (0, 1, 104, 122, 465)]
        fingerprints, names = set(), []
        for _ in range(15):
            _, plan = self.skill.select(catalogue)
            self.assertNotIn(unique.fingerprint(plan), fingerprints)
            self.store.reserve(plan)
            fingerprints.add(unique.fingerprint(plan))
            names.append(plan['species'])
        self.assertEqual(len(set(names[:5])), 5)
        self.assertEqual(len(self.store.records()), 15)

    def test_invalid_planner_configuration_is_rejected(self):
        for value in (0, -1, float('nan'), 1.1):
            with self.assertRaises(ValueError):
                unique.UniqueAnimalGenerationSkill(self.store, threshold=value)
        with self.assertRaises(ValueError):
            unique.UniqueAnimalGenerationSkill(self.store, max_retries=0)

    def test_plan_really_changes_renderer_pixels(self):
        from src.animal_scene_variation import draw_habitat, motion_state
        plan = {**self.plan, 'seed': 9}
        a = draw_habitat(plan, 1)
        self.assertEqual(a.tobytes(), draw_habitat(plan, 1).tobytes())
        self.assertNotEqual(a.tobytes(), draw_habitat({**plan, 'environment': 'river'}, 1).tobytes())
        self.assertNotEqual(a.tobytes(), draw_habitat({**plan, 'lighting': 'moonlight'}, 1).tobytes())
        species = unique.apply_plan(self.species, plan)
        image = render_animal_layer(species, 1, (240, 160), 'draft')
        other = unique.apply_plan(self.species, {**plan, 'camera_angle': 'side'})
        self.assertNotEqual(image.tobytes(), render_animal_layer(other, 1, (240, 160), 'draft').tobytes())
        self.assertEqual(motion_state({**plan, 'action': 'rest'}, 2, .5)[0], 0)

    def test_ci_checkpoint_requires_explicit_durable_push(self):
        with patch.dict('os.environ', {'GITHUB_ACTIONS': 'true', 'UNIQUE_HISTORY_GIT': '0'}):
            with self.assertRaises(unique.HistoryError):
                unique.checkpoint_git(self.store.directory, self.store)


class GitCheckpointTests(unittest.TestCase):
    """Real git against a temporary local bare remote; never touches GitHub."""
    def setUp(self):
        import subprocess
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base/'working'
        self.remote = self.base/'remote.git'
        self.root.mkdir()
        self.env = patch.dict('os.environ', {
            'UNIQUE_HISTORY_GIT': '1', 'GITHUB_ACTIONS': 'true',
            'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null',
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        self.run_git = lambda *args, cwd=self.root: subprocess.run(
            ['git', *args], cwd=cwd, check=True, capture_output=True, text=True, timeout=30)
        self.run_git('init', '--bare', '--initial-branch=main', str(self.remote))
        self.run_git('init', '--initial-branch=main')
        self.run_git('config', 'user.name', 'Offline Test')
        self.run_git('config', 'user.email', 'offline@example.invalid')
        self.run_git('commit', '--allow-empty', '-m', 'Initial test commit')
        self.run_git('remote', 'add', 'origin', str(self.remote))
        self.run_git('push', '-u', 'origin', 'main')
        self.store = unique.HistoryStore(self.root/'data')
        _, self.plan = unique.UniqueAnimalGenerationSkill(self.store).select([
            configure_species(get_species_for_id(1))])
        self.identifier = self.store.reserve(self.plan)

    def test_checkpoint_persists_intent_in_real_remote(self):
        unique.checkpoint_git(self.root, self.store)
        self.store.transition(self.identifier, 'completed', validated=True,
                              output_hash='a'*64, visual_hashes=['0'*16]*3)
        self.store.transition(self.identifier, 'publishing')
        unique.checkpoint_git(self.root, self.store)
        raw = self.run_git('show', 'main:data/unique_animal_history.jsonl', cwd=self.remote).stdout
        self.assertEqual(json.loads(raw.splitlines()[-1])['record']['status'], 'publishing')
        self.assertEqual(self.run_git('rev-parse', 'HEAD').stdout,
                         self.run_git('rev-parse', 'main', cwd=self.remote).stdout)
        tracked = self.run_git('ls-tree', '-r', '--name-only', 'HEAD').stdout.splitlines()
        self.assertEqual(len(tracked), 3)
        self.assertFalse(any(name.endswith('.lock') for name in tracked))

    def test_unrelated_staged_file_prevents_checkpoint(self):
        (self.root/'unrelated.txt').write_text('do not commit')
        self.run_git('add', 'unrelated.txt')
        before = self.run_git('rev-parse', 'main', cwd=self.remote).stdout
        with self.assertRaisesRegex(unique.HistoryError, 'unrelated'):
            unique.checkpoint_git(self.root, self.store)
        self.assertEqual(before, self.run_git('rev-parse', 'main', cwd=self.remote).stdout)
        self.assertEqual(self.run_git('diff', '--cached', '--name-only').stdout.strip(), 'unrelated.txt')

    def test_rejected_push_raises_and_keeps_local_intent(self):
        import subprocess
        hook = self.remote/'hooks'/'pre-receive'
        hook.write_text('#!/bin/sh\nexit 1\n')
        hook.chmod(0o755)
        before = self.run_git('rev-parse', 'main', cwd=self.remote).stdout
        with self.assertRaises(subprocess.CalledProcessError):
            unique.checkpoint_git(self.root, self.store)
        self.assertEqual(before, self.run_git('rev-parse', 'main', cwd=self.remote).stdout)
        self.assertEqual(self.store.records()[0]['status'], 'reserved')

    def test_checkpoint_rebases_unrelated_remote_changes(self):
        peer = self.base/'peer'
        self.run_git('clone', str(self.remote), str(peer))
        self.run_git('config', 'user.name', 'Offline Peer', cwd=peer)
        self.run_git('config', 'user.email', 'peer@example.invalid', cwd=peer)
        (peer/'peer.txt').write_text('remote update')
        self.run_git('add', 'peer.txt', cwd=peer)
        self.run_git('commit', '-m', 'Unrelated update', cwd=peer)
        self.run_git('push', 'origin', 'main', cwd=peer)
        unique.checkpoint_git(self.root, self.store)
        self.assertEqual((self.root/'peer.txt').read_text(), 'remote update')
        self.assertEqual(self.run_git('rev-parse', 'HEAD').stdout,
                         self.run_git('rev-parse', 'main', cwd=self.remote).stdout)


class AuditTests(unittest.TestCase):
    def test_invalid_audit_arguments(self):
        for count in (0, 31, True, 1.5):
            with self.assertRaises(ValueError):
                auditor.audit_video('missing.mp4', sample_count=count)
        with self.assertRaises(ValueError):
            auditor.audit_video('missing.mp4', minimum_duration=float('nan'))

    def test_garbage_is_not_an_encoded_video(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'invalid.mp4'
            path.write_bytes(b'invalid' * 20000)
            report = auditor.audit_video(path, minimum_duration=.1, sample_count=3)
            self.assertFalse(report['passed'])
            self.assertTrue(report['errors'])

    def test_decode_failure_fails_gate_even_with_good_sampled_frames(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'fake.mp4'
            path.write_bytes(b'x' * 2048)
            meta = {'streams': [{'codec_type': 'video', 'width': 1080, 'height': 1920,
                                 'duration': '3', 'r_frame_rate': '30/1'}, {'codec_type': 'audio'}]}
            def run(cmd):
                if '-xerror' in cmd:
                    return 1, '', 'corrupt middle frame'
                for i in range(3):
                    im = Image.new('RGB', (270, 480), 'white')
                    im.paste((20, 40, 60), (10, 20, 180, 380))
                    im.save(cmd[-1].replace('%02d', str(i).zfill(2)))
                return 0, '', ''
            with patch.object(auditor, '_probe', return_value=meta), patch.object(auditor, '_run', side_effect=run):
                report = auditor.audit_video(path, minimum_duration=3, sample_count=3)
            self.assertFalse(report['passed'])
            self.assertIn('full_decode_failed', report['errors'])
            self.assertEqual(len(report['metrics']['visual_hashes']), 3)


if __name__ == '__main__':
    unittest.main()
