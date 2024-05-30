# -*- encoding: utf-8 -*-
from flask import render_template
from app.core.main.BasePlugin import BasePlugin
from app.core.main.ObjectsStorage import objects
from app.authentication.handlers import handle_user_required

class Dashboard(BasePlugin):

    def __init__(self,app):
        super().__init__(app,__name__)
        self.title = "Dashboard"
        self.description = """Simple dashboard"""
        self.version = 0.1
    
    def initialization(self):
        pass

    def admin(self, request):
        return render_template("dashboard.html")

    def route_index(self):
        @self.blueprint.route("/index")
        @handle_user_required
        def index():
            templates = {}
            for key,obj in objects.items():
                if not obj.template: continue
                render = obj.render()
                templates[key]=render
            content = {
                'objects': templates,
            }
            return self.render("index.html", content)