from datetime import datetime

from apps.app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

#建立繼承db.Model的User類別
class User(db.Model, UserMixin):
    #指定表格名稱
    __tablename__ = "users"
    #定義直欄內容
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String, index = True)
    email = db.Column(db.String, unique = True, index = False)
    password_hash = db.Column(db.String)
    identity = db.Column(db.String(50), server_default = "student")
    created_at = db.Column(db.DateTime, default = datetime.now)
    updated_at = db.Column(db.DateTime, default = datetime.now, onupdate = datetime.now)


    #設置密碼的屬性
    @property
    def password(self):
        raise AttributeError("無法加載")

    #藉由設置密碼的setter函數，設定經過雜湊處理的密碼
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_duplicate_email(self):
        return User.query.filter_by(email=self.email).first() is not None
    
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

import cv2
import numpy as np

def analyze_image(img):
    # 假設我們偵測危險區域並進行標示
    # 在這裡執行你的圖片分析邏輯，這裡是簡單的例子

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # 轉換為灰階
    edges = cv2.Canny(gray, 100, 200)  # 使用 Canny 邊緣偵測

    # 標記邊緣
    marked_img = img.copy()
    marked_img[edges > 0] = [0, 0, 255]  # 將邊緣區域標為紅色

    # 假設我們分析後給出改善建議
    analysis_text = "圖片中偵測到潛在的危險區域，建議進行檢查並確保安全。"

    return marked_img, analysis_text


class AnalysisResult(db.Model):
    __tablename__ = 'analysis_result'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_user_id'), nullable=False)  # 與使用者關聯
    username = db.Column(db.String(255), nullable=False)  # 儲存使用者名稱
    original_image_path = db.Column(db.String(255), nullable=False)
    marked_image_path = db.Column(db.String(255), nullable=False)
    suggestions = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(255), nullable=False, default='default_value')

    user = db.relationship('User', backref=db.backref('results', lazy=True))
    
    # 新增標籤關聯
    tags = db.relationship('ImageTag', backref='analysis_result', lazy=True)

    def __repr__(self):
        return f'<AnalysisResult {self.id} by User {self.user_id}>'

class ImageTag(db.Model):
    __tablename__ = 'image_tag'
    id = db.Column(db.Integer, primary_key=True)
    tag_name = db.Column(db.String(255), nullable=False)
    analysis_result_id = db.Column(db.Integer, db.ForeignKey('analysis_result.id', name='fk_analysis_result_id'), nullable=False)

    def __repr__(self):
        return f'<ImageTag {self.tag_name} for Result {self.analysis_result_id}>'

class RawArticle(db.Model):
    __tablename__ = 'raw_articles'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    url = db.Column(db.String(255), unique=True, nullable=False)
    scraped_at = db.Column(db.DateTime, server_default=db.func.now())
    

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    filtered_articles = db.relationship('FilteredArticle', backref='category', lazy=True)
    
class FilteredArticle(db.Model):
    __tablename__ = 'filtered_articles'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    url = db.Column(db.String(255), unique=True, nullable=False)
    view_count = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    filtered_at = db.Column(db.DateTime, server_default=db.func.now())