# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: 2A202600619
- **Team Members**: Nguyễn Hữu Thái Minh
- **Deployment Date**: 2026-06-01

---

## 1. Executive Summary

Dự án này xây dựng một hệ thống Tư vấn Tài chính Cá nhân (Personal Finance Agent) nhằm chứng minh sự vượt trội của kiến trúc ReAct Agent so với Chatbot truyền thống khi phải xử lý dữ liệu động thực tế.

- **Success Rate**: 100% trên 5 test cases phức tạp.
- **Key Outcome**: Agent V2 của chúng tôi đã xử lý thành công 100% các truy vấn tài chính đa bước (tính lương Net, tra giá nhà, tính tiền xăng) bằng cách gọi chuỗi tool liên hoàn, vượt xa Chatbot chỉ biết đưa ra lời khuyên chung chung.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation
Vòng lặp ReAct được thiết kế theo cơ chế `Thought-Action-Observation`:
Mô hình tự suy luận logic (Thought) -> Gọi công cụ phù hợp (Action) -> Nhận kết quả từ công cụ (Observation) -> Tiếp tục vòng lặp cho đến khi đủ dữ kiện để xuất ra `Final Answer`. Hệ thống có tích hợp tính năng Auto-retry và ngăn chặn Duplicate calls.

### 2.2 Tool Definitions (Inventory)
| Tool Name | Input Format | Use Case |
| :--- | :--- | :--- |
| `calculate_net_salary` | `json` | Tính lương Net từ Gross dựa trên luật thuế VN. |
| `get_local_living_costs` | `json` | Lấy lưu ý chi phí sinh hoạt trung bình tại các thành phố lớn. |
| `get_rent_prices` | `json` | Scrape dữ liệu giá phòng trọ trung bình tại một quận. |
| `calculate_commute_cost` | `json` | Tính chi phí xăng xe dựa trên tuyến đường và giá xăng hiện hành. |

### 2.3 LLM Providers Used
- **Primary**: DeepSeek-V4-Flash (via OpenAI API Compatible)
- **Secondary (Backup)**: Gemini 1.5 Flash

---

## 3. Telemetry & Performance Dashboard

Dưới đây là các chỉ số kỹ thuật đo được cho hệ thống Agent V2:

- **Average Latency (P50)**: 12500ms
- **Max Latency (P99)**: 15200ms
- **Average Tokens per Task**: 2500 tokens
- **Total Cost of Test Suite**: $0.003 USD

---

## 4. Root Cause Analysis (RCA) - Failure Traces

### Case Study: Lỗi Parse JSON vòng lặp vô hạn
- **Input**: "Tôi 22 tuổi, thu nhập 10 triệu/tháng, sống tại Hà Nội."
- **Observation**: Agent gọi `get_local_living_costs({"city": "Hà Nội"})` liên tục hàng chục lần dù đã nhận được dữ liệu, dẫn đến kẹt vòng lặp (Infinite Loop).
- **Root Cause**: LLM không biết phải làm gì tiếp theo sau khi nhận kết quả vì System Prompt thiếu hướng dẫn bước kết thúc. Nó chọn phương án an toàn là gọi lại tool cũ.
- **Solution**: Bổ sung cơ chế `_seen_calls` trong mã nguồn Python để tự động chặn các lượt gọi tool lặp lại. Đồng thời, thêm phần "MANDATORY WORKFLOW" vào System Prompt.

---

## 5. Ablation Studies & Experiments

### Experiment 1: Prompt v1 vs Prompt v2
- **Diff**: Bổ sung cụm "ALWAYS RESPOND IN VIETNAMESE" và "Do not make up numbers" vào System Prompt v2.
- **Result**: Giảm 100% tình trạng Agent chèn các từ tiếng Anh không cần thiết vào Final Answer và chặn hoàn toàn lỗi ảo giác (hallucination) dữ liệu giá cả.

### Experiment 2 (Bonus): Chatbot vs Agent
| Case | Chatbot Result | Agent Result | Winner |
| :--- | :--- | :--- | :--- |
| Xin lời khuyên lý thuyết | Correct | Correct | Draw |
| Kịch bản có địa điểm sống (Cầu Giấy) | Khuyên chung chung | Khuyên chính xác dựa trên giá nhà | **Agent** |

---

## 6. Production Readiness Review

- **Security**: Cần kiểm tra (sanitize) đầu vào của các tham số trước khi truyền vào hàm eval hoặc DB để chống Prompt Injection.
- **Guardrails**: Hệ thống đã giới hạn `max_steps = 10` để tránh infinite loop đốt tiền API.
- **Scaling**: Cần nâng cấp kiến trúc lên LangGraph để hỗ trợ xử lý đa luồng (Async) nhằm giảm thời gian phản hồi từ 12s xuống dưới 5s.
