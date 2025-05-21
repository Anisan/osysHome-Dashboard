# -*- encoding: utf-8 -*-
from flask import redirect
from app.core.main.BasePlugin import BasePlugin
from app.core.main.ObjectsStorage import objects_storage
from app.database import row2dict
from app.core.models.Clasess import Class
from app.authentication.handlers import handle_user_required
from plugins.Dashboard.forms.SettingForms import SettingsForm

class Dashboard(BasePlugin):

    def __init__(self,app):
        super().__init__(app,__name__)
        self.title = "Dashboard"
        self.description = """Simple dashboard"""
        self.version = 0.3
        self.category = "App"
        self.author = "Eraser"

    def initialization(self):
        pass

    def admin(self, request):
        
        settings = SettingsForm()
        if request.method == 'GET':
            settings.group.data = self.config.get('group',False)
        else:
            if settings.validate_on_submit():
                self.config["group"] = settings.group.data
                self.saveConfig()
                return redirect("Dashboard")

        content = {
            "form": settings,
        }
        return self.render("dashboard.html",content)

    def route_index(self):
        @self.blueprint.route("/index")
        @handle_user_required
        def index():
            objects_storage.preload_objects()

            if self.config.get('group',False):
                groups = {}
                classes = {}
                res = Class.query.all()
                for item in res:
                    classes[item.name] = row2dict(item)
            
                for key, obj in sorted(objects_storage.items(), key=lambda x: x[0].lower()):
                    render = obj.render()
                    if render:
                        if obj.parents:
                            parent = obj.parents[0]
                            if parent not in groups:
                                groups[parent] = {"objects":{}}
                            groups[parent]["class"] = classes[parent]
                            groups[parent]["objects"][key] = render
                        else:
                            if 'root' not in groups:
                                groups['root'] = {"objects":{}}
                                groups['root']["objects"][key] = render
                content = {
                    'groups': groups,
                }
                return self.render("index_group.html", content)
            
            templates = {}
            for key, obj in sorted(objects_storage.items(), key=lambda x: x[0].lower()):
                render = obj.render()
                if render:
                    templates[key] = render
            content = {
                'objects': templates,
            }
            return self.render("index.html", content)
