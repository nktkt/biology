# ビマンの静的消光を予測する二つの構造指標

T4リゾチーム5組の公開分光データを再解析し、色素を付ける位置を二つの方法で順位付けした計算研究。人工タンパク質α3Dについては、表面のアラニン9か所を比較した。2026年11月25日作成。

[English study page](README.md) · [英語論文（PDF）](paper/bimane-static-quenching.pdf) · [日本語論文（PDF）](paper/ja/bimane-static-quenching.ja.pdf) · [日本語の編集用原稿（Word）](paper/ja/bimane-static-quenching.ja.docx) · [日本語の図](results/ja/figure1.png)

## 結果

- T4リゾチーム5組で、原著の静的消光率とのSpearman順位相関は、主鎖間距離で **0.90**、接触できる配置の割合で **0.82** だった。W116/C128では約58.5%の静的消光が報告図から読み取れたが、主解析の許容配置171通りの接触数は0だった。
- α3DでTrp4の向きをNMR構造に固定すると、A55Cで許容配置260通りのうち33通りが接触した。側鎖の向きを変えた条件では556通り中90通りだった。選定条件を満たした他の8か所では、どちらの条件も接触数は0だった。
- これらの配置数は角度格子と衝突判定に依存する。α3Dで実際の蛍光強度・静的消光率・折りたたみ状態の識別性能を測定する段階は未実施である。

## 研究資料

| ファイル | 内容 |
| --- | --- |
| [原図の読み取り位置](data/experimental/figure4c_pixels.csv)・[強度比の読み取り位置](data/experimental/figure4a_pixels.csv) | 原著図4のTrp系列。静的消光はパネルC、蛍光強度比はパネルA |
| [出典とハッシュ値](data/sources.json) | PDB、論文、補足資料の取得先と検証用SHA-256 |
| [実験値と予測](results/calibration.csv) | 部位、Cα間距離、推定消光率、配置数、順位 |
| [順位相関](results/rank_metrics.csv)・[1組除外](results/leave_one_out.csv) | 同順位・別の評価項目・部位除外の影響 |
| [配置の条件別集計](results/geometry_sensitivity.csv)・[条件別の順位相関](results/sensitivity_ranks.csv) | 閾値、衝突許容幅、格子の移動と高密度探索 |
| [α3Dの全候補](results/alpha3d_sites.csv) | 選定前10か所すべての溶媒露出面積、適格性、評価した9か所の結果 |
| [追試候補のアミノ酸配列](results/alpha3d_followup.fasta) | A55C、A44Cおよび各W4F対照の4配列。すべて実験未検証 |
| [出版用の図（ベクトルPDF）](results/ja/figure1.pdf) | 論文図1の独立ファイル |
| [数値計算](analysis/run.py)・[立体計算](analysis/geometry.py)・[作図](analysis/figures.py)・[日本語原稿の生成](paper/ja/build.py) | 入力から集計・図・原稿を再生成するコード |

## 再実行

Python 3.12以降と、解析用メモリのある一般的なPCで実行できる。主要な依存ライブラリのバージョンは固定した。この研究ディレクトリ（research/bimane-quenching）で以下を実行する。

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
make japanese PYTHON=.venv/bin/python
```

`make japanese` は公開構造と原図の読取座標のハッシュ値を照合し、集計、図のPNG・PDF、日本語のWord原稿を再生成する。英語のWord原稿と図は `make all` で再生成できる。計算は同梱のファイルで完結する。WindowsなどMakeを使わない環境では同じPythonで次のコマンドを順に実行する。

```sh
python analysis/run.py
python analysis/figures.py --language ja
python scripts/check_results.py
python paper/ja/build.py
```

配布時には独立したPython 3.12.12環境とPython 3.14.4環境で解析を再実行し、6個の結果CSV、候補のFASTA、図のPNGがバイト単位で一致することを確認した。

本文PDFはWord原稿をLibreOfficeで書き出した。日本語フォントを利用できる環境でWordの「PDFとして保存」、または次のコマンドを使う。本文の和文書体はヒラギノ明朝 ProN、見出しはヒラギノ角ゴシック。環境の代替書体によって改行やページ数は変わる。日本語の作図にはヒラギノ、Noto Sans CJK JP、IPAexゴシックなどを使える。

```sh
libreoffice --headless --convert-to pdf --outdir paper/ja paper/ja/bimane-static-quenching.ja.docx
```

LibreOfficeが使える場合は、`make japanese-pdf PYTHON=.venv/bin/python` で集計から日本語PDFまで通して再生成できる。`libreoffice` というコマンド名が登録されていない環境では、Makeの `SOFFICE` 変数に実行ファイルのパスを渡す。

## 出典と原図の照合

Jones BrunetteとFarrensの論文（2014年）の図4C・Aを読み、対応部位は図1・3と1L63のCα間距離で照合した。図4Cは強度・寿命に基づく**原著者の推定値**。個々の測定の生データはこの集計に含まれない。原図の負の点推定はそのまま保存した。図1の誤差棒は原図に描かれた上側の長さを再現したもので、信頼区間とみなしていない。全5組の一次データとして曲線を新たに測ったものではない。[原著](https://doi.org/10.1021/bi500493r)・[補足表](https://doi.org/10.1021/bi500493r.s001)

読み取りを検証する場合は、Popplerの `pdfimages` を用意して以下を実行する。NLMが配布する公開PDFを一時取得し、SHA-256を照合してから第6ページの原画像を抽出する。座標は画像左上を原点とする0始まりのピクセル。1250 × 1289ピクセルの原画像で、パネルCの0%は y = 1097.5、100%は y = 813.0。原図の1ピクセルは約0.35ポイントに相当する。既にPDFがある場合はオフラインでも照合できる。

```sh
python scripts/audit_source.py
python scripts/audit_source.py --pdf /path/to/PMC4196733.1.pdf
```

構造は公開PDBのA鎖・最初のモデルを使用した。1L63はT4リゾチームの骨格、2A3Dはα3DおよびTrp側鎖の環内座標、9PHRはCys151と9UM 201の結合部を含む色素の形状の出典。9UMはC8とCysのSGが結合した状態の座標を用いた。著者の論文PDFや元図を同梱せず、独自に作成した数値表と図を収録した。[1L63](https://www.rcsb.org/structure/1L63)・[2A3D](https://www.rcsb.org/structure/2A3D)・[9PHR](https://www.rcsb.org/structure/9PHR)

## 幾何計算と結果の読み方

- Trpのχ1とCysのχ1は±60°・180°付近の9値。Trpのχ2は±70°・±90°・±110°の6値。標識の残りのねじれ角は3 × 3 × 24通り。1組につき54 × 1,944 = 104,976通りを比較した。実験値を使ったパラメータ学習は行っていない。
- 衝突判定は入力の重原子座標に基づく。1–2結合を介する対を免除し、3結合を介する対は半径の和に対して0.50 Åの追加許容を与えた。T4リゾチームではTrpと標識側鎖の両方を置き換える。α3DのTrp固定条件では入力構造の既存接触を保持し、新しい側鎖・色素との接触を検査する。
- 主解析の許容幅は0.30 Å、接触は環上の重原子の最近接距離4.5 Å以下。ビマン環は C1–C6、N1、N2、インドール環は9個の重原子を使った。両環に接近した配置を等重みで数える。付いた色素の全原子は立体衝突判定に含めた。
- 現在の固定骨格・等重みのモデルは測定条件での存在確率や量子収率を表さない。空欄は許容配置が得られない場合、同順位で相関が定まらない場合、または候補選定から除いた場合を表す。接触数0・許容配置数が正の場合の配置指標は0になる。
- 順位相関は同順位を平均して算出した。正の相関が期待される向きにそろえるため、距離には負号を付けた。5! 通りの両側置換p値は部位の順序を置換した参考値。5組中4組がTrp116を共有する。2指標間の優劣についての有意差検定は行っていない。
- 高密度リンカー格子は見落としたW116/C128を受けて追加した探索的な検査で、同じ条件を5組全てに適用した。ゼロ付近の2組を同順位とする場合、静的消光率の絶対値が5ポイント未満の組をひとまとめにした。
- α3Dの選定は第2・第3ヘリックス（28～44番、53～70番）で、もとの残基がAla、Cβの溶媒露出面積が20 Å²以上の位置を対象とした。順位の選別に実験値は使っていない。A55Cの性能・折りたたみ依存性・他の残基種を含めた最適性は未検証である。
