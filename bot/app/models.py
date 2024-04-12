from __future__ import annotations

import aiohttp
import uuid
import config
from datetime import datetime, date
from tortoise.models import Model
from tortoise import fields
from aiogram.types import BufferedInputFile
from app import utils
from app.extras import helpers
from app.enums import OrdersXlsxSheet
from loaders import bot


class User(Model):
    id = fields.BigIntField(pk=True)
    tg_id = fields.BigIntField()

    async def is_channel_sub(self) -> bool:
        channel_member = await bot.get_chat_member(
            config.CHANNEL_ID, self.tg_id
        )
        return channel_member.status != "left"

    async def is_group_member(self) -> bool:
        group_member = await bot.get_chat_member(config.GROUP_ID, self.tg_id)
        return group_member.status != "left"

    async def get_basket(self) -> list[Basket]:
        return await Basket.filter(user_id=self.id).all()

    async def clear_basket(self) -> None:
        await Basket.filter(user_id=self.id).delete()

    async def add_basket_to_xl(self, address: str) -> None:
        # генерирую id заказа тут, потому что никуда его не записываю
        order_id = str(uuid.uuid4())
        order_date = datetime.now()
        order_amount = 0

        data = []
        items = await self.get_basket()
        for item in items:
            product: Product = await item.product
            amount = product.price * item.count
            order_amount += amount
            data.append(
                [
                    self.id,
                    self.tg_id,
                    order_id,
                    product.id,
                    product.title,
                    product.price,
                    item.count,
                    amount,
                    order_date,
                ]
            )
        await helpers.sync_to_async(
            utils.add_to_xls, OrdersXlsxSheet.DETAILS, data
        )

        data = []
        data.append(
            [self.id, self.tg_id, order_id, order_amount, address, order_date]
        )
        await helpers.sync_to_async(
            utils.add_to_xls, OrdersXlsxSheet.ORDERS, data
        )

    class Meta:
        table = "bot_users"


class Category(Model):
    id = fields.BigIntField(pk=True)
    parent = fields.ForeignKeyField(
        "models.Category",
        on_delete=fields.CASCADE,
        null=True,
        related_name="children",
    )
    title = fields.CharField(max_length=255)

    async def get_all_products(self) -> list[Product]:
        category_ids = [self.id]
        children = await Category.filter(parent_id=self.id).all()
        while children:
            child_ids = [child.id for child in children]
            category_ids.extend(child_ids)
            # TODO: оптимизировать
            children = await Category.filter(parent_id__in=child_ids).all()
        return await Product.filter(category_id__in=category_ids).all()

    async def get_back_tree(self) -> str:
        category_tree = [self.title]
        parent_category = await self.parent
        while parent_category:
            category_tree.insert(0, parent_category.title)
            parent_category = await parent_category.parent
        return " -> ".join(category_tree)

    class Meta:
        table = "categories"


class Poster(Model):
    id = fields.BigIntField(pk=True)
    path = fields.CharField(max_length=255, null=False)
    tg_id = fields.CharField(max_length=255, null=True)

    async def get_image(self) -> str | BufferedInputFile | None:
        image = self.tg_id
        if not image:
            async with aiohttp.ClientSession() as session:
                url = f"{config.ADMIN_IMAGES_URL}/{self.path}"
                async with session.get(url) as resp:
                    if resp.status == 200:
                        image = BufferedInputFile(
                            await resp.read(), filename="poster"
                        )
                    else:
                        image = None
        return image

    class Meta:
        table = "posters"


class Product(Model):
    id = fields.BigIntField(pk=True)
    title = fields.CharField(max_length=255)
    description = fields.TextField()
    poster = fields.OneToOneField(
        "models.Poster",
        on_delete=fields.SET_NULL,
        related_name="products",
        null=True,
    )
    category = fields.ForeignKeyField(
        "models.Category",
        on_delete=fields.SET_NULL,
        related_name="products",
        null=True,
    )
    created_at = fields.DatetimeField(auto_now_add=True)
    price = fields.DecimalField(max_digits=12, decimal_places=2, null=False)

    async def add_one_to_basket(self, user_id: int) -> Basket:
        item = await Basket.filter(user_id=user_id, product_id=self.id).first()
        if item is None:
            item = await Basket.create(
                user_id=user_id, product_id=self.id, count=1
            )
            return item
        item.count += 1
        await item.save()
        return item

    async def remove_one_from_basket(self, user_id: int) -> Basket | None:
        item = await Basket.filter(user_id=user_id, product_id=self.id).first()
        if item is None:
            return None
        if item.count <= 1:
            await item.delete()
            return None
        item.count -= 1
        await item.save()
        return item

    class Meta:
        table = "products"


class Basket(Model):
    id = fields.BigIntField(pk=True)
    user_id = fields.BigIntField(null=False)
    product = fields.ForeignKeyField(
        "models.Product",
        on_delete=fields.CASCADE,
        related_name="items",
        null=False,
    )
    count = fields.IntField(null=False)

    class Meta:
        table = "basket"
