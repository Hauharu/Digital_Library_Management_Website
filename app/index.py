from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def index():
    featured_books = [
        {"title": "Fundamentals of database systems", "author": "Elmasri, Ramez", "image": "/static/images/sachmau.png"},
        {"title": "Computer networks : a systems approach", "author": "Peterson, Larry L.", "image": "/static/images/sachmau.png"},
        {"title": "Mining of massive datasets", "author": "Leskovec, Jure", "image": "/static/images/sachmau.png"},
        {"title": "Quản trị mạng", "author": "Lưu Quang Phương", "image": "/static/images/sachmau.png"},
        {"title": "Java how to program : early objects", "author": "Deitel, Paul", "image": "/static/images/sachmau.png"},
        {"title": "Mathematics for computer graphics", "author": "Vince, John", "image": "/static/images/sachmau.png"},
        {"title": "The Road to React", "author": "Wieruch, Robin", "image": "/static/images/sachmau.png"},
        {"title": "Giáo trình thiết kế web", "author": "Lê Viết Tuấn", "image": "/static/images/sachmau.png"},
    ]
    return render_template('index.html', featured_books=featured_books)

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('login.html')

# Mock data để xem thử giao diện chi tiết sách
class MockAuthor:
    name = "Nguyễn Nhật Ánh"
    
    def __str__(self):
        return self.name

class MockCategory:
    name = "Truyện dài"
    
    def __str__(self):
        return self.name

class MockBook:
    book_id = 1
    title = "Mắt Biếc (Bản Demo)"
    image = "/static/images/sachmau.png"
    status = "available"
    author = MockAuthor()
    category = MockCategory()
    publication_info = "NXB Trẻ - 2018"
    language = "Tiếng Việt"
    isbn = "978-604-1-13278-5"
    quantity = 5
    library_location = "Kệ A - Tầng 2"
    weight = 300
    size = "13 x 20 cm"
    page_count = 300
    cover_type = "Bìa mềm"
    description = "Mắt biếc là một tác phẩm được nhiều người yêu thích của nhà văn Nguyễn Nhật Ánh. Cuốn sách kể về tình yêu trong sáng nhưng đầy tiếc nuối của Ngạn dành cho Hà Lan - cô bạn gái có đôi mắt tuyệt đẹp."

class MockUser:
    is_authenticated = False

@app.route('/demo-book')
def demo_book():
    related_books = [
        {"title": "Đắc Nhân Tâm", "image": "/static/images/sachmau.png"},
        {"title": "Nhà Giả Kim", "image": "/static/images/sachmau.png"},
        {"title": "Tuổi trẻ đáng giá bao nhiêu", "image": "/static/images/sachmau.png"},
        {"title": "Tôi thấy hoa vàng trên cỏ xanh", "image": "/static/images/sachmau.png"},
        {"title": "Cây chuối non đi giày xanh", "image": "/static/images/sachmau.png"},
        {"title": "Làm bạn với bầu trời", "image": "/static/images/sachmau.png"},
        {"title": "Cho tôi xin một vé đi tuổi thơ", "image": "/static/images/sachmau.png"},
        {"title": "Có hai con mèo ngồi bên cửa sổ", "image": "/static/images/sachmau.png"},
    ]
    return render_template('book_detail.html', book=MockBook(), current_user=MockUser(), user_state=None, related_books=related_books)

# Dummy routes to prevent url_for errors in templates during demo
@app.route('/request_borrow/<int:book_id>', endpoint='main.request_borrow')
def request_borrow(book_id): pass

@app.route('/request_list', endpoint='user.request_list')
def request_list(): pass

if __name__ == '__main__':
    app.run(debug=True)
