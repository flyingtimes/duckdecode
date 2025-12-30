# Duck Decode - Android APK

[![Build Android APK](https://github.com/flyingtimes/duckdecode/actions/workflows/build-apk.yml/badge.svg?branch=main)](https://github.com/flyingtimes/duckdecode/actions/workflows/build-apk.yml)

隐写解码工具 - 从图片中提取隐藏的文件

## 功能

- 从图片中解码隐藏的文件内容
- 支持密码保护的文件
- Android原生文件选择器
- 自动保存到外部存储

## GitHub Actions 自动构建

本项目使用 GitHub Actions 自动构建 APK。

### 获取 APK

1. 进入 [Actions](https://github.com/USERNAME/duckdecode/actions) 页面
2. 选择最近的构建任务
3. 在 "Artifacts" 部分下载 `duckdecode-apk`

### 手动触发构建

在 Actions 页面选择 "Build Android APK" 工作流，点击 "Run workflow" 按钮。

## 本地构建

### 方法1: 使用 Docker（推荐）

```bash
docker pull kivy/buildozer:patched
docker run --rm --privileged -v "%CD%:/apphost" kivy/buildozer:patched bash -c "cd /apphost && yes | buildozer android debug"
```

### 方法2: 使用 build_apk_simple.bat

双击运行 `build_apk_simple.bat`

### 方法3: 直接使用 buildozer

```bash
pip install buildozer
buildozer android debug
```

## 本地测试应用（无需APK）

```bash
pip install kivy numpy pillow
python duck_decode_android.py
```

## 文件说明

| 文件 | 说明 |
|------|------|
| [duck_decode_android.py](duck_decode_android.py) | Kivy Android应用源码 |
| [buildozer.spec](buildozer.spec) | Buildozer配置文件 |
| [.github/workflows/build-apk.yml](.github/workflows/build-apk.yml) | GitHub Actions工作流 |

## 应用权限

- `READ_EXTERNAL_STORAGE` - 读取图片文件
- `WRITE_EXTERNAL_STORAGE` - 保存解码后的文件
- `READ_MEDIA_IMAGES` - Android 13+ 图片访问权限

## 系统要求

- Android 7.0 (API 24) 或更高版本
- ARM64 或 ARMv7 设备

## License

MIT
