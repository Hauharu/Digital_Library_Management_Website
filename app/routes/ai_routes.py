from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
import google.generativeai as genai
import os
from app.models import Book, Category, Review
from app.services.semantic_search_service import SemanticSearchService
from sqlalchemy import func

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message')
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    # 1. Tự động tìm kiếm sách
    search_results = ""
    search_keywords = ['tìm', 'sách', 'có cuốn', 'mượn', 'đọc', 'muốn', 'gợi ý', 'hư hỏng', 'mất']
    
    # Tìm kiếm sách theo từ khóa
    try:
        found_books = SemanticSearchService.search(user_message, limit=5)
        if found_books:
            search_results += "Kết quả tìm kiếm từ kho sách:\n"
            for b in found_books:
                search_results += f"- {b.title} (ID: {b.id}) của {b.author}\n"
    except Exception:
        pass

    # 2. Lấy danh sách sách nổi bật
    top_viewed = Book.query.order_by(Book.view_count.desc()).limit(5).all()
    
    # Lấy sách có đánh giá cao nhất (giả định có property average_rating hoặc tính toán)
    # Ở đây chúng ta lấy top 5 sách bất kỳ có điểm cao
    top_rated = Book.query.join(Review).group_by(Book.id).order_by(func.avg(Review.rating).desc()).limit(5).all()
    if not top_rated: # Fallback nếu chưa có đánh giá nào
        top_rated = top_viewed

    # 3. Định nghĩa bộ quy tắc thư viện mở rộng
    library_rules = f"""
    - Phí phạt trả muộn: 5,000 VNĐ / ngày.
    - Thời gian mượn mặc định: 14 ngày.
    - Sách hư hỏng hoặc làm mất: Người dùng phải bồi thường theo quy định (tùy mức độ hư hỏng, tối đa 100% giá trị sách). Hãy khuyên người dùng liên hệ thủ thư để lập biên bản sự cố.
    - Cách mượn sách: Tìm sách -> Nhấn vào xem chi tiết -> Nhấn nút 'Mượn sách'.
    - Thanh toán: Hỗ trợ VNPay, PayPal và Tiền mặt.
    
    DANH SÁCH SÁCH XEM NHIỀU NHẤT (Top Views):
    {", ".join([f"{b.title} (ID: {b.id})" for b in top_viewed])}
    
    DANH SÁCH SÁCH ĐÁNH GIÁ CAO NHẤT (Top Rated):
    {", ".join([f"{b.title} (ID: {b.id})" for b in top_rated])}
    """

    prompt = f"""
    Bạn là 'Trợ lý thông minh OUBOOK' của hệ thống Thư viện số OU.
    
    KIẾN THỨC HỆ THỐNG:
    {library_rules}
    
    DỮ LIỆU TÌM KIẾM THEO YÊU CẦU:
    {search_results}

    YÊU CẦU TRẢ LỜI:
    1. Trình bày đẹp mắt bằng Markdown.
    2. Nếu nhắc đến sách cụ thể, LUÔN LUÔN đính kèm link: [Tên Sách](/book-detail/ID).
    3. Nếu người dùng hỏi về hư hỏng/mất sách, hãy giải thích quy trình bồi thường và khuyên gặp thủ thư.
    4. Nếu họ muốn gợi ý sách, hãy dùng danh sách 'SÁCH XEM NHIỀU NHẤT' và 'SÁCH ĐÁNH GIÁ CAO NHẤT'.
    
    Người dùng hỏi: {user_message}
    """

    # Cấu hình AI
    try:
        all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        available_models = [m for m in all_models if '2.5' in m]
        if not available_models:
            available_models = [all_models[0]]
    except Exception:
        available_models = ['models/gemini-2.5-flash', 'models/gemini-2.5-pro']

    api_key = current_app.config.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)

    for m_name in available_models:
        try:
            model = genai.GenerativeModel(m_name)
            response = model.generate_content(prompt)
            return jsonify({'reply': response.text})
        except Exception:
            continue
            
    return jsonify({'reply': "Xin lỗi, mình gặp chút trục trặc. Bạn thử lại sau nhé!"})
