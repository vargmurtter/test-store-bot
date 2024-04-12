import config

from aiogram import Router, F
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from aiogram.enums import ChatType
from aiogram.fsm.context import FSMContext

from app.states import BotStates


router = Router()
router.inline_query.filter(F.chat_type == ChatType.SENDER)


@router.inline_query(BotStates.main_menu)
async def handle_faq_query(
    inline_query: InlineQuery, state: FSMContext
) -> None:
    query = inline_query.query or ""
    questions = config.QUESTIONS
    articles = []
    for question in questions:
        if query in question["q"].lower() or query == "":
            articles.append(
                InlineQueryResultArticle(
                    id=question["q"],
                    title=question["q"],
                    input_message_content=InputTextMessageContent(
                        message_text=f"<b>{question['q']}</b>\n\n {question['a']}"
                    ),
                )
            )
    await inline_query.answer(
        articles, cache_time=60 * 5, is_personal=True, next_offset=""
    )
