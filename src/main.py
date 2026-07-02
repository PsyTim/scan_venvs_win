
"""
901_scan_venvs - Сканер виртуальных окружений на Windows
"""

import customtkinter as ctk
import psutil


# Настройка темы
ctk.set_appearance_mode("dark")  # или "light"
ctk.set_default_color_theme("blue")


class VenvScanner:
    """Основное приложение"""
    
    def __init__(self):
        # Создаём главное окно
        self.window = ctk.CTk()
        self.window.title("901_scan_venvs - Сканер виртуальных окружений")
        self.window.geometry("800x600")
        
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
        
        # Контейнер для чекбоксов дисков
        self.disks_container = ctk.CTkFrame(disks_frame)
        self.disks_container.pack(pady=5, padx=10, fill="x")
        
        # Получаем и отображаем диски
        self.disk_vars = []
        disks = self.get_available_disks()
        if disks:
            for disk in disks:
                var = ctk.StringVar(value="0")  # 0 - не выбран, 1 - выбран
                cb = ctk.CTkCheckBox(self.disks_container, text=disk, variable=var, onvalue="1", offvalue="0")
                cb.pack(side="left", padx=5)
                self.disk_vars.append((disk, var))
        else:
            ctk.CTkLabel(self.disks_container, text="Не найдено доступных дисков").pack()
        
        # Информация о версии
        version_label = ctk.CTkLabel(
            self.window,
            text="Версия 0.1.2",
            font=("Arial", 14)
        )
        version_label.pack(pady=10)
        
        # Сообщение о готовности
        ready_label = ctk.CTkLabel(
            self.window,
            text="Выберите диски для сканирования",
            font=("Arial", 16)
        )
        ready_label.pack(pady=20)
    
    def get_available_disks(self):
        """Получить список доступных локальных дисков (только физические)"""
        disks = []
        for partition in psutil.disk_partitions():
            # Исключаем CD-ROM и сетевые диски, оставляем только локальные
            if 'cdrom' in partition.opts or partition.fstype == '':
                continue
            disks.append(partition.device)
        return disks
    
    def run(self):
        """Запуск приложения"""
        self.window.mainloop()


if __name__ == "__main__":
    app = VenvScanner()
    app.run()