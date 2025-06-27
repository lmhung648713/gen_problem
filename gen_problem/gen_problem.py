from langgraph.graph import StateGraph, END, START
from structures import *
from services import ProblemGenerationService
from testcase_processor import create_testcase
import os
import shutil
from typing import List

# ============================================================================
# CONFIGURATION AND CONSTANTS
# ============================================================================

# Creator types for problem idea generation
CREATOR_TYPES = [
    "data_structure_expert",
    "algorithm_strategist", 
    "math_game_master"
]

# Tester types for problem evaluation
TESTER_TYPES = [
    "Statement_Tester",
    "Solution_Tester", 
    "Testcase_Tester"
]

# Default workflow limits
DEFAULT_MAX_REGENERATIONS = 2
DEFAULT_MAX_REVISIONS = 2
DEFAULT_RANDOM_CASES_PER_GENERATOR = 3

# ============================================================================
# SERVICE INITIALIZATION
# ============================================================================

class WorkflowService:
    """Service class to handle workflow operations with proper dependency injection."""
    
    def __init__(self):
        self.problem_service = ProblemGenerationService()
        
    def create_problem_ideas(self, requirements: ProblemRequirements) -> List[ProblemIdea]:
        """Generate problem ideas from multiple creators."""
        ideas = []
        for creator in CREATOR_TYPES:
            try:
                idea = self.problem_service.create_problem_idea(creator, requirements)
                ideas.append(idea)
            except Exception as e:
                print(f"⚠️ Warning: Failed to create idea from {creator}: {e}")
        return ideas
    
    def evaluate_ideas(self, requirements: ProblemRequirements, ideas: List[ProblemIdea]) -> List[ExpertEvaluation]:
        """Evaluate all problem ideas."""
        evaluations = []
        for idea in ideas:
            try:
                evaluation = self.problem_service.evaluate_problem_idea(requirements, idea)
                evaluations.append(evaluation)
            except Exception as e:
                print(f"⚠️ Warning: Failed to evaluate idea '{idea.title}': {e}")
        return evaluations
    
    def test_complete_problem(self, problem: CompleteProblem) -> List[TesterFeedback]:
        """Test complete problem with multiple testers."""
        feedbacks = []
        for tester in TESTER_TYPES:
            try:
                feedback = self.problem_service.test_problem(tester, problem)
                feedbacks.append(feedback)
            except Exception as e:
                print(f"⚠️ Warning: Failed to test with {tester}: {e}")
        return feedbacks

# Global service instance
workflow_service = WorkflowService()

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def log_state(state: ProblemGenerationState, filename: str = "logs.txt") -> None:
    """Log current state to file."""
    try:
        with open(filename, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"STEP: {state.current_step}\n")
            f.write(f"STATUS: {state.status}\n")
            f.write(f"{'='*80}\n")
            f.write(state.display())
            f.write("\n")
    except Exception as e:
        print(f"Failed to log state: {e}")

def print_section_header(title: str, icon: str = "🔹") -> None:
    """Print formatted section header."""
    print(f"\n{icon} {title.upper()} {icon}")
    print("-" * (len(title) + 6))

def select_best_recommended_idea(ideas: List[ProblemIdea], evaluations: List[ExpertEvaluation]) -> tuple[ProblemIdea, ExpertEvaluation]:
    """Select the best recommended idea from evaluations."""
    recommended_pairs = []
    
    for idea, evaluation in zip(ideas, evaluations):
        if evaluation.is_recommended:
            recommended_pairs.append((idea, evaluation))
            print(f"✅ ACCEPTED: '{idea.title}' (Score: {evaluation.total_score})")
        else:
            print(f"❌ REJECTED: '{idea.title}' - {evaluation.rejection_reason}")
    
    if not recommended_pairs:
        raise ValueError("No ideas were accepted by the curator")
    
    # Select idea with highest score
    best_idea, best_evaluation = max(recommended_pairs, key=lambda x: x[1].total_score)
    return best_idea, best_evaluation

def analyze_feedback_severity(feedbacks: List[TesterFeedback]) -> bool:
    """Analyze if feedback indicates serious issues requiring revision."""
    serious_issues = 0
    
    for feedback in feedbacks:
        # Count serious issues
        if not feedback.solved:
            serious_issues += 2  # Not solving is serious
        if feedback.understanding_clarity < 3:
            serious_issues += 1  # Poor clarity
        if len(feedback.bad_feedbacks) > 2:
            serious_issues += 1  # Multiple negative feedbacks
        if len(feedback.ambiguities) > 0:
            serious_issues += 1  # Ambiguities present
        if len(feedback.edge_case_issues) > 0:
            serious_issues += 1  # Edge case problems
    
    # Require revision if more than 2 serious issues total
    return serious_issues > 2

def generate_testcases(problem: CompleteProblem, case_id_start: int = 1) -> List[dict]:
    """Generate test cases from the complete problem."""
    testcases = []
    case_id = case_id_start
    
    # Generate random test cases
    for generator in problem.random_test_generator:
        for _ in range(DEFAULT_RANDOM_CASES_PER_GENERATOR):
            try:
                case = create_testcase(
                    case_id=case_id,
                    solution_code=problem.code,
                    input_code=generator
                )
                testcases.append(case)
                case_id += 1
            except Exception as e:
                print(f"⚠️ Warning: Failed to generate random test case: {e}")
    
    # Generate edge test cases
    for generator in problem.edge_case_generator:
        try:
            case = create_testcase(
                case_id=case_id,
                solution_code=problem.code,
                input_code=generator
            )
            testcases.append(case)
            case_id += 1
        except Exception as e:
            print(f"⚠️ Warning: Failed to generate edge test case: {e}")
    
    return testcases

# ============================================================================
# GRAPH NODES
# ============================================================================

def create_problem_ideas_node(state: ProblemGenerationState) -> ProblemGenerationState:
    """Generate new problem ideas from multiple expert creators."""
    print_section_header("Generating Problem Ideas", "💡")
    
    # Update state
    state.current_step = "idea_generation"
    
    # Generate ideas
    state.ideas = workflow_service.create_problem_ideas(state.requirements)
    
    # Display generated ideas
    for i, idea in enumerate(state.ideas, 1):
        print(f"\n--- Idea {i}: {idea.title} ---")
        print(idea.display())
    
    # Handle regeneration tracking
    if state.regeneration_needed:
        state.regeneration_count += 1
        state.regeneration_needed = False
        print(f"\n🔄 Regeneration #{state.regeneration_count} completed")
    
    log_state(state)
    return state

def evaluate_and_select_idea_node(state: ProblemGenerationState) -> ProblemGenerationState:
    """Evaluate all ideas and select the best one."""
    print_section_header("Evaluating and Selecting Best Idea", "🧐")
    
    # Update state
    state.current_step = "expert_evaluation"
    
    # Evaluate all ideas
    state.expert_evaluations = workflow_service.evaluate_ideas(state.requirements, state.ideas)
    
    # Display evaluations
    for i, evaluation in enumerate(state.expert_evaluations, 1):
        print(f"\n--- Evaluation {i} ---")
        print(evaluation.display())
    
    # Try to select best idea
    try:
        best_idea, best_evaluation = select_best_recommended_idea(state.ideas, state.expert_evaluations)
        state.selected_idea = best_idea
        state.current_step = "idea_selected"
        
        print(f"\n⭐ SELECTED: '{best_idea.title}' with score {best_evaluation.total_score}")
        
    except ValueError as e:
        print(f"\n⚠️ WARNING: {e}")
        
        # Check if we can regenerate
        if state.regeneration_count >= state.max_regenerations:
            print("⛔ FAILURE: Maximum regeneration limit reached")
            state.status = ProcessStatus.FAILED
            state.current_step = "failed"
        else:
            print(f"🔄 Marking for regeneration (attempt {state.regeneration_count + 1}/{state.max_regenerations})")
            state.regeneration_needed = True
            state.selected_idea = None
            state.current_step = "regeneration_needed"
    
    log_state(state)
    return state

def develop_complete_problem_node(state: ProblemGenerationState) -> ProblemGenerationState:
    """Develop the selected idea into a complete problem."""
    print_section_header("Developing Complete Problem", "✍️")
    
    # Update state
    state.current_step = "problem_development"
    
    # Develop complete problem
    state.complete_problem = workflow_service.problem_service.complete_problem(
        state.selected_idea, 
        state.requirements
    )
    
    print(f"\n--- Complete Problem: {state.complete_problem.title} ---")
    print(state.complete_problem.display())
    
    log_state(state)
    return state

def test_problem_node(state: ProblemGenerationState) -> ProblemGenerationState:
    """Test the complete problem with virtual testers."""
    print_section_header("Testing Problem with Virtual Testers", "🧪")
    
    # Update state
    state.current_step = "testing"
    
    # Test with multiple testers
    state.tester_feedbacks = workflow_service.test_complete_problem(state.complete_problem)
    
    # Display feedback
    for i, feedback in enumerate(state.tester_feedbacks, 1):
        print(f"\n--- Tester Feedback {i} ---")
        print(feedback.display())
    
    log_state(state)
    return state

def refine_problem_node(state: ProblemGenerationState) -> ProblemGenerationState:
    """Refine the problem based on tester feedback."""
    print_section_header("Refining Problem Based on Feedback", "🛠️")
    
    # Update state
    state.current_step = "revision"
    state.revision_count += 1
    
    print(f"🔄 Revision #{state.revision_count}")
    
    # Refine the problem
    state.complete_problem = workflow_service.problem_service.reflect_on_feedback(
        state.complete_problem, 
        state.tester_feedbacks
    )
    
    print(f"\n--- Refined Problem: {state.complete_problem.title} ---")
    print(state.complete_problem.display())
    
    # Reset for next testing round
    state.tester_feedbacks = []
    state.revision_needed = False
    
    log_state(state)
    return state

def finalize_problem_node(state: ProblemGenerationState) -> ProblemGenerationState:
    """Finalize the problem generation process."""
    print_section_header("Finalizing Problem", "🎉")
    
    if state.status == ProcessStatus.FAILED:
        print("❌ Problem generation failed")
        return state
    
    # Update state to completed
    state.status = ProcessStatus.COMPLETED
    state.current_step = "completed"
    
    print("✅ Problem generation completed successfully!")
    
    # Display final summary
    summary = state.get_summary()
    print("\n--- Final Summary ---")
    for key, value in summary.items():
        print(f"{key}: {value}")
    
    log_state(state)
    return state

# ============================================================================
# ROUTING FUNCTIONS
# ============================================================================

def route_after_evaluation(state: ProblemGenerationState) -> str:
    """Route after idea evaluation - either regenerate or proceed."""
    print_section_header("Routing Decision After Evaluation", "🤔")
    
    if state.status == ProcessStatus.FAILED:
        print("❌ Process failed - routing to finalization")
        return "finalize"
    
    if state.regeneration_needed:
        print("🔄 No acceptable ideas - routing to regeneration")
        return "regenerate"
    
    print("✅ Good idea selected - routing to development")
    return "develop"

def route_after_testing(state: ProblemGenerationState) -> str:
    """Route after testing - either refine or finalize."""
    print_section_header("Routing Decision After Testing", "🤔")
    
    # Analyze feedback to determine if revision is needed
    needs_revision = analyze_feedback_severity(state.tester_feedbacks)
    
    if needs_revision and state.revision_count < state.max_revisions:
        print(f"🔧 Issues found - routing to revision (attempt {state.revision_count + 1}/{state.max_revisions})")
        state.revision_needed = True
        return "refine"
    
    if needs_revision and state.revision_count >= state.max_revisions:
        print("⚠️ Issues found but max revisions reached - proceeding to finalization")
    else:
        print("✅ Problem is ready - routing to finalization")
    
    return "finalize"

# ============================================================================
# GRAPH CONSTRUCTION
# ============================================================================

def build_problem_generation_graph() -> StateGraph:
    """Build and return the problem generation workflow graph."""
    workflow = StateGraph(ProblemGenerationState)
    
    # Add nodes
    workflow.add_node("create_ideas", create_problem_ideas_node)
    workflow.add_node("evaluate_select", evaluate_and_select_idea_node)
    workflow.add_node("develop_problem", develop_complete_problem_node)
    workflow.add_node("test_problem", test_problem_node)
    workflow.add_node("refine_problem", refine_problem_node)
    workflow.add_node("finalize", finalize_problem_node)
    
    # Set entry point
    workflow.set_entry_point("create_ideas")
    
    # Add edges
    workflow.add_edge("create_ideas", "evaluate_select")
    workflow.add_edge("develop_problem", "test_problem")
    workflow.add_edge("refine_problem", "test_problem")
    workflow.add_edge("finalize", END)
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "evaluate_select",
        route_after_evaluation,
        {
            "regenerate": "create_ideas",
            "develop": "develop_problem", 
            "finalize": "finalize"
        }
    )
    
    workflow.add_conditional_edges(
        "test_problem",
        route_after_testing,
        {
            "refine": "refine_problem",
            "finalize": "finalize"
        }
    )
    
    return workflow.compile()

# ============================================================================
# MAIN EXECUTION FUNCTION
# ============================================================================

def generate_problem(
    topic: str,
    constraints: str = "",
    special_requirements: str = "",
    max_regenerations: int = DEFAULT_MAX_REGENERATIONS,
    max_revisions: int = DEFAULT_MAX_REVISIONS
) -> dict:
    """
    Generate a complete competitive programming problem.
    
    Args:
        topic: Main topic (e.g., "Graph", "DP", "String", "Math")
        constraints: Problem constraints (e.g., "n ≤ 10^5, time ≤ 2s")
        special_requirements: Additional requirements
        max_regenerations: Maximum idea regeneration attempts
        max_revisions: Maximum problem revision attempts
        
    Returns:
        Dictionary containing the complete problem or empty dict if failed
    """
    print_section_header("Starting Problem Generation Workflow", "🚀")
    
    # Initialize requirements
    requirements = ProblemRequirements(
        topic=topic,
        constraints=constraints,
        special_requirements=special_requirements
    )
    
    # Initialize state
    initial_state = ProblemGenerationState(
        requirements=requirements,
        max_regenerations=max_regenerations,
        max_revisions=max_revisions,
        current_step="initialization",
        status=ProcessStatus.IN_PROGRESS
    )
    
    # Build and run workflow
    app = build_problem_generation_graph()
    final_state = app.invoke(initial_state)
    
    # Check final status
    if final_state.status == ProcessStatus.FAILED:
        print_section_header("Problem Generation Failed", "❌")
        return {}
    
    # Extract complete problem
    problem = final_state.complete_problem
    if not problem:
        print_section_header("No Complete Problem Generated", "⚠️")
        return {}
    
    # Generate test cases
    print_section_header("Generating Test Cases", "📝")
    testcases = generate_testcases(problem)
    print(f"Generated {len(testcases)} test cases")
    
    print_section_header("Problem Generation Completed Successfully", "✅")
    
    # Return formatted result
    return {
        "title": problem.title,
        "problem_statement": problem.problem_statement,
        "input_specification": problem.input_specification,
        "output_specification": problem.output_specification,
        "sample_cases": [case.model_dump() for case in problem.test_cases],
        "solution_approach": problem.approach,
        "solution_code": problem.code,
        "time_complexity": problem.time_complexity,
        "space_complexity": problem.space_complexity,
        "testcases": testcases,
        "generation_summary": final_state.get_summary()
    }

# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example usage
    result = generate_problem(
        topic="unweighted graph",
        constraints="n ≤ 100000",
        special_requirements="đi ăn sinh nhật, ghé tiệm mua quà"
    )
    
    if result:
        print(f"\nGenerated problem: {result['title']}")
        print(f"Test cases: {len(result['testcases'])}")
        print("Success!")
    else:
        print("Failed to generate problem")