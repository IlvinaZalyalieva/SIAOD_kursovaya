import sys
import random
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton,
    QHBoxLayout, QTabWidget, QTextEdit, QSplitter
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont
import darkdetect

import random

def generate_driver_schedule(driver_category, driver_name):
    if driver_category == 1:  # Дневной водитель
        # Генерация рабочего времени

        shift_start_hour = random.randint(6, 10)
        shift_start_minute = random.choice([0, 15, 30, 45])
        shift_start_time = f"{shift_start_hour:02d}:{shift_start_minute:02d}"
        working_hours = 9
        shift_end_hour = shift_start_hour + working_hours
        shift_end_minute = shift_start_minute
        shift_end_minute, shift_end_hour = minutee(shift_end_minute, shift_end_hour)
        shift_end_time = f"{shift_end_hour:02d}:{shift_end_minute:02d}"

        # Генерация перерывов
        breaks = []
        break_start_hour = random.randint(13, 15)
        break_start_minute = random.choice([0, 15, 30, 45])
        break_start_time = f"{break_start_hour:02d}:{break_start_minute:02d}"

        break_end_hour = break_start_hour + 1
        break_end_minute = break_start_minute
        break_end_time = f"{break_end_hour:02d}:{break_end_minute:02d}"

        breaks.append({
                "Начало": break_start_time,
                "Конец": break_end_time
            })


        daily_schedule = {
            "Имя": driver_name,
            "График": "Дневной",
            "Начало": shift_start_time,
            "Конец": shift_end_time,
            "Перерывы": breaks,
            "Конечная": random.choice(["Ферма-2", "Аделя Кутуя"]),
            "Выходные": ["Суббота", "Воскресенье"]
        }
        return daily_schedule

    else:  # Сменный водитель
        # Генерация рабочего времени
        shift_start_hour = random.randint(0, 23)
        shift_start_minute = random.choice([0, 15, 30, 45])
        shift_start_time = f"{shift_start_hour:02d}:{shift_start_minute:02d}"
        shift_end_hour = (shift_start_hour + 12) % 24
        shift_end_minute = shift_start_minute
        shift_end_time = f"{shift_end_hour:02d}:{shift_end_minute:02d}"

        # Генерация перерывов
        breaks = []
        current_time = datetime.strptime(shift_start_time, "%H:%M")
        end_time = datetime.strptime(shift_end_time, "%H:%M")
        while current_time + timedelta(minutes=30) <= end_time:
            break_start = current_time + timedelta(hours=3)
            break_end = break_start + timedelta(minutes=10)
            if break_end > end_time:
                break
            breaks.append({
                "Начало": break_start.strftime("%H:%M"),
                "Конец": break_end.strftime("%H:%M")
            })
            current_time = break_end

        shift_schedule = {
            "Имя": driver_name,
            "График": "Сменный",
            "Начало": shift_start_time,
            "Конец": shift_end_time,
            "Перерывы": breaks,
            "Конечная": random.choice(["Ферма-2", "Аделя Кутуя"]),
            "Начало работы - день недели": random.choice(["Понедельник", "Вторник"])
        }
        return shift_schedule

def minutee(minute, hour):
    if minute >= 60:
        minute -= 60
        hour += 1
    if hour >= 24:
        hour -= 24
    return minute, hour

def is_time_in_interval(start_time, end_time, current_time):
    if start_time <= end_time:
        return start_time <= current_time < end_time
    else:
        return current_time >= start_time or current_time < end_time
def generate_buses(num_buses, stops, reverse_stops):
    buses = []
    for i in range(num_buses):
        bus_number = i + 1
        start_stop_index = random.randint(0, 17)
        direction = random.choice([1, -1])
        bus = Bus(bus_number, stops, reverse_stops, start_stop_index, direction)
        buses.append(bus)
    return buses

def generate_drivers(num_drivers):
    drivers = []
    for i in range(num_drivers):
        driver_name = f"Водитель {i + 1}"
        driver_category = random.choice([1, 2])  # 1 - дневной, 2 - сменный
        schedule = generate_driver_schedule(driver_category, driver_name)
        drivers.append(schedule)
    return drivers

# Класс водителя
class Driver:
    def __init__(self, name, driver_type, start_time, end_time, breaks=None, start_day=None):
        self.name = name
        self.driver_type = driver_type  # 'day' или 'shift'
        self.start_time = start_time  # Время начала работы (часы)
        self.end_time = end_time  # Время окончания работы (часы)
        self.breaks = breaks if breaks else []  # Перерывы в работе
        self.start_day = start_day  # День начала работы (например, "Monday", "Tuesday" и т.д.)
        self.assigned = False  # Флаг, указывающий, назначен ли водитель на автобус

    def is_available_on_day(self, current_time):
        # Словарь для перевода русских названий дней недели в английские
        day_translation = {
            "Понедельник": "Monday",
            "Вторник": "Tuesday",
            "Среда": "Wednesday",
            "Четверг": "Thursday",
            "Пятница": "Friday",
            "Суббота": "Saturday",
            "Воскресенье": "Sunday"
        }

        # Преобразуем текущий день и день начала работы в английские названия
        current_day = current_time.strftime("%A")
        start_day = day_translation.get(self.start_day, self.start_day)  # Перевод дня начала работы

        if self.driver_type == "Дневной":
            return current_day not in ["Saturday", "Sunday"]
        elif self.driver_type == "Сменный":
            if self.start_day:
                start_day_index = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(
                    start_day)
                current_day_index = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",
                                     "Sunday"].index(current_day)
                days_on = (current_day_index - start_day_index) % 7
                return days_on % 2 == 0
            else:
                return current_day in ["Saturday", "Sunday"]
        return False

    def is_working(self, current_time):
        # Преобразуем время начала и окончания работы в объекты datetime
        start_time = datetime.strptime(self.start_time, "%H:%M").replace(year=current_time.year,
                                                                         month=current_time.month, day=current_time.day)
        end_time = datetime.strptime(self.end_time, "%H:%M").replace(year=current_time.year, month=current_time.month,
                                                                     day=current_time.day)

        # Если водитель работает с 23:00 до 07:00, то end_time может быть на следующий день
        if end_time < start_time:
            end_time += timedelta(days=1)

        # Проверяем, находится ли текущее время в рабочем интервале
        if start_time <= current_time < end_time:
            # Проверяем перерывы
            for break_ in self.breaks:
                break_start = break_["start"]  # Извлекаем значение "start" из словаря
                break_end = break_["end"]  # Извлекаем значение "end" из словаря

                break_start_time = datetime.strptime(break_start, "%H:%M").replace(year=current_time.year,
                                                                                   month=current_time.month,
                                                                                   day=current_time.day)
                break_end_time = datetime.strptime(break_end, "%H:%M").replace(year=current_time.year,
                                                                               month=current_time.month,
                                                                               day=current_time.day)

                if break_start_time <= current_time < break_end_time:
                    return False  # Водитель на перерыве
            return True  # Водитель работает
        return False  # Водитель не работает


# Класс автобуса
class Bus:
    def __init__(self, bus_number, route, reverse_route, start_stop_index, direction):
        self.bus_number = bus_number
        self.route = route
        self.reverse_route = reverse_route
        self.current_route = self.route
        self.current_stop_index = start_stop_index
        self.time_to_next_stop = 0
        self.direction = direction  # 1 = прямая, -1 = обратная
        self.on_parking = True  # На стоянке ли автобус
        self.passengers = 0  # Текущее количество пассажиров в автобусе
        self.driver = None  # Водитель, назначенный на автобус

    def move_to_next_stop(self):
        if self.on_parking:
            return
        if self.time_to_next_stop > 0:
            self.time_to_next_stop -= 1
        else:
            self.current_stop_index += self.direction
            if self.current_stop_index >= len(self.current_route):
                self.current_route = self.reverse_route
                self.current_stop_index = 0
            elif self.current_stop_index < 0:
                self.current_route = self.route
                self.current_stop_index = len(self.route) - 1
            self.time_to_next_stop = 5

    def park(self):
        self.on_parking = True

    def unpark(self):
        self.on_parking = False


# Класс расписания
class Schedule:
    def __init__(self, stops):
        self.stops = stops
        self.buses = []
        self.drivers = []
        self.passenger_manager = Passenger(self)

    def add_bus(self, bus):
        self.buses.append(bus)

    def add_driver(self, driver):
        self.drivers.append(driver)

    def assign_driver(self, current_time):
        for driver in self.drivers:
            print(
                f"Проверяем водителя {driver.name}: доступен={driver.is_available_on_day(current_time)}, работает={driver.is_working(current_time)}")
            if not driver.assigned and driver.is_available_on_day(current_time) and driver.is_working(current_time):
                driver.assigned = True
                print(f"Назначен водитель {driver.name} на время {current_time}")
                return driver
        print(f"Нет доступных водителей на время {current_time}")
        return None

    def update(self, current_time):
        # Сбрасываем флаг назначенности для всех водителей
        for driver in self.drivers:
            driver.assigned = False

        self.passenger_manager.update_passenger_flow(current_time)
        for bus in self.buses:
            driver = self.assign_driver(current_time)
            if driver:
                bus.driver = driver
                bus.unpark()
                bus.move_to_next_stop()
                if not bus.on_parking:
                    self.passenger_manager.board_passengers(bus)
                else:
                    bus.park()
            else:
                bus.park()
            print(
                f"Автобус {bus.bus_number}: Водитель - {bus.driver.name if bus.driver else 'Нет'}")  # Отладочный вывод

class Passenger:
    def __init__(self, schedule):
        self.schedule = schedule
        self.passengers_on_stops = {stop: 0 for stop in schedule.stops}
        self.bus_capacity = 60

    def update_passenger_flow(self, current_time):
        hour = current_time.hour
        current_day = current_time.strftime("%A")
        if current_day not in ["Saturday", "Sunday"]:
            for stop in self.schedule.stops:
                if 7 <= hour < 9 or 17 <= hour < 19:
                    self.passengers_on_stops[stop] = random.randint(30, 50)
                elif 9 <= hour < 17 or 19 <= hour < 22:
                    self.passengers_on_stops[stop] = random.randint(20, 40)
                else:
                    self.passengers_on_stops[stop] = random.randint(0, 10)
        else:
            for stop in self.schedule.stops:
                if 8 <= hour < 16:
                    self.passengers_on_stops[stop] = random.randint(10, 20)
                elif 16 <= hour < 22:
                    self.passengers_on_stops[stop] = random.randint(20, 30)
                else:
                    self.passengers_on_stops[stop] = random.randint(0, 10)

    def board_passengers(self, bus):
        if bus.on_parking:
            return 0
        current_stop = self.schedule.stops[bus.current_stop_index]
        passengers_on_stop = self.passengers_on_stops[current_stop]
        alighting_passengers = random.randint(0, bus.passengers - bus.passengers // 3)
        bus.passengers -= alighting_passengers
        available_seats = self.bus_capacity - bus.passengers
        boarding_passengers = min(passengers_on_stop, available_seats)
        self.passengers_on_stops[current_stop] -= boarding_passengers
        bus.passengers += boarding_passengers
        return passengers_on_stop - boarding_passengers


# Главный интерфейс
class BusScheduleApp(QMainWindow):
    def __init__(self, schedule):
        super().__init__()
        self.schedule = schedule
        self.current_time = datetime(2024, 1, 1, 7, 0)
        self.time_speed = 1
        self.init_ui()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_schedule)
        self.timer.start(1000 // self.time_speed)

    def init_ui(self):
        self.setWindowTitle("Расписание автобусов")
        self.setGeometry(30, 50, 1400, 900)

        self.tab_widget = QTabWidget(self)
        self.tab_widget.setStyleSheet(self.get_theme_styles())

        self.main_tab = QWidget()
        self.tab_widget.addTab(self.main_tab, "Информация")

        self.driver_tab = QWidget()
        self.tab_widget.addTab(self.driver_tab, "Расписание водителей")

        self.stop_tab = QWidget()
        self.tab_widget.addTab(self.stop_tab, "Расписание остановок")

        self.time_label = QLabel(self)
        self.time_label.setAlignment(Qt.AlignCenter)
        self.info_text = QTextEdit(self)
        self.info_text.setReadOnly(True)

        self.speed_button = QPushButton("Изменить время (2x)", self)
        self.speed_button.clicked.connect(self.speed_up_time)
        self.speed_button.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #005BB5;
            }
            QPushButton:pressed {
                background-color: #004A99;
            }
        """)

        self.pause_button = QPushButton("Пауза", self)
        self.pause_button.clicked.connect(self.toggle_pause)
        self.pause_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9500;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #E68A00;
            }
            QPushButton:pressed {
                background-color: #CC7A00;
            }
        """)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.speed_button)
        button_layout.addWidget(self.pause_button)

        splitter = QSplitter(Qt.Vertical)
        info_layout = QVBoxLayout()
        info_layout.addWidget(self.time_label)
        info_layout.addWidget(self.info_text)
        info_widget = QWidget()
        info_widget.setLayout(info_layout)
        splitter.addWidget(info_widget)

        self.layout = QVBoxLayout(self.main_tab)
        self.layout.addWidget(splitter)
        self.layout.addLayout(button_layout)

        self.driver_layout = QVBoxLayout(self.driver_tab)
        self.driver_text = QTextEdit(self)
        self.driver_text.setReadOnly(True)
        self.driver_layout.addWidget(self.driver_text)

        self.stop_layout = QVBoxLayout(self.stop_tab)
        self.stop_text = QTextEdit(self)
        self.stop_text.setReadOnly(True)
        self.stop_layout.addWidget(self.stop_text)

        self.setCentralWidget(self.tab_widget)

    def get_theme_styles(self):
        if darkdetect.isDark():
            return """
                QMainWindow { background-color: #1E1E1E; color: #FFFFFF; }
                QTabWidget::pane { border: 1px solid #444444; border-radius: 8px; }
                QTabBar::tab { background-color: #333333; color: #FFFFFF; padding: 10px 20px; border: 1px solid #444444; border-bottom: none; border-top-left-radius: 8px; border-top-right-radius: 8px; }
                QTabBar::tab:selected { background-color: #007AFF; color: #FFFFFF; }
                QTextEdit { background-color: #2E2E2E; color: #FFFFFF; border: 1px solid #444444; border-radius: 8px; padding: 10px; font-size: 14px; }
                QLabel { font-size: 18px; font-weight: bold; font-family: 'Helvetica Neue', sans-serif; color: #FFFFFF; }
            """
        else:
            return """
                QMainWindow { background-color: #F5F5F5; color: #333333; }
                QTabWidget::pane { border: 1px solid #E0E0E0; border-radius: 8px; }
                QTabBar::tab { background-color: #F5F5F5; color: #333333; padding: 10px 20px; border: 1px solid #E0E0E0; border-bottom: none; border-top-left-radius: 8px; border-top-right-radius: 8px; }
                QTabBar::tab:selected { background-color: #007AFF; color: #FFFFFF; }
                QTextEdit { background-color: #FFFFFF; color: #333333; border: 1px solid #E0E0E0; border-radius: 8px; padding: 10px; font-size: 14px; }
                QLabel { font-size: 18px; font-weight: bold; font-family: 'Helvetica Neue', sans-serif; color: #333333; }
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
        return driver_types.get(driver_type, driver_type)

    def show_driver_schedule(self):
        driver_info = "Расписание водителей (в часах):\n"
        for driver in self.schedule.drivers:
            driver_type_ru = self.translate_driver_type(driver.driver_type)
            driver_info += (
                f"  Водитель: {driver.name}\n"
                f"  Тип: {driver_type_ru}\n"
                f"  Рабочие часы: {driver.start_time} - {driver.end_time}\n"
            )
            # Добавляем перерывы
            if driver.breaks:
                breaks_str = ", ".join([f"{break_['start']}-{break_['end']}" for break_ in driver.breaks])
                driver_info += f"  Перерывы: {breaks_str}\n"
            else:
                driver_info += "  Перерывы: \n"
            driver_info += "\n"
        self.driver_text.setText(driver_info)

    def show_stop_schedule(self):
        info_listt = ''
        for bus in self.schedule.buses:
            if bus.driver and bus.driver.is_working(self.current_time) and not bus.on_parking:
                current_stop = self.schedule.stops[bus.current_stop_index]
                arrival_time = self.current_time + timedelta(minutes=bus.time_to_next_stop)
                current_day = self.current_time.strftime("%A")
                current_day_ru = self.translate_day_to_russian(current_day)
                info = (
                    f"В {current_day_ru} {arrival_time.strftime('%H:%M')} - {current_stop} - Автобус {bus.bus_number} (Водитель: {bus.driver.name})\n"
                )
                info_listt += info
        if info_listt:
            self.stop_text.append(info_listt[:-2])

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
        return days.get(day, day)

    def update_schedule(self):
        self.schedule.update(self.current_time)
        self.current_time += timedelta(minutes=1)
        current_day = self.current_time.strftime("%A")
        current_day_ru = self.translate_day_to_russian(current_day)
        self.time_label.setText(f"{current_day_ru} - {self.current_time.strftime('%H:%M')}")
        self.info_text.setText(self.get_bus_info())
        self.show_driver_schedule()
        self.show_stop_schedule()

    def get_bus_info(self):
        info = ""
        for bus in self.schedule.buses:
            if bus.driver and not bus.on_parking and bus.driver.is_working(self.current_time):
                stop = self.schedule.stops[bus.current_stop_index]
                passengers_left = self.schedule.passenger_manager.board_passengers(bus)
                info += f"Автобус {bus.bus_number} на остановке {stop}, водитель: {bus.driver.name}, пассажиров в автобусе: {bus.passengers}, не поместились {passengers_left}\n"
        return info

    def speed_up_time(self):
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
        self.timer.setInterval(1000 // self.time_speed)


# Основная функция
def main():
    stops = [
        "Ферма-2", "Рауиса Гареева", "Азамат", "ДРКБ", "РКБ",
        "Южная", "д. Универсиады (Победы)", "Академика Парина",
        "Медучилище", "Мавлютова", "Братьев Касимовых", "Метро Горки",
        "Рихарда Зорге", "Даурская (Рихарда Зорге)", "Сады",
        "Гвардейская", "Кафе Сирень", "Аделя Кутуя"
    ]
    reverse_stops = list(reversed(stops))
    # Создаем расписание
    schedule = Schedule(stops)

    # Генерируем автобусы
    num_buses = 8  # Количество автобусов
    buses = generate_buses(num_buses, stops, reverse_stops)

    # Добавляем автобусы в расписание
    for bus in buses:
        schedule.add_bus(bus)

    # Генерируем водителей
    num_drivers = 10  # Количество водителей
    drivers = generate_drivers(num_drivers)


    for driver in drivers:
        breaks = []
        if "Перерывы" in driver and driver["Перерывы"]:  # Проверяем, что перерывы есть
            for break_period in driver["Перерывы"]:
                if "Начало" in break_period and "Конец" in break_period:  # Проверяем, что ключи есть
                    breaks.append({"start": break_period["Начало"], "end": break_period["Конец"]})

        driver_obj = Driver(
            name=driver["Имя"],
            driver_type=driver["График"],
            start_time=driver["Начало"],
            end_time=driver["Конец"],
            breaks=breaks,
            start_day=driver["Начало работы - день недели"] if "Начало работы - день недели" in driver else None
        )
        schedule.add_driver(driver_obj)

    # Запускаем приложение
    app = QApplication(sys.argv)
    main_window = BusScheduleApp(schedule)
    main_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()