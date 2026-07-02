
"""
901_scan_venvs - Сканер виртуальных окружений на Windows
"""

import customtkinter as ctk
import psutil
import os
import threading


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
            text="Версия 0.1.3",
            font=("Arial", 14)
        )
        version_label.pack(pady=10)

        self.scanning = False

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
        """Получить список папок первого уровня на диске (непосредственно в корне)"""
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
        """Получить список папок второго уровня внутри заданной папки (непосредственные подпапки)"""
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

        thread = threading.Thread(target=self.scan_thread, args=(selected,))
        thread.daemon = True
        thread.start()

    def scan_thread(self, disks):
        """Поток сканирования с иерархическим прогрессом"""
        # Собираем все папки первого уровня со всех дисков
        first_level = []
        for disk in disks:
            first_level.extend(self.get_first_level_folders(disk))

        N = len(first_level)
        if N == 0:
            self.update_status("❌ Не найдено папок первого уровня на выбранных дисках")
            self.scanning = False
            self.window.after(0, self.scan_finished, 0)
            return

        # Для каждой папки первого уровня собираем папки второго уровня
        second_level_counts = []
        second_level_lists = []
        for folder in first_level:
            second = self.get_second_level_folders(folder)
            second_level_lists.append(second)
            second_level_counts.append(len(second))

        self.update_status(f"🔍 Найдено {N} папок первого уровня")

        total_found = 0

        # Итерация по папкам первого уровня
        for i, root_folder in enumerate(first_level):
            if not self.scanning:
                break

            # Обновляем статус: текущая папка первого уровня
            self.update_current_folder(root_folder)
            self.update_status(f"🔍 Сканирование: {root_folder}")

            M_i = second_level_counts[i]
            processed_second = 0

            # Сканируем всю папку первого уровня рекурсивно через os.walk
            # При этом будем отслеживать папки второго уровня для обновления прогресса
            # и одновременно искать .venv
            try:
                for dirpath, dirnames, filenames in os.walk(root_folder):
                    if not self.scanning:
                        break

                    # Проверяем, является ли текущая папка папкой второго уровня
                    # Для этого вычисляем относительный путь от root_folder
                    rel_path = os.path.relpath(dirpath, root_folder)
                    # Если rel_path == '.' — это сама root_folder (первый уровень)
                    # Если количество разделителей == 1 — это папка второго уровня
                    if rel_path != '.' and rel_path.count(os.sep) == 1:
                        # Это папка второго уровня
                        processed_second += 1
                        self.update_current_folder(dirpath)
                        # Прогресс: (i/N) + (processed_second / M_i) * (1/N), но если M_i == 0, то сразу переходим к следующему
                        if M_i > 0:
                            progress = (i / N) + (processed_second / M_i) * (1 / N)
                        else:
                            # Если нет папок второго уровня, то прогресс остаётся i/N до завершения всей папки
                            progress = i / N
                        self.update_progress(min(progress, 1.0))

                    # Проверяем наличие .venv в текущей папке
                    if '.venv' in dirnames:
                        venv_path = os.path.join(dirpath, '.venv')
                        total_found += 1
                        self.add_result(f"✅ Найдена папка .venv: {venv_path}")

            except (PermissionError, OSError) as e:
                self.add_result(f"⚠️ Ошибка доступа к {root_folder}: {e}")

            # После завершения os.walk для этой папки первого уровня,
            # прогресс должен стать (i+1)/N
            # Если M_i == 0, то мы уже установили прогресс = i/N, теперь добавляем 1/N
            if M_i == 0:
                progress = (i + 1) / N
                self.update_progress(min(progress, 1.0))
            else:
                # Убедимся, что прогресс достиг (i+1)/N (может быть небольшая погрешность)
                progress = (i + 1) / N
                self.update_progress(min(progress, 1.0))

        # Завершение
        self.scanning = False
        self.window.after(0, self.scan_finished, total_found)

    def update_status(self, message):
        self.window.after(0, lambda: self.status_label.configure(text=message))

    def update_current_folder(self, folder_path):
        self.window.after(0, lambda: self.current_folder_label.configure(text=f"Текущая папка: {folder_path}"))

    def update_progress(self, value):
        self.window.after(0, lambda: self.progress_bar.set(value))

    def add_result(self, text):
        def _add():
            self.results_text.insert("end", text + "\n")
            self.results_text.see("end")
        self.window.after(0, _add)

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