#!/usr/bin/env python3
"""
Duck Decode Android - 隐写解码移动端工具
从图片中解码隐藏的文件内容
"""
import os
import struct
import numpy as np
from PIL import Image

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.window import Window

CATEGORY = "SSTool"
WATERMARK_SKIP_W_RATIO = 0.40
WATERMARK_SKIP_H_RATIO = 0.08


class DecodeLogic:
    """解码逻辑类"""

    @staticmethod
    def extract_payload_with_k(arr: np.ndarray, k: int) -> bytes:
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

    @staticmethod
    def generate_key_stream(password: str, salt: bytes, length: int) -> bytes:
        import hashlib
        key_material = (password + salt.hex()).encode("utf-8")
        out = bytearray()
        counter = 0
        while len(out) < length:
            out.extend(hashlib.sha256(key_material + str(counter).encode("utf-8")).digest())
            counter += 1
        return bytes(out[:length])

    @staticmethod
    def parse_header(header: bytes, password: str):
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
        ks = DecodeLogic.generate_key_stream(password, salt, len(data))
        plain = bytes(a ^ b for a, b in zip(data, ks))
        return plain, ext

    @staticmethod
    def binpng_bytes_to_mp4_bytes(p: str) -> bytes:
        img = Image.open(p).convert("RGB")
        arr = np.array(img).astype(np.uint8)
        flat = arr.reshape(-1, 3).reshape(-1)
        return flat.tobytes().rstrip(b"\x00")

    @staticmethod
    def decode(image_path: str, password: str, output_dir: str, callback=None):
        """执行解码"""
        try:
            if callback:
                callback("Loading image... 正在加载图像")

            img = Image.open(image_path)
            arr = np.array(img.convert("RGB")).astype(np.uint8)

            if callback:
                callback("Extracting data... 正在提取隐写数据")

            header = None
            raw = None
            ext = None
            last_err = None
            for k in (2, 6, 8):
                try:
                    header = DecodeLogic.extract_payload_with_k(arr, k)
                    raw, ext = DecodeLogic.parse_header(header, password)
                    break
                except Exception as e:
                    last_err = e
                    continue

            if raw is None:
                raise last_err or RuntimeError("Decoding failed / 解析失败")

            if callback:
                callback("Saving file... 正在保存文件")

            os.makedirs(output_dir, exist_ok=True)
            name = "duck_recovered"
            out_path = os.path.join(output_dir, name)

            if ext.endswith(".binpng"):
                tmp_png = out_path + ".binpng"
                with open(tmp_png, "wb") as f:
                    f.write(raw)
                mp4_bytes = DecodeLogic.binpng_bytes_to_mp4_bytes(tmp_png)
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

            size = os.path.getsize(final_path)
            if size > 1024 * 1024:
                size_str = f"{size / (1024 * 1024):.2f} MB"
            elif size > 1024:
                size_str = f"{size / 1024:.2f} KB"
            else:
                size_str = f"{size} bytes"

            return final_path, final_ext, size_str

        except Exception as e:
            raise e


class DuckDecodeApp(App):
    """主应用类"""

    def build(self):
        self.title = "Duck Decode"
        Window.softinput_mode = "below_target"

        # 主布局
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # 标题
        title_label = Label(
            text="Duck Decode",
            font_size='30sp',
            size_hint_y=None,
            height=60,
            bold=True
        )
        main_layout.add_widget(title_label)

        # 输入文件选择
        input_layout = GridLayout(cols=1, rows=2, size_hint_y=None, height=80, spacing=5)
        input_layout.add_widget(Label(text="Input File / 输入文件", font_size='16sp', halign='left'))

        self.file_label = Label(
            text="Tap to select image / 点击选择图片",
            font_size='14sp',
            color=(0, 0, 1, 1),
            size_hint_y=None,
            height=40
        )
        self.file_label.bind(on_touch_down=self.select_file)
        input_layout.add_widget(self.file_label)
        main_layout.add_widget(input_layout)

        # 密码输入
        pwd_layout = GridLayout(cols=1, rows=2, size_hint_y=None, height=80, spacing=5)
        pwd_layout.add_widget(Label(text="Password / 密码 (可选)", font_size='16sp', halign='left'))
        self.password_input = TextInput(
            hint_text="Enter password if needed / 如有密码请输入",
            password=True,
            multiline=False,
            size_hint_y=None,
            height=40,
            font_size='14sp'
        )
        pwd_layout.add_widget(self.password_input)
        main_layout.add_widget(pwd_layout)

        # 输出目录
        output_layout = GridLayout(cols=1, rows=2, size_hint_y=None, height=80, spacing=5)
        output_layout.add_widget(Label(text="Output Dir / 输出目录", font_size='16sp', halign='left'))

        self.output_label = Label(
            text=self.get_default_output_dir(),
            font_size='12sp',
            color=(0, 0, 0, 1),
            size_hint_y=None,
            height=40,
            text_size=(None, 40)
        )
        output_layout.add_widget(self.output_label)
        main_layout.add_widget(output_layout)

        # 解码按钮
        self.decode_btn = Button(
            text="DECODE / 解码",
            font_size='20sp',
            size_hint_y=None,
            height=60,
            background_color=(0.2, 0.6, 1, 1)
        )
        self.decode_btn.bind(on_press=self.start_decode)
        main_layout.add_widget(self.decode_btn)

        # 日志显示
        log_label = Label(text="Log / 日志:", font_size='14sp', halign='left', size_hint_y=None, height=30)
        main_layout.add_widget(log_label)

        self.log_text = TextInput(
            readonly=True,
            font_size='12sp',
            size_hint_y=1
        )
        main_layout.add_widget(self.log_text)

        # 打开输出目录按钮
        self.open_btn = Button(
            text="Open Output / 打开输出目录",
            font_size='16sp',
            size_hint_y=None,
            height=50,
            disabled=True
        )
        self.open_btn.bind(on_press=self.open_output_dir)
        main_layout.add_widget(self.open_btn)

        self.selected_file = None
        self.output_dir = self.get_default_output_dir()

        return main_layout

    def get_default_output_dir(self):
        """获取默认输出目录"""
        if platform == 'android':
            from android.storage import primary_external_storage_path
            return primary_external_storage_path()
        return os.getcwd()

    def select_file(self, instance, touch):
        if instance.collide_point(*touch.pos):
            if platform == 'android':
                self.select_file_android()
            else:
                self.select_file_desktop()

    def select_file_android(self):
        """Android文件选择"""
        from jnius import autoclass
        from android import activity

        Intent = autoclass('android.content.Intent')
        activity_result = None

        def on_activity_result(request_code, result_code, intent):
            nonlocal activity_result
            activity_result = (request_code, result_code, intent)

        activity.bind(on_activity_result=on_activity_result)

        intent = Intent()
        intent.setAction(Intent.ACTION_GET_CONTENT)
        intent.setType("image/*")
        current_activity = autoclass('org.kivy.android.PythonActivity').mActivity
        current_activity.startActivityForResult(intent, 1001)

        # 等待结果
        Clock.schedule_interval(self.check_file_result, 0.1)

    def check_file_result(self, dt):
        """检查文件选择结果"""
        from android import activity
        if hasattr(self, '_activity_result'):
            request_code, result_code, intent = self._activity_result
            if request_code == 1001:
                if result_code == -1:  # RESULT_OK
                    uri = intent.getData()
                    from jnius import autoclass
                    Uri = autoclass('android.net.Uri')
                    content_resolver = autoclass('org.kivy.android.PythonActivity').mActivity.getContentResolver()

                    # 读取文件
                    import io
                    from kivy.core.image import Image as CoreImage

                    # 使用ContentResolver打开输入流
                    input_stream = content_resolver.openInputStream(uri)
                    data = bytearray()
                    buffer = bytearray(4096)
                    while True:
                        read = input_stream.read(buffer, 0, 4096)
                        if read == -1:
                            break
                        data.extend(buffer[:read])
                    input_stream.close()

                    # 保存到临时文件
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as f:
                        f.write(data)
                        self.selected_file = f.name

                    self.file_label.text = f"Selected: {os.path.basename(self.selected_file)}"
                    self.log(f"File selected: {self.selected_file}")

                delattr(self, '_activity_result')
                return False
        return True

    def select_file_desktop(self):
        """桌面端文件选择（用于测试）"""
        # 简单实现，仅用于测试
        self.log("Please select file manually for now / 请手动输入文件路径测试")
        self.selected_file = input("Enter image path: ")
        if os.path.isfile(self.selected_file):
            self.file_label.text = f"Selected: {os.path.basename(self.selected_file)}"
            self.log(f"File: {self.selected_file}")

    def start_decode(self, instance):
        """开始解码"""
        if not self.selected_file:
            self.show_popup("Error / 错误", "Please select an image file first / 请先选择图片文件")
            return

        if not os.path.isfile(self.selected_file):
            self.show_popup("Error / 错误", "File not found / 文件不存在")
            return

        password = self.password_input.text

        # 禁用按钮
        self.decode_btn.disabled = True
        self.log_text.text = ""
        self.log("Starting decode... 开始解码\n")

        # 使用定时器执行解码（避免阻塞UI）
        Clock.schedule_once(lambda dt: self.do_decode(password), 0.1)

    def do_decode(self, password):
        """执行解码"""
        try:
            result = DecodeLogic.decode(
                self.selected_file,
                password,
                self.output_dir,
                callback=self.log
            )

            final_path, final_ext, size_str = result
            self.log("-" * 50)
            self.log("SUCCESS! / 解码成功!")
            self.log(f"File: {final_path}")
            self.log(f"Type: {final_ext}")
            self.log(f"Size: {size_str}")

            self.decode_btn.disabled = False
            self.open_btn.disabled = False

            self.show_popup(
                "Success / 成功",
                f"File decoded successfully!\n解码成功!\n\nType: {final_ext}\nSize: {size_str}"
            )

        except Exception as e:
            self.decode_btn.disabled = False
            self.log("-" * 50)
            self.log(f"ERROR / 错误: {str(e)}")
            self.show_popup("Error / 错误", str(e))

    def open_output_dir(self, instance):
        """打开输出目录"""
        if platform == 'android':
            from jnius import autoclass
            Intent = autoclass('android.content.Intent')
            intent = Intent()
            intent.setAction(Intent.ACTION_VIEW)
            from android.storage import primary_external_storage_path
            import urllib.parse
            uri = autoclass('android.net.Uri').parse(f"file://{self.output_dir}")
            intent.setDataAndType(uri, "resource/folder")
            autoclass('org.kivy.android.PythonActivity').mActivity.startActivity(intent)
        else:
            import subprocess
            subprocess.Popen(f'explorer "{self.output_dir}"')

    def log(self, message):
        """添加日志"""
        self.log_text.text += message + "\n"

    def show_popup(self, title, message):
        """显示弹窗"""
        popup_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        popup_label = Label(text=message, font_size='16sp', text_size=(None, None))
        popup_layout.add_widget(popup_label)

        close_btn = Button(text="OK / 确定", size_hint_y=None, height=50, font_size='18sp')
        popup_layout.add_widget(close_btn)

        popup = Popup(
            title=title,
            content=popup_layout,
            size_hint=(0.9, 0.5),
            auto_dismiss=False
        )
        close_btn.bind(on_press=popup.dismiss)
        popup.open()


if __name__ == "__main__":
    DuckDecodeApp().run()