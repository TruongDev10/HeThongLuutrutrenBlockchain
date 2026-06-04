# AI Computer Vision Color Product Inspection

Đề tài: **Xây dựng hệ thống thị giác máy tính hỗ trợ nhận diện, phân loại và thống kê sản phẩm theo màu sắc**.

Project dùng Flask, OpenCV, YOLOv8, NumPy, SQLite, Bootstrap và Chart.js để nhận diện vật thể qua webcam hoặc file upload, phân tích màu chủ đạo, đếm số lượng từng màu, cảnh báo sai màu và export CSV.

## Tính năng

- Realtime webcam stream với bounding box và label màu.
- Detect vật thể bằng YOLOv8 pretrained hoặc `models/best.pt` custom.
- Fallback contour detection nếu chưa cài được Ultralytics/model.
- Phân tích màu bằng HSV threshold và OpenCV KMeans.
- Chỉ nhận diện 5 màu mục tiêu: đỏ, xanh lá, xanh dương, vàng, cam.
- Màu trắng, xám, đen, nâu, tím hoặc màu nền được trả về `not_target_color` / `ignored`.
- Chỉ phân tích vùng trung tâm bbox YOLO, không lấy dominant color toàn frame.
- Chọn màu chuẩn để phát hiện sai màu `NG`.
- Upload ảnh/video và lưu output đã vẽ bounding box.
- Dashboard dark mode, glassmorphism, Chart.js realtime.
- SQLite log, thống kê màu, export CSV.
- Voice alert trên trình duyệt khi phát hiện sai màu.
- Ghi nhật ký phân loại lên Local Blockchain Ganache/Ethereum bằng Web3.py.
- Smart Contract Solidity lưu `productId`, màu sắc, kết quả OK/NG, RGB/HSV và thời gian.

## Cấu trúc

```text
.
├── app.py
├── config.py
├── config/colors.py
├── requirements.txt
├── README.md
├── models/
├── static/css/style.css
├── static/js/dashboard.js
├── templates/
├── database/init_db.py
├── detection/
├── analytics/
├── blockchain/
│   ├── contracts/ProductClassificationLedger.sol
│   ├── abi/ProductClassificationLedger.json
│   └── scripts/deploy_contract.py
├── utils/
├── uploads/
├── outputs/
├── exports/
└── reports/
```

## Cài đặt

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python database/init_db.py
python app.py
```

Mở trình duyệt: `http://127.0.0.1:5000`

Nếu chưa có file model trong `models/`, Ultralytics sẽ tự tải `yolov8n.pt` trong lần chạy đầu tiên khi máy có mạng. Nếu không có mạng hoặc model lỗi, app vẫn dùng fallback contour detection để test giao diện và luồng xử lý.

## Dùng custom YOLOv8

Chuẩn dataset YOLO:

```text
datasets/color_product/
├── train/images
├── train/labels
├── valid/images
├── valid/labels
├── test/images
├── test/labels
└── data.yaml
```

Train:

```bash
pip install ultralytics
yolo detect train data=datasets/color_product/data.yaml model=yolov8n.pt epochs=50 imgsz=640
```

Sau khi train xong:

```bash
copy runs\detect\train\weights\best.pt models\best.pt
```

Khởi động lại app để dùng `models/best.pt`.

## Tích hợp Blockchain cục bộ với Ganache

Luồng hoạt động:

1. Camera/OpenCV/YOLO nhận diện vật thể và màu.
2. App tạo `product_id`, kết quả `OK/NG`, RGB, HSV và timestamp.
3. SQLite lưu log cục bộ.
4. Nếu status là `valid` hoặc `wrong_color`, YOLO confidence >= 0.5, color ratio >= 0.12, Web3.py đưa log vào hàng đợi nền và gửi transaction tới Smart Contract.
5. Smart Contract ghi bản ghi bất biến lên local blockchain.
6. Dashboard hiển thị trạng thái kết nối, số record on-chain và tx hash gần nhất.

### 1. Chạy Ganache

Mở Ganache Desktop hoặc Ganache CLI. RPC mặc định thường là:

```text
http://127.0.0.1:7545
```

Chain ID thường là `1337` hoặc `5777`. Kiểm tra trong phần cài đặt network của Ganache.

### 2. Deploy Smart Contract

```bash
python blockchain/scripts/deploy_contract.py
```

Script sẽ in ra:

```text
Contract deployed
Address: 0x...
Tx hash: 0x...
```

Copy `Address` vào ô `Contract address` trên dashboard, sau đó bấm `Kết nối blockchain`.
Provider, contract address, account address và chain id sẽ được lưu trong:

```text
blockchain/blockchain_settings.json
```

Private key không được lưu bởi dashboard.

Nếu dùng account chưa mở khóa, cấu hình thêm:

```bash
set BLOCKCHAIN_ACCOUNT_ADDRESS=0xYourGanacheAccount
set BLOCKCHAIN_PRIVATE_KEY=your_ganache_private_key
set BLOCKCHAIN_CONTRACT_ADDRESS=0xYourContractAddress
set BLOCKCHAIN_CHAIN_ID=1337
python run_server.py
```

Với Ganache local mở khóa account, thường không cần private key, app có thể dùng account đầu tiên từ node.

### Smart Contract

File contract nằm tại:

```text
blockchain/contracts/ProductClassificationLedger.sol
```

Hàm ghi dữ liệu mới:

```solidity
addRecord(productId, objectName, color, result, rgbValue, hsvValue, confidence, resultHash, timestamp)
```

Dữ liệu được phát qua event `ClassificationLogged` và lưu trong mapping `records`, phục vụ truy xuất nguồn gốc.
Hàm cũ `addClassification(...)` vẫn được giữ như alias tương thích.

## API

- `GET /` hoặc `GET /dashboard`: dashboard.
- `GET /video_feed`: MJPEG webcam stream.
- `POST /upload-image`: upload ảnh, field name `image`.
- `POST /upload-video`: upload video, field name `video`.
- `GET /api/stats`: thống kê màu và trạng thái realtime.
- `GET /api/logs`: lịch sử nhận diện.
- `GET /api/colors`: danh sách 5 màu, HEX/RGB/HSL/CMYK/HSV/tolerance.
- `GET /export-csv`: xuất CSV.
- `POST /set-target-color`: body JSON `{ "target_color": "red" }`.
- `POST /api/set-target-color`: body JSON `{ "target_color": "red" }`.
- `POST /set-confidence`: body JSON `{ "confidence": 0.45 }`.
- `GET /api/blockchain/status`: trạng thái Ganache/contract.
- `POST /api/blockchain/config`: cấu hình provider, contract, account, private key, chain id.
- `POST /api/blockchain/log`: ghi log blockchain thủ công để test.
- `GET /api/blockchain/logs`: lịch sử log blockchain.

## Logic nhận diện màu mới

1. YOLO phát hiện bbox sản phẩm.
2. Bỏ bbox `person`, bbox quá nhỏ hoặc quá lớn.
3. Crop bbox, chỉ lấy vùng trung tâm 70% bằng `CENTER_CROP_MARGIN_RATIO = 0.15`.
4. Gaussian blur nhẹ.
5. Chuyển BGR sang HSV.
6. Tạo mask cho 5 màu trong `config/colors.py`.
7. Morphology open/close để giảm nhiễu.
8. Tính `color_ratio = pixel_màu_hợp_lệ / pixel_crop`.
9. Nếu ratio < `MIN_COLOR_RATIO = 0.12`, trả `not_target_color`, status `ignored`.
10. Nếu ratio đủ ngưỡng, trả màu có ratio lớn nhất và tính:

```text
detected_hex
standard_hex
detected_rgb
standard_rgb
average_hsv
color_distance
match_standard
```

`color_distance` là khoảng cách Euclidean RGB giữa màu phát hiện và màu chuẩn. Tolerance mặc định là `45`.

## Chỉnh ngưỡng nếu nhận sai

File cấu hình:

```text
config/colors.py
```

Các tham số thường chỉnh:

- `MIN_COLOR_RATIO`: tăng lên `0.16` hoặc `0.20` nếu nền/áo vẫn bị nhận nhầm; giảm xuống `0.08` nếu vật thể nhỏ hoặc thiếu sáng.
- `CENTER_CROP_MARGIN_RATIO`: tăng lên `0.20` nếu bbox dính nền nhiều; giảm xuống `0.10` nếu vật thể nằm sát viền bbox.
- `hsv_ranges`: chỉnh khoảng H/S/V cho từng màu theo ánh sáng thực tế.
- `tolerance`: tăng nếu muốn `match_standard` dễ đạt hơn khi camera bị lệch màu.

Sau khi chỉnh, restart app:

```bash
python run_server.py
```

## Kịch bản demo báo cáo

1. Chạy `python app.py`.
2. Mở dashboard.
3. Đưa vật thể nhiều màu trước webcam.
4. Quan sát bounding box, tên màu, RGB/HSV và biểu đồ.
5. Chọn màu chuẩn, đưa vật thể sai màu để nhận cảnh báo `NG`.
6. Kết nối Ganache và contract trên dashboard.
7. Quan sát tx hash và số record on-chain tăng sau mỗi log phân loại.
8. Upload ảnh/video mẫu để phân tích offline.
9. Bấm `Export CSV` để lấy lịch sử nhận diện kèm tx hash blockchain.

## Gợi ý dataset

- Roboflow Universe: `colored object detection`, `bottle cap color detection`, `product color detection`, `fruit color detection`.
- Kaggle: `color classification dataset`, `fruit color dataset`, `product defect detection`, `bottle cap dataset`.
- Tự chụp: nắp chai, hộp sản phẩm, trái cây, đồ vật trong lớp học với nhiều điều kiện ánh sáng.

## Ghi chú kỹ thuật

- Camera mặc định là `CAMERA_INDEX = 0` trong `config.py`.
- Có thể chỉnh `FRAME_WIDTH`, `FRAME_HEIGHT`, `DEFAULT_CONFIDENCE`.
- Log realtime được throttle bằng `LOG_COOLDOWN_SECONDS` để tránh ghi SQLite quá dày.
- File lỗi sai màu được lưu trong `outputs/images`.

## Chay voi canh tay Arduino that

Sketch Arduino nam tai:

```text
arduino/robot_arm_camera_pick/robot_arm_camera_pick.ino
```

Nap sketch nay vao Arduino, cap nguon rieng cho servo va noi chung GND voi Arduino. App Flask se lay tam bbox tu camera, quy doi sang toa do robot `x=0..300`, `y=0..220`, roi gui lenh Serial:

```text
PICK <x> <y> <color> <status>
```

Mac dinh app chi mo phong de tranh tay robot chay bat ngo. Bat dieu khien that bang PowerShell:

```powershell
$env:ROBOT_SERIAL_ENABLED="1"
$env:ROBOT_SERIAL_PORT="COM3"
$env:ROBOT_SERIAL_BAUDRATE="9600"
python run_server.py
```

Neu Arduino cua ban o cong khac, doi `COM3` thanh cong dung trong Arduino IDE. Cac goc can can chinh trong sketch:

```cpp
BASE_MIN, BASE_MAX
ARM2_NEAR, ARM2_FAR
ARM3_NEAR, ARM3_FAR
DROP_RED, DROP_GREEN, DROP_BLUE, DROP_WRONG
```

Nen test tung buoc bang cach gui `HOME` va mot lenh mau trong Serial Monitor truoc:

```text
PICK 150 110 red valid
```
