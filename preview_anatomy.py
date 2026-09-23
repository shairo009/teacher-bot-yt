"""Offline-only 2D anatomy previews. No uploader, research or publication state imports."""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

from PIL import Image, ImageDraw
from src.anatomy_profiles import anatomy_summary, mammal_profile, supports_spider_rig, supports_scorpion_rig
from src.natural_anatomy_renderer import (
    gait_parameters, mammal_pose, axial_pose, AXIAL_PLANS, insect_pose, INSECT_PLANS, spider_pose, scorpion_pose,
)
from src.generative_dragon_engine import (
    FPS, WIDTH, HEIGHT, MOTION_RATE, get_font, get_species_for_id, load_encyclopedia,
    render_generative_frame, fixed_camera_bounds, camera_zoom, creature_geometry_bounds,
    new_preview_simulator, CAMERA_LAST_FRAME, CAMERA_SAMPLE_STEP,
)

ROOT = Path(__file__).resolve().parent
OUTPUT_ROOT = ROOT / "outputs"
DEFAULT_IDS = [0, 1, 15, 17, 586, 547, 351, 280, 576, 450, 231, 403]


def output_directory(value: str | Path | None = None) -> Path:
    allowed = ROOT.resolve() / "outputs"
    path = (Path(value) if value else OUTPUT_ROOT / "anatomy_preview").resolve()
    if not path.is_relative_to(allowed):
        raise ValueError("Preview output must be inside teacher-bot/outputs; source and publication ledgers are protected")
    path.mkdir(parents=True, exist_ok=True)
    return path


def output_file(output: Path, name: str) -> Path:
    """Reject traversal and pre-existing file symlinks before writing previews."""
    if Path(name).name != name:
        raise ValueError("Preview filenames must not contain directories")
    directory = output_directory(output)
    path = directory / name
    if path.is_symlink() or path.is_dir() or path.resolve().parent != directory:
        raise ValueError("Preview output must not overwrite a symlink target")
    return path


@contextmanager
def atomic_output(output: Path, name: str):
    """Replace complete artifacts; never truncate existing files or hardlinks."""
    destination = output_file(output, name)
    fd, temporary = tempfile.mkstemp(prefix="artifact_", suffix=destination.suffix, dir=destination.parent)
    os.close(fd)
    partial = Path(temporary)
    try:
        yield partial
        # Recheck in case the destination changed while rendering/encoding.
        output_file(output, name)
        partial.replace(destination)
    finally:
        partial.unlink(missing_ok=True)


def save_image(image: Image.Image, output: Path, name: str, **options) -> Path:
    with atomic_output(output, name) as partial:
        image.save(partial, **options)
    return output_file(output, name)


def save_report(report, output: Path, name: str) -> Path:
    with atomic_output(output, name) as partial:
        partial.write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    return output_file(output, name)


def timeline_frames(duration: float) -> int:
    if not math.isfinite(duration) or not 0.1 <= duration <= 30:
        raise ValueError("Preview duration must be finite and between 0.1 and 30 seconds")
    return max(1, round(duration * FPS))


def preview_species(animal_id: int, mode: str = "surface") -> dict:
    species = get_species_for_id(animal_id)
    if mode not in anatomy_summary(species)["diagnostic_modes"]:
        raise ValueError(f"{mode} is not implemented for {species['name']}; use surface mode")
    species["render_mode"] = mode
    return species


def create_contact_sheet(ids: list[int], output: Path) -> Path:
    if not ids or len(ids) > 48:
        raise ValueError("Contact sheets require 1 to 48 animal IDs")
    species_list = [preview_species(i) for i in ids]
    columns = min(4, len(ids))
    cell_w, cell_h = 420, 300
    sheet = Image.new("RGB", (columns*cell_w, 110+math.ceil(len(ids)/columns)*cell_h), (12, 20, 30))
    draw = ImageDraw.Draw(sheet)
    draw.text((24, 18), "2D ANATOMY / MOTION STUDIES", font=get_font(26, bold=True), fill=(228, 237, 244))
    draw.text((24, 61), "Family-level approximations. Rig ratios are not specimen measurements.", font=get_font(16), fill=(149, 171, 186))
    report = []
    for index, species in enumerate(species_list):
        x, y = (index % columns)*cell_w, 110+(index//columns)*cell_h
        frame = render_generative_frame(species, 45, 180)
        crop = frame.crop((110, 340, 970, 832)).resize((cell_w-12, 234), Image.Resampling.LANCZOS)
        sheet.paste(crop, (x+6, y+37))
        label = f"{species['animal_id']:03d} / {species['name']}"
        font = get_font(15, bold=True)
        while font.getlength(label) > cell_w-24:
            font = get_font(font.size-1, bold=True)
        draw.text((x+12, y+8), label, font=font, fill=(231, 239, 245))
        summary = anatomy_summary(species)
        draw.text((x+12, y+275), summary['body_plan'], font=get_font(13), fill=(131, 197, 191))
        report.append({"animal_id": species["animal_id"], "name": species["name"], **summary})
    path = save_image(sheet, output, "contact_sheet.jpg", quality=94)
    save_report(report, output, "contact_sheet_report.json")
    return path


def create_comparison(animal_id: int, frame_idx: int, output: Path) -> Path:
    """Aligned diagnostic views at one timestamp and one fixed camera scale."""
    modes = ("surface", "overlay", "skeleton")
    subject = preview_species(animal_id)
    labels = ("SURFACE", "OVERLAY", "JOINT GUIDE (EXOSKELETON)") if anatomy_summary(subject)["body_plan"] in INSECT_PLANS or supports_spider_rig(subject) or supports_scorpion_rig(subject) else tuple(mode.upper() for mode in modes)
    subjects = [preview_species(animal_id, mode) for mode in modes]
    sheet = Image.new("RGB", (1720, 490), (12, 20, 30))
    draw = ImageDraw.Draw(sheet)
    draw.text((24, 18), subjects[0]["name"] + " / LINKED 2D RIG", font=get_font(26, bold=True), fill=(231, 239, 245))
    draw.text((24, 60), f"Same pose and camera / frame {frame_idx} / family-level approximation, not a specimen reconstruction", font=get_font(16), fill=(151, 175, 187))
    for index, subject in enumerate(subjects):
        x = 10 + index*570
        draw.text((x+14, 108), labels[index], font=get_font(19, bold=True), fill=(135, 211, 203))
        image = render_generative_frame(subject, frame_idx, 180)
        crop = image.crop((110, 340, 970, 832)).resize((560, 320), Image.Resampling.LANCZOS)
        sheet.paste(crop, (x, 148))
    return save_image(sheet, output, f"{subjects[0]['id']}_comparison.jpg", quality=94)


def gait_report(species: dict) -> dict:
    """Numerical rig checks across a complete cycle, not biological validation."""
    if anatomy_summary(species)["body_plan"] != "mammal":
        raise ValueError("Gait diagnostics are currently implemented for mammals only")
    p = mammal_profile(species)
    stride, duty = gait_parameters(p)
    bone_error = height_error = contact_drift = 0.0
    penetration = swing_clearance = 0.0
    anchors = {}
    stance_samples = 0
    for step in range(121):
        travel = stride*step/120
        _, _, limbs = mammal_pose(species, travel/72, travel)
        for limb in limbs:
            points = limb["points"]
            bone_error = max(bone_error, *(abs(math.dist(a,b)-length)
                                         for a,b,length in zip(points,points[1:],limb["lengths"])))
            key = (limb["side"], limb["front"])
            # Kangaroo forelimbs are unsupported hands, not ground-contact feet.
            if not (p.family == "kangaroo" and limb["front"]):
                clearance = p.legs-points[-1][1]
                penetration = max(penetration, -clearance)
                if not limb["planted"]:
                    swing_clearance = max(swing_clearance, clearance)
            if limb["planted"]:
                stance_samples += 1
                height_error = max(height_error, abs(points[-1][1]-p.legs))
                # Compare to the first contact in this stance, not only to the
                # adjacent sample: slow cumulative sliding must not be hidden.
                if key not in anchors or limb["phase"] < anchors[key]["phase"]:
                    anchors[key] = {"x": limb["contact_x"], "phase": limb["phase"]}
                contact_drift = max(contact_drift, abs(limb["contact_x"]-anchors[key]["x"]))
            else:
                anchors.pop(key, None)
    start = mammal_pose(species, 0, 0)[2]
    end = mammal_pose(species, stride/72, stride)[2]
    cycle_error = max(math.dist(a,b) for first,last in zip(start,end)
                      for a,b in zip(first["points"],last["points"]))
    position_gap = velocity_gap = 0.0
    epsilon = stride*1e-6
    for index, limb in enumerate(start):
        for boundary in (duty, 1.0):
            center = stride*(boundary-limb["phase"])
            samples = [mammal_pose(species, x/72, x)[2][index]["points"][-1]
                       for x in (center-epsilon, center, center+epsilon)]
            before, at, after = samples
            position_gap = max(position_gap, math.dist(before,after))
            velocity_gap = max(velocity_gap, math.hypot(*(
                (after[k]-2*at[k]+before[k])/epsilon for k in (0,1))))
    errors = {"max_bone_length_error": bone_error,
              "max_planted_height_error": height_error,
              "max_stance_world_drift": contact_drift,
              "max_ground_penetration": penetration,
              "max_limb_cycle_closure_error": cycle_error,
              "max_boundary_position_gap": position_gap,
              "max_boundary_velocity_gap": velocity_gap}
    tolerances = {key: 1e-7 for key in errors}
    tolerances.update(max_boundary_position_gap=1e-3, max_boundary_velocity_gap=1e-2)
    checks = {key: math.isfinite(value) and value <= tolerances[key] for key,value in errors.items()}
    return {"animal_id": species["animal_id"], "name": species["name"],
            "gait": p.gait, "stride_rig_units": stride, "stance_fraction": duty,
            "cycle_seconds_at_preview_speed": stride/(72*MOTION_RATE), "numerical_samples": 121,
            "planted_limb_samples": stance_samples, **errors,
            "max_sampled_swing_clearance": swing_clearance,
            "boundary_sample_epsilon": epsilon,
            "velocity_units": "rig displacement per rig unit of travel",
            "numerical_checks": checks, "numerical_tolerances": tolerances,
            "numerical_pass": all(checks.values()),
            "cycle_scope": "limb rig only; secondary tail sway is not stride-periodic",
            "units": "procedural rig units, not centimeters",
            "offline": True, "uploaded": False, **anatomy_summary(species)}


def create_gait_sheet(animal_id: int, output: Path) -> Path:
    """Eight aligned overlay poses and stance/swing indicators over one stride."""
    species = preview_species(animal_id, "overlay")
    report = gait_report(species)
    cell_w, cell_h = 430, 332
    sheet = Image.new("RGB", (1720, 804), (12,20,30))
    draw = ImageDraw.Draw(sheet)
    title = species["name"] + " / ONE GAIT CYCLE"
    draw.text((24,18), title, font=get_font(25,bold=True), fill=(231,239,245))
    draw.text((24,57), "Same camera / shared skin, head, tail and limb rig / near and far sides are layered in 2D", font=get_font(16), fill=(154,179,192))
    draw.text((24,86), "Four limbs: F=front, H=hind; N=near, F=far. Green=stance, amber=swing. Overlap is expected in a lateral view.", font=get_font(15), fill=(154,179,192))
    cycle_frames = report["cycle_seconds_at_preview_speed"]*FPS
    report["poses"] = []
    for index in range(8):
        frame_idx = round(cycle_frames*index/7)
        time = frame_idx/FPS*MOTION_RATE
        _, _, limbs = mammal_pose(species,time)
        frame = render_generative_frame(species,frame_idx,max(180,math.ceil(cycle_frames)+1))
        x,y = (index%4)*cell_w,126+(index//4)*cell_h
        draw.text((x+12,y+3), f"{index+1:02} / {frame_idx/FPS:.2f}s / phase {time*72/report['stride_rig_units']:.2f}", font=get_font(16,bold=True), fill=(231,239,245))
        crop = frame.crop((110,340,970,832)).resize((418,239), Image.Resampling.LANCZOS)
        sheet.paste(crop,(x+6,y+34))
        statuses = []
        for offset,limb in enumerate(limbs):
            label = ("F" if limb["front"] else "H")+("N" if limb["side"]==1 else "F")
            color = (123,220,177) if limb["planted"] else (236,187,111)
            draw.rounded_rectangle((x+9+offset*105,y+285,x+109+offset*105,y+310),radius=4,outline=color)
            draw.text((x+15+offset*105,y+291),label+(" stance" if limb["planted"] else " swing"),font=get_font(12),fill=color)
            statuses.append({"limb": label, "planted": limb["planted"], "points": limb["points"], "lengths": limb["lengths"]})
        report["poses"].append({"frame":frame_idx,"time_seconds":frame_idx/FPS,"limbs":statuses})
    path = save_image(sheet,output,f"{species['id']}_gait.jpg",quality=94)
    save_report(report,output,f"{species['id']}_gait.json")
    return path


def axial_report(species: dict) -> dict:
    """A full rig-local wave cycle; no claim about substrate contact or biology."""
    initial = axial_pose(species,0)
    cycle = initial['cycle_seconds']
    bone_error = 0.0
    max_motion = 0.0
    max_turn = 0.0
    for index in range(121):
        pose = axial_pose(species,cycle*index/120)
        points = pose['points']
        bone_error = max(bone_error, *(abs(math.dist(a,b)-length) for a,b,length in
                                       zip(points,points[1:],pose['segment_lengths'])))
        max_motion = max(max_motion, *(math.dist(a,b) for a,b in zip(initial['points'],points)))
        angles = [math.atan2(b[1]-a[1],b[0]-a[0]) for a,b in zip(points,points[1:])]
        max_turn = max(max_turn, *(abs((b-a+math.pi)%math.tau-math.pi) for a,b in zip(angles,angles[1:])))
    final = axial_pose(species,cycle)
    closure = max(math.dist(a,b) for a,b in zip(initial['points'],final['points']))
    epsilon = cycle*1e-6
    before, after = axial_pose(species,-epsilon), axial_pose(species,epsilon)
    velocity_gap = max(math.hypot(*((a[k]-2*b[k]+c[k])/epsilon for k in (0,1)))
                       for a,b,c in zip(before['points'],initial['points'],after['points']))
    metrics = {'max_segment_length_error': bone_error, 'max_cycle_closure_error': closure,
               'max_boundary_velocity_gap': velocity_gap, 'max_adjacent_turn_radians': max_turn}
    tolerances = {'max_segment_length_error': 1e-7, 'max_cycle_closure_error': 1e-7,
                  'max_boundary_velocity_gap': .01, 'max_adjacent_turn_radians': .40}
    checks = {key: math.isfinite(value) and value <= tolerances[key] for key,value in metrics.items()}
    checks['nonzero_wave_motion'] = math.isfinite(max_motion) and max_motion > 1
    return {'animal_id': species['animal_id'], 'name': species['name'], **anatomy_summary(species),
            'rig_segments': len(initial['segment_lengths']), 'numerical_samples': 121,
            'cycle_seconds_at_preview_speed': cycle/MOTION_RATE,
            'total_length_rig_units': sum(initial['segment_lengths']),
            'max_sampled_node_displacement': max_motion, **metrics,
            'numerical_checks': checks, 'numerical_tolerances': tolerances,
            'numerical_pass': all(checks.values()), 'offline': True, 'uploaded': False,
            'scope': 'Rig-local axial wave only. Root steering, tongue and decorations are not required to loop. No contact, friction or fluid simulation; schematic guide is not a measured skeleton.'}


def insect_report(species: dict) -> dict:
    return planar_limb_report(species, insect_pose, 6, 36.0)


def spider_report(species: dict) -> dict:
    return planar_limb_report(species, spider_pose, 8, 32.0)


def scorpion_report(species: dict) -> dict:
    """Leg checks plus independent fixed-link tail and pincer motion checks."""
    report = planar_limb_report(species, scorpion_pose, 8, 28.0)
    initial = scorpion_pose(species, 0)
    cycle = initial['appendage_cycle_seconds']
    if not math.isfinite(cycle) or cycle <= 0:
        raise ValueError('Scorpion appendage cycle must be finite and positive')

    def chains(pose):
        if len(pose['tail']) != 6 or len(pose['tail_lengths']) != 5 or len(pose['pedipalps']) != 2:
            raise ValueError('Scorpion guide requires five tail links and two separate pedipalps')
        result = [(pose['tail'], pose['tail_lengths'])]
        for palp in pose['pedipalps']:
            if len(palp['points']) != 3 or len(palp['lengths']) != 2 or len(palp['fingers']) != 2 or len(palp['finger_lengths']) != 2:
                raise ValueError('Malformed scorpion pincer guide')
            result.append((palp['points'],palp['lengths']))
            result.extend((finger,[length]) for finger,length in zip(palp['fingers'],palp['finger_lengths']))
        for points,lengths in result:
            if len(points) != len(lengths)+1 or not all(math.isfinite(v) for p in points for v in p) or not all(math.isfinite(v) and v > 0 for v in lengths):
                raise ValueError('Invalid scorpion appendage links')
        return result

    reference = chains(initial)
    link_error = rest_drift = 0.0
    for step in range(121):
        pose = scorpion_pose(species,cycle*step/120)
        for (points,lengths),(_,rest) in zip(chains(pose),reference):
            link_error = max(link_error,*(abs(math.dist(a,b)-length) for a,b,length in zip(points,points[1:],lengths)))
            rest_drift = max(rest_drift,*(abs(a-b) for a,b in zip(lengths,rest)))
    final = chains(scorpion_pose(species,cycle))
    closure = max(math.dist(a,b) for (before,_),(after,_) in zip(reference,final) for a,b in zip(before,after))
    metrics = dict(max_appendage_link_error=link_error, max_appendage_rest_length_drift=rest_drift,
                   max_appendage_cycle_closure_error=closure)
    report.update(metrics)
    report['numerical_tolerances'].update({key:1e-7 for key in metrics})
    report['numerical_checks'].update({key:math.isfinite(v) and v <= 1e-7 for key,v in metrics.items()})
    report.update(numerical_pass=all(report['numerical_checks'].values()), metasomal_links=5,
                  chelate_pedipalps=2, telson_separate=True, appendage_samples=121,
                  appendage_cycle_seconds_at_preview_speed=cycle/MOTION_RATE,
                  scope='Planar rig-local walking and independent pincer/tail cycles. Five metasomal links plus separate telson; tail splays in the 2D plane, not a raised arch. No strike, venom, elevation or force simulation. Exoskeleton guides are schematic; proportions and gait are not specimen validated.')
    return report


def planar_limb_report(species, pose_function, leg_count, speed) -> dict:
    """Shared fixed-link diagnostics for six-leg insects and eight-leg arachnids."""
    def pose_at(time, travel=None):
        pose = pose_function(species,time,travel)
        if len(pose['limbs']) != leg_count:
            raise ValueError('Planar diagnostic rig has an unexpected leg count')
        for limb in pose['limbs']:
            if len(limb['points']) != 4 or len(limb['lengths']) != 3:
                raise ValueError('Planar diagnostic rig must have three links per leg')
            numbers = [value for point in limb['points']+[limb['target'],limb['contact']] for value in point]
            numbers += limb['lengths']+[limb['phase'],limb['phase_offset']]
            if not all(math.isfinite(value) for value in numbers) or min(limb['lengths']) <= 0:
                raise ValueError('Nonfinite or nonpositive planar rig geometry')
        return pose
    initial = pose_at(0)
    stride, cycle = initial['stride'], initial['cycle_seconds']
    link_error = target_error = drift = rest_drift = contact_error = 0.0
    min_stance = leg_count
    anchors = {}
    for index in range(241):
        travel = stride*index/120
        pose = pose_at(travel/speed,travel)
        min_stance = min(min_stance,sum(limb['planted'] for limb in pose['limbs']))
        for j,limb in enumerate(pose['limbs']):
            points = limb['points']
            rest_drift = max(rest_drift,*(abs(a-b) for a,b in zip(limb['lengths'],initial['limbs'][j]['lengths'])))
            contact_error = max(contact_error,math.dist(limb['contact'],(points[-1][0]+travel,points[-1][1])))
            link_error = max(link_error,*(abs(math.dist(a,b)-length) for a,b,length in
                                         zip(points,points[1:],limb['lengths'])))
            target_error = max(target_error,math.dist(points[-1],limb['target']))
            if limb['planted']:
                if j not in anchors or limb['phase'] < anchors[j][0]:
                    anchors[j] = (limb['phase'],limb['contact'])
                drift = max(drift,math.dist(anchors[j][1],limb['contact']))
            else:
                anchors.pop(j,None)
    final = pose_at(cycle)
    closure = max(math.dist(a,b) for first,last in zip(initial['limbs'],final['limbs'])
                  for a,b in zip(first['points'],last['points']))
    position_gap = velocity_gap = 0.0
    epsilon = stride*1e-6
    for j,limb in enumerate(initial['limbs']):
        for boundary in (initial['duty'],1.0):
            center = stride*(boundary-limb['phase_offset'])
            before,at,after = [pose_at(x/speed,x)['limbs'][j]['points'][-1]
                              for x in (center-epsilon,center,center+epsilon)]
            position_gap = max(position_gap,math.dist(before,after))
            velocity_gap = max(velocity_gap,math.hypot(*((a-2*b+c)/epsilon for a,b,c in zip(before,at,after))))
    metrics = {'max_link_length_error': link_error, 'max_target_error': target_error,
               'max_rest_length_drift': rest_drift, 'max_contact_transform_error': contact_error,
               'max_local_stance_drift': drift, 'max_cycle_closure_error': closure,
               'max_boundary_position_gap': position_gap,'max_boundary_velocity_gap': velocity_gap}
    tolerances = {key: 1e-7 for key in metrics}
    tolerances.update(max_boundary_position_gap=.001,max_boundary_velocity_gap=.01)
    checks = {key: math.isfinite(value) and value <= tolerances[key] for key,value in metrics.items()}
    checks['six_legs' if leg_count == 6 else 'eight_legs'] = len(initial['limbs']) == leg_count
    checks['at_least_three_stance_contacts' if leg_count == 6 else 'at_least_four_stance_contacts'] = min_stance >= leg_count//2
    return {'animal_id': species['animal_id'],'name': species['name'],**anatomy_summary(species),
            'numerical_samples': 241,'sampled_cycles': 2,'walking_legs':leg_count,
            'cycle_seconds_at_preview_speed': cycle/MOTION_RATE,
            'minimum_stance_contacts': min_stance, **metrics, 'numerical_tolerances': tolerances,
            'boundary_sample_epsilon': epsilon, 'numerical_checks': checks,'numerical_pass': all(checks.values()),
            'offline': True,'uploaded': False,
            'scope': 'Planar rig-local contacts only, not world-space planted feet during steering. No elevation, forces, jumping or flight; three links per leg are schematic exoskeleton guides, not internal bones.'}


def catalogue_audit() -> dict:
    """Audit routing and numeric mammal/axial/insect rigs without publishing."""
    entries = []
    counts = {}
    for animal_id in range(len(load_encyclopedia())):
        species = get_species_for_id(animal_id)
        summary = anatomy_summary(species)
        plan = summary["body_plan"]
        counts[plan] = counts.get(plan, 0)+1
        entry = {"animal_id": animal_id, "name": species["name"], **summary}
        if plan == "mammal":
            entry["gait_report"] = gait_report(species)
        elif plan in AXIAL_PLANS:
            entry["axial_report"] = axial_report(species)
        elif plan in INSECT_PLANS:
            entry['insect_report'] = insect_report(species)
        elif supports_spider_rig(species):
            entry['spider_report'] = spider_report(species)
        elif supports_scorpion_rig(species):
            entry['scorpion_report'] = scorpion_report(species)
        entries.append(entry)
    mammal_reports = [entry["gait_report"] for entry in entries if "gait_report" in entry]
    axial_reports = [entry['axial_report'] for entry in entries if 'axial_report' in entry]
    insect_reports = [entry['insect_report'] for entry in entries if 'insect_report' in entry]
    spider_reports = [entry['spider_report'] for entry in entries if 'spider_report' in entry]
    scorpion_reports = [entry['scorpion_report'] for entry in entries if 'scorpion_report' in entry]
    failed = [report["animal_id"] for report in mammal_reports+axial_reports+insect_reports+spider_reports+scorpion_reports if not report["numerical_pass"]]
    maxima = {key: max(report[key] for report in mammal_reports)
              for key in mammal_reports[0]["numerical_checks"]} if mammal_reports else {}
    return {"schema_version": 1, "offline": True, "uploaded": False,
            "catalogue_entries": len(entries), "body_plan_counts": counts,
            "mammal_rigs_checked": len(mammal_reports), "axial_rigs_checked": len(axial_reports),
            "insect_rigs_checked": len(insect_reports), "spider_rigs_checked": len(spider_reports),
            "scorpion_rigs_checked": len(scorpion_reports),
            "failed_animal_ids": failed,
            "numerical_pass": not failed, "maxima": maxima,
            "render_smoke_performed": False,
            "scope": "Routing and numeric rig audit, not pixel or biological validation. Run test_anatomy for render smoke tests.",
            "entries": entries}


def framing_report(species: dict) -> dict:
    """Check command extents at independent timestamps, not the camera-fit samples."""
    bounds = fixed_camera_bounds(species)
    sim = new_preview_simulator(species)
    minimum_margin = math.inf
    worst_frame = 0
    samples = 0
    for frame_idx in range(CAMERA_LAST_FRAME + 1):
        time = frame_idx / FPS * MOTION_RATE
        sim.update(time)
        if frame_idx % 7 != 3 and frame_idx not in (0, CAMERA_LAST_FRAME):
            continue
        x0, y0, x1, y1 = creature_geometry_bounds(species, sim, time)
        margin = min(x0-sim.x-bounds[0], y0-sim.y-bounds[1],
                     bounds[2]-(x1-sim.x), bounds[3]-(y1-sim.y))
        samples += 1
        if margin < minimum_margin:
            minimum_margin, worst_frame = margin, frame_idx
    return {"animal_id": species["animal_id"], "name": species["name"],
            "body_plan": anatomy_summary(species)["body_plan"],
            "camera_bounds_rig_units": bounds, "zoom": camera_zoom(bounds),
            "camera_type": "fixed root-relative tracking; not a world-locked camera",
            "horizon_seconds": (CAMERA_LAST_FRAME+1)/FPS,
            "calibration_step_frames": CAMERA_SAMPLE_STEP if anatomy_summary(species)["body_plan"] != "mammal" else None,
            "validation_step_frames": 7, "validation_offset_frames": 3,
            "sampled_frames": samples, "minimum_margin_rig_units": minimum_margin,
            "worst_frame": worst_frame, "framing_pass": minimum_margin >= 0,
            "offline": True, "uploaded": False, "specimen_validated": False,
            "scope": "Conservative draw-command bounds at sampled times, not full-pixel, all-time or biological validation. Non-mammal rendering also checks each output frame."}


def framing_audit(ids=None) -> dict:
    ids = range(len(load_encyclopedia())) if ids is None else ids
    entries = [framing_report(preview_species(i)) for i in ids]
    failed = [entry["animal_id"] for entry in entries if not entry["framing_pass"]]
    return {"schema_version": 1, "offline": True, "uploaded": False,
            "entries_checked": len(entries), "failed_animal_ids": failed,
            "framing_pass": not failed, "entries": entries,
            "scope": "Sampled command-envelope checks; no biological validation or publishing."}


def create_motion_sheet(animal_id: int, duration: float, output: Path) -> Path:
    """Eight timestamped surface views; works for every body plan, not just mammals."""
    total = timeline_frames(duration)
    species = preview_species(animal_id)
    frames = [round(i*(total-1)/7) for i in range(8)]
    sheet = Image.new("RGB", (1720, 800), (12, 20, 30))
    draw = ImageDraw.Draw(sheet)
    title = species["name"] + " / FIXED-CAMERA MOTION REVIEW"
    size = 28
    while get_font(size, bold=True).getlength(title) > 1672 and size > 12:
        size -= 1
    draw.text((24, 19), title, font=get_font(size, bold=True), fill=(231, 239, 245))
    draw.text((24, 62), "Same scale and root-relative framing / eight timestamps / surface illustration only", font=get_font(18), fill=(148, 189, 200))
    poses = []
    for index, frame_idx in enumerate(frames):
        x, y = index % 4 * 430, 107 + index // 4 * 318
        draw.text((x+15, y+8), f"{frame_idx/FPS:.2f}s / frame {frame_idx:03d}", font=get_font(17, bold=True), fill=(136, 213, 201))
        frame = render_generative_frame(species, frame_idx, total)
        crop = frame.crop((110, 340, 970, 832)).resize((418, 239), Image.Resampling.LANCZOS)
        sheet.paste(crop, (x+6, y+40))
        poses.append({"frame": frame_idx, "time_seconds": frame_idx/FPS})
    draw.text((24, 756), "Procedural family-level approximation. Stable framing is NOT evidence of correct anatomy or natural gait.", font=get_font(17), fill=(157, 179, 193))
    report = framing_report(species)
    report.update(poses=poses, duration_seconds=total/FPS)
    path = save_image(sheet, output, f"{species['id']}_motion.jpg", quality=94)
    save_report(report, output, f"{species['id']}_framing.json")
    return path


STUDY_SIZE = (1600, 900)


def render_study_frame(species: dict, frame_idx: int, total: int) -> Image.Image:
    """Synchronized lateral surface/overlay views with real rig contact states."""
    plan = anatomy_summary(species)["body_plan"]
    spider = supports_spider_rig(species)
    scorpion = supports_scorpion_rig(species)
    arachnid = spider or scorpion
    if plan not in AXIAL_PLANS | INSECT_PLANS | {'mammal'} and not arachnid:
        raise ValueError("Motion-study video supports mammal, axial, insect, true-spider and true-scorpion rigs only")
    image = Image.new("RGB", STUDY_SIZE, (12,20,30))
    draw = ImageDraw.Draw(image)
    title = species["name"].upper()+" / 2D MOTION STUDY"
    font_size = 32
    while get_font(font_size,bold=True).getlength(title) > 1516 and font_size > 12:
        font_size -= 1
    draw.text((42,30),title,font=get_font(font_size,bold=True),fill=(231,239,245))
    subtitle = ("Shared skin and axial guide / fixed-length travelling wave / no 3D assets"
                if plan in AXIAL_PLANS else "Shared skin, head, tail and limb rig / fixed camera / no 3D assets")
    if plan in INSECT_PLANS or arachnid:
        subtitle = ('Eight' if arachnid else 'Six')+' fixed-link legs / shared surface and exoskeleton joint guide / 2D only'
    draw.text((42,80),subtitle,font=get_font(20),fill=(151,178,193))
    for index, mode in enumerate(("surface", "overlay")):
        subject = {**species, "render_mode": mode}
        frame = render_generative_frame(subject,frame_idx,total)
        crop = frame.crop((110,340,970,832)).resize((744,426),Image.Resampling.LANCZOS)
        x = 42+index*774
        draw.text((x,127),mode.upper(),font=get_font(19,bold=True),fill=(132,215,203))
        image.paste(crop,(x,162))
    time = frame_idx/FPS*MOTION_RATE
    if plan in INSECT_PLANS or arachnid:
        pose = scorpion_pose(species,time) if scorpion else spider_pose(species,time) if spider else insect_pose(species,time)
        phase = (time/pose['cycle_seconds'])%1
        gait_label = ('scorpion' if scorpion else 'spider')+' / planar tetrapod' if arachnid else f'{plan} / planar tripod'
        draw.text((42,609),f"{gait_label} approximation / {frame_idx/FPS:.2f}s",font=get_font(21,bold=True),fill=(230,238,245))
        for index,limb in enumerate(pose['limbs']):
            y = 647+index*(21 if arachnid else 25)
            name = f"leg {limb['index']+1}" if arachnid else ('front','middle','hind')[limb['index']]
            label = ('Left' if limb['side'] == -1 else 'Right')+' '+name
            draw.text((42,y),label,font=get_font(16),fill=(194,210,222))
            for sample in range(160):
                planted = (sample/160+limb['phase_offset'])%1 < pose['duty']
                color = (77,158,124) if planted else (175,131,65)
                draw.rectangle((210+sample*1100/160,y,210+(sample+1)*1100/160,y+17),fill=color)
            marker = 210+phase*1100
            draw.line((marker,y-2,marker,y+20),fill=(238,245,248),width=3)
            draw.text((1340,y),'local stance' if limb['planted'] else 'swing',font=get_font(16),fill=(153,210,195))
        draw.text((42,823 if arachnid else 811),'Contacts are rig-local, not world-locked during steering. No foot elevation, forces or jump model.',font=get_font(18),fill=(157,179,193))
        note = ('Two pincers / five tail links + telson. Tail splays in 2D, not a raised arch. Family approximation.' if scorpion else
                'Schematic exoskeleton joint guides, not internal bones. Family approximation; review required.')
        draw.text((42,850),note,font=get_font(18),fill=(157,179,193))
        return image
    if plan in AXIAL_PLANS:
        pose = axial_pose(species,time)
        phase = (time/pose['cycle_seconds'])%1
        draw.text((42,612),f"{plan} / axial wave / {frame_idx/FPS:.2f}s / phase {phase:.2f}",font=get_font(21,bold=True),fill=(230,238,245))
        draw.text((42,658),"52 fixed-length rig segments / schematic guide, NOT a vertebra count",font=get_font(21),fill=(153,210,195))
        draw.text((42,699),"Local chain length: %.1f rig units / wave period: %.2fs at preview speed" %
                  (sum(pose['segment_lengths']),pose['cycle_seconds']/MOTION_RATE),font=get_font(20),fill=(194,210,222))
        draw.rounded_rectangle((42,747,1558,770),radius=5,fill=(43,65,77))
        marker = 42+phase*1516
        draw.line((marker,742,marker,775),fill=(133,220,205),width=4)
        draw.text((42,791),"No ground-contact, friction or fluid model. Root steering is not wave-periodic.",font=get_font(19),fill=(157,179,193))
        draw.text((42,836),"Family-level procedural approximation. Numeric rig checks are NOT biological validation.",font=get_font(19),fill=(157,179,193))
        return image
    p,_,limbs = mammal_pose(species,time)
    stride,duty = gait_parameters(p)
    phase = (time*72/stride)%1
    draw.text((42,612),f"{p.family} / {p.gait} approximation / {frame_idx/FPS:.2f}s / cycle {phase:.2f}",font=get_font(21,bold=True),fill=(230,238,245))
    for x,label,color in ((985,"STANCE",(77,158,124)),(1140,"SWING",(175,131,65)),(1290,"UNSUPPORTED",(69,87,106))):
        draw.rectangle((x,615,x+17,632),fill=color)
        draw.text((x+25,613),label,font=get_font(16),fill=(188,207,216))
    initial = mammal_pose(species,0,0)[2]
    bar_x,bar_w = 210,1100
    for index,limb in enumerate(limbs):
        y = 662+index*37
        label = ("Front" if limb["front"] else "Hind")+(" near" if limb["side"]==1 else " far")
        unsupported = p.family == "kangaroo" and limb["front"]
        draw.text((42,y+3),label,font=get_font(17),fill=(194,210,222))
        for sample in range(160):
            planted = (sample/160+initial[index]["phase"])%1 < duty
            color = (69,87,106) if unsupported else (77,158,124) if planted else (175,131,65)
            draw.rectangle((bar_x+sample*bar_w/160,y,bar_x+(sample+1)*bar_w/160,y+23),fill=color)
        marker = bar_x+phase*bar_w
        draw.line((marker,y-3,marker,y+27),fill=(238,245,248),width=3)
        status = "unsupported" if unsupported else "stance" if limb["planted"] else "swing"
        draw.text((1340,y+2),status,font=get_font(17),fill=(153,210,195))
    draw.text((42,836),"Family-level procedural approximation. Numeric rig checks are NOT biological validation.",font=get_font(19),fill=(157,179,193))
    return image


def encode_preview(species: dict, output: Path, duration: float, *, study: bool = False) -> Path:
    """Stream frames with bounded memory and atomic output; no stale JPEG sequences."""
    total = timeline_frames(duration)
    if study and anatomy_summary(species)["body_plan"] not in AXIAL_PLANS | INSECT_PLANS | {'mammal'} and not (supports_spider_rig(species) or supports_scorpion_rig(species)):
        raise ValueError("Motion-study video supports mammal, axial, insect, true-spider and true-scorpion rigs only")
    width, height = STUDY_SIZE if study else (WIDTH, HEIGHT)
    renderer = render_study_frame if study else render_generative_frame
    executable = shutil.which("ffmpeg")
    if not executable:
        raise RuntimeError("Install FFmpeg to encode videos; PNG previews do not need it")
    suffix = "study" if study else species['render_mode']
    destination = output_file(output, f"{species['id']}_{suffix}.mp4")
    fd, temp_name = tempfile.mkstemp(prefix="preview_", suffix=".mp4", dir=output)
    os.close(fd)
    partial = Path(temp_name)
    command = [executable, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", f"{width}x{height}", "-r", str(FPS), "-i", "pipe:0", "-an",
               "-c:v", "libx264", "-threads", "2", "-preset", "fast", "-crf", "20",
               "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(partial)]
    process = None
    try:
        with tempfile.TemporaryFile() as errors:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=errors)
            try:
                for frame_idx in range(total):
                    frame = renderer(species, frame_idx, total)
                    if frame.size != (width, height) or frame.mode != "RGB":
                        raise ValueError("Renderer returned an invalid raw-video frame")
                    process.stdin.write(frame.tobytes())
                process.stdin.close()
            except BrokenPipeError as exc:
                raise RuntimeError("FFmpeg closed the stream before every frame was sent") from exc
            status = process.wait(timeout=180)
            if status:
                errors.seek(0)
                raise RuntimeError("FFmpeg encoding failed: " + errors.read().decode(errors="replace")[-1500:])
        output_file(output, destination.name)
        partial.replace(destination)
    finally:
        if process is not None:
            if process.poll() is None:
                process.kill()
                process.wait()
            if process.stdin and not process.stdin.closed:
                try:
                    process.stdin.close()
                except BrokenPipeError:
                    pass
        partial.unlink(missing_ok=True)
    return destination


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="List matching catalogue IDs without rendering")
    parser.add_argument("--search", default="", help="Filter --list by name, class or morphology")
    parser.add_argument("--animal-id", type=int, default=0)
    parser.add_argument("--mode", choices=("surface", "overlay", "skeleton"), default="surface")
    parser.add_argument("--frame", type=int, default=45, help="Still image frame on a 6-second timeline (0..179)")
    parser.add_argument("--contact-sheet", action="store_true")
    parser.add_argument("--motion-sheet", action="store_true", help="Eight fixed-camera surface timestamps and framing JSON (all body plans)")
    parser.add_argument("--audit-framing", action="store_true", help="Standalone sampled camera-envelope audit of all 687 entries")
    parser.add_argument("--comparison", action="store_true", help="Aligned mammal/axial/insect/spider/scorpion surface, overlay and schematic joint-guide sheet")
    parser.add_argument("--gait-sheet", action="store_true", help="Eight mammal poses across a full stride, with JSON rig checks")
    parser.add_argument("--ids", default=",".join(map(str, DEFAULT_IDS)))
    parser.add_argument("--audit-catalogue", action="store_true", help="Standalone routing/numeric audit of all 687 entries, without rendering")
    parser.add_argument("--study-video", action="store_true", help="Also create a silent 1600x900 surface/overlay motion study (mammal/axial/insect/spider/scorpion rigs)")
    parser.add_argument("--video", action="store_true", help="Also create a silent 1080x1920 MP4")
    parser.add_argument("--duration", type=float, default=4.0)
    parser.add_argument("--output-dir", help="Directory inside teacher-bot/outputs")
    args = parser.parse_args(argv)
    try:
        if args.audit_framing:
            if any((args.audit_catalogue, args.list, args.video, args.study_video, args.comparison, args.gait_sheet, args.contact_sheet, args.motion_sheet)):
                raise ValueError("--audit-framing is standalone; do not combine it with list/render options")
            report = framing_audit()
            output = output_directory(args.output_dir)
            print(save_report(report, output, "framing_audit.json"))
            print(f"{report['entries_checked']} entries / {len(report['failed_animal_ids'])} framing failures")
            return 0 if report["framing_pass"] else 1
        if args.audit_catalogue:
            if any((args.list, args.video, args.study_video, args.comparison, args.gait_sheet, args.contact_sheet, args.motion_sheet)):
                raise ValueError("--audit-catalogue is standalone; do not combine it with list/render options")
            report = catalogue_audit()
            output = output_directory(args.output_dir)
            print(save_report(report, output, "catalogue_audit.json"))
            print(f"{report['catalogue_entries']} entries / {report['mammal_rigs_checked']} mammal rigs / {report.get('axial_rigs_checked', 0)} axial rigs / {report.get('insect_rigs_checked', 0)} insect rigs / {report.get('spider_rigs_checked', 0)} spider rigs / {report.get('scorpion_rigs_checked', 0)} scorpion rigs / {len(report['failed_animal_ids'])} numerical failures")
            return 0 if report["numerical_pass"] else 1
        if args.list:
            query = args.search.casefold()
            for index, species in enumerate(load_encyclopedia()):
                fields = f"{species['name']} {species['class_type']} {species['morphology']}"
                if query in fields.casefold():
                    print(f"{index:03d}  {species['name']}  [{anatomy_summary(species)['body_plan']}]")
            return 0
        if not 0 <= args.frame < 180:
            raise ValueError("Still frame must be between 0 and 179")
        timeline_frames(args.duration)
        species = preview_species(args.animal_id, args.mode)
        if args.comparison or args.gait_sheet or args.study_video:
            preview_species(args.animal_id, "skeleton")
        if args.gait_sheet and anatomy_summary(species)['body_plan'] != 'mammal':
            raise ValueError("Gait/contact sheets support mammal rigs only; use --motion-sheet for axial/insect animals")
        ids = [int(value.strip()) for value in args.ids.split(",")] if args.contact_sheet else []
        if args.contact_sheet:
            if not 1 <= len(ids) <= 48:
                raise ValueError("Contact sheets require 1 to 48 animal IDs")
            for animal_id in ids:
                get_species_for_id(animal_id)
        output = output_directory(args.output_dir)
        still = save_image(render_generative_frame(species, args.frame, 180), output, f"{species['id']}_{args.mode}.png")
        print(still)
        report = {"animal_id": args.animal_id, "name": species['name'], "mode": args.mode,
                  "offline": True, "uploaded": False, **anatomy_summary(species)}
        if anatomy_summary(species)['body_plan'] in AXIAL_PLANS:
            report['axial_report'] = axial_report(species)
        if anatomy_summary(species)['body_plan'] in INSECT_PLANS:
            report['insect_report'] = insect_report(species)
        if supports_spider_rig(species):
            report['spider_report'] = spider_report(species)
        if supports_scorpion_rig(species):
            report['scorpion_report'] = scorpion_report(species)
        save_report(report, output, f"{species['id']}_{args.mode}.json")
        if args.contact_sheet:
            print(create_contact_sheet(ids, output))
        if args.comparison:
            print(create_comparison(args.animal_id, args.frame, output))
        if args.gait_sheet:
            print(create_gait_sheet(args.animal_id, output))
        if args.motion_sheet:
            print(create_motion_sheet(args.animal_id, args.duration, output))
        if args.video:
            print(encode_preview(species, output, args.duration))
        if args.study_video:
            print(save_image(render_study_frame(species, args.frame, 180), output, f"{species['id']}_study.jpg", quality=94))
            print(encode_preview(species, output, args.duration, study=True))
        return 0
    except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        parser.exit(2, f"Preview error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
