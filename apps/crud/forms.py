from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, RadioField, SelectField
from wtforms.validators import DataRequired, Email, length, Length


class UserForm(FlaskForm):
    #設定使用者表單中的username屬性的標籤和驗證器
    username = StringField(
        "使用者名稱",
        validators=[
            DataRequired(message="必須填寫使用這名稱"),
            length(max = 30, message = "請勿輸入超過30個字元"),
        ],
    )
    #設定使用者表單中email屬性的標籤和驗證器
    email = StringField(
        "郵件位址",
        validators=[
            DataRequired(message="必須填寫郵件地址"),
            Email(message = "請依照電子郵件格式輸入"),
        ],
    )
    #設定使用者標單中password屬性的標籤和驗證器
    password = PasswordField(
        "密碼",
        validators=[DataRequired(message = "必須填寫密碼")],
    )
    
    identity = RadioField(
        'Choose an option:',
        choices=[('option1', 'Option 1'), ('option2', 'Option 2'), ('option3', 'Option 3')],
        validators=[DataRequired()]
    )
    #設定使用者表單中submit的內容
    submit = SubmitField("提交表單")
    
class CategoryForm(FlaskForm):
    category = SelectField(
        '選擇分類',
        coerce=int,  # 表示選項的值是整數類型
        choices=[],  # 稍後在視圖函數中動態填充
        validators=[DataRequired(message="請選擇分類")]
    )
    new_category = StringField(
        '新增分類',
        validators=[
            Length(max=50, message="分類名稱不能超過 50 個字符")
        ]
    )
    submit = SubmitField('儲存分類')