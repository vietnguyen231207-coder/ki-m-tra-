# Nguyễn Việt Insight — Hệ Thống AI Thẩm Định Dữ Liệu & Đề Xuất Chiến Lược (RFQ AI Agent)

Hệ thống AI tiếp nhận, làm sạch dữ liệu, thẩm định báo giá và phân tích kịch bản thương mại đa chiều (Human-In-The-Loop).

---

## 🌟 Tính Năng Nổi Bật

- **Quy trình 6 Chặng Chuẩn Hóa:**
  1. **Chặng 01 · Tiếp Nhận Tệp:** Tự động phát hiện cấu trúc bảng, nhận diện delimiter (`,`, `;`, `\t`), hỗ trợ định dạng Excel (`.xlsx`, `.xls`), CSV (`.csv`) và Word (`.docx`).
  2. **Chặng 02 · AI Làm Sạch Dữ Liệu:** Chuẩn hóa kiểu dữ liệu, kiểm tra ngày tháng năm, đơn giá, số lượng, loại bỏ rủi ro sai lệch.
  3. **Chặng 03 · Duyệt & Chỉnh Sửa (HITL):** Cho phép chuyên viên sửa trực tiếp số lượng, đơn giá trên bảng hoặc nhập câu lệnh điều chỉnh tự động qua AI.
  4. **Chặng 04 · Phân Tích Đa Chiều:** Đánh giá tính tuân thủ kỹ thuật, tính toán COGS, tiến độ và rủi ro.
  5. **Chặng 05 · Báo Cáo & Biểu Đồ:** Trực quan hóa tài chính, cơ cấu chi phí, radar năng lực và 3 kịch bản chào thầu (Cơ sở, Tối ưu lợi nhuận, Cạnh tranh).
  6. **Chặng 06 · Nghiệm Thu & Xuất Bản:** Mô phỏng biên độ chiết khấu và xuất hồ sơ Word (`.docx`) & bảng tính BOQ (`.csv`).

- **Thích Ứng Mọi Bộ Dữ Liệu (Adaptive Schema Engine):**
  - Bảng hợp đồng dịch vụ / doanh thu định kỳ.
  - Bảng dự toán mua sắm vật tư.
  - Bảng thiết bị viễn thông, CNTT & hạ tầng.
  - Bảng đơn hàng & doanh số bán hàng.

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy Cục Bộ (Localhost)

### 1. Yêu Cầu Môi Trường
- Python 3.9+ trở lên.

### 2. Cài Đặt Thư Viện
```bash
pip install -r requirements.txt
```

### 3. Khởi Chạy Ứng Dụng
```bash
python app.py
```
Truy cập hệ thống tại: **[http://localhost:8080](http://localhost:8080)**

---

## 📁 Cấu Trúc Thư Mục

```text
├── api/
│   └── index.py             # Serverless handler (hỗ trợ Vercel deployment)
├── backend/
│   ├── agent_engine.py      # Core AI Agent & quy trình phân tích nghiệp vụ
│   ├── export_docs.py       # Xuất báo cáo tài liệu Word (.docx)
│   ├── gemini_service.py    # Tích hợp dịch vụ AI nâng cao
│   └── parsers.py           # Bộ đọc & ánh xạ dữ liệu thông minh (CSV, XLSX, DOCX)
├── data/
│   ├── sample_rfqs/         # Các bộ hồ sơ mẫu chuẩn test nhanh
│   ├── policies_and_schedule.json
│   └── solution_catalog.csv
├── exports/                 # Thư mục chứa tệp xuất báo cáo
├── static/
│   └── index.html           # Bản sao tĩnh tối ưu hóa
├── app.py                   # HTTP Web Server cục bộ (port 8080)
├── index.html               # Giao diện chính 6 Chặng
├── requirements.txt         # Danh mục thư viện Python
├── vercel.json              # Cấu hình triển khai đám mây Vercel
├── .gitignore
└── README.md
```

---

## 📄 Bản Quyền
Dự án được xây dựng và phát triển bởi **Nguyễn Việt Insight**.
