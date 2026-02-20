from pvp.routing import websocket_urlpatterns as pvp
from search_enemy.routing import websocket_urlpatterns as enemy
from trainings.routing import websocket_urlpatterns as trainings
from channels.routing import URLRouter

applications = URLRouter(pvp + enemy + trainings)
