"""
Application: app.py
Máy chủ Web & API Trung tâm Điều hành AI Agent Đánh giá Yêu cầu Chào giá - Nguyễn Việt Insight
Hỗ trợ cả môi trường Cục bộ (localhost:8080) và Đám mây Vercel (WSGI / Serverless).
"""

import sys
import os
import io
import json
import urllib.parse
from http.server import HTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.handler import (
    NguyenVietRequestHandler,
    extract_input_data,
    agent,
    latest_states,
    cleaning_sessions,
    export_requirements_matrix_docx,
    export_official_quotation_docx,
    export_approval_form_docx,
    gemini_agent,
    get_file_path,
    PORT
)

# ----------------------------------------------------------------
# 1. WSGI Callable (Chuẩn quốc tế PEP 3333 cho Vercel Python Runtime)
# ----------------------------------------------------------------
def app(environ, start_response):
    method = environ.get('REQUEST_METHOD', 'GET')
    path = environ.get('PATH_INFO', '/')
    query_string = environ.get('QUERY_STRING', '')
    query = urllib.parse.parse_qs(query_string)

    cors_headers = [
        ('Access-Control-Allow-Origin', '*'),
        ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
        ('Access-Control-Allow-Headers', 'Content-Type'),
        ('Cache-Control', 'no-cache, no-store, must-revalidate'),
    ]

    # Xử lý CORS Preflight
    if method == 'OPTIONS':
        start_response('200 OK', [('Content-Type', 'text/plain')] + cors_headers)
        return [b'']

    # Phục vụ trang HTML chính
    if path == '/' or path == '/index.html':
        index_candidates = [
            get_file_path('index.html'),
            os.path.join(BASE_DIR, 'index.html'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html'),
            os.path.join(os.getcwd(), 'index.html'),
            'index.html',
            get_file_path('static/index.html'),
            os.path.join(BASE_DIR, 'static', 'index.html'),
            'static/index.html'
        ]
        index_file = None
        for candidate in index_candidates:
            if candidate and os.path.exists(candidate):
                index_file = candidate
                break

        if not index_file:
            start_response('500 Internal Server Error', [('Content-Type', 'text/plain; charset=utf-8')] + cors_headers)
            return [b"Khong tim thay tap tin index.html tren may chu."]

        try:
            with open(index_file, 'rb') as f:
                content = f.read()
            headers = [
                ('Content-Type', 'text/html; charset=utf-8'),
                ('Content-Length', str(len(content)))
            ] + cors_headers
            start_response('200 OK', headers)
            return [content]
        except Exception as e:
            start_response('500 Internal Server Error', [('Content-Type', 'text/plain; charset=utf-8')] + cors_headers)
            return [f"Lỗi đọc index.html: {str(e)}".encode('utf-8')]

    # GET: Tải tệp DOCX / CSV
    if method == 'GET' and path.startswith('/api/download/'):
        doc_type = path.replace('/api/download/', '').strip()
        rfq_code = query.get('rfq_code', ['NV-2026-ALPHA-01'])[0]
        state = latest_states.get(rfq_code) or (list(latest_states.values())[-1] if latest_states else {})

        try:
            if doc_type == 'compliance':
                buf = export_requirements_matrix_docx(state)
                mime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                fn = f"NguyenViet_ComplianceMatrix_{rfq_code}.docx"
            elif doc_type == 'quotation':
                buf = export_official_quotation_docx(state)
                mime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                fn = f"NguyenViet_OfficialQuotation_{rfq_code}.docx"
            elif doc_type == 'approval':
                buf = export_approval_form_docx(state)
                mime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                fn = f"NguyenViet_ApprovalForm_{rfq_code}.docx"
            elif doc_type == 'boq_csv':
                items = state.get('information_extraction', {}).get('extracted_items', [])
                csv_buf = io.StringIO()
                csv_buf.write("STT,Tên Thiết Bị / Hàng Hóa,Chủng Loại,Số Lượng,Đơn Vị,Đơn Giá (VND),Thành Tiền (VND)\n")
                for it in items:
                    csv_buf.write(f"{it.get('stt')},\"{it.get('item_name')}\",\"{it.get('category','Thiết bị')}\",{it.get('quantity',1)},\"{it.get('unit','Bộ')}\",{it.get('unit_price',0)},{it.get('total_price',0)}\n")
                buf = io.BytesIO(csv_buf.getvalue().encode('utf-8-sig'))
                mime = 'text/csv; charset=utf-8'
                fn = f"BOQ_NguyenViet_{rfq_code}.csv"
            else:
                start_response('404 Not Found', [('Content-Type', 'text/plain')] + cors_headers)
                return [b'Document type not found']

            data = buf.getvalue()
            headers = [
                ('Content-Type', mime),
                ('Content-Disposition', f'attachment; filename="{fn}"'),
                ('Content-Length', str(len(data)))
            ] + cors_headers
            start_response('200 OK', headers)
            return [data]
        except Exception as e:
            err = json.dumps({'error': f"Lỗi xuất file: {str(e)}"}).encode('utf-8')
            start_response('500 Internal Server Error', [('Content-Type', 'application/json')] + cors_headers)
            return [err]

    # POST APIs
    if method == 'POST':
        content_type = environ.get('CONTENT_TYPE', '')
        try:
            content_length = int(environ.get('CONTENT_LENGTH', 0))
        except (ValueError, TypeError):
            content_length = 0
        body = environ['wsgi.input'].read(content_length)

        # 1. API: Tiếp nhận tệp và Làm sạch dữ liệu
        if path == '/api/clean-data':
            try:
                parsed_data, source_name = extract_input_data(content_type, body)
                if not parsed_data:
                    res = json.dumps({'error': 'Không nhận diện được nội dung hoặc định dạng tập tin đầu vào.', 'return_to_step': 1}).encode('utf-8')
                    start_response('400 Bad Request', [('Content-Type', 'application/json')] + cors_headers)
                    return [res]

                phase1 = agent.phase1_receipt_and_classification(parsed_data)
                rfq_code = phase1['rfq_code']
                dataset_type = parsed_data.get('dataset_type', 'Bảng Doanh Thu & Dữ Liệu')
                if dataset_type:
                    phase1['project_type'] = dataset_type
                if parsed_data.get('customer_name'):
                    phase1['customer_name'] = parsed_data['customer_name']
                elif source_name:
                    phase1['customer_name'] = source_name

                phase2a = agent.phase2a_extract_information(parsed_data, phase1)
                items = phase2a.get('extracted_items', [])

                cleaned_items = []
                errors = []
                if not items or len(items) == 0:
                    errors.append('Không tìm thấy bất kỳ dòng dữ liệu nào trong tệp.')

                for idx, it in enumerate(items):
                    stt = str(it.get('stt') or (idx + 1)).strip()
                    name = str(it.get('item_name') or '').strip()
                    qty = it.get('quantity', 1)
                    unit = str(it.get('unit') or 'Bộ').strip()
                    specs = str(it.get('specs') or '').strip()
                    date_val = str(it.get('date') or '').strip()
                    u_price = float(it.get('unit_price', 0.0))
                    t_price = float(it.get('total_price', 0.0))

                    cleaned_items.append({
                        'stt': stt,
                        'date': date_val,
                        'item_name': name,
                        'category': it.get('category') or 'Hạng mục Doanh nghiệp',
                        'quantity': qty,
                        'unit': unit,
                        'specs': specs or (f"Ngày ghi nhận: {date_val}" if date_val else 'Tiêu chuẩn kỹ thuật Nguyễn Việt'),
                        'unit_price': u_price,
                        'total_price': t_price,
                        'status': it.get('status', 'Hợp lệ')
                    })

                phase2a['extracted_items'] = cleaned_items
                cleaning_sessions[rfq_code] = {
                    'phase1': phase1,
                    'phase2a': phase2a,
                    'parsed_data': parsed_data,
                    'source_name': source_name
                }

                res_payload = {
                    'success': True,
                    'rfq_code': rfq_code,
                    'source_name': source_name,
                    'dataset_type': dataset_type,
                    'customer_name': phase1.get('customer_name', 'Khách hàng Doanh nghiệp'),
                    'items': cleaned_items
                }
                res = json.dumps(res_payload, ensure_ascii=False).encode('utf-8')
                start_response('200 OK', [('Content-Type', 'application/json; charset=utf-8')] + cors_headers)
                return [res]
            except Exception as e:
                res = json.dumps({'success': False, 'error': f"Lỗi làm sạch dữ liệu: {str(e)}"}).encode('utf-8')
                start_response('500 Internal Server Error', [('Content-Type', 'application/json')] + cors_headers)
                return [res]

        # 2. API: Phân tích nghiệp vụ AI
        elif path == '/api/analyze':
            try:
                payload = json.loads(body.decode('utf-8'))
                rfq_code = payload.get('rfq_code', '')
                session = cleaning_sessions.get(rfq_code)
                if not session:
                    res = json.dumps({'error': 'Không tìm thấy phiên làm sạch dữ liệu. Vui lòng nạp lại file.'}).encode('utf-8')
                    start_response('400 Bad Request', [('Content-Type', 'application/json')] + cors_headers)
                    return [res]

                phase1 = session['phase1']
                phase2a = session['phase2a']
                if 'approved_items' in payload and payload['approved_items']:
                    phase2a['extracted_items'] = payload['approved_items']

                phase2b = agent.phase2b_match_solution_and_capability(phase2a, phase1)
                phase2c = agent.phase2c_commercial_and_financial(phase2a, phase2b, phase1)
                phase2d = agent.phase2d_risk_and_scoring(phase2a, phase2b, phase2c, phase1)

                state = {
                    'rfq_code': rfq_code,
                    'receipt_and_classification': phase1,
                    'information_extraction': phase2a,
                    'solution_matching': phase2b,
                    'commercial_evaluation': phase2c,
                    'risk_and_decision': phase2d
                }
                latest_states[rfq_code] = state

                res = json.dumps({'success': True, 'rfq_code': rfq_code, 'state': state}, ensure_ascii=False).encode('utf-8')
                start_response('200 OK', [('Content-Type', 'application/json; charset=utf-8')] + cors_headers)
                return [res]
            except Exception as e:
                res = json.dumps({'error': f"Lỗi phân tích: {str(e)}"}).encode('utf-8')
                start_response('500 Internal Server Error', [('Content-Type', 'application/json')] + cors_headers)
                return [res]

    start_response('404 Not Found', [('Content-Type', 'text/plain')] + cors_headers)
    return [b'Endpoint not found']


# ----------------------------------------------------------------
# 2. BaseHTTPRequestHandler cho Vercel / Local Server tương thích ngược
# ----------------------------------------------------------------
class handler(NguyenVietRequestHandler):
    """Entrypoint tương thích ngược cho Vercel Serverless Function."""
    pass

application = app


# ----------------------------------------------------------------
# 3. Chạy cục bộ (Localhost:8080)
# ----------------------------------------------------------------
def run_server():
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, NguyenVietRequestHandler)
    print("================================================================", flush=True)
    print(f" Nguyễn Việt Insight Server đang hoạt động tại cổng {PORT}", flush=True)
    print(f" URL: http://localhost:{PORT}", flush=True)
    print("================================================================", flush=True)
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
