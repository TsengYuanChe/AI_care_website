from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, SelectField, FileField
from wtforms.validators import DataRequired, Email, Length

class SignUpForm(FlaskForm):
    username = StringField(
        "使用者名稱",
        validators =[
            DataRequired("必須填寫使用者名稱"),
            Length(1, 30, "請勿輸入超過30個字元"),
        ],
    )
    email = StringField(
        "郵件地址",
        validators =[
            DataRequired("必須填寫郵件地址"),
            Email("請依照電子郵件格式輸入"),
        ],
    )
    password = PasswordField("密碼",
        validators=[DataRequired("必須填寫密碼")])
    
    identity = SelectField(
        'Choose an option:',
        choices=[('option1', 'Option 1'), ('option2', 'Option 2'), ('option3', 'Option 3')],
        validators=[DataRequired()]
    )
    
    submit = SubmitField("提交表單")
    
class LoginForm(FlaskForm):
    email = StringField(
        "郵件位址",
        validators=[
            DataRequired("必須填寫郵件地址"),
            Email("請依照電子郵件的格式輸入"),
        ],
    )
    password = PasswordField("密碼", validators=[DataRequired("必須填寫密碼")])
    submit = SubmitField("登入")
    
class UploadForm(FlaskForm):
    image = FileField('上傳圖片', validators=[DataRequired()])
    submit = SubmitField('上傳並分析')