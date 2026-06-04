# Demo giai doan 1: Nhan dien 3 mau va robot gia lap

## Muc tieu

He thong demo truoc khi co canh tay robot that:

1. Camera hoac file upload phat hien vat the.
2. OpenCV loc 3 mau muc tieu: do, xanh la, xanh duong.
3. Tinh tam vat the theo toa do anh `(x, y)`.
4. Tao lenh robot gia lap theo mau.
5. Luu log SQLite va co the dua log len blockchain local neu Ganache/contract da ket noi.

## Lenh robot gia lap

| Mau | Lenh | Khay tha |
| --- | --- | --- |
| Do | `PICK_RED_DROP_BIN_A` | `BIN_A - Do` |
| Xanh la | `PICK_GREEN_DROP_BIN_B` | `BIN_B - Xanh la` |
| Xanh duong | `PICK_BLUE_DROP_BIN_C` | `BIN_C - Xanh duong` |

Toa do robot hien tai la toa do gia lap duoc scale tu toa do camera:

```text
robot_x = image_x / frame_width * 300
robot_y = image_y / frame_height * 220
robot_z = 35
```

Sau nay khi co canh tay robot that, chi can thay lenh gia lap bang gui Serial cho Arduino/ESP32.

## Chay demo

```bash
python run_server.py
```

Mo dashboard:

```text
http://127.0.0.1:5000
```

## Kich ban thuyet trinh

1. Mo dashboard va cho thay he thong chi cau hinh 3 mau: do, xanh la, xanh duong.
2. Dua vat mau do/xanh la/xanh duong vao vung camera.
3. Chi vao bounding box tren video: he thong ve khung, danh dau tam vat the va hien lenh robot.
4. Chi vao bang log realtime: co cot `Tam` va `Lenh robot`.
5. Chi vao khung `Robot arm simulator`: co object center, pick position, drop bin va last command.
6. Neu co Ganache/contract, ket noi blockchain va cho thay log phan loai duoc dua vao hang doi/ghi on-chain.
7. Giai thich rang day la giai doan 1; giai doan 2 se thay simulator bang canh tay robot that.

## Kiem tra nhanh

API mau muc tieu:

```text
GET /api/colors
```

API thong ke realtime:

```text
GET /api/stats
```

Neu `blockchain.status` hien `offline: cannot connect to Ganache`, app van demo nhan dien va robot gia lap binh thuong. Blockchain chi can khi ban muon demo truy xuat log.
