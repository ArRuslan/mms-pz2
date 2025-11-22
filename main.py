import math
import sys
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QSlider, QGroupBox, \
    QRadioButton, QStatusBar
from pydub import AudioSegment


class AudioEditor(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Pz2")
        self.resize(400, 300)

        self.audio: AudioSegment | None = None
        self.result_audio: AudioSegment | None = None
        self.file_path = None

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
            self, "Select audio", "", "Audio Files (*.wav *.flac *.mp3)"
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

    def export_audio(self) -> None:
        if not self.result_audio:
            self.status_bar.showMessage("No audio")
            return

        self.status_bar.showMessage("Saving file...")
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Export audio", "output.wav", "WAV (*.wav);;FLAC (*.flac)"
        )
        if not save_path:
            self.status_bar.showMessage("Saving canceled")
            return

        self.result_audio.export(save_path, format=save_path.split('.')[-1])
        self.status_bar.showMessage(f"Saved file to {save_path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AudioEditor()
    window.show()
    sys.exit(app.exec())
