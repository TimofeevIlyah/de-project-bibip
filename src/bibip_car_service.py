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
    
    def has_index_changed(self, obj) -> bool:
        result = False
        if hasattr(obj, '_has_index_changed'):
            return obj._has_index_changed
        
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
    def save_index(self, obj):
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

    def update_index(self, obj, prior_index):
        obj_index = self.get_primary_value(obj)
        # Если у объекта есть индекс
        if obj_index != None:
            index = self.index_collection[type(obj).__name__]
            # изменить по старому ключу запись, внеся новый ключ, оставив старый номер строки
            for item in index:
                if item.get('key') == prior_index:
                    item['key'] = self.get_primary_value(obj)
            # сортировка
            index.sort(key = lambda x: x["key"])
            # записать обратно
            self.index_collection[type(obj).__name__] = index
            # сохранить. TODO: вынести в функцию
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

    def delete_data_with_vacuum(self, obj_type, filters: list[dict]):
        # считать все данные в DataSet
        ds = self.read_table_file(obj_type, None, None)
        # удалить файлы данных и индекса
        data_filename = self.get_object_data_file_name(obj_type)
        if os.path.exists(data_filename):
            os.remove(data_filename)
        index_filename = self.get_object_index_file_name(obj_type)
        if os.path.exists(index_filename):
            os.remove(index_filename)
        # очистить индекс в памяти
        self.index_collection[obj_type.__name__] = []
        
        # сохранить последовательно данные, которые не удовлетворяют фильтру на удаление
        for obj in ds:
            if not self.apply_filter(obj, filters):
                self.save_data(obj)


    #проверяет, соответствует ли объект фильтру
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
    def save_data(self, obj) -> object:
        index_index: int = 0
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
            # record_number = len(self.index_collection[type(obj).__name__]) + 1
            self.save_index(obj)

        return obj

    # чтение данных. одну запись, если поиск идет по индексу (postition) или все записи.
    # для обоих случаев есть дополнительная фильтрация
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
        result = None
        # найти номер строки в файле
        index_index = self.scan_index(obj_type, key_value)
        if index_index != 0:
            result = self.read_table_file(obj_type, index_index, filters)
        # выдать данные
        return result

    # сканирование кучи по фильтру
    def scan_data(self, obj_type, filters: list[dict]) -> list[object]:
        result = self.read_table_file(obj_type, None, filters)
        if len(result)==0:
            result = None
        return result

    # выборка данных из таблицы. Выдает список типа obj_type 
    # фильтр filters указываь как список словарей в виде [{'<имя поля N>': 'Значение'}, {'<имя поля N>': Значение}, ...]
    # сортировку указывать как список словарей в виде [{'<имя поля N>': 'asc|desc'}, ...]
    def select_data(self, obj_type, filters: list[dict] = None, sorts: list[dict] = None) -> list[object]:
        founded_data = None
        # получим имя индексового поля
        index_field = obj_type.primary_key_field()
        index_value = None
        # есть ли индекс в фильтре
        if filters:
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
        
        # сортировка
        if  founded_data != None and sorts:
            # с конца сортируем
            for sort in reversed(sorts):
                for field, order in sort.items():
                    is_desc = order.lower() == "desc"
                    founded_data.sort(
                        key = lambda x: getattr(x, field),
                        reverse = is_desc
                    )
            
        return founded_data

    # Задание 1. Сохранение автомобилей и моделей
    def add_model(self, model: Model) -> Model:
        return self.save_data(model)

    # Задание 1. Сохранение автомобилей и моделей
    def add_car(self, car: Car) -> Car:
        return self.save_data(car)

    # Задание 2. Сохранение продаж.
    def sell_car(self, sale: Sale) -> Car:
        # поиск машины, указанной в продаже
        car: Car = self.select_data(Car, [{'vin': sale.car_vin}])[0]
        if car != None:            
            # меняем статус на Продано
            car.status = CarStatus('sold')
            # дамп в файл. тут бы транзакцию...
            self.save_data(car)
            self.save_data(sale)
            return car

        return None

    # Задание 3. Доступные к продаже
    def get_cars(self, status: CarStatus) -> list[Car]:
        result: list[Car] = self.select_data(Car, [{'status':status}], [{'vin': 'asc'}])
        return result

    # Задание 4. Детальная информация
    def get_car_info(self, vin: str) -> CarFullInfo | None:
        result = None
        car: Car = self.select_data(Car, [{'vin': vin}])[0]
        if car != None:
            result_vin = car.vin
            result_price = car.price
            result_date_start = car.date_start
            result_status = car.status

            model: Model = self.select_data(Model, [{'id': car.model}])[0]
            if model != None:
                result_car_model_name = model.name
                result_car_model_brand = model.brand
            
            sale: Sale = self.select_data(Sale, [{'car_vin': vin}])[0]
            if sale!=None:
                result_sales_date = sale.sales_date
                result_sales_cost = sale.cost

            result = CarFullInfo(
                vin = result_vin,
                car_model_name = result_car_model_name,
                car_model_brand = result_car_model_brand,
                price = result_price,
                date_start = result_date_start,
                status = result_status,
                sales_date = result_sales_date,
                sales_cost = result_sales_cost,
            )            

        return result

    # Задание 5. Обновление ключевого поля
    def update_vin(self, vin: str, new_vin: str) -> Car:
        car = None
        if vin != new_vin:
            ds_cars = self.select_data(Car, [{'vin': vin}])
            if ds_cars:
                car: Car = ds_cars[0]
                if car:
                    if car.vin != new_vin:
                        old_vin = car.vin
                        car.vin = new_vin
                        car._has_index_changed = True   # настроить валидатор или сеттер на автоматическое заполнение у меня не вышло
                        self.update_index(car, old_vin) # полный ахтунг с точки зрения принципов ООП. Но моих знаний питона не хватает(особенно с не ясным для меня pydantic)
                        self.save_data(car)
                        car._has_index_changed = False

        return car

    # Задание 6. Удаление продажи
    def revert_sale(self, sales_number: str) -> Car:
        ds_sales = self.select_data(Sale, [{'sales_number': sales_number}])
        if ds_sales != None:
            sale: Sale = ds_sales[0]
            car: Car = self.select_data(Car, [{'vin': sale.car_vin}])[0]
            # удалить продажу
            self.delete_data_with_vacuum(Sale, [{'sales_number': sales_number}])
            # обновить статус машины
            car.status = CarStatus('available')
            # сохранить
            self.save_data(car)


    # Задание 7. Самые продаваемые модели
    def top_models_by_sales(self) -> list[ModelSaleStats]:
        result = []# list[ModelSaleStats]
        # подсчет количеств моделей
        models_prepare = {}
        ds_sales = self.select_data(Sale)
        for sale in ds_sales:
            car: Car = self.select_data(Car, [{'vin': sale.car_vin}])[0]
            amount = models_prepare.get(car.model)
            if amount == None:
                models_prepare[car.model] = 1
            else:
                models_prepare[car.model] = amount + 1
        # сортировка
        models_prepare = dict(sorted(models_prepare.items(), key=lambda item: item[1], reverse=True)[:3])
        for model_id, amount in models_prepare.items():
            model: Model = self.select_data(Model, [{'id': model_id}])[0]
            result.append(ModelSaleStats(car_model_name = model.name, brand = model.brand, sales_number = amount))

        return result