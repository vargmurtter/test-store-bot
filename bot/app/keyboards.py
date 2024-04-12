import config
import math
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from app.models import Category, Product, Basket
from loaders import loc


class KeyboardCollection:
    def __init__(self, lang: str = "RU") -> None:
        loc.set_language(lang)
        self._language = lang

    def return_button(self) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text=loc.get_text("button/RETURN", self._language),
            callback_data="return",
        )

    def return_button_row(self) -> list[list[InlineKeyboardButton]]:
        return [
            [
                InlineKeyboardButton(
                    text=loc.get_text("button/RETURN", self._language),
                    callback_data="return",
                )
            ]
        ]

    def return_keyboard(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.add(self.return_button())
        builder.adjust(1)
        return builder.as_markup()

    def follow_us_keyboard(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(
            text=loc.get_text("button/CHANNEL"), url=config.CHANNEL_URL
        )
        builder.button(text=loc.get_text("button/GROUP"), url=config.GROUP_URL)
        builder.button(
            text=loc.get_text("button/CHECK_SUBS"),
            callback_data="check_channel_sub",
        )
        builder.adjust(1)
        return builder.as_markup()

    def main_menu_keyboard(
        self, basket_products_count: int
    ) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(
            text=loc.get_text("button/CATALOG"), callback_data="main:catalog"
        )
        builder.button(
            text=loc.get_text("button/BASKET", basket_products_count),
            callback_data="main:basket",
        )
        builder.button(
            text=loc.get_text("button/FAQ"),
            switch_inline_query_current_chat="",
        )
        builder.adjust(1)
        return builder.as_markup()

    async def catalog_keyboard(
        self,
        current_category: Category,
        category_children: list[Category],
        products: list[Product],
        page: int = 0,
    ) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for cat in category_children:
            builder.button(
                text=f"📘 {loc.get_text(cat.title)}",
                callback_data=f"catalog:cat_id:{cat.id}",
            )

        pages_count = 1
        if current_category:
            builder.button(
                text=loc.get_text(
                    "button/CATEGORY_PLACEHOLDER", current_category.title
                ),
                callback_data="-",
            )

            per_page = 5
            pages_count = math.ceil(len(products) / per_page)
            start_index = page * per_page
            finish_index = start_index + per_page
            products = products[start_index:finish_index]
            for product in products:
                builder.button(
                    text=f"🎮 {loc.get_text(product.title)}",
                    callback_data=f"product:{product.id}",
                )
            if pages_count > 1:
                for page_num in range(pages_count):
                    builder.button(
                        text=(
                            f"[ {page_num + 1} ]"
                            if page_num == page
                            else str(page_num + 1)
                        ),
                        callback_data=f"catalog:page:{page_num}",
                    )
            builder.button(
                text=loc.get_text("button/RETURN"),
                callback_data=f"catalog:cat_id:{current_category.parent_id}",
            )
        builder.button(
            text=loc.get_text("button/GO_HOME"),
            callback_data="return",
        )

        adjust = [1 for _ in range(len(category_children) + 1 + len(products))]
        builder.adjust(*adjust, pages_count if pages_count > 1 else 1, 1)

        return builder.as_markup()

    def product_keyboard(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(
            text=loc.get_text("button/ADD_BASKET"),
            callback_data="product:to_basket",
        )
        builder.button(
            text=loc.get_text("button/GOBACK_CATALOG"),
            callback_data="return",
        )
        builder.adjust(1)
        return builder.as_markup()

    def add_basket_keyboard(self, count: int) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(
            text=loc.get_text("button/BASKET_DECREASE"),
            callback_data="product_basket:decrease",
        )
        builder.button(
            text=str(count),
            callback_data="-",
        )
        builder.button(
            text=loc.get_text("button/BASKET_INCREASE"),
            callback_data="product_basket:increase",
        )
        builder.button(
            text=loc.get_text("button/ADD"),
            callback_data="product_basket:add",
        )
        builder.adjust(3, 1)
        return builder.as_markup()

    async def basket_keyboard(
        self, items: list[Basket]
    ) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for item in items:
            product: Product = await item.product
            builder.button(
                text=f"{product.title} ({item.count})",
                callback_data=f"basket_item:{item.id}",
            )
        builder.button(
            text=loc.get_text("button/CHECKOUT"),
            callback_data="basket:checkout",
        )
        builder.add(self.return_button())
        builder.adjust(1)
        return builder.as_markup()

    def checkout_keyboard(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text=loc.get_text("button/PAY"), pay=True)
        builder.add(self.return_button())
        builder.adjust(1)
        return builder.as_markup()

    def empty_basket_keyboard(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(
            text=loc.get_text("button/GO_CATALOG"),
            callback_data="basket:go_catalog",
        )
        builder.add(self.return_button())
        builder.adjust(1)
        return builder.as_markup()

    def basket_product_keyboard(self, count: int) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(
            text=loc.get_text("button/BASKET_DECREASE"),
            callback_data="basket_product:decrease",
        )
        builder.button(
            text=str(count),
            callback_data="-",
        )
        builder.button(
            text=loc.get_text("button/BASKET_INCREASE"),
            callback_data="basket_product:increase",
        )

        builder.button(
            text=loc.get_text("button/SAVE"),
            callback_data="basket_product:save",
        )
        builder.button(
            text=loc.get_text("button/DELETE"),
            callback_data="basket_product:delete",
        )
        builder.adjust(3, 1)
        return builder.as_markup()

    def choose_address_keyboard(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(
            text=loc.get_text("button/DELIVERY_OLD"),
            callback_data="basket_address:old",
        )
        builder.button(
            text=loc.get_text("button/DELIVERY_NEW"),
            callback_data="basket_address:new",
        )

        builder.adjust(1)
        return builder.as_markup()
