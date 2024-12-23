from flask import Flask, render_template

app = Flask(__name__)

# 路由到主页
@app.route('/')
def home():
    return '<h1>欢迎来到 Flask 简单网页！</h1><p>这是主页内容。</p>'

# 路由到另一个页面
@app.route('/about')
def about():
    return '<h1>关于页面</h1><p>这是关于我们的信息。</p>'

if __name__ == '__main__':
    app.run(debug=True)