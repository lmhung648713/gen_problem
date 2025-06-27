"""
Problem Generation System Models

This module contains all the data models for a competitive programming problem
generation system, including requirements, ideas, evaluations, and testing phases.
"""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, model_validator
from enum import Enum
import math
from pprint import pformat


# =============================================================================
# Enums and Constants
# =============================================================================

class OverallRating(str, Enum):
    """Overall rating levels for problem evaluation."""
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    ACCEPTABLE = "ACCEPTABLE"
    NEEDS_WORK = "NEEDS_WORK"
    REJECT = "REJECT"


class CompetitiveViability(str, Enum):
    """Competitive programming contest viability levels."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ProcessStatus(str, Enum):
    """Process status for problem generation workflow."""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# =============================================================================
# Base Classes
# =============================================================================

class BaseModel(BaseModel):
    """Enhanced base model with common configuration and display functionality."""
    
    class Config:
        use_enum_values = True
        validate_assignment = True
        extra = "forbid"
    
    def display(self) -> str:
        """Return a formatted string representation of the model."""
        class_name = self.__class__.__name__
        return f"--- {class_name} ---\n{pformat(self.model_dump())}"


class DisplayableMixin:
    """Mixin class for models that need custom display functionality."""
    
    def _format_section(self, title: str, content: str) -> str:
        """Format a section with title and content."""
        return f"\n{title}:\n{content}\n"
    
    def _format_list(self, items: List[str], prefix: str = "- ") -> str:
        """Format a list of items with optional prefix."""
        if not items:
            return "None"
        return "\n".join(f"{prefix}{item}" for item in items)


# =============================================================================
# Core Data Models
# =============================================================================

class ProblemRequirements(BaseModel):
    """Requirements specification for problem generation."""
    
    topic: str = Field(
        default="Toán, Implementation",
        description="Main topic: Graph, DP, String, Math, etc."
    )
    constraints: str = Field(
        default="",
        description="Constraints: n ≤ 10^5, time ≤ 2s, etc."
    )
    special_requirements: Optional[str] = Field(
        default="",
        description="Other special requirements"
    )


class TestCase(BaseModel):
    """Structured representation of a test case."""
    
    input_data: str = Field(..., description="Input data for test case")
    expected_output: str = Field(..., description="Expected output")
    explanation: Optional[str] = Field(None, description="Test case explanation")
    is_sample: bool = Field(False, description="Whether this is a sample case")
    is_edge_case: bool = Field(False, description="Whether this is an edge case")
    
    def display(self) -> str:
        """Display test case information in a formatted way."""
        lines = [
            "--- Test Case ---",
            f"Input: {self.input_data}",
            f"Expected Output: {self.expected_output}"
        ]
        
        if self.explanation:
            lines.append(f"Explanation: {self.explanation}")
        
        lines.append(f"Sample: {self.is_sample}, Edge Case: {self.is_edge_case}")
        
        return "\n".join(lines) + "\n"


class ProblemIdea(BaseModel, DisplayableMixin):
    """Model representing a problem idea from creators."""
    
    # Basic information
    title: str = Field(..., description="Problem title")
    description: str = Field(
        ..., 
        description="Concise description. E.g.: Given integer n, determine if n is a perfect square"
    )
    
    # Technical specifications
    input_format: str = Field(..., description="Input format specification")
    output_format: str = Field(..., description="Output format specification")
    sample_input: str = Field(..., description="Sample input")
    sample_output: str = Field(..., description="Sample output")
    
    # Analysis
    key_insights: List[str] = Field(
        default_factory=list,
        description="Key insights for solving the problem"
    )
    time_complexity: str = Field(..., description="Time complexity of the algorithm")
    space_complexity: str = Field(..., description="Space complexity of the algorithm")
    engagement_factor: str = Field(
        ..., 
        description="Why this problem is interesting and engaging"
    )
    
    # Prerequisites
    prerequisite_knowledge: List[str] = Field(
        default_factory=list,
        description="Required prerequisite knowledge"
    )
    
    def display(self) -> str:
        """Display problem idea with structured formatting."""
        sections = [
            f"=== Problem Idea: {self.title} ===",
            f"Description: {self.description}",
            f"Input Format: {self.input_format}",
            f"Output Format: {self.output_format}",
            f"Sample Input: {self.sample_input}",
            f"Sample Output: {self.sample_output}",
            f"Time Complexity: {self.time_complexity}",
            f"Space Complexity: {self.space_complexity}",
            f"Engagement Factor: {self.engagement_factor}"
        ]
        
        if self.key_insights:
            sections.append(f"Key Insights:\n{self._format_list(self.key_insights)}")
        
        if self.prerequisite_knowledge:
            sections.append(f"Prerequisites:\n{self._format_list(self.prerequisite_knowledge)}")
        
        return "\n\n".join(sections) + "\n"


class ExpertEvaluation(BaseModel, DisplayableMixin):
    """In-depth evaluation from Chief Problem Curator."""
    
    # Basic information
    problem_title: str = Field(..., description="Title of evaluated problem")
    overall_rating: OverallRating = Field(..., description="Overall rating")
    total_score: float = Field(..., ge=0, le=100, description="Total score out of 100")
    
    # Detailed scoring (total = 100 points)
    algorithm_quality: float = Field(
        ..., ge=0, le=35, 
        description="Algorithm quality and insights (0-35)"
    )
    creativity_originality: float = Field(
        ..., ge=0, le=25,
        description="Creativity and originality (0-25)"
    )
    problem_clarity: float = Field(
        ..., ge=0, le=20,
        description="Problem clarity and understandability (0-20)"
    )
    requirement_alignment: float = Field(
        ..., ge=0, le=15,
        description="Alignment with initial requirements (0-15)"
    )
    development_potential: float = Field(
        ..., ge=0, le=5,
        description="Potential for development into complete problem (0-5)"
    )
    
    # Expert feedback
    key_strengths: List[str] = Field(
        default_factory=list, max_length=4,
        description="Up to 4 key strengths"
    )
    major_concerns: List[str] = Field(
        default_factory=list, max_length=3,
        description="Up to 3 major concerns"
    )
    improvement_suggestions: List[str] = Field(
        default_factory=list, max_length=5,
        description="Up to 5 specific improvement suggestions"
    )
    
    # Decision reasoning
    decision_reasoning: str = Field(
        ..., 
        description="Detailed reasoning for this decision (2-3 sentences)"
    )
    competitive_viability: CompetitiveViability = Field(
        ..., 
        description="Viability for use in actual contest"
    )
    
    # Recommendation
    is_recommended: bool = Field(
        ..., 
        description="Whether to recommend for full problem development"
    )
    rejection_reason: Optional[str] = Field(
        None, 
        description="Detailed rejection reason (if not recommended)"
    )
    
    @model_validator(mode='after')
    def validate_scoring(self):
        """Validate that component scores sum to total score."""
        component_sum = sum([
            self.algorithm_quality,
            self.creativity_originality,
            self.problem_clarity,
            self.requirement_alignment,
            self.development_potential
        ])
        
        if not math.isclose(component_sum, self.total_score, rel_tol=1e-9):
            raise ValueError(
                f"Component scores ({component_sum}) must equal total_score ({self.total_score})"
            )
        return self
    
    @model_validator(mode='after')
    def validate_rejection_reason(self):
        """Ensure rejection reason is provided when and only when not recommended."""
        if not self.is_recommended and not self.rejection_reason:
            raise ValueError("Must provide 'rejection_reason' when 'is_recommended' is False")
        
        if self.is_recommended and self.rejection_reason:
            raise ValueError("'rejection_reason' should only be provided when 'is_recommended' is False")
        
        return self
    
    def display(self) -> str:
        """Display expert evaluation with detailed formatting."""
        sections = [
            f"=== Expert Evaluation: {self.problem_title} ===",
            f"Overall Rating: {self.overall_rating.value}",
            f"Total Score: {self.total_score}/100",
            "",
            "Detailed Scoring:",
            f"  Algorithm Quality: {self.algorithm_quality}/35",
            f"  Creativity: {self.creativity_originality}/25",
            f"  Problem Clarity: {self.problem_clarity}/20",
            f"  Requirement Alignment: {self.requirement_alignment}/15",
            f"  Development Potential: {self.development_potential}/5",
            "",
            f"Competitive Viability: {self.competitive_viability.value}",
            f"Recommended: {self.is_recommended}",
            f"Decision Reasoning: {self.decision_reasoning}"
        ]
        
        if self.key_strengths:
            sections.extend(["", f"Key Strengths:\n{self._format_list(self.key_strengths)}"])
        
        if self.major_concerns:
            sections.extend(["", f"Major Concerns:\n{self._format_list(self.major_concerns)}"])
        
        if self.improvement_suggestions:
            sections.extend(["", f"Improvement Suggestions:\n{self._format_list(self.improvement_suggestions)}"])
        
        if self.rejection_reason:
            sections.extend(["", f"Rejection Reason: {self.rejection_reason}"])
        
        return "\n".join(sections) + "\n"


class CompleteProblem(BaseModel, DisplayableMixin):
    """Complete problem description ready for use."""
    
    # Basic information
    title: str = Field(..., description="Problem title")
    problem_statement: str = Field(
        ..., 
        description="Detailed problem statement embedded in a story"
    )
    
    # I/O specifications
    input_specification: str = Field(..., description="Detailed input format description")
    output_specification: str = Field(..., description="Detailed output format description")
    
    # Examples
    test_cases: List[TestCase] = Field(
        ..., min_length=1,
        description="List of test cases (minimum 2)"
    )
    
    # Solution
    approach: str = Field(
        ..., 
        description="Analysis of approach and algorithm for solving"
    )
    code: str = Field(..., description="Sample source code in Python")
    time_complexity: str = Field(..., description="Time complexity of solution")
    space_complexity: str = Field(..., description="Space complexity of solution")
    
    # Test case generators
    random_test_generator: List[str] = Field(
        default_factory=list,
        description="Programs to generate random test cases"
    )
    edge_case_generator: List[str] = Field(
        default_factory=list,
        description="Programs to generate important edge cases"
    )
    
    def display(self) -> str:
        """Display complete problem with full formatting."""
        sections = [
            f"=== Complete Problem: {self.title} ===",
            f"Problem Statement:\n{self.problem_statement}",
            f"Input Specification:\n{self.input_specification}",
            f"Output Specification:\n{self.output_specification}",
            "Sample Cases:"
        ]
        
        for case in self.test_cases:
            sections.append(case.display())
        
        sections.extend([
            f"Solution Approach:\n{self.approach}",
            f"Sample Code:\n{self.code}",
            f"Complexity: Time {self.time_complexity}, Space {self.space_complexity}"
        ])
        
        return "\n\n".join(sections) + "\n"


class TesterFeedback(BaseModel, DisplayableMixin):
    """Feedback from a virtual contestant after attempting the problem."""
    
    # Results
    solved: bool = Field(..., description="Whether the contestant solved the problem")
    
    # Detailed feedback
    understanding_clarity: float = Field(
        ..., ge=1, le=5,
        description="Problem clarity rating (1-5 scale)"
    )
    difficulty_perception: str = Field(..., description="Personal perception of difficulty")
    good_feedbacks: List[str] = Field(
        default_factory=list,
        description="Positive aspects of the problem"
    )
    bad_feedbacks: List[str] = Field(
        default_factory=list,
        description="Areas needing improvement"
    )
    
    # Issues found
    ambiguities: List[str] = Field(
        default_factory=list,
        description="Ambiguous or unclear points in the problem"
    )
    edge_case_issues: List[str] = Field(
        default_factory=list,
        description="Issues related to edge cases"
    )
    test_case_problems: List[str] = Field(
        default_factory=list,
        description="Issues with sample test cases"
    )
    
    # Suggestions
    improvement_suggestions: List[str] = Field(
        default_factory=list,
        description="Suggestions for improving the problem"
    )
    additional_examples_needed: bool = Field(
        False,
        description="Whether additional sample cases are needed"
    )
    detail_additional_examples: List[str] = Field(
        default_factory=list,
        description="Description of needed additional examples"
    )
    
    @model_validator(mode='after')
    def validate_additional_examples(self):
        """Ensure additional examples are detailed when needed."""
        if self.additional_examples_needed and not self.detail_additional_examples:
            raise ValueError(
                "Must provide 'detail_additional_examples' when 'additional_examples_needed' is True"
            )
        return self
    
    def display(self) -> str:
        """Display tester feedback with structured formatting."""
        sections = [
            "=== Tester Feedback ===",
            f"Solved: {self.solved}",
            f"Understanding Clarity: {self.understanding_clarity}/5",
            f"Difficulty Perception: {self.difficulty_perception}"
        ]
        
        feedback_sections = [
            ("Positive Feedback", self.good_feedbacks),
            ("Areas for Improvement", self.bad_feedbacks),
            ("Ambiguities", self.ambiguities),
            ("Edge Case Issues", self.edge_case_issues),
            ("Test Case Problems", self.test_case_problems),
            ("Improvement Suggestions", self.improvement_suggestions)
        ]
        
        for title, items in feedback_sections:
            if items:
                sections.extend(["", f"{title}:\n{self._format_list(items)}"])
        
        if self.additional_examples_needed:
            sections.extend([
                "",
                "Additional Examples Needed: Yes",
                f"Details:\n{self._format_list(self.detail_additional_examples)}"
            ])
        
        return "\n".join(sections) + "\n"


# =============================================================================
# Main State Management
# =============================================================================

class ProblemGenerationState(BaseModel):
    """Main state managing the entire problem generation workflow."""
    
    # Input requirements
    requirements: ProblemRequirements
    
    # Ideas from creators
    ideas: List[ProblemIdea] = Field(default_factory=list)
    
    # Expert evaluation
    expert_evaluations: List[ExpertEvaluation] = Field(default_factory=list)
    selected_idea: Optional[ProblemIdea] = None
    regeneration_needed: bool = False
    regeneration_count: int = 0
    max_regenerations: int
    
    # Problem development
    complete_problem: Optional[CompleteProblem] = None
    
    # Testing phase
    tester_feedbacks: List[TesterFeedback] = Field(default_factory=list)
    revision_needed: bool = False
    revision_count: int = 0
    max_revisions: int  # Limit to avoid infinite loops
    
    # Control flow
    current_step: str = ""
    status: ProcessStatus = ProcessStatus.IN_PROGRESS
    
    @model_validator(mode='after')
    def validate_selected_idea_exists(self):
        """Ensure selected idea exists in the ideas list."""
        if self.selected_idea:
            idea_dicts = [idea.model_dump() for idea in self.ideas]
            if self.selected_idea.model_dump() not in idea_dicts:
                raise ValueError("selected_idea must be one of the ideas in the 'ideas' list")
        return self
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the current state."""
        return {
            "current_step": self.current_step,
            "status": self.status.value,
            "ideas_count": len(self.ideas),
            "evaluations_count": len(self.expert_evaluations),
            "has_selected_idea": self.selected_idea is not None,
            "has_complete_problem": self.complete_problem is not None,
            "feedback_count": len(self.tester_feedbacks),
            "regeneration_info": f"{self.regeneration_count}/{self.max_regenerations}",
            "revision_info": f"{self.revision_count}/{self.max_revisions}",
            "regeneration_needed": self.regeneration_needed,
            "revision_needed": self.revision_needed
        }
    
    def display(self) -> str:
        """Display complete system state with organized sections."""
        sections = [
            "=== Problem Generation System State ===",
            "",
            "[Requirements]",
            self.requirements.display()
        ]
        
        # Ideas section
        sections.append("\n[Ideas Generated]")
        if not self.ideas:
            sections.append("No ideas yet.")
        else:
            for i, idea in enumerate(self.ideas, 1):
                sections.append(f"\nIdea {i}:")
                sections.append(idea.display())
        
        # Expert evaluations section
        sections.append("\n[Expert Evaluations]")
        if not self.expert_evaluations:
            sections.append("No evaluations yet.")
        else:
            for i, evaluation in enumerate(self.expert_evaluations, 1):
                sections.append(f"\nEvaluation {i}:")
                sections.append(evaluation.display())
        
        # Selected idea section
        sections.append("\n[Selected Idea]")
        if self.selected_idea:
            sections.append(self.selected_idea.display())
        else:
            sections.append("No idea selected yet.")
        
        # Complete problem section
        sections.append("\n[Complete Problem]")
        if self.complete_problem:
            sections.append(self.complete_problem.display())
        else:
            sections.append("No complete problem yet.")
        
        # Tester feedback section
        sections.append("\n[Tester Feedback]")
        if not self.tester_feedbacks:
            sections.append("No feedback yet.")
        else:
            for i, feedback in enumerate(self.tester_feedbacks, 1):
                sections.append(f"\nFeedback {i}:")
                sections.append(feedback.display())
        
        # Summary section
        sections.extend([
            "\n[Process Summary]",
            f"Current Step: {self.current_step}",
            f"Status: {self.status.value}",
            f"Regeneration: {self.regeneration_needed} ({self.regeneration_count}/{self.max_regenerations})",
            f"Revision: {self.revision_needed} ({self.revision_count}/{self.max_revisions})"
        ])
        
        return "\n".join(sections) + "\n"


# =============================================================================
# Utility Functions
# =============================================================================

def create_initial_state(
    requirements: ProblemRequirements,
    max_regenerations: int = 3,
    max_revisions: int = 3
) -> ProblemGenerationState:
    """Create an initial problem generation state with given requirements."""
    return ProblemGenerationState(
        requirements=requirements,
        max_regenerations=max_regenerations,
        max_revisions=max_revisions,
        current_step="initialization",
        status=ProcessStatus.IN_PROGRESS
    )


def validate_state_transition(
    current_state: ProblemGenerationState,
    next_step: str
) -> bool:
    """Validate if a state transition is allowed."""
    valid_transitions = {
        "initialization": ["idea_generation"],
        "idea_generation": ["expert_evaluation"],
        "expert_evaluation": ["idea_selection", "idea_regeneration"],
        "idea_selection": ["problem_development"],
        "idea_regeneration": ["idea_generation"],
        "problem_development": ["testing"],
        "testing": ["completion", "revision"],
        "revision": ["problem_development"],
        "completion": []
    }
    
    return next_step in valid_transitions.get(current_state.current_step, [])