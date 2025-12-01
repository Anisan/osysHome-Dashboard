from flask_wtf import FlaskForm
from wtforms import BooleanField, SubmitField, FieldList, FormField, StringField
from wtforms.validators import Optional
from wtforms.form import Form

# Определение подформы для одной группы (используем Form вместо FlaskForm, чтобы избежать проверки CSRF)
class GroupForm(Form):
    group_name = StringField('Name', validators=[Optional()])
    group_icon = StringField('Icon (optional)', validators=[Optional()])
    property_name = StringField('Property Name', validators=[Optional()])
    object_property = StringField('Object Property (optional)', validators=[Optional()])
    show_undefined = BooleanField('Show Undefined', default=False)
    value_substitutions = StringField('Value Substitutions (optional)', validators=[Optional()])

# Определение класса формы
class SettingsForm(FlaskForm):
    group = BooleanField('Group objects')
    hide_welcome = BooleanField('Hide Welcome')
    hide_no_grouping = BooleanField('Hide No Grouping')
    groups = FieldList(FormField(GroupForm), min_entries=0)
    submit = SubmitField('Submit')
