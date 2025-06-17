from typing import Dict, Any, List
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
import os
from dotenv import load_dotenv

# Giả định các lớp này được import từ các file khác
# from llm_config import gemini_2_flash, gemini_2_5_pro, gpt_4o_mini, o3_mini 
from prompts import *
from structures import *

load_dotenv()

# --- LLM Configuration Functions (giả định đã tồn tại) ---
# ... (gemini_2_flash, gpt_4o_mini, etc.)

# ============================================================================
# AGENT NODES (CÁC NODE TRONG GRAPH)
# ============================================================================

def create_idea_data_structure(state: ProblemGenerationState) -> Dict[str, Any]:
    """Agent 1: Data Structure Expert tạo ý tưởng."""
    print("--- 💡 AGENT: Data Structure Expert creating idea ---")
    # Logic để gọi LLM với CREATOR_PROMPTS["data_structure_expert"]
    # ...
    # Kết quả trả về sẽ được parse thành ProblemIdea và thêm vào state
    # new_idea = ProblemIdea(...) 
    # return {"all_ideas": [new_idea]}
    pass

def create_idea_algorithm(state: ProblemGenerationState) -> Dict[str, Any]:
    """Agent 2: Algorithm Strategist tạo ý tưởng."""
    print("--- 💡 AGENT: Algorithm Strategist creating idea ---")
    # Logic để gọi LLM với CREATOR_PROMPTS["algorithm_strategist"]
    # ...
    # new_idea = ProblemIdea(...)
    # return {"all_ideas": [new_idea]}
    pass

def create_idea_math_game(state: ProblemGenerationState) -> Dict[str, Any]:
    """Agent 3: Math Game Master tạo ý tưởng."""
    print("--- 💡 AGENT: Math Game Master creating idea ---")
    # Logic để gọi LLM với CREATOR_PROMPTS["math_game_master"]
    # ...
    # new_idea = ProblemIdea(...)
    # return {"all_ideas": [new_idea]}
    pass

def select_best_idea(state: ProblemGenerationState) -> Dict[str, Any]:
    """Agent 4: Chief Problem Curator chọn ý tưởng tốt nhất."""
    print("--- 🔎 AGENT: Curator selecting best idea ---")
    # Logic gọi LLM với problem_selector_prompt, truyền vào state['all_ideas']
    # ...
    # Kết quả trả về là một ExpertEvaluation
    # evaluation = ExpertEvaluation(...)
    # selected_idea = state['all_ideas'][evaluation.selected_idea_index]
    # return {"expert_evaluations": [evaluation], "selected_idea": selected_idea, "all_ideas": []} # Xóa ideas cũ để chuẩn bị cho vòng lặp mới nếu cần
    pass

def complete_problem_from_idea(state: ProblemGenerationState) -> Dict[str, Any]:
    """Agent 5: Master Problem Writer phát triển ý tưởng thành bài toán hoàn chỉnh."""
    print("--- ✍️ AGENT: Writer creating complete problem ---")
    # Logic gọi LLM với problem_completer_prompt, truyền vào state['selected_idea']
    # ...
    # complete_problem = CompleteProblem(...)
    # return {"complete_problem": complete_problem}
    pass

def run_tester_an(state: ProblemGenerationState) -> Dict[str, Any]:
    """Tester 1 (An - Intermediate): Kiểm tra sự rõ ràng."""
    print("--- 🧪 TESTER: An (Intermediate) checking clarity ---")
    # Logic gọi LLM với tester1_prompt, truyền vào state['complete_problem']
    # ...
    # feedback = TesterFeedback(...)
    # return {"tester_feedbacks": [feedback]}
    pass

def run_tester_binh(state: ProblemGenerationState) -> Dict[str, Any]:
    """Tester 2 (Bình - Advanced): Tìm lời giải thay thế."""
    print("--- 🧪 TESTER: Binh (Advanced) finding unintended solutions ---")
    # Logic gọi LLM với tester2_prompt
    # ...
    # feedback = TesterFeedback(...)
    # return {"tester_feedbacks": [feedback]}
    pass

def run_tester_cuong(state: ProblemGenerationState) -> Dict[str, Any]:
    """Tester 3 (Cường - Expert Tester): Tìm edge cases."""
    print("--- 💣 TESTER: Cuong (Expert) breaking edge cases ---")
    # Logic gọi LLM với tester3_prompt
    # ...
    # feedback = TesterFeedback(...)
    # return {"tester_feedbacks": [feedback]}
    pass

def refine_complete_problem(state: ProblemGenerationState) -> Dict[str, Any]:
    """Agent 6: Cải thiện bài toán dựa trên feedback."""
    print(f"--- 🛠️ AGENT: Refining problem (Revision {state['revision_count'] + 1}) ---")
    # Logic gọi lại Master Problem Writer (problem_completer_prompt)
    # nhưng lần này truyền thêm state['tester_feedbacks'] để cải thiện
    # ...
    # refined_problem = CompleteProblem(...)
    # return {
    #     "complete_problem": refined_problem, 
    #     "revision_count": state['revision_count'] + 1,
    #     "tester_feedbacks": [] # Xóa feedback cũ
    # }
    pass

def assess_final_difficulty(state: ProblemGenerationState) -> Dict[str, Any]:
    """Agent 7: AI Rating Assessor đánh giá độ khó cuối cùng."""
    print("--- 📊 AGENT: Assessor evaluating final difficulty ---")
    # Logic gọi LLM với problem_complexity_evaluator_prompt
    # ...
    # assessment = DifficultyAssessment(...)
    # final_problem = state['complete_problem']
    # # Gán các metadata từ assessment vào bài toán cuối cùng
    # final_problem.difficulty_level = assessment.difficulty_rating
    # final_problem.tags.extend(assessment.required_algorithms)
    # return {"difficulty_assessment": assessment, "final_problem": final_problem, "status": "completed"}
    pass


# ============================================================================
# ROUTING FUNCTIONS (CÁC HÀM ĐIỀU HƯỚNG)
# ============================================================================

def should_regenerate_ideas(state: ProblemGenerationState) -> str:
    """Kiểm tra xem Curator có yêu cầu tạo lại ý tưởng không."""
    print("--- 🤔 ROUTER: Checking curator's decision ---")
    # Logic đơn giản: nếu không có ý tưởng nào được chọn, tạo lại.
    if state.get("selected_idea") is None:
        print("--- 👎 DECISION: No idea selected. Regenerating ideas. ---")
        return "regenerate_ideas"
    print("--- 👍 DECISION: Idea selected. Proceeding to completion. ---")
    return "create_problem"

def should_refine_problem(state: ProblemGenerationState) -> str:
    """Kiểm tra xem feedback của tester có yêu cầu chỉnh sửa không."""
    print("--- 🤔 ROUTER: Checking tester feedback ---")
    if not state.get("tester_feedbacks"):
        return "finalize_problem"
        
    # Nếu có bất kỳ feedback nào yêu cầu cải thiện hoặc tìm ra lỗi
    # và chưa vượt quá số lần sửa tối đa
    needs_revision = any(fb.improvement_suggestions or fb.ambiguities or fb.edge_case_issues for fb in state["tester_feedbacks"])
    
    if needs_revision and state["revision_count"] < state["max_revisions"]:
        print(f"--- 👎 DECISION: Issues found. Proceeding to revision {state['revision_count'] + 1}. ---")
        return "refine_problem"
        
    print("--- 👍 DECISION: Problem is solid. Proceeding to final assessment. ---")
    return "finalize_problem"

# ============================================================================
# GRAPH CONSTRUCTION (XÂY DỰNG GRAPH)
# ============================================================================

def create_problem_generation_graph():
    """Tạo LangGraph workflow cho hệ thống multi-agent."""
    workflow = StateGraph(ProblemGenerationState)
    
    # 1. Thêm các node vào graph
    workflow.add_node("create_idea_data_structure", create_idea_data_structure)
    workflow.add_node("create_idea_algorithm", create_idea_algorithm)
    workflow.add_node("create_idea_math_game", create_idea_math_game)
    workflow.add_node("select_best_idea", select_best_idea)
    workflow.add_node("complete_problem_from_idea", complete_problem_from_idea)
    workflow.add_node("run_tester_an", run_tester_an)
    workflow.add_node("run_tester_binh", run_tester_binh)
    workflow.add_node("run_tester_cuong", run_tester_cuong)
    workflow.add_node("refine_complete_problem", refine_complete_problem)
    workflow.add_node("assess_final_difficulty", assess_final_difficulty)
    
    # 2. Xây dựng luồng xử lý
    
    # Giai đoạn 1: Tạo ý tưởng (chạy song song)
    workflow.add_edge(START, "create_idea_data_structure")
    workflow.add_edge(START, "create_idea_algorithm")
    workflow.add_edge(START, "create_idea_math_game")
    
    # Giai đoạn 2: Chọn ý tưởng (điểm hội tụ)
    workflow.add_edge("create_idea_data_structure", "select_best_idea")
    workflow.add_edge("create_idea_algorithm", "select_best_idea")
    workflow.add_edge("create_idea_math_game", "select_best_idea")
    
    # Giai đoạn 3: Điều hướng sau khi chọn ý tưởng
    workflow.add_conditional_edges(
        "select_best_idea",
        should_regenerate_ideas,
        {
            "regenerate_ideas": START,  # Quay lại từ đầu để tạo ý tưởng mới
            "create_problem": "complete_problem_from_idea"
        }
    )
    
    # Giai đoạn 4: Phát triển bài toán và kiểm thử (chạy song song)
    workflow.add_edge("complete_problem_from_idea", "run_tester_an")
    workflow.add_edge("complete_problem_from_idea", "run_tester_binh")
    workflow.add_edge("complete_problem_from_idea", "run_tester_cuong")
    
    # Giai đoạn 5: Điểm hội tụ sau kiểm thử và điều hướng
    # Ta cần một node trung gian để tập hợp kết quả trước khi đưa vào router
    # Tuy nhiên, LangGraph xử lý việc này ngầm. Ta chỉ cần định nghĩa các cạnh
    # đến một node và router sẽ được gọi sau khi tất cả các nhánh song song hoàn thành.
    # Trong phiên bản mới của langgraph, ta có thể trỏ trực tiếp đến conditional edge.
    workflow.add_conditional_edges(
        "run_tester_an", # Router sẽ được gọi sau khi tất cả tester chạy xong
        should_refine_problem,
        {
            "refine_problem": "refine_complete_problem",
            "finalize_problem": "assess_final_difficulty"
        }
    )
    workflow.add_edge("run_tester_binh", END) # Các nhánh song song phải kết thúc ở đâu đó
    workflow.add_edge("run_tester_cuong", END) # Node điều kiện sẽ quyết định luồng chính

    
    # Giai đoạn 6: Vòng lặp cải thiện
    # Sau khi cải thiện, quay lại bước kiểm thử
    workflow.add_edge("refine_complete_problem", "run_tester_an")
    workflow.add_edge("refine_complete_problem", "run_tester_binh")
    workflow.add_edge("refine_complete_problem", "run_tester_cuong")
    
    # Giai đoạn 7: Hoàn tất
    workflow.add_edge("assess_final_difficulty", END)
    
    # Compile graph với memory checkpointer
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app

# ============================================================================
# MAIN EXECUTION FUNCTION
# ============================================================================

def generate_problem(requirements: ProblemRequirements) -> Dict[str, Any]:
    """
    Hàm chính để chạy toàn bộ hệ thống multi-agent.
    
    Args:
        requirements: Một đối tượng ProblemRequirements chứa các yêu cầu.
    
    Returns:
        Dict chứa bài toán cuối cùng và các metadata.
    """
    app = create_problem_generation_graph()
    
    initial_state = ProblemGenerationState(
        requirements=requirements,
        all_ideas=[],
        expert_evaluations=[],
        selected_idea=None,
        complete_problem=None,
        tester_feedbacks=[],
        revision_needed=False,
        revision_count=0,
        max_revisions=2,  # Cho phép sửa tối đa 2 lần
        difficulty_assessment=None,
        final_problem=None,
        generation_metadata={},
        current_step="idea_generation",
        error_messages=[],
        status="in_progress"
    )
    
    # Chạy workflow
    config = {"configurable": {"thread_id": "problem_gen_thread_1"}}
    final_state = app.invoke(initial_state, config)
    
    return final_state

# Example usage
if __name__ == "__main__":
    # Tạo yêu cầu ban đầu
    reqs = ProblemRequirements(
        difficulty_level="Easy",
        topic="Math, Implementation",
        constraints="N <= 10000",
        special_requirements="Thừa số nguyên tố"
    )
    
    # Chạy hệ thống
    result = generate_problem(requirements=reqs)
    
    # In kết quả cuối cùng
    if result.get("final_problem"):
        print("\n✅✅✅ PROBLEM GENERATION COMPLETE! ✅✅✅")
        # In ra tóm tắt bài toán cuối cùng
        print(result["final_problem"].model_dump_json(indent=2))
    else:
        print("\n❌❌❌ PROBLEM GENERATION FAILED. ❌❌❌")
        # print(result)