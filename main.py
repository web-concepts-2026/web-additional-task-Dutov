import socket
import os


def parse_http(data):
    parts = data.split('\r\n\r\n', 1)
    header_data = parts[0]
    body = parts[1] if len(parts) > 1 else ""

    lines = header_data.split('\r\n')
    request_line = lines[0].split(' ')

    if len(request_line) < 3:
        return None, None, None, [], body

    method, full_path, http_version = request_line
    return method, full_path, http_version, lines, body


def parse_query_request(full_path):
    query_params = {}
    path = full_path

    if '?' in full_path:
        path, query_string = full_path.split('?', 1)
        for param in query_string.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                query_params[key] = value

    return path, query_params


def parse_headers(lines):
    headers = {}
    for line in lines[1:]:
        if ': ' in line:
            key, value = line.split(': ', 1)
            headers[key] = value
    return headers


def handle_get_request(conn, path):
    if path == '/':
        path = '/index.html'

    filepath = path.lstrip('/')

    if os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            file_content = f.read()

        content_type = "text/html"
        if filepath.endswith(".css"): content_type = "text/css"

        response_headers = (
            "HTTP/1.1 200 OK\r\n"
            f"Content-Type: {content_type}; charset=utf-8\r\n"
            f"Content-Length: {len(file_content)}\r\n"
            "\r\n"
        ).encode('utf-8')

        conn.sendall(response_headers + file_content)
    else:
        response = "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\n\r\nFile not found."
        conn.sendall(response.encode('utf-8'))


def handle_post_request(conn, headers, body):
    content_type = headers.get('Content-Type', '')

    if 'application/json' in content_type:
        response_body = '{"status": "success", "message": "JSON POST data processed"}'
        response_headers = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: application/json; charset=utf-8\r\n"
            f"Content-Length: {len(response_body)}\r\n"
            "\r\n"
        )
        conn.sendall((response_headers + response_body).encode('utf-8'))
    else:
        response = "HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\n\r\nExpected application/json"
        conn.sendall(response.encode('utf-8'))


def start_server():
    HOST = '127.0.0.1'
    PORT = 8080

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server launch on http://{HOST}:{PORT}")

        while True:
            conn, addr = s.accept()
            with conn:
                try:
                    data = conn.recv(4096).decode('utf-8')
                    if not data:
                        continue
                    method, full_path, http_version, lines, body = parse_http(data)
                    if not method:
                        continue

                    path, query_params = parse_query_request(full_path)
                    headers = parse_headers(lines)

                    print(f"[{method}] Path: {path} | Parameters: {query_params}")

                    if method == "GET":
                        handle_get_request(conn, path)
                    elif method == "POST":
                        handle_post_request(conn, headers, body)
                    else:
                        response = "HTTP/1.1 405 Method Not Allowed\r\n\r\nMethod Not Allowed"
                        conn.sendall(response.encode('utf-8'))

                except Exception as e:
                    print(f"Issues with connection: {e}")


if __name__ == "__main__":
    start_server()