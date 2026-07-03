
"""
901_scan_venvs - Сканер виртуальных окружений на Windows
"""

import customtkinter as ctk
import psutil
import os
import threading
import subprocess
import re
from datetime import datetime


# Настройка темы
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class VenvScanner:
    """Основное приложение"""

    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("901_scan_venvs - Сканер виртуальных окружений")
        self.window.geometry("800x780")

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

        # Метка общего размера
        self.total_size_label = ctk.CTkLabel(
            self.window,
            text="Общий размер найденных папок: 0 Б",
            font=("Arial", 14, "bold")
        )
        self.total_size_label.pack(pady=5)

        # Фрейм для кнопок сортировки
        sort_frame = ctk.CTkFrame(self.window)
        sort_frame.pack(pady=5, padx=20, fill="x")

        ctk.CTkLabel(sort_frame, text="Сортировка:", font=("Arial", 14)).pack(side="left", padx=10)

        self.sort_buttons = {}
        sort_options = [
            ("По дате создания", "ctime"),
            ("По дате изменения", "mtime"),
            ("По размеру", "size"),
            ("По пути", "path")
        ]
        for label, key in sort_options:
            btn = ctk.CTkButton(
                sort_frame,
                text=label,
                command=lambda k=key: self.apply_sort(k),
                width=120,
                height=30,
                font=("Arial", 12)
            )
            btn.pack(side="left", padx=5)
            self.sort_buttons[key] = btn

        # Текстовое поле результатов
        self.results_text = ctk.CTkTextbox(self.window, height=200, width=700)
        self.results_text.pack(pady=10, padx=20, fill="both", expand=True)
        self.results_text.insert("end", "Результаты сканирования будут показаны здесь.\n")
        self.results_text.bind("<Button-1>", self.on_result_click)

        # Версия
        version_label = ctk.CTkLabel(
            self.window,
            text="Версия 0.2.1",
            font=("Arial", 14)
        )
        version_label.pack(pady=10)

        self.scanning = False
        self.total_size_bytes = 0
        self.folders_data = []          # список словарей: path, size, ctime, mtime, size_str
        self.size_calculated = False    # флаг, что все размеры вычислены
        self.current_sort = "ctime"     # текущий критерий сортировки

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
        self.total_size_bytes = 0
        self.update_total_size_label(0)
        self.folders_data = []
        self.size_calculated = False
        self.current_sort = "ctime"

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
                        # Получаем время создания и изменения
                        try:
                            ctime = os.path.getctime(venv_path)
                            mtime = os.path.getmtime(venv_path)
                        except OSError:
                            ctime = 0
                            mtime = 0
                        # Добавляем запись в данные
                        self.folders_data.append({
                            'path': venv_path,
                            'size': None,
                            'size_str': 'вычисляется...',
                            'ctime': ctime,
                            'mtime': mtime
                        })
                        # Добавляем строку с "размер вычисляется..."
                        self.add_result_simple(f"✅ Найдена папка .venv: {venv_path} (размер вычисляется...)")
                        # Запускаем подсчёт размера в отдельном потоке
                        threading.Thread(target=self.calculate_and_update_size, args=(venv_path,)).start()

            except (PermissionError, OSError) as e:
                self.add_result_simple(f"⚠️ Ошибка доступа к {root_folder}: {e}")

            progress = (i + 1) / N
            self.update_progress(min(progress, 1.0))

        self.scanning = False
        self.window.after(0, self.scan_finished, total_found)

    def calculate_and_update_size(self, path):
        """Вычислить размер папки и обновить строку и общий размер"""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.isfile(fp):
                        total_size += os.path.getsize(fp)
            size_str = self.format_size(total_size)
            # Обновляем данные
            for item in self.folders_data:
                if item['path'] == path:
                    item['size'] = total_size
                    item['size_str'] = size_str
                    break
            # Обновляем строку
            self.window.after(0, self.update_result_line_by_path, path, size_str)
            # Добавляем к общему размеру
            self.total_size_bytes += total_size
            self.window.after(0, self.update_total_size_label, self.total_size_bytes)
        except Exception as e:
            self.window.after(0, self.update_result_line_by_path, path, f"ошибка: {e}")

    def format_size(self, size_bytes):
        """Форматирует размер в удобном виде"""
        for unit in ['Б', 'КБ', 'МБ', 'ГБ', 'ТБ']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} ТБ"

    def update_result_line_by_path(self, path, size_text):
        """Обновить строку, содержащую указанный путь, заменив 'размер вычисляется' на размер"""
        search_pattern = f"✅ Найдена папка .venv: {path}"
        index = self.results_text.search(search_pattern, "1.0", stopindex="end")
        if not index:
            return
        end_index = self.results_text.index(f"{index} lineend")
        self.results_text.delete(index, end_index)
        new_text = f"✅ Найдена папка .venv: {path} (размер: {size_text})"
        self.results_text.insert(index, new_text)

    def update_total_size_label(self, total_bytes):
        """Обновить метку общего размера"""
        self.total_size_label.configure(text=f"Общий размер найденных папок: {self.format_size(total_bytes)}")

    def on_result_click(self, event):
        """Обработчик клика по текстовому полю"""
        index = self.results_text.index(f"@{event.x},{event.y}")
        line = self.results_text.get(f"{index} linestart", f"{index} lineend")
        match = re.search(r'✅ Найдена папка \.venv: (.+?)(?: \(размер:.*?\))?$', line)
        if match:
            path = match.group(1).strip()
            if os.name == 'nt':
                subprocess.Popen(['explorer', os.path.dirname(path)])
            else:
                pass

    def scan_finished(self, total_found):
        """Завершение сканирования: ожидание вычисления размеров и отображение результатов"""
        if total_found == 0:
            self.scan_button.configure(state="normal")
            self.status_label.configure(text="✅ Сканирование завершено. Папок .venv не найдено.")
            self.progress_bar.set(1.0)
            self.current_folder_label.configure(text="Текущая папка: -")
            self.scanning = False
            return

        # Начинаем ожидание завершения вычисления размеров
        self.status_label.configure(text="⏳ Ожидание вычисления размеров...")
        self.wait_for_sizes_and_display()

    def wait_for_sizes_and_display(self):
        """Проверяет, все ли размеры вычислены, и отображает отсортированные результаты"""
        # Проверяем, все ли элементы имеют size не None
        all_computed = all(item['size'] is not None for item in self.folders_data)
        if all_computed:
            self.size_calculated = True
            self.display_sorted_results(self.current_sort)
            self.scan_button.configure(state="normal")
            self.status_label.configure(text="✅ Сканирование завершено. Все размеры вычислены.")
            self.progress_bar.set(1.0)
            self.current_folder_label.configure(text="Текущая папка: -")
            self.scanning = False
        else:
            # Проверяем через 500 мс
            self.window.after(500, self.wait_for_sizes_and_display)

    def display_sorted_results(self, sort_key):
        """Отображает результаты, отсортированные по указанному ключу"""
        if not self.folders_data:
            return

        # Определяем порядок сортировки
        reverse = True  # по умолчанию убывание
        if sort_key == "path":
            reverse = False  # путь – по возрастанию

        # Сортировка
        if sort_key == "size":
            sorted_data = sorted(self.folders_data, key=lambda x: x['size'] if x['size'] is not None else 0, reverse=reverse)
        elif sort_key == "ctime":
            sorted_data = sorted(self.folders_data, key=lambda x: x['ctime'], reverse=reverse)
        elif sort_key == "mtime":
            sorted_data = sorted(self.folders_data, key=lambda x: x['mtime'], reverse=reverse)
        else:  # path
            sorted_data = sorted(self.folders_data, key=lambda x: x['path'].lower(), reverse=reverse)

        # Перестраиваем текстовое поле
        self.results_text.delete("1.0", "end")
        header = f"Результаты сканирования (сортировка: {sort_key}, {'убывание' if reverse else 'возрастание'}):\n"
        self.results_text.insert("end", header)
        for item in sorted_data:
            size_str = item['size_str']
            line = f"✅ Найдена папка .venv: {item['path']} (размер: {size_str})"
            self.results_text.insert("end", line + "\n")
        # Добавляем итоговую строку
        total = len(self.folders_data)
        self.results_text.insert("end", f"\n🎯 Всего найдено папок .venv: {total}\n")
        self.current_sort = sort_key

    def apply_sort(self, sort_key):
        """Обработчик нажатия кнопки сортировки"""
        if not self.folders_data:
            return
        if not self.size_calculated:
            self.status_label.configure(text="⚠️ Подождите завершения вычисления размеров")
            return
        self.display_sorted_results(sort_key)

    def update_status(self, message):
        self.window.after(0, lambda: self.status_label.configure(text=message))

    def update_current_folder(self, folder_path):
        self.window.after(0, lambda: self.current_folder_label.configure(text=f"Текущая папка: {folder_path}"))

    def update_progress(self, value):
        self.window.after(0, lambda: self.progress_bar.set(value))

    def add_result_simple(self, text):
        self.window.after(0, lambda: self.results_text.insert("end", text + "\n") or self.results_text.see("end"))

    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    app = VenvScanner()
    app.run()