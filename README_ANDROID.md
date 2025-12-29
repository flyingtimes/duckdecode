# Duck Decode Android - APK编译指南

## 项目文件

| 文件 | 说明 |
|------|------|
| [duck_decode_android.py](duck_decode_android.py) | Kivy版本的Android应用 |
| [buildozer.spec](buildozer.spec) | Buildozer配置文件 |
| [build_apk.sh](build_apk.sh) | Linux/Mac构建脚本 |
| [build_apk_win.bat](build_apk_win.bat) | Windows构建脚本 |
| [requirements-android.txt](requirements-android.txt) | Android依赖包 |

## 方法一：使用Docker构建（推荐）

### 1. 安装Docker Desktop
- 下载: https://www.docker.com/products/docker-desktop

### 2. 运行构建
```bash
docker pull kivy/buildozer
docker run --privileged -v %cd%:/home/user/apphost kivy/buildozer
```

## 方法二：使用WSL构建

### 1. 安装WSL
```bash
wsl --install -d Ubuntu
```

### 2. 在WSL中安装依赖
```bash
sudo apt update
sudo apt install -y build-essential git python3-pip python3-setuptools
sudo apt install -y python3-wheel openjdk-17-jdk
pip3 install --user buildozer cython
```

### 3. 运行构建
```bash
cd /mnt/c/Users/13802/code/decode-image-from-RH
bash build_apk.sh
```

## 方法三：使用在线构建服务

由于APK编译需要完整的环境，您也可以使用在线服务：

1. **GitHub Actions** - 创建仓库并自动构建
2. **Google Colab** - 使用免费的云端GPU环境
3. **CodeOcean** - 在线开发环境

## 应用权限

APK需要以下权限：
- `READ_EXTERNAL_STORAGE` - 读取图片文件
- `WRITE_EXTERNAL_STORAGE` - 保存解码后的文件
- `READ_MEDIA_IMAGES` - Android 13+图片访问权限

## 测试应用

### 在电脑上测试（需要Kivy）
```bash
pip install kivy numpy pillow
python duck_decode_android.py
```

### 在Android设备上安装
```bash
adb install -r bin/duckdecode-*.apk
```

## 应用界面预览

```
+----------------------------------+
|       Duck Decode                |
+----------------------------------+
| Input File / 输入文件            |
| [点击选择图片]                   |
+----------------------------------+
| Password / 密码 (可选)           |
| [******]                         |
+----------------------------------+
| Output Dir / 输出目录            |
| /storage/emulated/0              |
+----------------------------------+
|     [DECODE / 解码]              |
+----------------------------------+
| Log / 日志:                      |
| Starting decode...               |
| Loading image...                 |
| SUCCESS!                         |
+----------------------------------+
|   [Open Output / 打开输出目录]   |
+----------------------------------+
```

## 注意事项

1. 首次构建需要下载Android SDK/NDK，时间较长（10-30分钟）
2. 编译后的APK约30-50MB
3. Android 7.0 (API 24) 或更高版本
4. 应用支持ARM64和ARMv7设备