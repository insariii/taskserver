import socket
import threading
import protocol as proto

HOST = "127.0.0.1"
PORT = 5555


def listen_loop(sock, stop_event):
    while not stop_event.is_set():
        try:
            msg = proto.recv_message(sock)
        except (ConnectionResetError, OSError):
            msg = None

        if msg is None:
            print("\n[!] соединение с сервером потеряно")
            stop_event.set()
            break

        command, payload = msg
        text = payload.decode("utf-8", errors="replace")

        if command == "LIST":
            print(f"\n[список задач]\n{text}\n> ", end="")
        elif command == "ERRO":
            print(f"\n[ошибка] {text}\n> ", end="")
        else:
            print(f"\n{text}\n> ", end="")


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((HOST, PORT))
    except (ConnectionRefusedError, OSError) as e:
        print(f"Не удалось подключиться: {e}")
        return

    stop_event = threading.Event()
    threading.Thread(
        target=listen_loop,
        args=(sock, stop_event),
        daemon=True
    ).start()

    print("Команды: /add <text>, /list, /done <number>, /delete <number>, /quit.")

    try:
        while not stop_event.is_set():
            line = input("> ").strip()

            if line == "/quit":
                proto.send_message(sock, "QUIT")
                break

            elif line == "/list":
                proto.send_message(sock, "LIST")

            elif line[:5] == "/add ":
                text = line[5:].strip()

                if text:
                    proto.send_message(sock, "ADD", text.encode("utf-8"))
                else:
                    print("[ошибка] после /add нужно указать текст")

            elif line[:6] == "/done ":
                number = line[6:].strip()

                if number:
                    proto.send_message(sock, "DONE", number.encode("utf-8"))
                else:
                    print("[ошибка] после /done нужно указать номер")

            elif line[:8] == "/delete ":
                number = line[8:].strip()

                if number:
                    proto.send_message(sock, "DELE", number.encode("utf-8"))
                else:
                    print("[ошибка] после /delete нужно указать номер")

            elif line:
                print("[ошибка] неизвестная команда")

    except (EOFError, KeyboardInterrupt, BrokenPipeError, OSError):
        pass
    finally:
        stop_event.set()
        sock.close()


if __name__ == "__main__":
    main()
