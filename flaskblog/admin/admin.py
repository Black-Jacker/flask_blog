#! /env python
# _*_ coding:utf8 _*_
# @author:Haojie Ren
# @time:2017/9/2 0:46

from os import path
from flask import Blueprint
from flask import render_template
from flask import redirect
from flask import flash
from flask import url_for
from flask import request
from flask import session
from flask import current_app
from flask import g,make_response
from flask import jsonify
from sqlalchemy import func
from sqlalchemy import desc
from flask_login import login_user
from flask_login import logout_user
from flask_login import current_user
from flask_login import login_required
from flask_principal import Identity,AnonymousIdentity,identity_changed,current_app

from flaskblog.models import db
from flaskblog.models.users import Users
from flaskblog.models.posts import Posts
from flaskblog.models.tags import Tags
from flaskblog.models.comments import Comments
from flaskblog.models.posts_tags import posts_tags

from flaskblog.form import PostForm

from flaskblog.extensions import facebook

# 定义蓝图
admin_blueprint = Blueprint('admin',__name__,template_folder='templates',static_folder='static',url_prefix='/admin')

@admin_blueprint.route('/')
def admin():
    """weblcom the admin; list the blog"""
    return render_template('admin.admin.html',title='admin',user=current_user)

@admin_blueprint.route('/test')
def test():
    """weblcom the admin; list the blog"""
    return render_template('admin.new.html',title='admin',user=current_user)

# 博客列表
@admin_blueprint.route('/list_blog')
@login_required
def list_blog():
    """list the blog, if method is DELETE,delete the blog""" 
    # 返回用户的所有文章
    blogs = db.session.query(Posts).filter_by(user_id=current_user.id).all()
    return render_template('admin.list_blog.html',title='list blog',blogs=blogs)

# 删除
@admin_blueprint.route('/delete_blog/<string:id>')
@login_required
def delete_blog(id):
    blog = db.session.query(Posts).filter_by(id=id).first_or_404()
    db.session.delete(blog)
    db.session.commit()
    flash(u'删除成功')
    return redirect(url_for('admin.list_blog'))

# 编辑
@admin_blueprint.route('/edit_blog/<string:id>', methods=['GET','POST'])
@login_required
def edit_blog(id):
    """
    :parm: post.id
    edit the post
    """
    blog = db.session.query(Posts).filter_by(id=id).first_or_404()
    if request.method == 'POST':
        blog.title = request.form.get('title',None)
        blog.content = request.form.get('content',None)
        blog.tags = request.form.getlist('tags[]',None)
        db.session.add(blog)
        db.session.commit()
        flash(u'修改成功')
        return redirect(url_for('admin.list_blog'))
    if request.method == 'GET':
        form = PostForm()
        return render_template('admin.edit_blog.html',title='edit blog',blog=blog,form=form)

# 新建
@admin_blueprint.route('/new_blog',methods=['GET','POST'])
@login_required
def new_blog():
    """new a blog"""
    if request.method == 'POST':
        title = request.form.get('title',None)
        content = request.form.get('content',None)
        tags = request.form.getlist('tags[]',None)
        post = Posts(title=title,content=content)
        post.user_id = current_user.id
        post.tags = tags
        db.session.add(post)
        db.session.commit()
        flash(u'添加成功!')
        return redirect(url_for('admin.list_blog'))
    if request.method == 'GET':
        form = PostForm()
        return render_template('admin.new_blog.html',title='new blog',form=form)


@admin_blueprint.route('/list_tag')
@login_required
def list_tag():
    pass

@admin_blueprint.route('/del_tag',methods=['DELETE'])
@login_required
def del_tag(tag_id):
    try:
        tag = db.session.query(Tags).filter_by(id=tag_id).first_or_404()
        db.session.delete(tag)
        db.session.commit()
    except Exception as e:
        return jsonify({'code':417,'message':'删除失败！','exception':e})
    finally:
        pass


@admin_blueprint.route('/add_tag',methods=['GET','POST'])
@login_required
def add_tag():
    if request.method == 'GET':
        return render_template('admin.add_tag.html',title='add tag')

    if request.content_type == "application/json":
        code = request.json.get('tag_code')
        name = request.json.get('tag_name')
        pid = db.session.query(Tags).filter_by(code=request.json.get('p')).first_or_404()
        tag = Tags(code=code,name=name,pid=pid)
        try:
            db.session.add(tag)
            db.session.commit()
            return jsonify({'code':201,'message':'添加%s成功','data':tag}) %(name)
        except Exception as e:
            return jsonify({'code':417,'message':'添加%s失败！发生异常！','exception':e})
    else:
        code = request.form.get('tag_code')
        name = request.form.get('tag_name')
        pid = db.session.query(Tags).filter_by(code=request.json.get('p')).first_or_404()
        tag = Tags(code=code,name=name,pid=pid)
        try:
            db.session.add(tag)
            db.session.commit()
            return redirect(url_for('admin.list_tag'))
        except Exception as e:
           return jsonify({'code':417,'message':'添加%s失败！发生异常！','exception':e})



@admin_blueprint.teardown_request
def shutdown_session(exception=None):
    try:
        db.session.remove()
    except Exception as e:
        print e