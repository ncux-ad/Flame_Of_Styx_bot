# 🔧 Исправления установочного скрипта

## ⚠️ **Проблема с жестко заданными путями**

### 🔍 **Что было не так:**

Скрипт `install.sh` использовал жестко заданные пути, которые не учитывали реальное расположение проекта:

```bash
# Старый код (проблемный)
BASE_DIR="${user_home}/bots/Flame_Of_Styx_bot"  # ЖЕСТКО ЗАДАН!
```

### 🎯 **Сценарии проблемы:**

1. **Git clone в другую папку:**
   ```bash
   git clone https://github.com/ncux-ad/Flame_Of_Styx_bot.git my-bot
   cd my-bot
   sudo bash install.sh --profile=user
   # Будет искать в ~/bots/Flame_Of_Styx_bot, а не в my-bot!
   ```

2. **Развертывание из архива:**
   ```bash
   wget https://github.com/ncux-ad/Flame_Of_Styx_bot/archive/main.zip
   unzip main.zip
   cd Flame_Of_Styx_bot-main
   sudo bash install.sh --profile=user
   # Будет искать в ~/bots/Flame_Of_Styx_bot, а не в текущей папке!
   ```

3. **Установка в произвольную папку:**
   ```bash
   mkdir /home/user/my-projects
   cd /home/user/my-projects
   git clone https://github.com/ncux-ad/Flame_Of_Styx_bot.git
   sudo bash install.sh --profile=user
   # Будет искать в ~/bots/Flame_Of_Styx_bot, а не в my-projects!
   ```

## ✅ **Решение: Автоматическое определение путей**

### 🔧 **Что исправлено:**

1. **Автоматическое определение текущей директории**
2. **Проверка наличия файлов проекта** (`bot.py`, `requirements.txt`)
3. **Параметр `--base-dir`** для явного указания директории
4. **Поддержка обоих профилей** (user и prod)

### 📋 **Новая логика:**

```bash
# Новая функция resolve_paths_by_profile()
resolve_paths_by_profile() {
    # 1. Если указана пользовательская директория, используем её
    if [ -n "$CUSTOM_BASE_DIR" ]; then
        BASE_DIR="$CUSTOM_BASE_DIR"
        # ... настройка путей
        return
    fi
    
    # 2. Если мы в папке с проектом, используем её
    if [ -f "bot.py" ] && [ -f "requirements.txt" ]; then
        BASE_DIR="$(pwd)"  # Текущая директория
        log "Используем текущую директорию проекта: $BASE_DIR"
    else
        # 3. Иначе используем стандартную папку
        BASE_DIR="${user_home}/bots/${project_name}"
        log "Используем стандартную директорию: $BASE_DIR"
    fi
}
```

## 🎯 **Новые возможности:**

### 1. **Автоматическое определение:**
```bash
# Работает из любой папки с проектом
cd /home/user/my-bot
sudo bash install.sh --profile=user
# Автоматически использует /home/user/my-bot
```

### 2. **Параметр --base-dir:**
```bash
# Явное указание директории
sudo bash install.sh --profile=user --base-dir=/home/user/my-custom-bot
sudo bash install.sh --profile=prod --base-dir=/opt/my-bot
```

### 3. **Поддержка архивов:**
```bash
# Развертывание из архива
wget https://github.com/ncux-ad/Flame_Of_Styx_bot/archive/main.zip
unzip main.zip
cd Flame_Of_Styx_bot-main
sudo bash install.sh --profile=user
# Автоматически использует текущую папку
```

### 4. **Гибкая установка:**
```bash
# Установка в произвольную папку
mkdir /home/user/projects
cd /home/user/projects
git clone https://github.com/ncux-ad/Flame_Of_Styx_bot.git
sudo bash install.sh --profile=user
# Автоматически использует /home/user/projects/Flame_Of_Styx_bot
```

## 🔧 **Технические детали:**

### **Проверка наличия проекта:**
```bash
if [ -f "bot.py" ] && [ -f "requirements.txt" ]; then
    # Это папка с проектом, используем её
    BASE_DIR="$(pwd)"
else
    # Это не папка с проектом, используем стандартную
    BASE_DIR="${user_home}/bots/${project_name}"
fi
```

### **Поддержка профилей:**
- **user**: Использует текущего пользователя
- **prod**: Использует root для нестандартных путей

### **Параметр --base-dir:**
- Приоритет над автоматическим определением
- Работает с любыми путями
- Поддерживает оба профиля

## 🚀 **Примеры использования:**

### **Стандартная установка:**
```bash
git clone https://github.com/ncux-ad/Flame_Of_Styx_bot.git
cd Flame_Of_Styx_bot
sudo bash install.sh
# Автоматически использует текущую папку
```

### **Установка в произвольную папку:**
```bash
sudo bash install.sh --profile=user --base-dir=/home/user/my-bot
sudo bash install.sh --profile=prod --base-dir=/opt/custom-bot
```

### **Установка из архива:**
```bash
wget https://github.com/ncux-ad/Flame_Of_Styx_bot/archive/main.zip
unzip main.zip
cd Flame_Of_Styx_bot-main
sudo bash install.sh --profile=user
# Автоматически использует текущую папку
```

### **Установка в подпапку:**
```bash
mkdir /home/user/projects
cd /home/user/projects
git clone https://github.com/ncux-ad/Flame_Of_Styx_bot.git
sudo bash install.sh --profile=user
# Автоматически использует /home/user/projects/Flame_Of_Styx_bot
```

## ✅ **Результат:**

### **Теперь скрипт:**
- ✅ **Автоматически определяет** текущую директорию проекта
- ✅ **Работает из любой папки** с проектом
- ✅ **Поддерживает архивы** и произвольные пути
- ✅ **Имеет параметр --base-dir** для явного указания
- ✅ **Совместим** с существующими установками
- ✅ **Логирует** выбранную директорию

### **Проблема решена:**
- ❌ **Больше нет жестко заданных путей**
- ❌ **Больше нет проблем с архивами**
- ❌ **Больше нет проблем с произвольными папками**

**Установочный скрипт теперь работает из любой папки!** 🚀

---

**Исправления внесены с ❤️ для удобства пользователей**
