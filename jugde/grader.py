#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trình chấm bài tự động
Sử dụng: python grader.py <đường_dẫn_bài_nộp.py> <folder_input> <folder_output>
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path
import difflib
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

class AutoGrader:
    def __init__(self, submission_file, input_folder, output_folder, timeout=5):
        """
        Khởi tạo trình chấm bài
        
        Args:
            submission_file: Đường dẫn file bài nộp (.py)
            input_folder: Thư mục chứa các file input
            output_folder: Thư mục chứa các file output mẫu
            timeout: Thời gian timeout cho mỗi test case (giây)
        """
        self.submission_file = Path(submission_file)
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.timeout = timeout
        
        # Kiểm tra file và folder tồn tại
        self._validate_paths()
        
        # Lấy danh sách test cases
        self.test_cases = self._get_test_cases()
        
    def _validate_paths(self):
        """Kiểm tra tính hợp lệ của các đường dẫn"""
        if not self.submission_file.exists():
            raise FileNotFoundError(f"File bài nộp không tồn tại: {self.submission_file}")
        
        if not self.submission_file.suffix == '.py':
            raise ValueError("File bài nộp phải có đuôi .py")
            
        if not self.input_folder.exists():
            raise FileNotFoundError(f"Thư mục input không tồn tại: {self.input_folder}")
            
        if not self.output_folder.exists():
            raise FileNotFoundError(f"Thư mục output không tồn tại: {self.output_folder}")
    
    def _get_test_cases(self):
        """Lấy danh sách các test cases từ thư mục input"""
        input_files = list(self.input_folder.glob("*.txt"))
        test_cases = []
        
        for input_file in sorted(input_files):
            # Tìm file output tương ứng
            output_file = self.output_folder / input_file.name
            if output_file.exists():
                test_cases.append({
                    'name': input_file.stem,
                    'input_file': input_file,
                    'output_file': output_file
                })
            else:
                print(f"⚠️  Cảnh báo: Không tìm thấy file output cho {input_file.name}")
        
        return test_cases
    
    def _run_submission(self, input_data):
        """
        Chạy bài nộp với input cho trước
        
        Args:
            input_data: Dữ liệu input (string)
            
        Returns:
            tuple: (output, error, return_code, execution_time)
        """
        start_time = time.time()
        
        try:
            # Chạy bài nộp với timeout
            process = subprocess.Popen(
                [sys.executable, str(self.submission_file)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            
            # Đặt timeout
            try:
                output, error = process.communicate(input=input_data, timeout=self.timeout)
                return_code = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                output, error = process.communicate()
                return_code = -1
                error = f"Time Limit Exceeded (>{self.timeout}s)\n" + error
                
        except Exception as e:
            output = ""
            error = f"Runtime Error: {str(e)}"
            return_code = -1
            
        execution_time = time.time() - start_time
        return output.strip(), error.strip(), return_code, execution_time
    
    def _compare_output(self, actual_output, expected_output):
        """
        So sánh output thực tế với output mong đợi
        
        Args:
            actual_output: Output từ bài nộp
            expected_output: Output mẫu
            
        Returns:
            dict: Kết quả so sánh
        """
        # Chuẩn hóa output (loại bỏ whitespace thừa)
        actual_lines = [line.rstrip() for line in actual_output.split('\n')]
        expected_lines = [line.rstrip() for line in expected_output.split('\n')]
        
        # Loại bỏ các dòng trống ở cuối
        while actual_lines and not actual_lines[-1]:
            actual_lines.pop()
        while expected_lines and not expected_lines[-1]:
            expected_lines.pop()
        
        is_correct = actual_lines == expected_lines
        
        if not is_correct:
            # Tạo diff để hiển thị sự khác biệt
            diff = list(difflib.unified_diff(
                expected_lines, actual_lines,
                fromfile='Expected', tofile='Actual',
                lineterm=''
            ))
            diff_text = '\n'.join(diff) if diff else "Outputs differ but diff unavailable"
        else:
            diff_text = ""
            
        return {
            'correct': is_correct,
            'actual': '\n'.join(actual_lines),
            'expected': '\n'.join(expected_lines),
            'diff': diff_text
        }
    
    def _print_test_result(self, test_name, result):
        """In kết quả của một test case"""
        status = "✅ PASS" if result['status'] == 'AC' else f"❌ {result['status']}"
        print(f"Test {test_name}: {status} ({result['time']:.3f}s)")
        
        if result['status'] != 'AC':
            print(f"  Lỗi: {result['message']}")
            if result['status'] == 'WA' and result.get('diff'):
                print("  Sự khác biệt:")
                for line in result['diff'].split('\n')[:10]:  # Chỉ hiện 10 dòng đầu
                    print(f"    {line}")
                if len(result['diff'].split('\n')) > 10:
                    print("    ...")
        print()
    
    def run_single_test(self, test_case):
        """
        Chạy một test case
        
        Args:
            test_case: Dictionary chứa thông tin test case
            
        Returns:
            dict: Kết quả test
        """
        test_name = test_case['name']
        
        try:
            # Đọc input
            with open(test_case['input_file'], 'r', encoding='utf-8') as f:
                input_data = f.read()
            
            # Đọc expected output
            with open(test_case['output_file'], 'r', encoding='utf-8') as f:
                expected_output = f.read().strip()
            
            # Chạy bài nộp
            actual_output, error, return_code, exec_time = self._run_submission(input_data)
            
            # Xử lý các trường hợp lỗi
            if return_code == -1 and "Time Limit Exceeded" in error:
                return {
                    'status': 'TLE',
                    'message': 'Time Limit Exceeded',
                    'time': exec_time
                }
            elif return_code != 0:
                return {
                    'status': 'RE',
                    'message': f'Runtime Error: {error}',
                    'time': exec_time
                }
            elif error:
                return {
                    'status': 'RE',
                    'message': f'Error output: {error}',
                    'time': exec_time
                }
            
            # So sánh output
            comparison = self._compare_output(actual_output, expected_output)
            
            if comparison['correct']:
                return {
                    'status': 'AC',
                    'message': 'Accepted',
                    'time': exec_time
                }
            else:
                return {
                    'status': 'WA',
                    'message': 'Wrong Answer',
                    'time': exec_time,
                    'diff': comparison['diff'],
                    'actual': comparison['actual'],
                    'expected': comparison['expected']
                }
                
        except Exception as e:
            return {
                'status': 'IE',
                'message': f'Internal Error: {str(e)}',
                'time': 0
            }
    
    def run_all_tests(self, max_workers=None):
        """Chạy tất cả test cases với đa luồng"""
        if not self.test_cases:
            print("❌ Không tìm thấy test case nào!")
            return
        
        # Tự động xác định số luồng tối ưu nếu không được chỉ định
        if max_workers is None:
            max_workers = min(len(self.test_cases), 4)  # Tối đa 4 luồng
        
        print(f"🚀 Bắt đầu chấm bài: {self.submission_file.name}")
        print(f"📂 Input folder: {self.input_folder}")
        print(f"📂 Output folder: {self.output_folder}")
        print(f"⏱️  Timeout: {self.timeout}s")
        print(f"📝 Số lượng test cases: {len(self.test_cases)}")
        print(f"🧵 Số luồng: {max_workers}")
        print("=" * 50)
        
        results = {}
        total_time = 0
        start_time = time.time()
        
        # Lock để đồng bộ hóa việc in kết quả
        print_lock = threading.Lock()
        
        def run_test_with_index(test_case, index):
            """Wrapper function để chạy test và in kết quả với thread-safe"""
            with print_lock:
                print(f"Đang chạy test {index}/{len(self.test_cases)}: {test_case['name']}")
            
            result = self.run_single_test(test_case)
            
            with print_lock:
                self._print_test_result(test_case['name'], result)
            
            return test_case['name'], result
        
        # Sử dụng ThreadPoolExecutor để chạy đa luồng
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit tất cả các test cases
            future_to_test = {
                executor.submit(run_test_with_index, test_case, i): (test_case, i)
                for i, test_case in enumerate(self.test_cases, 1)
            }
            
            # Thu thập kết quả khi các luồng hoàn thành
            for future in as_completed(future_to_test):
                try:
                    test_name, result = future.result()
                    results[test_name] = result
                    total_time += result['time']
                except Exception as e:
                    test_case, index = future_to_test[future]
                    with print_lock:
                        print(f"❌ Lỗi khi chạy test {test_case['name']}: {str(e)}")
                    results[test_case['name']] = {
                        'status': 'ERROR',
                        'time': 0,
                        'memory': 0,
                        'error': str(e)
                    }
        
        actual_time = time.time() - start_time
        
        # Tổng kết
        with print_lock:
            self._print_summary(results, total_time, actual_time)
        
        return results
    
    def _print_summary(self, results, total_cpu_time, actual_time=None):
        """In tổng kết kết quả với thông tin về thời gian thực tế"""
        print("\n" + "=" * 50)
        print("📊 TỔNG KẾT KẾT QUẢ")
        print("=" * 50)
        
        accepted = sum(1 for r in results.values() if r['status'] == 'AC')
        unaccepted = sum(1 for r in results.values() if r['status'] in ['WA', 'TLE', 'MLE', 'RE', 'IE'])
        error = sum(1 for r in results.values() if r['status'] == 'ERROR')
        
        print(f"✅ Passed: {accepted}/{len(results)}")
        print(f"❌ Failed: {unaccepted}/{len(results)}")
        if error > 0:
            print(f"🔥 Error: {error}/{len(results)}")
        
        print(f"⏱️  Tổng thời gian CPU: {total_cpu_time:.3f}s")
        if actual_time:
            print(f"🕐 Thời gian thực tế: {actual_time:.3f}s")
            if total_cpu_time > 0:
                speedup = total_cpu_time / actual_time
                print(f"🚀 Tăng tốc: {speedup:.2f}x")
        
        if accepted == len(results):
            print("🎉 TẤT CẢ TEST CASES ĐỀU PASS!")
        else:
            print(f"💡 Tỉ lệ thành công: {accepted/len(results)*100:.1f}%")


def grade_submission(submission_file, input_folder, output_folder, timeout=5, verbose=True):
    """
    Hàm chấm bài - gọi trực tiếp với 3 đường dẫn
    
    Args:
        submission_file: Đường dẫn file bài nộp (.py)
        input_folder: Thư mục chứa các file input
        output_folder: Thư mục chứa các file output mẫu
        timeout: Thời gian timeout cho mỗi test case (giây)
        verbose: Có in chi tiết hay không
        
    Returns:
        dict: Kết quả chấm bài với key là tên test case
    """
    try:
        # Tạo đối tượng grader
        grader = AutoGrader(submission_file, input_folder, output_folder, timeout)
        
        # Chạy tất cả test cases
        if verbose:
            results = grader.run_all_tests()
        else:
            # Chạy im lặng, chỉ trả về kết quả
            results = {}
            for test_case in grader.test_cases:
                result = grader.run_single_test(test_case)
                results[test_case['name']] = result
        
        return results
        
    except Exception as e:
        if verbose:
            print(f"❌ Lỗi: {e}")
        return {'error': str(e)}


def main():
    """Hàm main cho command line"""
    if len(sys.argv) != 4:
        print("Cách sử dụng:")
        print("python grader.py <đường_dẫn_bài_nộp.py> <folder_input> <folder_output>")
        print()
        print("Ví dụ:")
        print("python grader.py solution.py inputs outputs")
        print()
        print("Hoặc import và gọi hàm:")
        print("from grader import grade_submission")
        print("results = grade_submission('solution.py', 'inputs', 'outputs')")
        sys.exit(1)
    
    submission_file = sys.argv[1]
    input_folder = sys.argv[2]
    output_folder = sys.argv[3]
    
    # Gọi hàm grade_submission
    results = grade_submission(submission_file, input_folder, output_folder)


if __name__ == "__main__":
    main()


# Ví dụ sử dụng hàm grade_submission
def example_usage():
    """Ví dụ cách sử dụng hàm grade_submission"""
    
    # Cách 1: Chấm với output chi tiết
    results = grade_submission(
        submission_file="solution.py",
        input_folder="inputs", 
        output_folder="outputs",
        timeout=5,
        verbose=True
    )
    
    # In kết quả tóm tắt
    if 'error' not in results:
        ac_count = sum(1 for r in results.values() if r['status'] == 'AC')
        total_count = len(results)
        print(f"\n🎯 Kết quả cuối cùng: {ac_count}/{total_count} test cases PASS")
    
    # Cách 2: Chấm im lặng, chỉ lấy kết quả
    results_quiet = grade_submission(
        submission_file="solution.py",
        input_folder="inputs",
        output_folder="outputs", 
        verbose=False
    )
    
    # Xử lý kết quả
    if 'error' not in results_quiet:
        for test_name, result in results_quiet.items():
            if result['status'] == 'AC':
                print(f"✅ {test_name}: PASS ({result['time']:.3f}s)")
            else:
                print(f"❌ {test_name}: {result['status']} - {result['message']}")
    
    return results