from models import *
from prompts import *
from structures import *
import sys
import io

def create_problem_idea(creator: str, problem_requirements: ProblemRequirements) -> ProblemIdea:
    """
    Creates a problem idea based on the creator and problem requirements
    """
    llm = gemini_2_flash(temperature=0.7).with_structured_output(ProblemIdea)
    prompt = CREATOR_PROMPTS[creator].format(problem_requirements=problem_requirements.model_dump_json())
    response = llm.invoke(prompt)
    return response

def evaluate_problem_idea(problem_requirements: ProblemRequirements, problem_idea: ProblemIdea) -> ExpertEvaluation:
    """
    Evaluates a problem idea based on the problem requirements
    """
    llm = gemini_2_flash(temperature=0.7).with_structured_output(ProblemIdea)
    prompt = problem_evaluator_prompt.format(problem_requirements=problem_requirements.model_dump_json(),
                                            problem_idea=problem_idea.model_dump_json())
    response = llm.invoke(prompt)
    return response

def complete_problem(problem_idea: ProblemIdea) -> CompleteProblem:
    """
    Completes a problem idea
    """
    llm = gemini_2_flash(temperature=0.7).with_structured_output(ProblemIdea)
    prompt = problem_completer_prompt.format(problem_idea=problem_idea.model_dump_json())
    response = llm.invoke(prompt)
    return response

def test_problem(tester: str,complete_problem: CompleteProblem) -> TesterFeedback:
    """
    Tests a complete problem
    """
    llm = gemini_2_flash(temperature=0.7).with_structured_output(ProblemIdea)
    prompt = TESTER_PROMPT[tester].format(complete_problem=complete_problem.model_dump_json())
    response = llm.invoke(prompt)
    return response

def reflect_on_feedback(complete_problem: CompleteProblem ,tester_feedbacks: List[TesterFeedback]) -> CompleteProblem:
    """
    Reflects on tester feedback
    """
    llm = gemini_2_flash(temperature=0.7).with_structured_output(ProblemIdea)
    prompt = reflect_prompt.format(tester_feedbacks=tester_feedbacks.model_dump_json(),
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
    print(prompt)

    llm = gemini_2_flash(temperature=0.7).with_structured_output(ProblemIdea)
    
    response = llm.invoke(prompt)
    print(type(response))
    print(response.model_dump_json())