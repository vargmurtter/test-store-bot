import telebot
from telebot.apihelper import ApiTelegramException
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.urls import path
from django.template.response import TemplateResponse
from django.utils.html import format_html
from .models import User, Product, Category, Poster
from django.contrib.auth.models import User as DjangoUser, Group
from store.settings import BOT_TOKEN


class PosterAdmin(admin.ModelAdmin):
    list_display = ('preview', 'tg_id')
    readonly_fields = ('preview_big', 'tg_id')
    
    def preview(self, obj):
        if obj and obj.path:
            return mark_safe(f'<img src="{obj.path.url}" height="100" />')
        return '-'
    preview.short_description = 'Изображение'
    
    def preview_big(self, obj):
        if obj and obj.path:
            return mark_safe(f'<img src="{obj.path.url}" height="300" />')
        return '-'
    preview_big.short_description = 'Изображение'


class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'poster', 'poster_preview', 'category')
    list_editable = ('category', 'poster')
    readonly_fields = ('poster_preview',)
    
    def poster_preview(self, obj):
        if obj.poster and obj.poster.path:
            return mark_safe(f'<img src="{obj.poster.path.url}" height="100" />')
        return '-'
    poster_preview.short_description = 'Постер'
    

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'parent')


class UserAdmin(admin.ModelAdmin):
    change_list_template = "admin/main/user_change_list.html"
    
    bot = telebot.TeleBot(BOT_TOKEN)
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('mailing/', self.admin_site.admin_view(self.mass_mailing), name='mass_mailing'),
        ]
        return custom_urls + urls

    def mass_mailing(self, request):
        context = dict(
           self.admin_site.each_context(request),
           title='Массовая рассылка',
        )
        success_sent = 0
        if request.method == 'POST':
            message = request.POST.get('message')
            user_ids = [user.tg_id for user in User.objects.all()]
            for tg_id in user_ids:
                try:
                    self.bot.send_message(
                        chat_id=tg_id, text=message
                    )
                    success_sent += 1
                except ApiTelegramException: ...
            context['success'] = f"Сообщение успешно отправлено {success_sent} пользователям!"
        return TemplateResponse(request, "admin/main/mass_mailing.html", context)


admin.site.register(User, UserAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Poster, PosterAdmin)

admin.site.unregister(DjangoUser)
admin.site.unregister(Group)