<h2 align="center">
    <a href="https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin">
    🎓 Faculty of Information Technology (DaiNam University)
    </a>
</h2>

<h2 align="center">
LƯU TRỮ LỊCH SỬ PHÂN LOẠI SẢN PHẨM BẰNG BLOCKCHAIN
</h2>

<div align="center">

<p align="center">
<img src="./aiotlab_logo.png" width="170"/>
<img src="./fitdnu_logo.png" width="180"/>
<img src="./dnu_logo.png" width="200"/>
</p>

[![AIoTLab](https://img.shields.io/badge/AIoTLab-green?style=for-the-badge)](https://www.facebook.com/DNUAIoTLab)
[![Faculty of Information Technology](https://img.shields.io/badge/Faculty%20of%20Information%20Technology-blue?style=for-the-badge)](https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin)
[![DaiNam University](https://img.shields.io/badge/DaiNam%20University-orange?style=for-the-badge)](https://dainam.edu.vn)

</div>

---

## 📌 Poster dự án

<div align="center">
<img src="./Poster_Blockchain.JPG" width="850"/>
</div>

---

# 📖 Giới thiệu đề tài

**Lưu trữ lịch sử phân loại sản phẩm bằng Blockchain** là hệ thống kết hợp giữa **Thị giác máy tính (Computer Vision)**, **Trí tuệ nhân tạo (AI)** và **Blockchain Ethereum** nhằm xây dựng một nền tảng giám sát và truy xuất nguồn gốc dữ liệu phân loại sản phẩm một cách minh bạch và bất biến.

Hệ thống sử dụng camera để thu nhận hình ảnh sản phẩm, áp dụng mô hình YOLOv8 kết hợp OpenCV để phát hiện vật thể và nhận diện màu sắc. Sau khi phân tích, dữ liệu sẽ được lưu đồng thời vào SQLite và Smart Contract trên Blockchain thông qua Web3.py.

🎯 **Mục tiêu của hệ thống**

* Tự động nhận diện và phân loại sản phẩm theo màu sắc.
* Hỗ trợ cánh tay robot Arduino thực hiện gắp và phân loại.
* Lưu trữ nhật ký phân loại lên Blockchain Ethereum cục bộ.
* Đảm bảo dữ liệu không thể chỉnh sửa hoặc giả mạo.
* Hỗ trợ truy xuất lịch sử phân loại và thống kê trực quan.

---

# ⚙️ Tính năng nổi bật

* 📷 Realtime Webcam Stream.
* 🎯 Phát hiện vật thể bằng YOLOv8 hoặc Custom Model.
* 🎨 Nhận diện 5 màu mục tiêu:

  * Đỏ
  * Xanh lá
  * Xanh dương
  * Vàng
  * Cam
* 🧠 Phân tích màu bằng HSV Threshold và OpenCV.
* 🚫 Loại bỏ màu nền và các màu không mong muốn.
* 📊 Dashboard realtime với Chart.js.
* 🗂️ Lưu lịch sử SQLite.
* 📄 Export dữ liệu CSV.
* 🔊 Voice Alert khi phát hiện sai màu.
* ⛓️ Ghi dữ liệu lên Local Blockchain Ganache/Ethereum.
* 🤖 Hỗ trợ điều khiển cánh tay robot Arduino Nano.

---

# 🖥️ Kiến trúc hệ thống

## 🎨 Giao diện người dùng (UI)

* Dashboard Dark Mode.
* Glassmorphism Design.
* Hiển thị webcam realtime.
* Hiển thị Bounding Box.
* Biểu đồ thống kê màu sắc.
* Trạng thái Blockchain.

## 🧠 Module xử lý AI

* YOLOv8 Object Detection.
* OpenCV Image Processing.
* HSV Color Detection.
* Center Crop Analysis.
* Morphology Noise Removal.
* RGB & HSV Extraction.

## 🗄️ Module lưu trữ

* SQLite Database.
* CSV Export.
* Blockchain Ledger.

## 🤖 Module Robot

* Arduino Nano.
* Servo SG90.
* Điều khiển Pick & Place.
* Giao tiếp Serial COM.

---

# 🔄 Quy trình hoạt động

1. Camera thu nhận hình ảnh sản phẩm.

2. YOLOv8 phát hiện vật thể.

3. Crop vùng trung tâm của Bounding Box.

4. Chuyển đổi ảnh sang không gian màu HSV.

5. Tính toán tỷ lệ màu hợp lệ.

6. Xác định màu có tỷ lệ lớn nhất.

7. So sánh với màu chuẩn.

8. Sinh kết quả:

* OK
* NG
* Ignored

9. Lưu dữ liệu vào SQLite.

10. Gửi Transaction qua Web3.py.

11. Smart Contract ghi dữ liệu lên Blockchain.

12. Dashboard cập nhật trạng thái và Tx Hash.

---

# ⛓️ Tích hợp Blockchain

Luồng Blockchain:

```
Camera
   ↓
YOLO + OpenCV
   ↓
Color Detection
   ↓
SQLite Database
   ↓
Web3.py
   ↓
Ganache Ethereum
   ↓
Smart Contract
   ↓
Blockchain Ledger
```

Thông tin lưu trữ:

* Product ID
* Object Name
* Detected Color
* RGB Value
* HSV Value
* Result (OK / NG)
* Confidence
* Timestamp
* Result Hash

---

# 📂 Cấu trúc Project

```text
.
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── models/
├── detection/
├── analytics/
├── database/
├── blockchain/
│   ├── contracts/
│   ├── abi/
│   └── scripts/
├── templates/
├── static/
├── uploads/
├── outputs/
├── exports/
└── reports/
```

---

# 🔧 Công nghệ sử dụng

## Ngôn ngữ lập trình

* Python
* Solidity

## Thư viện

* OpenCV
* Ultralytics YOLOv8
* NumPy
* Flask
* Web3.py
* SQLite3
* Chart.js

## Công cụ phát triển

* Visual Studio Code
* Git & GitHub
* Ganache
* Remix IDE

## Phần cứng

* Webcam
* Arduino Nano
* Servo SG90
* Cánh tay Robot

## Hệ điều hành

* Windows 10
* Windows 11

---

# 🚀 Hướng dẫn cài đặt

### Clone Project

```bash
git clone https://github.com/TruongDev10/Blockchain-Product-Classification.git
```

### Di chuyển vào thư mục

```bash
cd Blockchain-Product-Classification
```

### Tạo môi trường ảo

```bash
python -m venv .venv
```

### Kích hoạt

Windows

```bash
.venv\Scripts\activate
```

Linux / Mac

```bash
source .venv/bin/activate
```

### Cài đặt thư viện

```bash
pip install -r requirements.txt
```

### Khởi tạo Database

```bash
python database/init_db.py
```

### Chạy hệ thống

```bash
python app.py
```

Mở trình duyệt:

```text
http://127.0.0.1:5000
```

---

# 🔗 Kết nối Blockchain

### Chạy Ganache

RPC:

```text
http://127.0.0.1:7545
```

Chain ID:

```text
1337
```

### Deploy Smart Contract

```bash
python blockchain/scripts/deploy_contract.py
```

Sau khi deploy thành công:

```text
Contract deployed
Address : 0x...
Tx Hash : 0x...
```

Nhập Contract Address vào Dashboard và nhấn:

**Kết nối Blockchain**

---

# 🤖 Điều khiển Robot thật

Nạp Sketch Arduino:

```text
arduino/robot_arm_camera_pick/robot_arm_camera_pick.ino
```

Khởi động:

```powershell
$env:ROBOT_SERIAL_ENABLED="1"
$env:ROBOT_SERIAL_PORT="COM3"
$env:ROBOT_SERIAL_BAUDRATE="9600"

python run_server.py
```

Lệnh gửi tới Arduino:

```text
PICK <x> <y> <color> <status>
```

Ví dụ:

```text
PICK 150 110 red valid
```

---

# 📷 Hình ảnh minh họa

<p align="center">
<img src="./giao diện.jpg" width="700"/>
</p>

<p align="center">
<em>Giao diện Dashboard</em>
</p>

<p align="center">
<img src="./kết nối Block.jpg" width="700"/>
</p>

<p align="center">
<em>Kết nối Blockchain</em>
</p>

<p align="center">
<img src="./assets/images/robot.png" width="700"/>
</p>

<p align="center">
<em>Cánh tay Robot phân loại</em>
</p>

---

# 👨‍💻 Người thực hiện

* **Bùi Văn Trường**

* Chuyên ngành: Công nghệ Thông tin

* Trường Đại học Đại Nam

* GitHub:
  https://github.com/TruongDev10

---

<div align="center">

### © 2026 - Faculty of Information Technology - DaiNam University

### AI • Computer Vision • Blockchain • Arduino • IoT

</div>
