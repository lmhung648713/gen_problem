from langchain_openai import AzureChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
load_dotenv()

def gemini_2_flash(temperature):
    return ChatGoogleGenerativeAI(
        api_key=os.getenv("GEMINI_API_KEY"),
        model="gemini-2.0-flash",
        temperature=temperature,
        max_tokens=8190
    )

def gemini_2_5_pro(temperature):
    return ChatGoogleGenerativeAI(
        api_key=os.getenv("GEMINI_API_KEY"),
        model="gemini-2.5-pro-preview-03-25",
        temperature=temperature,
        max_tokens=65000,
        max_retries=3,
        timeout=60
    )

def gpt_4o_mini(temperature=0.7):
    return AzureChatOpenAI(
        model="gpt-4o-mini",
        temperature=temperature,
        max_tokens=16000,
        api_version="2024-08-01-preview",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        azure_deployment="gpt-4o-mini"
    )

def o3_mini():
    return AzureChatOpenAI(
        model="o3-mini",
        model_kwargs = {"max_completion_tokens": 100000},
        api_version="2024-12-01-preview",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        azure_deployment="o3-mini"
    )

if __name__ == "__main__":
    statement = """Cho mảng số nguyên có n phần tử. 
Tìm độ dài dãy con tăng dài nhất(tăng tức là số sau lớn hơn số trước). 
Dãy con của 1 mảng a là dãy có được khi xóa một vài phần tử của mảng a(có thể không xóa) và vẫn giữ nguyên thứ tự các phần tử còn lại. 
Input:
Dòng đầu tiên chứa 1 số nguyên duy nhất n. (1 <= n <= 100)
Dòng tiếp theo chứa n số nguyên cách nhau bởi khoảng trẳng. (1<=a[i]<=1000)

Output:
Số nguyên duy nhất là đáp án theo yêu cầu đề bài.

Ví dụ:
Input:
3
1 5 2 7 3 8

Output:
4

Giải thích:

Dãy con tăng dài nhất của mảng là [1, 2, 7, 8] (có độ dài 4). Đáp án [1, 5, 7, 8] cũng được nhấp nhận.
"""
    prompt = f"""Tạo chương trình Python sinh random testcase cho bài toán sau:

<problem_statement>
{statement}
</problem_statement>

Yêu cầu kỹ thuật:
- Chỉ viết code trong khối if __name__ == "__main__":
- Không định nghĩa thêm hàm hoặc class
- Sử dụng thư viện random với seed cố định để tái tạo kết quả
- In output theo định dạng yêu cầu của đề bài

Định dạng output:
- Chỉ trả về code Python thuần túy
- Không có comment, giải thích hay markdown
- Không có ```python``` hay bất kỳ ký hiệu đánh dấu nào
- Code phải chạy được ngay lập tức

Ví dụ cấu trúc:
```
import random
random.seed(42)

if __name__ == "__main__":
    # Tạo testcase ở đây
    print(test_input)
```
"""

    llm = gemini_2_flash(temperature=0.7)
    print(llm.invoke(prompt).content)