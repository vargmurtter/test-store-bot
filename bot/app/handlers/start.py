from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ChatType
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from app.extras import helpers
from app.handlers import basket
from app.models import User
from app.keyboards import KeyboardCollection
from app.states import BotStates
from loaders import loc


router = Router()
router.message.filter(F.from_user.id != F.bot.id)
router.message.filter(F.chat.type == ChatType.PRIVATE)
router.callback_query.filter(F.message.chat.type == ChatType.PRIVATE)


@router.message(CommandStart())
async def start_cmd(message: Message, state: FSMContext) -> None:
    if (user := await User.filter(tg_id=message.from_user.id).first()) is None:
        user = await User.create(tg_id=message.from_user.id)

    kbc = KeyboardCollection()
    if not await user.is_channel_sub() or not await user.is_group_member():
        await state.set_state(BotStates.check_sub)
        await message.answer(
            loc.get_text("start/channel_group_needed"),
            reply_markup=kbc.follow_us_keyboard(),
        )
        return
    await main_menu(message, state)


@router.callback_query(F.data == "check_channel_sub", BotStates.check_sub)
async def handle_check_sub_button(
    callback: CallbackQuery, state: FSMContext
) -> None:
    user = await User.filter(tg_id=callback.from_user.id).first()
    if user is None:
        return

    is_channel_sub = await user.is_channel_sub()
    is_group_member = await user.is_group_member()

    if is_channel_sub and is_group_member:
        await callback.answer(loc.get_text("start/thanks"))
        await main_menu(callback.message, state)
        return

    if not is_channel_sub:
        await callback.answer(loc.get_text("start/channel_needed"))
    elif not is_group_member:
        await callback.answer(loc.get_text("start/group_needed"))


async def main_menu(message: Message, state: FSMContext) -> None:
    user = await User.filter(tg_id=message.chat.id).first()
    if user is None:
        return

    items = await user.get_basket()

    await helpers.try_delete_message(message)
    await state.set_state(BotStates.main_menu)

    kbc = KeyboardCollection()
    await message.answer(
        loc.get_text("start/welcome"),
        reply_markup=kbc.main_menu_keyboard(len(items)),
    )


@router.callback_query(F.data == "main:basket", BotStates.main_menu)
async def handle_basket_button(
    callback: CallbackQuery, state: FSMContext
) -> None:
    await basket.start_basket(callback.message, state)
