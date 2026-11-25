"""Reproduce five-site comparisons and blinded-to-outcome applications to alpha3D."""
import csv
import hashlib
import itertools
import json
from pathlib import Path
from textwrap import wrap
import numpy as np
from scipy.stats import rankdata
from geometry import (INDOLE, THIOETHER, c_beta_sasa, dye_conformers, dye_reference, joint_clearance,
                      points, read_chain, tryptophans)

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"results"
ANCHORS=("N","CA","CB")
PRIMARY="primary"
# One factor is changed at a time. Units are Å except shift, in degrees.
SETTINGS=[(PRIMARY,4.5,0.30,0.0),
          ("contact_3.5",3.5,0.30,0.0),("contact_4.0",4.0,0.30,0.0),
          ("contact_5.0",5.0,0.30,0.0),("contact_5.5",5.5,0.30,0.0),
          ("overlap_0.20",4.5,0.20,0.0),("overlap_0.40",4.5,0.40,0.0),
          ("grid_shift_7.5",4.5,0.30,7.5)]

def read_csv(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))

def write_csv(path, rows):
    with path.open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key:round(float(v),8) if isinstance(v,(float,np.floating)) else v for key,v in row.items()})

def observations():
    directory=ROOT/"data"/"experimental"
    rows=read_csv(directory/"figure4c_pixels.csv")
    totals={row["pair"]:row for row in read_csv(directory/"figure4a_pixels.csv")}
    output=[]
    for row in rows:
        base=float(row["source_zero_y_px"])
        scale=100/(base-float(row["source_100_y_px"]))
        edge=float(row["static_edge_y_px"])
        total=totals[row["pair"]]
        ratio=(float(total["zero_y_px"])-float(total["bar_y_px"]))*30/(float(total["zero_y_px"])-float(total["ratio30_y_px"]))
        output.append(dict(pair=row["pair"],trp=int(row["trp_site"]),label=int(row["label_site"]),
                           reported_ca_A=float(row["pub_ca_A"]),static_pct=(base-edge)*scale,
                           plotted_upper_error_pp=(edge-float(row["upper_cap_y_px"]))*scale,
                           intensity_F0_over_F=ratio))
    return output

def settings_for(atoms, w, c, w_reference, dye, settings, native=False, thioether=THIOETHER):
    wa=points(atoms,w,ANCHORS)
    ca=points(atoms,c,ANCHORS)
    fixed=points(atoms,w,INDOLE) if native else None
    wposes=tryptophans(w_reference,wa,fixed)
    result=[]
    for shift in sorted({s[3] for s in settings}):
        dposes=dye_conformers(dye,ca,shift,thioether)
        clearance,ring_dist=joint_clearance(atoms,w,c,wposes,dposes,dye,fixed_native_trp=native)
        for name,cutoff,tolerance,grid in settings:
            if grid!=shift:
                continue
            eligible=clearance>=-tolerance
            n=int(eligible.sum())
            contacts=int(np.count_nonzero(ring_dist[eligible]<=cutoff))
            result.append(dict(setting=name,cutoff_A=cutoff,overlap_A=tolerance,shift_deg=grid,
                               tried=len(wposes)*len(dposes),allowed=n,contacts=contacts,
                               score=contacts/n if n else None,
                               min_ring_A=float(ring_dist[eligible].min()) if n else None))
    return result

def rho(x,y):
    xr,yr=rankdata(x),rankdata(y)
    if np.ptp(xr)==0 or np.ptp(yr)==0:
        return None
    return float(np.corrcoef(xr,yr)[0,1])

def summarize(x,y):
    value=rho(x,y)
    if value is None:
        return {"rho":None,"exact_p":None}
    perms=[rho(x,z) for z in itertools.permutations(y)]
    p=sum(abs(v)>=abs(value)-1e-10 for v in perms)/len(perms)
    return {"rho":round(value,6),"exact_p":round(p,6)}

def main():
    OUT.mkdir(exist_ok=True)
    base=ROOT/"data"/"structures"
    # Verify that coordinates and numeric source annotations have not changed.
    for entry in json.loads((ROOT/"data"/"sources.json").read_text())["bundled_inputs"]:
        assert hashlib.sha256((ROOT/entry["path"]).read_bytes()).hexdigest()==entry["sha256"],entry["path"]
    t4=read_chain(base/"1L63.pdb")
    alpha=read_chain(base/"2A3D.pdb")
    dye=dye_reference(read_chain(base/"9PHR.pdb",ligand=True))
    ref=(points(alpha,4,ANCHORS),points(alpha,4,INDOLE))
    obs=observations()
    settings_results=[]
    for row in obs:
        w,c=row["trp"],row["label"]
        ca_dist=float(np.linalg.norm(t4[w,"CA"].xyz-t4[c,"CA"].xyz))
        assert abs(ca_dist-row["reported_ca_A"])<0.12
        all_settings=settings_for(t4,w,c,ref,dye,SETTINGS)
        # Post-hoc sensitivity applied to every reference pair, retaining the
        # original rotamers and adding offsets to each of the two linker torsions.
        dense_angles=tuple(ch+offset for ch in THIOETHER for offset in (-20,0,20))
        all_settings+=settings_for(t4,w,c,ref,dye,[("dense_linker",4.5,0.30,0.0)],thioether=dense_angles)
        for s in all_settings:
            settings_results.append({"pair":row["pair"],**s})
        primary=next(v for v in all_settings if v["setting"]==PRIMARY)
        if primary["score"] is None:
            raise ValueError(f'No valid primary conformer for {row["pair"]}')
        row.update(ca_A=ca_dist,allowed=primary["allowed"],contacts=primary["contacts"],geom_score=primary["score"])
    target=np.array([r["static_pct"] for r in obs])
    ca_scores=np.array([-r["ca_A"] for r in obs])
    geom_scores=np.array([r["geom_score"] for r in obs])
    for field,values in (("static_rank",target),("distance_rank",ca_scores),("geometry_rank",geom_scores)):
        ranks=rankdata(-values)
        for row,rank in zip(obs,ranks):
            row[field]=rank
    write_csv(OUT/"calibration.csv",obs)
    write_csv(OUT/"geometry_sensitivity.csv",settings_results)
    metrics=[]
    for label,measured in (("digitized",target),("near_zero_tied",np.where(abs(target)<5,0,target)),
                           ("intensity_ratio",np.array([q["intensity_F0_over_F"] for q in obs]))):
        for key,values in (("distance",ca_scores),("geometry",geom_scores)):
            metrics.append({"outcome":label,"predictor":key,**summarize(values,measured)})
    write_csv(OUT/"rank_metrics.csv",metrics)
    sens=[]
    for name,cutoff,tolerance,shift in SETTINGS+[("dense_linker",4.5,0.30,0.0)]:
        scores=[next(q["score"] for q in settings_results if q["pair"]==row["pair"] and q["setting"]==name) for row in obs]
        sens.append({"setting":name,"geometry_rho":rho(scores,target) if None not in scores else None,
                     "distance_rho":rho(ca_scores,target),"valid_pairs":sum(s is not None for s in scores)})
    write_csv(OUT/"sensitivity_ranks.csv",sens)
    delete=[]
    for i,row in enumerate(obs):
        keep=np.arange(len(obs))!=i
        delete.append({"omitted":row["pair"],"distance_rho":rho(ca_scores[keep],target[keep]),
                       "geometry_rho":rho(geom_scores[keep],target[keep])})
    write_csv(OUT/"leave_one_out.csv",delete)

    # Same starting amino acid and different helices from Trp4. Eligibility is
    # decided by native Ala exposure, never by a contact score.
    candidates=[]
    for c in list(range(28,45))+list(range(53,71)):
        if alpha[c,"CA"].aa!="ALA":
            continue
        area=c_beta_sasa(alpha,c)
        record=dict(label=f"A{c}C",site=c,cb_sasa_A2=area,eligible=area>=20,
                    ca_A=float(np.linalg.norm(alpha[4,"CA"].xyz-alpha[c,"CA"].xyz)),
                    fixed_allowed=None,fixed_contacts=None,fixed_score=None,fixed_min_ring_A=None,
                    sampled_allowed=None,sampled_contacts=None,sampled_score=None)
        if record["eligible"]:
            for mode,native in (("fixed",True),("sampled",False)):
                s=settings_for(alpha,4,c,ref,dye,[SETTINGS[0]],native=native)[0]
                record.update({f"{mode}_allowed":s["allowed"],f"{mode}_contacts":s["contacts"],f"{mode}_score":s["score"]})
                if native:
                    record["fixed_min_ring_A"]=s["min_ring_A"]
        candidates.append(record)
    write_csv(OUT/"alpha3d_sites.csv",candidates)
    alphabet=dict(zip("ALA CYS ASP GLU PHE GLY HIS ILE LYS LEU MET ASN PRO GLN ARG SER THR VAL TRP TYR".split(),
                      "ACDEFGHIKLMNPQRSTVWY"))
    parent=[alphabet[alpha[i,"CA"].aa] for i in range(1,74)]
    fasta=[]
    for c in (55,44):
        assert parent[c-1]=="A" and parent[3]=="W" and "C" not in parent
        for has_trp in (True,False):
            sequence=parent.copy()
            sequence[c-1]="C"
            sequence[3]="W" if has_trp else "F"
            mutations=f"A{c}C" if has_trp else f"W4F_A{c}C"
            fasta.append(f">alpha3D_{mutations} | 2A3D numbering | untested | bimane attachment Cys{c}")
            fasta.extend(wrap("".join(sequence),60))
    (OUT/"alpha3d_followup.fasta").write_text("\n".join(fasta)+"\n")
    return obs, metrics, candidates

if __name__=="__main__":
    rows, metrics, sites=main()
    print("T4 sites",len(rows),"eligible alpha3D sites",sum(r["eligible"] for r in sites))
    for metric in metrics[:2]:
        print(metric)
