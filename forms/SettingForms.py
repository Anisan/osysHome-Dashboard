from flask_wtf import FlaskForm
from wtforms import BooleanField, SubmitField

# Определение класса формы
class SettingsForm(FlaskForm):
    group = BooleanField('Group objects')
    submit = SubmitField('Submit')
