
"""
Юнит-тесты для модуля сканирования виртуальных окружений.

Запуск:
    pytest tests/

Для запуска с покрытием:
    pytest --cov=src tests/
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock, call

# Добавляем путь к src для импорта main
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from main import VenvScanner


class TestVenvScanner:
    """Тесты для класса VenvScanner (с моками GUI)."""

    @pytest.fixture
    def scanner(self, mocker):
        """
        Фикстура, создающая экземпляр VenvScanner без реального GUI.
        """
        # Мокаем StringVar
        mock_stringvar = MagicMock()
        mock_stringvar.get = MagicMock(return_value="0")
        mock_stringvar.set = MagicMock()
        mocker.patch('customtkinter.StringVar', return_value=mock_stringvar)

        # Мокаем окно
        mock_window = MagicMock(spec=['title', 'geometry', 'mainloop', 'after', 'destroy'])
        mock_window.title = MagicMock()
        mock_window.geometry = MagicMock()
        mock_window.mainloop = MagicMock()
        mock_window.after = MagicMock()

        # Мокаем виджеты
        mock_widget = MagicMock(spec=['pack', 'configure', 'insert', 'delete', 'bind', 'get', 'index', 'see', 'search'])
        mock_widget.pack = MagicMock()
        mock_widget.configure = MagicMock()
        mock_widget.insert = MagicMock()
        mock_widget.delete = MagicMock()
        mock_widget.bind = MagicMock()
        mock_widget.get = MagicMock()
        mock_widget.index = MagicMock()
        mock_widget.see = MagicMock()
        mock_widget.search = MagicMock()

        # Патчим все классы customtkinter
        mocker.patch('customtkinter.CTk', return_value=mock_window)
        mocker.patch('customtkinter.CTkLabel', return_value=mock_widget)
        mocker.patch('customtkinter.CTkFrame', return_value=mock_widget)
        mocker.patch('customtkinter.CTkButton', return_value=mock_widget)
        mocker.patch('customtkinter.CTkProgressBar', return_value=MagicMock(spec=['pack', 'configure', 'set']))
        mocker.patch('customtkinter.CTkTextbox', return_value=MagicMock(spec=['pack', 'configure', 'insert', 'delete', 'bind', 'get', 'index', 'see', 'search']))
        mocker.patch('customtkinter.CTkCheckBox', return_value=mock_widget)
        mocker.patch('customtkinter.set_appearance_mode')
        mocker.patch('customtkinter.set_default_color_theme')
        mocker.patch('customtkinter.DoubleVar', return_value=MagicMock())

        # Создаём экземпляр приложения
        app = VenvScanner()
        # Подменяем results_text на отдельный мок
        app.results_text = MagicMock(spec=['insert', 'delete', 'get', 'index', 'search', 'see', 'bind'])
        app.window = mock_window
        return app

    # 1. Тест get_available_disks
    @patch('psutil.disk_partitions')
    def test_get_available_disks(self, mock_partitions, scanner):
        mock_partitions.return_value = [
            MagicMock(device='C:\\', opts='rw,fixed', fstype='NTFS'),
            MagicMock(device='D:\\', opts='rw,fixed', fstype='NTFS'),
            MagicMock(device='E:\\', opts='cdrom', fstype='CDFS'),
            MagicMock(device='Z:\\', opts='rw,remote', fstype=''),
        ]
        assert scanner.get_available_disks() == ['C:\\', 'D:\\']

    # 2. Тест get_selected_disks
    def test_get_selected_disks(self, scanner):
        scanner.disk_vars = [
            ('C:\\', MagicMock(get=lambda: '1')),
            ('D:\\', MagicMock(get=lambda: '0')),
            ('E:\\', MagicMock(get=lambda: '1')),
        ]
        assert scanner.get_selected_disks() == ['C:\\', 'E:\\']

    # 3. Тест format_size
    def test_format_size(self, scanner):
        assert scanner.format_size(0) == '0.00 Б'
        assert scanner.format_size(500) == '500.00 Б'
        assert scanner.format_size(1024) == '1.00 КБ'
        assert scanner.format_size(1234567) == '1.18 МБ'
        assert scanner.format_size(1234567890) == '1.15 ГБ'
        assert scanner.format_size(1234567890123) == '1.12 ТБ'

    # 4. Тест get_first_level_folders
    @patch('os.scandir')
    def test_get_first_level_folders(self, mock_scandir, scanner):
        mock_entry1 = MagicMock()
        mock_entry1.is_dir.return_value = True
        mock_entry1.is_symlink.return_value = False
        mock_entry1.path = 'C:\\Users'

        mock_entry2 = MagicMock()
        mock_entry2.is_dir.return_value = True
        mock_entry2.is_symlink.return_value = False
        mock_entry2.path = 'C:\\Windows'

        mock_entry3 = MagicMock()
        mock_entry3.is_dir.return_value = False
        mock_entry3.path = 'C:\\pagefile.sys'

        mock_context = MagicMock()
        mock_context.__enter__.return_value = [mock_entry1, mock_entry2, mock_entry3]
        mock_context.__exit__.return_value = False
        mock_scandir.return_value = mock_context

        assert scanner.get_first_level_folders('C:\\') == ['C:\\Users', 'C:\\Windows']

    # 5. Тест get_second_level_folders
    @patch('os.scandir')
    def test_get_second_level_folders(self, mock_scandir, scanner):
        mock_entry1 = MagicMock()
        mock_entry1.is_dir.return_value = True
        mock_entry1.is_symlink.return_value = False
        mock_entry1.path = 'C:\\Users\\Admin'

        mock_entry2 = MagicMock()
        mock_entry2.is_dir.return_value = True
        mock_entry2.is_symlink.return_value = False
        mock_entry2.path = 'C:\\Users\\Guest'

        mock_context = MagicMock()
        mock_context.__enter__.return_value = [mock_entry1, mock_entry2]
        mock_context.__exit__.return_value = False
        mock_scandir.return_value = mock_context

        assert scanner.get_second_level_folders('C:\\Users') == ['C:\\Users\\Admin', 'C:\\Users\\Guest']

    # 6. Тест add_result_simple
    def test_add_result_simple(self, scanner):
        mock_text = MagicMock()
        mock_text.insert.return_value = None
        scanner.results_text = mock_text

        mock_after = MagicMock()
        scanner.window.after = mock_after

        scanner.add_result_simple("test")
        mock_after.assert_called_once()
        args, kwargs = mock_after.call_args
        assert args[0] == 0
        assert callable(args[1])
        func = args[1]
        func()
        mock_text.insert.assert_called_once_with("end", "test\n")
        mock_text.see.assert_called_once_with("end")

    # 7. Тест update_result_line_by_path
    def test_update_result_line_by_path(self, scanner):
        mock_text = MagicMock()
        mock_text.get.return_value = "some text\n✅ Найдена папка .venv: C:\\test\\.venv (размер вычисляется...)\n"
        mock_text.search.return_value = "2.0"
        mock_text.index.return_value = "2.0 lineend"
        scanner.results_text = mock_text

        scanner.update_result_line_by_path("C:\\test\\.venv", "1.2 МБ")

        mock_text.search.assert_called_once_with("✅ Найдена папка .venv: C:\\test\\.venv", "1.0", stopindex="end")
        mock_text.delete.assert_called_once_with("2.0", "2.0 lineend")
        mock_text.insert.assert_called_once_with(
            "2.0",
            "✅ Найдена папка .venv: C:\\test\\.venv (размер: 1.2 МБ)"
        )

    # 8. Тест calculate_and_update_size
    @patch('os.walk')
    @patch('os.path.isfile', return_value=True)
    def test_calculate_and_update_size(self, mock_isfile, mock_walk, scanner):
        mock_walk.return_value = [
            ('C:\\test\\.venv', ['subdir'], ['file1.txt', 'file2.txt']),
            ('C:\\test\\.venv\\subdir', [], ['file3.txt']),
        ]
        with patch('os.path.getsize') as mock_getsize:
            mock_getsize.side_effect = [100, 200, 50]
            mock_after = MagicMock()
            scanner.window.after = mock_after

            with patch.object(scanner, 'update_result_line_by_path') as mock_update:
                with patch.object(scanner, 'update_total_size_label') as mock_total:
                    scanner.calculate_and_update_size("C:\\test\\.venv")

                    assert mock_after.call_count == 2
                    # Первый вызов: update_result_line_by_path
                    first_call = mock_after.call_args_list[0]
                    assert first_call[0][0] == 0
                    func = first_call[0][1]
                    path_arg = first_call[0][2]
                    size_arg = first_call[0][3]
                    assert path_arg == "C:\\test\\.venv"
                    assert size_arg == "350.00 Б"
                    func(path_arg, size_arg)
                    mock_update.assert_called_once_with("C:\\test\\.venv", "350.00 Б")

                    # Второй вызов: update_total_size_label
                    second_call = mock_after.call_args_list[1]
                    assert second_call[0][0] == 0
                    func2 = second_call[0][1]
                    total_arg = second_call[0][2]
                    assert total_arg == 350
                    func2(total_arg)
                    mock_total.assert_called_once_with(350)

    # 9. Тест scan_thread
    @patch('os.walk')
    @patch('os.scandir')
    def test_scan_thread(self, mock_scandir, mock_walk, scanner):
        mock_entry1 = MagicMock()
        mock_entry1.is_dir.return_value = True
        mock_entry1.is_symlink.return_value = False
        mock_entry1.path = 'C:\\Users'
        mock_context1 = MagicMock()
        mock_context1.__enter__.return_value = [mock_entry1]
        mock_context1.__exit__.return_value = False

        mock_entry2 = MagicMock()
        mock_entry2.is_dir.return_value = True
        mock_entry2.is_symlink.return_value = False
        mock_entry2.path = 'C:\\Users\\Admin'
        mock_context2 = MagicMock()
        mock_context2.__enter__.return_value = [mock_entry2]
        mock_context2.__exit__.return_value = False

        mock_scandir.side_effect = [mock_context1, mock_context2]

        mock_walk.return_value = [
            ('C:\\Users\\Admin\\project', ['venv', '.venv'], ['file.py']),
        ]

        scanner.add_result_simple = MagicMock()
        scanner.calculate_and_update_size = MagicMock()
        scanner.update_status = MagicMock()
        scanner.update_current_folder = MagicMock()
        scanner.update_progress = MagicMock()
        scanner.scan_finished = MagicMock()

        def immediate_after(delay, func, *args, **kwargs):
            func(*args, **kwargs)
        scanner.window.after = immediate_after

        scanner.scanning = True
        scanner.scan_thread(['C:\\'])

        scanner.add_result_simple.assert_called_once_with(
            "✅ Найдена папка .venv: C:\\Users\\Admin\\project\\.venv (размер вычисляется...)"
        )
        scanner.calculate_and_update_size.assert_called_once_with(
            "C:\\Users\\Admin\\project\\.venv"
        )
        scanner.scan_finished.assert_called_once_with(1)

    # 10. Тест scan_thread когда нет папок первого уровня
    @patch('os.scandir')
    def test_scan_thread_no_first_level(self, mock_scandir, scanner):
        mock_context = MagicMock()
        mock_context.__enter__.return_value = []
        mock_context.__exit__.return_value = False
        mock_scandir.return_value = mock_context

        scanner.update_status = MagicMock()
        scanner.scan_finished = MagicMock()
        scanner.window.after = MagicMock()

        scanner.scanning = True
        scanner.scan_thread(['C:\\'])

        scanner.update_status.assert_called_once_with("❌ Не найдено папок первого уровня на выбранных дисках")
        scanner.window.after.assert_called_once()
        args, kwargs = scanner.window.after.call_args
        assert args[0] == 0
        func = args[1]
        func(0)  # вызываем scan_finished с 0
        scanner.scan_finished.assert_called_once_with(0)

    # 11. Тест scan_thread с ошибкой доступа внутри os.walk
    @patch('os.walk')
    @patch('os.scandir')
    def test_scan_thread_permission_error(self, mock_scandir, mock_walk, scanner):
        mock_entry1 = MagicMock()
        mock_entry1.is_dir.return_value = True
        mock_entry1.is_symlink.return_value = False
        mock_entry1.path = 'C:\\Users'
        mock_context1 = MagicMock()
        mock_context1.__enter__.return_value = [mock_entry1]
        mock_context1.__exit__.return_value = False

        mock_entry2 = MagicMock()
        mock_entry2.is_dir.return_value = True
        mock_entry2.is_symlink.return_value = False
        mock_entry2.path = 'C:\\Users\\Admin'
        mock_context2 = MagicMock()
        mock_context2.__enter__.return_value = [mock_entry2]
        mock_context2.__exit__.return_value = False

        mock_scandir.side_effect = [mock_context1, mock_context2]

        mock_walk.side_effect = PermissionError("Access denied")

        scanner.add_result_simple = MagicMock()
        scanner.update_status = MagicMock()
        scanner.update_current_folder = MagicMock()
        scanner.update_progress = MagicMock()
        scanner.scan_finished = MagicMock()
        scanner.window.after = MagicMock()

        scanner.scanning = True
        scanner.scan_thread(['C:\\'])

        scanner.add_result_simple.assert_called_once_with("⚠️ Ошибка доступа к C:\\Users: Access denied")

        scanner.window.after.assert_called_once()
        args, kwargs = scanner.window.after.call_args
        assert args[0] == 0
        func = args[1]
        func(0)
        scanner.scan_finished.assert_called_once_with(0)

    # 12. Тест scan_finished (total_found == 0)
    def test_scan_finished_zero(self, scanner):
        scanner.scan_button = MagicMock()
        scanner.status_label = MagicMock()
        scanner.progress_bar = MagicMock()
        scanner.current_folder_label = MagicMock()
        scanner.results_text = MagicMock()

        scanner.scan_finished(0)

        scanner.scan_button.configure.assert_called_once_with(state="normal")
        scanner.status_label.configure.assert_called_once_with(text="✅ Сканирование завершено. Папок .venv не найдено.")
        scanner.progress_bar.set.assert_called_once_with(1.0)
        scanner.current_folder_label.configure.assert_called_once_with(text="Текущая папка: -")
        assert scanner.scanning == False

    # 13. Тест scan_finished (total_found > 0)
    def test_scan_finished_positive(self, scanner):
        scanner.scan_button = MagicMock()
        scanner.status_label = MagicMock()
        scanner.progress_bar = MagicMock()
        scanner.current_folder_label = MagicMock()
        scanner.results_text = MagicMock()

        scanner.wait_for_sizes_and_display = MagicMock()
        scanner.scanning = True

        scanner.scan_finished(5)

        scanner.status_label.configure.assert_called_once_with(text="⏳ Ожидание вычисления размеров...")
        scanner.scan_button.configure.assert_not_called()
        scanner.progress_bar.set.assert_not_called()
        scanner.current_folder_label.configure.assert_not_called()
        assert scanner.scanning == True
        scanner.wait_for_sizes_and_display.assert_called_once()

    # 14. Тест update_status
    def test_update_status(self, scanner):
        mock_after = MagicMock()
        scanner.window.after = mock_after
        scanner.status_label = MagicMock()

        scanner.update_status("test message")
        mock_after.assert_called_once()
        args, kwargs = mock_after.call_args
        assert args[0] == 0
        func = args[1]
        func()
        scanner.status_label.configure.assert_called_once_with(text="test message")

    # 15. Тест update_current_folder
    def test_update_current_folder(self, scanner):
        mock_after = MagicMock()
        scanner.window.after = mock_after
        scanner.current_folder_label = MagicMock()

        scanner.update_current_folder("C:\\test")
        mock_after.assert_called_once()
        args, kwargs = mock_after.call_args
        assert args[0] == 0
        func = args[1]
        func()
        scanner.current_folder_label.configure.assert_called_once_with(text="Текущая папка: C:\\test")

    # 16. Тест update_progress
    def test_update_progress(self, scanner):
        mock_after = MagicMock()
        scanner.window.after = mock_after
        scanner.progress_bar = MagicMock()

        scanner.update_progress(0.5)
        mock_after.assert_called_once()
        args, kwargs = mock_after.call_args
        assert args[0] == 0
        func = args[1]
        func()
        scanner.progress_bar.set.assert_called_once_with(0.5)

    # 17. Тест run()
    def test_run(self, scanner):
        mock_mainloop = MagicMock()
        scanner.window.mainloop = mock_mainloop
        scanner.run()
        mock_mainloop.assert_called_once()

    # 18. Тест get_first_level_folders с ошибкой
    @patch('os.scandir')
    def test_get_first_level_folders_error(self, mock_scandir, scanner):
        mock_scandir.side_effect = PermissionError("Access denied")
        result = scanner.get_first_level_folders('C:\\')
        assert result == []

    # 19. Тест get_second_level_folders с ошибкой
    @patch('os.scandir')
    def test_get_second_level_folders_error(self, mock_scandir, scanner):
        mock_scandir.side_effect = PermissionError("Access denied")
        result = scanner.get_second_level_folders('C:\\Users')
        assert result == []

    # 20. Тест start_scan с невыбранными дисками
    def test_start_scan_no_disks(self, scanner):
        scanner.get_selected_disks = MagicMock(return_value=[])
        scanner.status_label = MagicMock()
        scanner.start_scan()
        scanner.status_label.configure.assert_called_once_with(text="⚠️ Не выбрано ни одного диска!")

    # 21. Тест start_scan когда scanning уже True
    def test_start_scan_already_scanning(self, scanner):
        scanner.scanning = True
        scanner.get_selected_disks = MagicMock(return_value=['C:\\'])
        scanner.status_label = MagicMock()
        scanner.start_scan()
        scanner.status_label.configure.assert_not_called()

    # 22. Тест on_result_click
    def test_on_result_click(self, scanner):
        class MockEvent:
            x = 10
            y = 10

        mock_text = MagicMock()
        mock_text.index.return_value = "2.0"
        mock_text.get.return_value = "✅ Найдена папка .venv: C:\\test\\.venv (размер: 1.2 МБ)"
        scanner.results_text = mock_text

        with patch('subprocess.Popen') as mock_popen:
            scanner.on_result_click(MockEvent())
            mock_popen.assert_called_once_with(['explorer', 'C:\\test'])

    # 23. Тест on_result_click когда строка не содержит .venv
    def test_on_result_click_no_venv(self, scanner):
        class MockEvent:
            x = 10
            y = 10

        mock_text = MagicMock()
        mock_text.index.return_value = "2.0"
        mock_text.get.return_value = "Some other text"
        scanner.results_text = mock_text

        with patch('subprocess.Popen') as mock_popen:
            scanner.on_result_click(MockEvent())
            mock_popen.assert_not_called()

    # 24. Тест display_sorted_results
    def test_display_sorted_results(self, scanner):
        scanner.folders_data = [
            {'path': 'D:\\proj2\\.venv', 'size': 5000000, 'ctime': 1000, 'mtime': 2000, 'size_str': '4.77 МБ'},
            {'path': 'C:\\proj1\\.venv', 'size': 1000000, 'ctime': 3000, 'mtime': 1500, 'size_str': '0.95 МБ'},
            {'path': 'E:\\proj3\\.venv', 'size': 2000000, 'ctime': 500, 'mtime': 2500, 'size_str': '1.91 МБ'},
        ]
        scanner.results_text = MagicMock()
        scanner.size_calculated = True

        scanner.display_sorted_results('size')
        scanner.results_text.delete.assert_called_once_with("1.0", "end")
        assert scanner.results_text.insert.call_count >= 5

    # 25. Тест display_sorted_results с пустыми данными
    def test_display_sorted_results_empty(self, scanner):
        scanner.folders_data = []
        scanner.results_text = MagicMock()
        scanner.display_sorted_results('size')
        scanner.results_text.delete.assert_not_called()
        scanner.results_text.insert.assert_not_called()

    # 26. Тест apply_sort когда нет данных
    def test_apply_sort_no_data(self, scanner):
        scanner.folders_data = []
        scanner.status_label = MagicMock()
        scanner.apply_sort('size')
        scanner.status_label.configure.assert_not_called()

    # 27. Тест apply_sort когда размеры не вычислены
    def test_apply_sort_not_calculated(self, scanner):
        scanner.folders_data = [{'path': 'C:\\test\\.venv', 'size': None}]
        scanner.size_calculated = False
        scanner.status_label = MagicMock()
        scanner.apply_sort('size')
        scanner.status_label.configure.assert_called_once_with(text="⚠️ Подождите завершения вычисления размеров")

    # 28. Тест apply_sort когда всё готово
    def test_apply_sort_ready(self, scanner):
        scanner.folders_data = [{'path': 'C:\\test\\.venv', 'size': 100, 'ctime': 1, 'mtime': 2, 'size_str': '100 Б'}]
        scanner.size_calculated = True
        scanner.results_text = MagicMock()
        with patch.object(scanner, 'display_sorted_results') as mock_display:
            scanner.apply_sort('ctime')
            mock_display.assert_called_once_with('ctime')

    # 29. Тест wait_for_sizes_and_display когда все размеры вычислены
    def test_wait_for_sizes_and_display_all_computed(self, scanner):
        scanner.folders_data = [
            {'path': 'C:\\test\\.venv', 'size': 100, 'ctime': 1, 'mtime': 2, 'size_str': '100 Б'},
            {'path': 'D:\\test\\.venv', 'size': 200, 'ctime': 3, 'mtime': 4, 'size_str': '200 Б'},
        ]
        scanner.size_calculated = False
        scanner.scan_button = MagicMock()
        scanner.status_label = MagicMock()
        scanner.progress_bar = MagicMock()
        scanner.current_folder_label = MagicMock()
        scanner.results_text = MagicMock()

        with patch.object(scanner, 'display_sorted_results') as mock_display:
            scanner.wait_for_sizes_and_display()
            mock_display.assert_called_once_with("ctime")
            scanner.scan_button.configure.assert_called_once_with(state="normal")
            scanner.status_label.configure.assert_called_once_with(text="✅ Сканирование завершено. Все размеры вычислены.")
            scanner.progress_bar.set.assert_called_once_with(1.0)
            scanner.current_folder_label.configure.assert_called_once_with(text="Текущая папка: -")
            assert scanner.scanning == False
            assert scanner.size_calculated == True

    # 30. Тест wait_for_sizes_and_display когда не все размеры вычислены
    def test_wait_for_sizes_and_display_not_computed(self, scanner):
        scanner.folders_data = [
            {'path': 'C:\\test\\.venv', 'size': None, 'ctime': 1, 'mtime': 2, 'size_str': 'вычисляется...'},
            {'path': 'D:\\test\\.venv', 'size': 200, 'ctime': 3, 'mtime': 4, 'size_str': '200 Б'},
        ]
        scanner.size_calculated = False
        scanner.window.after = MagicMock()

        # Сброс моков, чтобы игнорировать вызовы из конструктора
        scanner.progress_bar.set.reset_mock()
        scanner.scan_button.configure.reset_mock()
        scanner.status_label.configure.reset_mock()
        scanner.current_folder_label.configure.reset_mock()

        scanner.wait_for_sizes_and_display()

        scanner.window.after.assert_called_once_with(500, scanner.wait_for_sizes_and_display)
        scanner.progress_bar.set.assert_not_called()
        scanner.scan_button.configure.assert_not_called()
        scanner.status_label.configure.assert_not_called()
        scanner.current_folder_label.configure.assert_not_called()

    # 31. Тест update_total_size_label
    def test_update_total_size_label(self, scanner):
        scanner.total_size_label = MagicMock()
        scanner.update_total_size_label(1234567)
        scanner.total_size_label.configure.assert_called_once_with(text="Общий размер найденных папок: 1.18 МБ")

    # 32. Тест calculate_and_update_size с исключением
    @patch('os.walk')
    def test_calculate_and_update_size_exception(self, mock_walk, scanner):
        mock_walk.side_effect = Exception("Some error")
        scanner.window.after = MagicMock()
        scanner.update_result_line_by_path = MagicMock()

        scanner.calculate_and_update_size("C:\\test\\.venv")

        scanner.window.after.assert_called_once()
        args, kwargs = scanner.window.after.call_args
        assert args[0] == 0
        func = args[1]
        path_arg = args[2]
        size_text = args[3]
        assert path_arg == "C:\\test\\.venv"
        assert size_text == "ошибка: Some error"
        func(path_arg, size_text)
        scanner.update_result_line_by_path.assert_called_once_with("C:\\test\\.venv", "ошибка: Some error")