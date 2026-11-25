"""Build the English manuscript using the archived numerical results."""
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Mm, Pt

from manuscript_layout import ROOT, RESULTS, data, reference, save_document, settings, table

TITLE = "Predicting static quenching of bimane by tryptophan"
SUBTITLE = "Five site pairs in T4 lysozyme and a labeling-site prediction for α3D"

def manuscript():
    doc = Document()
    settings(doc, language="en", title=TITLE, subject=SUBTITLE)
    measured = data("calibration.csv")
    metrics = {(r["outcome"], r["predictor"]): r for r in data("rank_metrics.csv")}
    settings_rows = data("geometry_sensitivity.csv")
    sensitivity = {r["setting"]: r for r in data("sensitivity_ranks.csv")}
    loo = data("leave_one_out.csv")
    sites = sorted((r for r in data("alpha3d_sites.csv") if r["eligible"] == "True"),
                   key=lambda r: float(r["ca_A"]))
    a55 = next(r for r in sites if r["label"] == "A55C")
    missed = next(r for r in measured if r["pair"] == "W116/C128")
    missed_primary = next(r for r in settings_rows if r["pair"] == missed["pair"] and r["setting"] == "primary")
    missed_dense = next(r for r in settings_rows if r["pair"] == missed["pair"] and r["setting"] == "dense_linker")
    distance = metrics["digitized", "distance"]
    geometry = metrics["digitized", "geometry"]

    p = doc.add_paragraph
    def heading(text):
        doc.add_heading(text, level=2)
    def next_section(text):
        doc.add_page_break()
        doc.add_heading(text, level=1)
    def caption(text):
        p(text, style="Caption note")

    p("Predicting static quenching\nof bimane by tryptophan", style="Title")
    p(SUBTITLE, style="Sub")
    p("Secondary analysis of published fluorescence measurements  ·  25 November 2026", style="Meta")
    p("Abstract", style="Front heading")
    p("Can a folded protein structure identify where a bimane label will be quenched most strongly by a nearby "
      "tryptophan? We compared two ways to rank five previously measured site pairs in T4 lysozyme. One used the "
      "distance between the backbone Cα atoms. The other counted sterically allowed conformations in which the dye "
      f"and indole rings came into contact. Spearman correlations with the estimated static-quenching fraction were "
      f"{float(distance['rho']):.2f} for distance and {float(geometry['rho']):.2f} for the contact score. Both ranked the "
      f"most strongly quenched pair first. The contact model missed a pair with an estimated static fraction of "
      f"{float(missed['static_pct']):.1f}%. When applied to the designed three-helix bundle α3D, the model found "
      f"contacts at A55C alone among {len(sites)} exposed alanine sites. A55C and A44C provide a pair of sites "
      "for an experimental comparison in α3D.")
    p("Rationale", style="Front heading")
    p("A bimane attached to cysteine can form a dark complex with a nearby tryptophan (Trp) before excitation. "
      "Backbone distance is easy to measure. The dye linker, the Trp side chain and neighboring atoms determine "
      "whether the two rings can touch. We asked whether explicitly sampling their orientations improves the ordering "
      "of labeling sites obtained from distance alone. Published intensity and lifetime measurements provided an "
      "experimental estimate of static quenching for each pair [1].")
    figure = p()
    figure.alignment = WD_ALIGN_PARAGRAPH.CENTER
    figure.paragraph_format.space_after = Pt(0)
    figure.paragraph_format.line_spacing = 1.0
    figure.paragraph_format.keep_with_next = True
    figure.add_run().add_picture(str(RESULTS / "figure1.png"), width=Mm(164))
    caption("Figure 1. Static quenching and site ranks. A shows the point estimates and upper error bars digitized "
            "from the Trp series in Figure 4C of reference [1]. B gives ranks in the same row order. Rank 1 denotes "
            "the highest measured or predicted quenching. The two zero contact scores share rank 4.5.")

    next_section("Materials and methods")
    heading("Experimental endpoints")
    p("We digitized the Trp–bimane series in Figure 4 of Jones Brunette and Farrens [1]. The primary endpoint was "
      "the static-quenching fraction in panel C. The original authors estimated it as 1 − (F/F₀)(τ₀/τ), where F "
      "and τ are the emission intensity and mean fluorescence lifetime of the Trp sample. Subscript 0 denotes the "
      "matched phenylalanine control carrying bimane at the same site. The secondary endpoint, the intensity ratio "
      "F₀/F in panel A, includes both static and dynamic quenching.")
    p("We extracted the 1,250 × 1,289-pixel image from page 6 of the published PDF. We recorded the axis ticks, bar "
      "edges and upper error-bar caps, then converted pixel coordinates to values by linear interpolation. One pixel "
      "in panel C represents approximately 0.35 percentage points. We retained the slightly negative point estimate "
      "reported for one pair. The original intensity ratios used three measurements for the 8.4 Å pair and four "
      "for each other pair. We treated each of the five site pairs as one observation.")
    heading("Backbone distance and contact score")
    p("We measured Cα distances in chain A of the T4 lysozyme structure used in the original study (PDB 1L63) [2]. "
      "Shorter distances ranked higher. On the same backbone, we modeled a Trp side chain at the quenching site and "
      "a bimane-bearing cysteine at the labeling site. Trp4 of α3D supplied the indole geometry (PDB 2A3D) [3]. "
      "The covalent dye geometry came from Cys151 and ligand 9UM, alternate location A, in PDB 9PHR [4]. We used "
      "chain A of the first coordinate model and omitted water molecules and hydrogen atoms.")
    p("For each site pair we enumerated 54 Trp conformations and 1,944 labeled-cysteine conformations, yielding "
      "104,976 joint poses. We screened for heavy-atom clashes using van der Waals radii [5]. A pose counted as a "
      "contact if the closest pair of heavy atoms on the bimane and indole rings lay within 4.5 Å. The contact score "
      "is the number of contact poses divided by the number of allowed poses. Every sampled pose received equal "
      "weight. The computational details on page 5 specify the torsions, radii and bonded-neighbor exceptions.")
    heading("Statistical comparison and transfer to α3D")
    p("We used Spearman rank correlation (ρ) with average ranks for ties. Reference two-sided permutation p values "
      "used all 120 orderings of the five observations. Sensitivity analyses varied the geometric thresholds, tied "
      "the two near-zero experimental estimates and omitted one pair at a time. For α3D we considered alanines in "
      "helices 2 and 3 with at least 20 Å² of solvent-accessible area on the native Cβ atom [3,6]. We evaluated both "
      "the deposited Trp4 orientation and a sampled Trp4 side chain.")

    next_section("Results")
    heading("Experimental estimates and geometric predictions")
    p("Table 1. Measured quenching and modeled contacts in T4 lysozyme", style="T caption")
    rows = []
    for r in measured:
        rows.append((r["pair"], f"{float(r['ca_A']):.2f}", f"{float(r['static_pct']):.1f}",
                     f"{float(r['intensity_F0_over_F']):.1f}", f"{r['contacts']} / {r['allowed']}",
                     f"{100*float(r['geom_score']):.1f}"))
    table(doc, ("Site pair", "Cα distance\n(Å)", "Static\n(%)", "Intensity\nF₀/F", "Contacts /\nallowed", "Contact\nscore (%)"),
          rows, (.20,.17,.12,.15,.20,.16))
    caption("W designates the Trp site and C the bimane-labeled Cys site. Static fractions and intensity ratios "
            "were digitized from the original figure. Cα distances were calculated from the 1L63 coordinates.")
    p(f"W116/C132 was both the closest pair and the pair with the highest estimated static quenching "
      f"({float(measured[0]['static_pct']):.1f}%). At W116/C128 the experiment indicated substantial quenching, "
      f"but the model found {missed['contacts']} contacts among {missed['allowed']} allowed poses. The closest "
      f"ring atoms were {float(missed_primary['min_ring_A']):.2f} Å apart. For W116/C123 the estimated static "
      "fraction was −1.4%, with an upper error bar of approximately 23 percentage points. This negative estimate "
      "is compatible with measurement uncertainty near zero.")
    p("Table 2. Rank correlations with the experimental endpoints", style="T caption")
    rows = []
    for key, name in (("digitized","Static fraction"), ("near_zero_tied","Two near-zero static fractions tied"),
                      ("intensity_ratio","Steady-state intensity ratio F₀/F")):
        rows.append((name, *[f"{float(metrics[key,k]['rho']):.2f}" for k in ("distance","geometry")]))
    rows.append(("One site pair omitted (range)", *[
        f"{min(float(r[k+'_rho']) for r in loo):.2f}–{max(float(r[k+'_rho']) for r in loo):.2f}"
        for k in ("distance","geometry")]))
    table(doc, ("Endpoint or sensitivity analysis","Distance ρ","Contact score ρ"), rows, (.54,.21,.25))
    caption("The near-zero tie includes absolute estimates below 5 percentage points. The last row gives the range "
            "across the five four-pair subsets.")
    p(f"For the primary endpoint, the permutation p values were {float(distance['exact_p']):.3f} for distance and "
      f"{float(geometry['exact_p']):.3f} for the contact score. Four pairs share Trp116. These p values describe "
      "each ordering separately, and the shared site limits inference across independent systems.")
    p(f"At a 4.0 Å contact cutoff, the contact-score correlation was {float(sensitivity['contact_4.0']['geometry_rho']):.2f}. "
      "At 5.0 and 5.5 Å it was 0.82. A 3.5 Å cutoff gave five zero scores and an undefined correlation. A post hoc "
      f"denser linker grid produced {int(missed_dense['allowed']):,} allowed W116/C128 poses, {missed_dense['contacts']} "
      f"contacts and a closest ring distance of {float(missed_dense['min_ring_A']):.2f} Å.")

    next_section("Application to α3D and interpretation")
    heading("Two sites for an experimental comparison")
    p("Helices 2 and 3 contained ten alanines. Nine passed the Cβ exposure criterion. A55C was the only site with "
      "any modeled contact with Trp4, both when its side chain was held in the NMR orientation and when its torsions "
      "were sampled. The next closest site by backbone distance was A44C.")
    p("Table 3. The three eligible α3D sites closest to Trp4 by Cα distance", style="T caption")
    rows = []
    for r in sites[:3]:
        rows.append((r["label"], f"{float(r['ca_A']):.2f}", f"{r['fixed_contacts']} / {r['fixed_allowed']}",
                     f"{100*float(r['fixed_score']):.1f}", f"{r['sampled_contacts']} / {r['sampled_allowed']}",
                     f"{100*float(r['sampled_score']):.1f}"))
    table(doc, ("Site","Cα distance\n(Å)","Fixed Trp4\ncontact / allowed","Fixed\n(%)",
                "Sampled Trp4\ncontact / allowed","Sampled\n(%)"), rows,(.12,.16,.23,.11,.25,.13))
    caption("The six other eligible sites had zero contacts in both treatments. A60C fell below the solvent-exposure "
            "threshold. The companion data include all ten sites and their selection records.")
    p(f"The A55C backbone separation of {float(a55['ca_A']):.2f} Å is just beyond the T4 calibration range of "
      "7.54–11.08 Å. Its 12.7% score with fixed Trp4 denotes the fraction of sampled, allowed poses that met the "
      "contact cutoff. Relating this score to a molecular population or fluorescence signal would require an "
      "experimental calibration.")
    heading("What the missed contact implies")
    p("The simple distance ranking agreed more closely with these five static-quenching estimates. W116/C128 shows "
      "how a site can exhibit appreciable static quenching while producing no contacts in a fixed-backbone search. "
      "We varied the linker angles, but the surrounding side chains and backbone retained their input coordinates. "
      "Local relaxation, dye–protein interactions and unequal conformational energies could each contribute. The "
      "five measurements cannot distinguish these explanations.")
    p("The calibration covers one protein and four of its five pairs share a quencher site. The α3D calculations "
      "also use a single folded structure. Transient contacts in partially folded or unfolded molecules and changes "
      "in stability caused by labeling remain open questions.")
    heading("Testable prediction")
    p("The model predicts greater Trp4-dependent static quenching for bimane-labeled A55C than for A44C. A direct "
      "test would compare each variant with its own W4F control at matched labeling fractions and measure both "
      "steady-state intensity and fluorescence lifetime. Far-UV circular dichroism during denaturation could track "
      "changes in helical content alongside fluorescence. The α3D variants and their fluorescence responses remain "
      "experimentally untested.")

    next_section("Computational details and references")
    heading("Sampling and steric rules")
    p("For each of Trp χ1 and Cys χ1, we used −60°, 60° and 180°, each with offsets of −15°, 0° and 15°. Trp χ2 "
      "used ±70°, ±90° and ±110°. The dye torsions CA–CB–SG–C8 and CB–SG–C8–C4 each used −60°, 60° and 180°. "
      "SG–C8–C4–N1 was sampled from −180° to 165° in 15° steps. Dye atom names follow PDB component 9UM. The "
      "contact calculation used its C1–C6, N1 and N2 ring atoms and the nine indole ring heavy atoms of Trp.")
    p("The C, N, O and S radii were 1.70, 1.55, 1.52 and 1.80 Å. We allowed up to 0.30 Å of overlap between "
      "nonbonded van der Waals surfaces, excluded atoms one or two bonds apart from clash testing and allowed another "
      "0.50 Å for atoms three bonds apart. We screened modeled side chains against the scaffold and each other, plus "
      "mobile nonbonded pairs within the dye. Unchanged native Trp contacts were retained in the fixed-Trp4 analysis. "
      "A site with no allowed poses has an undefined score.")
    p("Solvent accessibility was evaluated with a 1.4 Å probe and 1,024 trial points per atom sphere. The selected "
      "helix spans were residues 28–44 and 53–70 of 2A3D. Sensitivity runs used overlap allowances of 0.20 and "
      "0.40 Å and a 7.5° shift of the terminal dye grid. At 0.20 Å, two T4 pairs had no allowed poses. The denser "
      "linker grid added offsets of ±20° to both linker torsions, giving 944,784 poses per pair.")
    heading("Data and research contributions")
    p("The study repository contains the source-figure coordinates, input structures, analysis code, rendering "
      "scripts, numerical results and proposed α3D sequences. Source hashes and automated checks support reproduction. "
      "Codex was used to prepare the data, code, figure and manuscript. The original spectroscopy was performed by "
      "Jones Brunette and Farrens [1].")
    heading("References")
    reference(doc,1,"Jones Brunette AM, Farrens DL. Distance mapping in proteins using fluorescence spectroscopy: tyrosine, like tryptophan, quenches bimane fluorescence in a distance-dependent manner. Biochemistry. 2014, 53, 6290–6301.","doi 10.1021/bi500493r","https://doi.org/10.1021/bi500493r")
    reference(doc,2,"Protein Data Bank. T4 lysozyme, chain A. X-ray diffraction, 1.75 Å.","PDB 1L63","https://www.rcsb.org/structure/1L63")
    reference(doc,3,"Walsh STR et al. Solution structure and dynamics of a de novo designed three-helix bundle protein. Proc Natl Acad Sci USA. 1999, 96, 5486–5491.","PDB 2A3D","https://www.rcsb.org/structure/2A3D")
    reference(doc,4,"Protein Data Bank. BTB modified at C151 with monobimane. Covalent dye geometry.","PDB 9PHR","https://www.rcsb.org/structure/9PHR")
    reference(doc,5,"Bondi A. van der Waals volumes and radii. J Phys Chem. 1964, 68, 441–451.","doi 10.1021/j100785a001","https://doi.org/10.1021/j100785a001")
    reference(doc,6,"Shrake A, Rupley JA. Environment and exposure to solvent of protein atoms. Lysozyme and insulin. J Mol Biol. 1973, 79, 351–371.","doi 10.1016/0022-2836(73)90011-9","https://doi.org/10.1016/0022-2836(73)90011-9")
    save_document(doc, ROOT / "paper" / "bimane-static-quenching.docx")

if __name__ == "__main__":
    manuscript()
