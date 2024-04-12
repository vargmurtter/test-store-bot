from django.db import models


class User(models.Model):
    tg_id = models.BigIntegerField()
    
    def __str__(self) -> str:
        return str(self.tg_id)
    
    class Meta:
        db_table = "bot_users"
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Category(models.Model):
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title
    
    class Meta:
        db_table = "categories"
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class Poster(models.Model):
    path = models.ImageField(upload_to="content/", null=True)
    tg_id = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "posters"
        verbose_name = 'Постер'
        verbose_name_plural = 'Постеры'


class Product(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    poster = models.OneToOneField(Poster, on_delete=models.SET_NULL, related_name='products', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, related_name='products', null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, null=False)
    
    def __str__(self) -> str:
        return self.title

    class Meta:
        db_table = "products"
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'


class Basket(models.Model):
    user_id = models.BigIntegerField(null=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='items', null=False)
    count = models.IntegerField(null=False)
    
    class Meta:
        db_table = "basket"