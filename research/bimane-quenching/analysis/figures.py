"""Publication figure from the two measured and predicted ranking tables."""
import argparse
import csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch
import numpy as np

OUT=Path(__file__).resolve().parents[1]/"results"
def main(language="en"):
    with (OUT/"calibration.csv").open() as f:
        rows=list(csv.DictReader(f))
    japanese = language == "ja"
    directory = OUT/"ja" if japanese else OUT
    directory.mkdir(exist_ok=True)
    font = "DejaVu Sans"
    if japanese:
        available = {f.name for f in font_manager.fontManager.ttflist}
        font = next((f for f in ("Hiragino Sans", "Noto Sans CJK JP", "Noto Sans JP",
                                 "IPAexGothic", "Yu Gothic", "Meiryo") if f in available), None)
        if font is None:
            raise SystemExit("Install a Japanese font such as Noto Sans CJK JP to redraw the Japanese figure.")
    plt.rcParams.update({"font.family":font,"font.size":10,
                         "axes.unicode_minus":False,"pdf.fonttype":42,"savefig.facecolor":"white"})
    fig,(left,right)=plt.subplots(1,2,figsize=(7.30,2.65),gridspec_kw={"width_ratios":[1.62,1]})
    fig.subplots_adjust(left=0.145,right=0.99,top=0.81,bottom=0.22,wspace=0.18)
    measured=np.array([float(r["static_pct"]) for r in rows])
    upper=np.array([float(r["plotted_upper_error_pp"]) for r in rows])
    y=np.arange(len(rows))
    ink="#1e3442"; muted="#526976"
    left.set_title("A   "+("実験から推定した静的消光" if japanese else "Static quenching estimate"),loc='left',
                   fontsize=11,fontweight='semibold',color=ink,pad=12)
    left.set_axisbelow(True)
    left.grid(axis="x",color="#d5dfe2",linewidth=.55)
    left.axvline(0,color="#8c9aa3",lw=.85)
    for i in y:
        left.plot([measured[i],measured[i]+upper[i]],[i,i],lw=1.4,color=muted)
        left.plot([measured[i]+upper[i]]*2,[i-.105,i+.105],lw=1.2,color=muted)
    left.scatter(measured,y,s=29,color="#176d69",edgecolor="white",linewidth=.6,zorder=3)
    left.set_xlim(-10,103); left.set_ylim(4.5,-.5)
    left.set_xticks([0,25,50,75,100])
    left.set_xlabel("静的消光の割合（%）" if japanese else "Static quenching (%)",fontsize=10)
    left.set_yticks(y,[r["pair"] for r in rows])
    left.tick_params(axis='both',labelsize=9,length=0,pad=4,labelcolor=ink)
    for side in ("top","left","right"): left.spines[side].set_visible(False)
    left.spines['bottom'].set_color("#aebfc3")
    right.set_title("B   "+("5組の順位" if japanese else "Ranks of the five pairs"),loc='left',
                    fontsize=11,fontweight='semibold',color=ink,pad=12)
    right.set_xlim(-.53,2.53);right.set_ylim(4.5,-.5)
    color=matplotlib.colors.LinearSegmentedColormap.from_list("rank",["#dcece8","#f7f9f9"])
    for i,row in enumerate(rows):
        for j,k in enumerate(("static_rank","distance_rank","geometry_rank")):
            rank=float(row[k])
            rect=FancyBboxPatch((j-.45,i-.42),.9,.84,boxstyle='round,pad=0.00,rounding_size=0.08',
                                transform=right.transData,facecolor=color((rank-1)/4),linewidth=0)
            right.add_patch(rect)
            right.text(j,i,f"{rank:g}",ha="center",va="center",color=ink,fontsize=10.5)
    right.set_xticks(range(3),["実測","距離","配置"] if japanese else ["Expt.","Distance","Poses"])
    right.tick_params(length=0,pad=5,labelsize=9)
    right.set_yticks([])
    for spine in right.spines.values():spine.set_visible(False)
    fig.savefig(directory/"figure1.png",dpi=320)
    fig.savefig(directory/"figure1.pdf",metadata={"Title":"Static quenching and site ranks","CreationDate":None,"ModDate":None})
    plt.close(fig)

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--language", choices=("en","ja"), default="en")
    main(parser.parse_args().language)
