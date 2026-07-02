# 1. Переходим в папку проекта
cd 901_scan_venvs

# 2. Создаём виртуальное окружение
uv venv --python 3.10.9

# 3. Активируем (выберите одну команду):
# Для CMD:
.venv\Scripts\activate.bat
# Для PowerShell:
.venv\Scripts\Activate.ps1
# 4. Устанавливаем зависимости
uv pip install -r requirements.txt

# 5. Запускаем приложение
python src/main.py