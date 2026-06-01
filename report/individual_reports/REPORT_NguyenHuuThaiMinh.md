# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Hữu Thái Minh
- **Student ID**: 2A202600619
- **Date**: 2026-06-01

---

## I. Technical Contribution (15 Points)

Trong phòng thí nghiệm này, tôi phụ trách xây dựng kiến trúc Agent, kho dữ liệu Tools và giao diện web.

- **Modules Implementated**: 
  - `src/agent/agent_v2.py` (Vòng lặp ReAct nâng cao).
  - `src/tools/tax_calculator.py`, `src/tools/living_costs.py`, v.v...
  - `web/app.js` và `web/index.html` (Giao diện hiển thị Metrics, Trace).
- **Code Highlights**: 
  - Viết logic `_seen_calls` trong `agent_v2.py` để chặn gọi lại cùng một tool.
  - Viết hàm `renderMeta()` trong `app.js` để render Thẻ Thống kê (Latency, Tokens, Tools) dưới dạng UI trực quan.
- **Documentation**: Hệ thống tích hợp trực tiếp vào UI với nút "Xem Lịch sử Tư duy" giúp người dùng xem chi tiết vòng lặp Thought-Action-Observation của hệ thống bên dưới lớp Backend Flask.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: LLM gọi tên công cụ sai định dạng JSON. LLM xuất ra chuỗi `Action: get_rent_prices("Cầu Giấy")` thay vì `{"tool": "get_rent_prices", "args": {"district": "Cầu Giấy"}}`.
- **Log Source**: File `telemetry/logger.py` ghi nhận: `[PARSE ERROR] JSON decode failed`.
- **Diagnosis**: Do System Prompt thiếu ví dụ cụ thể (Few-shot), mô hình bị nhầm lẫn giữa cú pháp gọi hàm (Function Calling) của Python và định dạng JSON bắt buộc của bài lab.
- **Solution**: Cập nhật lại System Prompt bằng cách thêm khối `=== FEW-SHOT EXAMPLES ===` minh họa rõ cú pháp JSON chuẩn. Đồng thời, tôi viết thêm đoạn code `auto-retry` trong `agent_v2.py` để tự động đẩy lỗi `[PARSE ERROR]` lại cho LLM tự sửa.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: Khối `Thought` giúp LLM chia nhỏ bài toán. Khi gặp truy vấn "Lương 10tr trọ Cầu Giấy đi làm Thanh Xuân", LLM biết phân tích thành 3 bài toán con: Tính Net -> Giá phòng -> Xăng xe. Điều này Chatbot không bao giờ làm được nếu không có `Thought`.
2. **Reliability**: Trong các trường hợp truy vấn cực kỳ đơn giản (như "Định nghĩa quản lý tài chính"), Agent V2 có thể trả lời chậm hơn Chatbot rất nhiều (15s so với 2s) do phải chạy qua vòng lặp kiểm tra tool, gây ảnh hưởng đến UX.
3. **Observation**: Môi trường phản hồi rất quan trọng. Khi tool trả về lỗi "Không tìm thấy dữ liệu cho thành phố này", Agent V2 có thể đọc `Observation` đó và tự động xuất ra câu xin lỗi "Tôi không có dữ liệu cho vùng này" thay vì nhắm mắt bịa ra con số ảo giác.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Nâng cấp lên kiến trúc Vector DB (như ChromaDB) để tự động RAG các tool liên quan thay vì nhét toàn bộ mô tả 100 tools vào System Prompt.
- **Safety**: Xây dựng một "Supervisor Agent" trung gian để duyệt lại kế hoạch tài chính (Final Answer) trước khi hiển thị cho người dùng, đảm bảo các lời khuyên không vi phạm đạo đức hoặc luật pháp.
- **Performance**: Sử dụng Queue (như Celery/RabbitMQ) hoặc `asyncio` để cho phép Agent gọi 2 tools không phụ thuộc nhau (VD: tra giá trọ và tính tiền xăng) cùng một lúc.
