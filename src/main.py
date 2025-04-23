from models import Car, CarFullInfo, CarStatus, Model, ModelSaleStats, Sale
from bibip_car_service import CarService

path: str = 'DB'


def Main(data_path: str):
    car_service = CarService(data_path)

    # car_service.add_model(Model(id = 2, brand = 'Kia',     name = 'Sorento'))
    # car_service.add_model(Model(id = 1, brand = 'Kia',     name = 'Optima'))
    # car_service.add_model(Model(id = 3, brand = 'Mazda',   name = '3'))
    # car_service.add_model(Model(id = 4, brand = 'Nissan',  name = 'Pathfinder'))
    # car_service.add_model(Model(id = 5, brand = 'Renault', name = 'Logan'))
    # car_service.add_car(Car(vin = 'KNAGM4A77D5316538', model = 1, price = 2000,    date_start = '2024-02-08', status = 'available'))
    # car_service.add_car(Car(vin = '5XYPH4A10GG021831', model = 2, price = 2300,    date_start = '2024-02-20', status = 'reserve'))
    # car_service.add_car(Car(vin = 'KNAGH4A48A5414970', model = 1, price = 2100,    date_start = '2024-04-04', status = 'available'))
    # car_service.add_car(Car(vin = 'JM1BL1TFXD1734246', model = 3, price = 2276.65, date_start = '2024-05-17', status = 'available'))
    # car_service.add_car(Car(vin = 'JM1BL1M58C1614725', model = 3, price = 2549.10, date_start = '2024-05-17', status = 'reserve'))
    # car_service.add_car(Car(vin = 'KNAGR4A63D5359556', model = 1, price = 2376,    date_start = '2024-05-17', status = 'available'))
    # car_service.add_car(Car(vin = '5N1CR2MN9EC641864', model = 4, price = 3100,    date_start = '2024-06-01', status = 'available'))
    # car_service.add_car(Car(vin = 'JM1BL1L83C1660152', model = 3, price = 2635.17, date_start = '2024-06-01', status = 'available'))
    # car_service.add_car(Car(vin = '5N1CR2TS0HW037674', model = 4, price = 3100,    date_start = '2024-06-01', status = 'available'))
    # car_service.add_car(Car(vin = '5N1AR2MM4DC605884', model = 4, price = 3200,    date_start = '2024-07-15', status = 'available'))
    # car_service.add_car(Car(vin = 'VF1LZL2T4BC242298', model = 5, price = 2280.76, date_start = '2024-08-31', status = 'delivery'))

    # result = car_service.select_data(Model, [], [{'brand': 'desc'}, {'name':'asc'}])
    result = car_service.get_cars(CarStatus.available)
    for r in result:
        print(r)
    # result = car_service.select_data(Model, [{'brand': 'Kia'},{'name': 'Optima'}])
    # print(result)

    # car_service.sell_car(Sale(sales_number = '1', car_vin = 'KNAGM4A77D5316538', sales_date = '2025-04-01', cost = 1900.))
    # car_service.sell_car(Sale(sales_number = '2', car_vin = '5N1AR2MM4DC605884', sales_date = '2025-04-02', cost = 3333.33))
    # car_service.sell_car(Sale(sales_number = '3', car_vin = 'VF1LZL2T4BC242298', sales_date = '2025-04-03', cost = 14134))
    # car_service.sell_car(Sale(sales_number = '4', car_vin = 'KNAGR4A63D5359556', sales_date = '2025-04-04', cost = 2321))
    # car_service.sell_car(Sale(sales_number = '5', car_vin = 'KNAGH4A48A5414970', sales_date = '2025-04-05', cost = 3452))
    # car_service.sell_car(Sale(sales_number = '6', car_vin = '5XYPH4A10GG021831', sales_date = '2025-04-06', cost = 1111))
    # car_service.sell_car(Sale(sales_number = '7', car_vin = 'JM1BL1TFXD1734246', sales_date = '2025-04-07', cost = 2222))
    # car_service.sell_car(Sale(sales_number = '8', car_vin = '5N1CR2TS0HW037674', sales_date = '2025-04-08', cost = 3333))

    # s = car_service.get_car_info('KNAGM4A77D5316538')
    # print(s)

    # car_service.update_vin('ZNAGM4A77D5316538', 'KNAGM4A77D5316538')
    
    # car_service.revert_sale('1')
    print(car_service.top_models_by_sales())


if __name__ == '__main__':
    Main(f'd:\\DB')