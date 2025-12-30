#!/usr/bin/env python3
"""
Duck Decode Android - 隐写解码移动端工具
从图片中解码隐藏的文件内容
Modern Material Design Style - Elderly Friendly
"""
import os
import sys
import struct
import traceback
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
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.properties import NumericProperty

# 全局错误捕获
def global_exception_handler(exc_type, exc_value, exc_traceback):
    """全局异常处理器"""
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print("CRITICAL ERROR:", error_msg, file=sys.stderr)
    # 尝试写入错误日志文件
    try:
        log_path = os.path.join(App.get_running_app().user_data_dir, "error_log.txt")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(error_msg)
    except:
        pass

sys.excepthook = global_exception_handler

CATEGORY = "SSTool"
WATERMARK_SKIP_W_RATIO = 0.40
WATERMARK_SKIP_H_RATIO = 0.08


class RoundedButton(Button):
    """圆角按钮 - 老人友好的大按钮"""
    radius = NumericProperty(25)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.background_normal = ''
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.3, 0.6, 1, 1)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size


class CardLayout(BoxLayout):
    """卡片式布局"""
    radius = NumericProperty(20)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.padding = 25
        self.spacing = 15
        self.orientation = 'vertical'
        self.canvas.before.clear()
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
            Color(0.93, 0.93, 0.96, 1)
            self.border_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.border_rect.pos = self.pos
        self.border_rect.size = self.size


class MaterialLabel(Label):
    """Material风格标签"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.color = (0.15, 0.15, 0.15, 1)
        self.markup = True
        self.halign = 'left'
        self.valign = 'middle'


class SafeDecodeLogic:
    """安全的解码逻辑类 - 带完整错误处理"""

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
        """执行解码 - 安全版本"""
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

            # 尝试不同的位数
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
                raise Exception(f"解码失败: {error_msg}\n\n请确保这是正确的隐写图片")

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


class DuckDecodeApp(App):
    """主应用类 - 老人友好版"""

    def build(self):
        self.title = "Duck Decode"
        Window.softinput_mode = "below_target"

        # 设置背景色
        Window.clearcolor = (0.94, 0.94, 0.97, 1)

        # 主布局
        root = BoxLayout(orientation='vertical')

        # 顶部标题栏 - 更大更醒目
        header = BoxLayout(size_hint_y=None, height=100, padding=20, spacing=10)
        with header.canvas.before:
            Color(0.25, 0.55, 0.95, 1)
            header.rect = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=self.update_header_rect, size=self.update_header_rect)

        title_layout = BoxLayout(orientation='vertical', size_hint_x=1)
        app_title = Label(
            text="🦆 鸭鸭解码器",
            font_size='36sp',
            color=(1, 1, 1, 1),
            bold=True,
            size_hint_y=None,
            height=55
        )
        app_subtitle = Label(
            text="图片隐写解码工具 · 简单易用",
            font_size='14sp',
            color=(0.95, 0.95, 1, 1),
            size_hint_y=None,
            height=25
        )
        title_layout.add_widget(app_title)
        title_layout.add_widget(app_subtitle)
        header.add_widget(title_layout)
        root.add_widget(header)

        # 内容区域 - 可滚动
        content_scroll = ScrollView(do_scroll_x=False)
        content_layout = BoxLayout(orientation='vertical', spacing=20, padding=20, size_hint_y=None)
        content_layout.bind(minimum_height=content_layout.setter('height'))

        # 说明卡片
        info_card = CardLayout(size_hint_y=None, height=80)
        info_label = MaterialLabel(
            text="[size=18][b]使用说明[/b][/size]\n[size=14]1. 点击下方蓝色按钮选择图片\n2. 如果需要密码，输入密码\n3. 点击「开始解码」按钮[/size]",
            font_size='13sp',
            size_hint_y=None,
            height=60
        )
        info_card.add_widget(info_label)
        content_layout.add_widget(info_card)

        # 选择文件卡片 - 更大
        file_card = CardLayout(size_hint_y=None, height=150)
        file_label = MaterialLabel(
            text="[size=20][b]第一步：选择图片[/b][/size]",
            font_size='16sp',
            size_hint_y=None,
            height=35
        )
        self.file_btn = Button(
            text="📱\n点击这里选择图片\n\n请在相册中选择含有隐藏信息的图片",
            font_size='18sp',
            size_hint_y=None,
            height=90,
            background_color=(0.88, 0.88, 0.92, 1),
            color=(0.25, 0.25, 0.25, 1)
        )
        self.file_btn.bind(on_press=self.safe_select_file)
        file_card.add_widget(file_label)
        file_card.add_widget(self.file_btn)
        content_layout.add_widget(file_card)

        # 密码卡片 - 更大
        pwd_card = CardLayout(size_hint_y=None, height=140)
        pwd_label = MaterialLabel(
            text="[size=20][b]第二步：输入密码（如果需要）[/b][/size]",
            font_size='16sp',
            size_hint_y=None,
            height=35
        )
        pwd_hint = MaterialLabel(
            text="💡 如果图片没有设置密码，可以跳过此步骤",
            font_size='14sp',
            color=(0.5, 0.5, 0.5, 1),
            size_hint_y=None,
            height=25
        )
        self.password_input = TextInput(
            hint_text="请输入密码（如果不需要密码请留空）",
            password=True,
            password_mask="●",
            multiline=False,
            size_hint_y=None,
            height=55,
            font_size='20sp',
            background_color=(0.98, 0.98, 1, 1),
            foreground_color=(0.2, 0.2, 0.2, 1),
            padding_x=20,
            padding_y=15,
            focus=True
        )
        pwd_card.add_widget(pwd_label)
        pwd_card.add_widget(pwd_hint)
        pwd_card.add_widget(self.password_input)
        content_layout.add_widget(pwd_card)

        # 解码按钮 - 超大
        self.decode_btn = RoundedButton(
            text="🔙\n\n开始解码\n\n点击这里开始从图片中提取隐藏的文件",
            font_size='22sp',
            bold=True,
            size_hint_y=None,
            height=140,
            color=(1, 1, 1, 1)
        )
        self.decode_btn.bind(on_press=self.safe_start_decode)
        content_layout.add_widget(self.decode_btn)

        # 日志区域 - 更大字体
        log_card = CardLayout(size_hint_y=None, height=220)
        log_header = MaterialLabel(
            text="[size=18][b]解码进度与结果[/b][/size]",
            font_size='15sp',
            size_hint_y=None,
            height=30
        )
        self.log_text = TextInput(
            readonly=True,
            font_size='16sp',
            size_hint_y=None,
            height=170,
            background_color=(0.98, 0.98, 1, 1),
            foreground_color=(0.25, 0.25, 0.25, 1),
            padding_x=15,
            padding_y=10,
            text="等待开始解码...\n\n请先选择图片，然后点击「开始解码」按钮"
        )
        log_card.add_widget(log_header)
        log_card.add_widget(self.log_text)
        content_layout.add_widget(log_card)

        # 打开输出目录按钮 - 更大
        self.open_btn = RoundedButton(
            text="📁\n\n打开文件位置\n\n查看解码后的文件保存在哪里",
            font_size='18sp',
            size_hint_y=None,
            height=100,
            disabled=True,
            color=(1, 1, 1, 1)
        )
        self.open_btn.canvas.before.clear()
        with self.open_btn.canvas.before:
            Color(0.5, 0.5, 0.5, 1)
            self.open_btn.bg_rect = RoundedRectangle(pos=self.open_btn.pos, size=self.open_btn.size, radius=[25])
        self.open_btn.bind(pos=self.open_btn.update_rect, size=self.open_btn.update_rect)
        self.open_btn.bind(on_press=self.safe_open_output_dir)
        content_layout.add_widget(self.open_btn)

        # 底部帮助信息
        help_card = CardLayout(size_hint_y=None, height=80)
        help_text = MaterialLabel(
            text="[size=14][b]遇到问题？[/b][/size]\n[size=13]• 确保选择的是正确的隐写图片\n• 检查密码是否正确\n• 查看上方的进度信息了解详情[/size]",
            font_size='12sp',
            size_hint_y=None,
            height=60
        )
        help_card.add_widget(help_text)
        content_layout.add_widget(help_card)

        # 版本信息
        version_label = Label(
            text="🦆 鸭鸭解码器 v1.0.0 | 简单易用的隐写解码工具",
            font_size='13sp',
            color=(0.5, 0.5, 0.5, 1),
            size_hint_y=None,
            height=40
        )
        content_layout.add_widget(version_label)

        content_scroll.add_widget(content_layout)
        root.add_widget(content_scroll)

        self.selected_file = None
        self.output_dir = self.get_default_output_dir()

        # 启动时的欢迎提示
        Clock.schedule_once(self.show_welcome, 1)

        return root

    def show_welcome(self, dt):
        """显示欢迎信息"""
        self.log_text.text = "👋 欢迎使用鸭鸭解码器！\n\n使用方法很简单：\n1️⃣ 先点击上方蓝色按钮选择图片\n2️⃣ 如有密码请输入\n3️⃣ 点击大按钮「开始解码」\n\n准备好了吗？开始吧！"

    def update_header_rect(self, instance, value):
        instance.rect.pos = instance.pos
        instance.rect.size = instance.size

    def get_default_output_dir(self):
        """获取默认输出目录"""
        try:
            if platform == 'android':
                from android.storage import primary_external_storage_path
                return primary_external_storage_path()
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
            self.log(f"❌ 选择文件时出错: {str(e)}")
            self.show_error_dialog("选择文件失败", str(e))

    def select_file_android(self):
        """Android文件选择"""
        try:
            from jnius import autoclass
            from android import activity

            Intent = autoclass('android.content.Intent')

            def on_activity_result(request_code, result_code, intent):
                if request_code == 1001:
                    if result_code == -1:  # RESULT_OK
                        try:
                            uri = intent.getData()
                            content_resolver = autoclass('org.kivy.android.PythonActivity').mActivity.getContentResolver()

                            # 读取文件
                            input_stream = content_resolver.openInputStream(uri)
                            data = bytearray()
                            buffer = bytearray(8192)
                            while True:
                                read = input_stream.read(buffer, 0, 8192)
                                if read == -1:
                                    break
                                data.extend(buffer[:read])
                            input_stream.close()

                            # 保存到临时文件
                            import tempfile
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as f:
                                f.write(data)
                                self.selected_file = f.name

                            self.file_btn.text = f"✅ 已选择\n\n{os.path.basename(self.selected_file)[:30]}\n\n图片已准备好，可以解码了"
                            self.file_btn.background_color = (0.75, 0.95, 0.75, 1)
                            self.file_btn.color = (0.1, 0.4, 0.1, 1)
                            self.log(f"✅ 图片选择成功！\n\n文件名: {os.path.basename(self.selected_file)}\n大小: {len(data)} 字节\n\n现在可以点击「开始解码」了")

                        except Exception as e:
                            self.log(f"❌ 读取图片失败: {str(e)}")
                            self.show_error_dialog("读取图片失败", str(e))

            activity.bind(on_activity_result=on_activity_result)

            intent = Intent()
            intent.setAction(Intent.ACTION_GET_CONTENT)
            intent.setType("image/*")
            current_activity = autoclass('org.kivy.android.PythonActivity').mActivity
            current_activity.startActivityForResult(intent, 1001)

        except Exception as e:
            self.log(f"❌ 打开文件选择器失败: {str(e)}")
            self.show_error_dialog("打开文件选择器失败", str(e))

    def select_file_desktop(self):
        """桌面端文件选择（用于测试）"""
        try:
            self.log("📝 请输入图片文件路径进行测试:")
            self.selected_file = input("Enter image path: ")
            if os.path.isfile(self.selected_file):
                self.file_btn.text = f"✅ 已选择\n\n{os.path.basename(self.selected_file)}"
                self.log(f"✅ 文件: {self.selected_file}")
            else:
                self.log("❌ 文件不存在")
        except Exception as e:
            self.log(f"❌ 错误: {str(e)}")

    def safe_start_decode(self, instance):
        """安全地开始解码"""
        try:
            if not self.selected_file:
                self.show_error_dialog(
                    "请先选择图片",
                    "您还没有选择图片\n\n请点击上方蓝色的「点击这里选择图片」按钮来选择含有隐藏信息的图片"
                )
                return

            if not os.path.isfile(self.selected_file):
                self.show_error_dialog(
                    "文件不存在",
                    "选择的文件找不到了\n\n请重新选择图片"
                )
                return

            password = self.password_input.text

            # 禁用按钮
            self.decode_btn.disabled = True
            self.decode_btn.text = "⏳\n\n正在解码中...\n\n请稍候，这需要一点时间"
            self.log_text.text = "🚀 开始解码...\n\n正在从图片中提取隐藏数据，请稍候...\n\n这可能需要几秒钟时间"

            # 使用定时器执行解码（避免阻塞UI）
            Clock.schedule_once(lambda dt: self.safe_do_decode(password), 0.1)

        except Exception as e:
            self.decode_btn.disabled = False
            self.decode_btn.text = "🔙\n\n开始解码\n\n点击这里开始从图片中提取隐藏的文件"
            self.log(f"❌ 启动解码失败: {str(e)}")
            self.show_error_dialog("启动解码失败", str(e))

    def safe_do_decode(self, password):
        """安全地执行解码"""
        try:
            result = SafeDecodeLogic.decode(
                self.selected_file,
                password,
                self.output_dir,
                callback=self.log
            )

            final_path, final_ext, size_str = result
            self.log("=" * 50)
            self.log("🎉 解码成功！")
            self.log(f"📄 文件名: {os.path.basename(final_path)}")
            self.log(f"📁 文件类型: {final_ext.upper()}")
            self.log(f"📊 文件大小: {size_str}")
            self.log(f"💾 保存位置: {self.output_dir}")
            self.log("=" * 50)
            self.log("\n✅ 文件已保存！点击下方按钮可以打开文件夹查看")

            self.decode_btn.disabled = False
            self.decode_btn.text = "✅\n\n解码成功！\n\n可以继续解码其他图片"
            self.open_btn.disabled = False
            self.open_btn.canvas.before.clear()
            with self.open_btn.canvas.before:
                Color(0.3, 0.65, 0.95, 1)
                self.open_btn.bg_rect = RoundedRectangle(pos=self.open_btn.pos, size=self.open_btn.size, radius=[25])

            self.show_success_dialog(
                "🎉 解码成功！",
                f"文件已成功解码并保存！\n\n📁 文件类型: {final_ext.upper()}\n📊 文件大小: {size_str}\n💾 保存位置: {self.output_dir}\n\n点击「打开文件位置」按钮可以查看文件"
            )

        except Exception as e:
            self.decode_btn.disabled = False
            self.decode_btn.text = "🔙\n\n开始解码\n\n点击这里开始从图片中提取隐藏的文件"
            self.log("=" * 50)
            error_msg = str(e)
            self.log(f"❌ 解码失败\n\n{error_msg}")
            self.log("=" * 50)
            self.log("\n💡 提示：\n• 请确保这是正确的隐写图片\n• 如果有密码，请检查密码是否正确\n• 尝试使用其他图片")

            self.show_error_dialog("解码失败", error_msg)

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
                self.log(f"📁 正在打开文件夹: {self.output_dir}")
            else:
                import subprocess
                subprocess.Popen(f'explorer "{self.output_dir}"')
                self.log(f"📁 已打开文件夹: {self.output_dir}")
        except Exception as e:
            self.log(f"❌ 打开文件夹失败: {str(e)}")
            self.show_error_dialog("打开文件夹失败", f"无法打开文件夹\n\n{self.output_dir}\n\n请手动使用文件管理器打开该位置")

    def log(self, message):
        """添加日志"""
        try:
            self.log_text.text = message + "\n\n" + self.log_text.text[:500]
        except:
            pass

    def show_error_dialog(self, title, message):
        """显示错误对话框 - 不会闪退"""
        try:
            popup_layout = BoxLayout(orientation='vertical', padding=30, spacing=20)

            # 错误图标
            icon_label = Label(
                text="❌",
                font_size='60sp',
                size_hint_y=None,
                height=70
            )

            # 错误消息
            msg_label = Label(
                text=message,
                font_size='18sp',
                text_size=(320, None),
                halign='center',
                color=(0.2, 0.2, 0.2, 1),
                size_hint_y=None,
                height=150
            )

            popup_layout.add_widget(icon_label)
            popup_layout.add_widget(msg_label)

            # 确定按钮
            close_btn = RoundedButton(
                text="我知道了",
                size_hint_y=None,
                height=60,
                font_size='20sp',
                color=(1, 1, 1, 1)
            )
            popup_layout.add_widget(close_btn)

            popup = Popup(
                title=title,
                title_font_size='24sp',
                title_align='center',
                title_color=(0.8, 0.2, 0.2, 1),
                content=popup_layout,
                size_hint=(0.9, 0.6),
                separator_color=(0.8, 0.2, 0.2, 1),
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
            popup_layout = BoxLayout(orientation='vertical', padding=30, spacing=20)

            # 成功图标
            icon_label = Label(
                text="✅",
                font_size='60sp',
                size_hint_y=None,
                height=70
            )

            # 成功消息
            msg_label = Label(
                text=message,
                font_size='18sp',
                text_size=(320, None),
                halign='center',
                color=(0.2, 0.2, 0.2, 1),
                size_hint_y=None,
                height=150
            )

            popup_layout.add_widget(icon_label)
            popup_layout.add_widget(msg_label)

            # 确定按钮
            close_btn = RoundedButton(
                text="太好了！",
                size_hint_y=None,
                height=60,
                font_size='20sp',
                color=(1, 1, 1, 1)
            )
            popup_layout.add_widget(close_btn)

            popup = Popup(
                title=title,
                title_font_size='24sp',
                title_align='center',
                title_color=(0.2, 0.6, 0.2, 1),
                content=popup_layout,
                size_hint=(0.9, 0.6),
                separator_color=(0.2, 0.6, 0.2, 1),
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
