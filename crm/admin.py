from django.contrib import admin
from crm import models
# Register your models here.

@admin.register(models.ConsultRecord)
class ConsultrecordAdmin(admin.ModelAdmin):
    pass