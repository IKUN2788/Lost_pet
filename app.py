from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import uuid
from PIL import Image

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pet_lost.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 数据库模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    real_name = db.Column(db.String(50), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    avatar = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    posts = db.relationship('Post', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    pet_type = db.Column(db.String(50), nullable=False)
    lost_location = db.Column(db.String(200), nullable=False)
    contact_info = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    images = db.relationship('PostImage', backref='post', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='post', lazy=True, cascade='all, delete-orphan')

class PostImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    images = db.relationship('CommentImage', backref='comment', lazy=True, cascade='all, delete-orphan')

class CommentImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 辅助函数
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file):
    if file and allowed_file(file.filename):
        filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # 压缩图片
        image = Image.open(file)
        image.thumbnail((800, 800), Image.Resampling.LANCZOS)
        image.save(filepath, optimize=True, quality=85)
        
        return filename
    return None

# 路由定义
@app.route('/')
def index():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('index.html', posts=posts)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # 检查用户是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'error')
            return render_template('register.html')
        
        # 创建新用户
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功！请登录', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('登录成功！', 'success')
            return redirect(url_for('index'))
        else:
            flash('邮箱或密码错误', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已退出登录', 'info')
    return redirect(url_for('index'))

@app.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        pet_type = request.form['pet_type']
        lost_location = request.form['lost_location']
        contact_info = request.form['contact_info']
        
        # 创建帖子
        post = Post(
            title=title,
            description=description,
            pet_type=pet_type,
            lost_location=lost_location,
            contact_info=contact_info,
            user_id=current_user.id
        )
        db.session.add(post)
        db.session.flush()  # 获取post.id
        
        # 处理图片上传
        files = request.files.getlist('images')
        for file in files[:9]:  # 最多9张图片
            if file and file.filename:  # 确保文件存在且有文件名
                filename = save_image(file)
                if filename:
                    post_image = PostImage(filename=filename, post_id=post.id)
                    db.session.add(post_image)
        
        db.session.commit()
        flash('发布成功！', 'success')
        return redirect(url_for('index'))
    
    return render_template('create_post.html')

@app.route('/post/<int:post_id>')
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.created_at.desc()).all()
    return render_template('view_post.html', post=post, comments=comments)

@app.route('/my_posts')
@login_required
def my_posts():
    posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.created_at.desc()).all()
    return render_template('my_posts.html', posts=posts)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.real_name = request.form.get('real_name', '')
        current_user.phone = request.form.get('phone', '')
        current_user.location = request.form.get('location', '')
        current_user.bio = request.form.get('bio', '')
        
        # 处理头像上传
        avatar_file = request.files.get('avatar')
        if avatar_file and avatar_file.filename:
            filename = save_image(avatar_file)
            if filename:
                current_user.avatar = filename
        
        db.session.commit()
        flash('个人资料更新成功！', 'success')
        return redirect(url_for('profile'))
    
    return render_template('edit_profile.html', user=current_user)

@app.route('/add_comment/<int:post_id>', methods=['POST'])
@login_required
def add_comment(post_id):
    content = request.form['content']
    
    if not content.strip():
        return jsonify({'success': False, 'message': '评论内容不能为空'})
    
    comment = Comment(
        content=content,
        user_id=current_user.id,
        post_id=post_id
    )
    db.session.add(comment)
    db.session.flush()
    
    # 处理评论图片
    files = request.files.getlist('comment_images')
    for file in files[:3]:  # 评论最多3张图片
        filename = save_image(file)
        if filename:
            comment_image = CommentImage(filename=filename, comment_id=comment.id)
            db.session.add(comment_image)
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/delete_comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    post = comment.post
    
    # 权限验证：评论作者或帖子作者可以删除评论
    if comment.user_id != current_user.id and post.user_id != current_user.id:
        return jsonify({'success': False, 'message': '无权限删除此评论'})
    
    # 删除评论相关的图片文件
    for image in comment.images:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image.filename))
        except:
            pass
    
    db.session.delete(comment)
    db.session.commit()
    return jsonify({'success': True, 'message': '评论已删除'})

@app.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    if post.user_id != current_user.id:
        flash('无权限删除此帖子', 'error')
        return redirect(url_for('index'))
    
    # 删除相关图片文件
    for image in post.images:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image.filename))
        except:
            pass
    
    db.session.delete(post)
    db.session.commit()
    flash('帖子已删除', 'success')
    return redirect(url_for('my_posts'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)