from flask import Blueprint, render_template, redirect, url_for, current_app, request, flash
from apps.app import db
from apps.crud.models import User
from apps.crud.forms import UserForm
from flask_login import login_required
import os
import cv2
from werkzeug.utils import secure_filename
from flask_login import current_user
from apps.crud.models import analyze_image, AnalysisResult, Category, FilteredArticle, RawArticle, ImageTag
from apps.auth.forms import UploadForm, CategoryForm
from PIL import Image
import numpy as np
import torch
import torchvision
import uuid
from pathlib import Path
from sqlalchemy.exc import SQLAlchemyError

crud = Blueprint(
    "crud",
    __name__,
    template_folder = "templates",
    static_folder = "static",
)

@crud.route("/")
def nccu():
    return render_template("crud/nccu.html")

@crud.route("/sql")
def sql():
    db.session.query(User).count()
    return "請確認控制台日誌"

@crud.route("/users/new",methods=["GET","POST"])
def create_user():
    #建立UserForm的實體
    form = UserForm()
    #驗證表單值
    if form.validate_on_submit():
        #建立使用者
        user = User(
            username = form.username.data,
            email = form.email.data,
            password = form.password.data,
            identity = form.identity.data,
        )
        #增加並提交使用者
        db.session.add(user)
        db.session.commit()
        #重新導向使用者列表
        return redirect(url_for("crud.users"))
    return render_template("crud/create.html", form = form)

@crud.route("/users")
@login_required
def users():
    """取得使用者列表"""
    users = User.query.all()
    return render_template("crud/users.html", users = users)

@crud.route("/users/<user_id>", methods=["GET","POST"])
def edit_user(user_id):
    form = UserForm()
    #使用User模型取得使用者
    user = User.query.filter_by(id = user_id).first()
    #發送表單後，修改內容定重新導向使用者列表頁面
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.password = form.password.data
        user.identity = form.identity
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("crud.users"))
    #請求方法為GET時，回傳HTML檔案
    return render_template("crud/edit.html", user=user, form=form)   

@crud.route("/users/<user_id>/delete", methods=["GET","POST"])
def delete_user(user_id):
    user  = User.query.filter_by(id=user_id).first()
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for("crud.users"))

@crud.route('/us')
def display_us_file():
    try:
        file_path = os.path.join(current_app.root_path, 'crud', 'static', 'text', 'us.txt')
        with open(file_path, 'r') as file:
            content = file.read()
        return render_template('crud/us.html', content=content)
    except FileNotFoundError:
        return "File not found", 404
    
    
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 建立用戶專屬目錄
def create_user_directory(username):
    user_folder = os.path.join(current_app.root_path, 'crud', 'static', 'uploads', username)
    os.makedirs(user_folder, exist_ok=True)
    return user_folder

@crud.route('/upload', methods=['GET', 'POST'])
def upload_image():
    form = UploadForm()
    if form.validate_on_submit():
        file = form.image.data
        if file and allowed_file(file.filename):
            username = current_user.username
            user_folder = create_user_directory(username)

            # 保存原始圖片
            filename = secure_filename(file.filename)
            original_path = os.path.join(user_folder, filename)
            file.save(original_path)

            # 執行檢測
            tags, marked_filename = exec_detect(
                target_image_path=original_path,
                model_path=MODEL_PATH,
                labels=LABELS
            )

            # 調試輸出
            print("檢測到的標籤：", tags)

            # 處理位置參數
            location = request.form.get('image_choice', 'default_value')
            print("接收到的位置參數：", location)

            try:
                # 保存分析結果
                result = AnalysisResult(
                    user_id=current_user.id,
                    username=current_user.username,
                    original_image_path=f'uploads/{username}/{filename}',
                    marked_image_path=f'uploads/{username}/{marked_filename}',
                    suggestions=", ".join(tags) if tags else "無標籤",
                    location=location,
                )
                db.session.add(result)
                db.session.commit()
                flash('圖片上傳成功', 'success')
            except SQLAlchemyError as e:
                db.session.rollback()
                flash('數據庫錯誤', 'danger')
                print(str(e))

            return render_template(
                'crud/uploadresult.html',
                original_image=f'uploads/{username}/{filename}',
                marked_image=f'uploads/{username}/{marked_filename}',
                suggestions=tags,
                location=location
            )
        else:
            flash('請選擇有效的圖片文件', 'danger')

    return render_template('crud/upload.html', form=form)

@crud.route("/result/<username>")
def results(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    results = AnalysisResult.query.filter_by(user_id=user.id).paginate(page=page, per_page=5)
    
    for result in results.items:
        result.original_filename = os.path.basename(result.original_image_path)
        result.marked_filename = os.path.basename(result.marked_image_path)
        
    return render_template("crud/results.html", results=results, user=user)

@crud.route("/example")
def example():
    return render_template("crud/example.html")

@crud.route('/articles')
def articles():
    # 獲取查詢參數
    page = request.args.get('page', 1, type=int)
    selected_category = request.args.get('category', None, type=str)
    search_query = request.args.get('query', '', type=str)

    # 獲取所有分類
    categories = Category.query.order_by(Category.name).all()

    # 根據分類和搜尋查詢篩選文章
    articles_query = FilteredArticle.query

    if selected_category:
        category = Category.query.filter_by(name=selected_category).first_or_404()
        articles_query = articles_query.filter_by(category=category)

    if search_query:
        articles_query = articles_query.filter(
            FilteredArticle.title.ilike(f'%{search_query}%') |
            FilteredArticle.content.ilike(f'%{search_query}%')
        )

    # 按瀏覽次數排序，並進行分頁
    articles_pagination = articles_query.order_by(FilteredArticle.view_count.desc()).paginate(page=page, per_page=10)

    return render_template('crud/articles.html',
                           articles=articles_pagination,
                           categories=categories,
                           selected_category=selected_category,
                           search_query=search_query)

@crud.route('/view_article/<int:article_id>')
def view_article(article_id):
    article = FilteredArticle.query.get_or_404(article_id)
    # 增加瀏覽次數
    article.view_count += 1
    db.session.commit()
    return render_template('crud/view_article.html', article=article)

@crud.route('/admin/raw_articles')
def admin_raw_articles():
    raw_articles = RawArticle.query.all()
    return render_template('crud/admin_raw_articles.html', raw_articles=raw_articles)

@crud.route('/admin/categorize/<int:article_id>', methods=['GET', 'POST'])
def categorize_article(article_id):
    article = RawArticle.query.get_or_404(article_id)
    categories = Category.query.all()

    form = CategoryForm()
    form.category.choices = [(0, '選擇分類')] + [(c.id, c.name) for c in categories]

    if form.validate_on_submit():
        new_category_name = form.new_category.data.strip()
        selected_category_id = form.category.data

        if new_category_name:  # 使用者新增分類
            existing_category = Category.query.filter_by(name=new_category_name).first()
            if not existing_category:
                new_category = Category(name=new_category_name)
                db.session.add(new_category)
                db.session.commit()
                flash(f'分類 "{new_category_name}" 新增成功', 'success')
                # 將文章分類到新增的分類中
                selected_category_id = new_category.id
            else:
                flash(f'分類 "{new_category_name}" 已存在', 'warning')
                selected_category_id = existing_category.id

        if selected_category_id and selected_category_id != 0:  # 檢查是否有選擇有效分類
            category = Category.query.get(selected_category_id)
            filtered_article = FilteredArticle(
                title=article.title,
                content=article.content,
                url=article.url,
                category_id=category.id
            )
            db.session.add(filtered_article)
            db.session.delete(article)
            db.session.commit()
            flash('文章已成功分類', 'success')
            return redirect(url_for('crud.admin_raw_articles'))
        else:
            flash('請選擇有效分類或新增分類', 'danger')

    return render_template(
        'crud/categorize_article.html',
        article=article,
        form=form
    )

@crud.route('/search')
def search():
    query = request.args.get('query', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 10  # 每頁顯示的文章數量

    if query:
        # 使用 FilteredArticle 模型進行搜尋
        pagination = FilteredArticle.query.filter(
            (FilteredArticle.title.contains(query)) | (FilteredArticle.content.contains(query))
        ).paginate(page=page, per_page=per_page, error_out=False)
    else:
        # 如果沒有搜尋詞，重定向到文章列表首頁
        return redirect(url_for('crud.articles'))

    articles = pagination
    categories = Category.query.all()
    selected_category = None  # 搜尋結果不特定於某個分類

    return render_template('crud/articles.html', articles=articles, categories=categories, selected_category=selected_category)

UPLOAD_FOLDER = "apps/crud/static/uploads"
MODEL_PATH = Path('apps/crud/model.pt')  # 請確認模型路徑
LABELS = [
    "unlabeled", "person", "bicycle", "car", "motorcycle", "airplane", 
    "bus", "train", "truck", "boat",  # 簡化標籤，完整標籤請根據需求替換
]

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 執行檢測
def exec_detect(target_image_path, model_path, labels):
    # 加載圖片
    image = Image.open(target_image_path).convert('RGB')
    image_tensor = torchvision.transforms.functional.to_tensor(image)

    # 加載模型
    model = torch.load(model_path)
    model = model.eval()

    # 執行檢測
    output = model([image_tensor])[0]

    tags = []
    result_image = np.array(image.copy())
    for box, label, score in zip(output["boxes"], output["labels"], output["scores"]):
        if score > 0.5 and label < len(labels):  # 添加索引檢查
            color = [np.random.randint(0, 255) for _ in range(3)]
            c1 = (int(box[0]), int(box[1]))
            c2 = (int(box[2]), int(box[3]))
            cv2.rectangle(result_image, c1, c2, color, 2)
            cv2.putText(result_image, labels[label], c1, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            tags.append(labels[label])
        else:
            print(f"忽略無效標籤: {label}, 範圍超出 labels 長度")

    # 保存標記後的圖片
    detected_image_file_name = f"marked_{uuid.uuid4().hex}.jpg"
    detected_image_file_path = os.path.join(os.path.dirname(target_image_path), detected_image_file_name)
    cv2.imwrite(detected_image_file_path, cv2.cvtColor(result_image, cv2.COLOR_RGB2BGR))

    return tags, detected_image_file_name

# 建立用戶目錄
def create_user_directory(username):
    user_folder = os.path.join(UPLOAD_FOLDER, username)
    os.makedirs(user_folder, exist_ok=True)
    return user_folder