import os

from sanic import Sanic
from sanic.response import file, json

from app.factory.boot import startup, shutdown
from app.urls.healthz import health_bp
from app.fdk import get_extension_client 
from app.config import CONFIG

from fdk_extension.middleware.session_middleware import session_middleware
from fdk_extension.middleware.api_middleware import platform_api_on_request

from fdk_extension.extension import FdkExtensionClient

def create_app() -> Sanic:
    fdk_extension_client: FdkExtensionClient = get_extension_client()

    # Sanic Application
    app = Sanic(__name__)

    # health apis
    app.blueprint(health_bp)

    # Add your Routes here
    app.blueprint(fdk_extension_client.fdk_route)

    from app.urls.application import app_bp
    # Add your Middlewares here
    app_bp.middleware(session_middleware, "request")
    app_bp.middleware(platform_api_on_request, "request")

    # Register your routes here
    app.blueprint(app_bp)


    # # Redirect routes
    # REDIRECTS = {
    #     '/': '/index.html',
    # }
    # def get_static_func(value: object):
    #     return lambda *_, **__: value
    
    # for src, dest in REDIRECTS.items():
    #     response = sanic.response.redirect(dest)
    #     handler = get_static_func(response)
    #     app.route(src)(handler)
    

    # Configure Static Files
    DIST_DIR = os.path.join(CONFIG.ROOT_DIR, "dist")
    if not os.path.exists(DIST_DIR):
        raise Exception(f"DIST_DIR not found: {DIST_DIR}, Build FrondEnd before running server!")
    app.static('/', DIST_DIR)


    # Home Page
    @app.get("/company/<company_id>")
    async def home_page_handler(request, company_id):
        return await file(os.path.join(DIST_DIR, "index.html"), headers={"Content-Type": "text/html"})


    # handle webhook
    @app.post("api/v1.0/webhooks")
    async def handle_webbhook(request):
        try: 
            res = await fdk_extension_client.webhook_registry.process_webhook(request)
            print(res)
            return json({"msg": "success"}, status=200)
        except Exception as e:
            return json({"msg": f"err: {str(e)}"}, status=400)
    

    # Boot 
    app.register_listener(startup, "after_server_start")
    app.register_listener(shutdown, "before_server_stop")

    return app