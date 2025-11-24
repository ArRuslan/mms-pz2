import math
import os
import sys
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QSlider, QGroupBox, \
    QRadioButton, QStatusBar, QListWidget, QHBoxLayout, QComboBox, QTabWidget
from pydub import AudioSegment


class BatchConverterWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.files = []

        layout = QVBoxLayout()

        layout.addWidget(QLabel("<b>Batch Audio Converter (OGG - FLAC)</b>"))

        self.file_list = QListWidget()
        layout.addWidget(self.file_list)

        btn_add = QPushButton("Add OGG/FLAC files…")
        btn_add.clicked.connect(self.add_files)
        layout.addWidget(btn_add)

        btn_clear = QPushButton("Clear list")
        btn_clear.clicked.connect(lambda: (self.file_list.clear(), self.files.clear()))
        layout.addWidget(btn_clear)

        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Convert to:"))

        self.format_box = QComboBox()
        self.format_box.addItems(["ogg", "flac"])
        format_layout.addWidget(self.format_box)

        layout.addLayout(format_layout)

        btn_convert = QPushButton("Convert All")
        btn_convert.clicked.connect(self.convert_all)
        layout.addWidget(btn_convert)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select OGG/FLAC files", "", "Audio Files (*.ogg *.flac)")
        if not files:
            return

        for f in files:
            if f not in self.files:
                self.files.append(f)
                self.file_list.addItem(f)

    def convert_all(self):
        if not self.files:
            self.status_label.setText("No files to convert.")
            return

        out_format = self.format_box.currentText()

        out_dir = QFileDialog.getExistingDirectory(self, "Select output folder", "")
        if not out_dir:
            return

        count = 0

        for file_path in self.files:
            try:
                audio = AudioSegment.from_file(file_path)
                base = os.path.splitext(os.path.basename(file_path))[0]
                out_path = os.path.join(out_dir, base + "." + out_format)

                audio.export(out_path, format=out_format)

                count += 1

            except Exception as e:
                print("Error converting:", file_path, "\n", e)

        self.status_label.setText(f"Converted {count} files to {out_format}.")


class AudioEditor(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Pz2")
        self.resize(400, 300)

        self.audio: AudioSegment | None = None
        self.result_audio: AudioSegment | None = None
        self.file_path: str | None = None
        self.filter_str: str | None = None

        layout = QVBoxLayout()

        self.label = QLabel("No file selected")
        layout.addWidget(self.label)

        btn_open = QPushButton("Open audio file")
        btn_open.clicked.connect(self.open_file)
        layout.addWidget(btn_open)

        radio_group = QGroupBox("Edit")
        group_layout = QVBoxLayout()

        radio_original = QRadioButton("Original")
        radio_original.clicked.connect(lambda: self.apply_pan(0))
        group_layout.addWidget(radio_original)

        radio_left = QRadioButton("Left only")
        radio_left.clicked.connect(lambda: self.apply_pan(-1))
        group_layout.addWidget(radio_left)

        radio_right = QRadioButton("Right only")
        radio_right.clicked.connect(lambda: self.apply_pan(1))
        group_layout.addWidget(radio_right)

        radio_right = QRadioButton("Smooth pan")
        radio_right.clicked.connect(self.make_smooth)
        group_layout.addWidget(radio_right)

        radio_group.setLayout(group_layout)
        radio_original.setChecked(True)

        layout.addWidget(radio_group)

        layout.addWidget(QLabel("Volume"))
        self.vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setMinimum(-40)
        self.vol_slider.setMaximum(10)
        self.vol_slider.setValue(0)
        self.vol_slider.valueChanged.connect(self.update_volume)
        layout.addWidget(self.vol_slider)

        layout.addWidget(QLabel("Compressor"))

        self.threshold_label = QLabel("Threshold (dB)")
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.valueChanged.connect(self.on_threshold_update)
        self.threshold_slider.setMinimum(-60)
        self.threshold_slider.setMaximum(0)
        self.threshold_slider.setValue(-20)
        layout.addWidget(self.threshold_label)
        layout.addWidget(self.threshold_slider)

        self.ratio_label = QLabel("Ratio")
        self.ratio_slider = QSlider(Qt.Orientation.Horizontal)
        self.ratio_slider.valueChanged.connect(self.on_ratio_update)
        self.ratio_slider.setMinimum(1)
        self.ratio_slider.setMaximum(20)
        self.ratio_slider.setValue(4)
        layout.addWidget(self.ratio_label)
        layout.addWidget(self.ratio_slider)

        self.attack_label = QLabel("Attack (ms)")
        self.attack_slider = QSlider(Qt.Orientation.Horizontal)
        self.attack_slider.valueChanged.connect(self.on_attack_update)
        self.attack_slider.setMinimum(1)
        self.attack_slider.setMaximum(200)
        self.attack_slider.setValue(20)
        layout.addWidget(self.attack_label)
        layout.addWidget(self.attack_slider)

        self.release_label = QLabel("Release (ms)")
        self.release_slider = QSlider(Qt.Orientation.Horizontal)
        self.release_slider.valueChanged.connect(self.on_release_update)
        self.release_slider.setMinimum(10)
        self.release_slider.setMaximum(1000)
        self.release_slider.setValue(200)
        layout.addWidget(self.release_label)
        layout.addWidget(self.release_slider)

        btn_compress = QPushButton("Apply Compression")
        btn_compress.clicked.connect(self.apply_compression)
        layout.addWidget(btn_compress)

        btn_compress_reset = QPushButton("Reset Compression")
        btn_compress_reset.clicked.connect(self.reset_compression)
        layout.addWidget(btn_compress_reset)

        layout.addWidget(QLabel("Export"))

        btn_export = QPushButton("Export processed audio")
        btn_export.clicked.connect(self.export_audio)
        layout.addWidget(btn_export)

        self.status_bar = QStatusBar()
        self.status_bar.showMessage("...")
        layout.addWidget(self.status_bar)

        self.setLayout(layout)

    def open_file(self) -> None:
        self.status_bar.showMessage("Opening file")
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select audio", "", "Audio Files (*.ogg *.flac *.mp3)"
        )

        if not file_path:
            self.status_bar.showMessage("Opening canceled")
            return

        self.file_path = file_path
        self.label.setText(file_path)

        self.audio = self.result_audio = AudioSegment.from_file(file_path)
        self.status_bar.showMessage(f"Opened file {file_path}")

    def apply_pan(self, value: float) -> None:
        if not self.audio:
            self.status_bar.showMessage("No audio")
            return
        self.status_bar.showMessage("Applying...")
        self.result_audio = self.audio.pan(value)
        self.status_bar.showMessage("Applied")

    chunk_ms = 20

    def _make_smooth_thread(self, audio: AudioSegment, idx: int, chunks: list[AudioSegment | None]) -> None:
        phase = idx * 0.01
        start = self.chunk_ms * idx
        chunk = audio[start:start + self.chunk_ms]
        pan = math.sin(phase)
        chunks[idx] = chunk.pan(pan)

    def make_smooth(self) -> None:
        duration_ms = len(self.audio)

        chunks = [None for _ in range(0, duration_ms, self.chunk_ms)]

        with ThreadPoolExecutor(max_workers=4) as executor:
            for idx in range((duration_ms + self.chunk_ms - 1) // self.chunk_ms):
                executor.submit(self._make_smooth_thread, self.audio, idx, chunks)

        self.result_audio = sum(chunks)

    def update_volume(self) -> None:
        if not self.audio:
            self.status_bar.showMessage("No audio")
            return

        self.status_bar.showMessage("Applying volume...")
        db = self.vol_slider.value()
        self.result_audio = self.audio + db
        self.status_bar.showMessage("Applied volume")

    def on_threshold_update(self, value: int) -> None:
        self.threshold_label.setText(f"Threshold (dB): {value}")

    def on_ratio_update(self, value: int) -> None:
        self.ratio_label.setText(f"Ratio: {value}")

    def on_attack_update(self, value: int) -> None:
        self.attack_label.setText(f"Attack (ms): {value}")

    def on_release_update(self, value: int) -> None:
        self.release_label.setText(f"Release (ms): {value}")

    def apply_compression(self) -> None:
        if not self.audio:
            self.status_bar.showMessage("No audio")
            return

        threshold = self.threshold_slider.value()
        ratio = self.ratio_slider.value()
        attack = self.attack_slider.value() / 1000.0
        release = self.release_slider.value() / 1000.0

        self.filter_str = (
            f"acompressor="
            f"threshold={threshold}dB:"
            f"ratio={ratio}:"
            f"attack={attack}:"
            f"release={release}"
        )

    def reset_compression(self) -> None:
        self.filter_str = None
        self.threshold_slider.setValue(-20)
        self.ratio_slider.setValue(4)
        self.attack_slider.setValue(20)
        self.release_slider.setValue(200)

    def export_audio(self) -> None:
        if not self.result_audio:
            self.status_bar.showMessage("No audio")
            return

        self.status_bar.showMessage("Saving file...")
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Export audio", "output.ogg", "Vorbis (*.ogg);;FLAC (*.flac)"
        )
        if not save_path:
            self.status_bar.showMessage("Saving canceled")
            return

        self.result_audio.export(
            out_f=save_path,
            format=save_path.split('.')[-1],
            parameters=["-af", self.filter_str] if self.filter_str else None,
        )
        self.status_bar.showMessage(f"Saved file to {save_path}")


def main() -> None:
    app = QApplication(sys.argv)
    tabs = QTabWidget()
    tabs.addTab(AudioEditor(), "Editor")
    tabs.addTab(BatchConverterWidget(), "Converter")
    tabs.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
