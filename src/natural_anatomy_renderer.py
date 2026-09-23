"""Pure 2D anatomical illustration: linked silhouette, joints and surface markings.

No meshes, 3D projection, downloaded artwork or network calls. Mammals use a
lateral tracking-camera walk study; other animals retain dorsal swimming/crawl
views. Debug bones come from the SAME pose that draws the limbs.
"""
from __future__ import annotations

import math
from src.anatomy_profiles import mammal_profile, words, resolve_body_plan, finite_ratio, supports_spider_rig, supports_scorpion_rig
from src.bio_bone_renderer import solve_two_bone_ik


def blend(a, b, t):
    return tuple(round(x * (1 - t) + y * t) for x, y in zip(a, b))


def smooth(points, closed=False, steps=7):
    """Centrally tangent Catmull-Rom contour; drawing-only, never changes joints."""
    if len(points) < 3: return points
    p = [points[-1]] + list(points) + [points[0], points[1]] if closed else [points[0]] + list(points) + [points[-1]]
    result = []
    for i in range(1, len(p) - 2):
        a, b, c, d = p[i - 1:i + 3]
        for j in range(steps):
            t = j / steps
            result.append(tuple(0.5 * (2*b[k] + (-a[k]+c[k])*t + (2*a[k]-5*b[k]+4*c[k]-d[k])*t*t + (-a[k]+3*b[k]-3*c[k]+d[k])*t*t*t) for k in (0, 1)))
    if not closed: result.append(points[-1])
    return result


class Pen:
    def __init__(self, draw, x, y, angle=0):
        self.draw, self.x, self.y = draw, x, y
        self.c, self.s = math.cos(angle), math.sin(angle)

    def point(self, p): return (self.x + p[0]*self.c - p[1]*self.s, self.y + p[0]*self.s + p[1]*self.c)

    def poly(self, pts, fill, outline=None, width=1, curved=True):
        pts = smooth(pts, True) if curved else pts
        self.draw.polygon([self.point(p) for p in pts], fill=fill, outline=outline, width=max(1, round(width)))

    def line(self, pts, color, width=1, curved=True):
        pts = smooth(pts) if curved else pts
        self.draw.line([self.point(p) for p in pts], fill=color, width=max(1, round(width)))

    def oval(self, x, y, rx, ry, fill, outline=None, width=1):
        self.poly([(x + rx*math.cos(i*math.tau/40), y + ry*math.sin(i*math.tau/40)) for i in range(40)], fill, outline, width, False)

    def taper(self, points, widths, fill, outline=None):
        left, right = [], []
        for i, ((x, y), width) in enumerate(zip(points, widths)):
            a, b = points[max(0, i-1)], points[min(len(points)-1, i+1)]
            dx, dy = b[0]-a[0], b[1]-a[1]
            length = max(1e-8, math.hypot(dx, dy))
            nx, ny = -dy/length*width/2, dx/length*width/2
            left.append((x+nx, y+ny)); right.append((x-nx, y-ny))
        self.poly(left + right[::-1], fill, outline, curved=True)


def gait_parameters(profile):
    """Shared stride and stance timing for the renderer and diagnostic timeline."""
    return min(profile.stride, profile.legs * 0.90), (0.54 if profile.gait == "bound" else 0.67)


def mammal_head_geometry(p, bob):
    """Common head envelope for the skin and diagnostic skull/jaw outline.

    This is a simplified silhouette-aligned guide, not a measured skull.
    Felids get a short, broad muzzle rather than a tapered canid snout.
    """
    hx, hy = p.body*.40+p.neck, -p.depth*.28-p.neck_rise+bob
    h = p.head
    skull = [(hx-h*.45,hy-h*.26),(hx-h*.14,hy-h*.47),(hx+h*.28,hy-h*.31),
             (hx+h*.48,hy),(hx+h*.25,hy+h*.36),(hx-h*.2,hy+h*.40),(hx-h*.49,hy+h*.11)]
    my = hy+h*.13
    if p.family == "feline":
        muzzle = [(hx+h*.10,hy-h*.08),(hx+h*.34+p.muzzle,my-h*.16),
                  (hx+h*.43+p.muzzle,my+h*.02),(hx+h*.36+p.muzzle,my+h*.24),
                  (hx+h*.12,my+h*.25)]
    else:
        muzzle = [(hx+h*.06,hy-h*.09),(hx+h*.32+p.muzzle,my-11),
                  (hx+h*.38+p.muzzle,my+8),(hx+h*.20,my+h*.23)]
    return dict(center=(hx,hy), skull=skull, muzzle=muzzle, muzzle_y=my,
                nose=(hx+h*.35+p.muzzle,my-3))


def mammal_tail_geometry(p, bob, time):
    """Shared sacral-to-tip centerline; tail-less animals have no invented bones."""
    if not p.tail:
        return [], []
    points = []
    for i in range(15):
        u = i/14
        x = -p.body*.45-p.tail*u*.79
        y = -p.depth*.26+bob + math.sin(u*2.8)*p.tail*.30 + math.sin(time*2-u*3)*u*13
        if p.trait == "squirrel":
            y = -p.depth*.26+bob-math.sin(u*2.2)*p.tail*.72
        if p.family in {"equine", "giraffe"}:
            x, y = -p.body*.45-u*p.tail*.28, -p.depth*.26+bob+u*p.tail
        if p.family == "kangaroo":
            y = bob+u*p.legs*.95
        points.append((x,y))
    widths = [max(2,p.tail_width*(1-i/17)) for i in range(15)]
    if p.trait == "paddle_tail":
        widths = [8+math.sin(i/14*math.pi)*p.tail_width for i in range(15)]
    return points, widths


def mammal_pose(species, time, travel=None):
    """A fixed-length 3-bone rig with explicit stance/swing contact states.

    During stance, contact_x + travel is constant within each stride. This is
    a lateral tracking study, not the dorsal cursor solver's world foot model.
    """
    p = mammal_profile(species)
    if travel is None: travel = time * 72
    # Small, short-legged species must keep the contact target inside the IK
    # reach annulus; otherwise a 'planted' foot is projected above the floor.
    stride, duty = gait_parameters(p)
    metadata = species.get("bone_structure", {}).get("limbs", {})
    upper_ratio = finite_ratio(metadata.get("upper_bone_len"), 1, 0.01, 500)
    lower_ratio = finite_ratio(metadata.get("lower_bone_len"), 1, 0.01, 500)
    split = finite_ratio(upper_ratio / lower_ratio, 1, 0.8, 1.25)
    cycle = travel / stride
    bob = math.sin(cycle * math.tau * 2) * min(p.legs * 0.025, 1.5 if p.family in {"elephant", "rhino", "hippo"} else 3)
    limbs = []
    for side in (-1, 1):
        for front in (False, True):
            phase = {(True, -1): 0.0, (False, 1): 0.25, (True, 1): 0.5, (False, -1): 0.75}[(front, side)]
            if p.gait == "pace": phase = (0 if side == -1 else 0.5) + (0.06 if front else 0)
            if p.gait == "bound": phase = (0 if front else 0.5) + (0.03 if side == 1 else 0)
            u = cycle + phase
            phase_u = u % 1
            root_x = p.body * (0.34 if front else -0.34)
            root_y = (-min(7, p.legs * 0.07) if front else 0) + bob
            if p.family == "primate" and front: root_y -= 38
            if p.family == "kangaroo" and front: root_y -= 82
            # A complete stance uses exactly duty*stride backward displacement.
            if phase_u < duty:
                foot_x = root_x + stride*(duty/2 - phase_u)
                foot_y, planted = p.legs, True
            else:
                q = (phase_u - duty)/(1 - duty)
                eased = q*q*q*(10 + q*(-15 + 6*q))
                # Match the stance velocity at both ends of the swing.
                foot_x = root_x - stride*duty/2 - stride*(1-duty)*q + stride*eased
                foot_y, planted = p.legs - math.sin(math.pi*q)**2 * min(35, p.legs*0.20), False
            if p.family == "kangaroo" and front:
                foot_y = p.legs*0.33 + math.sin(cycle*math.tau)*9
                planted = False
            digit = p.legs * (0.23 if p.stance == "digitigrade" else 0.13)
            ankle = (foot_x - min(10 if front else 18, p.legs * 0.13), foot_y - digit)
            # Catalogue ratios influence the split, not total reach or species
            # stature. The source ratios are rig controls, not measured bones.
            reach = p.legs * (1.09 if front else 1.10)
            upper = reach * split / (1 + split)
            lower = reach / (1 + split)
            if p.family == "primate" and front: upper *= 1.20; lower *= 1.20
            root, knee, endpoint = solve_two_bone_ik((root_x, root_y), ankle, upper, lower, 1 if front else -1)
            # Fixed distal segment, even if malformed inputs force ankle projection.
            dx, dy = foot_x - ankle[0], foot_y - ankle[1]
            foot = (endpoint[0]+dx, endpoint[1]+dy)
            limbs.append(dict(front=front, side=side, points=[root, knee, endpoint, foot], lengths=[upper, lower, math.hypot(dx, dy)], planted=planted, contact_x=foot[0]+travel, phase=phase_u))
    return p, bob, limbs


def _draw_mammal_limb(pen, limb, p, base, outline):
    pts = limb["points"]
    width = p.limb_width
    if not limb["front"]: width *= 1.24
    pen.taper(pts, [width*1.85, width*1.07, width*0.53, width*0.61], base, outline)
    pen.line([(x-2, y) for x,y in pts[1:]], blend(base, (244, 228, 199), .19), max(1, width*.17))
    for x,y in pts[1:3]: pen.oval(x,y,width*.32,width*.30,blend(base,outline,.15))
    x,y = pts[-1]
    dark = (39, 37, 33)
    if p.stance in {"cloven", "hoof"}:
        pen.poly([(x-7,y-9),(x+8,y-9),(x+17,y+2),(x-9,y+2)],dark,curved=False)
        if p.stance == "cloven": pen.line([(x+4,y-8),(x+5,y+2)],(163,151,128),1)
    else:
        length = 20 if p.stance == "plantigrade" else 15
        pen.poly([(x-8,y-7),(x+5,y-9),(x+length,y-3),(x+length+2,y+2),(x-10,y+2)],base,outline)
        for i in range(2): pen.line([(x+length-5+i*4,y-4),(x+length-5+i*4,y+1)],outline,1)


def _body_pattern(pen, p, bob, base, dark):
    """Deterministic markings bounded inside the dorsal/ventral body envelope."""
    b,d = p.body,p.depth
    if p.pattern in {"stripes", "zebra"}:
        for i in range(15 if p.pattern=="zebra" else 12):
            x = -b*.44 + i*b*.065
            depth = d*(.48 if i%3 else .57)
            top = -d*.48 + bob + abs(x/b)*12
            width = 5 + (i%3)*2
            pts=[(x,top),(x+width,top-1),(x+width+math.sin(i)*9,top+depth*.45),(x-5,top+depth*1.48),(x-1,top+depth*.53)]
            pen.poly(pts, (37, 34, 29), curved=True)
            if i%2: pen.line([(x+width,top+depth*.38),(x+20,top+depth*.27)],(37,34,29),3)
    elif p.pattern in {"spots", "rosettes", "patches"}:
        for row in range(5):
            for col in range(13):
                x=-b*.43+col*b*.071 + (row%2)*7
                y=-d*.44+row*d*.155+bob
                if (x/(b*.52))**2 + ((y-bob)/(d*.62))**2 > .95: continue
                radius=3 if p.pattern=="spots" else 6 if p.pattern=="rosettes" else 10
                radius *= 0.8+0.3*math.sin(col*7+row*13)**2
                pts=[(x+radius*math.cos(k*math.tau/6),y+radius*.82*math.sin(k*math.tau/6)) for k in range(6)]
                if p.pattern=="rosettes": pen.poly(pts,blend(base,dark,.15),dark,2)
                else: pen.poly(pts,dark)
    elif p.pattern == "panda":
        pen.poly([(b*.16,-d*.54+bob),(b*.35,-d*.52+bob),(b*.45,d*.25+bob),(b*.16,d*.30+bob)],(41,43,40))
    elif p.pattern == "badger":
        pen.poly([(-b*.45,-d*.32+bob),(-b*.22,-d*.54+bob),(b*.26,-d*.52+bob),(b*.42,-d*.26+bob),(b*.1,-d*.32+bob)],(195,190,170))
    elif p.trait == "armor":
        for i in range(11):
            x=-b*.42+i*b*.074
            pen.line([(x,-d*.43+bob),(x+9,-d*.18+bob),(x+8,d*.2+bob)],dark,3)
    if p.trait == "spines":
        for i in range(52):
            u=i/51;x=-b*.47+u*b*.87;y=-math.sin(u*math.pi)*d*.5+bob
            pen.line([(x,y+18),(x-16,y-20-(i%5)*3)],blend(dark,(220,210,179),.48),2)


def draw_mammal(draw, sim, species, time, *unused):
    p,bob,limbs = mammal_pose(species,time)
    pen=Pen(draw,sim.x,sim.y)
    base=p.coat; dark=blend(base,(23,22,20),.56); light=blend(base,(249,230,192),.32)
    b,d=p.body,p.depth
    head_geometry = mammal_head_geometry(p, bob)
    tail, widths = mammal_tail_geometry(p, bob, time)
    hx, hy = head_geometry["center"]
    if species.get("render_mode") == "skeleton":
        _mammal_skeleton(pen,p,bob,limbs,head_geometry,tail)
        return
    # Far-side feet, near-side feet, muscles and bones all share this one pose.
    for limb in limbs:
        if limb["side"]==-1: _draw_mammal_limb(pen,limb,p,blend(base,(17,23,28),.24),dark)
    # Tail emerges from the sacrum, not the end of a caterpillar torso.
    if tail:
        pen.taper(tail,widths,base,dark)
        if p.trait in {"fox", "mane"} or p.family=="giraffe":
            pen.taper(tail[-4:],[widths[-4]+5, widths[-3]+8,widths[-2]+4,2],light if p.trait=="fox" else dark)
        if p.pattern=="ringtail":
            for i in range(2,14,2): pen.line(tail[i:i+2],dark,max(3,widths[i]))
    # Smooth chest, withers, lumbar tuck, pelvis; no circle-chain body.
    contour=[(-b*.50,-d*.17),(-b*.43,-d*.45),(-b*.23,-d*.53),(0,-d*.49),(b*.27,-d*.54),(b*.43,-d*.34),(b*.46,d*.04),(b*.36,d*.35),(b*.18,d*.40),(-b*.05,d*.26),(-b*.28,d*.34),(-b*.46,d*.24)]
    if p.trait in {"one_hump","two_humps"}:
        contour[2:4]=[(-b*.25,-d*.90),(-b*.09,-d*.52),(b*.09,-d*.88),(b*.25,-d*.51)] if p.trait=="two_humps" else [(-b*.23,-d*.54),(-b*.05,-d*.99),(b*.15,-d*.60)]
    if p.trait=="bovid": contour[3]=(b*.07,-d*.72)
    contour=[(x,y+bob) for x,y in contour]
    pen.poly(contour,base,dark,2)
    # Low-contrast, layered 2D contour washes (no 3D ellipsoids).
    for j in range(7,0,-1):
        f=j/8
        pts=[(x*.97,y*.74 - d*(1-f)*.17) for x,y in contour]
        pen.poly(pts,blend(base,light,(1-f)*.28))
    _body_pattern(pen,p,bob,base,dark)
    # Pelvic crest and scapular muscle edges, intentionally subtle.
    pen.line([(-b*.36,-d*.29+bob),(-b*.23,-d*.04+bob),(-b*.30,d*.23+bob)],blend(base,dark,.25),2)
    pen.line([(b*.21,-d*.41+bob),(b*.34,-d*.15+bob),(b*.23,d*.28+bob)],blend(base,dark,.30),2)
    pen.poly([(b*.18,-d*.45+bob),(b*.36,-d*.57+bob),(hx-p.head*.22,hy-p.head*.37),(hx+p.head*.18,hy+p.head*.12),(hx-p.head*.20,hy+p.head*.48),(b*.34,d*.24+bob)],base,dark,2)
    if p.family=="giraffe" and p.pattern=="patches":
        for i in range(8):
            u=i/8;x=b*.36+(hx-b*.36)*u;y=-d*.36+(hy+d*.36)*u+bob
            pen.poly([(x-7,y-10),(x+8,y-10),(x+10,y+3),(x-6,y+7)],dark)
    if p.family in {"equine","camelid"}:
        pen.line([(b*.24,-d*.53+bob),(hx-p.head*.33,hy-p.head*.35)],dark,9)
    for limb in limbs:
        if limb["side"]==1:
            col=(45,44,40) if p.pattern=="panda" else base
            _draw_mammal_limb(pen,limb,p,col,dark)
            if p.pattern in {"zebra","okapi"}:
                a,c=limb["points"][1:3]
                for j in range(5):
                    x=a[0]+(c[0]-a[0])*j/5;y=a[1]+(c[1]-a[1])*j/5
                    pen.line([(x-5,y),(x+5,y+3)],(43,39,33) if p.pattern=="zebra" else (219,206,176),3)
    # Far ear then head, muzzle, near ear and species-defining cranial appendages.
    head=p.head
    pen.poly([(hx-head*.35,hy-head*.24),(hx-head*.42,hy-head*.30-p.ear*.85),(hx-head*.1,hy-head*.35)],dark)
    if p.trait=="mane":
        pts=[]
        for i in range(50):
            a=i*math.tau/50;r=head*(.80+.08*math.sin(i*7))
            pts.append((hx-head*.25+math.cos(a)*r,hy+math.sin(a)*r))
        pen.poly(pts,(92,57,29),dark,2)
        for i in range(22):
            a=i*math.tau/22
            pen.line([(hx-head*.25+math.cos(a)*head*.52,hy+math.sin(a)*head*.52),(hx-head*.25+math.cos(a)*head*.78,hy+math.sin(a)*head*.78)],(127,83,40),2)
    pen.poly(head_geometry["skull"],base,dark,2)
    muzzle_y=head_geometry["muzzle_y"]
    pen.poly(head_geometry["muzzle"],light,dark,1)
    nx=head_geometry["nose"][0]
    if p.family != "elephant":
        pen.oval(nx,muzzle_y-3,6,4,(38,34,29))
        pen.line([(nx,muzzle_y+9),(hx+head*.30,muzzle_y+14)],dark,2)
    if p.family=="elephant":
        trunk=[(hx+head*.34,hy),(hx+head*.68,hy+38),(hx+head*.66,hy+104),(hx+head*.83,hy+157),(hx+head*1.08,hy+153+math.sin(time*2)*13)]
        pen.taper(trunk,[43,35,26,16,8],base,dark)
        for i in range(8): pen.line([(hx+head*.52,hy+40+i*10),(hx+head*.78,hy+43+i*10)],blend(base,dark,.38),1)
        if "asian" not in words(species): pen.taper([(hx+head*.38,hy+30),(hx+head*.77,hy+56),(hx+head*1.06,hy+43)],[12,8,1],(231,219,181),dark)
        pen.poly([(hx-head*.18,hy-head*.2),(hx-head*.66,hy-head*.59),(hx-head*.93,hy),(hx-head*.58,hy+head*.68),(hx-head*.13,hy+head*.37)],blend(base,dark,.13),dark,2)
        pen.line([(hx-head*.25,hy-head*.08),(hx-head*.60,hy+head*.38)],blend(base,light,.5),2)
    else:
        ex,ey=hx-head*.25,hy-head*.27
        if p.family in {"bear", "primate"} or (p.family == "feline" and p.trait != "ear_tufts"):
            pen.oval(ex,ey-p.ear*.42,p.ear*.48,p.ear*.62,base,dark,2)
            pen.oval(ex,ey-p.ear*.42,p.ear*.26,p.ear*.36,blend(base,(156,106,92),.6))
        else:
            pen.poly([(ex-10,ey+6),(ex-12,ey-p.ear*.63),(ex-3,ey-p.ear),(ex+11,ey-p.ear*.44),(ex+10,ey+3)],base,dark,2)
            pen.poly([(ex-4,ey),(ex-5,ey-p.ear*.66),(ex+4,ey-p.ear*.37)],blend(base,(156,106,92),.6))
        if p.trait=="ear_tufts": pen.line([(ex-3,ey-p.ear+2),(ex-6,ey-p.ear-15)],dark,3)
    if p.family=="rhino":
        pen.poly([(hx+head*.33,hy-head*.12),(hx+head*.52,hy-head*.84),(hx+head*.66,hy-head*.10)],(192,186,165),dark,2)
        if not words(species)&{"indian","javan"}: pen.poly([(hx+head*.06,hy-head*.3),(hx+head*.15,hy-head*.65),(hx+head*.28,hy-head*.25)],(158,150,128),dark)
    if p.family=="giraffe":
        for off in (-8,15):
            pen.line([(hx+off,hy-head*.33),(hx+off-4,hy-head*.80)],base,7)
            pen.oval(hx+off-4,hy-head*.80,5,6,dark)
    if p.trait in {"horns","bovid","antlers","curled_horns"}:
        for off in (-12,7):
            root=(hx+off,hy-head*.37)
            if p.trait=="curled_horns":
                pts=[(root[0]+math.cos(a*.23)*22,root[1]+math.sin(a*.23)*23-10) for a in range(24)]
                pen.taper(pts,[10-i*.38 for i in range(24)],(156,143,109),dark)
            else:
                pts=[root,(root[0]-15,root[1]-26),(root[0]-32,root[1]-64),(root[0]-24,root[1]-94)]
                pen.taper(pts,[9,7,4,1],(175,161,121),dark)
                if p.trait=="antlers":
                    for j in (1,2): pen.taper([pts[j],(pts[j][0]+23,pts[j][1]-20),(pts[j][0]+29,pts[j][1]-39)],[5,3,1],(181,166,124),dark)
    if p.pattern == "stripes":
        for i in range(3):
            y=hy-head*.23+i*head*.16
            pen.poly([(hx-head*.36,y),(hx-head*.02,y+5),(hx-head*.20,y+9)],(37,34,29),curved=False)
        pen.line([(hx+head*.18,hy-head*.34),(hx+head*.06,hy-head*.20)],(37,34,29),3)
    # Eye is set inside the skull; no floating disks or neon biological tissue.
    ex,ey=hx+head*.15,hy-head*.10
    if p.pattern=="panda": pen.oval(ex,ey,13,10,(45,44,40))
    pen.oval(ex,ey,5,3.8,(31,27,22));pen.oval(ex+1.5,ey-1.3,1.25,1.25,(244,238,214))
    pen.line([(ex-8,ey-6),(ex+5,ey-7)],dark,2)
    if p.family in {"feline","canine","small_mammal"}:
        for i in range(3): pen.line([(hx+head*.46,muzzle_y+6),(hx+head*.61+p.muzzle*.5,muzzle_y+3+i*6)],blend(dark,light,.3),1)
    if species.get("render_mode") in {"skeleton","overlay"}:
        _mammal_skeleton(pen,p,bob,limbs,head_geometry,tail)


def _mammal_skeleton(pen,p,bob,limbs,head_geometry,tail):
    bone=(232,230,201);joint=(98,220,209)
    hx,hy = head_geometry["center"]
    spine=[(-p.body*.45,-p.depth*.26+bob),(-p.body*.10,-p.depth*.31+bob),(p.body*.32,-p.depth*.32+bob),(hx-p.head*.25,hy)]
    if tail:
        pen.line(tail,bone,2)
        for x,y in tail[1::2]: pen.oval(x,y,2,2,joint)
    pen.line(spine,bone,4)
    for i in range(11):
        x=-p.body*.25+i*p.body*.05;y=-p.depth*.28+bob
        pen.line([(x,y),(x+9,y+19),(x+4,y+p.depth*.52)],bone,1)
        pen.oval(x,y,3,3,joint)
    pen.poly([(-p.body*.41,-16+bob),(-p.body*.22,-27+bob),(-p.body*.25,17+bob)],None,bone,3)
    pen.poly([(p.body*.18,-p.depth*.42+bob),(p.body*.36,-p.depth*.35+bob),(p.body*.34,-7+bob)],None,bone,3)
    pen.poly(head_geometry["skull"],None,bone,2)
    pen.poly(head_geometry["muzzle"],None,bone,2)
    pen.oval(hx+p.head*.15,hy-p.head*.10,5,4,None,joint,1)
    for limb in limbs:
        color=bone if limb['side']==1 else (140,158,156)
        pen.line(limb['points'],color,3,False)
        for x,y in limb['points']: pen.oval(x,y,4,4,joint,(22,38,42),1)


AXIAL_PLANS = frozenset({"serpent", "eel", "legless_lizard"})
AXIAL_ANGULAR_SPEED = 3.0


def axial_pose(species, time):
    """Fixed-length 2D chain with a travelling tangent wave.

    A rig-local motion study, not a friction/fluid simulation. The 52 segments
    are drawing controls, NOT a species' anatomical vertebra count. Surface,
    axial guide and measurements all consume this exact geometry.
    """
    plan = resolve_body_plan(species)
    if plan not in AXIAL_PLANS or not math.isfinite(time):
        raise ValueError("Axial poses require a supported body plan and finite time")
    names = words(species)
    cobra = plan == "serpent" and "cobra" in names
    rattle = plan == "serpent" and "rattlesnake" in names
    broad_head = plan == "serpent" and bool(names & {"viper", "rattlesnake", "adder"})
    length = 480.0 if plan == "serpent" else 420.0
    segments = 52
    segment_length = length / segments
    flex = finite_ratio(species.get("bone_structure", {}).get("vertebrae", {}).get("flexibility_index"), 1, .5, 1.4)
    amplitude = (.60 if plan == "serpent" else .44) * flex
    phase = time * AXIAL_ANGULAR_SPEED
    points = [(0.0, 0.0)]
    for index in range(segments):
        u = index / (segments-1)
        # The head/neck tangent remains fixed; the wave grows caudally.
        envelope = min(1.0, u/.18)
        envelope = envelope*envelope*(3-2*envelope)
        angle = amplitude * envelope * math.sin(phase-u*math.tau*1.35)
        x, y = points[-1]
        points.append((x-segment_length*math.cos(angle), y+segment_length*math.sin(angle)))
    widths, normals, ribs = [], [], []
    for index, (x, y) in enumerate(points):
        u = index / segments
        width = max(1.5, (39 if plan == "serpent" else 36)*(1-u)**.65)
        if cobra and .02 < u < .25:
            width += 43*math.sin(math.pi*(u-.02)/.23)**2
        widths.append(width)
        a, b = points[max(0,index-1)], points[min(segments,index+1)]
        dx, dy = b[0]-a[0], b[1]-a[1]
        span = math.hypot(dx,dy)
        normal = (-dy/span, dx/span)
        normals.append(normal)
        if 3 <= index < int(segments*.78) and index % 2 == 0:
            nx, ny = normal
            # Schematic transverse guides terminate INSIDE the shared skin.
            ribs.append([(x+nx*width*.37,y+ny*width*.37),(x,y),
                         (x-nx*width*.37,y-ny*width*.37)])
    head_width = 22 if broad_head else 16
    head = [(27,0),(17,-head_width*.72),(0,-head_width),(-15,-11),
            (-15,11),(0,head_width),(17,head_width*.72)]
    # End decorations follow the tail tangent, not the head's heading.
    a, b = points[-2:]
    tangent = ((b[0]-a[0])/segment_length, (b[1]-a[1])/segment_length)
    rattles = [(b[0]+tangent[0]*(4+i*5), b[1]+tangent[1]*(4+i*5)) for i in range(4)] if rattle else []
    return {"points": points, "widths": widths, "normals": normals, "ribs": ribs,
            "head": head, "rattles": rattles, "cobra_hood": cobra,
            "segment_lengths": [segment_length]*segments,
            "cycle_seconds": math.tau/AXIAL_ANGULAR_SPEED, "plan": plan}


def draw_elongated(draw, sim, species, time, *unused):
    """Shared surface/axial guide for snakes, eels and legless lizards."""
    pose = axial_pose(species,time)
    pen = Pen(draw,sim.x,sim.y,sim.angle)
    pts, widths = pose["points"], pose["widths"]
    base, dark = tuple(species['fur_mid']), tuple(species['fur_dark'])
    mode = species.get("render_mode", "surface")
    if mode != "skeleton":
        if pose["plan"] == "eel":
            # Median fin fringe only: never add paired hind fins.
            pen.taper(pts,[w*1.30 for w in widths],blend(base,(166,177,141),.35),dark)
        pen.taper(pts,widths,base,dark)
        highlight = [(x+nx*w*.17,y+ny*w*.17) for (x,y),(nx,ny),w in zip(pts,pose['normals'],widths)]
        pen.line(highlight,blend(base,(206,202,160),.28),2)
        if pose["plan"] == "serpent":
            for i in range(5,len(pts)-5,3):
                x,y = pts[i]
                nx,ny = pose['normals'][i]
                radius = widths[i]*.18
                pen.poly([(x+nx*radius,y+ny*radius),(x+ny*5,y-nx*5),
                          (x-nx*radius,y-ny*radius),(x-ny*5,y+nx*5)],dark,curved=False)
        pen.poly(pose['head'],base,dark)
        for side in (-1,1):
            pen.oval(13,side*10,3,3,(18,20,15))
            pen.oval(14,side*10-1,1,1,(224,227,201))
        pen.line([(25,2),(7,6)],dark,1)
        if pose['plan'] in {'serpent','legless_lizard'}:
            # Smooth extension/retraction avoids the old on/off tongue pop.
            extension = max(0,math.sin(time*6))**2
            if extension > .01:
                tip = 27+19*extension
                pen.line([(25,0),(tip,0)],(154,69,69),1)
                for side in (-1,1):
                    pen.line([(tip,0),(tip+7*extension,side*4*extension)],(154,69,69),1)
        for i,(x,y) in enumerate(pose['rattles']):
            pen.oval(x,y,4-i*.5,4-i*.5,(189,166,120),dark)
    if mode in {'skeleton','overlay'}:
        bone, joint = (231,232,203), (102,219,204)
        pen.line(pts,bone,2,False)
        for rib in pose['ribs']:
            pen.line(rib,bone,1,False)
        pen.poly(pose['head'],None,bone,2)
        for x,y in pts[1::2]:
            pen.oval(x,y,1.8,1.8,joint)
        # The rattle is keratin, not an extension of the bony axial guide.


def draw_myriapod(draw,sim,species,time,*unused):
    pen=Pen(draw,sim.x,sim.y,sim.angle)
    millipede='millipede' in words(species);n=30 if millipede else 21
    base=(103,75,48) if millipede else (127,70,36);dark=(39,29,22)
    points=[(-i*14,math.sin(time*2-i*.26)*14) for i in range(n)]
    for i,(x,y) in enumerate(points):
        for side in (-1,1):
            for pair in range(2 if millipede else 1):
                step=math.sin(time*7-i*.75+side*math.pi+pair*.4)
                pen.line([(x+pair*4,y+side*10),(x-6+pair*4,y+side*23),(x-12+step*9,y+side*(29 if millipede else 43))],(171,118,58),3)
    for x,y in reversed(points): pen.oval(x,y,10,15,base,dark,2);pen.line([(x-2,y-11),(x-2,y+11)],(165,117,59),1)
    pen.oval(8,0,17,19,(125,61,30),dark,2)
    for side in (-1,1): pen.line([(15,side*8),(38,side*22),(54,side*(25+math.sin(time)*4))],(174,136,77),2)


def draw_marine_body(draw,sim,species,time,*unused):
    """Dorsal mammals: horizontal flukes, rounded manatee paddle, no fish gills."""
    pen=Pen(draw,sim.x,sim.y,sim.angle);w=words(species)
    base=tuple(species['fur_mid']);dark=tuple(species['fur_dark'])
    siren=bool(w & {'manatee','dugong'});orca='orca' in w
    if orca: base=(38,48,53);dark=(18,26,31)
    pts=[];widths=[]
    for i in range(22):
        u=i/21;pts.append((-u*350,math.sin(time*3-u*3)*u*u*16))
        widths.append(12+100*math.sin((u*.85+.10)*math.pi)*(1-u*.75))
    for side in (-1,1):
        pen.poly([(-55,side*32),(-73,side*80),(-126,side*125),(-117,side*68),(-97,side*24)],base,dark)
    end=pts[-1];ex,ey=end
    if 'manatee' in w:
        pen.oval(ex-28,ey,59,57,base,dark,2)
    else:
        pen.poly([(ex+12,ey),(ex-25,ey-74),(ex-62,ey-92),(ex-45,ey-29),(ex-37,ey),(ex-45,ey+29),(ex-62,ey+92),(ex-25,ey+74)],base,dark,2)
    pen.taper(pts,widths,base,dark)
    pen.line([(x,y-8) for x,y in pts],blend(base,(207,220,219),.19),6)
    pen.oval(0,0,42 if siren else 35,37 if siren else 28,base,dark,2)
    if w & {'dolphin','porpoise'}: pen.poly([(18,-18),(65,-10),(70,0),(65,10),(18,18)],base,dark)
    if 'narwhal' in w: pen.taper([(25,-7),(92,-8),(165,-10)],[8,5,1],(224,213,177),dark)
    for side in (-1,1):
        pen.oval(9,side*25,3,4,(14,20,21))
        if orca: pen.oval(-21,side*29,19,9,(227,229,209))
    if not siren:
        pen.line([(-34,-7),(-38,0),(-34,7)],dark,3)
    if species.get('render_mode') in {'overlay','skeleton'}:
        pen.line(pts,(220,226,201),3)
        for i in range(3,12):
            x,y=pts[i];pen.line([(x-7,y-widths[i]*.4),(x,y),(x-7,y+widths[i]*.4)],(213,221,195),2)


def draw_pinniped(draw,sim,species,time,*unused):
    pen=Pen(draw,sim.x,sim.y,sim.angle);w=words(species)
    base=tuple(species['fur_mid']);dark=tuple(species['fur_dark'])
    for side in (-1,1):
        pen.poly([(-66,side*28),(-86,side*90),(-121,side*101),(-110,side*32)],base,dark)
        pen.poly([(-251,side*9),(-286,side*(43+math.sin(time*2)*5)),(-310,side*47),(-293,side*8)],base,dark)
    pen.taper([(28,0),(-20,0),(-82,0),(-150,0),(-218,0),(-272,0)],[42,65,105,111,75,20],base,dark)
    pen.oval(24,0,37,30,base,dark)
    pen.oval(48,0,18,22,blend(base,(201,184,155),.4),dark)
    for side in (-1,1):
        pen.oval(33,side*20,4,4,(22,24,24))
        for i in range(4): pen.line([(48,side*9),(64-i*4,side*(32+i*3))],(204,195,172),1)
        if 'walrus' in w: pen.taper([(44,side*17),(79,side*22),(108,side*20)],[9,7,1],(228,219,192),dark)
        if 'lion' in w: pen.poly([(9,side*25),(0,side*43),(-8,side*28)],base,dark)


def draw_shell_special(draw,sim,species,time,*unused):
    plan=resolve_body_plan(species);pen=Pen(draw,sim.x,sim.y,sim.angle)
    base=tuple(species['fur_mid']);dark=tuple(species['fur_dark'])
    if plan=='horseshoe':
        pen.taper([(-88,0),(-166,math.sin(time)*3),(-266,math.sin(time)*7)],[15,8,1],(107,89,57),dark)
        for side in (-1,1):
            for i in range(5): pen.line([(-5-i*14,side*30),(-25-i*14,side*73),(-35-i*14,side*89)],(123,99,65),4)
        pen.poly([(-30,-70),(-71,-56),(-104,-31),(-104,31),(-71,56),(-30,70)],(113,95,62),dark)
        pen.poly([(59,0),(40,-62),(-3,-86),(-62,-72),(-49,0),(-62,72),(-3,86),(40,62)],(147,124,77),dark,3)
        pen.line([(32,-53),(8,-63),(-27,-56)],(188,162,106),3)
    elif plan=='nautilus':
        for i in range(24):
            a=-1.2+i/23*2.4
            pen.line([(20,0),(50+math.cos(a)*17,math.sin(a)*36),(92+math.sin(time*2+i)*13,math.sin(a)*76)],(207,170,121),2)
        pen.oval(-45,0,91,93,(219,201,161),dark,2)
        for i in range(18):
            a=i*math.tau/18
            pen.poly([(-45+math.cos(a)*86,math.sin(a)*89),(-45+math.cos(a+.11)*86,math.sin(a+.11)*89),(-45+math.cos(a+.32)*45,math.sin(a+.32)*45)],(144,88,55))
        spiral=[(-45+math.cos(i*.13)*(.55+i*.40), math.sin(i*.13)*(.55+i*.40)) for i in range(165)]
        pen.line(spiral,(113,79,48),2)
        pen.oval(34,-22,7,7,(39,37,30));pen.oval(36,-24,2,2,(228,220,197))
    else:  # stalked barnacle, NOT a shrimp with raptorial claws
        pen.taper([(-135,0),(-90,8),(-22,0)],[35,28,23],(127,100,82),dark)
        pen.poly([(-31,0),(-5,-37),(39,-32),(65,0),(39,32),(-5,37)],(213,211,191),dark,3)
        pen.line([(-18,0),(43,0),(57,0)],(132,135,124),2)
        for i in range(10):
            y=(i-5)*5
            pen.line([(49,y),(81,y*1.6),(107+math.sin(time*3+i*.2)*7,y*2.8)],(180,153,102),2)


def draw_shrimp(draw, sim, species, time, *unused):
    """Dorsal decapod study: five walking-leg pairs, abdomen and tail fan.

    Ordinary shrimp do not inherit a stomatopod's striking clubs. Appendage
    proportions remain illustrative; pistol shrimp get one enlarged chela.
    """
    pen = Pen(draw, sim.x, sim.y, sim.angle)
    base = (184, 130, 98)
    dark = (81, 64, 51)
    light = (218, 184, 150)
    for side in (-1, 1):
        for i in range(5):
            root = (-9-i*13, side*19)
            phase = time*5-i*.8+side*math.pi
            knee = (root[0]-15, side*(45+i*3))
            foot = (root[0]-34+math.sin(phase)*8, side*(69+i*3))
            pen.taper([root, knee, foot], [5, 3, 1], base, dark)
        # Antennules and the much longer sensory antennae.
        pen.line([(23, side*9), (74, side*28), (126, side*(50+math.sin(time*2)*4))], light, 2)
        pen.line([(27, side*6), (64, side*10), (93, side*17)], base, 2)
    points = [(-65-i*22, math.sin(time*3-i*.35)*i*1.4) for i in range(7)]
    ex, ey = points[-1]
    for side in (-1, 1):
        pen.poly([(ex+9, ey), (ex-12, ey+side*39), (ex-44, ey+side*36), (ex-29, ey)], light, dark)
    pen.poly([(ex, ey-9), (ex-39, ey-12), (ex-52, ey), (ex-39, ey+12), (ex, ey+9)], base, dark)
    for i in reversed(range(7)):
        x, y = points[i]
        pen.oval(x, y, 19, 29-i*2.8, base, dark, 2)
        pen.line([(x-4, y-18+i*2), (x+3, y), (x-4, y+18-i*2)], light, 1)
    pen.taper([(35, 0), (8, 0), (-33, 0), (-75, 0)], [10, 49, 62, 44], base, dark)
    pen.poly([(9, -5), (66, 0), (9, 5)], light, dark, curved=False)
    for side in (-1, 1):
        pen.line([(16, side*17), (33, side*28)], base, 4)
        pen.oval(34, side*29, 6, 6, (32, 34, 29), light)
    if "pistol" in words(species):
        pen.taper([(0, 21), (27, 51), (64, 57)], [8, 11, 15], base, dark)
        pen.poly([(53, 48), (83, 39), (96, 51), (81, 54), (93, 64), (68, 69)], base, dark, curved=False)


def scorpion_pose(species, time, travel=None):
    """Dorsal 2D study: eight walking legs, chelate pedipalps and metasoma.

    Tail bends IN the illustration plane; this is not projection of a raised
    tail. All links are fixed-length artist controls, not specimen dimensions.
    The independent tail/pincer cycle is not required to match the walking gait.
    """
    if not supports_scorpion_rig(species) or not math.isfinite(time):
        raise ValueError('Scorpion diagnostics require a true scorpion and finite time')
    travel = time*28 if travel is None else travel
    if not math.isfinite(travel):
        raise ValueError('Scorpion travel must be finite')
    w = words(species)
    form = 'robust' if w & {'emperor', 'volt'} else 'slender'
    robust = form == 'robust'
    rx, ry = (36.0, 31.0) if robust else (31.0, 25.0)
    stride, duty = 26.0, .70
    limbs = []
    for side in (-1, 1):
        for index in range(4):
            root = (rx*(.52, .18, -.18, -.52)[index], side*ry*(.76, .94, .94, .76)[index])
            offset = ((index+(side == 1)) % 2)*.5
            phase = (travel/stride+offset) % 1
            neutral_x = root[0]+(39, 10, -29, -60)[index]
            reach_y = (92, 105, 109, 98)[index]
            if phase < duty:
                foot_x, foot_y = neutral_x+stride*(duty/2-phase), side*reach_y
            else:
                q = (phase-duty)/(1-duty)
                eased = q**3*(10+q*(-15+6*q))
                foot_x = neutral_x-stride*duty/2-stride*(1-duty)*q+stride*eased
                foot_y = side*(reach_y-7*math.sin(math.pi*q)**2)
            distal = 12.0
            ankle = (foot_x, foot_y-side*distal)
            total = math.hypot(neutral_x-root[0], reach_y-abs(root[1])-distal)*1.32+stride*.35
            lengths = [total*.51, total*.49, distal]
            root, knee, end = solve_two_bone_ik(root, ankle, *lengths[:2], side)
            foot = (end[0], end[1]+side*distal)
            limbs.append(dict(side=side, index=index, points=[root,knee,end,foot],
                              lengths=lengths, phase=phase, phase_offset=offset,
                              target=(foot_x,foot_y), planted=phase < duty,
                              contact=(foot[0]+travel,foot[1])))

    def advance(point, length, angle):
        return point[0]+length*math.cos(angle), point[1]+length*math.sin(angle)

    pedipalps = []
    for side in (-1, 1):
        angles = (side*(.88+.035*math.sin(time*1.6)), side*(.28+.04*math.sin(time*1.6+.4)))
        points = [(rx*.72, side*ry*.61)]
        lengths = [43.0, 39.0] if robust else [49.0, 43.0]
        for length, angle in zip(lengths, angles):
            points.append(advance(points[-1], length, angle))
        angle = angles[-1]
        palm_length, palm_width = (29.0, 17.0) if robust else (22.0, 8.0)
        def palm_point(x, y):
            return (points[-1][0]+x*math.cos(angle)-y*math.sin(angle),
                    points[-1][1]+x*math.sin(angle)+y*math.cos(angle))
        palm = [palm_point(palm_length*(.5+.6*math.cos(k*math.tau/32)),
                           palm_width*math.sin(k*math.tau/32)) for k in range(32)]
        fixed_root = palm_point(palm_length*.85, -side*palm_width*.60)
        moving_root = palm_point(palm_length*.72, side*palm_width*.65)
        opening = .27+.12*math.sin(time*1.6+.8)
        fixed = [fixed_root, advance(fixed_root, 27.0, angle+side*.12)]
        moving = [moving_root, advance(moving_root, 27.0, angle-side*opening)]
        pedipalps.append(dict(side=side, points=points, lengths=lengths, palm=palm,
                             fingers=[fixed,moving], finger_lengths=[27.0,27.0]))
    # Seven dorsal mesosoma plates, then five metasomal segments; telson separate.
    mesosoma = [(-rx-9-index*13, 0, 12, ry*(1.01-index*.075)) for index in range(7)]
    tail = [(mesosoma[-1][0]-11, 0)]
    tail_lengths = [20.0, 22.0, 24.0, 26.0, 29.0] if robust else [24.0, 26.0, 28.0, 30.0, 33.0]
    for index, length in enumerate(tail_lengths):
        angle = math.pi+.15+index*.13+.08*math.sin(time*1.6-index*.3)
        tail.append(advance(tail[-1], length, angle))
    telson_center = advance(tail[-1], 9, angle)
    tip = advance(telson_center, 27, angle-.48)
    stinger = [tail[-1], telson_center, advance(telson_center, 17, angle), tip]
    return dict(plan='arachnid', rig_type='scorpion', form=form, limbs=limbs,
                prosoma=(0,0,rx,ry), mesosoma=mesosoma, pedipalps=pedipalps,
                tail=tail, tail_lengths=tail_lengths, telson=(*telson_center,12,8), stinger=stinger,
                limb_width=7 if robust else 4, stride=stride, duty=duty,
                cycle_seconds=stride/28, travel_speed=28.0, appendage_cycle_seconds=math.tau/1.6)


def draw_scorpion(draw, sim, species, time, *unused):
    """Shared planar geometry for surface, overlay and exoskeleton joint guide."""
    pose = scorpion_pose(species,time)
    pen = Pen(draw,sim.x,sim.y,sim.angle)
    base = (70,76,65) if pose['form'] == 'robust' else (187,155,88)
    dark, light = blend(base,(17,22,22),.60), blend(base,(239,225,185),.32)
    guide = (223,232,205)
    mode = species.get('render_mode','surface')
    if mode != 'skeleton':
        for limb in pose['limbs']:
            width = pose['limb_width']
            for index in range(3):
                pen.taper(limb['points'][index:index+2], [width*(1-index*.25),max(2,width*(.75-index*.25))],base,dark)
            for x,y in limb['points'][1:3]: pen.oval(x,y,width*.44,width*.44,light,dark)
        for palp in pose['pedipalps']:
            for index in range(2): pen.taper(palp['points'][index:index+2],[10,8],base,dark)
            pen.poly(palp['palm'],base,dark,2,False)
            for finger in palp['fingers']: pen.taper(finger,[6,1.6],base,dark)
        for segment in reversed(pose['mesosoma']):
            pen.oval(*segment,base,dark,2)
            x,y,rx,ry = segment
            pen.line([(x-2,y-ry*.7),(x+3,y),(x-2,y+ry*.7)],light,1)
        pen.oval(*pose['prosoma'],base,dark,2)
        pen.line([(-22,-17),(2,-20),(20,-10)],light,2)
        for side in (-1,1):
            pen.oval(12,side*6,2.6,2.6,(16,20,19),light)
            pen.line([(pose['prosoma'][2]-3,side*6),(pose['prosoma'][2]+8,side*5)],dark,4,False)
        for index in range(5):
            pen.taper(pose['tail'][index:index+2],[16-index,15-index],base,dark)
            pen.oval(*pose['tail'][index+1],5,5,light,dark)
        pen.oval(*pose['telson'],base,dark,2)
        pen.taper(pose['stinger'][1:],[10,5,1],dark)
    if mode in {'overlay','skeleton'}:
        pen.oval(*pose['prosoma'],None,guide,2)
        for segment in pose['mesosoma']: pen.oval(*segment,None,guide,1)
        pen.oval(*pose['telson'],None,guide,2)
        pen.line(pose['stinger'],guide,1,False)
        chains = [limb['points'] for limb in pose['limbs']]+[pose['tail']]
        for palp in pose['pedipalps']:
            pen.poly(palp['palm'],None,guide,1,False)
            chains.append(palp['points'])
            chains.extend(palp['fingers'])
        for points in chains:
            pen.line(points,guide,2,False)
            for x,y in points: pen.oval(x,y,2.5,2.5,guide)
        for limb in pose['limbs']:
            pen.oval(*limb['points'][-1],3.5,3.5,(112,220,165) if limb['planted'] else (240,182,94))


def spider_pose(species, time, travel=None):
    """Pure dorsal eight-leg pose; three fixed links per leg are rig controls.

    Four roots per side attach to the prosoma, never the abdomen. Pedipalps
    are separate non-walking appendages. The alternating-tetrapod timing and
    translated local contacts are an illustration, not a measured spider gait.
    """
    if not supports_spider_rig(species) or not math.isfinite(time):
        raise ValueError('Spider diagnostics require a supported true spider and finite time')
    travel = time*32 if travel is None else travel
    if not math.isfinite(travel):
        raise ValueError('Spider travel must be finite')
    w = words(species)
    family = ('tarantula' if 'tarantula' in w or {'ornamental', 'tree'} <= w else
              'jumping' if w & {'jumping', 'peacock'} else
              'widow' if 'widow' in w else 'orb_weaver' if 'weaver' in w else
              'laterigrade' if w & {'crab', 'huntsman', 'sand'} else 'ground')
    # Length, radius and outward leg reach differentiate broad family silhouettes.
    shapes = {'tarantula': (32,29,44,34,104,9), 'jumping': (31,27,32,23,73,7),
              'widow': (23,20,40,36,100,4), 'orb_weaver': (24,18,45,25,130,3),
              'laterigrade': (30,27,36,28,129,5), 'ground': (30,24,38,26,105,5)}
    rx,ry,ax,ay,reach,width = shapes[family]
    stride, duty = (22.0 if family == 'jumping' else 30.0), .68
    limbs = []
    for side in (-1,1):
        for index in range(4):
            root_x = rx*(.55,.20,-.20,-.55)[index]
            root_y = side*ry*(.77,.94,.94,.77)[index]
            root = (root_x,root_y)
            offset = ((index+(side == 1))%2)*.5
            phase = (travel/stride+offset)%1
            splay = (1.0,.50,-.38,-.95)[index]
            if family == 'laterigrade': splay = (.62,.25,-.22,-.64)[index]
            neutral_x = root_x+splay*reach*.72
            reach_y = reach*(.87,1.04,1.04,.90)[index]
            if family == 'laterigrade' and index < 2: reach_y *= 1.16
            if phase < duty:
                foot_x = neutral_x+stride*(duty/2-phase)
                foot_y = side*reach_y
            else:
                q = (phase-duty)/(1-duty)
                eased = q**3*(10+q*(-15+6*q))
                foot_x = neutral_x-stride*duty/2-stride*(1-duty)*q+stride*eased
                foot_y = side*(reach_y-7*math.sin(math.pi*q)**2)
            distal = 13.0
            ankle = (foot_x,foot_y-side*distal)
            # Constant lengths leave reach margin across the entire stride.
            neutral_reach = math.hypot(neutral_x-root_x,reach_y-abs(root_y)-distal)
            total = neutral_reach*1.32+stride*.35
            upper,lower = total*.51,total*.49
            root,knee,end = solve_two_bone_ik(root,ankle,upper,lower,side)
            foot = (end[0],end[1]+side*distal)
            limbs.append({'side':side,'index':index,'points':[root,knee,end,foot],
                          'lengths':[upper,lower,distal],'target':(foot_x,foot_y),
                          'phase':phase,'phase_offset':offset,'planted':phase < duty,
                          'contact':(foot[0]+travel,foot[1])})
    abdomen = (-rx-ax+6,0,ax,ay)
    pedipalps = [[(rx*.78,side*ry*.38),(rx+12,side*ry*.71),(rx+24,side*ry*.60)]
                for side in (-1,1)]
    return {'plan':'arachnid','rig_type':'spider','family':family,'limbs':limbs,
            'prosoma':(0,0,rx,ry),'abdomen':abdomen,'pedipalps':pedipalps,
            'pedicel':[(-rx+4,0),(abdomen[0]+ax-3,0)],'limb_width':width,
            'stride':stride,'duty':duty,'cycle_seconds':stride/32,'travel_speed':32.0}


def draw_spider(draw, sim, species, time, *unused):
    """Surface and joint guide consume the same eight-leg geometry in 2D."""
    pose = spider_pose(species,time)
    pen = Pen(draw,sim.x,sim.y,sim.angle)
    family = pose['family']
    base = {'tarantula':(116,81,57),'jumping':(64,71,66),'widow':(41,42,43),
            'orb_weaver':(153,128,70),'laterigrade':(166,147,98),'ground':(124,100,70)}[family]
    w = words(species)
    if 'cobalt' in w: base = (54,84,121)
    if 'greenbottle' in w: base = (76,107,112)
    dark = blend(base,(17,21,23),.62)
    light = blend(base,(233,213,175),.38)
    guide = (223,232,205)
    mode = species.get('render_mode','surface')
    rx = pose['prosoma'][2]
    if mode != 'skeleton':
        for limb in pose['limbs']:
            points = limb['points']
            width = pose['limb_width']
            widths = (width*1.2,width,width*.56,1.8)
            for i in range(3):
                pen.taper(points[i:i+2],widths[i:i+2],base,dark)
                if family == 'tarantula':
                    a,b = points[i:i+2]
                    dx,dy = b[0]-a[0],b[1]-a[1]
                    length = math.hypot(dx,dy)
                    for fraction in (.25,.45,.65,.85):
                        x,y = a[0]+dx*fraction,a[1]+dy*fraction
                        pen.line([(x,y),(x-dy/length*(width*.7+2),y+dx/length*(width*.7+2))],light,1,False)
            for x,y in points[1:3]:
                color = (187,111,62) if w & {'redknee','redleg'} else light
                pen.oval(x,y,width*.5,width*.5,color,dark)
        pen.line(pose['pedicel'],dark,10,False)
        pen.oval(*pose['abdomen'],base,dark,2)
        pen.oval(*pose['prosoma'],base,dark,2)
        # Dorsal markings only: never paint a widow's ventral hourglass on its back.
        ax,ay,arx,ary = pose['abdomen']
        if family in {'ground','tarantula'}:
            pen.line([(ax-arx*.6,0),(ax+arx*.55,0)],light,3,False)
            for i in range(4):
                x = ax-arx*.4+i*arx*.24
                pen.line([(x-5,-ary*.40),(x,0),(x-5,ary*.40)],dark,2)
        if family == 'jumping':
            for x,y in ((ax+8,0),(ax-10,-9),(ax-10,9)):
                pen.oval(x,y,4,3,(211,211,185))
        for palp in pose['pedipalps']:
            pen.line(palp,light,4,False)
        for side in (-1,1):
            pen.line([(rx*.85,side*5),(rx+9,side*7),(rx+11,side*3)],dark,3)
        # Schematic eye field; no species-level eye-count/layout claim.
        for side in (-1,1):
            pen.oval(rx*.71,side*7,4 if family == 'jumping' else 2.5,3,(18,22,22),light)
            pen.oval(rx*.40,side*16,2,2,(18,22,22))
    if mode in {'overlay','skeleton'}:
        pen.oval(*pose['abdomen'],None,guide,2)
        pen.oval(*pose['prosoma'],None,guide,2)
        pen.line(pose['pedicel'],guide,2,False)
        for palp in pose['pedipalps']: pen.line(palp,guide,1,False)
        for limb in pose['limbs']:
            pen.line(limb['points'],guide,2,False)
            for x,y in limb['points'][:-1]: pen.oval(x,y,2.8,2.8,guide)
            color = (112,220,165) if limb['planted'] else (240,182,94)
            pen.oval(*limb['points'][-1],3.5,3.5,color)


INSECT_PLANS = frozenset({'orthoptera', 'cicada', 'stick_insect', 'insect'})


def insect_pose(species, time, travel=None):
    """Pure planar six-leg study with fixed links and alternating tripod timing.

    Contacts are stationary only in a straight rig-local reference translated by
    ``travel``. Dorsal swing is a lateral excursion, NOT physical foot elevation;
    cursor steering, substrate forces, flight and jumping are not simulated.
    Three links per leg are animation controls, not a full anatomical inventory.
    """
    plan = resolve_body_plan(species)
    if plan not in INSECT_PLANS or not math.isfinite(time):
        raise ValueError('Six-leg diagnostics require a supported insect and finite time')
    travel = time*36 if travel is None else travel
    if not math.isfinite(travel):
        raise ValueError('Insect travel must be finite')
    stick = plan == 'stick_insect'
    mole = {'mole', 'cricket'} <= words(species)
    radius = 9 if stick else 30
    length = 210 if stick else 143
    stride, duty = 32.0, .65
    limbs = []
    for side in (-1, 1):
        for index in range(3):
            offset = ((index + (side == 1)) % 2)*.5
            phase = (travel/stride+offset) % 1
            root = (-12-index*21, side*radius*.65)
            enlarged_hind = index == 2 and plan == 'orthoptera' and not mole
            reach_y = 132 if enlarged_hind else 100 if stick else 94
            neutral_x = root[0]+(20, -12, -35)[index]
            if phase < duty:
                foot_x = neutral_x+stride*(duty/2-phase)
                foot_y = side*reach_y
            else:
                q = (phase-duty)/(1-duty)
                eased = q**3*(10+q*(-15+6*q))
                foot_x = neutral_x-stride*duty/2-stride*(1-duty)*q+stride*eased
                foot_y = side*(reach_y-8*math.sin(math.pi*q)**2)
            # A fixed outward distal link keeps the tarsus connected to the IK.
            distal = 12.0
            ankle = (foot_x, foot_y-side*distal)
            total = (reach_y-abs(root[1]))*1.38
            split = .58 if enlarged_hind else .50
            upper, lower = total*split, total*(1-split)
            root, knee, end = solve_two_bone_ik(root, ankle, upper, lower, side)
            foot = (end[0], end[1]+side*distal)
            limbs.append({'index': index, 'side': side, 'points': [root,knee,end,foot],
                          'lengths': [upper,lower,distal], 'phase': phase, 'phase_offset': offset,
                          'planted': phase < duty, 'contact': (foot[0]+travel,foot[1]),
                          'target': (foot_x,foot_y), 'enlarged_hind': enlarged_hind,
                          'digging_front': mole and index == 0})
    return {'plan': plan, 'length': length, 'radius': radius, 'limbs': limbs,
            'stride': stride, 'duty': duty, 'cycle_seconds': stride/36,
            'head': (21,0,17,19), 'thorax': [(8,0),(-12,0),(-33,0),(-57,0)],
            'abdomen': [(-57,0),(-length*.67,0),(-length,0)], 'mole_cricket': mole}


def draw_special_insect(draw,sim,species,time,*unused):
    """One shared six-leg pose for surface and schematic exoskeleton guides."""
    pose = insect_pose(species,time)
    pen = Pen(draw,sim.x,sim.y,sim.angle)
    base, dark = tuple(species['fur_mid']), tuple(species['fur_dark'])
    light = blend(base,(223,225,183),.35)
    guide = (218,231,205)
    mode = species.get('render_mode','surface')
    radius, length = pose['radius'], pose['length']
    if mode != 'skeleton':
        for limb in pose['limbs']:
            widths = [15,11,4,2] if limb['enlarged_hind'] else [6,5,3,2]
            if limb['digging_front']: widths = [12,14,9,3]
            points = limb['points']
            # Draw individual straight links: no smoothed taper bends off-rig.
            for i in range(3):
                pen.taper(points[i:i+2],widths[i:i+2],base,dark)
            for (x,y),width in zip(points[1:3],widths[1:3]):
                pen.oval(x,y,width*.45,width*.45,light,dark)
            if limb['digging_front']:
                x,y = points[2]
                for i in range(3):
                    pen.line([(x-i*4,y),(x-i*4-3,y+limb['side']*8)],dark,2,curved=False)
        pen.taper(pose['abdomen'],[radius*1.7,radius*1.5,4],base,dark)
        pen.taper(pose['thorax'],[radius*1.25,radius*1.65,radius*1.8,radius*1.7],base,dark)
        if pose['plan'] != 'stick_insect':
            for side in (-1,1):
                pen.poly([(-33,side*3),(-68,side*28),(-length+5,side*10)],light,dark)
            for i in range(6):
                pen.line([(-63-i*11,-radius*.5),(-67-i*11,radius*.5)],dark,1)
        pen.oval(*pose['head'],base,dark)
        for side in (-1,1):
            pen.oval(28,side*13,6,7,(75,75,42),dark)
            pen.line([(30,side*10),(66,side*20),(94,side*(22+math.sin(time)*3))],dark,2)
    if mode in {'overlay','skeleton'}:
        # Insects have exoskeletons: these are linked joint guides, not bones.
        pen.oval(*pose['head'],None,guide,2)
        pen.line(pose['thorax']+pose['abdomen'][1:],guide,2,curved=False)
        for limb in pose['limbs']:
            pen.line(limb['points'],guide,2,curved=False)
            for x,y in limb['points'][:-1]: pen.oval(x,y,3,3,guide)
            x,y = limb['points'][-1]
            color = (112,220,165) if limb['planted'] else (240,182,94)
            pen.oval(x,y,4,4,color)
