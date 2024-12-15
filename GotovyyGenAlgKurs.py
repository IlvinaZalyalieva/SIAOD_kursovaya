import random
from datetime import datetime, timedelta

# Остановки маршрута
stops = [
    "Ферма-2", "Рауиса Гареева", "Азамат", "ДРКБ", "РКБ",
    "Южная", "д. Универсиады (Победы)", "Академика Парина",
    "Медучилище", "Мавлютова", "Братьев Касимовых", "Метро Горки",
    "Рихарда Зорге", "Даурская (Рихарда Зорге)", "Сады",
    "Гвардейская", "Кафе Сирень", "Аделя Кутуя"
]
reverse_route_stops = list(reversed(stops))
# Задаем параметры
driver_list = [
    {'name': f'Driver{i+1}'} for i in range(10)
]
bus_list = [
    {'id': i+1, 'route': f'Route {chr(65+i)}', 'passengers': 0, 'current_stop': stops[0], 'on_parking': False} for i in range(8)
]
bus_capacity = 40
# Устанавливаем продолжительность симуляции на 24 часа
simulation_duration = timedelta(hours=24)
end_time = datetime(2024, 1, 1, 7, 0) + simulation_duration

def update_passenger_flow(stops, current_time):
    hour = current_time.hour
    current_day = current_time.strftime("%A")
    passengers_on_stops = {}

    if current_day not in ["Saturday", "Sunday"]:
        for stop in stops:
            if 7 <= hour < 9 or 17 <= hour < 19:  # Часы пик
                passengers_on_stops[stop] = random.randint(40, 60)
            elif 9 <= hour < 17 or 19 <= hour < 22:  # День
                passengers_on_stops[stop] = random.randint(30, 40)
            else:  # Ночь
                passengers_on_stops[stop] = random.randint(0, 20)
    else:
        for stop in stops:
            if 8 <= hour < 16:
                passengers_on_stops[stop] = random.randint(10, 20)
            elif 16 <= hour < 22:
                passengers_on_stops[stop] = random.randint(20, 40)
            else:  # Ночь
                passengers_on_stops[stop] = random.randint(0, 10)

    return passengers_on_stops

def board_passengers(bus, passengers_on_stops, bus_capacity):
    current_stop = bus['current_stop']
    passengers_on_stop = passengers_on_stops[current_stop]
    alighting_passengers = random.randint(0, bus['passengers'] - bus['passengers'] // 3)
    bus['passengers'] -= alighting_passengers
    available_seats = bus_capacity - bus['passengers']
    boarding_passengers = min(passengers_on_stop, available_seats)
    passengers_on_stops[current_stop] = passengers_on_stops[current_stop] - boarding_passengers + alighting_passengers // 4
    bus['passengers'] += boarding_passengers
    # Подсчет пассажиров, которые не поместились
    passengers_left = passengers_on_stop - boarding_passengers
    return passengers_left

def minutee(shift_end_minute, shift_end_hour):
    if shift_end_minute >= 60:
        shift_end_minute -= 60
        shift_end_hour += 1
    return shift_end_minute, shift_end_hour

# Инициализация популяции
def initialize_population(driver_pool, population_size):
    population = []
    for _ in range(population_size):
        individual_schedule = []
        for driver in driver_pool:
            driver_category = random.choice([1, 2])

            if driver_category == 1:  # Дневной водитель
                shift_start_hour = random.randint(6, 10)
                shift_start_minute = random.choice([0, 15, 30, 45])
                shift_start_time = f"{shift_start_hour:02d}:{shift_start_minute:02d}"

                working_hours = 9
                shift_end_hour = shift_start_hour + working_hours
                shift_end_minute = shift_start_minute
                shift_end_minute, shift_end_hour = minutee(shift_end_minute, shift_end_hour)
                shift_end_time = f"{shift_end_hour:02d}:{shift_end_minute:02d}"

                break_start_hour = random.randint(13, 15)
                break_start_minute = random.choice([0, 15, 30, 45])
                break_start_time = f"{break_start_hour:02d}:{break_start_minute:02d}"

                break_end_hour = break_start_hour + 1
                break_end_minute = break_start_minute
                break_end_time = f"{break_end_hour:02d}:{break_end_minute:02d}"

                daily_schedule = {
                    "Имя": driver["name"],
                    "График": driver_category,
                    "Начало": shift_start_time,
                    "Конец": shift_end_time,
                    "Перерывы": [{"Старт": break_start_time, "Конец": break_end_time}],
                    "Конечная": random.choice(["Ферма-2", "Аделя Кутуя"]),
                    "Выходные": ["Суббота", "Воскресенье"]
                }

            else:  # Сменный водитель
                shift_start_hour = random.randint(0, 23)
                shift_start_minute = random.choice([0, 15, 30, 45])
                shift_start_time = f"{shift_start_hour:02d}:{shift_start_minute:02d}"

                shift_end_hour = (shift_start_hour + 12) % 24
                shift_end_minute = shift_start_minute
                shift_end_time = f"{shift_end_hour:02d}:{shift_end_minute:02d}"

                break_periods = []
                current_hour = shift_start_hour
                current_minute = shift_start_minute

                while True:
                    travel_hours = 3
                    current_hour += travel_hours
                    if current_hour >= 24:
                        current_hour -= 24
                    current_minute += 10
                    current_minute, current_hour = minutee(current_minute, current_hour)

                    if current_hour >= shift_end_hour and current_minute >= shift_end_minute:
                        break

                    break_periods.append({
                        "Начало": f"{current_hour:02d}:{current_minute:02d}",
                        "Конец": f"{(current_hour):02d}:{(current_minute + 10) % 60:02d}"
                    })

                shift_schedule = {
                    "Имя": driver["name"],
                    "График": driver_category,
                    "Начало": shift_start_time,
                    "Конец": shift_end_time,
                    "Перерывы": break_periods,
                    "Конечная": random.choice(["Ферма-2", "Аделя Кутуя"]),
                    "Начало работы - день недели": [random.choice(["Понедельник", "Вторник"])]
                }
            individual_schedule.append(daily_schedule if driver_category == 1 else shift_schedule)
        population.append(individual_schedule)
    return population

# Функция оценки 
def fitness_function(individual, driver_list, bus_list):
    updated_driver_list = []
    for i, driver in enumerate(driver_list):
        updated_driver = individual[i]
        updated_driver_list.append(updated_driver)
    total_passengers = 0
    current_time = datetime.now().replace(hour=7, minute=0, second=0, microsecond=0) + timedelta(minutes=random.randint(0, 60))
    end_time = current_time + timedelta(hours=24)  # Конец дня

    while current_time < end_time:
        passengers_on_stops = update_passenger_flow(stops, current_time)
        for bus in bus_list:
            passengers_left = board_passengers(bus, passengers_on_stops, bus_capacity)
            total_passengers += passengers_left
        current_time += timedelta(minutes=10)  # Шаг времени
    return -total_passengers  # Невместившиеся пассажиры

def select(population, fitness_scores, top_parents):
    parents = list(zip(fitness_scores, population))
    sorted_population = sorted(parents, key=lambda x: x[0], reverse=True)
    # Извлекаем только индивидуумов из первых top_parents пар
    top_individuals = [individual for _, individual in sorted_population[:top_parents]]
    return top_individuals

def crossover(parent1, parent2):
    rndm = random.randint(1, len(parent1) - 1)
    child1 = parent1[:rndm] + parent2[rndm:]
    child2 = parent2[:rndm] + parent1[rndm:]
    return child1, child2

# Функция мутации
def mutate(individual, mutation_probability):
    for schedule in individual:
        if random.random() < mutation_probability:
            if schedule['График'] == 1:  # Дневной водитель
                new_shift_start_hour = random.randint(6, 11)
                new_shift_start_minute = random.choice([0, 15, 30, 45])

                new_break_start_hour = random.randint(13, 15)
                new_break_start_minute = random.choice([0, 15, 30, 45])

                new_break_end_hour = new_break_start_hour + 1
                new_break_end_minute = new_break_start_minute

                new_shift_end_hour = new_shift_start_hour + 8 + (1 if new_break_start_hour >= new_shift_start_hour else 0)
                new_shift_end_minute = new_shift_start_minute

                schedule['Начало'] = f"{new_shift_start_hour:02d}:{new_shift_start_minute:02d}"
                schedule['Конец'] = f"{new_shift_end_hour:02d}:{new_shift_end_minute:02d}"
                schedule['Перерывы'][0]['Начало'] = f"{new_break_start_hour:02d}:{new_break_start_minute:02d}"
                schedule['Перерывы'][0]['Конец'] = f"{new_break_end_hour:02d}:{new_break_end_minute:02d}"
                schedule['Конечная'] = random.choice(["Ферма-2", "Аделя Кутуя"])
            else:  # Сменный водитель
                new_shift_start_hour = random.randint(0, 23)
                new_shift_start_minute = random.choice([0, 15, 30, 45])

                new_shift_end_hour = (new_shift_start_hour + 12) % 24
                new_shift_end_minute = new_shift_start_minute

                break_periods = []
                current_hour = new_shift_start_hour
                current_minute = new_shift_start_minute
                while True:
                    break_hour = current_hour + 3
                    if break_hour >= 24 or break_hour > new_shift_end_hour:
                        break
                    break_minute = current_minute
                    break_periods.append(f"{break_hour:02d}:{break_minute:02d}")
                    current_hour = break_hour

                schedule['Начало'] = f"{new_shift_start_hour:02d}:{new_shift_start_minute:02d}"
                schedule['Конец'] = f"{new_shift_end_hour:02d}:{new_shift_end_minute:02d}"
                schedule['Конечная'] = random.choice(["Ферма-2", "Аделя Кутуя"])
                schedule['Перерывы'] = break_periods
    return individual

def genetic_algorithm(driver_list, bus_list, generations=100, population_size=300, mutation_rate=0.3, top_n=100):
    population = initialize_population(driver_list, population_size)
    best_solution = None
    best_fitness = float('-inf')
    no_improvement_count = 0
    last_best_fitness = float('-inf')

    for generation in range(generations):
        fitness_scores = [fitness_function(individual, driver_list, bus_list) for individual in population]
        current_best_fitness = max(fitness_scores)
        if current_best_fitness > last_best_fitness:
            last_best_fitness = current_best_fitness
            no_improvement_count = 0
        else:
            no_improvement_count += 1
        # Увеличиваем частоту мутации, если фитнес-функция не улучшается
        if no_improvement_count > 5:  
            mutation_rate *= 1.2  # Увеличиваем частоту мутаций

        for score, individual in zip(fitness_scores, population):
            if score > best_fitness:
                best_fitness = score
                best_solution = individual

        print(f"Generation {generation + 1}: Best Fitness = {best_fitness}")

        parents = select(population, fitness_scores, top_n)
        next_population = []

        while len(next_population) < population_size:
            parent1, parent2 = random.sample(parents, 2)
            child1, child2 = crossover(parent1, parent2)
            next_population.append(mutate(child1, mutation_rate))
            if len(next_population) < population_size:
                next_population.append(mutate(child2, mutation_rate))
        population = next_population
    return best_solution, best_fitness

best_solution, best_fitness = genetic_algorithm(driver_list, bus_list)
print(f"Best Schedule (Fitness = {best_fitness}):")
for schedule in best_solution:
    print(schedule)