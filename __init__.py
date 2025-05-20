# -*- encoding: utf-8 -*-
from flask import render_template
from app.core.main.BasePlugin import BasePlugin
from app.core.main.ObjectsStorage import objects_storage
from app.authentication.handlers import handle_user_required

class Dashboard(BasePlugin):

    def __init__(self,app):
        super().__init__(app,__name__)
        self.title = "Dashboard"
        self.description = """Simple dashboard"""
        self.version = 0.2
        self.category = "App"
        self.author = "Eraser"

    def initialization(self):
        pass

    def admin(self, request):
        return render_template("dashboard.html")

    def route_index(self):
        @self.blueprint.route("/index")
        @handle_user_required
        def index():
            templates = {}
            objects_storage.preload_objects()

            for key, obj in sorted(objects_storage.items(), key=lambda x: x[0].lower()):
                render = obj.render()
                if render:
                    templates[key] = render
            content = {
                'objects': templates,
            }
            return self.render("index.html", content)
