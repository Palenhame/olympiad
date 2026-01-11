from django.shortcuts import render


# Create your views here.
def pvp(request, room_id):
    request.session.setdefault("pvp_init", True)
    request.session.save()
    return render(request, 'pvp.html', {'room_id': room_id})
