from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from pydantic import BaseModel


class CarStatus(StrEnum):
    available = "available"
    reserve = "reserve"
    sold = "sold"
    delivery = "delivery"


class Car(BaseModel):
    vin: str
    model: int
    price: Decimal
    date_start: datetime
    status: CarStatus

    _has_index_changed: bool = False

    def index(self) -> str:
        return self.vin
    
    # имя индексного поля
    @staticmethod
    def primary_key_field() -> str:
        return 'vin'
    
    # создание объекта из строки с разделителями
    @staticmethod
    def from_string(value: str):
        fields = value.rstrip().split(';')
        return Car(
            vin = fields[0],
            model = int(fields[1]),
            price = Decimal(fields[2]),
            date_start = datetime.strptime(fields[3], f'%Y-%m-%d %H:%M:%S'),
            status = CarStatus(fields[4])
        )


class Model(BaseModel):
    id: int
    name: str
    brand: str

    _has_index_changed: bool = False

    def index(self) -> str:
        return str(self.id)

    # имя индексного поля
    @staticmethod
    def primary_key_field() -> str:
        return 'id'
    
    # создание объекта из строки с разделителями
    @staticmethod
    def from_string(value: str):
        fields = value.rstrip().split(';')
        return Model(
            id = int(fields[0]), 
            name = fields[1], 
            brand = fields[2]
        )


class Sale(BaseModel):
    sales_number: str
    car_vin: str
    sales_date: datetime
    cost: Decimal

    _has_index_changed: bool = False

    def index(self) -> str:
        return self.sales_number

    @staticmethod
    def primary_key_field() -> str:
        return 'sales_number'
    
    # создание объекта из строки с разделителями
    @staticmethod
    def from_string(value: str):
        fields = value.rstrip().split(';')
        return Sale(
            sales_number = fields[0],
            car_vin = fields[1], 
            sales_date = datetime.strptime(fields[2], f'%Y-%m-%d %H:%M:%S'),
            cost = Decimal(fields[3])
        )


class CarFullInfo(BaseModel):
    vin: str
    car_model_name: str
    car_model_brand: str
    price: Decimal
    date_start: datetime
    status: CarStatus
    sales_date: datetime | None
    sales_cost: Decimal | None


class ModelSaleStats(BaseModel):
    car_model_name: str
    brand: str
    sales_number: int
