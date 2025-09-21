from django.contrib import admin

from flight.models import (
    Flight,
    Route,
    Airplane,
    Crew,
    Airport,
    AirplaneType,
    Ticket,
    Order
)


class TicketInLine(admin.TabularInline):
    model = Ticket
    extra = 1

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = (TicketInLine,)

admin.site.register(Flight)
admin.site.register(Route)
admin.site.register(Airplane)
admin.site.register(Crew)
admin.site.register(Airport)
admin.site.register(AirplaneType)
admin.site.register(Ticket)
