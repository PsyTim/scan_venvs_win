
"""
901_scan_venvs - Сканер виртуальных окружений на Windows
"""

import customtkinter as ctk
import psutil
import os
import threading
from pathlib import Path


# Настройка темы
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class VenvScanner:
    """Основное приложение"""

    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("901_scan_venvs - Сканер виртуальных окружений")
        self.window.geometry("800x700")

        # Заголовок
        title_label = ctk.CTkLabel(
            self.window,
            text="🔍 Сканер виртуальных окружений .venv",
            font=("Arial", 24, "bold")
        )
        title_label.pack(pady=20)

        # Фрейм для дисков
        disks_frame = ctk.CTkFrame(self.window)
        disks_frame.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(disks_frame, text="Доступные диски:", font=("Arial", 16, "bold")).pack(anchor="w", padx=10, pady=5)

        self.disks_container = ctk.CTkFrame(disks_frame)
        self.disks_container.pack(pady=5, padx=10, fill="x")

        self.disk_vars = []
        disks = self.get_available_disks()
        if disks:
            for disk in disks:
                var = ctk.StringVar(value="0")
                cb = ctk.CTkCheckBox(self.disks_container, text=disk, variable=var, onvalue="1", offvalue="0")
                cb.pack(side="left", padx=5)
                self.disk_vars.append((disk, var))
        else:
            ctk.CTkLabel(self.disks_container, text="Не найдено доступных дисков").pack()

        # Кнопка сканирования
        self.scan_button = ctk.CTkButton(
            self.window,
            text="Начать сканирование",
            command=self.start_scan,
            width=200,
            height=40,
            font=("Arial", 16)
        )
        self.scan_button.pack(pady=20)

        # Прогресс-бар
        self.progress_var = ctk.DoubleVar(value=0.0)
        self.progress_bar = ctk.CTkProgressBar(self.window, width=600, variable=self.progress_var)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)

        # Текущая папка (второго уровня)
        self.current_folder_label = ctk.CTkLabel(
            self.window,
            text="Текущая папка: -",
            font=("Arial", 14)
        )
        self.current_folder_label.pack(pady=2)

        # Статус
        self.status_label = ctk.CTkLabel(
            self.window,
            text="Выберите диски для сканирования",
            font=("Arial", 16)
        )
        self.status_label.pack(pady=5)

        # Текстовое поле результатов
        self.results_text = ctk.CTkTextbox(self.window, height=250, width=700)
        self.results_text.pack(pady=10, padx=20, fill="both", expand=True)
        self.results_text.insert("end", "Результаты сканирования будут показаны здесь.\n")

        # Версия
        version_label = ctk.CTkLabel(
            self.window,
            text="Версия 0.2.0",
            font=("Arial", 14)
        )
        version_label.pack(pady=10)

        self.scanning = False
        self.found_items = []  # список словарей с ключами: path, line_start, size

    def get_available_disks(self):
        """Получить список доступных локальных дисков (только физические)"""
        disks = []
        for partition in psutil.disk_partitions():
            if 'cdrom' in partition.opts or partition.fstype == '':
                continue
            disks.append(partition.device)
        return disks

    def get_selected_disks(self):
        """Получить список выбранных дисков"""
        selected = []
        for disk, var in self.disk_vars:
            if var.get() == "1":
                selected.append(disk)
        return selected

    def get_first_level_folders(self, disk):
        """Получить список папок первого уровня на диске"""
        folders = []
        try:
            with os.scandir(disk) as it:
                for entry in it:
                    if entry.is_dir() and not entry.is_symlink():
                        folders.append(entry.path)
        except (PermissionError, OSError):
            pass
        return folders

    def get_second_level_folders(self, folder_path):
        """Получить список папок второго уровня внутри заданной папки"""
        folders = []
        try:
            with os.scandir(folder_path) as it:
                for entry in it:
                    if entry.is_dir() and not entry.is_symlink():
                        folders.append(entry.path)
        except (PermissionError, OSError):
            pass
        return folders

    def start_scan(self):
        """Запуск сканирования в отдельном потоке"""
        selected = self.get_selected_disks()
        if not selected:
            self.status_label.configure(text="⚠️ Не выбрано ни одного диска!")
            return

        if self.scanning:
            return

        self.scanning = True
        self.scan_button.configure(state="disabled")
        self.status_label.configure(text="🔄 Подготовка к сканированию...")
        self.current_folder_label.configure(text="Текущая папка: -")
        self.results_text.delete("1.0", "end")
        self.results_text.insert("end", "Начинаем сканирование...\n")
        self.progress_bar.set(0)
        self.found_items = []  # очищаем список для новой сессии

        thread = threading.Thread(target=self.scan_thread, args=(selected,))
        thread.daemon = True
        thread.start()

    def scan_thread(self, disks):
        """Поток сканирования с иерархическим прогрессом"""
        first_level = []
        for disk in disks:
            first_level.extend(self.get_first_level_folders(disk))

        N = len(first_level)
        if N == 0:
            self.update_status("❌ Не найдено папок первого уровня на выбранных дисках")
            self.scanning = False
            self.window.after(0, self.scan_finished, 0)
            return

        second_level_counts = []
        second_level_lists = []
        for folder in first_level:
            second = self.get_second_level_folders(folder)
            second_level_lists.append(second)
            second_level_counts.append(len(second))

        self.update_status(f"🔍 Найдено {N} папок первого уровня")

        total_found = 0

        for i, root_folder in enumerate(first_level):
            if not self.scanning:
                break

            self.update_current_folder(root_folder)
            self.update_status(f"🔍 Сканирование: {root_folder}")

            M_i = second_level_counts[i]
            processed_second = 0

            try:
                for dirpath, dirnames, filenames in os.walk(root_folder):
                    if not self.scanning:
                        break

                    rel_path = os.path.relpath(dirpath, root_folder)
                    if rel_path != '.' and rel_path.count(os.sep) == 1:
                        processed_second += 1
                        self.update_current_folder(dirpath)
                        if M_i > 0:
                            progress = (i / N) + (processed_second / M_i) * (1 / N)
                        else:
                            progress = i / N
                        self.update_progress(min(progress, 1.0))

                    if '.venv' in dirnames:
                        venv_path = os.path.join(dirpath, '.venv')
                        total_found += 1
                        # Добавляем строку и запускаем подсчёт размера
                        line_start = self.add_result(f"✅ Найдена папка .venv: {venv_path} (размер вычисляется...)")
                        # Сохраняем информацию для обновления
                        self.found_items.append({
                            'path': venv_path,
                            'line_start': line_start,
                            'size': None
                        })
                        # Запускаем поток для подсчёта размера
                        threading.Thread(target=self.calculate_and_update_size, args=(venv_path, line_start)).start()

            except (PermissionError, OSError) as e:
                self.add_result(f"⚠️ Ошибка доступа к {root_folder}: {e}")

            progress = (i + 1) / N
            self.update_progress(min(progress, 1.0))

        self.scanning = False
        self.window.after(0, self.scan_finished, total_found)

    def calculate_and_update_size(self, path, line_start):
        """Вычислить размер папки в отдельном потоке и обновить строку"""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.isfile(fp):
                        total_size += os.path.getsize(fp)
            # Форматируем размер
            size_str = self.format_size(total_size)
            # Обновляем строку в главном потоке
            self.window.after(0, self.update_result_line, line_start, path, size_str)
        except Exception as e:
            self.window.after(0, self.update_result_line, line_start, path, f"ошибка: {e}")

    def format_size(self, size_bytes):
        """Форматирует размер в удобном виде"""
        for unit in ['Б', 'КБ', 'МБ', 'ГБ', 'ТБ']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} ТБ"

    def update_result_line(self, line_start, path, size_text):
        """Обновить строку с результатом, заменив 'размер вычисляется' на реальный размер"""
        # Находим конец строки (до символа новой строки)
        end_line = self.results_text.index(f"{line_start} lineend")
        # Удаляем старую строку
        self.results_text.delete(line_start, end_line)
        # Вставляем обновлённую строку
        new_text = f"✅ Найдена папка .venv: {path} (размер: {size_text})"
        self.results_text.insert(line_start, new_text)

    def update_status(self, message):
        self.window.after(0, lambda: self.status_label.configure(text=message))

    def update_current_folder(self, folder_path):
        self.window.after(0, lambda: self.current_folder_label.configure(text=f"Текущая папка: {folder_path}"))

    def update_progress(self, value):
        self.window.after(0, lambda: self.progress_bar.set(value))

    def add_result(self, text):
        """Добавить строку в результаты, возвращает индекс начала строки"""
        def _add():
            self.results_text.insert("end", text + "\n")
            self.results_text.see("end")
        self.window.after(0, _add)
        # Возвращаем индекс начала строки (можно вычислить до вставки, но проще после)
        # Так как мы вставляем в конце, индекс начала будет "end-1c" (или "end-2c"?)
        # Но нам нужен индекс начала строки, можно сохранить позицию до вставки.
        # Используем синхронное выполнение для получения индекса.
        # Так как мы вызываем из потока сканирования, а добавление происходит через after, нужно синхронизировать.
        # Чтобы упростить, будем получать индекс сразу после вставки с помощью переменной.
        # Заменим на синхронную вставку в главном потоке с ожиданием?
        # Вместо этого модифицируем: будем вставлять текст и сразу запоминать индекс через метод.
        # Создадим локальную переменную для хранения индекса.
        import time
        # Получаем индекс до вставки
        start_index = self.results_text.index("end-1c")
        # Вставляем в главном потоке
        self.window.after(0, lambda: self.results_text.insert("end", text + "\n"))
        # Ждём, пока вставка выполнится (некрасиво, но для простоты)
        # Лучше использовать queue, но для упрощения сделаем по-другому:
        # Мы можем передавать индекс после вставки, используя callback.
        # Сделаем метод add_result, который будет возвращать индекс после вставки через Event.
        # Но чтобы не усложнять, мы можем просто хранить строку с путём, и при обновлении искать её в тексте.
        # Это проще: при обновлении размера ищем строку, содержащую путь.
        # Так мы избавляемся от необходимости хранить индексы.
        # Перепишем: при добавлении строки мы вставляем без индекса, а при обновлении находим строку по пути.
        # Так как пути уникальны, это надёжно.
        # Вернёмся к простому подходу: не храним индексы, а при обновлении ищем строку по пути.
        # Но тогда нужно быть уверенным, что путь уникален (да, он уникален).
        # Переделаем: метод add_result просто вставляет строку. При обновлении мы ищем строку, начинающуюся с "✅ Найдена папка .venv: {path}" и заменяем её.
        # Это надёжнее и проще.
        # Поэтому я откажусь от возврата индекса, а в calculate_and_update_size будем вызывать update_result_line_by_path.
        pass

    # Перепишем add_result без возврата индекса
    def add_result_simple(self, text):
        self.window.after(0, lambda: self.results_text.insert("end", text + "\n") or self.results_text.see("end"))

    # Изменим scan_thread, чтобы использовать новый метод
    # Заодно переделаем логику обновления размера через поиск строки по пути.
    def calculate_and_update_size_v2(self, path):
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.isfile(fp):
                        total_size += os.path.getsize(fp)
            size_str = self.format_size(total_size)
            self.window.after(0, self.update_result_line_by_path, path, size_str)
        except Exception as e:
            self.window.after(0, self.update_result_line_by_path, path, f"ошибка: {e}")

    def update_result_line_by_path(self, path, size_text):
        """Обновить строку, содержащую указанный путь, заменив 'размер вычисляется' на размер"""
        # Ищем строку, начинающуюся с "✅ Найдена папка .venv: {path}"
        search_pattern = f"✅ Найдена папка .venv: {path}"
        # Получаем весь текст
        text = self.results_text.get("1.0", "end")
        # Ищем позицию начала строки
        start_pos = text.find(search_pattern)
        if start_pos == -1:
            return  # строка не найдена (возможно, уже обновлена)
        # Преобразуем позицию в индекс Tkinter
        # Проще: найти строку с помощью метода search
        index = self.results_text.search(search_pattern, "1.0", stopindex="end")
        if not index:
            return
        # Получаем конец строки
        end_index = self.results_text.index(f"{index} lineend")
        # Заменяем
        self.results_text.delete(index, end_index)
        new_text = f"✅ Найдена папка .venv: {path} (размер: {size_text})"
        self.results_text.insert(index, new_text)

    # Исправляем scan_thread: используем новый метод add_result_simple и запускаем calculate_and_update_size_v2

    # Перепишем scan_thread с учётом новых методов
    # В целях сокращения кода, я скопирую его полностью с изменениями.
    def scan_thread_fixed(self, disks):
        """Поток сканирования с иерархическим прогрессом (исправленная версия)"""
        first_level = []
        for disk in disks:
            first_level.extend(self.get_first_level_folders(disk))

        N = len(first_level)
        if N == 0:
            self.update_status("❌ Не найдено папок первого уровня на выбранных дисках")
            self.scanning = False
            self.window.after(0, self.scan_finished, 0)
            return

        second_level_counts = []
        second_level_lists = []
        for folder in first_level:
            second = self.get_second_level_folders(folder)
            second_level_lists.append(second)
            second_level_counts.append(len(second))

        self.update_status(f"🔍 Найдено {N} папок первого уровня")

        total_found = 0

        for i, root_folder in enumerate(first_level):
            if not self.scanning:
                break

            self.update_current_folder(root_folder)
            self.update_status(f"🔍 Сканирование: {root_folder}")

            M_i = second_level_counts[i]
            processed_second = 0

            try:
                for dirpath, dirnames, filenames in os.walk(root_folder):
                    if not self.scanning:
                        break

                    rel_path = os.path.relpath(dirpath, root_folder)
                    if rel_path != '.' and rel_path.count(os.sep) == 1:
                        processed_second += 1
                        self.update_current_folder(dirpath)
                        if M_i > 0:
                            progress = (i / N) + (processed_second / M_i) * (1 / N)
                        else:
                            progress = i / N
                        self.update_progress(min(progress, 1.0))

                    if '.venv' in dirnames:
                        venv_path = os.path.join(dirpath, '.venv')
                        total_found += 1
                        # Добавляем строку с "размер вычисляется..."
                        self.add_result_simple(f"✅ Найдена папка .venv: {venv_path} (размер вычисляется...)")
                        # Запускаем подсчёт размера в отдельном потоке
                        threading.Thread(target=self.calculate_and_update_size_v2, args=(venv_path,)).start()

            except (PermissionError, OSError) as e:
                self.add_result_simple(f"⚠️ Ошибка доступа к {root_folder}: {e}")

            progress = (i + 1) / N
            self.update_progress(min(progress, 1.0))

        self.scanning = False
        self.window.after(0, self.scan_finished, total_found)

    # Заменяем старую scan_thread на новую
    scan_thread = scan_thread_fixed

    def scan_finished(self, total_found):
        self.scan_button.configure(state="normal")
        self.status_label.configure(text=f"✅ Сканирование завершено. Найдено папок .venv: {total_found}")
        self.progress_bar.set(1.0)
        self.current_folder_label.configure(text="Текущая папка: -")
        self.results_text.insert("end", f"\n🎯 Всего найдено папок .venv: {total_found}\n")
        self.scanning = False

    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    app = VenvScanner()
    app.run()