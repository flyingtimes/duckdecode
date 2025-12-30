#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Duck Decode Android - Steganography Decoder Tool
Modern Material Design - Enhanced UI/UX
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
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.modalview import ModalView
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.properties import NumericProperty, StringProperty
from kivy.metrics import dp, sp
from kivy.animation import Animation

# Android Chinese font path
ANDROID_CHINESE_FONT = '/system/fonts/NotoSansCJK-Regular.ttc'
ANDROID_FALLBACK_FONT = '/system/fonts/DroidSansFallback.ttf'

# Material Design Colors
MD_PRIMARY = (0.26, 0.35, 0.76, 1)      # Deep Blue
MD_PRIMARY_DARK = (0.13, 0.22, 0.63, 1)  # Darker Blue
MD_ACCENT = (0.26, 0.61, 0.76, 1)        # Cyan
MD_SUCCESS = (0.20, 0.73, 0.33, 1)       # Green
MD_WARNING = (0.98, 0.58, 0.00, 1)       # Orange
MD_ERROR = (0.94, 0.33, 0.33, 1)         # Red
MD_BACKGROUND = (0.97, 0.97, 1.0, 1)     # Light Gray
MD_SURFACE = (1.0, 1.0, 1.0, 1)          # White
MD_TEXT_PRIMARY = (0.13, 0.13, 0.13, 1)  # Dark Gray
MD_TEXT_SECONDARY = (0.60, 0.60, 0.60, 1) # Medium Gray
MD_DIVIDER = (0.91, 0.91, 0.91, 1)       # Light Divider


def get_chinese_font():
    """获取支持中文的字体"""
    if platform == 'android':
        if os.path.exists(ANDROID_CHINESE_FONT):
            return ANDROID_CHINESE_FONT
        elif os.path.exists(ANDROID_FALLBACK_FONT):
            return ANDROID_FALLBACK_FONT
    return 'Roboto'


CHINESE_FONT = get_chinese_font()


# 全局错误捕获
def global_exception_handler(exc_type, exc_value, exc_traceback):
    """全局异常处理器"""
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print("CRITICAL ERROR:", error_msg, file=sys.stderr)
    try:
        log_path = os.path.join(App.get_running_app().user_data_dir, "error_log.txt")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{error_msg}")
    except:
        pass


sys.excepthook = global_exception_handler

CATEGORY = "SSTool"
WATERMARK_SKIP_W_RATIO = 0.40
WATERMARK_SKIP_H_RATIO = 0.08


# ==================== 自定义 UI 组件 ====================

class ChineseLabel(Label):
    """支持中文的Label"""
    def __init__(self, **kwargs):
        kwargs['font_name'] = CHINESE_FONT
        super().__init__(**kwargs)


class ChineseButton(Button):
    """支持中文的Button"""
    def __init__(self, **kwargs):
        kwargs['font_name'] = CHINESE_FONT
        super().__init__(**kwargs)


class ChineseTextInput(TextInput):
    """支持中文的TextInput"""
    def __init__(self, **kwargs):
        kwargs['font_name'] = CHINESE_FONT
        super().__init__(**kwargs)


class MDCard(BoxLayout):
    """Material Design 卡片组件"""
    elevation = NumericProperty(2)
    radius = NumericProperty([12])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.padding = dp(16)
        self.spacing = dp(12)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.canvas.before.clear()
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            # 阴影效果
            Color(0.85, 0.85, 0.9, 0.3)
            self.shadow_rect = RoundedRectangle(
                pos=(self.pos[0] + dp(2), self.pos[1] - dp(2)),
                size=self.size,
                radius=self.radius
            )
            # 卡片背景
            Color(*MD_SURFACE)
            self.bg_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=self.radius
            )
            # 边框
            Color(*MD_DIVIDER)
            self.border_rect = Line(
                rectangle=[self.pos[0], self.pos[1], self.size[0], self.size[1]],
                width=dp(0.5),
                rounded_rectangle=[self.pos[0], self.pos[1], self.size[0], self.size[1], *self.radius]
            )


class MDButton(Button):
    """Material Design 按钮"""
    style = StringProperty('primary')  # primary, secondary, success, error, text

    def __init__(self, **kwargs):
        kwargs['font_name'] = CHINESE_FONT
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.background_normal = ''
        self.color = MD_SURFACE
        self.font_size = sp(16)
        self.bold = True
        self.size_hint_y = None
        self.height = dp(48)
        self.canvas.before.clear()
        self.bind(pos=self.update_canvas, size=self.update_canvas, on_press=self.on_press_down, on_release=self.on_press_up)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.style == 'primary':
                Color(*MD_PRIMARY)
            elif self.style == 'secondary':
                Color(*MD_ACCENT)
            elif self.style == 'success':
                Color(*MD_SUCCESS)
            elif self.style == 'error':
                Color(*MD_ERROR)
            else:
                Color(0, 0, 0, 0)
                Color(*MD_DIVIDER)

            bg_color = MD_PRIMARY if self.style == 'primary' else (
                MD_ACCENT if self.style == 'secondary' else (
                    MD_SUCCESS if self.style == 'success' else (
                        MD_ERROR if self.style == 'error' else MD_DIVIDER
                    )
                )
            )

            if self.style == 'text':
                Color(0, 0, 0, 0)
            else:
                Color(*bg_color)

            self.bg_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(8)]
            )

            # 涟漪效果
            if self.state == 'down':
                Color(1, 1, 1, 0.2)
                self.ripple = RoundedRectangle(
                    pos=self.pos,
                    size=self.size,
                    radius=[dp(8)]
                )

    def on_press_down(self, instance):
        anim = Animation(opacity=0.8, duration=0.1)
        anim.start(self)

    def on_press_up(self, instance):
        anim = Animation(opacity=1.0, duration=0.2)
        anim.start(self)


class MDTextField(BoxLayout):
    """Material Design 文本输入框"""
    hint_text = StringProperty('')
    text_value = StringProperty('')
    is_password = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(72)
        self.spacing = dp(4)
        self.padding = (dp(12), 0)

        # 标签/提示
        self.label = ChineseLabel(
            text=kwargs.get('hint_text', ''),
            font_size=sp(12),
            color=MD_TEXT_SECONDARY,
            size_hint_y=None,
            height=dp(20)
        )
        self.add_widget(self.label)

        # 输入框容器
        input_container = BoxLayout(size_hint_y=None, height=dp(48))
        input_container.canvas.before.clear()
        input_container.bind(pos=self.update_input_canvas, size=self.update_input_canvas)

        # 实际输入框
        self.text_input = ChineseTextInput(
            hint_text=kwargs.get('hint_text', ''),
            password=kwargs.get('password', False),
            password_mask='●',
            multiline=False,
            size_hint=(1, 1),
            background_color=(0, 0, 0, 0),
            foreground_color=MD_TEXT_PRIMARY,
            font_size=sp(16),
            padding_x=dp(12),
            padding_y=dp(12)
        )
        input_container.add_widget(self.text_input)
        self.add_widget(input_container)

        # 存储容器引用
        self.input_container = input_container

    def update_input_canvas(self, *args):
        self.input_container.canvas.before.clear()
        with self.input_container.canvas.before:
            Color(*MD_DIVIDER)
            self.line = Line(
                points=[
                    self.input_container.x, self.input_container.y,
                    self.input_container.right, self.input_container.y
                ],
                width=dp(1)
            )
            Color(*MD_PRIMARY)
            self.active_line = Line(
                points=[
                    self.input_container.x, self.input_container.y,
                    self.input_container.center_x, self.input_container.y
                ],
                width=dp(2)
            )

    @property
    def text(self):
        return self.text_input.text

    @text.setter
    def text(self, value):
        self.text_input.text = value


class MDProgressBar(ProgressBar):
    """Material Design 进度条"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(4)
        self.max = 100
        self.value = 0
        self.canvas.before.clear()
        self.bind(pos=self.update_canvas, size=self.update_canvas, value=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            # 背景轨道
            Color(0.88, 0.88, 0.9, 1)
            RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(2)]
            )
            # 进度条
            if self.value > 0:
                Color(*MD_PRIMARY)
                progress_width = self.width * (self.value / self.max)
                RoundedRectangle(
                    pos=self.pos,
                    size=(progress_width, self.height),
                    radius=[dp(2)]
                )


class MDIconLabel(BoxLayout):
    """带图标的标签"""
    def __init__(self, icon='', text='', **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.spacing = dp(8)
        self.size_hint_y = None
        self.height = dp(24)

        self.icon_label = ChineseLabel(
            text=icon,
            font_size=sp(20),
            color=MD_PRIMARY,
            size_hint_x=None,
            width=dp(24)
        )
        self.text_label = ChineseLabel(
            text=text,
            font_size=sp(14),
            color=MD_TEXT_PRIMARY,
            markup=True
        )
        self.add_widget(self.icon_label)
        self.add_widget(self.text_label)


class MDSnackbar(BoxLayout):
    """Material Design Snackbar 提示"""
    def __init__(self, message='', duration=3, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_x = 0.9
        self.size_hint_y = None
        self.height = dp(48)
        self.pos_hint = {'center_x': 0.5, 'y': dp(16)}
        self.padding = dp(16)
        self.canvas.before.clear()
        self.bind(pos=self.update_canvas, size=self.update_canvas)

        self.message_label = ChineseLabel(
            text=message,
            font_size=sp(14),
            color=(1, 1, 1, 1),
            size_hint_x=1
        )
        self.add_widget(self.message_label)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.2, 0.2, 0.2, 0.9)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(4)])

    def show(self, parent_widget):
        parent_widget.add_widget(self)
        Clock.schedule_once(lambda dt: self.dismiss(), 3)

    def dismiss(self):
        parent = self.parent
        if parent:
            parent.remove_widget(self)


# ==================== 解码逻辑 ====================

class SafeDecodeLogic:
    """安全的解码逻辑类"""

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
        """执行解码"""
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
    """主应用类 - 现代设计版"""

    def build(self):
        self.title = "Duck Decode"
        Window.softinput_mode = "below_target"
        Window.clearcolor = MD_BACKGROUND

        # 主布局
        root = BoxLayout(orientation='vertical')

        # AppBar
        appbar = BoxLayout(size_hint_y=None, height=dp(56), padding=[dp(16), 0])
        appbar.canvas.before.clear()
        with appbar.canvas.before:
            Color(*MD_PRIMARY)
            appbar.bg = Rectangle(pos=appbar.pos, size=appbar.size)
        appbar.bind(pos=self.update_appbar, size=self.update_appbar)

        title_layout = BoxLayout(orientation='vertical', spacing=dp(2))
        app_title = ChineseLabel(
            text="🦆 鸭鸭解码器",
            font_size=sp(20),
            color=(1, 1, 1, 1),
            bold=True,
            size_hint_y=None,
            height=dp(28)
        )
        app_subtitle = ChineseLabel(
            text="图片隐写解码工具",
            font_size=sp(12),
            color=(0.9, 0.9, 1, 1),
            size_hint_y=None,
            height=dp(18)
        )
        title_layout.add_widget(app_title)
        title_layout.add_widget(app_subtitle)
        appbar.add_widget(title_layout)
        root.add_widget(appbar)

        # 内容区域
        content_scroll = ScrollView(do_scroll_x=False)
        content_layout = BoxLayout(orientation='vertical', spacing=dp(16), padding=dp(16), size_hint_y=None)
        content_layout.bind(minimum_height=content_layout.setter('height'))

        # 欢迎卡片
        welcome_card = MDCard(size_hint_y=None, height=dp(80))
        welcome_label = ChineseLabel(
            text="[color=%s]欢迎使用！[/color]\n请按照下方步骤操作" % self._rgb_to_hex(MD_TEXT_PRIMARY),
            font_size=sp(14),
            markup=True,
            size_hint_y=None,
            height=dp(48)
        )
        welcome_card.add_widget(welcome_label)
        content_layout.add_widget(welcome_card)

        # 步骤1：选择图片
        step1_card = MDCard(size_hint_y=None, height=dp(110))
        step1_header = MDIconLabel(
            icon='📱',
            text="[b]步骤1：选择图片[/b]",
            size_hint_y=None,
            height=dp(28)
        )
        self.file_btn = MDButton(
            text="点击选择图片",
            style='primary',
            size_hint_y=None,
            height=dp(48)
        )
        self.file_btn.bind(on_press=self.safe_select_file)
        self.file_status = ChineseLabel(
            text="未选择图片",
            font_size=sp(12),
            color=MD_TEXT_SECONDARY,
            size_hint_y=None,
            height=dp(20)
        )
        step1_card.add_widget(step1_header)
        step1_card.add_widget(self.file_btn)
        step1_card.add_widget(self.file_status)
        content_layout.add_widget(step1_card)

        # 步骤2：输入密码
        step2_card = MDCard(size_hint_y=None, height=dp(100))
        step2_header = MDIconLabel(
            icon='🔐',
            text="[b]步骤2：输入密码（可选）[/b]",
            size_hint_y=None,
            height=dp(28)
        )
        self.password_field = MDTextField(
            hint_text='如果图片没有密码可以留空',
            password=False
        )
        # 添加密码可见性切换
        self.password_field.text_input.password = True
        step2_card.add_widget(step2_header)
        step2_card.add_widget(self.password_field)
        content_layout.add_widget(step2_card)

        # 步骤3：开始解码
        step3_card = MDCard(size_hint_y=None, height=dp(100))
        step3_header = MDIconLabel(
            icon='🚀',
            text="[b]步骤3：开始解码[/b]",
            size_hint_y=None,
            height=dp(28)
        )
        self.decode_btn = MDButton(
            text='开始解码',
            style='primary',
            size_hint_y=None,
            height=dp(56)
        )
        self.decode_btn.bind(on_press=self.safe_start_decode)
        step3_card.add_widget(step3_header)
        step3_card.add_widget(self.decode_btn)
        content_layout.add_widget(step3_card)

        # 进度条
        self.progress_card = MDCard(size_hint_y=None, height=dp(60))
        self.progress_card.opacity = 0
        progress_label = ChineseLabel(
            text="解码进度",
            font_size=sp(12),
            color=MD_TEXT_SECONDARY,
            size_hint_y=None,
            height=dp(20)
        )
        self.progress_bar = MDProgressBar(size_hint_y=None, height=dp(8))
        self.progress_label = ChineseLabel(
            text="准备中...",
            font_size=sp(12),
            color=MD_TEXT_PRIMARY,
            size_hint_y=None,
            height=dp(20)
        )
        self.progress_card.add_widget(progress_label)
        self.progress_card.add_widget(self.progress_bar)
        self.progress_card.add_widget(self.progress_label)
        content_layout.add_widget(self.progress_card)

        # 结果卡片
        self.result_card = MDCard(size_hint_y=None, height=dp(0))
        self.result_card.opacity = 0
        result_header = MDIconLabel(
            icon='📊',
            text="[b]解码结果[/b]",
            size_hint_y=None,
            height=dp(28)
        )
        self.result_label = ChineseLabel(
            text="",
            font_size=sp(13),
            color=MD_TEXT_PRIMARY,
            markup=True,
            size_hint_y=None,
            height=dp(100)
        )
        self.open_btn = MDButton(
            text='打开保存位置',
            style='secondary',
            size_hint_y=None,
            height=dp(48)
        )
        self.open_btn.bind(on_press=self.safe_open_output_dir)
        self.result_card.add_widget(result_header)
        self.result_card.add_widget(self.result_label)
        self.result_card.add_widget(self.open_btn)
        content_layout.add_widget(self.result_card)

        # 帮助卡片
        help_card = MDCard(size_hint_y=None, height=dp(90))
        help_label = ChineseLabel(
            text="[color=%s][b]💡 使用提示[/b][/color]\n"
                  "• 确保选择的是正确的隐写图片\n"
                  "• 如果有密码，请检查密码是否正确\n"
                  "• 解码后的文件保存在「图库/Pictures/DuckDecode」" % self._rgb_to_hex(MD_PRIMARY),
            font_size=sp(12),
            markup=True,
            size_hint_y=None,
            height=dp(70)
        )
        help_card.add_widget(help_label)
        content_layout.add_widget(help_card)

        # 版本信息
        version_label = ChineseLabel(
            text="🦆 鸭鸭解码器 v1.0.0",
            font_size=sp(11),
            color=MD_TEXT_SECONDARY,
            size_hint_y=None,
            height=dp(30),
            halign='center'
        )
        content_layout.add_widget(version_label)

        content_scroll.add_widget(content_layout)
        root.add_widget(content_scroll)

        self.selected_file = None
        self.output_dir = self.get_default_output_dir()
        self.snackbar_queue = []

        # 欢迎消息
        Clock.schedule_once(self.show_welcome, 0.5)

        return root

    def _rgb_to_hex(self, rgb):
        """将RGB颜色转换为十六进制"""
        return '#%02x%02x%02x' % (int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))

    def update_appbar(self, instance, value):
        instance.bg.pos = instance.pos
        instance.bg.size = instance.size

    def show_welcome(self, dt):
        """显示欢迎消息"""
        self.show_snackbar("欢迎使用鸭鸭解码器！")

    def get_default_output_dir(self):
        """获取默认输出目录"""
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
        """安全的选择文件"""
        try:
            if platform == 'android':
                self.select_file_android()
            else:
                self.select_file_desktop()
        except Exception as e:
            self.show_snackbar(f"选择文件失败: {str(e)}")
            self.show_error_dialog("选择文件失败", str(e))

    def select_file_android(self):
        """Android文件选择"""
        try:
            from jnius import autoclass
            from android import activity

            Intent = autoclass('android.content.Intent')

            def on_activity_result(request_code, result_code, intent):
                if request_code == 1001:
                    if result_code == -1:
                        try:
                            uri = intent.getData()
                            content_resolver = autoclass('org.kivy.android.PythonActivity').mActivity.getContentResolver()

                            input_stream = content_resolver.openInputStream(uri)
                            data = bytearray()
                            buffer = bytearray(8192)
                            while True:
                                read = input_stream.read(buffer, 0, 8192)
                                if read == -1:
                                    break
                                data.extend(buffer[:read])
                            input_stream.close()

                            import tempfile
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as f:
                                f.write(data)
                                self.selected_file = f.name

                            self.file_btn.text = "✓ 已选择图片"
                            self.file_btn.style = 'success'
                            self.file_status.text = f"文件: {os.path.basename(self.selected_file)[:40]}"
                            self.file_status.color = MD_SUCCESS
                            self.show_snackbar("图片选择成功！")

                        except Exception as e:
                            self.show_snackbar(f"读取图片失败: {str(e)}")

            activity.bind(on_activity_result=on_activity_result)

            intent = Intent()
            intent.setAction(Intent.ACTION_GET_CONTENT)
            intent.setType("image/*")
            current_activity = autoclass('org.kivy.android.PythonActivity').mActivity
            current_activity.startActivityForResult(intent, 1001)

        except Exception as e:
            self.show_snackbar(f"打开文件选择器失败: {str(e)}")

    def select_file_desktop(self):
        """桌面端文件选择"""
        try:
            self.log("请输入图片文件路径:")
            self.selected_file = input("Enter image path: ")
            if os.path.isfile(self.selected_file):
                self.file_btn.text = "✓ 已选择图片"
                self.file_status.text = f"文件: {os.path.basename(self.selected_file)}"
            else:
                self.show_snackbar("文件不存在")
        except Exception as e:
            self.show_snackbar(f"错误: {str(e)}")

    def safe_start_decode(self, instance):
        """安全地开始解码"""
        try:
            if not self.selected_file:
                self.show_error_dialog("请先选择图片", "请点击上方按钮选择含有隐藏信息的图片")
                return

            if not os.path.isfile(self.selected_file):
                self.show_error_dialog("文件不存在", "选择的文件找不到了，请重新选择")
                return

            password = self.password_field.text

            # 显示进度
            self.progress_card.opacity = 1
            self.progress_card.height = dp(60)
            self.progress_bar.value = 0
            self.progress_label.text = "正在解码..."

            # 禁用按钮
            self.decode_btn.disabled = True
            self.decode_btn.text = "解码中..."

            # 隐藏之前的结果
            self.result_card.opacity = 0
            self.result_card.height = dp(0)

            Clock.schedule_once(lambda dt: self.safe_do_decode(password), 0.1)

        except Exception as e:
            self.decode_btn.disabled = False
            self.decode_btn.text = "开始解码"
            self.show_snackbar(f"启动解码失败: {str(e)}")

    def safe_do_decode(self, password):
        """安全地执行解码"""
        try:
            def progress_callback(msg):
                self.progress_label.text = msg
                if "加载" in msg:
                    self.progress_bar.value = 20
                elif "提取" in msg:
                    self.progress_bar.value = 50
                elif "保存" in msg:
                    self.progress_bar.value = 80

            result = SafeDecodeLogic.decode(
                self.selected_file,
                password,
                self.output_dir,
                callback=progress_callback
            )

            final_path, final_ext, size_str = result
            self.progress_bar.value = 100
            self.progress_label.text = "解码完成！"

            # 显示结果
            self.result_label.text = (
                f"[color=%s]🎉 解码成功！[/color]\n\n"
                f"[b]文件名:[/b] {os.path.basename(final_path)}\n"
                f"[b]文件类型:[/b] {final_ext.upper()}\n"
                f"[b]文件大小:[/b] {size_str}\n"
                f"[b]保存位置:[/b] 图库/Pictures/DuckDecode" % self._rgb_to_hex(MD_SUCCESS)
            )
            self.result_card.height = dp(180)
            self.result_card.opacity = 1

            self.decode_btn.disabled = False
            self.decode_btn.text = "✓ 解码成功"
            self.decode_btn.style = 'success'

            self.show_snackbar("解码成功！文件已保存")
            self.show_success_dialog("🎉 解码成功！", f"文件已保存到:\n图库/Pictures/DuckDecode\n\n文件名: {os.path.basename(final_path)}")

            # 3秒后重置按钮
            Clock.schedule_once(lambda dt: self.reset_decode_button(), 3)

        except Exception as e:
            self.progress_label.text = "解码失败"
            self.decode_btn.disabled = False
            self.decode_btn.text = "重新解码"
            self.decode_btn.style = 'primary'

            error_msg = str(e)
            self.show_snackbar("解码失败")
            self.show_error_dialog("解码失败", error_msg)

    def reset_decode_button(self):
        """重置解码按钮"""
        self.decode_btn.text = "开始解码"
        self.decode_btn.style = 'primary'

    def safe_open_output_dir(self, instance):
        """安全地打开输出目录"""
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
            self.show_snackbar("正在打开文件夹...")
        except Exception as e:
            self.show_snackbar("打开文件夹失败")
            self.show_error_dialog("打开文件夹失败", "请手动打开文件管理器查看:\n图库/Pictures/DuckDecode")

    def log(self, message):
        """添加日志"""
        print(message)

    def show_snackbar(self, message):
        """显示Snackbar提示"""
        try:
            snackbar = MDSnackbar(message=message)
            content = self.root.children[0].children[1]  # 获取ScrollView
            snackbar.show(content)
        except:
            pass

    def show_error_dialog(self, title, message):
        """显示错误对话框"""
        try:
            popup_layout = BoxLayout(orientation='vertical', padding=dp(24), spacing=dp(16))

            icon_label = ChineseLabel(
                text="❌",
                font_size=sp(48),
                size_hint_y=None,
                height=dp(60),
                halign='center'
            )

            msg_label = ChineseLabel(
                text=message,
                font_size=sp(14),
                text_size=(dp(280), None),
                halign='center',
                color=MD_TEXT_PRIMARY,
                size_hint_y=None,
                height=dp(100)
            )

            close_btn = MDButton(
                text="我知道了",
                style='primary',
                size_hint_y=None,
                height=dp(48)
            )

            popup_layout.add_widget(icon_label)
            popup_layout.add_widget(msg_label)
            popup_layout.add_widget(close_btn)

            popup = Popup(
                title=title,
                title_font_size=sp(20),
                title_align='center',
                title_color=MD_ERROR,
                content=popup_layout,
                size_hint=(0.9, 0.5),
                separator_color=MD_ERROR,
                auto_dismiss=False
            )

            def dismiss_popup(*args):
                try:
                    popup.dismiss()
                except:
                    pass

            close_btn.bind(on_press=dismiss_popup)
            popup.open()
        except Exception as e:
            print(f"Error showing dialog: {e}")

    def show_success_dialog(self, title, message):
        """显示成功对话框"""
        try:
            popup_layout = BoxLayout(orientation='vertical', padding=dp(24), spacing=dp(16))

            icon_label = ChineseLabel(
                text="✅",
                font_size=sp(48),
                size_hint_y=None,
                height=dp(60),
                halign='center'
            )

            msg_label = ChineseLabel(
                text=message,
                font_size=sp(14),
                text_size=(dp(280), None),
                halign='center',
                color=MD_TEXT_PRIMARY,
                size_hint_y=None,
                height=dp(100)
            )

            close_btn = MDButton(
                text="太好了！",
                style='success',
                size_hint_y=None,
                height=dp(48)
            )

            popup_layout.add_widget(icon_label)
            popup_layout.add_widget(msg_label)
            popup_layout.add_widget(close_btn)

            popup = Popup(
                title=title,
                title_font_size=sp(20),
                title_align='center',
                title_color=MD_SUCCESS,
                content=popup_layout,
                size_hint=(0.9, 0.5),
                separator_color=MD_SUCCESS,
                auto_dismiss=False
            )

            def dismiss_popup(*args):
                try:
                    popup.dismiss()
                except:
                    pass

            close_btn.bind(on_press=dismiss_popup)
            popup.open()
        except Exception as e:
            print(f"Error showing dialog: {e}")


if __name__ == "__main__":
    try:
        DuckDecodeApp().run()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
