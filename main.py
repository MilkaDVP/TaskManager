import sys
import csv
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QTextEdit, QComboBox, QDateEdit, QHeaderView,
    QDialog, QFormLayout, QFileDialog, QToolBar, QAction, QMessageBox, QSplashScreen
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QDate, QTimer
import sqlite3


class SplashScreen(QSplashScreen):
    def __init__(self, pixmap):
        super().__init__(pixmap)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setEnabled(False)

        # Установка позиции SplashScreen по центру экрана
        screen_geometry = QApplication.desktop().screenGeometry()
        splash_geometry = self.geometry()
        self.move(
            (screen_geometry.width() - splash_geometry.width()) // 2,
            (screen_geometry.height() - splash_geometry.height()) // 2
        )

        # Закрытие SplashScreen через 3 секунды
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.close)
        self.timer.start(3000)


class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect('tasks.db')
        self.cur = self.conn.cursor()
        self.create_user_table()
        self.create_task_table()

    def create_user_table(self):
        # Создание таблицы пользователей
        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT
            )
        ''')
        self.conn.commit()

    def create_task_table(self):
        # Создание таблицы задач
        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                description TEXT,
                deadline DATE,
                priority TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        self.conn.commit()

    def add_user(self, username, password):
        # Добавление нового пользователя
        self.cur.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        self.conn.commit()

    def check_login(self, username, password):
        # Проверка логина и пароля при входе
        self.cur.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
        return self.cur.fetchone()

    def add_task(self, user_id, title, description, deadline, priority):
        # Добавление новой задачи
        self.cur.execute('''
            INSERT INTO tasks (user_id, title, description, deadline, priority)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, title, description, deadline, priority))
        self.conn.commit()

    def get_user_id(self, username):
        # Получение ID пользователя по его имени
        self.cur.execute('SELECT id FROM users WHERE username=?', (username,))
        user_id = self.cur.fetchone()
        return user_id[0] if user_id else None

    def delete_task(self, title, description, user_id):
        # Удаление задачи
        self.cur.execute('DELETE FROM tasks WHERE title=? AND description=? AND user_id=?', (title, description, user_id))
        self.conn.commit()


class LoginDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Вход')
        self.db_manager = db_manager
        self.username_label = QLabel('Имя пользователя:')
        self.username_edit = QLineEdit(self)

        self.password_label = QLabel('Пароль:')
        self.password_edit = QLineEdit(self)
        self.password_edit.setEchoMode(QLineEdit.Password)

        self.btn_login = QPushButton('Войти', self)
        self.btn_register = QPushButton('Зарегистрироваться', self)

        layout = QFormLayout(self)
        layout.addRow(self.username_label, self.username_edit)
        layout.addRow(self.password_label, self.password_edit)
        layout.addRow(self.btn_login, self.btn_register)

        self.btn_login.clicked.connect(self.login)
        self.btn_register.clicked.connect(self.register)

    def login(self):
        # Обработка нажатия кнопки "Войти"
        username = self.username_edit.text()
        password = self.password_edit.text()
        user_data = self.db_manager.check_login(username, password)

        if user_data:
            self.accept()
        else:
            QMessageBox.warning(self, 'Ошибка', 'Неверное имя пользователя или пароль.')

    def register(self):
        # Обработка нажатия кнопки "Зарегистрироваться"
        username = self.username_edit.text()
        password = self.password_edit.text()

        if not username or not password:
            QMessageBox.warning(self, 'Ошибка', 'Введите имя пользователя и пароль.')
            return

        existing_user_id = self.db_manager.get_user_id(username)
        if existing_user_id is not None:
            QMessageBox.warning(self, 'Ошибка', 'Пользователь с таким именем уже зарегистрирован.')
            return

        self.db_manager.add_user(username, password)
        QMessageBox.information(self, 'Успешная регистрация', 'Пользователь зарегистрирован успешно.')
        self.accept()

    def get_user_id(self):
        # Получение ID пользователя
        return self.db_manager.get_user_id(self.username_edit.text())


class TaskDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Добавление Задачи')
        self.title_label = QLabel('Заголовок:')
        self.title_edit = QLineEdit(self)

        self.description_label = QLabel('Описание:')
        self.description_edit = QTextEdit(self)

        self.deadline_label = QLabel('Срок исполнения:')
        self.deadline_edit = QDateEdit(self)

        self.priority_label = QLabel('Приоритет:')
        self.priority_combobox = QComboBox(self)
        self.priority_combobox.addItems(['Низкий', 'Средний', 'Высокий'])

        self.btn_add = QPushButton('Добавить', self)
        self.btn_cancel = QPushButton('Отмена', self)

        layout = QFormLayout(self)
        layout.addRow(self.title_label, self.title_edit)
        layout.addRow(self.description_label, self.description_edit)
        layout.addRow(self.deadline_label, self.deadline_edit)
        layout.addRow(self.priority_label, self.priority_combobox)
        layout.addRow(self.btn_add, self.btn_cancel)

        self.btn_add.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)


class FilterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Фильтрация Задач')
        self.filter_text_edit = QLineEdit(self)
        self.filter_priority_combobox = QComboBox(self)
        self.filter_priority_combobox.addItems(['', 'Низкий', 'Средний', 'Высокий'])

        self.start_date_edit = QDateEdit(self)
        self.end_date_edit = QDateEdit(self)

        self.btn_filter = QPushButton('Применить фильтр', self)

        layout = QFormLayout(self)
        layout.addRow(QLabel('Текст:'), self.filter_text_edit)
        layout.addRow(QLabel('Приоритет:'), self.filter_priority_combobox)
        layout.addRow(QLabel('Срок с:'), self.start_date_edit)
        layout.addRow(QLabel('Срок по:'), self.end_date_edit)
        layout.addRow(self.btn_filter)

        self.btn_filter.clicked.connect(self.accept)


class TaskManagerApp(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.current_user_id = None
        login_dialog = LoginDialog(db_manager, self)
        result = login_dialog.exec_()
        if result == QDialog.Accepted:
            self.current_user_id = login_dialog.get_user_id()
            splash_pixmap = QPixmap('splash_image.png')
            splash_screen = SplashScreen(splash_pixmap)
            splash_screen.show()
            QApplication.processEvents()
            self.init_ui()
            splash_screen.finish(self)

    def init_ui(self):
        # Инициализация пользовательского интерфейса
        self.toolbar = QToolBar(self)
        self.light_theme_action = QAction('Светлая тема', self)
        self.dark_theme_action = QAction('Темная тема', self)

        self.toolbar.addAction(self.light_theme_action)
        self.toolbar.addAction(self.dark_theme_action)

        self.toolbar.actionTriggered.connect(self.toggle_theme)

        vbox = QVBoxLayout(self)
        vbox.addWidget(self.toolbar)

        self.label_title = QLabel('Управление Задачами', self)
        self.label_title.setAlignment(Qt.AlignCenter)

        vbox.addWidget(self.label_title)
        vbox.addSpacing(10)

        self.table_tasks = QTableWidget(self)
        self.table_tasks.setColumnCount(4)
        self.table_tasks.setHorizontalHeaderLabels(['Заголовок', 'Описание', 'Срок', 'Приоритет'])
        self.table_tasks.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.btn_add_task = QPushButton('Добавить Задачу', self)
        self.btn_edit_task = QPushButton('Редактировать Задачу', self)
        self.btn_delete_task = QPushButton('Удалить Задачу', self)
        self.btn_export_csv = QPushButton('Экспорт в CSV', self)
        self.btn_import_csv = QPushButton('Импорт из CSV', self)
        self.btn_filter_tasks = QPushButton('Фильтровать Задачи', self)

        vbox.addWidget(self.table_tasks)
        vbox.addWidget(self.btn_add_task)
        vbox.addWidget(self.btn_edit_task)
        vbox.addWidget(self.btn_delete_task)
        vbox.addWidget(self.btn_export_csv)
        vbox.addWidget(self.btn_import_csv)
        vbox.addWidget(self.btn_filter_tasks)

        self.btn_add_task.clicked.connect(self.show_add_task_dialog)
        self.btn_edit_task.clicked.connect(self.edit_task)
        self.btn_delete_task.clicked.connect(self.delete_task)
        self.btn_export_csv.clicked.connect(self.export_csv)
        self.btn_import_csv.clicked.connect(self.import_csv)
        self.btn_filter_tasks.clicked.connect(self.show_filter_dialog)

        self.conn = sqlite3.connect('tasks.db')
        self.cur = self.conn.cursor()
        self.create_table()

        self.load_tasks()

        self.setStyleSheet('''
                    QWidget {
                        background-color: #fff;  /* Светлая тема по умолчанию */
                        color: #000;
                    }

                    QLabel {
                        color: #000;
                    }

                    QTableWidget {
                        background-color: #eee;
                        color: #000;
                        border: 1px solid #ccc;
                    }
                ''')

        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle('Менеджер Задач')
        self.show()

    def create_table(self):
        # Создание таблицы задач, если она не существует
        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                description TEXT,
                deadline DATE,
                priority TEXT
            )
        ''')
        self.conn.commit()

    def load_tasks(self):
        # Загрузка задач из базы данных для текущего пользователя
        if self.current_user_id is not None:
            self.cur.execute('SELECT id, title, description, deadline, priority FROM tasks WHERE user_id=?', (self.current_user_id,))
            tasks = self.cur.fetchall()
            self.table_tasks.setRowCount(0)
            for row_num, task in enumerate(tasks):
                self.table_tasks.insertRow(row_num)
                for col_num, data in enumerate(task[1:]):
                    self.table_tasks.setItem(row_num, col_num, QTableWidgetItem(str(data)))

    def show_add_task_dialog(self):
        # Отображение диалога добавления задачи
        dialog = TaskDialog(self)
        result = dialog.exec_()

        if result == QDialog.Accepted:
            title = dialog.title_edit.text()
            description = dialog.description_edit.toPlainText()
            deadline = dialog.deadline_edit.date().toString(Qt.ISODate)
            priority = dialog.priority_combobox.currentText()

            if not title:
                QMessageBox.warning(self, 'Ошибка', 'Введите обязательный заголовок.')
                return

            self.add_task_to_database(title, description, deadline, priority)
            self.load_tasks()

    def add_task_to_database(self, title, description, deadline, priority):
        # Добавление задачи в базу данных
        if self.current_user_id is not None:
            self.cur.execute('''
                INSERT INTO tasks (user_id, title, description, deadline, priority)
                VALUES (?, ?, ?, ?, ?)
            ''', (self.current_user_id, title, description, deadline, priority))
            self.conn.commit()

    def edit_task(self):
        # Редактирование выбранной задачи
        selected_row = self.table_tasks.currentRow()
        if selected_row != -1:
            title = self.table_tasks.item(selected_row, 0).text()
            description = self.table_tasks.item(selected_row, 1).text()
            deadline = self.table_tasks.item(selected_row, 2).text()
            priority = self.table_tasks.item(selected_row, 3).text()

            dialog = TaskDialog(self)
            dialog.title_edit.setText(title)
            dialog.description_edit.setPlainText(description)
            dialog.deadline_edit.setDate(QDate.fromString(deadline, Qt.ISODate))
            dialog.priority_combobox.setCurrentText(priority)

            result = dialog.exec_()

            if result == QDialog.Accepted:
                new_title = dialog.title_edit.text()
                new_description = dialog.description_edit.toPlainText()
                new_deadline = dialog.deadline_edit.date().toString(Qt.ISODate)
                new_priority = dialog.priority_combobox.currentText()

                self.edit_task_in_database(title, description, new_title, new_description, new_deadline, new_priority)
                self.load_tasks()

    def edit_task_in_database(self, title, description, new_title, new_description, new_deadline, new_priority):
        # Редактирование задачи в базе данных
        if self.current_user_id is not None:
            self.cur.execute('''
                        UPDATE tasks
                        SET title=?, description=?, deadline=?, priority=?
                        WHERE title=? AND description=? AND user_id=?
                    ''', (
            new_title, new_description, new_deadline, new_priority, title, description, self.current_user_id))
            self.conn.commit()

    def delete_task(self):
        # Удаление выбранной задачи
        selected_row = self.table_tasks.currentRow()
        if selected_row != -1:
            title = self.table_tasks.item(selected_row, 0).text()
            description = self.table_tasks.item(selected_row, 1).text()
            reply = QMessageBox.question(self, 'Удаление задачи', f'Вы уверены, что хотите удалить задачу "{title}"?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.delete_task_from_database(title, description)
                self.load_tasks()

    def delete_task_from_database(self, title, description):
        # Удаление задачи из базы данных
        if self.current_user_id is not None:
            self.db_manager.delete_task(title, description, self.current_user_id)

    def export_csv(self):
        # Экспорт данных в CSV файл
        file_path, _ = QFileDialog.getSaveFileName(self, 'Экспорт в CSV', '', 'CSV Files (*.csv);;All Files(*.*)')

        if file_path:
            with open(file_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['Заголовок', 'Описание', 'Срок исполнения', 'Приоритет'])

                for row in range(self.table_tasks.rowCount()):
                    row_data = []
                    for col in range(self.table_tasks.columnCount()):
                        item = self.table_tasks.item(row, col)
                        if item is not None:
                            row_data.append(item.text())
                        else:
                            row_data.append('')
                    writer.writerow(row_data)

    def import_csv(self):
        # Импорт данных из CSV файла
        file_path, _ = QFileDialog.getOpenFileName(self, 'Импорт из CSV', '', 'CSV Files (*.csv);;All Files (*.*)')

        if file_path:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                header = next(reader)
                if header == ['Заголовок', 'Описание', 'Срок исполнения', 'Приоритет']:
                    self.clear_table()
                    for row_data in reader:
                        self.add_task_from_csv(row_data)
                    self.load_tasks()
                else:
                    QMessageBox.warning(self, 'Ошибка', 'Выбранный файл не является файлом CSV с задачами.')

    def clear_table(self):
        # Очистка таблицы задач
        self.table_tasks.setRowCount(0)

    def add_task_from_csv(self, row_data):
        # Добавление задачи из CSV файла в базу данных
        if self.current_user_id is not None:
            title, description, deadline, priority = row_data
            self.db_manager.add_task(self.current_user_id, title, description, deadline, priority)

    def show_filter_dialog(self):
        # Отображение диалога фильтрации задач
        dialog = FilterDialog(self)
        result = dialog.exec_()

        if result == QDialog.Accepted:
            filter_text = dialog.filter_text_edit.text()
            filter_priority = dialog.filter_priority_combobox.currentText()
            start_date = dialog.start_date_edit.date().toString(Qt.ISODate)
            end_date = dialog.end_date_edit.date().toString(Qt.ISODate)

            self.filter_tasks(filter_text, filter_priority, start_date, end_date)

    def filter_tasks(self, text, priority, start_date, end_date):
        # Фильтрация задач по заданным параметрам
        if self.current_user_id is not None:
            query = 'SELECT id, title, description, deadline, priority FROM tasks WHERE user_id=?'
            params = (self.current_user_id,)

            if text:
                query += ' AND (title LIKE ? OR description LIKE ?)'
                params += (f'%{text}%', f'%{text}%')

            if priority:
                query += ' AND priority=?'
                params += (priority,)

            if start_date and end_date:
                query += ' AND deadline BETWEEN ? AND ?'
                params += (start_date, end_date)

            self.cur.execute(query, params)
            tasks = self.cur.fetchall()
            self.table_tasks.setRowCount(0)
            for row_num, task in enumerate(tasks):
                self.table_tasks.insertRow(row_num)
                for col_num, data in enumerate(task[1:]):
                    self.table_tasks.setItem(row_num, col_num, QTableWidgetItem(str(data)))

    def toggle_theme(self, action):
        # Переключение темы приложения
        if action == self.light_theme_action:
            self.setStyleSheet('''
                        QWidget {
                            background-color: #fff;
                            color: #000;
                        }

                        QLabel {
                            color: #000;
                        }

                        QTableWidget {
                            background-color: #eee;
                            color: #000;
                            border: 1px solid #ccc;
                        }
                    ''')

        elif action == self.dark_theme_action:
            self.setStyleSheet('''
                        QWidget {
                            background-color: #333;
                            color: #fff;
                        }

                        QLabel {
                            color: #fff;
                        }

                        QTableWidget {
                            background-color: #444;
                            color: #fff;
                            border: 1px solid #555;
                        }
                    ''')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    db_manager = DatabaseManager()
    task_manager_app = TaskManagerApp(db_manager)
    sys.exit(app.exec_())