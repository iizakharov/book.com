from mainapp.models import Bookings
import datetime
# import stripe

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect

from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, DetailView, DeleteView

import stripe

from ordersapp.models import Order

stripe.api_key = settings.STRIPE_SECRET_KEY


def checkout(request, hotel_id, room_id, check_in, check_out):
    booking = get_object_or_404(Bookings, hotel__pk=hotel_id, room__pk=room_id, date=check_in)
    start = datetime.datetime.strptime(check_in, "%Y-%m-%d")
    end = datetime.datetime.strptime(check_out, "%Y-%m-%d")
    date_list = [start + datetime.timedelta(days=x) for x in range(0, (end - start).days + 1)]
    total = sum([booking.room.price for x in range(len(date_list))])
    print(total)
    total = int(total) * 100

    # trying to find order

    order = Order.objects.get(booking__hotel=booking.hotel, booking__room=booking.room, days=len(date_list),
                         client_email=booking.client_email)

    if order.status == Order.PAID:
        # if it is already paid
        return HttpResponseRedirect(reverse('main:book_room',
                                            kwargs={
                                                'hotel_id': hotel_id,
                                                'room_id': room_id
                                            })
                                    )
    elif order.status == Order.FORMING:
        if request.method == 'POST':
            token = request.POST.get('stripeToken', False)
            print(token)
            if token:
                try:
                    stripe.Charge.create(
                        amount=total,
                        currency='rub',
                        description='Booking payment',
                        source=token,
                    )

                    order.status = Order.PAID
                    order.save()

                    return HttpResponseRedirect(reverse('main:book_room',
                                                        kwargs={
                                                            'hotel_id': hotel_id,
                                                            'room_id': room_id
                                                        })
                                                )
                except Exception as e:
                    print(e)
                    messages.error(request, "Your card has been declined.")

    return render(request, 'ordersapp/checkout.html', {'total': total / 100})


def main(request):
    user = request.user
    return render(request, 'ordersapp/base.html', {'user': user})


def success(request):
    user = request.user
    bookings = Bookings.objects.all()
    content = {
        'user': user,
        'bookings': bookings,
    }

    return render(request, 'ordersapp/success.html', content)


class OrderList(ListView):
    model = Order

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    @login_required(login_url='/auth/login/')
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class OrderRead(DetailView):
    model = Order

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'заказ/просмотр'
        return context


class OrderDelete(DeleteView):
    model = Order


def order_forming_complete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    order.status = Order.SENT_TO_PROCEED
    order.save()

    return HttpResponseRedirect(reverse('ordersapp:index'))
