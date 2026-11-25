"""Independent consistency checks of published inputs and derived results."""
from pathlib import Path
import csv
import numpy as np
import sys
from scipy.stats import spearmanr
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"analysis"))
from geometry import (INDOLE, THIOETHER, read_chain, dye_reference, dye_conformers, points, torsion, tryptophans)

def read(name):
    with (ROOT/"results"/name).open() as f:
        return list(csv.DictReader(f))

def main():
    rows=read("calibration.csv")
    assert len(rows)==5 and len({r["pair"] for r in rows})==5
    assert all(0<=int(r["contacts"])<=int(r["allowed"]) for r in rows)
    obs=[float(r["static_pct"]) for r in rows]
    dist=[-float(r["ca_A"]) for r in rows]
    score=[int(r["contacts"])/int(r["allowed"]) for r in rows]
    rec=read("rank_metrics.csv")
    for name,vals in (("distance",dist),("geometry",score)):
        provided=next(r for r in rec if r["outcome"]=="digitized" and r["predictor"]==name)
        np.testing.assert_allclose(float(provided["rho"]),spearmanr(obs,vals).statistic,atol=1e-6)
    all_scores=read("geometry_sensitivity.csv")
    for row in rows:
        pair=[r for r in all_scores if r["pair"]==row["pair"]]
        thresholds=sorted((float(r["cutoff_A"]),int(r["contacts"])) for r in pair if r["setting"].startswith("contact_") or r["setting"]=="primary")
        assert all(b[1]>=a[1] for a,b in zip(thresholds,thresholds[1:]))
        primary=next(r for r in pair if r["setting"]=="primary")
        denser=next(r for r in pair if r["setting"]=="dense_linker")
        assert int(denser["allowed"])>=int(primary["allowed"]) and int(denser["contacts"])>=int(primary["contacts"])
    base=ROOT/"data/structures"
    alpha=read_chain(base/"2A3D.pdb")
    donor=dye_reference(read_chain(base/"9PHR.pdb",ligand=True))
    anc=("N","CA","CB")
    anchor=points(alpha,55,anc)
    poses=dye_conformers(donor,anchor,0)
    assert len(poses)==1944
    names={name:i for i,name in enumerate(donor.names)}
    c8,c4,n1=[names[v] for v in ("C8","C4","N1")]
    bond=np.linalg.norm(donor.xyz[0]-donor.xyz[c8])
    np.testing.assert_allclose(np.linalg.norm(poses[:,0]-poses[:,c8],axis=1),bond,atol=1e-10)
    p=poses[0];n,ca,cb=anchor
    actual=[torsion(n,ca,cb,p[0]),torsion(ca,cb,p[0],p[c8]),torsion(cb,p[0],p[c8],p[c4]),torsion(p[0],p[c8],p[c4],p[n1])]
    np.testing.assert_allclose((np.array(actual) - [-75,THIOETHER[0],THIOETHER[0],-180]+180)%360-180,0,atol=1e-9)
    wposes=tryptophans((points(alpha,4,anc),points(alpha,4,INDOLE)),points(alpha,4,anc))
    assert len(wposes)==54
    w=wposes[0];n,ca,cb=points(alpha,4,anc)
    np.testing.assert_allclose([torsion(n,ca,cb,w[0]),torsion(ca,cb,w[0],w[1])],[-75,-110],atol=1e-9)
    eligible=[r for r in read("alpha3d_sites.csv") if r["eligible"]=="True"]
    assert len(eligible)==9 and all(int(r["fixed_allowed"])>0 for r in eligible)
    assert all(abs(float(r["fixed_score"])-int(r["fixed_contacts"])/int(r["fixed_allowed"]))<1e-8 for r in eligible)
    lines=(ROOT/"results"/"alpha3d_followup.fasta").read_text().splitlines()
    recs={}
    for line in lines:
        if line.startswith(">"):
            key=line.split()[0][1:];recs[key]=""
        else:
            recs[key]+=line
    assert len(recs)==4
    for c in (44,55):
        native=recs[f"alpha3D_A{c}C"]; control=recs[f"alpha3D_W4F_A{c}C"]
        assert len(native)==len(control)==73 and native.count("C")==1 and native[c-1]=="C"
        assert native[3]=="W" and control==native[:3]+"F"+native[4:]
    print("Checked pair counts, rankings, thresholds, grid nesting, geometry, torsions, alpha3D scores and four sequences.")

if __name__=="__main__":
    main()
