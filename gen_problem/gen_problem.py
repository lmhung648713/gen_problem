from structures import *
from functions import *

# ============================================================================
# AGENT NODES (CÁC NODE TRONG GRAPH)
# ============================================================================

def create_problemideas_node(state: ProblemGenerationState) -> ProblemGenerationState:
    data_structure_expert_idea = create_problem_idea("data_structure_expert", state["problem_requirements"])
    algorithm_strategist_idea = create_problem_idea("algorithm_strategist", state["problem_requirements"])
    math_game_master_idea = create_problem_idea("math_game_master", state["problem_requirements"])
    state["all_ideas"] = [data_structure_expert_idea, algorithm_strategist_idea, math_game_master_idea]
    if state["regeneration_needed"]:
        state["regeneration_count"] += 1

    return state

def select_best_idea_node(state: ProblemGenerationState) ->ProblemGenerationState:
    
    problem_evaluations = [evaluate_problem_idea(state["problem_requirements"], idea) for idea in state["all_ideas"]]
    acceepted_idea = [idea for idea in problem_evaluations if idea.is_recommended]
    if len(acceepted_idea) == 0:
        if state["regeneration_count"] == state["max_regenerations"]:
            state["status"] = "failed"
            return state
        state["regeneration_needed"] = True
        return state
    
    best_idea = acceepted_idea[0]
    for idea in acceepted_idea:
        if idea.score > best_idea.score:
            best_idea = idea
    state["selected_idea"] = best_idea
    return state

def complete_problem_node(state: ProblemGenerationState) ->ProblemGenerationState:
    completed_problem = complete_problem(state["selected_idea"])
    state["complete_problem"] = completed_problem
    return state

def run_test_problem_node(state: ProblemGenerationState) ->ProblemGenerationState:
    completed_problem = state["complete_problem"]
    for k in TESTER_PROMPT:
        tester_feedback = test_problem(k, completed_problem)
        state["tester_feedbacks"].append(tester_feedback)
    if len(state["tester_feedbacks"]) > 0:
        if state["revision_count"] == state["max_revisions"]:
            state["status"] = "failed"
            return state
        state["revision_needed"] = True
    return state

def refine_complete_problem_node(state: ProblemGenerationState) ->ProblemGenerationState:
    completed_problem = state["complete_problem"]
    feedbacks = state["tester_feedbacks"]
    completed_problem = reflect_on_feedback(completed_problem, feedbacks)
    state["complete_problem"] = completed_problem
    state["tester_feedbacks"] = []
    return state

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