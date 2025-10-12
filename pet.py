from PyQt5.QtMultimedia import QSound
from PyQt5.QtWidgets import QApplication, QLabel, QSystemTrayIcon, QMenu, QAction, QGraphicsOpacityEffect
from PyQt5.QtGui import QPixmap, QIcon, QImage, QFont, QPainter, QFontDatabase, QColor
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QEvent, QRect, QSize, pyqtProperty
from datetime import datetime
from Murasame import chat, generate, utils
import hashlib
import cv2
import threading
import textwrap
import os
import time
import sys
import pyautogui


def wrap_text(text, width=12):
    return '\n'.join(textwrap.wrap(text, width=width, break_long_words=True, break_on_hyphens=False))


class Murasame(QLabel):
    # 显示预设配置
    DISPLAY_PRESETS = {
        "compact": {
            "name": "紧凑模式",
            "visible_ratio": 0.35,
            "text_x_offset": 120,
            "text_y_offset": 15,
            "description": "最节省空间，只显示头部和肩部"
        },
        "balanced": {
            "name": "平衡模式",
            "visible_ratio": 0.45,
            "text_x_offset": 140,
            "text_y_offset": 20,
            "description": "推荐设置，显示上半身"
        },
        "standard": {
            "name": "标准模式",
            "visible_ratio": 0.6,
            "text_x_offset": 150,
            "text_y_offset": 25,
            "description": "显示到腰部，适中大小"
        },
        "full": {
            "name": "完整显示",
            "visible_ratio": 1.0,
            "text_x_offset": 160,
            "text_y_offset": -100,
            "description": "显示完整桌宠"
        }
    }
    
    def __init__(self):
        super().__init__()
        
        # 从配置文件读取显示设置
        config = utils.get_config()
        display_config = config.get('display', {})
        preset_name = display_config.get('preset', 'balanced')
        
        # 如果使用预设
        if preset_name in self.DISPLAY_PRESETS:
            preset = self.DISPLAY_PRESETS[preset_name]
            self.visible_ratio = preset['visible_ratio']
            self.text_x_offset_default = preset['text_x_offset']
            self.text_y_offset_default = preset['text_y_offset']
            print(f"✓ 使用显示预设: {preset['name']} - {preset['description']}")
        # 如果使用自定义配置
        elif preset_name == 'custom':
            custom_config = display_config.get('custom', {})
            self.visible_ratio = custom_config.get('visible_ratio', 0.4)
            self.text_x_offset_default = custom_config.get('text_x_offset', 140)
            self.text_y_offset_default = custom_config.get('text_y_offset', 20)
            print(f"✓ 使用自定义显示配置")
        else:
            # 默认使用平衡模式
            preset = self.DISPLAY_PRESETS['balanced']
            self.visible_ratio = preset['visible_ratio']
            self.text_x_offset_default = preset['text_x_offset']
            self.text_y_offset_default = preset['text_y_offset']
            print(f"⚠ 未知预设 '{preset_name}'，使用默认: {preset['name']}")
        
        self.history = chat.identity()
        self.emotion_history = []
        self.embeddings_history = []

        self._fade_bg = QLabel(self)
        self._fade_fg = QLabel(self)
        for lbl in (self._fade_bg, self._fade_fg):
            lbl.setAttribute(Qt.WA_TranslucentBackground)
            lbl.setVisible(False)
            lbl.setGeometry(self.rect())
            lbl.lower()
        self._fade_bg_effect = QGraphicsOpacityEffect(self._fade_bg)
        self._fade_fg_effect = QGraphicsOpacityEffect(self._fade_fg)
        self._fade_bg.setGraphicsEffect(self._fade_bg_effect)
        self._fade_fg.setGraphicsEffect(self._fade_fg_effect)
        self._fade_anim = None

        self.setWindowFlags(Qt.FramelessWindowHint |
                            Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 在 macOS 上使用原生 API 设置更高的窗口层级
        self._setup_macos_window_level()

        cv_img = generate.generate_fgimage(target="ムラサメb",
                                            embeddings_layers=[1717, 1475, 1261])
        pixmap = self.cvimg_to_qpixmap(cv_img)

        # 考虑 HiDPI 缩放
        scale_factor = 1.0
        if hasattr(app, 'devicePixelRatio'):
            scale_factor = app.devicePixelRatio()
        elif hasattr(app.primaryScreen(), 'devicePixelRatio'):
            scale_factor = app.primaryScreen().devicePixelRatio()

        # 在 HiDPI 屏幕上进一步缩小
        if scale_factor > 1.0:
            pixmap = pixmap.scaled(pixmap.width() // int(scale_factor * 2),
                                   pixmap.height() // int(scale_factor * 2),
                                   Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            pixmap = pixmap.scaled(pixmap.width() // 2, pixmap.height() // 2,
                                   Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.setPixmap(pixmap)
        self.resize(pixmap.size())

        self._xfade_old = None
        self._xfade_new = None
        self._xfade_t = 1.0
        self._xfade_anim = None

        self.mousePressEvent = self.start_move
        self.mouseMoveEvent = self.on_move
        self.offset = None
        self.touch_head = False
        self.head_press_x = None

        self.display_text = ""
        self.text_font = QFont()
        self.text_font.setFamily("思源黑体 CN Bold")

        # 根据 HiDPI 调整字体大小
        scale_factor = 1.0
        if hasattr(app, 'devicePixelRatio'):
            scale_factor = app.devicePixelRatio()
        elif hasattr(app.primaryScreen(), 'devicePixelRatio'):
            scale_factor = app.primaryScreen().devicePixelRatio()

        font_size = 24
        if scale_factor > 1.0:
            font_size = int(24 / scale_factor)
        self.text_font.setPointSize(font_size)

        self.text_x_offset = 0
        self.text_y_offset = 0
        QFontDatabase.addApplicationFont("./思源黑体Bold.otf")

        self.full_text = ""
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self._typing_step)
        self.typing_interval = 40
        self._typing_index = 0
        self.typing_prefix = ""

        self.setAttribute(Qt.WA_InputMethodEnabled, True)
        self.input_mode = False
        self.input_buffer = ""
        self.preedit_text = ""

        self.latest_response = "【 丛雨 】\n  主人，你好呀！"

    def _setup_macos_window_level(self):
        """在 macOS 上设置窗口层级，使其始终在最前但不抢占焦点"""
        import platform
        if platform.system() != 'Darwin':
            return
        
        try:
            # 使用 PyObjC 提供更优雅的 Cocoa API 访问
            from AppKit import NSApp, NSWindow, NSFloatingWindowLevel
            from PyQt5.QtGui import QWindow
            
            # 延迟设置，确保窗口已经创建
            def set_level():
                try:
                    # 获取 Qt 窗口对应的 NSWindow
                    ns_view = self.winId()
                    if ns_view:
                        # 通过 PyObjC 获取 NSWindow 对象
                        from objc import objc_object
                        import ctypes
                        ns_view_ptr = ctypes.c_void_p(int(ns_view))
                        
                        # 使用 PyObjC 的对象包装
                        from AppKit import NSView
                        view = objc_object(c_void_p=ns_view_ptr)
                        window = view.window()
                        
                        if window:
                            # 设置窗口层级为浮动窗口级别（不抢占焦点）
                            window.setLevel_(NSFloatingWindowLevel)
                            print("✓ macOS window level set to NSFloatingWindowLevel")
                except Exception as e:
                    print(f"Failed to set window level with PyObjC: {e}")
            
            QTimer.singleShot(100, set_level)
        except ImportError:
            print("PyObjC not available, falling back to Qt window flags")
            # 如果 PyObjC 未安装，回退到默认的 Qt.WindowStaysOnTopHint
        except Exception as e:
            print(f"Cannot setup macOS window level: {e}")

    def event(self, event):
        if event.type() == QEvent.WindowActivate:
            print("activate")
            screen_worker.should_capture = False
            if hasattr(screen_worker, "interrupt_event"):
                screen_worker.interrupt_event.set()
        elif event.type() == QEvent.WindowDeactivate:
            print("deactivate")
            self.input_mode = False
            self.show_text(self.latest_response, typing=True)
            screen_worker.should_capture = True
        return super().event(event)

    def cvimg_to_qpixmap(self, cv_img):
        if cv_img.shape[2] == 4:
            cv_img_bgra = cv2.cvtColor(cv_img, cv2.COLOR_RGBA2BGRA)
            height, width, channel = cv_img_bgra.shape
            bytes_per_line = 4 * width
            qimg = QImage(cv_img_bgra.data, width, height,
                          bytes_per_line, QImage.Format_RGBA8888)
            return QPixmap.fromImage(qimg)

    def start_move(self, event):
        if event.button() == Qt.LeftButton:
            rect = self.rect()
            
            # 由于只显示上半身，调整头部区域判断
            # 头部区域应该是可见区域的上半部分
            visible_height = int(self.height() * self.visible_ratio)  # 可见的部分
            head_threshold = visible_height // 2  # 头部区域约为可见区域的上半部分
            
            if event.y() < head_threshold:
                self.touch_head = True
                self.head_press_x = event.x()
                self.setCursor(Qt.OpenHandCursor)
            else:
                self.touch_head = False
                self.head_press_x = None
                self.setCursor(Qt.ArrowCursor)
            # 检查是否点击了文本区域
            text_clicked = False
            if self.display_text:
                # 计算文本区域
                rect = self.rect()
                text_rect = rect.adjusted(
                    self.text_x_offset,
                    self.text_y_offset,
                    self.text_x_offset,
                    -rect.height()//2 + self.text_y_offset
                )
                # 扩大点击区域，包含文本周围
                expanded_rect = text_rect.adjusted(-20, -20, 20, 20)
                if expanded_rect.contains(event.pos()):
                    text_clicked = True

            # 输入区域调整为可见区域的下半部分
            input_threshold = int(visible_height * 0.7)
            if event.y() > input_threshold or text_clicked:
                self.input_mode = True
                self.input_buffer = ""
                self.display_text = "【 LemonQu 】\n  ..."
                self.update()
                return

        if event.button() == Qt.MiddleButton:
            self.offset = event.pos()
            self.setCursor(Qt.SizeAllCursor)

    def on_move(self, event):
        # 检查左键是否按下，用于摸头交互
        if self.touch_head and self.head_press_x is not None and event.buttons() & Qt.LeftButton:
            if abs(event.x() - self.head_press_x) > 50:
                self.llm_worker = LLMWorker(
                    "主人摸了摸你的头", self.history, self.emotion_history, self.embeddings_history, role="system")
                self.llm_worker.finished.connect(self.on_llm_result)
                self.llm_worker.start()
                self.touch_head = False
                self.head_press_x = None
        # 中键拖动窗口
        if self.offset is not None and event.buttons() == Qt.MiddleButton:
            self.move(self.pos() + event.pos() - self.offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.offset = None
            self.setCursor(Qt.ArrowCursor)
        if event.button() == Qt.LeftButton:
            self.touch_head = False
            self.head_press_x = None
            self.setCursor(Qt.ArrowCursor)

    def show_text(self, text: str, x_offset: int = None, y_offset: int = None, typing: bool = True, typing_prefix: str = "【 丛雨 】\n  "):
        # 使用配置文件中的默认值
        if x_offset is None:
            x_offset = self.text_x_offset_default
        if y_offset is None:
            y_offset = self.text_y_offset_default
            
        # 根据缩放调整默认偏移量
        scale_factor = 1.0
        if hasattr(app, 'devicePixelRatio'):
            scale_factor = app.devicePixelRatio()
        elif hasattr(app.primaryScreen(), 'devicePixelRatio'):
            scale_factor = app.primaryScreen().devicePixelRatio()

        if scale_factor > 1.0:
            x_offset = int(x_offset / scale_factor)
            y_offset = int(y_offset / scale_factor)

        self.text_x_offset = x_offset
        self.text_y_offset = y_offset
        self.typing_prefix = typing_prefix
        if typing:
            if typing_prefix and text.startswith(typing_prefix):
                self.full_text = text[len(typing_prefix):]
                self.display_text = typing_prefix
            else:
                self.full_text = text
                self.display_text = ""
            self._typing_index = 0
            self.typing_timer.start(self.typing_interval)
        else:
            self.display_text = text
            self.full_text = text
            self.typing_timer.stop()
            self.update()

    def _typing_step(self):
        if self._typing_index < len(self.full_text):
            self.display_text = self.typing_prefix + \
                self.full_text[:self._typing_index + 1]
            self._typing_index += 1
            self.update()
        else:
            self.typing_timer.stop()

    def paintEvent(self, event):
        if self._xfade_old is not None and self._xfade_new is not None:
            w, h = self.width(), self.height()
            img_old = QImage(w, h, QImage.Format_ARGB32_Premultiplied)
            img_old.fill(0)
            p = QPainter(img_old)
            p.setCompositionMode(QPainter.CompositionMode_Source)
            p.drawPixmap(0, 0, self._xfade_old)
            p.setCompositionMode(QPainter.CompositionMode_DestinationIn)
            p.fillRect(img_old.rect(), QColor(
                0, 0, 0, int((1.0 - self._xfade_t) * 255)))
            p.end()
            img_new = QImage(w, h, QImage.Format_ARGB32_Premultiplied)
            img_new.fill(0)
            p = QPainter(img_new)
            p.setCompositionMode(QPainter.CompositionMode_Source)
            p.drawPixmap(0, 0, self._xfade_new)
            p.setCompositionMode(QPainter.CompositionMode_DestinationIn)
            p.fillRect(img_new.rect(), QColor(
                0, 0, 0, int(self._xfade_t * 255)))
            p.end()
            blended = QImage(w, h, QImage.Format_ARGB32_Premultiplied)
            blended.fill(0)
            p = QPainter(blended)
            p.setCompositionMode(QPainter.CompositionMode_Source)
            p.drawImage(0, 0, img_old)
            p.setCompositionMode(QPainter.CompositionMode_Plus)
            p.drawImage(0, 0, img_new)
            p.end()
            painter = QPainter(self)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            painter.drawImage(0, 0, blended)
            if self.display_text:
                painter.setRenderHint(QPainter.TextAntialiasing, True)
                painter.setFont(self.text_font)
                rect = self.rect()
                text_rect = rect.adjusted(
                    self.text_x_offset,
                    self.text_y_offset,
                    self.text_x_offset,
                    -rect.height()//2 + self.text_y_offset
                )
                align_flag = Qt.AlignLeft | Qt.AlignBottom if '\n' in self.display_text else Qt.AlignHCenter | Qt.AlignBottom

                # 根据缩放调整边框大小
                scale_factor = 1.0
                if hasattr(app, 'devicePixelRatio'):
                    scale_factor = app.devicePixelRatio()
                elif hasattr(app.primaryScreen(), 'devicePixelRatio'):
                    scale_factor = app.primaryScreen().devicePixelRatio()

                border_size = max(1, int(2 / scale_factor))
                painter.setPen(QColor(44, 22, 28))
                for dx, dy in [(-border_size, 0), (border_size, 0), (0, -border_size), (0, border_size),
                               (border_size, -border_size), (border_size, border_size),
                               (-border_size, -border_size), (-border_size, border_size)]:
                    painter.drawText(text_rect.translated(
                        dx, dy), align_flag, self.display_text)

                painter.setPen(Qt.white)
                painter.drawText(text_rect, align_flag, self.display_text)
            painter.end()
            return

        super().paintEvent(event)
        if self.display_text:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.TextAntialiasing, True)
            painter.setFont(self.text_font)
            rect = self.rect()
            text_rect = rect.adjusted(
                self.text_x_offset,
                self.text_y_offset,
                self.text_x_offset,
                -rect.height()//2 + self.text_y_offset
            )
            align_flag = Qt.AlignLeft | Qt.AlignBottom if '\n' in self.display_text else Qt.AlignHCenter | Qt.AlignBottom

            # 根据缩放调整边框大小
            scale_factor = 1.0
            if hasattr(app, 'devicePixelRatio'):
                scale_factor = app.devicePixelRatio()
            elif hasattr(app.primaryScreen(), 'devicePixelRatio'):
                scale_factor = app.primaryScreen().devicePixelRatio()

            border_size = max(1, int(2 / scale_factor))
            painter.setPen(QColor(44, 22, 28))
            for dx, dy in [(-border_size, 0), (border_size, 0), (0, -border_size), (0, border_size),
                           (border_size, -border_size), (border_size, border_size),
                           (-border_size, -border_size), (-border_size, border_size)]:
                painter.drawText(text_rect.translated(dx, dy),
                                 align_flag, self.display_text)

            painter.setPen(Qt.white)
            painter.drawText(text_rect, align_flag, self.display_text)
            painter.end()

    def _get_fade_progress(self) -> float:
        return self._xfade_t

    def _set_fade_progress(self, value: float):
        self._xfade_t = float(value)
        self.update()

    fadeProgress = pyqtProperty(
        float, fget=_get_fade_progress, fset=_set_fade_progress)

    def inputMethodQuery(self, query):
        if query == Qt.ImMicroFocus:
            rect = self.rect().adjusted(
                self.text_x_offset,
                self.text_y_offset,
                self.text_x_offset,
                -self.rect().height()//2 + self.text_y_offset
            )
            pos = self.mapToGlobal(rect.bottomLeft())
            return QRect(pos, QSize(1, 30))
        return super().inputMethodQuery(query)

    def inputMethodEvent(self, event):
        if self.input_mode:
            commit = event.commitString()
            preedit = event.preeditString()
            if commit:
                self.input_buffer += commit
            self.preedit_text = preedit
            wrapped = wrap_text(self.input_buffer + self.preedit_text)
            self.display_text = f"【 LemonQu 】\n  「{wrapped}」"
            self.update()
        else:
            super().inputMethodEvent(event)

    def handle_user_input(self):
        if hasattr(screen_worker, "interrupt_event"):
            screen_worker.interrupt_event.set()
        self.llm_worker = LLMWorker(
            self.input_buffer, self.history, self.emotion_history, self.embeddings_history, role="user")
        self.llm_worker.finished.connect(self.on_llm_result)
        self.llm_worker.start()

    def on_llm_result(self, result, history, emotion_history, embeddings_history, embeddings_layers, raw_response):
        raw_response_md5 = hashlib.md5(raw_response.encode()).hexdigest()
        voice_path = os.path.join(os.getcwd(), 'voices', f"{raw_response_md5}.wav")
        QSound.play(voice_path)
        self.show_text(result, typing=True)
        self.latest_response = result
        self.input_buffer = ""
        self.preedit_text = ""
        self.history = history
        self.emotion_history = emotion_history
        self.embeddings_history = embeddings_history
        self.switch_image("b", embeddings_layers)

    def keyPressEvent(self, event):
        if self.input_mode:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                self.input_mode = False
                self.handle_user_input()
            elif event.key() == Qt.Key_Backspace:
                if self.preedit_text:
                    pass
                else:
                    self.input_buffer = self.input_buffer[:-1]
                    wrapped = wrap_text(self.input_buffer)
                    if not wrapped.strip():
                        self.display_text = "【 LemonQu 】\n  ..."
                    else:
                        self.display_text = f"【 LemonQu 】\n  「{wrapped}」"
                    self.update()
            else:
                char = event.text()
                if char and not self.preedit_text:
                    self.input_buffer += char
                    wrapped = wrap_text(self.input_buffer)
                    if not wrapped.strip():
                        self.display_text = "【 LemonQu 】\n  ..."
                    else:
                        self.display_text = f"【 LemonQu 】\n  「{wrapped}」"
                    self.update()
        else:
            super().keyPressEvent(event)

    def switch_image(self, target, embeddings_layers):
        cv_img = generate.generate_fgimage(
            target=f"ムラサメ{target}", embeddings_layers=embeddings_layers)
        pixmap_new = self.cvimg_to_qpixmap(cv_img)

        # 考虑 HiDPI 缩放
        scale_factor = 1.0
        if hasattr(app, 'devicePixelRatio'):
            scale_factor = app.devicePixelRatio()
        elif hasattr(app.primaryScreen(), 'devicePixelRatio'):
            scale_factor = app.primaryScreen().devicePixelRatio()

        # 在 HiDPI 屏幕上进一步缩小
        if scale_factor > 1.0:
            pixmap_new = pixmap_new.scaled(pixmap_new.width() // int(scale_factor * 2),
                                           pixmap_new.height() // int(scale_factor * 2),
                                           Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            pixmap_new = pixmap_new.scaled(pixmap_new.width() // 2, pixmap_new.height() // 2,
                                           Qt.KeepAspectRatio, Qt.SmoothTransformation)

        pixmap_old = self.pixmap()
        if pixmap_old is None:
            self.setPixmap(pixmap_new)
            self.resize(pixmap_new.size())
            self.update()
            return

        self._xfade_old = pixmap_old
        self._xfade_new = pixmap_new
        self._xfade_t = 0.0

        if self._xfade_anim:
            self._xfade_anim.stop()
        from PyQt5.QtCore import QPropertyAnimation
        self._xfade_anim = QPropertyAnimation(self, b"fadeProgress")
        self._xfade_anim.setDuration(400)
        self._xfade_anim.setStartValue(0.0)
        self._xfade_anim.setEndValue(1.0)

        def finish():
            self.setPixmap(pixmap_new)
            self.resize(pixmap_new.size())
            self._xfade_old = None
            self._xfade_new = None
            self._xfade_anim = None
            self.update()

        self._xfade_anim.finished.connect(finish)
        self._xfade_anim.start()


class ScreenWorker(QThread):
    screen_result = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = True
        self.history = []
        self.should_capture = False
        self.llmworker = None
        self.interrupt_event = threading.Event()

    def run(self):
        while self.running:
            print(self.should_capture, "should_capture")
            if self.should_capture:
                self.interrupt_event.clear()
                try:
                    screenshot = pyautogui.screenshot()
                    sys_prompt = '''你现在要担任一个AI桌宠的视觉识别助手，我会向你提供用户此时的屏幕截图，你要识别用户此时的行为，并进行描述。我会将你的描述以system消息提供给另外一个处理语言的AI模型。'''
                    response, _ = chat.query_image(screenshot, "现在请描述用户此时的行为", [
                        {"role": "system", "content": sys_prompt}])
                    des, self.history = chat.think_image(
                        response, self.history)
                    if des['des']:
                        print("scr worker：", des['des'])
                        self.llmworker = LLMWorker(
                            des['des'], self.history, [], [], role="system", interrupt_event=self.interrupt_event
                        )
                        self.screen_result.emit(des['des'])

                        self.llmworker.start()
                        self.llmworker.wait()
                finally:
                    pass
            time.sleep(30)

    def stop(self):
        self.running = False
        if self.llmworker and self.llmworker.isRunning():
            self.interrupt_event.set()

    def on_llm_result(self, *args):
        pass


class LLMWorker(QThread):
    finished = pyqtSignal(str, list, list, list, list, str)

    def __init__(self, prompt, history, emotion_history, embeddings_history, role="user", interrupt_event=None):
        super().__init__()
        self.prompt = prompt
        self.history = history
        self.role = role
        self.emotion_history = emotion_history
        self.embeddings_history = embeddings_history
        self.interrupt_event = interrupt_event

    def run(self):
        try:
            t_start = time.time()
            hour = datetime.now().hour
            minute = datetime.now().minute
            if 0 <= hour < 5:
                period = "凌晨"
            elif 5 <= hour < 12:
                period = "早上"
            elif 12 <= hour < 18:
                period = "下午"
            elif 18 <= hour < 24:
                period = "晚上"
            self.history.append(
                {"role": "system", "content": f"现在是{period}{hour}点{minute}分"})

            if self.interrupt_event and self.interrupt_event.is_set():
                print("LLMWorker interrupted before start")
                return

            response, history = chat.query(
                prompt=self.prompt,
                history=self.history,
                role=self.role
            )

            if self.interrupt_event and self.interrupt_event.is_set():
                print("LLMWorker interrupted before start")
                return

            translated = chat.get_translate(response)

            if self.interrupt_event and self.interrupt_event.is_set():
                print("LLMWorker interrupted before start")
                return

            emotion, emotion_history = chat.get_emotion(
                f"用户：{self.prompt}\n丛雨：{response}", self.emotion_history)

            if self.interrupt_event and self.interrupt_event.is_set():
                print("LLMWorker interrupted before start")
                return

            tts_thread = threading.Thread(
                target=chat.generate_tts, args=(translated, emotion), daemon=True)
            tts_thread.start()

            if self.interrupt_event and self.interrupt_event.is_set():
                print("LLMWorker interrupted before start")
                return

            embeddings_layers, embeddings_history = chat.get_embedings_layers(
                response, "b", self.embeddings_history)

            if self.interrupt_event and self.interrupt_event.is_set():
                print("LLMWorker interrupted before start")
                return

            raw_response_md5 = hashlib.md5(translated.encode()).hexdigest()
            voice_path = f"./voices/{raw_response_md5}.wav"

            while not os.path.exists(voice_path):
                time.sleep(0.1)

            print(len(history), "history")
            print(embeddings_layers, "b")
            print(time.time() - t_start, "sec")
            print("Emitting ============")

            result = f"「{wrap_text(response)}」"
            self.finished.emit(result, history, emotion_history,
                               embeddings_history, embeddings_layers, translated)
        finally:
            pass


def clear_history(parent):
    from PyQt5.QtWidgets import QMessageBox
    reply = QMessageBox.question(parent, "Clear History", "Are you sure you want to clear the history?",
                                 QMessageBox.Ok | QMessageBox.Cancel)
    if reply == QMessageBox.Ok:
        murasame.history = chat.identity()
        murasame.emotion_history = []
        murasame.embeddings_history = []


if __name__ == "__main__":
    history = chat.identity()

    app = QApplication(sys.argv)
    murasame = Murasame()

    # 动态计算窗口位置，只显示上半身
    screen = app.primaryScreen()
    screen_geometry = screen.availableGeometry()
    window_width = murasame.width()
    window_height = murasame.height()

    # 放在右下角，只显示上半身
    x = screen_geometry.width() - window_width - 20
    # 让窗口下半部分超出屏幕，只显示上半身
    y = screen_geometry.height() - int(window_height * murasame.visible_ratio)

    murasame.move(x, y)
    murasame.show()

    tray_icon = QSystemTrayIcon(QIcon("icon.png"), parent=app)
    tray_menu = QMenu()

    clear_action = QAction("Clear History")
    clear_action.triggered.connect(lambda: clear_history(murasame))
    exit_action = QAction("Exit")
    exit_action.triggered.connect(app.quit)

    tray_menu.addAction(clear_action)
    tray_menu.addAction(exit_action)
    tray_icon.setContextMenu(tray_menu)
    tray_icon.show()

    murasame.show_text(murasame.latest_response, typing=True)

    if utils.get_config()['enable_vl']:
        screen_worker = ScreenWorker()

        def handle_screen_result(des_text):
            murasame.llm_worker = LLMWorker(
                des_text, murasame.history, murasame.emotion_history, murasame.embeddings_history, role="system"
            )
            murasame.llm_worker.finished.connect(murasame.on_llm_result)
            murasame.llm_worker.start()

        screen_worker.screen_result.connect(handle_screen_result)
        screen_worker.start()

    sys.exit(app.exec_())
