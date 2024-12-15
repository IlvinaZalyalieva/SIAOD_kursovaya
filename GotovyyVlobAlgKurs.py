import sys, random
from datetime import datetime, timedelta, time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsEllipseItem, QGraphicsTextItem, QVBoxLayout, QWidget, QLabel, QPushButton,
    QHBoxLayout, QTabWidget, QTextEdit, QSplitter, QLineEdit, QMessageBox, QInputDialog
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QBrush, QColor, QPen, QFont
import darkdetect 
import random

def is_time_in_interval(start_time, end_time, current_time):
    if start_time <= end_time:
        # Обычный случай: интервал не пересекает полночь
        return start_time <= current_time < end_time
    else:
        # Интервал пересекает полночь
        return current_time >= start_time or current_time < end_time


# Класс водителя
class Driver:
    begin = 0
    def __init__(self, name, driver_type, start_time, end_time, breaks=None, start_day=None):
        self.name = name
        self.driver_type = driver_type  # 'day' или 'shift'
        self.start_time = start_time  # Время начала работы (часы)
        self.end_time = end_time  # Время окончания работы (часы)
        self.breaks = breaks if breaks else []  # Перерывы в работе
        self.start_day = start_day  # День начала работы (например, "Monday", "Tuesday" и т.д.)
        self.busp = Bus(name, driver_type, start_time, end_time, start_time, end_time)

    def is_available_on_day(self, current_time):
        # Получаем день недели
        current_day = current_time.strftime("%A")
        
        if self.driver_type == 'day':
            return current_day not in ["Saturday", "Sunday"]  # Работает с понедельника по пятницу
        
        elif self.driver_type == 'shift':
            if self.start_day:  # Если точка отсчета для сменного водителя задана
                # Преобразуем начало работы в день недели
                start_day_index = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(self.start_day)
                current_day_index = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(current_day)
                
                # Рассчитываем день смены с учетом старта и сменных интервалов
                days_on = (current_day_index - start_day_index) // 2  # Работает через 2 дня
                return days_on % 2 == 0
            else:
                # Для водителей, работающих только по выходным, просто проверяем на выходные
                return current_day in ["Saturday", "Sunday"]

    def is_working(self, current_time):
        # Время начала и окончания работы
        start_time = datetime.combine(current_time.date(), datetime.min.time()) + timedelta(hours=self.start_time)
        end_time = datetime.combine(current_time.date(), datetime.min.time()) + timedelta(hours=self.end_time)
        self.busp.unpark() 
        # Проверяем, попадает ли текущее время в рабочий интервал
        if is_time_in_interval(start_time, end_time, current_time):
            # Проверка на перерывы
            for break_start, break_end in self.breaks:
                break_start_time = start_time + timedelta(hours=break_start - self.start_time)
                break_end_time = start_time + timedelta(hours=break_end - self.start_time)

                if is_time_in_interval(break_start_time, break_end_time, current_time):
                    return False
            return True
        return False


# Класс автобуса
class Bus:
    def __init__(self, bus_number, driver, route, reverse_route, start_stop_index, direction):
        self.bus_number = bus_number
        self.driver = driver
        self.route = route
        self.reverse_route = reverse_route
        self.current_route = self.route
        self.current_stop_index = start_stop_index
        self.time_to_next_stop = 0
        self.direction = direction  # 1 = прямая, -1 = обратная
        self.on_parking = True  # На стоянке ли автобус
        self.passengers = 0  # Текущее количество пассажиров в автобусе

    def move_to_next_stop(self):
        if self.on_parking:
            self.park()
            return  # Автобус стоит на стоянке
        if self.time_to_next_stop > 0:
            self.time_to_next_stop -= 1
        else:
            # Перемещение по маршруту
            self.current_stop_index += self.direction

            # Если автобус достиг конца маршрута (верхний или нижний)
            if self.current_stop_index >= len(self.current_route):
                # Если мы на верхнем маршруте, то переключаемся на нижний
                if self.current_route == self.route:
                    self.current_route = self.reverse_route
                    self.current_stop_index = -1  # Начинаем с конца нижнего маршрута
                else:
                    self.current_route = self.route
                    self.current_stop_index = 0  # Начинаем с начала верхнего маршрута
                # Меняем направление
                self.direction *= -1
            self.time_to_next_stop = 5  # Время между остановками
    
    def park(self):
        """Установить автобус на стоянку."""
        self.on_parking = True

    def unpark(self):
        """Снять автобус с парковки."""
        self.on_parking = False


# Класс расписания
class Schedule:
    def __init__(self, stops):
        self.stops = stops
        self.buses = []
        self.passenger_manager = Passenger(self)
        self.drivers = []  # Добавляем список водителей

    def add_bus(self, bus):
        self.buses.append(bus)

    def update(self, current_time):
        # Обновляем пассажиропоток
        self.passenger_manager.update_passenger_flow(current_time)
        # Получаем день недели для текущего времени
        current_day = current_time.strftime("%A")
        for bus in self.buses:
            if bus.driver.is_available_on_day(current_time) and bus.driver.is_working(current_time):
                bus.unpark()
                bus.move_to_next_stop()
                # Сажаем и высаживаем пассажиров
                if not bus.on_parking:
                    self.passenger_manager.board_passengers(bus)
                else:
                    bus.park()  # Автобус становится на стоянку
            else:
                bus.park()
    
    def assign_bus(self, current_time):
        for driver in self.drivers:
            print(f"Проверяем водителя {driver.name} на {current_time}. Работает ли: {driver.is_working(current_time)}")
            if driver.is_working(current_time):
                return driver
        print(f"Нет доступных водителей на {current_time}")
        return None

class Passenger:
    def __init__(self, schedule):
        self.schedule = schedule
        self.passengers_on_stops = {stop: 0 for stop in schedule.stops}  # Пассажиры на остановках
        self.bus_capacity = 60  # Вместимость автобуса

    def update_passenger_flow(self, current_time):
        """Обновляет количество пассажиров на остановках в зависимости от времени суток."""
        hour = current_time.hour
        current_day = current_time.strftime("%A")
        
        if current_day not in ["Saturday", "Sunday"]:
            for stop in self.schedule.stops:
                if 7 <= hour < 9 or 17 <= hour < 19:  # Часы пик
                    self.passengers_on_stops[stop] = random.randint(30, 50)
                elif 9 <= hour < 17 or 19 <= hour < 22:  # День
                    self.passengers_on_stops[stop] = random.randint(20, 40)
                else:  # Ночь
                    self.passengers_on_stops[stop] = random.randint(0, 10)
        else:
            for stop in self.schedule.stops:
                if 8 <= hour < 16:  
                    self.passengers_on_stops[stop] = random.randint(10, 20)
                elif 16 <= hour < 22:
                    self.passengers_on_stops[stop] = random.randint(20, 30)
                else:  # Ночь
                    self.passengers_on_stops[stop] = random.randint(0, 10)

    def board_passengers(self, bus):
        """Сажает пассажиров в автобус."""
        if bus.on_parking:
            return 0  # Возвращаем 0, так как автобус не работает

        current_stop = self.schedule.stops[bus.current_stop_index]
        passengers_on_stop = self.passengers_on_stops[current_stop]
        alighting_passengers = random.randint(0, bus.passengers - bus.passengers // 3)
        bus.passengers -= alighting_passengers
        available_seats = self.bus_capacity - bus.passengers
        boarding_passengers = min(passengers_on_stop, available_seats)
        self.passengers_on_stops[current_stop] = self.passengers_on_stops[current_stop] - boarding_passengers + alighting_passengers //4
        bus.passengers += boarding_passengers
        # Подсчет пассажиров, которые не поместились
        passengers_left = passengers_on_stop - boarding_passengers
        return passengers_left


# Главный интерфейс
class BusScheduleApp(QMainWindow):
    def __init__(self, schedule):
        super().__init__()
        self.schedule = schedule
        self.current_time = datetime(2024, 1, 1, 7, 0)  # Начало симуляции
        self.time_speed = 1  # Скорость времени (1 = 1х, 2 = 2х, 5 = 5х)
        self.init_ui()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_schedule)
        self.timer.start(1000 // self.time_speed)  # Обновляем каждую секунду
        self.flag = 1
        self.info_list = []

    def init_ui(self):
        self.setWindowTitle("Расписание автобусов")
        self.setGeometry(30, 50, 1400, 900)

        # Создаем QTabWidget для вкладок
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setStyleSheet(self.get_theme_styles())

        # Вкладка с картой и основным интерфейсом
        self.main_tab = QWidget()
        self.tab_widget.addTab(self.main_tab, "Карта")

        # Вкладка с расписанием водителей
        self.driver_tab = QWidget()
        self.tab_widget.addTab(self.driver_tab, "Расписание водителей")

        # Вкладка с расписанием остановок
        self.stop_tab = QWidget()
        self.tab_widget.addTab(self.stop_tab, "Расписание остановок")

        # Основной интерфейс на вкладке "Карта"
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.time_label = QLabel(self)
        self.time_label.setAlignment(Qt.AlignCenter)
        self.info_text = QTextEdit(self)
        self.info_text.setReadOnly(True)
        
        self.speed_button = QPushButton("Изменить время (2x)", self)
        self.speed_button.clicked.connect(self.speed_up_time)
        self.speed_button.setStyleSheet("""
            QPushButton {
                background-color: #007AFF; /* Синий цвет */
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #005BB5; /* Темнее синий при наведении */
            }
            QPushButton:pressed {
                background-color: #004A99; /* Еще темнее при нажатии */
            }
        """)

        # Кнопка для паузы
        self.pause_button = QPushButton("Пауза", self)
        self.pause_button.clicked.connect(self.toggle_pause)
        self.pause_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9500; /* Оранжевый цвет */
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #E68A00; /* Темнее оранжевый при наведении */
            }
            QPushButton:pressed {
                background-color: #CC7A00; /* Еще темнее при нажатии */
            }
        """)


        # Размещаем кнопки
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.speed_button)
        button_layout.addWidget(self.pause_button)

        # Используем QSplitter для разделения окна на карту и информационное окно
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.view)  # Карта
        info_layout = QVBoxLayout()
        info_layout.addWidget(self.time_label)
        info_layout.addWidget(self.info_text)
        info_widget = QWidget()
        info_widget.setLayout(info_layout)
        splitter.addWidget(info_widget)  # Информационное окно

        # Устанавливаем начальные размеры
        splitter.setSizes([600, 200])  # 600px для карты, 200px для информации

        # Основной layout для вкладки "Карта"
        self.layout = QVBoxLayout(self.main_tab)
        self.layout.addWidget(splitter)
        self.layout.addLayout(button_layout)

        # Интерфейс для вкладки "Расписание водителей"
        self.driver_layout = QVBoxLayout(self.driver_tab)
        self.driver_text = QTextEdit(self)
        self.driver_text.setReadOnly(True)
        self.driver_layout.addWidget(self.driver_text)

        # Интерфейс для вкладки "Расписание остановок"
        self.stop_layout = QVBoxLayout(self.stop_tab)
        self.stop_text = QTextEdit(self)
        self.stop_text.setReadOnly(True)
        self.stop_layout.addWidget(self.stop_text)

        # Устанавливаем центральный виджет
        self.setCentralWidget(self.tab_widget)

        self.draw_route()

    def get_theme_styles(self):
        if darkdetect.isDark():
            return """
                QMainWindow { background-color: #1E1E1E; color: #FFFFFF; }
                QTabWidget::pane { border: 1px solid #444444; border-radius: 8px; }
                QTabBar::tab { background-color: #333333; color: #FFFFFF; padding: 10px 20px; border: 1px solid #444444; border-bottom: none; border-top-left-radius: 8px; border-top-right-radius: 8px; }
                QTabBar::tab:selected { background-color: #007AFF; color: #FFFFFF; }
                QTextEdit { background-color: #2E2E2E; color: #FFFFFF; border: 1px solid #444444; border-radius: 8px; padding: 10px; font-size: 14px; }
                QLabel { font-size: 18px; font-weight: bold; font-family: 'Helvetica Neue', sans-serif; color: #FFFFFF; }
                QGraphicsTextItem { color: #FFFFFF; } /* Белый текст на карте */
            """
        else:
            return """
                QMainWindow { background-color: #F5F5F5; color: #333333; }
                QTabWidget::pane { border: 1px solid #E0E0E0; border-radius: 8px; }
                QTabBar::tab { background-color: #F5F5F5; color: #333333; padding: 10px 20px; border: 1px solid #E0E0E0; border-bottom: none; border-top-left-radius: 8px; border-top-right-radius: 8px; }
                QTabBar::tab:selected { background-color: #007AFF; color: #FFFFFF; }
                QTextEdit { background-color: #FFFFFF; color: #333333; border: 1px solid #E0E0E0; border-radius: 8px; padding: 10px; font-size: 14px; }
                QLabel { font-size: 18px; font-weight: bold; font-family: 'Helvetica Neue', sans-serif; color: #333333; }
                QGraphicsTextItem { color: #000000; } /* Белый текст на карте */
            """
    
    def toggle_pause(self):
        if self.timer.isActive():
            self.timer.stop()
            self.pause_button.setText("Возобновить")
        else:
            self.timer.start(1000 // self.time_speed)
            self.pause_button.setText("Пауза")

    def translate_driver_type(self, driver_type):
        driver_types = {
            "day": "Дневной",
            "shift": "Сменный",
        }
        return driver_types.get(driver_type, driver_type)  # Возвращаем русский день или оригинал, если не найдено
    
    def show_driver_schedule(self):
        driver_info = "Расписание водителей (в часах):\n"
        for bus in self.schedule.buses:
            driver_type_ru = self.translate_driver_type(bus.driver.driver_type)
            driver_info += (
                f"  Водитель: {bus.driver.name}\n"
                f"  Тип: {driver_type_ru}\n"
                f"  Рабочие часы: {bus.driver.start_time} - {bus.driver.end_time}\n"
                f"  Перерывы: {', '.join([f'{start}-{end}' for start, end in bus.driver.breaks])}\n"
                f"\n"
            )
        self.driver_text.setText(driver_info)

    def show_stop_schedule(self):
        info_listt = ''
        for bus in self.schedule.buses:
            info = ''
            if bus.driver.is_working(self.current_time) and not bus.on_parking:
                current_stop = self.schedule.stops[bus.current_stop_index]
                arrival_time = self.current_time + timedelta(minutes=bus.time_to_next_stop)
                current_day = self.current_time.strftime("%A")
                current_day_ru = self.translate_day_to_russian(current_day)  # Перевод дня недели на русский
                info = (
                    f"В {current_day_ru} {arrival_time.strftime('%H:%M')} - {current_stop} - Автобус {bus.bus_number}\n"
                )
                if info not in self.info_list:
                    self.info_list.append(info)
                    #print(self.info_list)
                    info_listt += info
        if len(info_listt) != 0:
            #print(info_listt)
            self.stop_text.append(info_listt[:-2])  # Добавляем новые данные в конец текста
        else:
            return None
        
    def draw_route(self):
        # Координаты верхней части маршрута (18 остановок)
        self.top_coordinates = [
            (100, 100), (160, 50), (220, 120), (280, 100),
            (340, 80), (400, 110), (480, 50), (540, 130),
            (600, 80), (650, 30), (720, 0), (780, 30),
            (830, 100), (890, 120), (940, 150), (1050, 130),
            (1160, 150), (1100, 200)
        ]

        # Координаты нижней части маршрута (16 остановок)
        self.bottom_coordinates = [
            (150, 150), (160, 250), (220, 320), (280, 300),
            (340, 280), (380, 310), (480, 250), (540, 330),
            (600, 280), (650, 230), (720, 200), (800, 230),
            (830, 280), (890, 320), (940, 350), (1050, 330)
        ]

        # Полный список остановок в порядке следования
        full_stops = self.schedule.stops + list(reversed(self.schedule.stops))

        # Соединяем линии верхней части маршрута
        for i in range(len(self.top_coordinates) - 1):
            start = self.top_coordinates[i]
            end = self.top_coordinates[i + 1]
            self.scene.addLine(start[0] + 10, start[1] + 10, end[0] + 10, end[1] + 10, QPen(QColor("#696969"), 1))

        # Соединяем линии нижней части маршрута
        for i in range(len(self.bottom_coordinates) - 1):
            start = self.bottom_coordinates[i]
            end = self.bottom_coordinates[i + 1]
            self.scene.addLine(start[0] + 10, start[1] + 10, end[0] + 10, end[1] + 10, QPen(QColor("#696969"), 1))

        # Соединяем верхнюю и нижнюю части маршрута на концах
        self.scene.addLine(
            self.top_coordinates[0][0] + 10, self.top_coordinates[0][1] + 10,
            self.bottom_coordinates[0][0] + 10, self.bottom_coordinates[0][1] + 10, 
            QPen(QColor("#696969"), 1)
        )
        self.scene.addLine(
            self.top_coordinates[-1][0] + 10, self.top_coordinates[-1][1] + 10,
            self.bottom_coordinates[-1][0] + 10, self.bottom_coordinates[-1][1] + 10,
            QPen(QColor("#696969"), 1)
        )
        # Рисуем остановки верхней части маршрута
        for i, (x, y) in enumerate(self.top_coordinates):
            ellipse = QGraphicsEllipseItem(x, y, 20, 20)
            ellipse.setBrush(QBrush(QColor("blue")))
            self.scene.addItem(ellipse)
            text = QGraphicsTextItem(full_stops[i])
            if darkdetect.isDark():
                text.setDefaultTextColor(QColor("#D5D5D5"))
            else:
                text.setDefaultTextColor(QColor("#293133"))
            text.setPos(x - 10, y - 30)
            self.scene.addItem(text)

        # Рисуем остановки нижней части маршрута
        for i, (x, y) in enumerate(self.bottom_coordinates):
            ellipse = QGraphicsEllipseItem(x, y, 20, 20)
            ellipse.setBrush(QBrush(QColor("blue")))
            self.scene.addItem(ellipse)
            text = QGraphicsTextItem(full_stops[34 - i])
            if darkdetect.isDark():
                text.setDefaultTextColor(QColor("#D5D5D5"))
            else:
                text.setDefaultTextColor(QColor("#293133"))
            text.setPos(x - 20, y + 20)
            self.scene.addItem(text)

        # Создаем элементы для автобусов
        self.bus_items = []
        for bus in self.schedule.buses:
            bus_item = QGraphicsEllipseItem(0, 0, 25, 25)
            bus_item.setBrush(QBrush(QColor("red")))
            bus_item.setPos(50, 50)
            self.scene.addItem(bus_item)
            self.bus_items.append(bus_item)

            # Добавляем номер автобуса
            bus_number_text = QGraphicsTextItem(str(bus.bus_number))

            bus_number_text.setDefaultTextColor(QColor("#FFFFFF"))  # Белый цвет текста
            bus_number_text.setFont(QFont("Arial", 15, QFont.Bold))  # Устанавливаем шрифт
            self.scene.addItem(bus_number_text)
            
            bus_number_text.setPos(50, 50)
            self.bus_items.append(bus_number_text)
    def translate_day_to_russian(self, day):
        days = {
            "Monday": "Понедельник",
            "Tuesday": "Вторник",
            "Wednesday": "Среда",
            "Thursday": "Четверг",
            "Friday": "Пятница",
            "Saturday": "Суббота",
            "Sunday": "Воскресенье"
        }
        return days.get(day, day)  # Возвращаем русский день или оригинал, если не найдено

    def update_schedule(self):
        # Обновляем расписание автобусов
        self.schedule.update(self.current_time)
        # Обновляем время
        self.current_time += timedelta(minutes=1)
        day_of_week = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        #current_day = day_of_week[self.current_time.weekday()]
        current_day = self.current_time.strftime("%A")
        current_day_ru = self.translate_day_to_russian(current_day)  # Перевод дня недели на русский
        self.time_label.setText(f"{current_day_ru} - {self.current_time.strftime('%H:%M')}")
        self.info_text.setText(self.get_bus_info())
        # Обновляем расписание водителей и остановок
        self.show_driver_schedule()
        self.show_stop_schedule()
        # Отладочный вывод для проверки пассажиров
        #for bus in self.schedule.buses:
            #print(f"Автобус {bus.bus_number}: Пассажиров в автобусе: {bus.passengers}")

        # Обновляем позиции автобусов
        for i, bus in enumerate(self.schedule.buses):
            #print('0', i)
            if bus.on_parking:
                coords = (50, 50)  # Координаты стоянки
                bus_circle = self.bus_items[i * 2]
                bus_circle.setPos(coords[0], coords[1])
                bus_circle = self.bus_items[i * 2]
                bus_text = self.bus_items[i * 2 + 1]
                bus_circle.setPos(coords[0], coords[1])
                bus_text.setPos(coords[0] - bus_text.boundingRect().width() / 2, coords[1] - bus_text.boundingRect().height() / 2)
                # Скрываем текст, если автобус на парковке
                bus_text.setVisible(False)
                 # Скрываем текст, если автобус на парковке
            else:
                if bus.direction == 1:  # Движение вперед по верхнему маршруту
                    #print('2', i)
                    if bus.current_stop_index < len(self.top_coordinates) - 1:
                        coords = self.top_coordinates[bus.current_stop_index]
                    else:
                        bus.direction *= -1
                        bus.current_stop_index = - 1
                        coords = self.top_coordinates[bus.current_stop_index]
                else:  # Движение назад по нижнему маршруту
                    #print('3', i)
                    if -17 < bus.current_stop_index < len(self.bottom_coordinates) :
                        coords = self.bottom_coordinates[bus.current_stop_index]
                        #print(bus.current_stop_index)
                    else:
                        bus.direction *= -1
                        bus.current_stop_index = 0
                        coords = self.bottom_coordinates[bus.current_stop_index]
                if bus.driver.is_working(self.current_time):
                    bus_circle = self.bus_items[i * 2]  # Круг автобуса
                    
                    self.bus_items[i * 2].setPos(coords[0], coords[1])
                    # Вычисляем центр круга
                    circle_center_x = bus_circle.boundingRect().center().x() + coords[0]
                    circle_center_y = bus_circle.boundingRect().center().y() + coords[1]
                    bus_text = self.bus_items[i * 2 + 1]  # Текст номера автобуса
                    # Вычисляем смещение текста, чтобы он был центрирован
                    text_width = bus_text.boundingRect().width()
                    text_height = bus_text.boundingRect().height()
                    bus_text.setVisible(True)
                    # Устанавливаем позицию текста
                    bus_text.setPos(
                        circle_center_x - text_width / 2,
                        circle_center_y - text_height / 2
                    )
                    
    def get_bus_info(self):
        # Вывод информации об автобусах
        info = ""
        for bus in self.schedule.buses:
            if bus.driver.is_working(self.current_time) and not bus.on_parking:
                stop = self.schedule.stops[bus.current_stop_index]
                # Получаем количество пассажиров, которые не поместились
                passengers_left = self.schedule.passenger_manager.board_passengers(bus)
                #print(bus.current_stop_index)
                if bus.current_stop_index < 0:
                    stop = self.schedule.stops[bus.current_stop_index - 1]
                    info += f"Автобус {bus.bus_number} на остановке {stop}, водитель: {bus.driver.name}, пассажиров в автобусе: {bus.passengers}, не поместились {passengers_left}\n"
                else:
                    info += f"Автобус {bus.bus_number} на остановке {stop}, водитель: {bus.driver.name}, пассажиров в автобусе: {bus.passengers}, не поместились {passengers_left}\n"
        return info

    def speed_up_time(self):
        # Увеличиваем скорость времени
        if self.time_speed == 1:
            self.time_speed = 2
            self.speed_button.setText("Изменить время (5x)")
        elif self.time_speed == 2:
            self.time_speed = 5
            self.speed_button.setText("Изменить время (10x)")
        elif self.time_speed == 5:
            self.time_speed = 10
            self.speed_button.setText("Изменить время (20x)")
        elif self.time_speed == 10:
            self.time_speed = 20
            self.speed_button.setText("Изменить время (1x)")
        else:
            self.time_speed = 1
            self.speed_button.setText("Изменить время (2x)")

        # Обновляем интервал таймера
        self.timer.setInterval(1000 // self.time_speed)


# Основная функция
def main():
    # Остановки
    stops = [
        "Ферма-2", "Рауиса Гареева", "Азамат", "ДРКБ", "РКБ",
        "Южная", "д. Универсиады (Победы)", "Академика Парина",
        "Медучилище", "Мавлютова", "Братьев Касимовых", "Метро Горки",
        "Рихарда Зорге", "Даурская (Рихарда Зорге)", "Сады",
        "Гвардейская", "Кафе Сирень", "Аделя Кутуя"
    ]
    reverse_stops = list(reversed(stops))

    schedule = Schedule(stops)
    schedule.reverse_stops = reverse_stops

# Создаем водителей
    driver1 = Driver("Иван", "shift", 21.5, 8.5, [(0.5, 0.6), (3.6, 3.8), (6.8, 7)], start_day="Monday")
    driver2 = Driver("Петр", "shift", 22.5, 9.5, [(1.5, 1.66), (4.66, 4.83), (7.83, 8)], start_day="Monday")
    #driver3 = Driver("Сидор", "day", 7.25, 16.25, [(14.75, 15.75)])
    #driver4 = Driver("Николай", "day", 7.5, 16.5, [(15, 16)])
    driver5 = Driver("Алексей", "day", 7.75, 16.75, [(13.75, 14.75)])
    driver6 = Driver("Михаил", "day", 10, 19, [(13, 14)])
    driver7 = Driver("Дмитрий", "shift", 17, 4, [(20, 20.17), (23.18, 23.33), (2.33, 2.5)], start_day="Monday")
    driver8 = Driver("Сергей", "day", 12, 21, [(15.5, 16.5)])

    driver12 = Driver("Петр2", "shift", 22.5, 9.5, [(1.5, 1.66), (4.66, 4.83), (7.83, 8)], start_day="Monday")
    #driver13 = Driver("Сидор2", "day", 7.25, 16.25, [(14.75, 15.75)])
    driver14 = Driver("Николай2", "day", 7.5, 16.5, [(15, 16)])
    driver15 = Driver("Алексей2", "day", 7.75, 16.75, [(13.75, 14.75)])
    driver16 = Driver("Михаил2", "day", 10, 19, [(13, 14)])
    driver17 = Driver("Дмитрий2", "shift", 17, 4, [(20, 20.17), (23.18, 23.33), (2.33, 2.5)], start_day="Monday")
    driver18 = Driver("Сергей2", "day", 12, 21, [(15.5, 16.5)])

    #driver21 = Driver("Иван3", "shift", 21.5, 8.5, [(0.5, 0.6), (3.6, 3.8), (6.8, 7)], start_day="Wednesday")
    driver22 = Driver("Петр3", "shift", 22.5, 9.5, [(1.5, 1.66), (4.66, 4.83), (7.83, 8)], start_day="Wednesday")
    driver27 = Driver("Дмитрий3", "shift", 17, 4, [(20, 20.17), (23.18, 23.33), (2.33, 2.5)], start_day="Wednesday")

    driver212 = Driver("Петр4", "shift", 22.5, 9.5, [(1.5, 1.66), (4.66, 4.83), (7.83, 8)], start_day="Wednesday")
    driver217 = Driver("Дмитрий4", "shift", 17, 4, [(20, 20.17), (23.18, 23.33), (2.33, 2.5)], start_day="Wednesday")

    # Водители выходного дня
    driver100 = Driver("вых1", "shift", 4.5, 16.5, [(7.5, 7.6), (10.6, 10.8), (13.8, 14)], start_day=None)
    driver101 = Driver("вых2", "shift", 4.5, 16.5, [(7.5, 7.6), (10.6, 10.8), (13.8, 14)], start_day=None)
    driver102 = Driver("вых1_1", "shift", 8, 20, [(11, 11.17), (14.18, 14.33), (17.33, 17.5)], start_day=None)
    driver103 = Driver("вых2_2", "shift", 8, 20, [(11, 11.17), (14.18, 14.33), (17.33, 17.5)], start_day=None)
    
    # Создаем автобусы
    bus1 = Bus(1, driver1, stops, reverse_stops, 0, 1)  # Начинает с Ферма-2, движется вперед
    bus2 = Bus(2, driver2, stops, reverse_stops, 0, 1)  # Начинает с Аделя Кутуя, движется назад
    #bus3 = Bus(3, driver3, stops, reverse_stops, 0, 1)
    #bus4 = Bus(4, driver4, stops, reverse_stops, 0, 1)
    bus5 = Bus(5, driver5, stops, reverse_stops, 0, 1)
    bus6 = Bus(6, driver6, stops, reverse_stops, 0, 1)
    bus7 = Bus(7, driver7, stops, reverse_stops, 0, 1)
    bus8 = Bus(8, driver8, stops, reverse_stops, 0, 1)
    #bus21 = Bus(21, driver21, stops, reverse_stops, 0, 1)
    bus22 = Bus(22, driver22, stops, reverse_stops, 0, 1)
    bus27 = Bus(27, driver27, stops, reverse_stops, 0, 1)
    bus100 = Bus(100, driver100, stops, reverse_stops, 0, 1)
    bus102 = Bus(102, driver102, stops, reverse_stops, 0, 1)

    bus12 = Bus(12, driver12, stops, reverse_stops, 17, 1)  # Начинает с Аделя Кутуя, движется назад
    #bus13 = Bus(13, driver13, stops, reverse_stops, 17, 1)
    bus14 = Bus(14, driver14, stops, reverse_stops, 17, 1)
    bus15 = Bus(15, driver15, stops, reverse_stops, 17, 1)
    bus16 = Bus(16, driver16, stops, reverse_stops, 17, 1)
    bus17 = Bus(17, driver17, stops, reverse_stops, 17, 1)
    bus18 = Bus(18, driver18, stops, reverse_stops, 17, 1)
    bus212 = Bus(212, driver212, stops, reverse_stops, 17, 1)
    bus217 = Bus(217, driver217, stops, reverse_stops, 17, 1)
    bus101 = Bus(101, driver101, stops, reverse_stops, 17, 1)
    bus103 = Bus(103, driver103, stops, reverse_stops, 17, 1)


    # Добавляем автобусы в расписание
    schedule.add_bus(bus1)
    schedule.add_bus(bus2)
    #schedule.add_bus(bus3)
    #schedule.add_bus(bus4)
    schedule.add_bus(bus5)
    schedule.add_bus(bus6)
    schedule.add_bus(bus7)
    schedule.add_bus(bus8)
    #schedule.add_bus(bus21)
    schedule.add_bus(bus22)
    schedule.add_bus(bus27)
    schedule.add_bus(bus100)
    schedule.add_bus(bus102)

    schedule.add_bus(bus12)
    #schedule.add_bus(bus13)
    schedule.add_bus(bus14)
    schedule.add_bus(bus15)
    schedule.add_bus(bus16)
    schedule.add_bus(bus17)
    schedule.add_bus(bus18)
    schedule.add_bus(bus212)
    schedule.add_bus(bus217)
    schedule.add_bus(bus101)
    schedule.add_bus(bus103)

    # Запускаем приложение
    app = QApplication(sys.argv)
    main_window = BusScheduleApp(schedule)
    main_window.show()
    sys.exit(app.exec_())
     


if __name__ == "__main__":
    main()