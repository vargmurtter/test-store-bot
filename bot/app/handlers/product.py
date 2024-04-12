import config
import aiohttp

from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile
from aiogram.enums import ChatType
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from app.extras import helpers
from app.handlers import catalog, basket
from app.models import User, Product, Poster, Category
from app.keyboards import KeyboardCollection
from app.states import BotStates
from loaders import loc, bot


router = Router()
router.message.filter(F.from_user.id != F.bot.id)
router.message.filter(F.chat.type == ChatType.PRIVATE)
router.callback_query.filter(F.message.chat.type == ChatType.PRIVATE)


@router.callback_query(F.data.startswith("product:"), BotStates.Catalog.main)
async def handle_product_btn(
    callback: CallbackQuery, state: FSMContext, product_id: int | None = None
) -> None:
    storage_data = await state.get_data()
    if catalog_message_id := storage_data.get("catalog_message_id"):
        await helpers.try_delete_message(
            catalog_message_id, callback.message.chat.id
        )

    product_id = product_id if product_id else int(callback.data.split(":")[1])
    if (product := await Product.get(id=product_id)) is None:
        return

    category: Category = await product.category
    await helpers.try_delete_message(callback.message)
    await state.set_state(BotStates.Product.main)
    kbc = KeyboardCollection()

    await state.update_data(chosen_product_id=product.id)

    if product.poster is not None:
        poster: Poster = await product.poster
        image = await poster.get_image()

        if image:
            msg = await callback.message.answer_photo(
                photo=image,
                caption=loc.get_text(
                    "product/info",
                    product.title,
                    product.description,
                    category.title,
                ),
                reply_markup=kbc.product_keyboard(),
            )
            file_id = msg.photo[-1].file_id
            poster.tg_id = file_id
            await poster.save()
            return

    await callback.message.answer(
        loc.get_text(
            "product/info", product.title, product.description, category.title
        ),
        reply_markup=kbc.product_keyboard(),
    )


@router.callback_query(F.data == "product:to_basket", BotStates.Product.main)
async def handle_basket_btn(
    callback: CallbackQuery, state: FSMContext
) -> None:
    user = await User.filter(tg_id=callback.message.chat.id).first()
    if user is None:
        return

    storage_data = await state.get_data()
    if (product_id := storage_data.get("chosen_product_id")) is None:
        return
    if (product := await Product.get(id=product_id)) is None:
        return

    item = await product.add_one_to_basket(user.id)

    await helpers.try_delete_message(callback.message)
    await state.set_state(BotStates.Product.basket)

    kbc = KeyboardCollection()
    msg = await callback.message.answer(
        loc.get_text("product/add", product.title),
        reply_markup=kbc.add_basket_keyboard(item.count),
    )
    await state.update_data(basket_msg_id=msg.message_id)


@router.callback_query(
    F.data.in_({"product_basket:increase", "product_basket:decrease"}),
    BotStates.Product.basket,
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
        return await handle_product_btn(callback, state, product_id=product.id)

    kbc = KeyboardCollection()
    await bot.edit_message_reply_markup(
        chat_id=callback.message.chat.id,
        message_id=basket_msg_id,
        reply_markup=kbc.add_basket_keyboard(item.count),
    )


@router.callback_query(
    F.data == "product_basket:add",
    BotStates.Product.basket,
)
async def handle_add_button(
    callback: CallbackQuery, state: FSMContext
) -> None:
    await basket.start_basket(callback.message, state)


@router.callback_query(
    F.data == "return",
    StateFilter(BotStates.Product.main, BotStates.Product.basket),
)
async def handle_return(callback: CallbackQuery, state: FSMContext) -> None:
    current_state = await state.get_state()
    match current_state:
        case BotStates.Product.main.state:
            await catalog.start_catalog(callback, state)
