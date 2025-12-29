#!/usr/bin/env python3
"""
Duck Decode GUI - 隐写解码图形界面工具
从图片中解码隐藏的文件内容
"""
import os
import struct
import sys
import numpy as np
from PIL import Image

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QFileDialog,
    QProgressBar, QMessageBox, QGroupBox
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QIcon

CATEGORY = "SSTool"
WATERMARK_SKIP_W_RATIO = 0.40
WATERMARK_SKIP_H_RATIO = 0.08


class DecodeWorker(QThread):
    """解码工作线程"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(str, str, str)  # (output_path, ext, size_str)
    error = pyqtSignal(str)

    def __init__(self, image_path: str, password: str, output_dir: str):
        super().__init__()
        self.image_path = image_path
        self.password = password
        self.output_dir = output_dir

    def run(self):
        try:
            self.progress.emit("正在加载图像...")
            img = Image.open(self.image_path)
            arr = np.array(img.convert("RGB")).astype(np.uint8)

            self.progress.emit("正在提取隐写数据...")
            header = None
            raw = None
            ext = None
            last_err = None
            for k in (2, 6, 8):
                try:
                    header = self._extract_payload_with_k(arr, k)
                    raw, ext = self._parse_header(header, self.password)
                    break
                except Exception as e:
                    last_err = e
                    continue

            if raw is None:
                raise last_err or RuntimeError("解析失败 / Decoding failed")

            self.progress.emit("正在保存文件...")
            os.makedirs(self.output_dir, exist_ok=True)
            name = "duck_recovered"
            out_path = os.path.join(self.output_dir, name)

            if ext.endswith(".binpng"):
                tmp_png = out_path + ".binpng"
                with open(tmp_png, "wb") as f:
                    f.write(raw)
                mp4_bytes = self._binpng_bytes_to_mp4_bytes(tmp_png)
                os.unlink(tmp_png)
                final_path = out_path + ".mp4"
                with open(final_path, "wb") as f:
                    f.write(mp4_bytes)
                final_ext = "mp4"
            else:
                final_path = out_path + ("." + ext if not ext.startswith(".") else ext)
                with open(final_path, "wb") as f:
                    f.write(raw)
                final_ext = ext.lstrip(".")

            # 计算文件大小
            size = os.path.getsize(final_path)
            if size > 1024 * 1024:
                size_str = f"{size / (1024 * 1024):.2f} MB"
            elif size > 1024:
                size_str = f"{size / 1024:.2f} KB"
            else:
                size_str = f"{size} bytes"

            self.finished.emit(final_path, final_ext, size_str)

        except Exception as e:
            self.error.emit(str(e))

    def _extract_payload_with_k(self, arr: np.ndarray, k: int) -> bytes:
        h, w, c = arr.shape
        skip_w = int(w * WATERMARK_SKIP_W_RATIO)
        skip_h = int(h * WATERMARK_SKIP_H_RATIO)
        mask2d = np.ones((h, w), dtype=bool)
        if skip_w > 0 and skip_h > 0:
            mask2d[:skip_h, :skip_w] = False
        mask3d = np.repeat(mask2d[:, :, None], c, axis=2)
        flat = arr.reshape(-1)
        idxs = np.flatnonzero(mask3d.reshape(-1))
        vals = (flat[idxs] & ((1 << k) - 1)).astype(np.uint8)
        ub = np.unpackbits(vals, bitorder="big").reshape(-1, 8)[:, -k:]
        bits = ub.reshape(-1)
        if len(bits) < 32:
            raise ValueError("Insufficient image data. 图像数据不足")
        len_bits = bits[:32]
        length_bytes = np.packbits(len_bits, bitorder="big").tobytes()
        header_len = struct.unpack(">I", length_bytes)[0]
        total_bits = 32 + header_len * 8
        if header_len <= 0 or total_bits > len(bits):
            raise ValueError("Payload length invalid. 载荷长度异常")
        payload_bits = bits[32:32 + header_len * 8]
        return np.packbits(payload_bits, bitorder="big").tobytes()

    def _generate_key_stream(self, password: str, salt: bytes, length: int) -> bytes:
        import hashlib
        key_material = (password + salt.hex()).encode("utf-8")
        out = bytearray()
        counter = 0
        while len(out) < length:
            out.extend(hashlib.sha256(key_material + str(counter).encode("utf-8")).digest())
            counter += 1
        return bytes(out[:length])

    def _parse_header(self, header: bytes, password: str):
        idx = 0
        if len(header) < 1:
            raise ValueError("Header corrupted. 文件头损坏")
        has_pwd = header[0] == 1
        idx += 1
        pwd_hash = b""
        salt = b""
        if has_pwd:
            if len(header) < idx + 32 + 16:
                raise ValueError("Header corrupted. 文件头损坏")
            pwd_hash = header[idx:idx + 32]
            idx += 32
            salt = header[idx:idx + 16]
            idx += 16
        if len(header) < idx + 1:
            raise ValueError("Header corrupted. 文件头损坏")
        ext_len = header[idx]
        idx += 1
        if len(header) < idx + ext_len + 4:
            raise ValueError("Header corrupted. 文件头损坏")
        ext = header[idx:idx + ext_len].decode("utf-8", errors="ignore")
        idx += ext_len
        data_len = struct.unpack(">I", header[idx:idx + 4])[0]
        idx += 4
        data = header[idx:]
        if len(data) != data_len:
            raise ValueError("Data length mismatch. 数据长度不匹配")
        if not has_pwd:
            return data, ext
        if not password:
            raise ValueError("Password required. 需要密码")
        import hashlib
        check_hash = hashlib.sha256((password + salt.hex()).encode("utf-8")).digest()
        if check_hash != pwd_hash:
            raise ValueError("Wrong password. 密码错误")
        ks = self._generate_key_stream(password, salt, len(data))
        plain = bytes(a ^ b for a, b in zip(data, ks))
        return plain, ext

    def _binpng_bytes_to_mp4_bytes(self, p: str) -> bytes:
        img = Image.open(p).convert("RGB")
        arr = np.array(img).astype(np.uint8)
        flat = arr.reshape(-1, 3).reshape(-1)
        return flat.tobytes().rstrip(b"\x00")


class DuckDecodeWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.worker = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Duck Decode - 隐写解码工具 v1.0")
        self.setGeometry(100, 100, 600, 500)
        self.setMinimumWidth(500)

        # 中心部件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("🦆 Duck Decode 隐写解码工具")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 输入文件组
        input_group = QGroupBox("输入文件")
        input_layout = QVBoxLayout()
        input_file_layout = QHBoxLayout()
        self.input_path_edit = QLineEdit()
        self.input_path_edit.setPlaceholderText("选择包含隐藏文件的图片...")
        self.input_path_edit.setReadOnly(True)
        input_file_layout.addWidget(self.input_path_edit)
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_input_file)
        input_file_layout.addWidget(browse_btn)
        input_layout.addLayout(input_file_layout)
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # 密码组
        pwd_group = QGroupBox("密码（可选）")
        pwd_layout = QHBoxLayout()
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("如果文件有密码保护，请输入...")
        self.password_edit.setEchoMode(QLineEdit.Password)
        pwd_layout.addWidget(self.password_edit)
        pwd_group.setLayout(pwd_layout)
        layout.addWidget(pwd_group)

        # 输出目录组
        output_group = QGroupBox("输出目录")
        output_layout = QVBoxLayout()
        output_dir_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setText(os.getcwd())
        self.output_dir_edit.setReadOnly(True)
        output_dir_layout.addWidget(self.output_dir_edit)
        output_browse_btn = QPushButton("浏览...")
        output_browse_btn.clicked.connect(self.browse_output_dir)
        output_dir_layout.addWidget(output_browse_btn)
        output_layout.addLayout(output_dir_layout)
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        # 解码按钮
        self.decode_btn = QPushButton("🔓 开始解码")
        self.decode_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.decode_btn.setMinimumHeight(45)
        self.decode_btn.clicked.connect(self.start_decode)
        layout.addWidget(self.decode_btn)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # 日志输出
        log_group = QGroupBox("运行日志")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setFont(QFont("Consolas", 9))
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        # 打开输出目录按钮
        self.open_btn = QPushButton("📁 打开输出目录")
        self.open_btn.setEnabled(False)
        self.open_btn.clicked.connect(self.open_output_dir)
        layout.addWidget(self.open_btn)

        self.current_output_dir = os.getcwd()

    def browse_input_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择包含隐藏文件的图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp);;所有文件 (*.*)"
        )
        if file_path:
            self.input_path_edit.setText(file_path)
            self.log(f"已选择输入文件: {file_path}")

    def browse_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择输出目录",
            self.output_dir_edit.text()
        )
        if dir_path:
            self.output_dir_edit.setText(dir_path)
            self.current_output_dir = dir_path

    def start_decode(self):
        input_path = self.input_path_edit.text()
        if not input_path:
            QMessageBox.warning(self, "警告", "请先选择输入文件!")
            return
        if not os.path.isfile(input_path):
            QMessageBox.warning(self, "警告", "输入文件不存在!")
            return

        password = self.password_edit.text()
        output_dir = self.output_dir_edit.text()

        # 禁用按钮
        self.decode_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 无限进度条
        self.open_btn.setEnabled(False)

        # 清空日志
        self.log_text.clear()
        self.log(f"开始解码: {os.path.basename(input_path)}")
        self.log(f"输出目录: {output_dir}")

        # 启动工作线程
        self.worker = DecodeWorker(input_path, password, output_dir)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_progress(self, message):
        self.log(message)

    def on_finished(self, output_path, ext, size_str):
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(1)
        self.decode_btn.setEnabled(True)
        self.open_btn.setEnabled(True)
        self.log("-" * 50)
        self.log("✓ 解码成功!")
        self.log(f"输出文件: {output_path}")
        self.log(f"文件类型: {ext}")
        self.log(f"文件大小: {size_str}")

        QMessageBox.information(
            self,
            "解码成功",
            f"文件已成功解码!\n\n输出位置: {output_path}\n文件类型: {ext}\n文件大小: {size_str}"
        )

    def on_error(self, error_msg):
        self.progress_bar.setVisible(False)
        self.decode_btn.setEnabled(True)
        self.log("-" * 50)
        self.log(f"✗ 错误: {error_msg}")

        QMessageBox.critical(
            self,
            "解码失败",
            f"解码过程中发生错误:\n\n{error_msg}"
        )

    def open_output_dir(self):
        import subprocess
        path = self.current_output_dir
        if os.path.exists(path):
            subprocess.Popen(f'explorer "{path}"')

    def log(self, message):
        self.log_text.append(message)
        # 自动滚动到底部
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 使用Fusion样式

    # 设置应用样式
    from PyQt5.QtGui import QPalette, QColor
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(240, 240, 240))
    palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
    palette.setColor(QPalette.Button, QColor(220, 220, 220))
    palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
    app.setPalette(palette)

    window = DuckDecodeWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()