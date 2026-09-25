"""Offline regression suite: python -m unittest test_anatomy -v.

All network connections are blocked during tests. Publication data is read-only;
fixtures and render artifacts live exclusively in temporary outputs directories.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image, ImageDraw

import preview_anatomy as preview
from src import animal_short_generator as publication
from src import animal_researcher as researcher
from src import generative_dragon_engine as engine
from src.anatomy_profiles import mammal_profile, resolve_body_plan
from src.bio_bone_renderer import draw_bio_creature, solve_two_bone_ik
from src import natural_anatomy_renderer as natural
from src.natural_anatomy_renderer import mammal_pose

ROOT = Path(__file__).resolve().parent


def ledger_snapshot():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (ROOT / 'data').rglob('*') if p.is_file()}


class OfflineCase(unittest.TestCase):
    def setUp(self):
        self.before = ledger_snapshot()
        for target in ('socket.socket.connect', 'socket.socket.connect_ex', 'urllib.request.urlopen'):
            guard = patch(target, side_effect=AssertionError('Network is forbidden in offline tests'))
            guard.start()
            self.addCleanup(guard.stop)
        (ROOT / 'outputs').mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='test_', dir=ROOT / 'outputs')
        self.output = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def tearDown(self):
        self.assertEqual(self.before, ledger_snapshot(), 'Publication/source data changed')

    def species_named(self, name):
        for i, entry in enumerate(engine.load_encyclopedia()):
            if entry['name'].casefold() == name.casefold():
                return engine.get_species_for_id(i)
        self.fail('Missing catalogue species: ' + name)


class CatalogueTests(OfflineCase):
    def test_all_687_entries_render_nonempty_silhouettes(self):
        catalogue = engine.load_encyclopedia()
        self.assertEqual(len(catalogue), 687)
        for i, entry in enumerate(catalogue):
            with self.subTest(animal=i, name=entry['name']):
                species = engine.get_species_for_id(i)
                self.assertTrue(resolve_body_plan(species))
                self.assertFalse(species['anatomy']['specimen_validated'])
                sim = engine._simulation_for_frame(species, 45)
                image = Image.new('RGBA', (1200, 1200))
                ca, sa = math.cos(sim.angle), math.sin(sim.angle)
                self.assertTrue(draw_bio_creature(ImageDraw.Draw(image), sim, species, .6, ca, sa, -sa, ca))
                self.assertIsNotNone(image.getbbox())

    def test_taxonomy_overrides_misleading_name_fragments(self):
        cases = [
            ('Crab Spider', 'arachnid', 'spider', 'arachnid'),
            ('Butterfly Ray', 'aquatic', 'ray', 'ray'),
            ('Rhinoceros Beetle', 'insect', 'beetle', 'beetle'),
            ('Squirrel Monkey', 'quadruped', 'primate', 'mammal'),
            ('Horseshoe Crab', 'crustacean', 'crab', 'horseshoe'),
            ('Giant Centipede', 'arachnid', 'spider', 'myriapod'),
            ('Moray Eel', 'aquatic', 'eel', 'eel'),
            ('Slow Worm', 'reptile', 'lizard', 'legless_lizard'),
            ('Peacock Mantis Shrimp', 'crustacean', 'shrimp', 'mantis_shrimp'),
            ('Cleaner Shrimp', 'crustacean', 'shrimp', 'shrimp'),
        ]
        for name, cls, morph, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(resolve_body_plan(dict(name=name, class_type=cls, morphology=morph)), expected)
        self.assertEqual(mammal_profile(dict(name='Squirrel Monkey', morphology='primate')).family, 'primate')

    def test_unknown_taxonomy_fails_instead_of_dog_fallback(self):
        with self.assertRaises(ValueError):
            resolve_body_plan(dict(name='Unknown', class_type='unknown', morphology='unknown'))

    def test_ids_reject_out_of_range_and_nonintegers(self):
        for value in (-1, 687, True, 1.5, '0'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                engine.get_species_for_id(value)

    def test_returned_species_do_not_mutate_catalogue(self):
        original = copy.deepcopy(engine.load_encyclopedia()[0])
        species = engine.get_species_for_id(0)
        species['bone_structure']['test'] = 'must not leak'
        species['code_lines'].append('must not leak')
        self.assertEqual(original, engine.load_encyclopedia()[0])

    def test_palette_is_not_forced_orange(self):
        lion = engine.get_species_for_id(0)
        bear = self.species_named('Polar Bear')
        self.assertNotEqual(lion['fur_mid'], bear['fur_mid'])
        self.assertGreater(min(bear['fur_mid']), 200)


class GeometryTests(OfflineCase):
    def test_ik_preserves_lengths_for_reachable_unreachable_and_folded_targets(self):
        for l1, l2 in ((10, 10), (12, 3), (3, 12), (1, 80)):
            for target in ((0, 0), (2, 1), (1000, 500), (-100, 0)):
                for bend in (-1, 1):
                    root, joint, end = solve_two_bone_ik((0, 0), target, l1, l2, bend)
                    self.assertAlmostEqual(math.dist(root, joint), l1, places=7)
                    self.assertAlmostEqual(math.dist(joint, end), l2, places=7)

    def test_ik_rejects_nonfinite_and_nonpositive_bones(self):
        for length in (0, -1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                solve_two_bone_ik((0, 0), (1, 1), length, 2)

    def test_all_mammal_bones_and_planted_contacts_across_two_cycles(self):
        for i, entry in enumerate(engine.load_encyclopedia()):
            species = engine.get_species_for_id(i)
            if resolve_body_plan(species) != 'mammal':
                continue
            with self.subTest(name=entry['name']):
                p = mammal_profile(species)
                stride = min(p.stride, p.legs*.90)
                previous = {}
                for step in range(100):
                    travel = stride*step/40
                    _, _, limbs = mammal_pose(species, travel/72, travel)
                    for limb in limbs:
                        points = limb['points']
                        for j, length in enumerate(limb['lengths']):
                            self.assertAlmostEqual(math.dist(points[j], points[j+1]), length, places=6)
                        if limb['planted']:
                            self.assertAlmostEqual(points[-1][1], p.legs, places=6)
                            key = (limb['side'], limb['front'])
                            prev = previous.get(key)
                            if prev and prev['planted'] and limb['phase'] > prev['phase']:
                                self.assertAlmostEqual(limb['contact_x'], prev['contact_x'], places=6)
                        previous[(limb['side'], limb['front'])] = limb

    def test_bone_metadata_affects_joint_split_without_stretching(self):
        species = engine.get_species_for_id(0)
        variants = []
        for upper in (1, 2):
            candidate = copy.deepcopy(species)
            candidate['bone_structure']['limbs'] = {'upper_bone_len': upper, 'lower_bone_len': 1}
            variants.append(mammal_pose(candidate, .3)[2][0])
        self.assertNotEqual(variants[0]['lengths'][0], variants[1]['lengths'][0])
        self.assertAlmostEqual(sum(variants[0]['lengths']), sum(variants[1]['lengths']))

    def test_camera_bounds_shared_by_all_mammal_modes(self):
        species = engine.get_species_for_id(0)
        bounds = engine.mammal_camera_bounds(species)
        for mode in ('surface', 'overlay', 'skeleton'):
            species['render_mode'] = mode
            self.assertEqual(bounds, engine.mammal_camera_bounds(species))

    def test_gait_swing_boundaries_are_position_continuous(self):
        species = engine.get_species_for_id(0)
        p = mammal_profile(species)
        stride = min(p.stride, p.legs*.9)
        for boundary in (.67, 1):
            before = mammal_pose(species, 0, stride*(boundary-1e-7))[2][1]
            after = mammal_pose(species, 0, stride*(boundary+1e-7))[2][1]
            self.assertLess(math.dist(before['points'][-1], after['points'][-1]), .001)


    def test_head_and_tail_geometry_shared_by_surface_overlay_and_skeleton(self):
        species = engine.get_species_for_id(0)
        p, bob, _ = mammal_pose(species, .6)
        expected_head = natural.mammal_head_geometry(p, bob)
        expected_tail = natural.mammal_tail_geometry(p, bob, .6)
        for mode in ('surface', 'overlay', 'skeleton'):
            with self.subTest(mode=mode):
                species['render_mode'] = mode
                with patch.object(natural, 'mammal_head_geometry', wraps=natural.mammal_head_geometry) as head, \
                     patch.object(natural, 'mammal_tail_geometry', wraps=natural.mammal_tail_geometry) as tail:
                    natural.draw_mammal(ImageDraw.Draw(Image.new('RGBA', (1200,1200))), SimpleNamespace(x=600,y=600), species, .6)
                    head.assert_called_once_with(p,bob)
                    tail.assert_called_once_with(p,bob,.6)
                self.assertEqual(expected_head, natural.mammal_head_geometry(p,bob))
                self.assertEqual(expected_tail, natural.mammal_tail_geometry(p,bob,.6))

    def test_tailless_apes_do_not_gain_skeleton_tails(self):
        species = self.species_named('Western Lowland Gorilla')
        p,bob,_ = mammal_pose(species, .5)
        self.assertEqual(natural.mammal_tail_geometry(p,bob,.5), ([],[]))

    def test_all_mammal_surface_extents_fit_fixed_camera(self):
        count = 0
        for i in range(len(engine.load_encyclopedia())):
            species = engine.get_species_for_id(i)
            if resolve_body_plan(species) != 'mammal':
                continue
            count += 1
            left,top,right,bottom = engine.mammal_camera_bounds(species)
            for step in range(4):
                with self.subTest(name=species['name'],step=step):
                    image = Image.new('RGBA',(1600,1600))
                    natural.draw_mammal(ImageDraw.Draw(image),SimpleNamespace(x=800,y=800),species,step*.7)
                    box = image.getbbox()
                    self.assertIsNotNone(box)
                    x0,y0,x1,y1 = (v-800 for v in box)
                    self.assertGreaterEqual(x0,left)
                    self.assertGreaterEqual(y0,top)
                    self.assertLessEqual(x1,right)
                    self.assertLessEqual(y1,bottom)
        self.assertEqual(count,234)

    def test_full_cycle_reports_for_all_mammals(self):
        for i in range(len(engine.load_encyclopedia())):
            species = engine.get_species_for_id(i)
            if resolve_body_plan(species) != 'mammal':
                continue
            with self.subTest(name=species['name']):
                report = preview.gait_report(species)
                for key in ('max_bone_length_error','max_planted_height_error','max_stance_world_drift'):
                    self.assertLess(report[key],1e-8)
                self.assertEqual(report['numerical_samples'],121)
                self.assertGreater(report['planted_limb_samples'],0)
                self.assertFalse(report['specimen_validated'])
                self.assertTrue(report['numerical_pass'], report['numerical_checks'])
                self.assertGreater(report['max_sampled_swing_clearance'], 0)
                self.assertLess(report['max_limb_cycle_closure_error'], 1e-8)

    def test_gait_report_detects_cumulative_sliding(self):
        real_pose = preview.mammal_pose
        def sliding_pose(species, time, travel=None):
            p, bob, limbs = real_pose(species, time, travel)
            for limb in limbs:
                limb['contact_x'] += (travel or 0)*.01
            return p, bob, limbs
        with patch.object(preview, 'mammal_pose', side_effect=sliding_pose):
            report = preview.gait_report(engine.get_species_for_id(0))
        self.assertFalse(report['numerical_pass'])
        self.assertFalse(report['numerical_checks']['max_stance_world_drift'])
        self.assertGreater(report['max_stance_world_drift'], .1)

    def test_gait_report_detects_boundary_teleport(self):
        real_pose = preview.mammal_pose
        def broken_pose(species, time, travel=None):
            p, bob, limbs = real_pose(species, time, travel)
            for limb in limbs:
                if not limb['planted']:
                    x, y = limb['points'][-1]
                    limb['points'][-1] = (x+10,y)
            return p, bob, limbs
        with patch.object(preview, 'mammal_pose', side_effect=broken_pose):
            report = preview.gait_report(engine.get_species_for_id(0))
        self.assertFalse(report['numerical_pass'])
        self.assertGreater(report['max_boundary_position_gap'], 9)
        self.assertFalse(report['numerical_checks']['max_boundary_velocity_gap'])


class FramingTests(OfflineCase):
    def test_geometry_probe_covers_strokes_and_rejects_nonfinite(self):
        probe = engine._GeometryBounds()
        probe.line([(0, 0), (10, 20)], width=10)
        self.assertEqual(probe.bounds, (-7, -7, 17, 27))
        probe.arc((0, 0, 40, 40), 0, 30, width=2)
        self.assertEqual(probe.bounds, (-7, -7, 43, 43))
        with self.assertRaises(ValueError):
            probe.polygon([(0, 0), (float('nan'), 1)])

    def test_every_body_plan_command_bounds_contain_raster(self):
        seen = set()
        for i, entry in enumerate(engine.load_encyclopedia()):
            plan = resolve_body_plan(entry)
            if plan in seen:
                continue
            seen.add(plan)
            species = engine.get_species_for_id(i)
            for frame in (0, 179):
                with self.subTest(plan=plan, frame=frame):
                    sim = engine._simulation_for_frame(species, frame)
                    image = Image.new('RGBA', (2400, 2400))
                    origin = (sim.x-600, sim.y-600)
                    painter = engine._SupersampledDraw(image, origin)
                    time = frame/engine.FPS*engine.MOTION_RATE
                    ca, sa = math.cos(sim.angle), math.sin(sim.angle)
                    draw_bio_creature(painter, sim, species, time, ca, sa, -sa, ca)
                    pixel = image.getbbox()
                    self.assertIsNotNone(pixel)
                    world = [pixel[k]/2+origin[k%2] for k in range(4)]
                    geometry = engine.creature_geometry_bounds(species, sim, time)
                    self.assertGreaterEqual(world[0], geometry[0])
                    self.assertGreaterEqual(world[1], geometry[1])
                    self.assertLessEqual(world[2], geometry[2])
                    self.assertLessEqual(world[3], geometry[3])
        self.assertGreater(len(seen), 30)

    def test_fixed_camera_preflight_does_not_mutate_species_or_seek_state(self):
        species = self.species_named('Monarch Butterfly')
        original = copy.deepcopy(species)
        sim = engine._simulation_for_frame(species, 29)
        state = copy.deepcopy(vars(sim))
        engine._nonmammal_camera_bounds.cache_clear()
        bounds = engine.fixed_camera_bounds(species)
        self.assertEqual(vars(sim), state)
        self.assertEqual(species, original)
        self.assertEqual(engine.fixed_camera_bounds(species), bounds)
        self.assertEqual(engine._nonmammal_camera_bounds.cache_info().hits, 1)
        self.assertEqual(engine._nonmammal_camera_bounds.cache_info().maxsize, 32)

    def test_geometry_cache_keys_include_rig_metadata_not_poster_text(self):
        species = self.species_named('King Cobra')
        engine._nonmammal_camera_bounds.cache_clear()
        engine.fixed_camera_bounds(species)
        changed = copy.deepcopy(species)
        changed['code_lines'] = ['different caption']
        engine.fixed_camera_bounds(changed)
        self.assertEqual(engine._nonmammal_camera_bounds.cache_info().misses, 1)
        changed['bone_structure']['vertebrae']['flexibility_index'] = .5
        engine.fixed_camera_bounds(changed)
        self.assertEqual(engine._nonmammal_camera_bounds.cache_info().misses, 2)

    def test_all_body_plans_fit_independent_camera_validation_samples(self):
        seen = set()
        for i, entry in enumerate(engine.load_encyclopedia()):
            plan = resolve_body_plan(entry)
            if plan in seen:
                continue
            seen.add(plan)
            with self.subTest(plan=plan):
                report = preview.framing_report(engine.get_species_for_id(i))
                self.assertTrue(report['framing_pass'], report)
                self.assertGreater(report['sampled_frames'], 100)
                self.assertEqual(report['horizon_seconds'], 30)
                self.assertFalse(report['specimen_validated'])

    def test_framing_report_detects_undersized_camera(self):
        species = self.species_named('King Cobra')
        with patch.object(preview, 'fixed_camera_bounds', return_value=(-1, -1, 1, 1)):
            report = preview.framing_report(species)
        self.assertFalse(report['framing_pass'])
        self.assertLess(report['minimum_margin_rig_units'], 0)

    def test_render_rejects_overflow_instead_of_silently_zooming(self):
        species = self.species_named('Monarch Butterfly')
        with patch.object(engine, 'fixed_camera_bounds', return_value=(-1, -1, 1, 1)):
            with self.assertRaisesRegex(ValueError, 'exceeds fixed camera'):
                engine.render_generative_frame(species, 0, 3)

    def test_nonmammal_render_seek_and_clip_length_share_identical_stage(self):
        species = self.species_named('King Cobra')
        original = copy.deepcopy(species)
        crop = (110, 340, 970, 832)
        direct = engine.render_generative_frame(species, 179, 180).crop(crop).tobytes()
        engine.render_generative_frame(species, 0, 900)
        again = engine.render_generative_frame(species, 179, 900).crop(crop).tobytes()
        engine._SIM_CACHE.clear()
        engine._nonmammal_camera_bounds.cache_clear()
        after_eviction = engine.render_generative_frame(species, 179, 180).crop(crop).tobytes()
        self.assertEqual(direct, again)
        self.assertEqual(direct, after_eviction)
        self.assertEqual(species, original)

    def test_motion_sheet_and_timestamps_for_nonmammal(self):
        species = self.species_named('Monarch Butterfly')
        path = preview.create_motion_sheet(species['animal_id'], .1, self.output)
        with Image.open(path) as image:
            self.assertEqual(image.size, (1720, 800))
        report = json.loads((self.output / f"{species['id']}_framing.json").read_text())
        self.assertTrue(report['framing_pass'])
        self.assertEqual(len(report['poses']), 8)
        self.assertEqual(report['poses'][0]['frame'], 0)
        self.assertEqual(report['poses'][-1]['frame'], 2)
        self.assertEqual(report['poses'][-1]['time_seconds'], 2/engine.FPS)
        self.assertFalse(report['uploaded'])

    def test_framing_cli_standalone_status_and_json_only(self):
        report = {'entries_checked': 1, 'failed_animal_ids': [21], 'framing_pass': False}
        with patch.object(preview, 'framing_audit', return_value=report), patch('builtins.print'):
            status = preview.main(['--audit-framing', '--output-dir', str(self.output)])
        self.assertEqual(status, 1)
        self.assertEqual([p.name for p in self.output.iterdir()], ['framing_audit.json'])
        self.assertEqual(json.loads((self.output/'framing_audit.json').read_text()), report)

    def test_cli_rejects_audit_render_combinations(self):
        for flags in (['--audit-framing', '--motion-sheet'], ['--audit-framing', '--audit-catalogue'],
                      ['--audit-catalogue', '--motion-sheet']):
            with self.subTest(flags=flags), patch('sys.stderr'), self.assertRaises(SystemExit) as raised:
                preview.main(flags+['--output-dir', str(self.output)])
            self.assertEqual(raised.exception.code, 2)
        self.assertEqual(list(self.output.iterdir()), [])


class PreviewTests(OfflineCase):
    def test_frame_seek_is_deterministic_and_cache_bounded(self):
        species = engine.get_species_for_id(0)
        direct = engine.render_generative_frame(species, 12, 60).tobytes()
        for frame in (0, 4, 11, 12):
            result = engine.render_generative_frame(species, frame, 60)
        self.assertEqual(direct, result.tobytes())
        for animal_id in range(12):
            engine._simulation_for_frame(engine.get_species_for_id(animal_id), 2)
        self.assertLessEqual(len(engine._SIM_CACHE), engine.MAX_SIMULATORS)
        self.assertEqual(direct, engine.render_generative_frame(species, 12, 60).tobytes())

    def test_stills_and_comparison_have_expected_dimensions(self):
        for mode in ('surface', 'overlay', 'skeleton'):
            species = preview.preview_species(0, mode)
            image = engine.render_generative_frame(species, 45, 180)
            self.assertEqual(image.size, (1080, 1920))
            self.assertEqual(image.mode, 'RGB')
        path = preview.create_comparison(0, 45, self.output)
        with Image.open(path) as image:
            self.assertEqual(image.size, (1720, 490))

    def test_invalid_timeline_and_duration(self):
        species = engine.get_species_for_id(0)
        for frame, total in ((-1, 30), (30, 30), (0, 0), (1.2, 30), (0, True)):
            with self.assertRaises(ValueError):
                engine.render_generative_frame(species, frame, total)
        for duration in (0, -.1, 31, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                preview.timeline_frames(duration)

    def test_nonmammal_diagnostics_are_not_mislabelled(self):
        index = next(i for i, e in enumerate(engine.load_encyclopedia()) if e['class_type'] == 'insect')
        with self.assertRaises(ValueError):
            preview.preview_species(index, 'skeleton')
        with self.assertRaises(ValueError):
            preview.create_comparison(index, 45, self.output)
        self.assertEqual(list(self.output.iterdir()), [])

    def test_output_rejects_data_paths_and_symlinks(self):
        with self.assertRaises(ValueError):
            preview.output_directory(ROOT / 'data')
        (self.output / 'escape').symlink_to(ROOT / 'data', target_is_directory=True)
        with self.assertRaises(ValueError):
            preview.output_directory(self.output / 'escape')
        (self.output / 'unsafe.png').symlink_to(ROOT / 'data' / 'animal_progress.json')
        with self.assertRaises(ValueError):
            preview.output_file(self.output, 'unsafe.png')
        with self.assertRaises(ValueError):
            preview.output_file(self.output, '../unsafe.png')

    def test_contact_sheet_and_json_report(self):
        path = preview.create_contact_sheet([0, 1], self.output)
        self.assertTrue(path.exists())
        report = json.loads((self.output / 'contact_sheet_report.json').read_text())
        self.assertEqual(len(report), 2)
        self.assertTrue(all(x['review_required'] and not x['specimen_validated'] for x in report))

    def test_gait_sheet_and_synchronized_report(self):
        species = preview.preview_species(0)
        path = preview.create_gait_sheet(0,self.output)
        with Image.open(path) as image:
            self.assertEqual(image.size,(1720,804))
        report = json.loads((self.output / f"{species['id']}_gait.json").read_text())
        self.assertEqual(len(report['poses']),8)
        self.assertLessEqual(abs(report['poses'][-1]['time_seconds']-report['cycle_seconds_at_preview_speed']),.5/engine.FPS)
        for pose in report['poses']:
            _,_,limbs = mammal_pose(species,pose['frame']/engine.FPS*engine.MOTION_RATE)
            self.assertEqual([x['planted'] for x in limbs],[x['planted'] for x in pose['limbs']])
            for actual,recorded in zip(limbs,pose['limbs']):
                self.assertEqual([list(p) for p in actual['points']],recorded['points'])

    def test_nonmammal_gait_rejected_without_artifacts(self):
        index = next(i for i,e in enumerate(engine.load_encyclopedia()) if e['class_type']=='insect')
        with self.assertRaises(ValueError):
            preview.create_gait_sheet(index,self.output)
        self.assertEqual(list(self.output.iterdir()),[])

    def test_atomic_image_failure_preserves_existing_file(self):
        path = self.output / 'safe.png'
        path.write_bytes(b'previous artifact')
        def partial_save(target, **kwargs):
            target.write_bytes(b'incomplete')
            raise OSError('simulated disk failure')
        image = Image.new('RGB',(10,10))
        with patch.object(image,'save',side_effect=partial_save):
            with self.assertRaises(OSError):
                preview.save_image(image,self.output,'safe.png')
        self.assertEqual(path.read_bytes(),b'previous artifact')
        self.assertEqual(list(self.output.glob('artifact_*')),[])

    def test_atomic_report_rejects_nonfinite_preserving_previous(self):
        path = self.output / 'safe.json'
        path.write_text('{"previous": true}')
        with self.assertRaises(ValueError):
            preview.save_report({'error':float('nan')},self.output,'safe.json')
        self.assertEqual(json.loads(path.read_text()),{'previous':True})
        self.assertEqual(list(self.output.glob('artifact_*')),[])

    def test_atomic_outputs_do_not_modify_hardlink_source(self):
        source = self.output / 'source.json'
        source.write_text('{"protected": true}')
        os.link(source,self.output / 'linked.json')
        preview.save_report({'new':True},self.output,'linked.json')
        self.assertEqual(json.loads(source.read_text()),{'protected':True})
        self.assertEqual(json.loads((self.output/'linked.json').read_text()),{'new':True})

    def test_atomic_output_rechecks_destination_symlink(self):
        source = self.output / 'source.json'
        source.write_text('{"protected": true}')
        with self.assertRaises(ValueError):
            with preview.atomic_output(self.output,'link.json') as partial:
                partial.write_text('{"new": true}')
                (self.output/'link.json').symlink_to(source)
        self.assertEqual(json.loads(source.read_text()),{'protected':True})
        self.assertEqual(list(self.output.glob('artifact_*')),[])

    def test_catalogue_audit_counts_and_truthful_scope(self):
        report = preview.catalogue_audit()
        self.assertEqual(report['catalogue_entries'],687)
        self.assertEqual(report['mammal_rigs_checked'],234)
        self.assertEqual(report['axial_rigs_checked'],56)
        self.assertEqual(report['insect_rigs_checked'],7)
        self.assertEqual(report['spider_rigs_checked'],20)
        self.assertEqual(sum(report['body_plan_counts'].values()),687)
        self.assertTrue(report['numerical_pass'])
        self.assertEqual(report['failed_animal_ids'],[])
        self.assertFalse(report['render_smoke_performed'])
        self.assertFalse(report['uploaded'])
        self.assertTrue(all(e['review_required'] and not e['specimen_validated'] for e in report['entries']))
        self.assertEqual(list(self.output.iterdir()),[])

    def test_audit_cli_writes_report_only_and_fails_on_numeric_error(self):
        report = {'catalogue_entries':1,'mammal_rigs_checked':1,'failed_animal_ids':[0],'numerical_pass':False}
        with patch.object(preview,'catalogue_audit',return_value=report), patch('builtins.print'):
            status = preview.main(['--audit-catalogue','--output-dir',str(self.output)])
        self.assertEqual(status,1)
        self.assertEqual([p.name for p in self.output.iterdir()],['catalogue_audit.json'])
        self.assertEqual(json.loads((self.output/'catalogue_audit.json').read_text()),report)

    def test_study_frame_is_deterministic_without_species_mutation(self):
        species = preview.preview_species(0)
        original = copy.deepcopy(species)
        first = preview.render_study_frame(species,12,60)
        preview.render_study_frame(species,0,60)
        again = preview.render_study_frame(species,12,60)
        self.assertEqual(first.size,(1600,900))
        self.assertEqual(first.mode,'RGB')
        self.assertEqual(first.tobytes(),again.tobytes())
        self.assertEqual(species,original)

    def test_nonmammal_study_rejected_before_creating_artifacts(self):
        species = self.species_named('Pacific Cleaner Shrimp')
        with self.assertRaises(ValueError):
            preview.encode_preview(species,self.output,.1,study=True)
        with self.assertRaises(ValueError):
            preview.render_study_frame(species,0,3)
        self.assertEqual(list(self.output.iterdir()),[])

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg required')
    def test_encoded_study_dimensions_and_frame_count(self):
        path = preview.encode_preview(preview.preview_species(0),self.output,.1,study=True)
        result = subprocess.run(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',str(path)],check=True,capture_output=True,text=True)
        streams = json.loads(result.stdout)['streams']
        self.assertEqual(len(streams),1)
        self.assertEqual(streams[0]['codec_type'],'video')
        self.assertEqual(streams[0]['nb_read_frames'],'3')
        self.assertEqual((streams[0]['width'],streams[0]['height']),(1600,900))
        self.assertEqual(list(self.output.glob('preview_*.mp4')),[])

    @unittest.skipUnless(shutil.which('ffmpeg'), 'FFmpeg required')
    def test_invalid_video_frame_preserves_existing_file(self):
        species = preview.preview_species(0)
        destination = self.output/f"{species['id']}_study.mp4"
        destination.write_bytes(b'previous')
        with patch.object(preview,'render_study_frame',return_value=Image.new('RGB',(10,10))):
            with self.assertRaises(ValueError):
                preview.encode_preview(species,self.output,.1,study=True)
        self.assertEqual(destination.read_bytes(),b'previous')
        self.assertEqual(list(self.output.glob('preview_*.mp4')),[])

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg required')
    def test_encoded_mp4_frame_count_and_no_audio(self):
        path = preview.encode_preview(preview.preview_species(0), self.output, .1)
        result = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-show_streams', '-of', 'json', str(path)], check=True, capture_output=True, text=True)
        streams = json.loads(result.stdout)['streams']
        self.assertEqual(len(streams), 1)
        self.assertEqual(streams[0]['codec_type'], 'video')
        self.assertEqual(streams[0]['nb_read_frames'], '3')
        self.assertEqual((streams[0]['width'], streams[0]['height']), (1080, 1920))
        self.assertEqual(list(self.output.glob('preview_*.mp4')), [])

    @unittest.skipUnless(shutil.which('ffmpeg'), 'FFmpeg required')
    def test_render_failure_preserves_existing_video_and_removes_partial(self):
        species = preview.preview_species(0)
        destination = self.output / f"{species['id']}_surface.mp4"
        destination.write_bytes(b'existing preview')
        with patch.object(preview, 'render_generative_frame', side_effect=RuntimeError('render failed')):
            with self.assertRaises(RuntimeError):
                preview.encode_preview(species, self.output, .1)
        self.assertEqual(destination.read_bytes(), b'existing preview')
        self.assertEqual(list(self.output.glob('preview_*.mp4')), [])


class PublicationSafetyTests(OfflineCase):
    def test_explicit_id_is_blocked_before_render_or_research(self):
        with patch.object(publication, 'is_already_used', return_value=True), \
             patch.object(publication, 'research_animal') as research, \
             patch.object(publication, 'render_generative_frame') as render:
            with self.assertRaises(RuntimeError):
                publication.generate(animal_id=0, duration=.1)
            research.assert_not_called()
            render.assert_not_called()

    def test_base_noun_variants_are_blocked(self):
        with patch.object(publication, 'is_already_used', return_value=False), \
             patch.object(publication, 'get_used_base_nouns', return_value={'SCORPION'}):
            for name in ('Scorpion', 'VOLT SCORPION', 'Giant Scorpion'):
                with self.assertRaises(RuntimeError):
                    publication.assert_unpublished({'name': name})

    def test_bad_history_entries_fail_closed(self):
        path = self.output / 'history.json'
        for content in ('{', '{}', '[{}]', '[{"species": ""}]', '[{"species": 5}]'):
            path.write_text(content)
            with self.assertRaises(RuntimeError):
                publication._load_json(path, [])

    def test_bad_used_ledger_fails_closed(self):
        path = self.output / 'used.json'
        with patch.object(researcher, 'USED_FILE', path):
            for content in ('{', '[]', '{}', '{"used": [null]}'):
                path.write_text(content)
                with self.assertRaises(RuntimeError):
                    researcher._load_used()

    def test_hash_and_difference_invariants(self):
        black = Image.new('RGB', (80, 80), 'black')
        white = Image.new('RGB', (80, 80), 'white')
        self.assertEqual(publication.compute_visual_difference(black, black), 0)
        self.assertEqual(publication.compute_visual_difference(black, white), 100)
        value = publication.compute_dhash(black)
        self.assertEqual(len(value), 16)
        self.assertEqual(publication.hamming_distance(value, value), 0)
        self.assertEqual(publication.hamming_distance('0'*16, 'f'*16), 64)
        with self.assertRaises(ValueError):
            publication.hamming_distance('bad', value)

    def test_corrupt_recent_frame_blocks_candidate(self):
        references = self.output / 'recent'
        references.mkdir()
        (references / 'recent_0.jpg').write_bytes(b'corrupt')
        with patch.object(publication, 'RECENT_FRAMES_DIR', references):
            with self.assertRaises(OSError):
                publication.verify_candidate_against_recent_buffer(engine.get_species_for_id(0))

    def test_thresholds_remain_strict(self):
        self.assertEqual(publication.MIN_VISUAL_DIFFERENCE, 2.0)
        self.assertEqual(publication.MIN_HASH_DISTANCE, 10)


class InsectRigTests(OfflineCase):
    IDS = (431,432,433,434,435,440,441)

    def test_all_supported_insects_have_six_fixed_link_legs_and_clean_reports(self):
        for animal_id in self.IDS:
            species = engine.get_species_for_id(animal_id)
            with self.subTest(name=species['name']):
                report = preview.insect_report(species)
                self.assertTrue(report['numerical_pass'],report)
                self.assertEqual(report['minimum_stance_contacts'],3)
                self.assertEqual(report['support'],'exoskeleton')
                self.assertFalse(report['specimen_validated'])
                initial = natural.insect_pose(species,0)
                for step in range(241):
                    pose = natural.insect_pose(species,step*initial['cycle_seconds']/120)
                    self.assertEqual(len(pose['limbs']),6)
                    for limb,original in zip(pose['limbs'],initial['limbs']):
                        self.assertEqual(limb['lengths'],original['lengths'])
                        self.assertLess(math.dist(limb['points'][-1],limb['target']),1e-7)
                        for a,b,length in zip(limb['points'],limb['points'][1:],limb['lengths']):
                            self.assertAlmostEqual(math.dist(a,b),length,places=7)

    def test_tripod_phase_groups_and_thoracic_roots(self):
        pose = natural.insect_pose(engine.get_species_for_id(431),0)
        groups = {}
        for limb in pose['limbs']:
            groups.setdefault(limb['phase_offset'],[]).append((limb['side'],limb['index']))
            self.assertIn(limb['points'][0][0],(-12,-33,-54))
        self.assertEqual(groups[0.0],[(-1,0),(-1,2),(1,1)])
        self.assertEqual(groups[.5],[(-1,1),(1,0),(1,2)])

    def test_mole_cricket_has_digging_forelegs_not_enlarged_jump_legs(self):
        mole = natural.insect_pose(engine.get_species_for_id(434),.3)
        locust = natural.insect_pose(engine.get_species_for_id(431),.3)
        self.assertEqual(sum(l['digging_front'] for l in mole['limbs']),2)
        self.assertFalse(any(l['enlarged_hind'] for l in mole['limbs']))
        self.assertEqual(sum(l['enlarged_hind'] for l in locust['limbs']),2)

    def test_invalid_insect_pose_inputs_fail_closed(self):
        for time in (float('nan'),float('inf'),-float('inf')):
            with self.assertRaises(ValueError): natural.insect_pose(engine.get_species_for_id(431),time)
            with self.assertRaises(ValueError): natural.insect_pose(engine.get_species_for_id(431),0,time)
        with self.assertRaises(ValueError): natural.insect_pose(engine.get_species_for_id(0),0)
        species = engine.get_species_for_id(440)
        self.assertEqual(natural.insect_pose(species,-.2),natural.insect_pose(species,-.2))

    def test_insect_surface_overlay_and_guide_consume_identical_pose(self):
        species = engine.get_species_for_id(431)
        expected = natural.insect_pose(species,.4)
        sim = SimpleNamespace(x=400,y=400,angle=0)
        for mode in ('surface','overlay','skeleton'):
            candidate = {**species,'render_mode':mode}
            image = Image.new('RGBA',(800,800))
            with patch.object(natural,'insect_pose',return_value=expected) as pose, \
                 patch.object(natural.Pen,'line',autospec=True,wraps=natural.Pen.line) as line:
                natural.draw_special_insect(ImageDraw.Draw(image),sim,candidate,.4)
                pose.assert_called_once_with(candidate,.4)
                if mode != 'surface':
                    for limb in expected['limbs']:
                        self.assertTrue(any(call.args[1] == limb['points'] for call in line.call_args_list))
            self.assertIsNotNone(image.getbbox())

    def test_all_insect_modes_fit_shared_camera_and_have_distinct_pixels(self):
        for animal_id in self.IDS:
            species = engine.get_species_for_id(animal_id)
            original = copy.deepcopy(species)
            bounds = engine.fixed_camera_bounds(species)
            frames = []
            for mode in ('surface','overlay','skeleton'):
                candidate = {**species,'render_mode':mode}
                self.assertEqual(engine.fixed_camera_bounds(candidate),bounds)
                for frame_idx in (0,45,179,449,899):
                    sim = engine._simulation_for_frame(candidate,frame_idx)
                    x0,y0,x1,y1 = engine.creature_geometry_bounds(candidate,sim,frame_idx/engine.FPS*engine.MOTION_RATE)
                    self.assertGreaterEqual(min(x0-sim.x-bounds[0],y0-sim.y-bounds[1],bounds[2]-(x1-sim.x),bounds[3]-(y1-sim.y)),0)
                image = engine.render_generative_frame(candidate,45,180)
                frames.append(image.crop((110,340,970,832)).tobytes())
            self.assertEqual(len(set(frames)),3)
            self.assertEqual(species,original)

    def test_insect_report_detects_local_stance_sliding(self):
        original = natural.insect_pose
        def sliding(*args,**kwargs):
            pose = original(*args,**kwargs)
            for limb in pose['limbs']:
                x,y = limb['contact']
                limb['contact'] = (x+limb['phase']*.05,y)
            return pose
        with patch.object(preview,'insect_pose',side_effect=sliding):
            report = preview.insect_report(engine.get_species_for_id(431))
        self.assertFalse(report['numerical_pass'])
        self.assertFalse(report['numerical_checks']['max_local_stance_drift'])

    def test_insect_report_detects_unreachable_target_and_bad_links(self):
        original = natural.insect_pose
        def broken(*args,**kwargs):
            pose = original(*args,**kwargs)
            pose['limbs'][0]['lengths'][0] += 1
            x,y = pose['limbs'][0]['target']
            pose['limbs'][0]['target'] = (x+5,y)
            return pose
        with patch.object(preview,'insect_pose',side_effect=broken):
            report = preview.insect_report(engine.get_species_for_id(431))
        self.assertFalse(report['numerical_checks']['max_link_length_error'])
        self.assertFalse(report['numerical_checks']['max_target_error'])

    def test_insect_cli_comparison_and_numeric_json(self):
        with patch('builtins.print'):
            self.assertEqual(preview.main(['--animal-id','431','--mode','overlay','--comparison','--output-dir',str(self.output)]),0)
        species = engine.get_species_for_id(431)
        report = json.loads((self.output/f"{species['id']}_overlay.json").read_text())
        self.assertTrue(report['insect_report']['numerical_pass'])
        with Image.open(self.output/f"{species['id']}_comparison.jpg") as image:
            self.assertEqual(image.size,(1720,490))

    def test_insect_study_timeline_uses_same_pose_and_is_deterministic(self):
        species = engine.get_species_for_id(440)
        original = copy.deepcopy(species)
        with patch.object(preview,'insect_pose',wraps=natural.insect_pose) as pose:
            first = preview.render_study_frame(species,45,180)
            pose.assert_called_once_with(species,45/engine.FPS*engine.MOTION_RATE)
        self.assertEqual(first.size,(1600,900))
        self.assertEqual(first.tobytes(),preview.render_study_frame(species,45,180).tobytes())
        self.assertEqual(species,original)

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg required')
    def test_insect_study_encodes_silent_video(self):
        path = preview.encode_preview(preview.preview_species(431),self.output,.1,study=True)
        probe = subprocess.run(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',str(path)],capture_output=True,text=True,check=True)
        streams = json.loads(probe.stdout)['streams']
        self.assertEqual(len(streams),1)
        self.assertEqual(streams[0]['nb_read_frames'],'3')
        self.assertEqual(streams[0]['pix_fmt'],'yuv420p')
        self.assertEqual(streams[0]['codec_type'],'video')


class SpiderRigTests(OfflineCase):
    IDS = (20,442,443,444,445,446,447,448,449,451,452,453,454,465,466,467,468,469,470,471)

    def test_spider_gate_excludes_other_orders_and_misleading_names(self):
        actual = tuple(i for i,s in enumerate(engine.load_encyclopedia()) if preview.supports_spider_rig(s))
        self.assertEqual(actual,self.IDS)
        for animal_id in (0,18,450,455,459,460):
            species = engine.get_species_for_id(animal_id)
            self.assertFalse(preview.supports_spider_rig(species))
            with self.assertRaises(ValueError): natural.spider_pose(species,0)
            if animal_id and animal_id != 18:
                with self.assertRaises(ValueError): preview.preview_species(animal_id,'overlay')
        fake = dict(name='SPIDER CRAB',class_type='crustacean',morphology='spider')
        self.assertFalse(preview.supports_spider_rig(fake))

    def test_twenty_spiders_have_fixed_links_and_clean_two_cycle_reports(self):
        for animal_id in self.IDS:
            species = engine.get_species_for_id(animal_id)
            with self.subTest(animal_id=animal_id):
                report = preview.spider_report(species)
                self.assertTrue(report['numerical_pass'],report)
                self.assertEqual(report['walking_legs'],8)
                self.assertEqual(report['minimum_stance_contacts'],4)
                self.assertEqual(report['rig_type'],'spider')
                self.assertEqual(report['support'],'exoskeleton')
                self.assertFalse(report['specimen_validated'])
                initial = natural.spider_pose(species,0)
                for sample in range(121):
                    pose = natural.spider_pose(species,initial['cycle_seconds']*sample/60)
                    for limb,first in zip(pose['limbs'],initial['limbs']):
                        self.assertEqual(limb['lengths'],first['lengths'])
                        self.assertLess(math.dist(limb['points'][-1],limb['target']),1e-7)

    def test_prosoma_roots_tetrapod_groups_and_separate_pedipalps(self):
        for animal_id in self.IDS:
            pose = natural.spider_pose(engine.get_species_for_id(animal_id),0)
            self.assertEqual(len(pose['limbs']),8)
            self.assertEqual(len(pose['pedipalps']),2)
            rx,ry = pose['prosoma'][2:]
            groups = {}
            for limb in pose['limbs']:
                x,y = limb['points'][0]
                self.assertLessEqual((x/rx)**2+(y/ry)**2,1)
                groups.setdefault(limb['phase_offset'],[]).append((limb['side'],limb['index']))
            self.assertEqual(groups[0.0],[(-1,0),(-1,2),(1,1),(1,3)])
            self.assertEqual(groups[.5],[(-1,1),(-1,3),(1,0),(1,2)])
            self.assertTrue(all(palp[0][0] > 0 for palp in pose['pedipalps']))

    def test_family_silhouettes_are_distinct(self):
        families = {}
        for animal_id in (20,444,446,447,451,452):
            pose = natural.spider_pose(engine.get_species_for_id(animal_id),0)
            families[pose['family']] = (pose['prosoma'],pose['abdomen'],pose['limb_width'])
        self.assertEqual(len(families),6)
        self.assertEqual(len(set(families.values())),6)

    def test_spider_pose_rejects_nonfinite_inputs_and_is_deterministic(self):
        species = engine.get_species_for_id(465)
        original = copy.deepcopy(species)
        for bad in (float('nan'),float('inf'),-float('inf')):
            with self.assertRaises(ValueError): natural.spider_pose(species,bad)
            with self.assertRaises(ValueError): natural.spider_pose(species,0,bad)
        self.assertEqual(natural.spider_pose(species,-.2),natural.spider_pose(species,-.2))
        self.assertEqual(species,original)

    def test_spider_modes_share_pose_and_body_envelopes(self):
        species = engine.get_species_for_id(465)
        expected = natural.spider_pose(species,.4)
        sim = SimpleNamespace(x=400,y=400,angle=.6)
        for mode in ('surface','overlay','skeleton'):
            candidate = {**species,'render_mode':mode}
            image = Image.new('RGBA',(800,800))
            with patch.object(natural,'spider_pose',return_value=expected) as pose, \
                 patch.object(natural.Pen,'oval',autospec=True) as oval, \
                 patch.object(natural.Pen,'line',autospec=True) as line:
                natural.draw_spider(ImageDraw.Draw(image),sim,candidate,.4)
                pose.assert_called_once_with(candidate,.4)
                for key in ('prosoma','abdomen'):
                    self.assertTrue(any(call.args[1:5] == expected[key] for call in oval.call_args_list))
                for palp in expected['pedipalps']:
                    self.assertTrue(any(call.args[1] == palp for call in line.call_args_list))
                if mode != 'surface':
                    for limb in expected['limbs']:
                        self.assertTrue(any(call.args[1] == limb['points'] for call in line.call_args_list))

    def test_all_spider_modes_fit_camera_with_distinct_pixels(self):
        for animal_id in self.IDS:
            species = engine.get_species_for_id(animal_id)
            original = copy.deepcopy(species)
            bounds = engine.fixed_camera_bounds(species)
            pixels = []
            for mode in ('surface','overlay','skeleton'):
                subject = {**species,'render_mode':mode}
                self.assertEqual(bounds,engine.fixed_camera_bounds(subject))
                for frame_idx in (0,45,179,449,899):
                    sim = engine._simulation_for_frame(subject,frame_idx)
                    box = engine.creature_geometry_bounds(subject,sim,frame_idx/engine.FPS*engine.MOTION_RATE)
                    margin = min(box[0]-sim.x-bounds[0],box[1]-sim.y-bounds[1],bounds[2]-(box[2]-sim.x),bounds[3]-(box[3]-sim.y))
                    self.assertGreaterEqual(margin,0)
                pixels.append(engine.render_generative_frame(subject,45,180).crop((110,340,970,832)).tobytes())
            self.assertEqual(len(set(pixels)),3)
            self.assertEqual(species,original)

    def test_spider_report_detects_sliding_stretch_and_bad_targets(self):
        original = natural.spider_pose
        def broken(*args,**kwargs):
            pose = original(*args,**kwargs)
            for limb in pose['limbs']:
                x,y = limb['contact']
                limb['contact'] = (x+limb['phase']*.05,y)
                limb['lengths'][0] += 1
                x,y = limb['target']
                limb['target'] = (x+5,y)
            return pose
        with patch.object(preview,'spider_pose',side_effect=broken):
            report = preview.spider_report(engine.get_species_for_id(465))
        self.assertFalse(report['numerical_pass'])
        for key in ('max_local_stance_drift','max_link_length_error','max_target_error'):
            self.assertFalse(report['numerical_checks'][key])

    def test_planar_reports_reject_nan_and_missing_legs(self):
        for name,original,reporter,animal_id in (
                ('spider_pose',natural.spider_pose,preview.spider_report,465),
                ('insect_pose',natural.insect_pose,preview.insect_report,431)):
            for fault in ('nan','missing','short_chain'):
                def broken(*args,**kwargs):
                    pose = original(*args,**kwargs)
                    if fault == 'nan': pose['limbs'][0]['points'][1] = (float('nan'),0)
                    elif fault == 'missing': pose['limbs'].pop()
                    else: pose['limbs'][0]['points'].pop()
                    return pose
                with patch.object(preview,name,side_effect=broken), self.assertRaises(ValueError):
                    reporter(engine.get_species_for_id(animal_id))

    def test_spider_cli_comparison_and_rig_report(self):
        with patch('builtins.print'):
            self.assertEqual(preview.main(['--animal-id','465','--mode','overlay','--comparison','--output-dir',str(self.output)]),0)
        species = engine.get_species_for_id(465)
        report = json.loads((self.output/f"{species['id']}_overlay.json").read_text())
        self.assertTrue(report['spider_report']['numerical_pass'])
        with Image.open(self.output/f"{species['id']}_comparison.jpg") as image:
            self.assertEqual(image.size,(1720,490))

    def test_spider_study_has_eight_synchronized_timeline_rows(self):
        species = engine.get_species_for_id(465)
        original = copy.deepcopy(species)
        with patch.object(preview,'spider_pose',wraps=natural.spider_pose) as pose:
            image = preview.render_study_frame(species,45,180)
            pose.assert_called_once_with(species,45/engine.FPS*engine.MOTION_RATE)
        self.assertEqual(image.size,(1600,900))
        self.assertEqual(image.tobytes(),preview.render_study_frame(species,45,180).tobytes())
        current = natural.spider_pose(species,45/engine.FPS*engine.MOTION_RATE)
        phase = (45/engine.FPS*engine.MOTION_RATE/current['cycle_seconds'])%1
        marker_x = round(210+phase*1100)
        for index in range(8):
            self.assertEqual(image.getpixel((marker_x,647+index*21+8)),(238,245,248))
        self.assertEqual(species,original)

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg required')
    def test_spider_study_encodes_silent_three_frame_video(self):
        path = preview.encode_preview(preview.preview_species(465),self.output,.1,study=True)
        probe = subprocess.run(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',str(path)],capture_output=True,text=True,check=True)
        streams = json.loads(probe.stdout)['streams']
        self.assertEqual(len(streams),1)
        self.assertEqual(streams[0]['codec_type'],'video')
        self.assertEqual(streams[0]['nb_read_frames'],'3')
        self.assertEqual(streams[0]['pix_fmt'],'yuv420p')
        self.assertEqual((streams[0]['width'],streams[0]['height']),(1600,900))


class AxialRegressionTests(OfflineCase):
    def test_all_56_axial_rigs_have_clean_reports_and_fixed_links(self):
        ids = [i for i,s in enumerate(engine.load_encyclopedia()) if resolve_body_plan(s) in natural.AXIAL_PLANS]
        self.assertEqual(len(ids),56)
        for animal_id in ids:
            species = engine.get_species_for_id(animal_id)
            with self.subTest(name=species['name']):
                report = preview.axial_report(species)
                self.assertTrue(report['numerical_pass'],report)
                self.assertEqual(report['rig_segments'],52)
                self.assertFalse(report['specimen_validated'])

    def test_axial_report_detects_stretched_chain(self):
        original = natural.axial_pose
        def stretched(*args,**kwargs):
            pose = original(*args,**kwargs)
            x,y = pose['points'][-1]
            pose['points'][-1] = (x+5,y)
            return pose
        species = next(engine.get_species_for_id(i) for i,s in enumerate(engine.load_encyclopedia()) if resolve_body_plan(s) == 'eel')
        with patch.object(preview,'axial_pose',side_effect=stretched):
            report = preview.axial_report(species)
        self.assertFalse(report['numerical_pass'])
        self.assertFalse(report['numerical_checks']['max_segment_length_error'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
