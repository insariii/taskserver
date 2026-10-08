import socket
import threading
import protocol as proto

HOST = "0.0.0.0"
PORT = 5555

tasks = []
tasks_lock = threading.Lock()

clients = {}
clients_lock = threading.Lock()


def send_error(sock, text):
    proto.send_message(sock, "ERRO", text.encode("utf-8"))


def handle_client(sock, addr):
    try:
        with clients_lock:
            clients[sock] = addr

        proto.send_message(sock, "TEXT", b"* вы подключились к серверу задач")
        print(f"[+] клиент подключился ({addr})")

        while True:
            msg = proto.recv_message(sock)
            if msg is None:
                print(f"[i] {addr} отключился")
                break

            command, payload = msg

            if command == "ADD":
                text = payload.decode("utf-8", errors="replace").strip()

                if not text:
                    send_error(sock, "после /add нужно указать текст задачи")
                    continue

                with tasks_lock:
                    tasks.append({
                        "text": text,
                        "done": False
                    })
                    number = len(tasks)

                proto.send_message(
                    sock,
                    "TEXT",
                    f"* задача {number} добавлена".encode("utf-8")
                )

            elif command == "LIST":
                with tasks_lock:
                    if not tasks:
                        text = "список задач пуст"
                    else:
                        lines = []
                        for i, task in enumerate(tasks, 1):
                            mark = "x" if task["done"] else " "
                            lines.append(
                                f"{i}. [{mark}] {task['text']}"
                            )
                        text = "\n".join(lines)

                proto.send_message(sock, "LIST", text.encode("utf-8"))

            elif command == "DONE":
                try:
                    number = int(
                        payload.decode("utf-8", errors="replace").strip()
                    )
                except ValueError:
                    send_error(sock, "номер задачи должен быть числом")
                    continue

                with tasks_lock:
                    if number < 1 or number > len(tasks):
                        send_error(sock, "такой задачи не существует")
                        continue

                    tasks[number - 1]["done"] = True
                    task_text = tasks[number - 1]["text"]

                proto.send_message(
                    sock,
                    "TEXT",
                    f"* задача {number} выполнена: {task_text}".encode("utf-8")
                )

            elif command == "DELE":
                try:
                    number = int(
                        payload.decode("utf-8", errors="replace").strip()
                    )
                except ValueError:
                    send_error(sock, "номер задачи должен быть числом")
                    continue

                with tasks_lock:
                    if number < 1 or number > len(tasks):
                        send_error(sock, "такой задачи не существует")
                        continue

                    task_text = tasks[number - 1]["text"]
                    tasks.pop(number - 1)

                proto.send_message(
                    sock,
                    "TEXT",
                    f"* задача {number} удалена: {task_text}".encode("utf-8")
                )

            elif command == "QUIT":
                proto.send_message(sock, "TEXT", b"* bye")
                print(f"[-] {addr} вышел через QUIT")
                break

            else:
                send_error(sock, f"unknown command {command}")

    except ConnectionResetError:
        print(f"[!] {addr} - соединение сброшено (RST)")
    except BrokenPipeError:
        print(f"[!] {addr} - соединение разорвано")
    finally:
        with clients_lock:
            clients.pop(sock, None)
        sock.close()


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen()
        print(f"[*] сервер слушает {HOST}:{PORT}")

        while True:
            client_sock, addr = server.accept()
            threading.Thread(
                target=handle_client,
                args=(client_sock, addr),
                daemon=True
            ).start()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[*] сервер остановлен")
