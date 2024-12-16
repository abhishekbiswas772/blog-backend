from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Define models
class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    author = db.Column(db.String(128), nullable=False)
    read_time = db.Column(db.String(32), nullable=False)
    date = db.Column(db.String(32), nullable=False)
    github_link = db.Column(db.String(256))

class Introduction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    images = db.Column(db.String(256))

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    introduction_id = db.Column(db.Integer, db.ForeignKey('introduction.id'), nullable=False)
    topic = db.Column(db.String(128), nullable=False)

class Paragraph(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=False)
    order = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(256), nullable=False)
    content = db.Column(db.Text, nullable=False)
    images = db.Column(db.String(256))

class BulletPoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    paragraph_id = db.Column(db.Integer, db.ForeignKey('paragraph.id'), nullable=False)
    point = db.Column(db.String(256), nullable=False)

class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=False)
    url = db.Column(db.String(256), nullable=False)

class Acknowledgment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=False)
    text = db.Column(db.String(256), nullable=False)

# API route to create a new blog
@app.route('/api/blog', methods=['POST'])
def create_blog():
    try:
        data = request.get_json()
        title = data.get('title')
        author = data.get('author')
        read_time = data.get('read_time')
        date = data.get('date')
        github_link = data.get('github_link')
        
        if not all([title, author, read_time, date]):
            return jsonify({"error": "Missing required fields"}), 400

        new_blog = Blog(title=title, author=author, read_time=read_time, date=date, github_link=github_link)
        db.session.add(new_blog)
        db.session.commit()

        # Save Introduction
        introduction = data.get('introduction', {})
        intro_summary = introduction.get('summary')
        intro_images = introduction.get('images')
        if intro_summary:
            new_intro = Introduction(blog_id=new_blog.id, summary=intro_summary, images=intro_images)
            db.session.add(new_intro)
            db.session.commit()

            # Save Topics
            topics = introduction.get('topics', [])
            for topic_text in topics:
                new_topic = Topic(introduction_id=new_intro.id, topic=topic_text)
                db.session.add(new_topic)

        # Save Paragraphs
        paragraphs = data.get('paragraph', [])
        for para in paragraphs:
            order = para.get('order')
            title = para.get('title')
            content = para.get('content')
            images = para.get('images')
            new_paragraph = Paragraph(blog_id=new_blog.id, order=order, title=title, content=content, images=images)
            db.session.add(new_paragraph)
            db.session.commit()

            # Save Bullets
            bullets = para.get('bullets', [])
            for bullet in bullets:
                new_bullet = BulletPoint(paragraph_id=new_paragraph.id, point=bullet)
                db.session.add(new_bullet)

        # Save Resources
        resources = data.get('resources', [])
        for resource_url in resources:
            new_resource = Resource(blog_id=new_blog.id, url=resource_url)
            db.session.add(new_resource)

        # Save Acknowledgments
        acknowledgments = data.get('acknowledgments', [])
        for ack_text in acknowledgments:
            new_ack = Acknowledgment(blog_id=new_blog.id, text=ack_text)
            db.session.add(new_ack)

        db.session.commit()
        
        return jsonify({
            "status" : True,
            "blog_id" : new_blog.id,
            "message": "Blog created successfully"
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API route to retrieve all blogs
@app.route('/api/blogs', methods=['GET'])
def get_blogs():
    try:
        blogs = Blog.query.all()
        response = []
        for blog in blogs:
            introduction = Introduction.query.filter_by(blog_id=blog.id).first()
            topics = [topic.topic for topic in Topic.query.filter_by(introduction_id=introduction.id).all()] if introduction else []
            paragraphs = Paragraph.query.filter_by(blog_id=blog.id).all()
            paragraphs_response = []
            for para in paragraphs:
                bullets = [bullet.point for bullet in BulletPoint.query.filter_by(paragraph_id=para.id).all()]
                paragraphs_response.append({
                    "order": para.order,
                    "title": para.title,
                    "content": para.content,
                    "images": para.images,
                    "bullets": bullets
                })
            resources = [resource.url for resource in Resource.query.filter_by(blog_id=blog.id).all()]
            acknowledgments = [ack.text for ack in Acknowledgment.query.filter_by(blog_id=blog.id).all()]
            response.append({
                "id" : blog.id,
                "title": blog.title,
                "author": blog.author,
                "read_time": blog.read_time,
                "date": blog.date,
                "introduction": {
                    "summary": introduction.summary if introduction else "",
                    "images": introduction.images if introduction else "",
                    "topics": topics
                },
                "paragraph": paragraphs_response,
                "resources": resources,
                "acknowledgments": acknowledgments,
                "github_link": blog.github_link
            })
        return jsonify({
            "status" : True,
            "data" : response
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/blog/<int:blog_id>', methods=['GET'])
def get_blog_by_id(blog_id):
    try:
        blog = Blog.query.get(blog_id)
        if not blog:
            return jsonify({"error": "Blog not found"}), 404

        introduction = Introduction.query.filter_by(blog_id=blog.id).first()
        topics = [topic.topic for topic in Topic.query.filter_by(introduction_id=introduction.id).all()] if introduction else []
        paragraphs = Paragraph.query.filter_by(blog_id=blog.id).all()
        paragraphs_response = []
        for para in paragraphs:
            bullets = [bullet.point for bullet in BulletPoint.query.filter_by(paragraph_id=para.id).all()]
            paragraphs_response.append({
                "order": para.order,
                "title": para.title,
                "content": para.content,
                "images": para.images,
                "bullets": bullets
            })
        resources = [resource.url for resource in Resource.query.filter_by(blog_id=blog.id).all()]
        acknowledgments = [ack.text for ack in Acknowledgment.query.filter_by(blog_id=blog.id).all()]

        response = {
            "title": blog.title,
            "author": blog.author,
            "read_time": blog.read_time,
            "date": blog.date,
            "introduction": {
                "summary": introduction.summary if introduction else "",
                "images": introduction.images if introduction else "",
                "topics": topics
            },
            "paragraph": paragraphs_response,
            "resources": resources,
            "acknowledgments": acknowledgments,
            "github_link": blog.github_link
        }

        return jsonify({
            "status" : True,
            "data" : response
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API route to search blogs by keyword
@app.route('/api/blogs/search', methods=['GET'])
def search_blogs():
    try:
        keyword = request.args.get('keyword', '').lower()
        if not keyword:
            return jsonify({"status": False, "error": "Keyword is required"}), 400

        blogs = Blog.query.filter(
            Blog.title.ilike(f"%{keyword}%") |
            Blog.author.ilike(f"%{keyword}%") |
            Blog.github_link.ilike(f"%{keyword}%")
        ).all()

        response = []
        for blog in blogs:
            introduction = Introduction.query.filter_by(blog_id=blog.id).first()
            topics = [topic.topic for topic in Topic.query.filter_by(introduction_id=introduction.id).all()] if introduction else []
            paragraphs = Paragraph.query.filter_by(blog_id=blog.id).all()
            paragraphs_response = []
            for para in paragraphs:
                bullets = [bullet.point for bullet in BulletPoint.query.filter_by(paragraph_id=para.id).all()]
                paragraphs_response.append({
                    "order": para.order,
                    "title": para.title,
                    "content": para.content,
                    "images": para.images,
                    "bullets": bullets
                })
            resources = [resource.url for resource in Resource.query.filter_by(blog_id=blog.id).all()]
            acknowledgments = [ack.text for ack in Acknowledgment.query.filter_by(blog_id=blog.id).all()]
            response.append({
                "id": blog.id,
                "title": blog.title,
                "author": blog.author,
                "read_time": blog.read_time,
                "date": blog.date,
                "introduction": {
                    "summary": introduction.summary if introduction else "",
                    "images": introduction.images if introduction else "",
                    "topics": topics
                },
                "paragraph": paragraphs_response,
                "resources": resources,
                "acknowledgments": acknowledgments,
                "github_link": blog.github_link
            })

        return jsonify({
            "status": True,
            "data": response
        }), 200
    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
