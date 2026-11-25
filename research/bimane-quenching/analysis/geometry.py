"""Steric sampling of a cysteine-bound bimane and a tryptophan on one protein."""
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from scipy.spatial.distance import cdist
from scipy.spatial.transform import Rotation

VDW = {"C": 1.70, "N": 1.55, "O": 1.52, "S": 1.80}
BACKBONE_CB = {"N", "CA", "C", "O", "OXT", "CB"}
INDOLE = ("CG", "CD1", "CD2", "NE1", "CE2", "CE3", "CZ2", "CZ3", "CH2")
BIMANE_RING = ("C1", "C2", "C3", "C4", "C5", "C6", "N1", "N2")
CHI1 = (-75, -60, -45, 45, 60, 75, 165, 180, 195)
TRP_CHI2 = (-110, -90, -70, 70, 90, 110)
THIOETHER = (-60, 60, 180)
MAX_TOLERANCE = 0.4

@dataclass
class Atom:
    site: int
    aa: str
    name: str
    element: str
    xyz: np.ndarray

def read_chain(path: Path, *, ligand=False):
    """First model, chain A, blank/A alternate locations. Exclude waters and H."""
    atoms = {}
    for line in path.read_text().splitlines():
        if line.startswith("ENDMDL"):
            break
        record = line[:6].strip()
        aa = line[17:20].strip()
        if record != "ATOM" and not (ligand and record == "HETATM" and aa == "9UM"):
            continue
        if line[21] != "A" or line[16] not in " A":
            continue
        element = line[76:78].strip()
        if element in ("H", "D"):
            continue
        site, name = int(line[22:26]), line[12:16].strip()
        xyz = np.array([float(line[i:i+8]) for i in (30, 38, 46)])
        assert (site, name) not in atoms
        atoms[site, name] = Atom(site, aa, name, element, xyz)
    return atoms

def points(atoms, site, names):
    return np.array([atoms[site, name].xyz for name in names])

def unit(vector):
    return vector / np.linalg.norm(vector)

def frame(n, ca, cb):
    axis = unit(cb - ca)
    normal = unit(n - ca - np.dot(n-ca, axis)*axis)
    return np.array([axis, normal, np.cross(axis, normal)])

def transplant(coords, source, target):
    """Retain donor geometry beyond C-beta and align the N/CA/CB local frame."""
    return (coords - source[2]) @ frame(*source).T @ frame(*target) + target[2]

def torsion(a, b, c, d):
    axis = unit(c-b)
    v = a-b - np.dot(a-b, axis)*axis
    w = d-c - np.dot(d-c, axis)*axis
    return np.degrees(np.arctan2(np.cross(axis, v).dot(w), v.dot(w)))

def set_torsion(coords, a, b, c, d, target):
    angle = np.radians(target-torsion(a,b,c,d))
    return Rotation.from_rotvec(angle*unit(c-b)).apply(coords-c)+c

def tryptophans(reference, anchors, fixed=None):
    if fixed is not None:
        return fixed[None, :, :]
    n, ca, cb = anchors
    donor_anchors, donor_ring = reference
    ring = transplant(donor_ring, donor_anchors, anchors)
    trial = []
    for chi1 in CHI1:
        first = set_torsion(ring, n, ca, cb, ring[0], chi1)
        for chi2 in TRP_CHI2:
            trial.append(set_torsion(first, ca, cb, first[0], first[1], chi2))
    return np.array(trial)

@dataclass
class Dye:
    names: list
    elements: list
    xyz: np.ndarray
    anchors: np.ndarray

def dye_reference(structure):
    lig = [a for a in structure.values() if a.aa == "9UM" and a.site == 201]
    assert len(lig) == 14 and all(a.element != "BR" for a in lig)
    return Dye(["SG"]+[a.name for a in lig], ["S"]+[a.element for a in lig],
               np.array([structure[151,"SG"].xyz]+[a.xyz for a in lig]),
               points(structure,151,("N","CA","CB")))

def dye_conformers(dye, anchors, grid_shift, thioether=THIOETHER):
    n, ca, cb = anchors
    keys = {s:i for i,s in enumerate(dye.names)}
    original = transplant(dye.xyz, dye.anchors, anchors)
    trial = []
    for chi1 in CHI1:
        first = set_torsion(original, n, ca, cb, original[0], chi1)
        sg = first[0]
        for chi2 in thioether:
            second = set_torsion(first, ca, cb, sg, first[keys["C8"]], chi2)
            for chi3 in thioether:
                third = set_torsion(second, cb, sg, second[keys["C8"]], second[keys["C4"]], chi3)
                for angle in range(-180,180,15):
                    last = set_torsion(third, sg, third[keys["C8"]], third[keys["C4"]], third[keys["N1"]], angle+grid_shift)
                    # This last axis does not pass through sulfur, which stays fixed.
                    last[0] = sg
                    trial.append(last)
    return np.array(trial)

def environment(atoms, w, c, origin):
    return [a for a in atoms.values() if (a.site not in (w,c) or a.name in BACKBONE_CB)
            and np.linalg.norm(a.xyz-origin) <= 18.0]

def local_clearance(poses, names, elements, env, site, backbone_bonds):
    """Minimum heavy-atom clearance in Å. Exempt 1–2/1–3, relax 1–4 by 0.50 Å."""
    req = np.add.outer([VDW[x] for x in elements], [VDW[a.element] for a in env])
    # Dictionary gives distance in bonds from each mobile atom to C-beta.
    to_cb = {"CB":0, "CA":1, "N":2, "C":2, "O":3, "OXT":3}
    for j,a in enumerate(env):
        if a.site != site:
            continue
        for i, name in enumerate(names):
            separation = backbone_bonds.get(name,99) + to_cb[a.name]
            if separation <= 2:
                req[i,j] = -np.inf
            elif separation == 3:
                req[i,j] -= 0.50
    xyz = np.array([a.xyz for a in env])
    minima = np.empty(len(poses))
    for start in range(0,len(poses),128):
        block=poses[start:start+128]
        distances=cdist(block.reshape(-1,3),xyz).reshape(len(block),len(names),len(env))
        minima[start:start+len(block)]=(distances-req).min(axis=(1,2))
    return minima

def joint_clearance(atoms, w, c, wposes, dposes, dye, *, fixed_native_trp=False):
    """Return clearance and nearest ring distance for each potentially valid pair."""
    welements = [name[0] for name in INDOLE]
    wenv = environment(atoms,w,c,atoms[w,"CB"].xyz)
    denv = environment(atoms,w,c,atoms[c,"CB"].xyz)
    if fixed_native_trp:
        # Pre-existing, unaltered contacts are part of the experimental scaffold.
        # Every new dye–Trp contact is still checked below.
        assert np.array_equal(wposes[0],points(atoms,w,INDOLE)) and len(wposes)==1
        wgaps = np.array([np.inf])
    else:
        wgaps = local_clearance(wposes, INDOLE, welements, wenv, w,
                                {"CG":1,"CD1":2,"CD2":2,"CE2":3,"CE3":3,"NE1":3})
    dgaps = local_clearance(dposes, dye.names, dye.elements, denv, c,
                            {"SG":1,"C8":2,"C4":3})
    # C8 and C4 are 1 or 2 bonds from sulfur. C5 and N1 are 3 bonds away.
    intradye = np.array([VDW["S"]+VDW[e] for e in dye.elements])
    for i,name in enumerate(dye.names):
        if name in ("SG","C8","C4"):
            intradye[i] = -np.inf
        elif name in ("C5","N1"):
            intradye[i] -= 0.50
    internal = np.linalg.norm(dposes-dposes[:,0:1,:],axis=2)-intradye
    dgaps = np.minimum(dgaps,internal.min(axis=1))
    wkeep, dkeep = wgaps >= -MAX_TOLERANCE, dgaps >= -MAX_TOLERANCE
    wposes, wgaps = wposes[wkeep], wgaps[wkeep]
    dposes, dgaps = dposes[dkeep], dgaps[dkeep]
    ring_indices = [dye.names.index(s) for s in BIMANE_RING]
    req = np.add.outer([VDW[e] for e in dye.elements],[VDW[e] for e in welements])
    joint, nearest = [], []
    for wp, wg in zip(wposes, wgaps):
        if not len(dposes):
            break
        cross = cdist(dposes.reshape(-1,3),wp).reshape(len(dposes),len(dye.names),len(wp))
        joint.append(np.minimum(np.minimum(dgaps,wg),(cross-req).min(axis=(1,2))))
        nearest.append(cross[:,ring_indices,:].min(axis=(1,2)))
    if not joint:
        return np.empty(0), np.empty(0)
    return np.concatenate(joint), np.concatenate(nearest)

def c_beta_sasa(atoms, site, samples=1024):
    """Shrake–Rupley area (Å²) of the native Ala C-beta, with a 1.4 Å probe."""
    atom = atoms[site,"CB"]
    radius = VDW["C"]+1.4
    i = np.arange(samples)+0.5
    z = 1-2*i/samples
    angle = np.pi*(3-np.sqrt(5))*i
    circle = np.sqrt(1-z*z)
    sphere = np.column_stack((circle*np.cos(angle),circle*np.sin(angle),z))
    env = [a for a in atoms.values() if a is not atom and np.linalg.norm(a.xyz-atom.xyz)<radius+VDW[a.element]+1.4]
    dist = cdist(sphere*radius+atom.xyz,[a.xyz for a in env])
    exposed = (dist >= np.array([VDW[a.element]+1.4 for a in env])).all(axis=1)
    return 4*np.pi*radius**2*exposed.mean()
