# 2D anatomy and locomotion: implementation and review guidelines

## Scope
This project draws procedural **2D family-level approximations**. Catalogue bone counts, proportions and animation periods are rig controls, not measured anatomy. Passing render or numerical tests is not a biological-accuracy certificate. All catalogue entries keep `review_required=true` and `specimen_validated=false`.

## Mammals
- Forelimb landmarks are shoulder, elbow, wrist and distal contact; hindlimb landmarks are hip, stifle, hock and distal contact. Do not call a hock a backward knee.
- Current rigs use two-bone IK plus a fixed distal segment, with the skin and schematic skeleton drawn from the same joints. They simplify digits, scapular motion and individual bones.
- Plantigrade, digitigrade, hooved and padded feet must not be described as universally four-toed paws. Current foot silhouettes are stylized.
- Walking, pacing and bounding are distinct. The default model is a four-limb walk, not a universal diagonal two-beat trot. Camelids use a pace approximation; rabbit/kangaroo models are approximate bounds.
- Check planted contact height, cumulative world-space drift, limb lengths, swing clearance, boundary continuity and limb-cycle closure. A contact-tracking model alone does not validate body mechanics.
- Tail-less apes must not gain tails in diagnostic mode. Elephant trunks are muscular soft tissue, not chains of invented bones.
- The shared head envelope is a silhouette-aligned diagnostic guide, not a measured skull. Review muzzle, ears, horns, mane and species traits separately.

## Arachnids and related forms
- Arachnids generally have four walking-leg pairs; pedipalps are separate appendages, not vertebrate arms with humerus bones.
- Scorpion pincers and a segmented sting-bearing tail are not universal spider features. Spider/scorpion stepping patterns must not be mislabeled as the insect tripod rule.
- Horseshoe crabs are chelicerates, not true crabs. The renderer routes them separately while preserving source publication data.
- Centipedes and millipedes are myriapods, not eight-legged arachnids. Repeated segment and leg counts here remain stylized.

## Insects and crustaceans
- Insects have three thoracic walking-leg pairs. Mantis raptorial forelegs are specialized; do not give them to all beetles, stick insects or locusts.
- Crustaceans are not insects. Decapod shrimp use five walking-leg pairs in this simplified renderer, with separate antennae and an abdominal tail fan.
- Mantis shrimp are stomatopods, not ordinary decapod shrimp. Their specialized striking limbs need separate treatment; pistol shrimp have a different enlarged claw.

## Reptiles and snakes
- Head shape, pupil shape, hood and tail specializations depend on species. Do not give every snake a triangular skull, cobra hood or rattlesnake rattle.
- An animation's axial segment count is not the animal's measured vertebral count.
- Slow worms are legless lizards. Turtles, crocodiles and chameleons need different shells, limb posture and digit shapes; not all reptiles have five identical clawed digits or crocodilian scutes.

## Cephalopods
- Octopuses have eight arms. Typical squid and cuttlefish have eight arms plus two specialized tentacles; these are not interchangeable with eight identical tentacles.
- Nautiluses have numerous suckerless appendages and an external shell. The drawing's chosen appendage count is illustrative.
- Vampire squid require explicit review rather than automatic inheritance of a conventional squid model.
- These animals have muscular/hydrostatic support, not a vertebrate limb skeleton.

## Aquatic animals
- Sharks, rays, bony fishes, eels and marine mammals do not share one tail or fin rig. Many sharks have heterocercal tails; this is not a universal fish tail shape.
- Marine mammals have horizontal flukes or specialized paddles and breathe air; do not invent fish gills. Manatee and dugong tails differ.
- Eels must not inherit generic paired hind fins. Pinnipeds need flippers, not land-mammal paws.

## Review procedure
1. Confirm catalogue ID, taxonomy and body-plan routing before rendering.
2. Inspect surface views at multiple phases; inspect overlay/skeleton only where the CLI explicitly supports them (currently mammals).
3. Run `python preview_anatomy.py --audit-catalogue` and `python -m unittest test_anatomy -v`.
4. Examine complete videos for clipping, scale pumping, foot sliding, joint discontinuities and misleading silhouettes.
5. Record unsupported detail honestly. Do not alter publication histories or relax duplicate gates to make a preview pass.

Non-mammal legacy renderers still have approximation and camera limitations. This guide distinguishes intended biological constraints from verified implementation; it does not certify every renderer against every statement above.
