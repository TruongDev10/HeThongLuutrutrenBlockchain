import argparse
import time

import serial


def main():
    parser = argparse.ArgumentParser(description="Send one command to the Arduino robot arm over COM.")
    parser.add_argument("--port", required=True, help="Arduino COM port, for example COM3")
    parser.add_argument("--baudrate", type=int, default=9600)
    parser.add_argument("command", nargs="+", help='Command, for example: HOME or PICK 150 110 red valid')
    args = parser.parse_args()

    command = " ".join(args.command).strip()
    with serial.Serial(args.port, args.baudrate, timeout=2) as board:
        time.sleep(2.0)
        board.reset_input_buffer()
        board.write((command + "\n").encode("ascii"))
        board.flush()
        print(f"sent: {command}")

        deadline = time.time() + 8
        while time.time() < deadline:
            line = board.readline().decode("ascii", errors="replace").strip()
            if line:
                print(f"arduino: {line}")
                if line.startswith(("OK", "ERR")):
                    break


if __name__ == "__main__":
    main()
