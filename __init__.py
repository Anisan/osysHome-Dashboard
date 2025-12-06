# -*- encoding: utf-8 -*-
from flask import redirect, jsonify, request as flask_request
from flask_login import current_user
from app.core.main.BasePlugin import BasePlugin
from app.core.main.ObjectsStorage import objects_storage
from app.database import row2dict
from app.core.models.Clasess import Class
from app.authentication.handlers import handle_user_required
from app.core.lib.object import getObject, getProperty, setProperty
from plugins.Dashboard.forms.SettingForms import SettingsForm
import json

# Translations будут применяться в шаблонах

class Dashboard(BasePlugin):

    def __init__(self,app):
        super().__init__(app,__name__)
        self.title = "Dashboard"
        self.description = """Simple dashboard"""
        self.version = 1.0
        self.category = "App"
        self.author = "Eraser"

    def initialization(self):
        pass

    def admin(self, request):

        # Создаем форму один раз для обоих случаев (GET и POST)
        settings = SettingsForm(request.form if request.method == 'POST' else None)
        
        if request.method == 'GET':
            settings.group.data = self.config.get('group',False)
            settings.hide_welcome.data = self.config.get('hide_welcome', False)
            settings.hide_no_grouping.data = self.config.get('hide_no_grouping', False)
            # Загружаем группы из конфигурации
            custom_groups = self.config.get('custom_groups', [])
            # Заполняем форму группами
            # Очищаем существующие записи через pop_entry
            while len(settings.groups.entries) > 0:
                settings.groups.pop_entry()
            # Добавляем новые записи
            for group in custom_groups:
                group_form = settings.groups.append_entry()
                if group_form:
                    group_form.group_name.data = group.get('name', '')
                    group_form.group_icon.data = group.get('icon', '')
                    group_form.property_name.data = group.get('property_name', '')
                    group_form.object_property.data = group.get('object_property', '')
                    group_form.show_undefined.data = group.get('show_undefined', False)
                    group_form.value_substitutions.data = group.get('value_substitutions', '')
        else:
            # При POST запросе обрабатываем данные формы
            # Логируем полученные данные для отладки
            self.logger.debug("POST data: %s", dict(request.form))
            
            if settings.validate_on_submit():
                self.config["group"] = settings.group.data
                self.config["hide_welcome"] = settings.hide_welcome.data
                self.config["hide_no_grouping"] = settings.hide_no_grouping.data
                # Сохраняем группы
                custom_groups = []
                self.logger.debug("Processing %d group entries", len(settings.groups.entries))
                for idx, group_form in enumerate(settings.groups.entries):
                    # Проверяем, что группа имеет имя (не пустая)
                    group_name = group_form.group_name.data
                    self.logger.debug("Group %d: name='%s', property_name='%s', show_undefined=%s", 
                                    idx, group_name, group_form.property_name.data, group_form.show_undefined.data)
                    if group_name and group_name.strip():
                        custom_groups.append({
                            'id': str(len(custom_groups)),
                            'name': group_name.strip(),
                            'icon': (group_form.group_icon.data or '').strip(),
                            'property_name': (group_form.property_name.data or '').strip(),
                            'object_property': (group_form.object_property.data or '').strip(),
                            'show_undefined': bool(group_form.show_undefined.data),
                            'value_substitutions': (group_form.value_substitutions.data or '').strip()
                        })
                
                self.config["custom_groups"] = custom_groups
                self.saveConfig()
                self.logger.info("Saved %d custom groups: %s", len(custom_groups), [g['name'] for g in custom_groups])
                return redirect("Dashboard")
            else:
                # Если форма не валидна, показываем ошибки
                self.logger.warning("Form validation failed: %s", settings.errors)
                # Передаем ошибки в шаблон для отображения
                for field, errors in settings.errors.items():
                    self.logger.warning("Field %s errors: %s", field, errors)
                # При ошибке валидации все равно нужно заполнить форму группами для отображения
                settings.group.data = self.config.get('group',False)

        content = {
            "form": settings,
        }
        return self.render("dashboard.html",content)

    def _parse_substitutions(self, substitutions_str):
        """Парсит строку подстановок в формате "0-Online,1-Offline" в словарь"""
        if not substitutions_str or not substitutions_str.strip():
            return {}
        
        result = {}
        try:
            parts = substitutions_str.strip().split(',')
            for part in parts:
                part = part.strip()
                if '-' in part:
                    key, value = part.split('-', 1)
                    result[key.strip()] = value.strip()
        except Exception as e:
            self.logger.warning(f"Error parsing substitutions '{substitutions_str}': {e}")
        
        return result
    
    def _get_group_title(self, group_value, group_config):
        """Получить заголовок группы с учетом подстановок"""
        if group_value is None:
            return None
        
        substitutions_str = group_config.get('value_substitutions', '').strip()
        if substitutions_str:
            substitutions = self._parse_substitutions(substitutions_str)
            # Пробуем найти подстановку для значения
            value_str = str(group_value)
            if value_str in substitutions:
                return substitutions[value_str]
            # Также пробуем числовое значение
            try:
                if isinstance(group_value, (int, float)):
                    if str(int(group_value)) in substitutions:
                        return substitutions[str(int(group_value))]
            except (ValueError, TypeError):
                pass
        
        return str(group_value)

    def _get_group_value(self, obj, group_config):
        """Получить значение для группировки объекта"""
        property_name = group_config.get('property_name', '').strip()
        if not property_name:
            return None
        
        # Проверяем наличие свойства      
        try:
            if property_name not in obj.properties:
                return None
                
            value = obj.getProperty(property_name)
            if value is None:
                return None
            
            # Если указано object_property, значит значение - имя объекта
            object_property = group_config.get('object_property', '').strip()
            if object_property:
                # value должен быть именем объекта
                if isinstance(value, str):
                    ref_value = getProperty(value+"."+object_property)
                    return ref_value
                return None
            
            return str(value) if value is not None else None
        except Exception as e:
            self.logger.error(f"Error getting group value for {obj.name}.{property_name}: {e}")
            return None

    def route_index(self):
        @self.blueprint.route("/index")
        @handle_user_required
        def index():
            objects_storage.preload_objects()
            
            # Загружаем настройки и группы
            custom_groups = self.config.get('custom_groups', [])
            show_class = self.config.get('group', False)
            show_none = not self.config.get('hide_no_grouping', False)

            # Получаем выбранную группу пользователя
            selected_group = None
            if current_user.is_authenticated:
                try:
                    user_obj = getObject(current_user.username)
                    if user_obj:
                        selected_group = getProperty(f"{current_user.username}.dashboard_group", 'value')
                except Exception as e:
                    self.logger.error(f"Error getting user dashboard_group: {e}")

            # Проверяем валидность текущего выбора и выбираем дефолтную группу при необходимости
            is_valid = False
            if selected_group == 'class':
                is_valid = show_class
            elif selected_group == 'none':
                is_valid = show_none
            elif selected_group:
                # Проверяем наличие кастомной группы
                for g in custom_groups:
                    if g.get('id') == selected_group:
                        is_valid = True
                        break
            
            if not is_valid:
                # Приоритет выбора дефолтной группы
                if show_class:
                    selected_group = 'class'
                elif show_none:
                    selected_group = 'none'
                elif custom_groups:
                    selected_group = custom_groups[0].get('id')
                else:
                    selected_group = 'none'

            # Получаем список доступных групп для UI
            available_groups = []
            if show_none:
                available_groups.append({'id': 'none', 'name': 'No Grouping', 'icon': 'fas fa-th'})
            if show_class:
                available_groups.append({'id': 'class', 'name': 'By Class', 'icon': 'fas fa-sitemap'})
            
            for group in custom_groups:
                available_groups.append({
                    'id': group.get('id', ''),
                    'name': group.get('name', ''),
                    'icon': group.get('icon', 'fas fa-layer-group')
                })

            # Группируем объекты
            groups = {}
            classes = {}
            res = Class.query.all()
            for item in res:
                classes[item.name] = row2dict(item)

            if selected_group == 'none':
                # Без группировки - создаем одну группу 'all'
                templates = {}
                for key, obj in sorted(objects_storage.items(), key=lambda x: x[0].lower()):
                    render = obj.render()
                    if render:
                        templates[key] = render
                groups['all'] = {"objects": templates, "title": None}

            elif selected_group == 'class':
                # Группировка по классу
                grouping_info = {'type': 'class'}  # Для JavaScript
                for key, obj in sorted(objects_storage.items(), key=lambda x: x[0].lower()):
                    render = obj.render()
                    if render:
                        if obj.parents:
                            parent = obj.parents[0]
                            if parent not in groups:
                                groups[parent] = {"objects":{}, "title": classes[parent].get('description') or classes[parent].get('name', parent)}
                            if "class" not in groups[parent]:
                                groups[parent]["class"] = classes[parent]
                            groups[parent]["objects"][key] = render
                        else:
                            if 'root' not in groups:
                                groups['root'] = {"objects":{}, "title": "Root"}
                            groups['root']["objects"][key] = render
            else:
                # Пользовательская группировка
                group_config = None
                for g in custom_groups:
                    if g.get('id') == selected_group:
                        group_config = g
                        break
                
                if group_config:
                    property_name = group_config.get('property_name', '').strip()
                    show_undefined = group_config.get('show_undefined', False)
                    
                    for key, obj in sorted(objects_storage.items(), key=lambda x: x[0].lower()):
                        if property_name not in obj.properties:
                            continue
                        render = obj.render()
                        if render:
                            group_value = self._get_group_value(obj, group_config)
                            
                            if group_value is None:
                                if show_undefined:
                                    group_key = 'undefined'
                                    if group_key not in groups:
                                        groups[group_key] = {"objects":{}, "title": "Undefined", "has_substitutions": False}
                                    groups[group_key]["objects"][key] = render
                                # Иначе пропускаем объект
                            else:
                                group_key = str(group_value)
                                group_title = self._get_group_title(group_value, group_config)
                                has_substitutions = bool(group_config.get('value_substitutions', '').strip())
                                
                                if group_key not in groups:
                                    groups[group_key] = {"objects":{}, "title": group_title, "has_substitutions": has_substitutions}
                                groups[group_key]["objects"][key] = render
                else:
                    # Если группа не найдена, показываем без группировки
                    templates = {}
                    for key, obj in sorted(objects_storage.items(), key=lambda x: x[0].lower()):
                        render = obj.render()
                        if render:
                            templates[key] = render
                    groups['all'] = {"objects": templates, "title": None}
                    selected_group = 'none'

            # Extract plugin name from module path
            plugin_name = self.name.split('.')[-1] if '.' in self.name else self.name
            
            # Получаем информацию о текущей группировке для JavaScript
            grouping_info = None
            if selected_group == 'class':
                grouping_info = {'type': 'class'}
            elif selected_group and selected_group != 'none':
                group_config = None
                for g in custom_groups:
                    if g.get('id') == selected_group:
                        group_config = g
                        break
                if group_config:
                    grouping_info = {
                        'type': 'custom',
                        'property_name': group_config.get('property_name', '').strip(),
                        'object_property': group_config.get('object_property', '').strip(),
                        'show_undefined': group_config.get('show_undefined', False),
                        'value_substitutions': group_config.get('value_substitutions', '').strip(),
                    }
            
            content = {
                'groups': groups,
                'available_groups': available_groups,
                'selected_group': selected_group,
                'save_group_url': f'/admin/{plugin_name}/save_group',
                'grouping_info': grouping_info,
                'hide_welcome': self.config.get('hide_welcome', False),
            }
            
            if flask_request.args.get('json'):
                return jsonify(content)

            return self.render("index.html", content)

    def route_save_group(self):
        @self.blueprint.route("/admin/Dashboard/save_group", methods=['POST'])
        @handle_user_required
        def save_group():
            """Сохранить выбранную группу пользователя"""
            if not current_user.is_authenticated:
                return jsonify({'success': False, 'error': 'Not authenticated'}), 401
            
            try:
                data = flask_request.get_json()
                group_id = data.get('group_id')
                
                if group_id is None:
                    return jsonify({'success': False, 'error': 'group_id is required'}), 400
                
                # Сохраняем в свойство пользователя
                user_obj = getObject(current_user.username)
                if user_obj:
                    if 'dashboard_group' not in user_obj.properties:
                        from app.core.lib.constants import PropertyType
                        from app.database import session_scope
                        from app.core.models.Clasess import Class as UserClass
                        with session_scope() as session:
                            cls = session.query(UserClass).filter(UserClass.name == 'Users').one_or_none()
                            if cls:
                                from app.core.lib.object import addClassProperty
                                addClassProperty('dashboard_group', 'Users', 'Dashboard grouping preference', 0, type=PropertyType.String)
                    
                    setProperty(f"{current_user.username}.dashboard_group", group_id, source='Dashboard')
                    return jsonify({'success': True})
                else:
                    return jsonify({'success': False, 'error': 'User object not found'}), 404
                    
            except Exception as e:
                self.logger.error(f"Error saving dashboard group: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

    def route_get_object_group(self):
        @self.blueprint.route("/admin/Dashboard/get_object_group", methods=['GET'])
        @handle_user_required
        def get_object_group():
            """Получить текущую группу объекта после изменения свойства"""
            if not current_user.is_authenticated:
                return jsonify({'success': False, 'error': 'Not authenticated'}), 401
            
            try:
                object_name = flask_request.args.get('object_name')
                if not object_name:
                    return jsonify({'success': False, 'error': 'object_name is required'}), 400
                
                # Получаем текущую выбранную группу
                selected_group = None
                user_obj = getObject(current_user.username)
                if user_obj:
                    selected_group = getProperty(f"{current_user.username}.dashboard_group", 'value')
                
                # Загружаем настройки
                custom_groups = self.config.get('custom_groups', [])
                show_class = self.config.get('group', False)
                show_none = not self.config.get('hide_no_grouping', False)

                # Проверяем валидность текущего выбора и выбираем дефолтную группу при необходимости
                is_valid = False
                if selected_group == 'class':
                    is_valid = show_class
                elif selected_group == 'none':
                    is_valid = show_none
                elif selected_group:
                    # Проверяем наличие кастомной группы
                    for g in custom_groups:
                        if g.get('id') == selected_group:
                            is_valid = True
                            break
                
                if not is_valid:
                    # Приоритет выбора дефолтной группы (должен совпадать с route_index)
                    if show_class:
                        selected_group = 'class'
                    elif show_none:
                        selected_group = 'none'
                    elif custom_groups:
                        selected_group = custom_groups[0].get('id')
                    else:
                        selected_group = 'none'
                
                # Если группировка отключена или по классу, возвращаем информацию
                if selected_group == 'none':
                    return jsonify({
                        'success': True,
                        'group_key': None,
                        'group_title': None,
                        'no_grouping': True
                    })
                
                if selected_group == 'class':
                    # Группировка по классу
                    obj = objects_storage.getObjectByName(object_name)
                    if not obj:
                        return jsonify({'success': False, 'error': 'Object not found'}), 404
                    
                    group_key = obj.parents[0] if obj.parents else 'root'
                    
                    # Получаем название класса
                    from app.database import session_scope
                    with session_scope() as session:
                        if group_key != 'root':
                            cls = session.query(Class).filter(Class.name == group_key).one_or_none()
                            if cls:
                                cls_dict = row2dict(cls)
                                group_title = cls_dict.get('description') or cls_dict.get('name', group_key)
                            else:
                                group_title = group_key
                        else:
                            group_title = 'Root'
                    
                    return jsonify({
                        'success': True,
                        'group_key': group_key,
                        'group_title': group_title
                    })
                
                # Пользовательская группировка
                group_config = None
                for g in custom_groups:
                    if g.get('id') == selected_group:
                        group_config = g
                        break
                
                if not group_config:
                    return jsonify({'success': False, 'error': 'Group configuration not found'}), 404
                
                obj = objects_storage.getObjectByName(object_name)
                if not obj:
                    return jsonify({'success': False, 'error': 'Object not found'}), 404
                
                # Получаем значение группы
                group_value = self._get_group_value(obj, group_config)
                show_undefined = group_config.get('show_undefined', False)
                has_substitutions = bool(group_config.get('value_substitutions', '').strip())
                
                if group_value is None:
                    if show_undefined:
                        return jsonify({
                            'success': True,
                            'group_key': 'undefined',
                            'group_title': 'Undefined',
                            'has_substitutions': False
                        })
                    else:
                        return jsonify({
                            'success': True,
                            'group_key': None,
                            'group_title': None,
                            'hidden': True
                        })
                else:
                    group_key = str(group_value)
                    group_title = self._get_group_title(group_value, group_config)
                    return jsonify({
                        'success': True,
                        'group_key': group_key,
                        'group_title': group_title,
                        'has_substitutions': has_substitutions
                    })
                    
            except Exception as e:
                self.logger.error(f"Error getting object group: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
