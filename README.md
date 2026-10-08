# Auto Blur & Track App

動画内の「人物の顔」および「車両のナンバープレート」をYOLOv8とByteTrackで自動検出し、追跡してモザイクを一括適用するデスクトップ向けアプリケーションです。

## プロジェクト構成

```
auto_blur_app/
├── app/
│   ├── main.py        # アプリケーションのエントリーポイント
│   ├── gui.py         # PyQt6を使用したGUIのレイアウトおよびイベント制御
│   └── processor.py   # YOLOv8推論、ByteTrackトラッキング、モザイク処理、および非同期エクスポート処理
├── models/            # YOLOv8のモデルファイル(.pt)を配置するディレクトリ
├── requirements.txt   # 依存ライブラリ一覧
└── README.md          # 本ドキュメント
```

## 動作環境・技術スタック
- Python 3.10以上
- GUI: PyQt6
- AI推論: Ultralytics (YOLOv8)
- トラッキング: Supervision (ByteTrack)
- 画像処理: OpenCV

## セットアップ手順

1. **Python環境の準備**
   仮想環境を作成して有効化することをお勧めします。
   ```bash
   python -m venv venv
   # Windowsの場合
   venv\Scripts\activate
   ```

2. **依存パッケージのインストール**
   CUDA (GPU) を利用可能な環境であれば、PyTorchのCUDA対応版をインストールすることで推論が高速化されます。デフォルトではCPUまたは自動フォールバックが機能します。
   ```bash
   pip install -r requirements.txt
   ```
   ※GPUを使用する場合は、事前に[PyTorch公式サイト](https://pytorch.org/get-started/locally/)の手順に従い、CUDA対応版のPyTorchをインストールしてください。

3. **AIモデルの準備**
   本ツールは `./models/yolov8n-face.pt` および `./models/yolov8n-plate.pt` をロードしようと試みます。ファイルがない場合は、自動的に標準の `yolov8n.pt` がダウンロードされ代替として使用されます（ただし標準モデルは顔専用・ナンバー専用ではないため検出精度は汎用的になります）。
   
   - **顔検出モデルの入手例**: GitHub等で公開されている YOLOv8-face の学習済みモデル(`.pt`ファイル)をダウンロードし、`models` フォルダに `yolov8n-face.pt` として配置してください。
   - **ナンバープレートモデルの入手例**: 同様に YOLOv8 用のライセンスプレート検出モデルを `models/yolov8n-plate.pt` として配置してください。

## アプリケーションの起動

以下のコマンドでGUIアプリケーションを起動します。
```bash
cd app
python main.py
```

## 使い方

1. **動画の読み込み**
   - 画面左側のプレビュー領域に動画ファイル（`.mp4`, `.mov`, `.avi`）をドラッグ＆ドロップするか、右側の「動画を開く」ボタンから選択します。
2. **プレビューとパラメータ調整**
   - スライダー（シークバー）や再生ボタンで動画を確認できます。
   - 右側のパネルで、検出対象（顔・ナンバー）のON/OFF、信頼度（Confidence Threshold）、モザイク強度（Pixelation Level）、余白（Padding）を調整できます。
   - 「プレビューにモザイク適用」にチェックを入れると、シーク時にリアルタイムで処理結果を確認できます。
3. **エクスポート（書き出し）**
   - 「書き出し開始」ボタンを押し、保存先を指定すると、別スレッドで高速に動画のエンコード処理が行われます。
   - 進行状況はプログレスバーに表示され、途中で「キャンセル」することも可能です。
   - 長時間の動画でも、逐次フレームを処理してファイルに書き込むため、メモリリークは発生しません。

## ライセンス (License)
本ソフトウェアは **GNU Affero General Public License v3.0 (AGPL-3.0)** の下で公開されています。詳細については `LICENSE` ファイルをご参照ください。

### サードパーティライセンス
本ソフトウェアは以下のオープンソースライブラリを使用しています：
- **Ultralytics (YOLOv8)**: AGPL-3.0
- **PyQt6**: GPLv3
- **Supervision**: MIT License
- **OpenCV**: Apache-2.0
- **imageio**: BSD-2-Clause
