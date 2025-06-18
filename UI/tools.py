import io
import sys

def run_code_with_input(code_str: str, input_str: str) -> str:
    """
    Thực thi code Python từ chuỗi với input được cung cấp dưới dạng chuỗi.
    Trả về toàn bộ output (stdout) dưới dạng chuỗi.
    """
    stdin_backup = sys.stdin
    stdout_backup = sys.stdout

    sys.stdin = io.StringIO(input_str)
    sys.stdout = io.StringIO()

    try:
        exec(code_str, {})
        output = sys.stdout.getvalue()
    except Exception as e:
        output = f"Exception: {e}"
    finally:
        sys.stdin = stdin_backup
        sys.stdout = stdout_backup

    return output