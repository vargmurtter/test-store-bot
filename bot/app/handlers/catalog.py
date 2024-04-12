from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.enums import ChatType
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from app.extras import helpers
from app.handlers import start
from app.models import User, Category
from app.keyboards import KeyboardCollection
from app.states import BotStates
from loaders import loc, bot


router = Router()
router.message.filter(F.from_user.id != F.bot.id)
router.message.filter(F.chat.type == ChatType.PRIVATE)
router.callback_query.filter(F.message.chat.type == ChatType.PRIVATE)


@router.callback_query(F.data == "main:catalog", BotStates.main_menu)
async def start_catalog(callback: CallbackQuery, state: FSMContext) -> None:
    children_cats = await Category.filter(parent=None).all()

    await state.set_state(BotStates.Catalog.main)
    await state.update_data(catalog_page=0)
    await helpers.try_delete_message(callback.message)

    kbc = KeyboardCollection()
    catalog_kb = await kbc.catalog_keyboard(None, children_cats, [], 0)
    message_obj = await callback.message.answer(
        loc.get_text("catalog/main"),
        reply_markup=catalog_kb,
    )
    await state.update_data(catalog_message_id=message_obj.message_id)


async def update_catalog_message(
    callback: CallbackQuery, state: FSMContext
) -> None:
    user = await User.filter(tg_id=callback.message.chat.id).first()
    if user is None:
        return

    storage_data = await state.get_data()
    if (catalog_message_id := storage_data.get("catalog_message_id")) is None:
        return
    if (catalog_page := storage_data.get("catalog_page")) is None:
        catalog_page = 0
    category_id = storage_data.get("category_id")

    current_category = (
        await Category.filter(id=int(category_id)).first()
        if category_id.isdigit()
        else None
    )

    children_cats = await Category.filter(parent=current_category).all()

    if current_category:
        cat_products = await current_category.get_all_products()
        tree = await current_category.get_back_tree()
        tree_text = loc.get_text("catalog/back_tree", tree)
    else:
        cat_products = []
        tree_text = loc.get_text("catalog/main")

    kbc = KeyboardCollection()
    catalog_kb = await kbc.catalog_keyboard(
        current_category, children_cats, cat_products, catalog_page
    )

    await bot.edit_message_text(
        text=tree_text,
        chat_id=user.tg_id,
        message_id=catalog_message_id,
        reply_markup=catalog_kb,
    )


@router.callback_query(
    F.data.startswith("catalog:cat_id:"), BotStates.Catalog.main
)
async def handle_category_change(
    callback: CallbackQuery, state: FSMContext
) -> None:
    category_id = callback.data.split(":")[2]
    await state.update_data(catalog_page=0)
    await state.update_data(category_id=category_id)
    await update_catalog_message(callback, state)


@router.callback_query(
    F.data.startswith("catalog:page:"), BotStates.Catalog.main
)
async def handle_page_change(
    callback: CallbackQuery, state: FSMContext
) -> None:
    page = callback.data.split(":")[2]
    await state.update_data(catalog_page=int(page))
    await update_catalog_message(callback, state)


@router.callback_query(F.data == "return", StateFilter(BotStates.Catalog.main))
async def handle_return(callback: CallbackQuery, state: FSMContext) -> None:
    current_state = await state.get_state()
    match current_state:
        case BotStates.Catalog.main.state:
            await start.main_menu(callback.message, state)
