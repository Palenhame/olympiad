from pvp.routing import websocket_urlpatterns as pvp
from search_enemy.routing import websocket_urlpatterns as enemy
from channels.routing import URLRouter

applications = URLRouter(pvp + enemy)
