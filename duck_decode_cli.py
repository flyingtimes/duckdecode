#!/usr/bin/env python3
"""
Duck Decode CLI - 隐写解码命令行工具
从图片中解码隐藏的文件内容

Usage:
    python duck_decode_cli.py input.png [password] [--output OUTPUT]
"""
import argparse
import os
import struct
import sys
import numpy as np
from PIL import Image

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    from moviepy import VideoFileClip
    HAS_MOVIEPY = True
except ImportError:
    HAS_MOVIEPY = False

CATEGORY = "SSTool"
WATERMARK_SKIP_W_RATIO = 0.40
WATERMARK_SKIP_H_RATIO = 0.08


def _extract_payload_with_k(arr: np.ndarray, k: int) -> bytes:
    """从图像数组中提取载荷数据"""
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


def _generate_key_stream(password: str, salt: bytes, length: int) -> bytes:
    """生成密钥流用于解密"""
    import hashlib
    key_material = (password + salt.hex()).encode("utf-8")
    out = bytearray()
    counter = 0
    while len(out) < length:
        out.extend(hashlib.sha256(key_material + str(counter).encode("utf-8")).digest())
        counter += 1
    return bytes(out[:length])


def _parse_header(header: bytes, password: str):
    """解析文件头并解密数据"""
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
    ks = _generate_key_stream(password, salt, len(data))
    plain = bytes(a ^ b for a, b in zip(data, ks))
    return plain, ext


def binpng_bytes_to_mp4_bytes(p: str) -> bytes:
    """将binpng格式的字节数据转换为mp4"""
    img = Image.open(p).convert("RGB")
    arr = np.array(img).astype(np.uint8)
    flat = arr.reshape(-1, 3).reshape(-1)
    return flat.tobytes().rstrip(b"\x00")


def decode_from_image(image_path: str, password: str = "", output_dir: str = "."):
    """
    从图像中解码隐藏的文件

    Args:
        image_path: 输入图像路径
        password: 解密密码（可选）
        output_dir: 输出目录

    Returns:
        tuple: (输出文件路径, 文件扩展名)
    """
    # 加载图像
    img = Image.open(image_path)
    arr = np.array(img.convert("RGB")).astype(np.uint8)

    # 尝试不同的k值提取载荷
    header = None
    raw = None
    ext = None
    last_err = None
    for k in (2, 6, 8):
        try:
            header = _extract_payload_with_k(arr, k)
            raw, ext = _parse_header(header, password)
            break
        except Exception as e:
            last_err = e
            continue

    if raw is None:
        raise last_err or RuntimeError("解析失败 / Decoding failed")

    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    name = "duck_recovered"
    out_path = os.path.join(output_dir, name)

    # 处理.binpng格式
    if ext.endswith(".binpng"):
        tmp_png = out_path + ".binpng"
        with open(tmp_png, "wb") as f:
            f.write(raw)
        mp4_bytes = binpng_bytes_to_mp4_bytes(tmp_png)
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

    return final_path, final_ext


def main():
    parser = argparse.ArgumentParser(
        description="Duck Decode CLI - 从图像中解码隐藏的文件内容",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python duck_decode_cli.py input.png
  python duck_decode_cli.py input.png "mypassword"
  python duck_decode_cli.py input.png "mypassword" --output ./decoded
        """
    )
    parser.add_argument("input", help="输入图像路径 (PNG/JPG等)")
    parser.add_argument("password", nargs="?", default="", help="解密密码（如果需要）")
    parser.add_argument("-o", "--output", default=".", help="输出目录 (默认: 当前目录)")
    parser.add_argument("-v", "--verbose", action="store_true", help="显示详细信息")

    args = parser.parse_args()

    # 检查输入文件
    if not os.path.isfile(args.input):
        print(f"错误: 输入文件不存在: {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        if args.verbose:
            print(f"输入文件: {args.input}")
            print(f"密码: {'已设置' if args.password else '无'}")
            print(f"输出目录: {args.output}")
            print("-" * 50)

        output_path, ext = decode_from_image(args.input, args.password, args.output)

        print(f"解码成功! / Decoding successful!")
        print(f"输出文件: {output_path}")
        print(f"文件类型: {ext}")

        # 显示文件大小
        size = os.path.getsize(output_path)
        if size > 1024 * 1024:
            print(f"文件大小: {size / (1024 * 1024):.2f} MB")
        elif size > 1024:
            print(f"文件大小: {size / 1024:.2f} KB")
        else:
            print(f"文件大小: {size} bytes")

    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
