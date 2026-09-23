"""Auditable 2D design profiles. Ratios are artist rig units, not specimen measurements.

Taxonomy is resolved before common-name traits. A spider never becomes a crab
because its name contains 'crab', and an eel never inherits a generic fish rig.
"""
from __future__ import annotations

import copy
import math
import re
from dataclasses import dataclass, replace


def words(species):
    return set(re.findall(r"[a-z]+", species.get("name", "").lower()))


def resolve_body_plan(species):
    w = words(species)
    morph = species.get("morphology", "").lower()
    cls = species.get("class_type", "").lower()
    # Corrections to the supplied catalogue, kept separate from publication data.
    if w & {"centipede", "millipede"}: return "myriapod"
    if "horseshoe" in w and "crab" in w: return "horseshoe"
    if "barnacle" in w: return "barnacle"
    if "nautilus" in w: return "nautilus"
    if cls == "quadruped": return "mammal"
    if cls == "bird": return "bird"
    if cls == "amphibian":
        if w & {"axolotl", "mudpuppy"}: return "axolotl"
        if w & {"salamander", "newt", "hellbender", "olm"}: return "salamander"
        return "frog"
    if cls == "serpent": return "serpent"
    if cls == "arachnid": return "arachnid"
    if cls == "cephalopod":
        if "vampire" in w: return "vampire_squid"
        if "pyjama" in w: return "cuttlefish"
        return morph if morph in {"octopus", "squid", "cuttlefish"} else "cuttlefish"
    if cls == "reptile":
        if "slow" in w and "worm" in w: return "legless_lizard"
        return morph if morph in {"turtle", "crocodile", "chameleon"} else "lizard"
    if cls == "aquatic":
        if morph == "marine_mammal":
            if w & {"walrus", "seal"} or {"sea", "lion"} <= w: return "pinniped"
            if "otter" in w: return "mammal"
            return "marine_mammal"
        if morph == "eel": return "eel"
        return morph if morph in {"shark", "ray", "seahorse", "jellyfish"} else "fish"
    if cls == "crustacean":
        if "mantis" in w and "shrimp" in w: return "mantis_shrimp"
        return morph if morph in {"crab", "lobster", "shrimp"} else "crab"
    if cls == "insect":
        if "cicada" in w: return "cicada"
        if "stick" in w: return "stick_insect"
        return morph if morph in {"beetle", "bee_wasp", "mantis", "ant", "dragonfly", "butterfly", "orthoptera"} else "insect"
    raise ValueError(f"Unsupported taxonomy: {cls}/{morph} ({species.get('name')})")


@dataclass(frozen=True)
class MammalProfile:
    family: str = "feline"
    body: float = 250
    depth: float = 108
    legs: float = 138
    neck: float = 60
    neck_rise: float = 42
    head: float = 64
    muzzle: float = 18
    ear: float = 22
    tail: float = 175
    tail_width: float = 12
    limb_width: float = 22
    stance: str = "digitigrade"
    coat: tuple = (180, 131, 73)
    pattern: str = "plain"
    trait: str = ""
    gait: str = "walk"
    stride: float = 82
    confidence: str = "family approximation"


PROFILES = {
    "feline": MammalProfile(),
    "canine": MammalProfile(family="canine", depth=98, legs=150, neck=60, neck_rise=50, muzzle=52, ear=39, tail=150, tail_width=22, limb_width=18, coat=(116, 111, 98)),
    "bear": MammalProfile(family="bear", body=280, depth=160, legs=136, neck=44, neck_rise=10, head=81, muzzle=40, ear=20, tail=16, limb_width=37, stance="plantigrade", coat=(103, 73, 49), stride=64),
    "elephant": MammalProfile(family="elephant", body=310, depth=205, legs=188, neck=24, neck_rise=16, head=100, muzzle=30, ear=75, tail=120, tail_width=6, limb_width=45, stance="padded", coat=(132, 137, 133), stride=64),
    "rhino": MammalProfile(family="rhino", body=320, depth=188, legs=112, neck=38, neck_rise=-15, head=100, muzzle=53, ear=27, tail=85, tail_width=5, limb_width=36, stance="three_toed", coat=(139, 134, 121), stride=62),
    "giraffe": MammalProfile(family="giraffe", body=245, depth=125, legs=226, neck=125, neck_rise=216, head=69, muzzle=40, ear=30, tail=148, tail_width=5, limb_width=17, stance="cloven", coat=(218, 179, 106), pattern="patches", stride=100),
    "equine": MammalProfile(family="equine", body=278, depth=140, legs=195, neck=75, neck_rise=95, head=79, muzzle=47, ear=35, tail=163, tail_width=22, limb_width=21, stance="hoof", coat=(148, 98, 57), stride=100),
    "cervid_bovid": MammalProfile(family="cervid_bovid", body=248, depth=124, legs=193, neck=72, neck_rise=93, head=61, muzzle=38, ear=38, tail=60, tail_width=8, limb_width=15, stance="cloven", coat=(158, 114, 70), trait="horns", stride=91),
    "camelid": MammalProfile(family="camelid", body=277, depth=143, legs=207, neck=116, neck_rise=132, head=62, muzzle=44, ear=24, tail=105, tail_width=8, limb_width=20, stance="padded", coat=(185, 145, 91), gait="pace", stride=100),
    "hippo": MammalProfile(family="hippo", body=310, depth=181, legs=86, neck=28, neck_rise=-8, head=115, muzzle=60, ear=18, tail=55, tail_width=6, limb_width=35, stance="four_toed", coat=(137, 126, 127), stride=52),
    "pachyderm": MammalProfile(family="tapir", body=240, depth=135, legs=122, neck=39, neck_rise=-5, head=75, muzzle=54, ear=28, tail=15, limb_width=23, stance="padded", coat=(89, 82, 72), stride=65),
    "small_mammal": MammalProfile(family="small_mammal", body=225, depth=98, legs=83, neck=37, neck_rise=15, head=60, muzzle=36, ear=22, tail=125, tail_width=15, limb_width=17, stance="plantigrade", coat=(123, 100, 75), stride=54),
    "primate": MammalProfile(family="primate", body=170, depth=128, legs=150, neck=26, neck_rise=42, head=80, muzzle=21, ear=20, tail=220, tail_width=10, limb_width=26, stance="plantigrade", coat=(102, 82, 57), stride=66),
    "kangaroo": MammalProfile(family="kangaroo", body=160, depth=140, legs=154, neck=68, neck_rise=128, head=62, muzzle=42, ear=52, tail=230, tail_width=31, limb_width=25, stance="plantigrade", coat=(167, 132, 99), gait="bound", stride=85),
}


def mammal_profile(species):
    w = words(species)
    p = PROFILES.get(species.get("morphology"), PROFILES["small_mammal"])
    if "otter" in w: p = replace(PROFILES["small_mammal"], body=277, legs=59, tail=170, tail_width=21, ear=11, coat=(98, 72, 52))
    if p.family == "feline":
        if "tiger" in w: p = replace(p, coat=(213, 131, 54), pattern="stripes", body=284, depth=120)
        elif w & {"jaguar", "leopard", "ocelot"}: p = replace(p, coat=(202, 161, 86), pattern="rosettes")
        elif w & {"cheetah", "serval"}: p = replace(p, depth=88, legs=175, coat=(211, 172, 104), pattern="spots", head=51, limb_width=15)
        if "snow" in w: p = replace(p, coat=(184, 188, 183), tail=232, tail_width=20)
        if "african" in w and "lion" in w: p = replace(p, trait="mane", coat=(188, 150, 89), tail_width=7)
        if w & {"lynx", "bobcat", "caracal"}: p = replace(p, tail=42 if "caracal" not in w else 130, ear=31, trait="ear_tufts")
    if p.family == "canine":
        if "fox" in w: p = replace(p, body=234, depth=82, legs=127, muzzle=42, head=52, tail=205, tail_width=32, coat=(182, 96, 42), trait="fox")
        if "fennec" in w: p = replace(p, ear=63, coat=(208, 183, 138))
        if "hyena" in w: p = replace(p, depth=135, neck_rise=13, ear=21, tail=80, pattern="spots", coat=(160, 138, 92))
        if "maned" in w: p = replace(p, legs=225, depth=99, coat=(177, 103, 57))
    if w & {"polar", "arctic"}: p = replace(p, coat=(218, 221, 207))
    if p.family == "bear" and "panda" in w: p = replace(p, coat=(216, 216, 201), pattern="panda")
    if "zebra" in w: p = replace(p, coat=(220, 217, 202), pattern="zebra")
    if "okapi" in w: p = replace(p, neck=73, neck_rise=88, legs=172, coat=(100, 61, 39), pattern="okapi")
    if p.family == "camelid":
        p = replace(p, trait="two_humps" if "bactrian" in w else "one_hump" if "camel" in w else "wool", neck_rise=132 if "camel" in w else 118)
    if p.family == "cervid_bovid":
        if w & {"deer", "elk", "moose", "caribou", "reindeer"}: p = replace(p, trait="antlers")
        if w & {"bison", "buffalo", "yak", "muskox"}: p = replace(p, body=300, depth=187, legs=141, neck_rise=12, head=80, limb_width=27, coat=(90, 71, 46), trait="bovid")
        if w & {"sheep", "mouflon", "argali"}: p = replace(p, body=230, depth=152, legs=124, coat=(176, 163, 131), trait="curled_horns")
        if w & {"gazelle", "springbok", "impala"}: p = replace(p, depth=98, limb_width=12)
    if p.family == "small_mammal":
        if w & {"rabbit", "hare", "jackrabbit", "pika"}: p = replace(p, body=170, depth=110, head=56, muzzle=21, ear=85 if "pika" not in w else 20, tail=22, trait="rabbit", gait="bound")
        elif w & {"boar", "hog", "pig", "warthog", "peccary"}: p = replace(p, body=246, depth=132, legs=99, head=84, muzzle=51, ear=32, tail=57, stance="cloven", trait="tusks", coat=(108, 88, 68))
        elif w & {"beaver", "platypus"}: p = replace(p, body=233, legs=61, tail=115, tail_width=42, ear=9, trait="paddle_tail", muzzle=56 if "platypus" in w else 26)
        elif w & {"hedgehog", "porcupine", "echidna"}: p = replace(p, body=200, depth=135, legs=48, tail=24, ear=12, trait="spines", coat=(122, 108, 86))
        elif w & {"pangolin", "armadillo"}: p = replace(p, body=244, depth=122, legs=63, tail=166, ear=9, trait="armor", coat=(139, 122, 94))
        elif w & {"anteater", "tamandua"}: p = replace(p, muzzle=102, head=41, tail=223, tail_width=38, ear=13, legs=119, trait="anteater")
        elif w & {"weasel", "ferret", "stoat", "polecat"}: p = replace(p, body=291, depth=64, legs=53, head=48, ear=14, tail=130)
        elif w & {"squirrel", "chipmunk"}: p = replace(p, body=184, legs=84, tail=205, tail_width=33, trait="squirrel", head=48)
        elif "koala" in w: p = replace(p, body=161, depth=140, legs=95, head=75, ear=44, tail=0, coat=(140, 142, 136))
        elif "capybara" in w: p = replace(p, body=260, depth=129, legs=81, head=82, muzzle=32, ear=13, tail=0)
        if w & {"skunk", "badger"}: p = replace(p, pattern="badger", coat=(70, 65, 57))
        if "red" in w and "panda" in w: p = replace(p, pattern="ringtail", coat=(168, 85, 49), tail=189, tail_width=25)
    if p.family == "primate":
        if w & {"gorilla", "chimpanzee", "bonobo", "orangutan", "gibbon"}: p = replace(p, tail=0, body=164, depth=161, limb_width=33, coat=(64, 61, 56), trait="ape")
        if "orangutan" in w: p = replace(p, coat=(160, 81, 40), limb_width=35)
        if "lemur" in w: p = replace(p, pattern="ringtail", coat=(142, 140, 133))
    return p


def natural_palette(species):
    plan = resolve_body_plan(species)
    if plan == "mammal": base = mammal_profile(species).coat
    else:
        base = {"serpent": (113, 122, 61), "legless_lizard": (121, 99, 63), "lizard": (91, 124, 68), "crocodile": (91, 112, 69), "turtle": (114, 124, 65), "arachnid": (93, 70, 48), "shark": (106, 133, 145), "fish": (129, 165, 159), "eel": (96, 112, 89), "marine_mammal": (115, 139, 146), "pinniped": (133, 125, 113), "bird": (130, 105, 74)}.get(plan, tuple(species.get("accent", (134, 147, 101))))
    def shift(n): return tuple(max(0, min(255, int(c + n))) for c in base)
    return dict(fur_dark=shift(-47), fur_mid=base, fur_gold=shift(16), fur_light=shift(38), fur_cream=shift(67), fur_highlight=shift(83))


def anatomy_summary(species):
    plan = resolve_body_plan(species)
    support = "endoskeleton"
    if plan in {"arachnid", "myriapod", "horseshoe", "crab", "lobster", "shrimp", "mantis_shrimp", "barnacle", "beetle", "bee_wasp", "mantis", "ant", "dragonfly", "butterfly", "orthoptera", "stick_insect", "cicada", "insect"}: support = "exoskeleton"
    if plan in {"octopus", "squid", "vampire_squid", "cuttlefish", "jellyfish"}: support = "hydrostatic / soft tissue"
    if plan == "nautilus": support = "shell + muscular arms"
    issues = []
    if plan in {"myriapod", "horseshoe"}:
        issues.append("Catalogue taxonomy corrected for rendering; source ledger preserved.")
    if words(species) & {"cyber", "quantum", "volt", "neon", "laser", "phantom"}:
        issues.append("Stylized catalogue name; identity requires manual review.")
    if plan in {"insect", "vampire_squid", "barnacle", "mantis_shrimp"}:
        issues.append("Specialized body form is approximated by a family-level rig.")
    return {"body_plan": plan, "support": support, "confidence": "family-level procedural approximation", "specimen_validated": False,
            "diagnostic_modes": ["surface", "overlay", "skeleton"] if plan == "mammal" else ["surface"],
            "review_required": True, "review_notes": issues,
            "notes": "Rig counts/ratios are animation controls, not measured anatomical bone counts. Species review is required before educational claims."}


def prepare_species(species):
    result = copy.deepcopy(species)
    result.update({k: v for k, v in natural_palette(species).items() if k not in species})
    result["anatomy"] = anatomy_summary(species)
    return result


def finite_ratio(value, default, low, high):
    """Catalogue data must never produce NaN or exploding joints."""
    try: value = float(value)
    except (TypeError, ValueError): return default
    return max(low, min(high, value)) if math.isfinite(value) else default
