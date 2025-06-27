"""
Problem Generation Service

This module provides a comprehensive service layer for generating competitive programming
problems using various LLM models. It includes proper error handling, logging, and
validation mechanisms.
"""

import json
import logging
from typing import List, Dict, Any, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

from models import (
    ProblemRequirements, ProblemIdea, ExpertEvaluation, 
    CompleteProblem, TesterFeedback
)
from prompts import CREATOR_PROMPTS, TESTER_PROMPT, problem_evaluator_prompt, problem_completer_prompt, reflect_prompt
from structures import o3_mini, gemini_2_5_pro


# =============================================================================
# Configuration and Constants
# =============================================================================

class LLMProvider(str, Enum):
    """Available LLM providers for different tasks."""
    O3_MINI = "o3_mini"
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
    "idea_creation": LLMConfig(LLMProvider.O3_MINI, temperature=0.7),
    "evaluation": LLMConfig(LLMProvider.GEMINI_2_5_PRO, temperature=0.6),
    "completion": LLMConfig(LLMProvider.GEMINI_2_5_PRO, temperature=0.6),
    "testing": LLMConfig(LLMProvider.O3_MINI, temperature=0.5),
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
        self.config = config or LLMConfig(LLMProvider.O3_MINI)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _get_llm_instance(self, output_type: type):
        """Get configured LLM instance with structured output."""
        try:
            if self.config.provider == LLMProvider.O3_MINI:
                return o3_mini().with_structured_output(output_type)
            elif self.config.provider == LLMProvider.GEMINI_2_5_PRO:
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
    
    def process(self, problem_idea: ProblemIdea, problem_requirements: ProblemRequirements) -> CompleteProblem:
        """Complete a problem idea into a full problem."""
        try:
            self._validate_inputs(problem_idea, problem_requirements)
            
            llm = self._get_llm_instance(CompleteProblem)
            prompt = self._build_prompt(problem_idea, problem_requirements)
            
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
    
    def _build_prompt(self, idea: ProblemIdea, requirements: ProblemRequirements) -> str:
        """Build prompt for problem completion."""
        try:
            return problem_completer_prompt.format(
                problem_idea=idea.model_dump_json(),
                problem_requirements=requirements.model_dump_json()
            )
        except Exception as e:
            raise PromptError(f"Failed to build completion prompt: {str(e)}")
    
    def _validate_response(self, response: CompleteProblem) -> None:
        """Validate the completed problem."""
        if not response.title.strip():
            raise ValidationError("Completed problem has empty title")
        if not response.problem_statement.strip():
            raise ValidationError("Completed problem has empty statement")
        if not response.sample_cases:
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
    
    def complete_problem(self, problem_idea: ProblemIdea, problem_requirements: ProblemRequirements) -> CompleteProblem:
        """Complete a problem idea into a full problem."""
        return self.completion_service.process(problem_idea, problem_requirements)
    
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


# =============================================================================
# Backwards Compatibility (Deprecated)
# =============================================================================

def create_problem_idea(creator: str, problem_requirements: ProblemRequirements) -> ProblemIdea:
    """Deprecated: Use ProblemGenerationService.create_problem_idea() instead."""
    import warnings
    warnings.warn("This function is deprecated. Use ProblemGenerationService.create_problem_idea() instead.", 
                  DeprecationWarning, stacklevel=2)
    service = ProblemGenerationService()
    return service.create_problem_idea(creator, problem_requirements)


def evaluate_problem_idea(problem_requirements: ProblemRequirements, problem_idea: ProblemIdea) -> ExpertEvaluation:
    """Deprecated: Use ProblemGenerationService.evaluate_problem_idea() instead."""
    import warnings
    warnings.warn("This function is deprecated. Use ProblemGenerationService.evaluate_problem_idea() instead.", 
                  DeprecationWarning, stacklevel=2)
    service = ProblemGenerationService()
    return service.evaluate_problem_idea(problem_requirements, problem_idea)


def complete_problem(problem_idea: ProblemIdea, problem_requirements: ProblemRequirements) -> CompleteProblem:
    """Deprecated: Use ProblemGenerationService.complete_problem() instead."""
    import warnings
    warnings.warn("This function is deprecated. Use ProblemGenerationService.complete_problem() instead.", 
                  DeprecationWarning, stacklevel=2)
    service = ProblemGenerationService()
    return service.complete_problem(problem_idea, problem_requirements)


def test_problem(tester: str, complete_problem: CompleteProblem) -> TesterFeedback:
    """Deprecated: Use ProblemGenerationService.test_problem() instead."""
    import warnings
    warnings.warn("This function is deprecated. Use ProblemGenerationService.test_problem() instead.", 
                  DeprecationWarning, stacklevel=2)
    service = ProblemGenerationService()
    return service.test_problem(tester, complete_problem)


def reflect_on_feedback(complete_problem: CompleteProblem, tester_feedbacks: List[TesterFeedback]) -> CompleteProblem:
    """Deprecated: Use ProblemGenerationService.reflect_on_feedback() instead."""
    import warnings
    warnings.warn("This function is deprecated. Use ProblemGenerationService.reflect_on_feedback() instead.", 
                  DeprecationWarning, stacklevel=2)
    service = ProblemGenerationService()
    return service.reflect_on_feedback(complete_problem, tester_feedbacks)