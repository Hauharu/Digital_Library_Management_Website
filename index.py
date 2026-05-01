import eventlet
eventlet.monkey_patch()
import os
from app import create_app, db, socketio
from sqlalchemy import text
from datetime import datetime

app = create_app()

with app.app_context():
    db.create_all()
    
    inspector = db.inspect(db.engine)
    columns = [c['name'] for c in inspector.get_columns('book')]
    if 'view_count' not in columns:
        db.session.execute(text("ALTER TABLE book ADD COLUMN view_count INTEGER DEFAULT 0"))
    
    slip_columns = [c['name'] for c in inspector.get_columns('borrow_slip')]
    if 'return_requested' not in slip_columns:
        db.session.execute(text("ALTER TABLE borrow_slip ADD COLUMN return_requested BOOLEAN NOT NULL DEFAULT FALSE"))
    db.session.commit()

    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        from app.services.semantic_search_service import SemanticSearchService
        print("--- Đang khởi động AI... ---")
        try:
            SemanticSearchService.load_embeddings()
            print("--- AI đã sẵn sàng! ---")
        except Exception as e:
            print(f"Lỗi khởi động AI: {e}")

if __name__ == '__main__':
    socketio.run(app, debug=True, host='127.0.0.1', port=5000)
