"""
901_scan_venvs - Сканер виртуальных окружений на Windows
"""

import customtkinter as ctk


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
        title_label.pack(pady=50)
        
        # Информация о версии
        version_label = ctk.CTkLabel(
            self.window,
            text="Версия 0.1.1",
            font=("Arial", 14)
        )
        version_label.pack(pady=10)
        
        # Сообщение о готовности
        ready_label = ctk.CTkLabel(
            self.window,
            text="Приложение готово к работе",
            font=("Arial", 16)
        )
        ready_label.pack(pady=30)
    
    def run(self):
        """Запуск приложения"""
        self.window.mainloop()


if __name__ == "__main__":
    app = VenvScanner()
    app.run()