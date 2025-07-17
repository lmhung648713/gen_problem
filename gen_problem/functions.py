"""
Problem Generation Service

This module provides a comprehensive service layer for generating competitive programming
problems using various LLM models. It includes proper error handling, logging, and
validation mechanisms.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

from structures import (
    ProblemRequirements, ProblemIdea, ExpertEvaluation, 
    CompleteProblem, TesterFeedback
)
from prompts import CREATOR_PROMPTS, TESTER_PROMPT, problem_evaluator_prompt, problem_completer_prompt, reflect_prompt
from models import gemini_2_5_pro


# =============================================================================
# Configuration and Constants
# =============================================================================

class LLMProvider(str, Enum):
    """Available LLM providers for different tasks."""
    GEMINI_2_5_PRO = "gemini_2_5_pro"


@dataclass
class LLMConfig:
    """Configuration for LLM usage."""
    provider: LLMProvider
    temperature: float = 0.6
    max_retries: int = 3
    timeout: int = 30


# Default configurations for different tasks
DEFAULT_CONFIGS = {
    "idea_creation": LLMConfig(LLMProvider.GEMINI_2_5_PRO, temperature=0.7),
    "evaluation": LLMConfig(LLMProvider.GEMINI_2_5_PRO, temperature=0.6),
    "completion": LLMConfig(LLMProvider.GEMINI_2_5_PRO, temperature=0.6),
    "testing": LLMConfig(LLMProvider.GEMINI_2_5_PRO, temperature=0.5),
    "reflection": LLMConfig(LLMProvider.GEMINI_2_5_PRO, temperature=0.5)
}


# =============================================================================
# Exceptions
# =============================================================================

class ProblemGenerationError(Exception):
    """Base exception for problem generation errors."""
    pass


class LLMError(ProblemGenerationError):
    """Exception for LLM-related errors."""
    pass


class ValidationError(ProblemGenerationError):
    """Exception for validation errors."""
    pass


class PromptError(ProblemGenerationError):
    """Exception for prompt-related errors."""
    pass


# =============================================================================
# Base Service Classes
# =============================================================================

class BaseLLMService(ABC):
    """Abstract base class for LLM services."""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig(LLMProvider.GEMINI_2_5_PRO)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _get_llm_instance(self, output_type: type):
        """Get configured LLM instance with structured output."""
        try:
            if self.config.provider == LLMProvider.GEMINI_2_5_PRO:
                return gemini_2_5_pro(temperature=self.config.temperature).with_structured_output(output_type)
            else:
                raise LLMError(f"Unsupported LLM provider: {self.config.provider}")
        except Exception as e:
            raise LLMError(f"Failed to initialize LLM: {str(e)}") from e
    
    def _invoke_with_retry(self, llm, prompt: str, retries: int = None) -> Any:
        """Invoke LLM with retry mechanism."""
        max_retries = retries or self.config.max_retries
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                self.logger.debug(f"LLM invocation attempt {attempt + 1}/{max_retries + 1}")
                response = llm.invoke(prompt)
                self.logger.debug("LLM invocation successful")
                return response
            except Exception as e:
                last_exception = e
                self.logger.warning(f"LLM invocation attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries:
                    continue
        
        raise LLMError(f"LLM invocation failed after {max_retries + 1} attempts: {str(last_exception)}") from last_exception
    
    @abstractmethod
    def process(self, *args, **kwargs) -> Any:
        """Abstract method for processing requests."""
        pass


# =============================================================================
# Specific Service Implementations
# =============================================================================

class ProblemIdeaService(BaseLLMService):
    """Service for creating problem ideas."""
    
    def __init__(self):
        super().__init__(DEFAULT_CONFIGS["idea_creation"])
    
    def process(self, creator: str, problem_requirements: ProblemRequirements) -> ProblemIdea:
        """Create a problem idea based on creator and requirements."""
        try:
            self._validate_creator(creator)
            self._validate_requirements(problem_requirements)
            
            llm = self._get_llm_instance(ProblemIdea)
            prompt = self._build_prompt(creator, problem_requirements)
            
            self.logger.info(f"Creating problem idea with creator: {creator}")
            response = self._invoke_with_retry(llm, prompt)
            
            self._validate_response(response)
            self.logger.info("Problem idea created successfully")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to create problem idea: {str(e)}")
            raise ProblemGenerationError(f"Problem idea creation failed: {str(e)}") from e
    
    def _validate_creator(self, creator: str) -> None:
        """Validate creator exists in available prompts."""
        if creator not in CREATOR_PROMPTS:
            available_creators = list(CREATOR_PROMPTS.keys())
            raise ValidationError(f"Invalid creator '{creator}'. Available: {available_creators}")
    
    def _validate_requirements(self, requirements: ProblemRequirements) -> None:
        """Validate problem requirements."""
        if not requirements.topic.strip():
            raise ValidationError("Problem topic cannot be empty")
    
    def _build_prompt(self, creator: str, requirements: ProblemRequirements) -> str:
        """Build prompt for problem idea creation."""
        try:
            return CREATOR_PROMPTS[creator].format(
                problem_requirements=requirements.model_dump_json()
            )
        except KeyError as e:
            raise PromptError(f"Prompt template error: missing key {e}")
        except Exception as e:
            raise PromptError(f"Failed to build prompt: {str(e)}")
    
    def _validate_response(self, response: ProblemIdea) -> None:
        """Validate the generated problem idea."""
        if not response.title.strip():
            raise ValidationError("Generated problem idea has empty title")
        if not response.description.strip():
            raise ValidationError("Generated problem idea has empty description")


class ExpertEvaluationService(BaseLLMService):
    """Service for evaluating problem ideas."""
    
    def __init__(self):
        super().__init__(DEFAULT_CONFIGS["evaluation"])
    
    def process(self, problem_requirements: ProblemRequirements, problem_idea: ProblemIdea) -> ExpertEvaluation:
        """Evaluate a problem idea based on requirements."""
        try:
            self._validate_inputs(problem_requirements, problem_idea)
            
            llm = self._get_llm_instance(ExpertEvaluation)
            prompt = self._build_prompt(problem_requirements, problem_idea)
            
            self.logger.info(f"Evaluating problem idea: {problem_idea.title}")
            response = self._invoke_with_retry(llm, prompt)
            
            self._validate_response(response)
            self.logger.info("Problem evaluation completed successfully")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to evaluate problem idea: {str(e)}")
            raise ProblemGenerationError(f"Problem evaluation failed: {str(e)}") from e
    
    def _validate_inputs(self, requirements: ProblemRequirements, idea: ProblemIdea) -> None:
        """Validate input parameters."""
        if not requirements.topic.strip():
            raise ValidationError("Problem requirements topic cannot be empty")
        if not idea.title.strip():
            raise ValidationError("Problem idea title cannot be empty")
    
    def _build_prompt(self, requirements: ProblemRequirements, idea: ProblemIdea) -> str:
        """Build prompt for problem evaluation."""
        try:
            return problem_evaluator_prompt.format(
                problem_requirements=requirements.model_dump_json(),
                problem_idea=idea.model_dump_json()
            )
        except Exception as e:
            raise PromptError(f"Failed to build evaluation prompt: {str(e)}")
    
    def _validate_response(self, response: ExpertEvaluation) -> None:
        """Validate the evaluation response."""
        if response.total_score < 0 or response.total_score > 100:
            raise ValidationError(f"Invalid total score: {response.total_score}")


class ProblemCompletionService(BaseLLMService):
    """Service for completing problem ideas into full problems."""
    
    def __init__(self):
        super().__init__(DEFAULT_CONFIGS["completion"])
    
    def process(self, problem_idea: ProblemIdea, problem_requirements: ProblemRequirements, expert_evaluation: ExpertEvaluation) -> CompleteProblem:
        """Complete a problem idea into a full problem."""
        try:
            self._validate_inputs(problem_idea, problem_requirements)
            
            llm = self._get_llm_instance(CompleteProblem)
            prompt = self._build_prompt(problem_idea, problem_requirements, expert_evaluation)
            
            self.logger.info(f"Completing problem: {problem_idea.title}")
            response = self._invoke_with_retry(llm, prompt)
            
            self._validate_response(response)
            self.logger.info("Problem completion successful")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to complete problem: {str(e)}")
            raise ProblemGenerationError(f"Problem completion failed: {str(e)}") from e
    
    def _validate_inputs(self, idea: ProblemIdea, requirements: ProblemRequirements) -> None:
        """Validate input parameters."""
        if not idea.title.strip():
            raise ValidationError("Problem idea title cannot be empty")
        if not idea.description.strip():
            raise ValidationError("Problem idea description cannot be empty")
    
    def _build_prompt(self, idea: ProblemIdea, requirements: ProblemRequirements, evaluation: ExpertEvaluation) -> str:
        """Build prompt for problem completion."""
        try:
            return problem_completer_prompt.format(
                problem_idea=idea.model_dump_json(),
                problem_requirements=requirements.model_dump_json(),
                expert_evaluation=evaluation.model_dump_json()
            )
        except Exception as e:
            raise PromptError(f"Failed to build completion prompt: {str(e)}")
    
    def _validate_response(self, response: CompleteProblem) -> None:
        """Validate the completed problem."""
        if not response.title.strip():
            raise ValidationError("Completed problem has empty title")
        if not response.problem_statement.strip():
            raise ValidationError("Completed problem has empty statement")
        if not response.test_cases:
            raise ValidationError("Completed problem has no sample cases")


class ProblemTestingService(BaseLLMService):
    """Service for testing complete problems."""
    
    def __init__(self):
        super().__init__(DEFAULT_CONFIGS["testing"])
    
    def process(self, tester: str, complete_problem: CompleteProblem) -> TesterFeedback:
        """Test a complete problem using specified tester."""
        try:
            self._validate_tester(tester)
            self._validate_problem(complete_problem)
            
            llm = self._get_llm_instance(TesterFeedback)
            prompt = self._build_prompt(tester, complete_problem)
            
            self.logger.info(f"Testing problem '{complete_problem.title}' with tester: {tester}")
            response = self._invoke_with_retry(llm, prompt)
            
            self._validate_response(response)
            self.logger.info("Problem testing completed successfully")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to test problem: {str(e)}")
            raise ProblemGenerationError(f"Problem testing failed: {str(e)}") from e
    
    def _validate_tester(self, tester: str) -> None:
        """Validate tester exists in available prompts."""
        if tester not in TESTER_PROMPT:
            available_testers = list(TESTER_PROMPT.keys())
            raise ValidationError(f"Invalid tester '{tester}'. Available: {available_testers}")
    
    def _validate_problem(self, problem: CompleteProblem) -> None:
        """Validate the complete problem."""
        if not problem.title.strip():
            raise ValidationError("Problem title cannot be empty")
        if not problem.problem_statement.strip():
            raise ValidationError("Problem statement cannot be empty")
    
    def _build_prompt(self, tester: str, problem: CompleteProblem) -> str:
        """Build prompt for problem testing."""
        try:
            return TESTER_PROMPT[tester].format(
                complete_problem=problem.model_dump_json()
            )
        except KeyError as e:
            raise PromptError(f"Tester prompt template error: missing key {e}")
        except Exception as e:
            raise PromptError(f"Failed to build testing prompt: {str(e)}")
    
    def _validate_response(self, response: TesterFeedback) -> None:
        """Validate the testing feedback."""
        if response.understanding_clarity < 1 or response.understanding_clarity > 5:
            raise ValidationError(f"Invalid understanding clarity score: {response.understanding_clarity}")


class ProblemReflectionService(BaseLLMService):
    """Service for reflecting on tester feedback and improving problems."""
    
    def __init__(self):
        super().__init__(DEFAULT_CONFIGS["reflection"])
    
    def process(self, complete_problem: CompleteProblem, tester_feedbacks: List[TesterFeedback]) -> CompleteProblem:
        """Reflect on tester feedback and improve the problem."""
        try:
            self._validate_inputs(complete_problem, tester_feedbacks)
            
            llm = self._get_llm_instance(CompleteProblem)
            prompt = self._build_prompt(complete_problem, tester_feedbacks)
            
            self.logger.info(f"Reflecting on {len(tester_feedbacks)} feedback(s) for problem: {complete_problem.title}")
            response = self._invoke_with_retry(llm, prompt)
            
            self._validate_response(response)
            self.logger.info("Problem reflection completed successfully")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to reflect on feedback: {str(e)}")
            raise ProblemGenerationError(f"Problem reflection failed: {str(e)}") from e
    
    def _validate_inputs(self, problem: CompleteProblem, feedbacks: List[TesterFeedback]) -> None:
        """Validate input parameters."""
        if not problem.title.strip():
            raise ValidationError("Problem title cannot be empty")
        if not feedbacks:
            raise ValidationError("No tester feedback provided")
    
    def _build_prompt(self, problem: CompleteProblem, feedbacks: List[TesterFeedback]) -> str:
        """Build prompt for problem reflection."""
        try:
            feedbacks_json = json.dumps([fb.model_dump() for fb in feedbacks], ensure_ascii=False, indent=2)
            return reflect_prompt.format(
                tester_feedbacks=feedbacks_json,
                complete_problem=problem.model_dump_json()
            )
        except Exception as e:
            raise PromptError(f"Failed to build reflection prompt: {str(e)}")
    
    def _validate_response(self, response: CompleteProblem) -> None:
        """Validate the improved problem."""
        if not response.title.strip():
            raise ValidationError("Improved problem has empty title")
        if not response.problem_statement.strip():
            raise ValidationError("Improved problem has empty statement")


# =============================================================================
# Facade Service
# =============================================================================

class ProblemGenerationService:
    """Facade service that orchestrates all problem generation operations."""
    
    def __init__(self):
        self.idea_service = ProblemIdeaService()
        self.evaluation_service = ExpertEvaluationService()
        self.completion_service = ProblemCompletionService()
        self.testing_service = ProblemTestingService()
        self.reflection_service = ProblemReflectionService()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def create_problem_idea(self, creator: str, problem_requirements: ProblemRequirements) -> ProblemIdea:
        """Create a problem idea using specified creator."""
        return self.idea_service.process(creator, problem_requirements)
    
    def evaluate_problem_idea(self, problem_requirements: ProblemRequirements, problem_idea: ProblemIdea) -> ExpertEvaluation:
        """Evaluate a problem idea against requirements."""
        return self.evaluation_service.process(problem_requirements, problem_idea)
    
    def complete_problem(self, problem_idea: ProblemIdea, problem_requirements: ProblemRequirements, expert_evaluation: ExpertEvaluation) -> CompleteProblem:
        """Complete a problem idea into a full problem."""
        return self.completion_service.process(problem_idea, problem_requirements, expert_evaluation)
    
    def test_problem(self, tester: str, complete_problem: CompleteProblem) -> TesterFeedback:
        """Test a complete problem using specified tester."""
        return self.testing_service.process(tester, complete_problem)
    
    def reflect_on_feedback(self, complete_problem: CompleteProblem, tester_feedbacks: List[TesterFeedback]) -> CompleteProblem:
        """Reflect on tester feedback and improve the problem."""
        return self.reflection_service.process(complete_problem, tester_feedbacks)
    
    def get_available_creators(self) -> List[str]:
        """Get list of available problem creators."""
        return list(CREATOR_PROMPTS.keys())
    
    def get_available_testers(self) -> List[str]:
        """Get list of available problem testers."""
        return list(TESTER_PROMPT.keys())


# =============================================================================
# Utility Functions
# =============================================================================

def setup_logging(level: int = logging.INFO) -> None:
    """Setup logging for the problem generation service."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('problem_generation.log')
        ]
    )


def create_service_with_custom_config(configs: Dict[str, LLMConfig]) -> ProblemGenerationService:
    """Create a problem generation service with custom LLM configurations."""
    # Update default configurations
    DEFAULT_CONFIGS.update(configs)
    return ProblemGenerationService()

# Fortmat complete problem to markdown

from structures import CompleteProblem

def convert_problem_to_markdown(complete_problem: CompleteProblem) -> tuple[str, str]:
    """
    Generate markdown strings for problem statement and editorial.
    
    Args:
        complete_problem: CompleteProblem instance
        
    Returns:
        tuple: (problem_markdown, editorial_markdown)
    """
    
    # Generate problem statement markdown
    problem_sections = [
        f"# {complete_problem.title}",
        "",
        f"**Difficulty:** {complete_problem.difficulty}",
        f"**Categories:** {', '.join([cat for cat in complete_problem.algorithm_categories])}",
        f"**Estimated Time:** {complete_problem.estimated_solve_time} minutes",
        ""
    ]
    
    # Add problem statement
    problem_sections.extend([
        "## Problem Statement",
        "",
        complete_problem.problem_statement,
        ""
    ])
    
    # Add input specification
    problem_sections.extend([
        "## Input",
        "",
        complete_problem.input_specification,
        ""
    ])
    
    # Add output specification  
    problem_sections.extend([
        "## Output",
        "",
        complete_problem.output_specification,
        ""
    ])
    
    # Add constraints
    problem_sections.extend([
        "## Constraints",
        "",
        complete_problem.constraints,
        ""
    ])
    
    # Add subtasks
    problem_sections.extend([
        "## Subtasks",
        ""
    ])
    
    for subtask in complete_problem.subtasks:
        problem_sections.extend([
            f"### {subtask.name} ({subtask.points}%)",
            "",
            f"**Description:** {subtask.description}",
            f"**Constraints:** {subtask.constraints}",
            f"**Expected Approach:** {subtask.expected_approach}",
            f"**Time Complexity:** {subtask.time_complexity}",
            ""
        ])
    
    # Add sample test cases
    problem_sections.extend([
        "## Sample Test Cases",
        ""
    ])
    
    for i, test_case in enumerate(complete_problem.test_cases, 1):
        problem_sections.extend([
            f"### Sample {i}",
            "",
            "**Input:**",
            "```",
            test_case.input,
            "```",
            "",
            "**Output:**",
            "```", 
            test_case.output,
            "```",
            ""
        ])
        
        if test_case.explanation:
            problem_sections.extend([
                "**Explanation:**",
                test_case.explanation,
                ""
            ])
    
    # Add metadata if available
    if complete_problem.author or complete_problem.contest_source or complete_problem.tags:
        problem_sections.extend([
            "## Information",
            ""
        ])
        
        if complete_problem.author:
            problem_sections.append(f"**Author:** {complete_problem.author}")
        if complete_problem.contest_source:
            problem_sections.append(f"**Source:** {complete_problem.contest_source}")
        if complete_problem.tags:
            problem_sections.append(f"**Tags:** {', '.join(complete_problem.tags)}")
        problem_sections.append("")
    
    # Generate editorial markdown
    editorial_sections = [
        f"# {complete_problem.title} - Editorial",
        "",
        f"**Difficulty:** {complete_problem.difficulty}",
        f"**Categories:** {', '.join([cat for cat in complete_problem.algorithm_categories])}",
        ""
    ]
    
    # Add problem analysis
    editorial_sections.extend([
        "## Problem Analysis",
        "",
        complete_problem.editorial.problem_analysis,
        ""
    ])
    
    # Add key insights
    editorial_sections.extend([
        "## Key Insights",
        ""
    ])
    
    for i, insight in enumerate(complete_problem.editorial.key_insights, 1):
        editorial_sections.append(f"{i}. {insight}")
    editorial_sections.append("")
    
    # Add solution progression
    editorial_sections.extend([
        "## Solution Progression",
        "",
        complete_problem.editorial.solution_progression,
        ""
    ])
    
    # Add proof of correctness if available
    if complete_problem.editorial.proof_of_correctness:
        editorial_sections.extend([
            "## Proof of Correctness",
            "",
            complete_problem.editorial.proof_of_correctness,
            ""
        ])
    
    # Add implementation details
    editorial_sections.extend([
        "## Implementation Details",
        "",
        complete_problem.editorial.implementation_details,
        ""
    ])
    
    # Add solution approaches
    editorial_sections.extend([
        "## Solution Approaches",
        ""
    ])
    
    for i, solution in enumerate(complete_problem.solution_approaches, 1):
        editorial_sections.extend([
            f"### Approach {i}: {solution.name}",
            "",
            f"**Complexity:** {solution.complexity}",
            f"**Suitable for:** {', '.join(solution.suitable_for)}",
            "",
            f"**Description:**",
            solution.description,
            "",
            f"**Implementation ({solution.language}):**",
            f"```{solution.language}",
            solution.code,
            "```",
            ""
        ])
    
    # Add common pitfalls
    if complete_problem.editorial.common_pitfalls:
        editorial_sections.extend([
            "## Common Pitfalls",
            ""
        ])
        
        for pitfall in complete_problem.editorial.common_pitfalls:
            editorial_sections.append(f"- {pitfall}")
        editorial_sections.append("")
    
    # Add alternative approaches
    if complete_problem.editorial.alternative_approaches:
        editorial_sections.extend([
            "## Alternative Approaches",
            ""
        ])
        
        for i, approach in enumerate(complete_problem.editorial.alternative_approaches, 1):
            editorial_sections.append(f"{i}. {approach}")
        editorial_sections.append("")
    
    # Add test generators if available
    if complete_problem.test_generators:
        editorial_sections.extend([
            "## Test Generators",
            ""
        ])
        
        for generator in complete_problem.test_generators:
            editorial_sections.extend([
                f"### {generator.name}",
                "",
                f"**Description:** {generator.description}",
                f"**Target Subtasks:** {', '.join(generator.target_subtasks)}",
                "",
                f"**Code ({generator.language}):**",
                f"```{generator.language}",
                generator.code,
                "```",
                ""
            ])
    
    # Join sections and return
    problem_markdown = "\n".join(problem_sections)
    editorial_markdown = "\n".join(editorial_sections)
    
    return problem_markdown, editorial_markdown

# Helper function to save to files
def save_problem_to_files(complete_problem: CompleteProblem, 
                         problem_filename: str = None, 
                         editorial_filename: str = None) -> None:
    """
    Save problem and editorial to separate markdown files.
    
    Args:
        complete_problem: CompleteProblem instance
        problem_filename: Optional filename for problem (default: problem_title.md)
        editorial_filename: Optional filename for editorial (default: problem_title_editorial.md)
    """
    problem_md, editorial_md = convert_problem_to_markdown(complete_problem)
    
    # Generate default filenames if not provided
    if problem_filename is None:
        safe_title = complete_problem.title.lower().replace(' ', '_').replace('-', '_')
        problem_filename = f"{safe_title}.md"
    
    if editorial_filename is None:
        safe_title = complete_problem.title.lower().replace(' ', '_').replace('-', '_')
        editorial_filename = f"{safe_title}_editorial.md"
    
    # Save problem statement
    with open(problem_filename, 'w', encoding='utf-8') as f:
        f.write(problem_md)
    
    # Save editorial
    with open(editorial_filename, 'w', encoding='utf-8') as f:
        f.write(editorial_md)
    
    print(f"Problem saved to: {problem_filename}")
    print(f"Editorial saved to: {editorial_filename}")
