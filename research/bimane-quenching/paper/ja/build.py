"""Build the Japanese edition from the shared research tables."""
from pathlib import Path
import sys

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Mm, Pt

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from manuscript_layout import ROOT, RESULTS, data, reference, save_document, settings, table

def manuscript():
    doc=Document();settings(doc,language="ja",title="ビマンの静的消光を予測する二つの構造指標",subject="T4リゾチーム5組の再解析とα3Dへの適用")
    rows=data("calibration.csv");raw=data("geometry_sensitivity.csv")
    ranks={(r["outcome"],r["predictor"]):r for r in data("rank_metrics.csv")}
    candidates=sorted((r for r in data("alpha3d_sites.csv") if r["eligible"]=="True"),key=lambda v:float(v["ca_A"]))
    rmain=lambda k:float(ranks["digitized",k]["rho"])
    p=doc.add_paragraph
    h=lambda t:doc.add_heading(t,level=2)
    H=lambda t:doc.add_heading(t,level=1)
    cap=lambda t:p(t,style="Caption note")
    tc=lambda t:p(t,style="T caption")
    page=doc.add_page_break

    p("ビマンの静的消光を予測する二つの構造指標",style="Title")
    p("T4リゾチーム5組の再解析と人工タンパク質α3Dへの適用",style="Sub")
    p("公開データの二次解析・計算研究　　2026年11月25日",style="Meta")
    p("要旨",style="Front heading")
    p(f"トリプトファン（Trp）の近くに蛍光色素ビマンを置くと、光を吸収する時点で両者が接触している分子は蛍光を発しにくい。T4リゾチームの既報5組を用い、この静的消光の順位を、主鎖のCα原子間距離と、計算上許容された配置のうち両者が接触する割合で予測した。実験値とのSpearman順位相関は距離で{rmain('distance'):.2f}、配置で{rmain('geometry'):.2f}だった。配置モデルは最大の消光を示す組を捉えたが、約59%の静的消光を示す組で接触を一つも見いだせなかった。人工タンパク質α3Dでは、調べた表面のアラニン{len(candidates)}か所のうち55番でのみ接触配置が得られた。55番は実験候補に残るが、蛍光変化の大きさは未測定である。")
    p("背景と目的",style="Front heading")
    p("蛍光標識の位置を選ぶ際、主鎖の間隔は立体構造からすぐに測れる。一方、ビマンはシステイン（Cys）に可動な結合でつながり、Trpの側鎖にも複数の向きがある。同じような距離でも、色素がインドール環に届く向きは周囲の原子に制約される。本研究では、立体的に許される向きを数えることで、距離から得られる順位が改善するかを調べた。比較対象には、同一色素の強度と寿命を複数部位で測定した研究を用いた［1］。")
    im=p();im.alignment=WD_ALIGN_PARAGRAPH.CENTER;im.paragraph_format.space_after=Pt(0);im.paragraph_format.line_spacing=1.0
    im.add_run().add_picture(str(RESULTS/"ja"/"figure1.png"),width=Mm(165))
    im.paragraph_format.keep_with_next=True
    cap("図1　実験値と二つの予測順位。Aは原著図4Cから読み取った静的消光の割合と、原図に描かれた上側の誤差棒。Bは同じ行に対応する順位で、1が最大の消光を予測する。配置が同順位の2組は平均順位4.5とした。")

    page();H("材料と方法")
    h("実験値の取得")
    p("Jones BrunetteとFarrensの原著図4のTrp・ビマン系列から、5組の静的消光率（パネルC）と、対照に対する蛍光強度比（パネルA）を読み取った［1］。静的消光率は、強度Fと平均蛍光寿命τから1 − (F/F₀)(τ₀/τ)として原著者が推定した値である。添字0は同じ標識位置で消光残基をフェニルアラニン（Phe）にした対照を示す。強度比F₀/Fは、同じ位置の対照に比べて蛍光が何倍弱くなったかを表す。")
    p("原著PDFの第6ページから、幅1250、高さ1289ピクセルの原図を抽出した。縦軸の目盛と色分けされた棒の境界を読み、線形換算した。パネルCでは1ピクセルが約0.35ポイントに相当する。値は図からの概算であり、負の推定値もそのまま用いた。原著での強度比の測定回数は8.4 Åの組が3回、ほかの組が4回である。解析単位は部位ペア5組とした。")
    h("構造から作った二つの指標")
    p("距離指標には、原著の構造図と同じT4リゾチームの座標1L63を使用した［2］。各部位のCα原子間距離が短い組を上位とした。配置指標では同じ主鎖にTrpとビマン標識Cysの側鎖を置いた。Trpの環の形には2A3DのTrp4、標識の結合構造には9PHRのCys151と色素9UMのA配置を用いた［3,4］。いずれもA鎖を用い、水分子と水素原子は計算から除いた。")
    p("主解析ではTrp側鎖54通りとビマン標識側鎖1,944通りを組み合わせ、1組につき104,976通りを調べた。非結合原子の距離がファンデルワールス半径の和を0.30 Åを超えて下回る配置を除外した［5］。共有結合で1または2本しか隔たらない対は除外判定の対象外とし、3本隔たる対は追加で0.50 Åを許容した。ビマンの縮合環とTrpのインドール環の最近接重原子間距離が4.5 Å以下であれば接触とした。")
    p("配置指標は接触配置数を許容配置数で割った値とした。候補の角度を等重みで数え、分子のエネルギーや滞在時間による重み付けは行っていない。角度格子、原子名、衝突判定の再現条件を付録と解析コードに示す。")
    h("順位の評価と候補の選定")
    p("主評価項目は静的消光率とのSpearman順位相関ρとし、同順位には平均順位を与えた。参考値として5組の順序の全120通りから両側置換p値を計算した。感度分析ではゼロ付近の2組を同順位にする条件、1組ずつの除外、幾何条件の変更を調べた。α3Dの候補は第2・第3ヘリックスのアラニンから、Cβの溶媒露出表面積が20 Å²以上のものを選んだ［3,6］。")

    page();H("結果")
    h("5組の静的消光と構造指標")
    tc("表1　T4リゾチームで得られた実験値と主解析の配置数")
    tbl=[]
    for r in rows:
        tbl.append((r["pair"],f"{float(r['ca_A']):.2f}",f"{float(r['static_pct']):.1f}",f"{float(r['intensity_F0_over_F']):.1f}",f"{r['contacts']} / {r['allowed']}",f"{100*float(r['geom_score']):.1f}"))
    table(doc,("部位ペア","Cα間\nÅ","静的消光\n%","強度比\nF₀/F","接触数 /\n許容数","接触配置\n%"),tbl,(.21,.12,.16,.14,.21,.16))
    cap("WはTrp、Cはビマンを付けたCys。静的消光率と強度比は原著の図の読取値。接触配置の割合は計算値である。Cα間距離は1L63の座標から求めた。")
    p("最短のW116/C132では静的消光率が約81%で、両指標とも1位とした。対照的にW116/C128では実験値が約59%だったが、モデルに残った171配置はいずれも接触条件を満たさなかった。最近接の環間距離は7.09 Åだった。W116/C123の−1.4%は強度と寿命から計算した推定値で、上側の誤差棒は約23ポイントある。生じた分子の割合を負と解釈することはできない。")
    h("評価指標と探索条件への依存")
    tc("表2　実験値との順位相関")
    mrows=[]
    for key,label in (("digitized","静的消光率"),("near_zero_tied","ゼロ付近2組を同順位"),("intensity_ratio","蛍光強度比 F₀/F")):
        mrows.append((label,*[f"{float(ranks[key,k]['rho']):.2f}" for k in ("distance","geometry")]))
    loo=data("leave_one_out.csv")
    mrows.append(("部位ペアを1組ずつ除外",*[f"{min(float(r[k+'_rho']) for r in loo):.2f} ～ {max(float(r[k+'_rho']) for r in loo):.2f}" for k in ("distance","geometry")]))
    table(doc,("評価条件","距離の順位相関","配置の順位相関"),mrows,(.51,.245,.245))
    cap("ゼロ付近は静的消光率の絶対値が5ポイント未満の2組。強度比は静的消光と動的消光をともに含む。除外行は4組で計算した5回の範囲。")
    p(f"主解析の参考置換p値は距離で{float(ranks['digitized','distance']['exact_p']):.3f}、配置で{float(ranks['digitized','geometry']['exact_p']):.3f}だった。5組中4組がTrp116を共有するため、独立な標本としての推論には制約がある。これらは二つの相関の差を検定した値ではない。")
    dense=next(r for r in raw if r["pair"]=="W116/C128" and r["setting"]=="dense_linker")
    p(f"接触の閾値を4.0 Åにすると配置のρは0.71、5.0・5.5 Åでは0.82だった。3.5 Åでは全組がゼロになり、相関は定義できなかった。事後解析としてリンカーの二つの角度を細分したところ、W116/C128の許容配置は{int(dense['allowed']):,}通りに増えたが、接触は0通り、最短距離は{float(dense['min_ring_A']):.2f} Åだった。")

    page();H("人工タンパク質への適用と考察")
    h("α3Dの55番をどう位置付けるか")
    p("2A3Dの第2・第3ヘリックスにはアラニンが10か所あり、露出面積の条件を満たす9か所を計算した。ネイティブのTrp4の向きをNMR座標に固定した場合と、その側鎖を54通りに動かした場合を比較した。どちらの条件でも、接触配置が生じた候補はA55Cだけだった。")
    tc("表3　α3DでTrp4との主鎖間距離が短い候補3か所")
    ar=[]
    for r in candidates[:3]:
        ar.append((r["label"],f"{float(r['ca_A']):.2f}",f"{r['fixed_contacts']} / {r['fixed_allowed']}",f"{100*float(r['fixed_score']):.1f}",f"{r['sampled_contacts']} / {r['sampled_allowed']}",f"{100*float(r['sampled_score']):.1f}"))
    table(doc,("候補","Cα間\nÅ","Trp固定\n接触 / 許容","固定\n%","Trp可動\n接触 / 許容","可動\n%"),ar,(.15,.12,.23,.12,.25,.13))
    cap("残り6候補も両条件で接触は0通りだった。A60Cは露出面積の条件により評価対象外。全10か所の選定記録と全9候補の結果を付属データに収録した。")
    p("A55CのCα間距離11.45 Åは、T4リゾチームで調べた範囲（7.54～11.08 Å）をわずかに超える。Trp4を固定した場合の12.7%は、用いた角度格子で接触できた配置の割合である。この値から試料の静的消光率や折りたたみの進行割合を数値で推定することはできない。")
    h("接触配置を数える方法の限界")
    p("今回の5組では、主鎖間距離の順位が実験順位により近かった。配置モデルが見落としたW116/C128は、固定した骨格と限られた側鎖の向きだけでは、実際の接触を捉え損なう例である。隣接側鎖や主鎖の緩和、色素と周囲の相互作用、配向ごとのエネルギーの違いを、この計算から切り分けることはできない。接触が0回だった候補にも同じ制約が及ぶ。")
    p("T4リゾチーム1種類の限られた部位で得た順位を、別のタンパク質の蛍光強度へ一般化するには追加の実測が必要である。また、本研究で扱ったα3Dの座標は折りたたみ状態の1構造で、変性状態や折りたたみ途中の一時的な接触頻度は評価していない。")
    h("検証できる予測")
    p("A55Cと、主鎖間距離が次に短いA44Cを同じビマンで標識し、それぞれにTrp4をPheへ変えた対照を置く。標識率をそろえ、強度と寿命から静的消光成分を求めれば、A55Cのほうが大きいという予測を検証できる。変性に伴う蛍光変化を折りたたみと関連付ける段階では、遠紫外円二色性でヘリックス量の変化も並行して測る。")
    h("結論")
    p("T4リゾチームで見いだした例外を踏まえると、α3DではA55Cを優先して測り、A44Cを比較対象とするのが妥当である。この組合せなら、主鎖間距離の差が小さい2か所で、色素の向きに由来する予測を試せる。")

    page();H("再現条件と参考文献")
    h("計算の再現条件")
    p("距離の単位はÅとした。Trpのχ1と標識Cysのχ1には−60°、60°、180°の各中心から−15°、0°、15°ずらした9値を用いた。Trpのχ2には−110°、−90°、−70°、70°、90°、110°を用いた。標識のCA–CB–SG–C8とCB–SG–C8–C4は各3値（−60°、60°、180°）、SG–C8–C4–N1は−180°から165°まで15°刻みで走査した。原子名はPDB 9PHRの9UMに従った。")
    p("C、N、O、Sの半径は順に1.70、1.55、1.52、1.80 Åとした。原子同士の衝突は導入した側鎖と既存原子の間、二つの導入側鎖の間、および標識内の可動な非結合対で評価した。固定したネイティブTrpと周囲の既存原子の接触は実験構造の一部として保持した。許容配置が0通りの場合は欠測とし、接触割合を0で代用していない。")
    p("露出面積は水分子のプローブ半径1.4 Å、原子球面上の1,024点から求めた。第2・第3ヘリックスの探索区間は28～44番と53～70番とした。感度分析では衝突許容幅0.20・0.40 Åと色素の末端角度格子の7.5°移動も試した。0.20 Åでは2組の許容配置が消失した。事後の高密度探索では、二つのリンカー角の各中心に±20°を加え、1組944,784通りに拡張した。")
    h("データと研究の実施")
    p("公開された分光測定値を二次利用し、立体配置の計算と順位比較を新たに行った。原図の座標、参照構造、コード、計算結果、実行手順を同一プロジェクトに収録した。画像読取と計算の整合性は検証スクリプトで確認した。データ整理、解析コード、作図および原稿作成にはCodexを使用した。α3D標識体の実験測定は今後の検証課題である。")
    h("参考文献")
    reference(doc,1,"Jones Brunette AM, Farrens DL. Distance mapping in proteins using fluorescence spectroscopy: tyrosine, like tryptophan, quenches bimane fluorescence in a distance-dependent manner. Biochemistry. 2014, 53, 6290–6301.","doi 10.1021/bi500493r","https://doi.org/10.1021/bi500493r")
    reference(doc,2,"Protein Data Bank. T4 lysozyme, chain A. X-ray diffraction, 1.75 Å.","PDB 1L63","https://www.rcsb.org/structure/1L63")
    reference(doc,3,"Walsh STR et al. Solution structure and dynamics of a de novo designed three-helix bundle protein. Proc Natl Acad Sci USA. 1999, 96, 5486–5491.","PDB 2A3D","https://www.rcsb.org/structure/2A3D")
    reference(doc,4,"Protein Data Bank. BTB modified at C151 with monobimane. Covalent dye geometry.","PDB 9PHR","https://www.rcsb.org/structure/9PHR")
    reference(doc,5,"Bondi A. van der Waals volumes and radii. J Phys Chem. 1964, 68, 441–451.","doi 10.1021/j100785a001","https://doi.org/10.1021/j100785a001")
    reference(doc,6,"Shrake A, Rupley JA. Environment and exposure to solvent of protein atoms. Lysozyme and insulin. J Mol Biol. 1973, 79, 351–371.","doi 10.1016/0022-2836(73)90011-9","https://doi.org/10.1016/0022-2836(73)90011-9")
    save_document(doc, ROOT/"paper"/"ja"/"bimane-static-quenching.ja.docx")

if __name__=="__main__":
    manuscript()
