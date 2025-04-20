from models import Car, CarFullInfo, CarStatus, Model, ModelSaleStats, Sale
import os
import json

class CarService:
    def __init__(self, root_directory_path: str) -> None:
        self.MAX_LINE_LEN = 500
        self.FIELD_SEPARATOR = ';'
        self.RN_LEN = 2 if os.name == 'nt' else 1

        self.root_directory_path = root_directory_path

        # загрузка индексов в память
        self.index_collection = {}
        self.load_index(Model)
        self.load_index(Car)
        self.load_index(Sale)

    def get_object_data_file_name(self, obj_type) -> str:
        return self.root_directory_path + os.path.sep + obj_type.__name__.lower() + 's.txt'

    def get_object_index_file_name(self, obj_type) -> str:
        return self.root_directory_path + os.path.sep + obj_type.__name__.lower() + 's_index.txt'

    def load_index(self, obj):
        index_filename = self.get_object_index_file_name(obj)
        loaded_index_data = []
        if os.path.exists(index_filename):
            with open(index_filename, "r") as f:
                loaded_index_data = json.load(f)
        self.index_collection[obj.__name__] = loaded_index_data

    # выдает имя ключевого поля, если таковое есть
    def get_primary_field(self, obj) -> str:
        if hasattr(obj, 'primary_key_field'):
            return obj.primary_key_field()
        
    # выдает значение ключевого поля, если такое есть
    def get_primary_value(self, obj) -> str:
        result = None
        if hasattr(obj, 'index'):
            return obj.index()
        return result

    # выдает строку из полей объекта через разделитель.
    def get_fields_str(self, obj) -> str:
        data_fields = {
            k: str(v)
            for k, v in vars(obj).items()
        }

        return self.FIELD_SEPARATOR.join(v for k, v in data_fields.items()).ljust(self.MAX_LINE_LEN) + '\n'
    
    # поиск по индексу. Выдает номер строки в файле данных
    def scan_index(self, obj_type, value) -> int:
        # получить индекс нужного объекта
        index = self.index_collection[obj_type.__name__]
        value = str(value)# TODO переделать, чтобы индекс хранил native значения, а не строки
        return int(next((found['value'] for found in index if found['key'] == value), 0))
    
    # сохраняет в индекс пару значений: ключ объекта и номер строки, сортирует и дампит в файл
    def save_index(self, obj, position):
        obj_index = self.get_primary_value(obj)
        # Если у объекта есть индекс
        if obj_index != None:
            index = self.index_collection[type(obj).__name__]
            # добавить в индекс новую пару Индекс-НомерВФайле
            index.append({'key': obj_index, 'value': len(index) + 1})
            # сортировка по ключу
            index.sort(key = lambda x: x["key"])
            # сохранение в файл. В идеале дампить не сразу, а после всех инсертов
            index_filename = self.get_object_index_file_name(type(obj))
            with open(index_filename, "w") as f:
                json.dump(index, f, indent = 4)
    
    # Обновляет\добавляет объект в куче
    def update_data(self, obj, position: int = 0):
        data_filename = self.get_object_data_file_name(type(obj))
        dumped_object = self.get_fields_str(obj)
        file_method = 'r+' if position > 0 else 'a'
        with open(data_filename, file_method) as f:
            if position > 0:
                seek_position = (position - 1) * (self.MAX_LINE_LEN + self.RN_LEN)
                f.seek(seek_position)
            f.write(dumped_object)

    #
    def apply_filter(self, obj: object, filters: list[dict]) -> bool:
        if not filters:
            return True
        
        for filter in filters:
            for field_name, value in filter.items():
                actual_value = getattr(obj, field_name)
                
                # Сравниваем значения
                if actual_value != value:
                    return False
                    
        return True

    # Сохранение записи в файл и индекс (если есть)
    def save_data(self, obj):
        # поиск в индексе объекта
        obj_index = self.get_primary_value(obj)
        if obj_index != None:            
            index_index = self.scan_index(type(obj), obj_index)

        # 2. Если есть запись, обновить данные
        if index_index != 0:
            self.update_data(obj, index_index)

        # 3. Если нет - добавить в кучу, внести в индекс
        if index_index == 0:
            self.update_data(obj)
            record_number = len(self.index_collection[type(obj).__name__]) + 1
            obj_index = self.save_index(obj, record_number)

    def read_table_file(self, obj_type, position: int, filters: list[dict]) -> list[object]:
        result = []
        data_filename = self.get_object_data_file_name(obj_type)
        with open(data_filename, 'r') as file:
            # если указан номер строки
            if position != None:
                seek_position = (position - 1) * (self.MAX_LINE_LEN + self.RN_LEN)
                file.seek(seek_position)
                value = file.read(self.MAX_LINE_LEN)
                current_object = obj_type.from_string(value)
                if self.apply_filter(current_object, filters):
                    result.append(current_object)
            else:
                # чтение кусками по MAX_LINE_LEN
                while True:
                    value = file.read(self.MAX_LINE_LEN + self.RN_LEN - 1)[:self.MAX_LINE_LEN] #-1 - потому что не знаю почему, но при чтении в винде 0x0D0A преобразовывется в один символ \n. А при записи - наоборот.
                    if value=='':
                        break
                    current_object = obj_type.from_string(value)
                    if self.apply_filter(current_object, filters):
                        result.append(current_object)

        return result
    
    # выдача данных из таблицы по индексу
    def lookup_data(self, obj_type, key_value: str, filters: list[dict]) -> list[object]:
        # найти номер строки в файле
        index_index = self.scan_index(obj_type, key_value)
        # выдать данные
        return self.read_table_file(obj_type, index_index, filters)

    # сканирование кучи по фильтру
    def scan_data(self, obj_type, filters: list[dict]) -> list[object]:
        return self.read_table_file(obj_type, None, filters)

    # выборка данных из таблицы. Выдает список типа obj_type 
    def select_data(self, obj_type, filters: list[dict] = None) -> list[object]:
        founded_data = []

        # получим имя индексового поля
        index_field = obj_type.primary_key_field()
        index_value = None
        # есть ли индекс в фильтре
        for filter in filters:
            for field_name, value in filter.items():
                if field_name == index_field:
                    index_value = value
        
        # если есть индекс у таблицы и задан поиск по ключу
        if hasattr(obj_type, 'primary_key_field') and index_value != None:            
            founded_data = self.lookup_data(obj_type, index_value, filters)
        else:
            # а если нет - сканирование кучи
            founded_data = self.scan_data(obj_type, filters)
        
        return founded_data

    # Задание 1. Сохранение автомобилей и моделей
    def add_model(self, model: Model) -> Model:
        return self.save_data(model)

    # Задание 1. Сохранение автомобилей и моделей
    def add_car(self, car: Car) -> Car:
        return self.save_data(car)

    # Задание 2. Сохранение продаж.
    def sell_car(self, sale: Sale) -> Car:
        self.save_data(sale)
        return None

    # Задание 3. Доступные к продаже
    def get_cars(self, status: CarStatus) -> list[Car]:        
        raise NotImplementedError

    # Задание 4. Детальная информация
    def get_car_info(self, vin: str) -> CarFullInfo | None:
        raise NotImplementedError

    # Задание 5. Обновление ключевого поля
    def update_vin(self, vin: str, new_vin: str) -> Car:
        raise NotImplementedError

    # Задание 6. Удаление продажи
    def revert_sale(self, sales_number: str) -> Car:
        raise NotImplementedError

    # Задание 7. Самые продаваемые модели
    def top_models_by_sales(self) -> list[ModelSaleStats]:
        raise NotImplementedError
