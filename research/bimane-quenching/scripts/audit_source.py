"""Verify annotated pixels against the exact source PDF without storing a reprint."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from urllib.request import urlopen
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf",type=Path,help="locally saved publisher PDF (PMC copy)")
    args=parser.parse_args()
    if not shutil.which("pdfimages"):
        raise SystemExit("Poppler pdfimages is required for checking the original figure.")
    meta=json.loads((ROOT/"data"/"sources.json").read_text())["reference_pdfs"][0]
    with tempfile.TemporaryDirectory() as tmp:
        work=Path(tmp)
        pdf=args.pdf
        if pdf is None:
            pdf=work/"source.pdf"
            with urlopen(meta["url"],timeout=35) as src:
                pdf.write_bytes(src.read())
        assert hashlib.sha256(pdf.read_bytes()).hexdigest()==meta["sha256"],"Unexpected PDF revision"
        subprocess.run(["pdfimages","-f","6","-l","6","-png",str(pdf),str(work/"fig")],check=True)
        pixels=np.asarray(Image.open(work/"fig-000.png").convert("RGB")).astype(int)
        assert pixels.shape==(1289,1250,3)
        def dark_line(x,y):
            x,y=int(x),round(y)
            # Seek a dark horizontal border or cap in a 3-row interval, away from the center stem.
            block=pixels[y-1:y+2,[x-3,x-2,x+2,x+3],:]
            return (block.max(axis=2)<165).sum(axis=1).max()>=3
        crows=list(csv.DictReader((ROOT/"data/experimental/figure4c_pixels.csv").open()))
        arows=list(csv.DictReader((ROOT/"data/experimental/figure4a_pixels.csv").open()))
        for crow,arow in zip(crows,arows,strict=True):
            x=int(crow["x_center_px"])
            assert crow["pair"]==arow["pair"]
            for key in ("static_edge_y_px","upper_cap_y_px"):
                assert dark_line(x,float(crow[key])),(crow["pair"],key)
            # The mid-body pixels of the static segment carry the magenta fill.
            y0=float(crow["source_zero_y_px"])
            y=float(crow["static_edge_y_px"])
            sample=pixels[round((y0+y)/2),x-4]
            assert sample[0]-sample[1]>20 and sample[2]-sample[1]>12,(crow["pair"],sample)
            for key in ("source_zero_y_px","source_100_y_px"):
                assert dark_line(220,float(crow[key])),key
            for key in ("zero_y_px","ratio30_y_px"):
                assert dark_line(220,float(arow[key])),key
            # The top edge of the panel-A blue fill must have white space just above it.
            ay=int(float(arow["bar_y_px"]))
            if_blue=lambda px: px[2]-px[0]>25 and px[1]-px[0]>9
            assert if_blue(pixels[ay+2,x-5]) and not if_blue(pixels[ay-3,x-5])
    print("Verified native image dimensions, axes, five static edges and error caps, five intensity bars.")

if __name__=="__main__":
    main()
