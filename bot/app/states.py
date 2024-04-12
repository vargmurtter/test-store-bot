from aiogram.fsm.state import State, StatesGroup


class BotStates(StatesGroup):
    check_sub = State()
    main_menu = State()

    class Catalog(StatesGroup):
        main = State()

    class Product(StatesGroup):
        main = State()
        basket = State()

    class Basket(StatesGroup):
        main = State()
        product = State()

        class Address(StatesGroup):
            main = State()
            city = State()
            street = State()
            building = State()

        checkout = State()
        success_payment = State()
