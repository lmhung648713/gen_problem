import json
from models import *
from prompts import *
from structures import *

def create_problem_idea(creator: str, problem_requirements: ProblemRequirements) -> ProblemIdea:
    """
    Creates a problem idea based on the creator and problem requirements
    """
    
    llm = gpt_4o_mini(temperature=0.7).with_structured_output(ProblemIdea)
    prompt = CREATOR_PROMPTS[creator].format(problem_requirements=problem_requirements.model_dump_json())
    response = llm.invoke(prompt)
    return response

def evaluate_problem_idea(problem_requirements: ProblemRequirements, problem_idea: ProblemIdea) -> ExpertEvaluation:
    """
    Evaluates a problem idea based on the problem requirements
    """
    
    llm = gemini_2_5_pro(temperature=0.6).with_structured_output(ExpertEvaluation)
    prompt = problem_evaluator_prompt.format(problem_requirements=problem_requirements.model_dump_json(),
                                            problem_idea=problem_idea.model_dump_json())
    response = llm.invoke(prompt)
    return response

def complete_problem(problem_idea: ProblemIdea, problem_requirements: ProblemRequirements) -> CompleteProblem:
    """
    Completes a problem idea
    """
    
    llm = gemini_2_5_pro(temperature=0.6).with_structured_output(CompleteProblem)
    prompt = problem_completer_prompt.format(problem_idea=problem_idea.model_dump_json(),
                                            problem_requirements=problem_requirements.model_dump_json())
    response = llm.invoke(prompt)
    return response

def test_problem(tester: str,complete_problem: CompleteProblem) -> TesterFeedback:
    """
    Tests a complete problem
    """
    
    llm = gemini_2_flash(temperature=0.4).with_structured_output(TesterFeedback)
    prompt = TESTER_PROMPT[tester].format(complete_problem=complete_problem.model_dump_json())
    response = llm.invoke(prompt)
    return response

def reflect_on_feedback(complete_problem: CompleteProblem ,tester_feedbacks: List[TesterFeedback]) -> CompleteProblem:
    """
    Reflects on tester feedback
    """
    # SỬA LỖI: Lớp output được sửa thành CompleteProblem
    llm = gemini_2_5_pro(temperature=0.5).with_structured_output(CompleteProblem)
    
    # SỬA LỖI: Chuyển đổi list các Pydantic object thành JSON string đúng cách
    feedbacks_json = json.dumps([fb.model_dump() for fb in tester_feedbacks])
    
    prompt = reflect_prompt.format(tester_feedbacks=feedbacks_json,
                                   complete_problem=complete_problem.model_dump_json())
    response = llm.invoke(prompt)
    return response

if __name__ == "__main__":
    problem_requirements = ProblemRequirements(
        difficulty_level="Easy",
        topic="Math, Implementation",
        constraints="n ≤ 100, time ≤ 1s",
        special_requirements=None
    )
    print(problem_requirements.model_dump_json(indent=2))

    prompt = algorithm_strategist_prompt.format(problem_requirements=problem_requirements.model_dump_json())
    # print(prompt) # Bỏ comment nếu muốn xem prompt đầy đủ

    # Lưu ý: Đoạn code bên dưới cần có môi trường và API key hợp lệ để chạy
    # llm = gemini_2_flash(temperature=0.7).with_structured_output(ProblemIdea)
    # response = llm.invoke(prompt)
    # print(type(response))
    # print(response.model_dump_json())