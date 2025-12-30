#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Duck Decode Android - Steganography Decoder Tool
Simplified stable version
"""
import os
import sys
import struct
import traceback
import numpy as np
from PIL import Image
from datetime import datetime

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp

# Android Chinese font path
ANDROID_CHINESE_FONT = '/system/fonts/NotoSansCJK-Regular.ttc'
ANDROID_FALLBACK_FONT = '/system/fonts/DroidSansFallback.ttf'

# Simple Colors
PRIMARY = (0.26, 0.35, 0.76, 1)
SUCCESS = (0.20, 0.73, 0.33, 1)
ERROR = (0.94, 0.33, 0.33, 1)
BACKGROUND = (0.97, 0.97, 1.0, 1)
SURFACE = (1.0, 1.0, 1.0, 1)
TEXT_PRIMARY = (0.13, 0.13, 0.13, 1)
TEXT_SECONDARY = (0.60, 0.60, 0.60, 1)


def get_chinese_font():
    try:
        if platform == 'android':
            if os.path.exists(ANDROID_CHINESE_FONT):
                return ANDROID_CHINESE_FONT
            elif os.path.exists(ANDROID_FALLBACK_FONT):
                return ANDROID_FALLBACK_FONT
    except:
        pass
    return 'Roboto'


CHINESE_FONT = get_chinese_font()


# 全局错误捕获
def global_exception_handler(exc_type, exc_value, exc_traceback):
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print("CRITICAL ERROR:", error_msg, file=sys.stderr)
    try:
        app = App.get_running_app()
        if app:
            log_path = os.path.join(app.user_data_dir, "error_log.txt")
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{error_msg}")
    except:
        pass


sys.excepthook = global_exception_handler

CATEGORY = "SSTool"
WATERMARK_SKIP_W_RATIO = 0.40
WATERMARK_SKIP_H_RATIO = 0.08


# ==================== 中文支持组件 ====================

class ChineseLabel(Label):
    def __init__(self, **kwargs):
        kwargs['font_name'] = CHINESE_FONT
        super().__init__(**kwargs)


class ChineseButton(Button):
    def __init__(self, **kwargs):
        kwargs['font_name'] = CHINESE_FONT
        super().__init__(**kwargs)


class ChineseTextInput(TextInput):
    def __init__(self, **kwargs):
        kwargs['font_name'] = CHINESE_FONT
        super().__init__(**kwargs)


# ==================== 解码逻辑 ====================

class SafeDecodeLogic:
    @staticmethod
    def extract_payload_with_k(arr: np.ndarray, k: int) -> bytes:
        try:
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
                raise ValueError("图片数据太少，无法解码")
            len_bits = bits[:32]
            length_bytes = np.packbits(len_bits, bitorder="big").tobytes()
            header_len = struct.unpack(">I", length_bytes)[0]
            total_bits = 32 + header_len * 8
            if header_len <= 0 or total_bits > len(bits):
                raise ValueError("文件数据长度异常")
            payload_bits = bits[32:32 + header_len * 8]
            return np.packbits(payload_bits, bitorder="big").tobytes()
        except Exception as e:
            raise Exception(f"提取数据失败: {str(e)}")

    @staticmethod
    def generate_key_stream(password: str, salt: bytes, length: int) -> bytes:
        try:
            import hashlib
            key_material = (password + salt.hex()).encode("utf-8")
            out = bytearray()
            counter = 0
            while len(out) < length:
                out.extend(hashlib.sha256(key_material + str(counter).encode("utf-8")).digest())
                counter += 1
            return bytes(out[:length])
        except Exception as e:
            raise Exception(f"密码处理失败: {str(e)}")

    @staticmethod
    def parse_header(header: bytes, password: str):
        try:
            idx = 0
            if len(header) < 1:
                raise ValueError("文件头损坏")
            has_pwd = header[0] == 1
            idx += 1
            pwd_hash = b""
            salt = b""
            if has_pwd:
                if len(header) < idx + 32 + 16:
                    raise ValueError("文件头损坏")
                pwd_hash = header[idx:idx + 32]
                idx += 32
                salt = header[idx:idx + 16]
                idx += 16
            if len(header) < idx + 1:
                raise ValueError("文件头损坏")
            ext_len = header[idx]
            idx += 1
            if len(header) < idx + ext_len + 4:
                raise ValueError("文件头损坏")
            ext = header[idx:idx + ext_len].decode("utf-8", errors="ignore")
            idx += ext_len
            data_len = struct.unpack(">I", header[idx:idx + 4])[0]
            idx += 4
            data = header[idx:]
            if len(data) != data_len:
                raise ValueError("数据长度不匹配")
            if not has_pwd:
                return data, ext
            if not password:
                raise ValueError("此图片需要密码才能解码")
            import hashlib
            check_hash = hashlib.sha256((password + salt.hex()).encode("utf-8")).digest()
            if check_hash != pwd_hash:
                raise ValueError("密码错误，请重新输入")
            ks = SafeDecodeLogic.generate_key_stream(password, salt, len(data))
            plain = bytes(a ^ b for a, b in zip(data, ks))
            return plain, ext
        except Exception as e:
            raise Exception(f"解析文件头失败: {str(e)}")

    @staticmethod
    def binpng_bytes_to_mp4_bytes(p: str) -> bytes:
        try:
            img = Image.open(p).convert("RGB")
            arr = np.array(img).astype(np.uint8)
            flat = arr.reshape(-1, 3).reshape(-1)
            return flat.tobytes().rstrip(b"\x00")
        except Exception as e:
            raise Exception(f"转换视频格式失败: {str(e)}")

    @staticmethod
    def decode(image_path: str, password: str, output_dir: str, callback=None):
        try:
            if callback:
                callback("正在加载图片...")

            if not os.path.exists(image_path):
                raise FileNotFoundError(f"图片文件不存在: {image_path}")

            img = Image.open(image_path)
            arr = np.array(img.convert("RGB")).astype(np.uint8)

            if callback:
                callback("正在从图片中提取隐藏数据...")

            header = None
            raw = None
            ext = None
            last_err = None

            for k in (2, 6, 8):
                try:
                    header = SafeDecodeLogic.extract_payload_with_k(arr, k)
                    raw, ext = SafeDecodeLogic.parse_header(header, password)
                    break
                except Exception as e:
                    last_err = e
                    continue

            if raw is None:
                error_msg = str(last_err) if last_err else "无法从图片中提取隐藏数据"
                if "密码" in error_msg or "password" in error_msg.lower():
                    raise Exception("需要正确的密码才能解码此图片")
                raise Exception(f"解码失败: {error_msg}")

            if callback:
                callback("正在保存解码后的文件...")

            os.makedirs(output_dir, exist_ok=True)
            name = "duck_recovered"
            out_path = os.path.join(output_dir, name)

            try:
                if ext.endswith(".binpng"):
                    tmp_png = out_path + ".binpng"
                    with open(tmp_png, "wb") as f:
                        f.write(raw)
                    mp4_bytes = SafeDecodeLogic.binpng_bytes_to_mp4_bytes(tmp_png)
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
            except Exception as e:
                raise Exception(f"保存文件失败: {str(e)}")

            size = os.path.getsize(final_path)
            if size > 1024 * 1024:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            elif size > 1024:
                size_str = f"{size / 1024:.0f} KB"
            else:
                size_str = f"{size} 字节"

            return final_path, final_ext, size_str

        except Exception as e:
            raise Exception(f"解码过程出错: {str(e)}")


# ==================== 主应用 ====================

class DuckDecodeApp(App):
    def build(self):
        print("DuckDecode: build() started", file=sys.stderr)

        self.title = "Duck Decode"
        Window.softinput_mode = "below_target"

        # 主布局
        root = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))

        # 顶部标题
        header = BoxLayout(size_hint_y=None, height=dp(60))
        with header.canvas.before:
            Color(*PRIMARY)
            header.rect = Rectangle(pos=header.pos, size=header.size)

        def update_header(instance, value):
            instance.rect.pos = instance.pos
            instance.rect.size = instance.size
        header.bind(pos=update_header, size=update_header)

        title = ChineseLabel(
            text="🦆 鸭鸭解码器\n图片隐写解码工具",
            font_size=sp(18),
            color=(1, 1, 1, 1),
            bold=True,
            halign='center',
            valign='middle'
        )
        header.add_widget(title)
        root.add_widget(header)

        # 内容滚动区域
        scroll = ScrollView(do_scroll_x=False)
        content = BoxLayout(orientation='vertical', spacing=dp(15), padding=dp(15), size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        # 欢迎信息
        welcome = ChineseLabel(
            text="欢迎使用！请按照下方步骤操作",
            font_size=sp(16),
            color=TEXT_PRIMARY,
            size_hint_y=None,
            height=dp(40)
        )
        content.add_widget(welcome)

        # 步骤1：选择图片
        self.file_btn = ChineseButton(
            text="📱 步骤1：点击选择图片",
            font_size=sp(16),
            size_hint_y=None,
            height=dp(55),
            background_color=PRIMARY,
            color=(1, 1, 1, 1)
        )
        self.file_btn.bind(on_press=self.safe_select_file)
        content.add_widget(self.file_btn)

        self.file_status = ChineseLabel(
            text="未选择图片",
            font_size=sp(13),
            color=TEXT_SECONDARY,
            size_hint_y=None,
            height=dp(30)
        )
        content.add_widget(self.file_status)

        # 步骤2：输入密码
        pwd_label = ChineseLabel(
            text="🔐 步骤2：输入密码（可选）",
            font_size=sp(16),
            color=TEXT_PRIMARY,
            size_hint_y=None,
            height=dp(35)
        )
        content.add_widget(pwd_label)

        self.password_input = ChineseTextInput(
            hint_text='如果图片没有密码可以留空',
            password=True,
            password_mask='●',
            multiline=False,
            size_hint_y=None,
            height=dp(45),
            font_size=sp(16),
            background_normal='white',
            background_active='white',
            foreground_color=TEXT_PRIMARY,
            padding_x=dp(15),
            padding_y=dp(10)
        )
        content.add_widget(self.password_input)

        # 步骤3：开始解码
        self.decode_btn = ChineseButton(
            text="🚀 步骤3：开始解码",
            font_size=sp(18),
            size_hint_y=None,
            height=dp(60),
            background_color=PRIMARY,
            color=(1, 1, 1, 1),
            bold=True
        )
        self.decode_btn.bind(on_press=self.safe_start_decode)
        content.add_widget(self.decode_btn)

        # 进度显示
        self.status_label = ChineseLabel(
            text="",
            font_size=sp(14),
            color=TEXT_PRIMARY,
            size_hint_y=None,
            height=dp(50),
            halign='center',
            valign='middle'
        )
        content.add_widget(self.status_label)

        # 结果显示
        self.result_label = ChineseLabel(
            text="",
            font_size=sp(14),
            color=TEXT_PRIMARY,
            size_hint_y=None,
            height=dp(150),
            halign='center',
            valign='top'
        )
        content.add_widget(self.result_label)

        # 打开文件夹按钮
        self.open_btn = ChineseButton(
            text="📁 打开保存位置",
            font_size=sp(15),
            size_hint_y=None,
            height=dp(50),
            background_color=SUCCESS,
            color=(1, 1, 1, 1),
            disabled=True
        )
        self.open_btn.bind(on_press=self.safe_open_output_dir)
        content.add_widget(self.open_btn)

        # 帮助信息
        help_label = ChineseLabel(
            text="💡 使用提示\n"
                 "• 确保选择的是正确的隐写图片\n"
                 "• 如果有密码，请检查密码是否正确\n"
                 "• 解码后的文件保存在「图库/Pictures/DuckDecode」",
            font_size=sp(12),
            color=TEXT_SECONDARY,
            size_hint_y=None,
            height=dp(80),
            halign='left'
        )
        content.add_widget(help_label)

        # 版本信息
        version = ChineseLabel(
            text="🦆 鸭鸭解码器 v1.0.0",
            font_size=sp(11),
            color=TEXT_SECONDARY,
            size_hint_y=None,
            height=dp(30),
            halign='center'
        )
        content.add_widget(version)

        scroll.add_widget(content)
        root.add_widget(scroll)

        self.selected_file = None
        self.output_dir = self.get_default_output_dir()

        print("DuckDecode: build() complete", file=sys.stderr)
        return root

    def get_default_output_dir(self):
        try:
            if platform == 'android':
                from android.storage import primary_external_storage_path
                base_path = primary_external_storage_path()
                pictures_dir = os.path.join(base_path, "Pictures", "DuckDecode")
                os.makedirs(pictures_dir, exist_ok=True)
                return pictures_dir
            return os.getcwd()
        except:
            return "."

    def safe_select_file(self, instance):
        try:
            print("DuckDecode: Select file", file=sys.stderr)
            if platform == 'android':
                self.select_file_android()
            else:
                self.log("Enter image path:")
                self.selected_file = input("Path: ")
                if os.path.isfile(self.selected_file):
                    self.file_btn.text = "✓ 已选择图片"
                    self.file_status.text = os.path.basename(self.selected_file)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            self.show_error_dialog("选择文件失败", str(e))

    def select_file_android(self):
        try:
            from jnius import autoclass
            from android import activity

            Intent = autoclass('android.content.Intent')

            def on_activity_result(request_code, result_code, intent):
                if request_code == 1001 and result_code == -1:
                    try:
                        uri = intent.getData()
                        cr = autoclass('org.kivy.android.PythonActivity').mActivity.getContentResolver()
                        inp = cr.openInputStream(uri)
                        data = bytearray()
                        buf = bytearray(8192)
                        while True:
                            r = inp.read(buf, 0, 8192)
                            if r == -1:
                                break
                            data.extend(buf[:r])
                        inp.close()

                        import tempfile
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as f:
                            f.write(data)
                            self.selected_file = f.name

                        self.file_btn.text = "✓ 已选择图片"
                        self.file_btn.background_color = SUCCESS
                        self.file_status.text = os.path.basename(self.selected_file)[:40]
                        print(f"File: {self.selected_file}", file=sys.stderr)
                    except Exception as e:
                        print(f"Read error: {e}", file=sys.stderr)

            activity.bind(on_activity_result=on_activity_result)
            intent = Intent()
            intent.setAction(Intent.ACTION_GET_CONTENT)
            intent.setType("image/*")
            autoclass('org.kivy.android.PythonActivity').mActivity.startActivityForResult(intent, 1001)
        except Exception as e:
            print(f"Chooser error: {e}", file=sys.stderr)

    def safe_start_decode(self, instance):
        try:
            print("DuckDecode: Start decode", file=sys.stderr)

            if not self.selected_file:
                self.show_error_dialog("请先选择图片", "请点击上方按钮选择含有隐藏信息的图片")
                return

            password = self.password_input.text

            self.status_label.text = "正在解码..."
            self.decode_btn.disabled = True
            self.decode_btn.text = "解码中..."
            self.result_label.text = ""
            self.open_btn.disabled = True

            Clock.schedule_once(lambda dt: self.safe_do_decode(password), 0.1)
        except Exception as e:
            print(f"Start error: {e}", file=sys.stderr)
            self.decode_btn.disabled = False
            self.decode_btn.text = "开始解码"

    def safe_do_decode(self, password):
        try:
            print("DuckDecode: Decoding...", file=sys.stderr)

            result = SafeDecodeLogic.decode(
                self.selected_file, password, self.output_dir,
                callback=lambda msg: setattr(self.status_label, 'text', msg)
            )

            final_path, final_ext, size_str = result

            self.result_label.text = (
                f"🎉 解码成功！\n\n"
                f"文件名: {os.path.basename(final_path)}\n"
                f"文件类型: {final_ext.upper()}\n"
                f"文件大小: {size_str}\n"
                f"保存位置: 图库/Pictures/DuckDecode"
            )

            self.decode_btn.disabled = False
            self.decode_btn.text = "✓ 解码成功"
            self.decode_btn.background_color = SUCCESS
            self.open_btn.disabled = False

            self.show_success_dialog("解码成功", f"文件已保存到:\n图库/Pictures/DuckDecode\n\n文件名: {os.path.basename(final_path)}")

            Clock.schedule_once(lambda dt: self.reset_decode_btn(), 3)

        except Exception as e:
            print(f"Decode error: {e}", file=sys.stderr)
            self.status_label.text = "解码失败"
            self.decode_btn.disabled = False
            self.decode_btn.text = "重新解码"
            self.result_label.text = f"错误: {str(e)}"
            self.show_error_dialog("解码失败", str(e))

    def reset_decode_btn(self):
        self.decode_btn.text = "🚀 步骤3：开始解码"
        self.decode_btn.background_color = PRIMARY

    def safe_open_output_dir(self, instance):
        try:
            if platform == 'android':
                from jnius import autoclass
                Intent = autoclass('android.content.Intent')
                intent = Intent()
                intent.setAction(Intent.ACTION_VIEW)
                uri = autoclass('android.net.Uri').parse(f"file://{self.output_dir}")
                intent.setDataAndType(uri, "resource/folder")
                autoclass('org.kivy.android.PythonActivity').mActivity.startActivity(intent)
            else:
                import subprocess
                subprocess.Popen(f'explorer "{self.output_dir}"')
        except Exception as e:
            print(f"Open error: {e}", file=sys.stderr)
            self.show_error_dialog("打开失败", "请手动打开文件管理器查看:\n图库/Pictures/DuckDecode")

    def log(self, msg):
        print(msg, file=sys.stderr)

    def show_error_dialog(self, title, message):
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))

            icon = ChineseLabel(text="❌", font_size=sp(40), size_hint_y=None, height=dp(50), halign='center')
            msg = ChineseLabel(text=message, font_size=sp(14), size_hint_y=None, height=dp(100), halign='center')
            btn = ChineseButton(text="我知道了", size_hint_y=None, height=dp(45), font_size=sp(16))

            content.add_widget(icon)
            content.add_widget(msg)
            content.add_widget(btn)

            popup = Popup(title=title, title_font_size=sp(18), title_color=ERROR,
                          content=content, size_hint=(0.9, 0.45), auto_dismiss=False)

            btn.bind(on_press=lambda x: popup.dismiss())
            popup.open()
        except Exception as e:
            print(f"Dialog error: {e}", file=sys.stderr)

    def show_success_dialog(self, title, message):
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))

            icon = ChineseLabel(text="✅", font_size=sp(40), size_hint_y=None, height=dp(50), halign='center')
            msg = ChineseLabel(text=message, font_size=sp(14), size_hint_y=None, height=dp(100), halign='center')
            btn = ChineseButton(text="太好了！", size_hint_y=None, height=dp(45), font_size=sp(16),
                               background_color=SUCCESS, color=(1,1,1,1))

            content.add_widget(icon)
            content.add_widget(msg)
            content.add_widget(btn)

            popup = Popup(title=title, title_font_size=sp(18), title_color=SUCCESS,
                          content=content, size_hint=(0.9, 0.45), auto_dismiss=False)

            btn.bind(on_press=lambda x: popup.dismiss())
            popup.open()
        except Exception as e:
            print(f"Dialog error: {e}", file=sys.stderr)


if __name__ == "__main__":
    try:
        print("DuckDecode: Starting...", file=sys.stderr)
        DuckDecodeApp().run()
    except Exception as e:
        print(f"Fatal: {e}", file=sys.stderr)
        traceback.print_exc()
