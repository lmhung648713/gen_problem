# gen_problem.py

import json
from typing import List
from langgraph.graph import StateGraph, END, START
from structures import *
from functions import *
from prompts import TESTER_PROMPT

# ============================================================================
# AGENT NODES (CÁC NODE TRONG GRAPH)
# ============================================================================

def create_problemideas_node(state: ProblemGenerationState) -> ProblemGenerationState:
    """Tạo ra các ý tưởng từ các chuyên gia khác nhau."""
    print("--- 💡 NODE: Generating new problem ideas ---")
    print(state)
    
    # SỬA ĐỔI: Dùng state.key
    state.ideas = [
        create_problem_idea("data_structure_expert", state.requirements),
        create_problem_idea("algorithm_strategist", state.requirements),
        create_problem_idea("math_game_master", state.requirements)
    ]
    if state.regeneration_needed:
        state.regeneration_count += 1
        print(f"--- 🔄 REGENERATION: Count: {state.regeneration_count} ---")
    state.regeneration_needed = False
    return state

def select_best_idea_node(state: ProblemGenerationState) ->ProblemGenerationState:
    """Đánh giá và lựa chọn ý tưởng tốt nhất."""
    print("--- 🧐 NODE: Evaluating and selecting the best idea ---")
    print(state)
    
    # SỬA ĐỔI: Dùng state.key
    evaluations = [evaluate_problem_idea(state.requirements, idea) for idea in state.ideas]
    state.expert_evaluations = evaluations

    recommended_pairs = []
    for i, evaluation in enumerate(evaluations):
        if evaluation.is_recommended:
            recommended_pairs.append({"evaluation": evaluation, "idea": state.ideas[i]})
            print(f"--- ✅ ACCEPTED: Idea '{state.ideas[i].title}' with score {evaluation.total_score} ---")
        else:
            print(f"--- ❌ REJECTED: Idea '{state.ideas[i].title}' ---")
    
    if not recommended_pairs:
        print("--- ⚠️ WARNING: No ideas were accepted by the curator. ---")
        if state.regeneration_count >= state.max_regenerations:
            print("--- ⛔️ FAILURE: Maximum regeneration limit reached. Halting. ---")
            state.status = "failed"
            return state
        state.regeneration_needed = True
        state.selected_idea = None
        return state
    
    best_pair = max(recommended_pairs, key=lambda p: p["evaluation"].total_score)
    
    state.selected_idea = best_pair["idea"]
    print(f"--- ⭐ SELECTED: Best idea is '{state.selected_idea.title}' with score {best_pair['evaluation'].total_score} ---")
    
    return state

def complete_problem_node(state: ProblemGenerationState) ->ProblemGenerationState:
    """Hoàn thiện ý tưởng đã chọn thành một bài toán đầy đủ."""
    print("--- ✍️ NODE: Developing the selected idea into a complete problem ---")
    print(state)
    
    # SỬA ĐỔI: Dùng state.key
    state.complete_problem = complete_problem(state.selected_idea)
    return state

def run_test_problem_node(state: ProblemGenerationState) ->ProblemGenerationState:
    """Thực hiện kiểm thử bài toán hoàn chỉnh với các tester ảo."""
    print("--- 🧪 NODE: Running virtual testers on the complete problem ---")
    print(state)
    
    # SỬA ĐỔI: Dùng state.key
    state.tester_feedbacks = []
    
    for tester_name in TESTER_PROMPT.keys():
        print(f"--- Testing with: {tester_name} ---")
        tester_feedback = test_problem(tester_name, state.complete_problem)
        state.tester_feedbacks.append(tester_feedback)
        
    return state

def refine_complete_problem_node(state: ProblemGenerationState) ->ProblemGenerationState:
    """Cải thiện bài toán dựa trên feedback của tester."""
    print("--- 🛠️ NODE: Refining the problem based on feedback ---")
    print(state)
    
    # SỬA ĐỔI: Dùng state.key
    state.revision_count += 1
    print(f"--- 🔄 REVISION: Count: {state.revision_count} ---")

    refined_problem = reflect_on_feedback(state.complete_problem, state.tester_feedbacks)
    state.complete_problem = refined_problem
    
    state.tester_feedbacks = []
    state.revision_needed = False
    
    return state

def finalize_problem_node(state: ProblemGenerationState) -> ProblemGenerationState:
    print(state)
    """Node cuối cùng để chuyển kết quả."""
    if state.status == "failed":
        return state
    print("\n--- 🎉 NODE: Finalizing Problem ---")
    state.final_problem = state.complete_problem
    state.status = "completed"
    state.current_step = "finished"
    return state

# ============================================================================
# ROUTING FUNCTIONS (CÁC HÀM ĐIỀU HƯỚNG)
# ============================================================================

def should_regenerate_ideas(state: ProblemGenerationState) -> str:
    """Kiểm tra xem Curator có yêu cầu tạo lại ý tưởng không."""
    print("--- 🤔 ROUTER: Checking curator's decision ---")
    # Logic đã đúng: nếu không có ý tưởng nào được chọn, tạo lại.
    if state.regeneration_needed:
        print("--- 👎 DECISION: No idea accepted. Regenerating ideas. ---")
        return "create_problemideas_node" # Sửa tên node cho nhất quán
    print("--- 👍 DECISION: Idea selected. Proceeding to completion. ---")
    return "complete_problem_node" # Sửa tên node cho nhất quán

def should_refine_problem(state: ProblemGenerationState) -> str:
    """Kiểm tra xem feedback của tester có yêu cầu chỉnh sửa không."""
    print("--- 🤔 ROUTER: Checking tester feedback ---")
    
    feedbacks = state.tester_feedbacks
    if not feedbacks:
        print("--- ✅ DECISION: No feedback yet. Finalizing problem. ---")
        return "finalize_problem"
        
    # Logic đã đúng: kiểm tra nội dung feedback để quyết định
    needs_revision = any(fb.improvement_suggestions or fb.ambiguities or fb.edge_case_issues for fb in feedbacks)
    
    if needs_revision and state.revision_count < state.max_revisions:
        print(f"--- 👎 DECISION: Issues found. Proceeding to revision {state.revision_count + 1}. ---")
        state.revision_needed = True # Cập nhật cờ ở đây
        return "refine_complete_problem_node" # Sửa tên node cho nhất quán
    
    if needs_revision:
        print(f"--- ⛔️ FAILURE: Issues still exist but max revision limit reached. Halting. ---")
        state.status = "failed"
        return "finalize_problem_node"

    print("--- 👍 DECISION: Problem is solid. Proceeding to finalization. ---")
    return "finalize_problem_node"


# ============================================================================
# GRAPH DEFINITION (ĐỊNH NGHĨA GRAPH)
# ============================================================================

def build_graph() -> StateGraph:
    workflow = StateGraph(ProblemGenerationState)

    # Thêm các node vào graph
    workflow.add_node("create_problemideas_node", create_problemideas_node)
    workflow.add_node("select_best_idea_node", select_best_idea_node)
    workflow.add_node("complete_problem_node", complete_problem_node)
    workflow.add_node("run_test_problem_node", run_test_problem_node)
    workflow.add_node("refine_complete_problem_node", refine_complete_problem_node)
    workflow.add_node("finalize_problem_node", finalize_problem_node)

    # Đặt điểm bắt đầu
    workflow.set_entry_point("create_problemideas_node")

    # Thêm các cạnh điều kiện (conditional edges)
    workflow.add_conditional_edges(
        "select_best_idea_node",
        should_regenerate_ideas,
        {
            "create_problemideas_node": "create_problemideas_node", # Loop
            "complete_problem_node": "complete_problem_node",
            "end": END
        }
    )
    workflow.add_conditional_edges(
        "run_test_problem_node",
        should_refine_problem,
        {
            "refine_complete_problem_node": "refine_complete_problem_node", # Loop
            "finalize_problem_node": "finalize_problem_node",
            "end": END
        }
    )

    # Thêm các cạnh thông thường
    workflow.add_edge("create_problemideas_node", "select_best_idea_node")
    workflow.add_edge("complete_problem_node", "run_test_problem_node")
    workflow.add_edge("refine_complete_problem_node", "run_test_problem_node") # Sau khi sửa, phải test lại
    workflow.add_edge("finalize_problem_node", END)

    # Biên dịch graph
    app = workflow.compile()
    return app

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def gen(problem_requirements: ProblemRequirements) -> ProblemGenerationState:
    # Khởi tạo trạng thái ban đầu của Graph
    initial_state = ProblemGenerationState(
        requirements=problem_requirements,
        ideas=[],
        expert_evaluations=[],
        selected_idea=None,
        regeneration_needed=False,
        regeneration_count=0,
        max_regenerations=2, # Cho phép tạo lại ý tưởng tối đa 2 lần
        complete_problem=None,
        testcases=[],
        tester_feedbacks=[],
        revision_needed=False,
        revision_count=0,
        max_revisions=2, # Cho phép sửa đề tối đa 2 lần
        final_problem=None,
        current_step="start",
        status="in_progress"
    )
    
    # Xây dựng và chạy Graph
    app = build_graph()
    print("--- 🚀 Starting Problem Generation Workflow ---")
    final_state = app.invoke(initial_state)

    # In kết quả cuối cùng
    print("\n\n--- ✨ WORKFLOW COMPLETE ✨ ---")
    if final_state["status"] == "completed":
        print("✅ Successfully generated a complete problem!")
        final_problem = final_state["final_problem"]
        # In ra dưới dạng JSON cho dễ đọc
        print("\n--- FINAL PROBLEM ---")
        print(final_problem.model_dump_json(indent=2))
    else:
        print("❌ Failed to generate a problem.")
        print("--- Last step:",final_state["current_step"], "---")
        print("--- Reason: Status is", final_state["status"], "---")

if __name__ == "__main__":
    # Định nghĩa yêu cầu ban đầu cho bài toán
    problem_requirements = ProblemRequirements(
        difficulty_level="Easy",
        topic="Math, Array",
        constraints="Bài toán xoay quanh các số nguyên dương <= 1000",
        special_requirements="Đề cập đến học sinh và kẹo"
    )

    # Tạo bài toán
    gen(problem_requirements)