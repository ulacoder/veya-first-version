# Veya - Eye Tracking Drawing Application

**First Version - v1.0**

Eye-tracking drawing application that allows people with motor disabilities to draw and control computers using eye movements.

Приложение с eye-tracking, которое позволяет людям с ограниченными двигательными функциями рисовать и управлять компьютером с помощью движений глаз.

## 🏆 Achievements / Достижения

- 🥈 **2nd place WRO 2026 Regional**
- Assistive technology for people with motor disabilities / Assistive technology для людей с моторными нарушениями
- Affordable alternative to expensive commercial solutions / Доступная альтернатива дорогим коммерческим решениям

## ✨ Features / Возможности

- **Eye Tracking** - Real-time eye movement detection / Отслеживание движений глаз в реальном времени
- **Calibration** - Precise eye-to-screen coordinate mapping (9-point calibration) / Точное сопоставление координат глаз с экраном (9-точечная калибровка)
- **Drawing** - Gaze-controlled cursor, dwell-time based drawing / Управление курсором взглядом, рисование с помощью "dwell time" (задержки взгляда)
- **Intuitive Interface** - No complex setup, works out of the box / Никаких сложных настроек, все работает из коробки

## 🚀 Quick Start / Быстрый старт

### Installation / Установка

```bash
# Clone the repository / Клонировать репозиторий
git clone https://github.com/ulacoder/veya-first-version.git
cd veya-first-version

# Install dependencies / Установить зависимости
pip install -r requirements.txt
```

### Launch / Запуск

```bash
python main.py
```

## 🎮 Controls / Управление

### General Commands / Общие команды
- `TAB` - Switch between calibration and drawing / Переключение между калибровкой и рисованием
- `R` - Reset calibration / Сброс калибровки
- `P` - Pause/unpause / Пауза/продолжить
- `E` - Toggle eye preview / Показать/скрыть превью камеры
- `ESC` - Exit / Выход

### Drawing Mode / Режим рисования
- `U` - Undo last stroke / Отменить последний штрих
- `C` - Clear canvas / Очистить холст
- `G` - Toggle grid / Показать/скрыть сетку
- `S` - Save drawing / Сохранить рисунок

### Drawing with Gaze / Рисование взглядом
1. Look at the point where you want to start drawing / Смотрите на точку где хотите начать рисовать
2. Hold your gaze for 1.5 seconds (green indicator will appear) / Задержите взгляд на 1.5 секунды (появится зеленый индикатор)
3. Drawing will begin - move your gaze / Начнется рисование - двигайте взглядом
4. Hold your gaze again to stop drawing / Задержите взгляд снова чтобы остановить рисование

## 🏗️ Architecture / Архитектура

```
veya/
├── eye_tracker.py          # Eye tracking with MediaPipe
├── calibration_manager.py  # Coordinate calibration
├── drawing_canvas.py       # Drawing canvas
├── main.py                 # Main application
└── requirements.txt        # Dependencies
```

### Components / Компоненты

#### `EyeTracker`
- Uses **MediaPipe Face Mesh** for eye detection / Использует **MediaPipe Face Mesh** для детекции глаз
- Tracks iris for precise gaze direction / Отслеживает iris (радужку) для точного определения направления взгляда
- Coordinate smoothing for stable cursor / Сглаживание координат для стабильного курсора

#### `CalibrationManager`
- 9-point calibration for accurate mapping / 9-точечная калибровка для точного маппинга
- Homography transform for perspective correction / Homography transform для perspective correction
- Automatic transition to drawing after calibration / Автоматический переход к рисованию после калибровки

#### `DrawingCanvas`
- Dwell-based interaction (gaze hold for activation) / Dwell-based interaction (задержка взгляда для активации)
- Smooth drawing with adjustable thickness / Сглаженное рисование с настраиваемой толщиной
- Stroke undo, clear, and save / Отмена штрихов, очистка, сохранение

## 🔧 Technologies / Технологии

- **Python 3.8+**
- **OpenCV** - Video processing / Обработка видео
- **MediaPipe** - Face and eye detection / Детекция лица и глаз
- **Pygame** - GUI and drawing / GUI и рисование
- **NumPy/SciPy** - Mathematical transformations / Математические трансформации

## 📝 Project History / История проекта

The original **EyeWriter** project was created in C++ using OpenFrameworks. This version is a complete port to Python with modern computer vision libraries.

Оригинальный проект **EyeWriter** был создан на C++ с использованием OpenFrameworks. Данная версия - полный порт на Python с современными computer vision библиотеками.

### Changes from Original / Что изменилось от оригинала:
- ✅ C++/OpenFrameworks → Python/MediaPipe
- ✅ Manual pupil/glint detection → MediaPipe iris tracking / Ручная детекция pupil/glint → MediaPipe iris tracking
- ✅ Complex setup → Works out of the box / Сложная настройка → работает из коробки
- ✅ Requires IR camera → Works with regular webcam / Требует IR камеру → работает с обычной веб-камерой

## 🎯 Applications / Применение

- **Assistive Technology** - For people with cerebral palsy, ALS, spinal cord injuries / Для людей с ДЦП, ALS, травмами спинного мозга
- **Education** - Computer skills training / Обучение работе с компьютером
- **Creativity** - Creating digital art hands-free / Создание цифрового искусства без рук
- **Communication** - Text input, application control / Печать текста, управление приложениями

## 📊 Performance / Производительность

- **FPS**: 30 (adjustable / настраивается)
- **Latency**: ~50ms from eye movement to cursor / ~50ms от движения глаз до курсора
- **Accuracy**: Depends on calibration, typically ±20-30px / Зависит от калибровки, обычно ±20-30px

## 🤝 Contributing / Вклад в проект

Open source project. Pull requests welcome! / Проект open source. Pull requests приветствуются!

### TODO
- [ ] Text typing mode (virtual keyboard) / Режим печати текста (виртуальная клавиатура)
- [ ] Enhanced calibration (more points, automatic) / Улучшенная калибровка (больше точек, автоматическая)
- [ ] Multiple drawing modes (lines, shapes, fill) / Поддержка разных drawing modes (линии, фигуры, заливка)
- [ ] Export to different formats (SVG, PDF) / Экспорт в разные форматы (SVG, PDF)
- [ ] Raspberry Pi version for standalone operation / Raspberry Pi версия для автономной работы

## 📄 License / Лицензия

Open Source - free to use for helping people / Open Source - используйте свободно для помощи людям.

## 👤 Author / Автор

Nurtas Ulagat

Created for **nFactorial Incubator 2026**

**Contact**: nurtasulagat@gmail.com

---

> "Technology should be accessible to everyone, regardless of physical abilities."
> "Технология должна быть доступна всем, независимо от физических возможностей."
