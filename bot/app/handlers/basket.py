import config

from aiogram import Bot, Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    LabeledPrice,
    PreCheckoutQuery,
)
from aiogram.enums import ChatType, ContentType
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from app.extras import helpers
from app.handlers import start, catalog
from app.models import User, Product, Basket
from app.keyboards import KeyboardCollection
from app.states import BotStates
from loaders import loc, bot


router = Router()
router.message.filter(F.from_user.id != F.bot.id)
router.message.filter(F.chat.type == ChatType.PRIVATE)
router.callback_query.filter(F.message.chat.type == ChatType.PRIVATE)


async def start_basket(message: Message, state: FSMContext) -> None:
    user = await User.filter(tg_id=message.chat.id).first()
    if user is None:
        return
    items = await user.get_basket()

    await state.set_state(BotStates.Basket.main)
    await helpers.try_delete_message(message)

    kbc = KeyboardCollection()
    if len(items) < 1:
        await message.answer(
            loc.get_text("basket/empty"),
            reply_markup=kbc.empty_basket_keyboard(),
        )
        return

    total_price = 0
    total_count = 0
    for item in items:
        product: Product = await item.product
        total_count += item.count
        total_price += item.count * product.price

    basket_kb = await kbc.basket_keyboard(items)
    await message.answer(
        loc.get_text("basket/main", total_count, total_price),
        reply_markup=basket_kb,
    )


@router.callback_query(
    F.data == "basket:go_catalog",
    BotStates.Basket.main,
)
async def handle_go_catalog_button(
    callback: CallbackQuery, state: FSMContext
) -> None:
    await catalog.start_catalog(callback, state)


# =======


@router.callback_query(
    F.data.startswith("basket_item:"), BotStates.Basket.main
)
async def handle_basket_btn(
    callback: CallbackQuery, state: FSMContext
) -> None:
    user = await User.filter(tg_id=callback.message.chat.id).first()
    if user is None:
        return

    item_id = int(callback.data.split(":")[1])
    item = await Basket.filter(id=item_id).first()
    product: Product = await item.product

    await helpers.try_delete_message(callback.message)
    await state.set_state(BotStates.Basket.product)
    await state.update_data(basket_item_id=item_id)

    kbc = KeyboardCollection()
    msg = await callback.message.answer(
        loc.get_text("basket/product_title", product.title),
        reply_markup=kbc.basket_product_keyboard(item.count),
    )
    await state.update_data(basket_msg_id=msg.message_id)


@router.callback_query(
    F.data.in_({"basket_product:increase", "basket_product:decrease"}),
    BotStates.Basket.product,
)
async def handle_count_buttons(
    callback: CallbackQuery, state: FSMContext
) -> None:
    user = await User.filter(tg_id=callback.message.chat.id).first()
    if user is None:
        return
    storage_data = await state.get_data()
    if (product_id := storage_data.get("chosen_product_id")) is None:
        return
    if (basket_msg_id := storage_data.get("basket_msg_id")) is None:
        return
    if (product := await Product.get(id=product_id)) is None:
        return

    action = callback.data.split(":")[1]
    if action == "increase":
        item = await product.add_one_to_basket(user.id)
    elif action == "decrease":
        item = await product.remove_one_from_basket(user.id)
    else:
        return

    if item is None:
        return await start_basket(callback.message, state)

    kbc = KeyboardCollection()
    await bot.edit_message_reply_markup(
        chat_id=callback.message.chat.id,
        message_id=basket_msg_id,
        reply_markup=kbc.basket_product_keyboard(item.count),
    )


@router.callback_query(
    F.data == "basket_product:save",
    BotStates.Basket.product,
)
async def handle_save_button(
    callback: CallbackQuery, state: FSMContext
) -> None:
    await start_basket(callback.message, state)


@router.callback_query(
    F.data == "basket_product:delete",
    BotStates.Basket.product,
)
async def handle_delete_button(
    callback: CallbackQuery, state: FSMContext
) -> None:
    storage_data = await state.get_data()
    if (item_id := storage_data.get("basket_item_id")) is None:
        return
    if (item := await Basket.get(id=item_id)) is None:
        return
    await item.delete()
    await start_basket(callback.message, state)


# =======


@router.callback_query(F.data == "basket:checkout", BotStates.Basket.main)
async def handle_checkout_button(
    callback: CallbackQuery, state: FSMContext
) -> None:
    await helpers.try_delete_message(callback.message)
    await state.set_state(BotStates.Basket.Address.main)

    kbc = KeyboardCollection()
    storage_data = await state.get_data()
    if delivery_address := storage_data.get("delivery_address"):
        await callback.message.answer(
            loc.get_text("basket/address/is_yours", delivery_address),
            reply_markup=kbc.choose_address_keyboard(),
        )
        return

    await state.set_state(BotStates.Basket.Address.city)
    await callback.message.answer(loc.get_text("basket/address/enter_city"))


@router.callback_query(
    F.data.in_({"basket_address:old", "basket_address:new"}),
    BotStates.Basket.Address.main,
)
async def handle_address_button(
    callback: CallbackQuery, state: FSMContext
) -> None:
    action = callback.data.split(":")[1]
    if action == "old":
        await checkout(callback.message, state)
    elif action == "new":
        await helpers.try_delete_message(callback.message)
        await state.set_state(BotStates.Basket.Address.city)
        await callback.message.answer(
            loc.get_text("basket/address/enter_city")
        )
    else:
        return


@router.message(
    F.text,
    StateFilter(
        BotStates.Basket.Address.main,
        BotStates.Basket.Address.city,
        BotStates.Basket.Address.street,
        BotStates.Basket.Address.building,
    ),
)
async def handle_address_input(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    match current_state:
        case BotStates.Basket.Address.city:
            await state.update_data(address_city=message.text)
            await state.set_state(BotStates.Basket.Address.street)
            await message.answer(loc.get_text("basket/address/enter_street"))
        case BotStates.Basket.Address.street:
            await state.update_data(address_street=message.text)
            await state.set_state(BotStates.Basket.Address.building)
            await message.answer(loc.get_text("basket/address/enter_building"))
        case BotStates.Basket.Address.building:
            storage_data = await state.get_data()
            if (address_city := storage_data.get("address_city")) is None:
                return
            if (address_street := storage_data.get("address_street")) is None:
                return
            delivery_address = (
                f"{address_city}, {address_street}, {message.text}"
            )
            await state.update_data(delivery_address=delivery_address)
            await checkout(message, state)
        case _:
            return


async def checkout(message: Message, state: FSMContext) -> None:
    user = await User.filter(tg_id=message.chat.id).first()
    if user is None:
        return
    items = await user.get_basket()

    await helpers.try_delete_message(message)
    await state.set_state(BotStates.Basket.checkout)

    order_price = 0
    labeled_prices = []
    for item in items:
        product: Product = await item.product
        item_price = product.price * item.count
        order_price += item_price
        labeled_prices.append(
            LabeledPrice(
                label=f"{product.title} x{item.count}", amount=item_price * 100
            )
        )

    kbc = KeyboardCollection()
    invoice_msg = await message.answer_invoice(
        title=loc.get_text("basket/checkout/title"),
        description=loc.get_text("basket/checkout/description", order_price),
        provider_token=config.UKASSA_TOKEN,
        currency="rub",
        prices=labeled_prices,
        protect_content=True,
        payload="pay",
        reply_markup=kbc.checkout_keyboard(),
    )
    await state.update_data(invoice_msg_id=invoice_msg.message_id)


@router.pre_checkout_query()
async def pre_checkout_query(
    pre_checkout_query: PreCheckoutQuery, bot: Bot
) -> None:
    await bot.answer_pre_checkout_query(
        pre_checkout_query_id=pre_checkout_query.id, ok=True
    )


@router.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def payment_success_callback(
    message: Message, state: FSMContext
) -> None:
    storage_data = await state.get_data()
    if invoice_msg_id := storage_data.get("invoice_msg_id"):
        helpers.try_delete_message(invoice_msg_id, message.chat.id)
    if (address := storage_data.get("delivery_address")) is None:
        return
    user = await User.filter(tg_id=message.chat.id).first()
    if user is None:
        return

    await state.set_state(BotStates.Basket.success_payment)

    await user.add_basket_to_xl(address)
    await user.clear_basket()

    kbc = KeyboardCollection()
    await message.answer(
        loc.get_text("basket/checkout/thanks"),
        reply_markup=kbc.return_keyboard(),
    )


@router.callback_query(
    F.data == "return",
    StateFilter(
        BotStates.Basket.main,
        BotStates.Basket.checkout,
        BotStates.Basket.success_payment,
    ),
)
async def handle_return(callback: CallbackQuery, state: FSMContext) -> None:
    current_state = await state.get_state()
    match current_state:
        case (
            BotStates.Basket.main.state
            | BotStates.Basket.success_payment.state
        ):
            await start.main_menu(callback.message, state)
        case BotStates.Basket.checkout.state:
            await start_basket(callback.message, state)
