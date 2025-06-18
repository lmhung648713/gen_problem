from typing import TypedDict, List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
import operator

# ============================================================================
# ENUMS FOR BETTER TYPE SAFETY
# ============================================================================

class DifficultyLevel(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"

class OverallRating(str, Enum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    ACCEPTABLE = "ACCEPTABLE"
    NEEDS_WORK = "NEEDS_WORK"
    REJECT = "REJECT"

# ============================================================================
# BASE MODELS
# ============================================================================

class BaseStateModel(BaseModel):
    """Base model with common configuration"""
    
    class Config:
        use_enum_values = True
        validate_assignment = True
        extra = "forbid"

class TestCase(BaseModel):
    """Structured test case representation"""
    input_data: str = Field(..., description="Input data for test case")
    expected_output: str = Field(..., description="Expected output")
    explanation: Optional[str] = Field("", description="Explanation of the test case")
    is_sample: bool = Field(False, description="Whether this is a sample case")
    is_edge_case: bool = Field(False, description="Whether this is an edge case")

# ============================================================================
# PROBLEM REQUIREMENTS AND IDEAS
# ============================================================================

class ProblemRequirements(BaseStateModel):
    """Requirements for problem generation"""
    difficulty_level: DifficultyLevel = Field(..., description="Difficulty level")
    topic: str = Field(..., description="Main topic: Graph, DP, String, Math, etc.")
    constraints: str = Field(..., description="Constraints: n ≤ 10^5, time ≤ 2s, etc.")
    special_requirements: Optional[str] = Field("", description="Special requirements")

class ProblemIdea(BaseModel):
    """Ý tưởng bài toán từ các nhà sáng tạo"""
    title: str = Field(..., description="Tên bài toán")
    description: str = Field(..., description="Mô tả ngắn gọn, súc tích. Ví dụ: Cho số nguyên n, hãy cho biết n có phải số chính phương không?")
    
    # Technical specs
    input_format: str = Field(..., description="Format input")
    output_format: str = Field(..., description="Format output")
    sample_input: str = Field(..., description="Input mẫu")
    sample_output: str = Field(..., description="Output mẫu")
    
    # Analysis
    key_insights: List[str] = Field(...,default_factory=list, description="Các insight quan trọng")
    time_complexity: str = Field(..., description="Độ phức tạp thời gian")
    space_complexity: str = Field(..., description="Độ phức tạp bộ nhớ")
    engagement_factor: str = Field(..., description="Tại sao bài này thú vị")
    
    # Metadata
    prerequisite_knowledge: List[str] = Field(default_factory=list, description="Kiến thức tiên quyết")


# ============================================================================
# EVALUATION AND SCORING
# ============================================================================

class ExpertEvaluation(BaseModel):
    """Đánh giá chuyên sâu từ Chief Problem Curator"""
    
    # Basic info
    problem_title: str = Field(..., description="Tên bài toán được đánh giá")
    overall_rating: Literal["EXCELLENT", "GOOD", "ACCEPTABLE", "NEEDS_WORK", "REJECT"] = Field(
        ..., description="Đánh giá tổng thể"
    )
    total_score: float = Field(..., ge=0, le=100, description="Tổng điểm (0-100)")
    
    # Detailed scoring (tổng = 100 điểm)
    algorithm_quality: float = Field(..., ge=0, le=35, description="Chất lượng thuật toán và insight (0-35)")
    creativity_originality: float = Field(..., ge=0, le=25, description="Tính sáng tạo và độc đáo (0-25)")
    problem_clarity: float = Field(..., ge=0, le=20, description="Độ rõ ràng và dễ hiểu (0-20)")
    requirement_alignment: float = Field(..., ge=0, le=15, description="Phù hợp với yêu cầu ban đầu (0-15)")
    development_potential: float = Field(..., ge=0, le=5, description="Tiềm năng phát triển thành bài hoàn chỉnh (0-5)")
    
    # Expert feedback
    key_strengths: List[str] = Field(...,default_factory=list, max_items=4, description="2-4 điểm mạnh nổi bật")
    major_concerns: List[str] = Field(default_factory=list, max_items=3, description="Tối đa 3 vấn đề chính (nếu có)")
    improvement_suggestions: List[str] = Field(..., default_factory=list, max_items=5, description="1-5 gợi ý cải thiện cụ thể")
    
    # Decision rationale  
    decision_reasoning: str = Field(..., description="Lý do chi tiết cho quyết định này (2-3 câu)")
    competitive_viability: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        ..., description="Khả năng sử dụng trong contest thực tế"
    )
    
    # Optional rejection
    is_recommended: bool = Field(..., description="Có đề xuất phát triển thành bài hoàn chỉnh không")
    rejection_reason: Optional[str] = Field("", description="Lý do từ chối chi tiết (nếu không recommend)")


# ============================================================================
# COMPLETE PROBLEM DEFINITION
# ============================================================================

class TestCase(BaseModel):
    input_data: str = Field(..., description="Input data for test case")
    expected_output: str = Field(..., description="Expected output")
    explanation: Optional[str] = Field("", description="Explanation of the test case")
    is_sample: bool = Field(False, description="Whether this is a sample case")
    is_edge_case: bool = Field(False, description="Whether this is an edge case")

class CompleteProblem(BaseModel):
    """Đề bài hoàn chỉnh"""
    # Basic info
    title: str = Field(..., description="Tên bài toán")
    problem_statement: str = Field(..., description="Đề bài chi tiết đã được lồng ghép vào một câu chuyện")
    
    # IO Specification
    input_specification: str = Field(..., description="Mô tả input chi tiết")
    output_specification: str = Field(..., description="Mô tả output chi tiết")
    
    # Examples
    sample_cases: List[TestCase] = Field(..., default_factory=list, description="Các test case mẫu")
    
    # Solution
    solution_approach: str = Field(..., description="Hướng giải quyết")
    solution_code: str = Field(..., description="Code mẫu Python")
    time_complexity: str = Field(..., description="Độ phức tạp thời gian")
    space_complexity: str = Field(..., description="Độ phức tạp bộ nhớ")
    
    # Test cases
    random_cases_program: List[str] = Field(..., default_factory=list, description="Chương trình sinh bộ test cases ngẫu nhiên với số lớn")
    edge_cases_program: List[str] = Field(..., default_factory=list, description="Chương trình sinh các edge cases quan trọng")
    

# ============================================================================
# FEEDBACK AND ASSESSMENT
# ============================================================================

class TesterFeedback(BaseModel):
    """Feedback từ thí sinh ảo"""
    # Test results
    solved: bool = Field(..., description="Có giải được không")
    
    # Detailed feedback
    understanding_clarity: float = Field(..., ge=1, le=5, description="Độ rõ ràng đề bài (1-5)")
    difficulty_perception: str = Field(..., description="Cảm nhận về độ khó")
    feedbacks: List[str] = Field(..., default_factory=list, description="Feedback chi tiết")
    
    # Issues found
    ambiguities: List[str] = Field(default_factory=list, description="Điểm không rõ ràng")
    edge_case_issues: List[str] = Field(default_factory=list, description="Vấn đề edge cases")
    test_case_problems: List[str] = Field(default_factory=list, description="Vấn đề test cases")
    
    # Suggestions
    improvement_suggestions: List[str] = Field(default_factory=list, description="Gợi ý cải thiện")
    additional_examples_needed: bool = Field(False, description="Cần thêm ví dụ không")
    detail_additional_examples: List[str] = Field(default_factory=list, description="Ví dụ cần bổ sung")

class DifficultyAssessment(BaseModel):
    """Đánh giá độ khó chi tiết"""
    # Detailed scoring (matching our difficulty assessment prompt)
    algorithm_score: int = Field(..., ge=1, le=30, description="Điểm thuật toán (1-30)")
    insight_score: int = Field(..., ge=1, le=25, description="Điểm độ ẩn ý (1-25)")
    complexity_score: int = Field(..., ge=1, le=20, description="Điểm độ phức tạp (1-20)")
    implementation_score: int = Field(..., ge=1, le=15, description="Điểm implementation (1-15)")
    math_score: int = Field(..., ge=1, le=10, description="Điểm toán học (1-10)")
    
    total_score: int = Field(..., ge=5, le=100, description="Tổng điểm")
    difficulty_rating: str = Field(..., description="Xếp hạng độ khó")
    estimated_rating_range: str = Field(..., description="Ước tính rating range")
    
    # Analysis
    required_algorithms: List[str] = Field(..., default_factory=list, description="Thuật toán cần thiết")
    key_challenges: List[str] = Field(..., default_factory=list, description="Thách thức chính")
    prerequisite_knowledge: List[str] = Field(..., default_factory=list, description="Kiến thức tiên quyết")
    potential_pitfalls: List[str] = Field(..., default_factory=list, description="Lỗi thường gặp")
    
    # Recommendations  
    target_audience: str = Field(..., description="Đối tượng phù hợp")
    estimated_solve_time: int = Field(..., description="Thời gian giải ước tính")

# ============================================================================
# GENERATION METADATA
# ============================================================================

class GenerationMetadata(BaseModel):
    """Metadata about the generation process"""
    generation_start_time: Optional[str] = Field("", description="Start timestamp")
    generation_end_time: Optional[str] = Field("", description="End timestamp")
    total_ideas_generated: int = Field(0, description="Total ideas generated")
    total_evaluations: int = Field(0, description="Total evaluations performed")
    regeneration_count: int = Field(0, description="Number of regenerations")
    revision_count: int = Field(0, description="Number of revisions")
    final_rating: Optional[OverallRating] = Field("", description="Final rating")

# ============================================================================
# MAIN STATE DEFINITION
# ============================================================================

class ProblemGenerationState(BaseModel):
    """State chính của toàn bộ hệ thống"""
    
    # Input requirements
    requirements: ProblemRequirements
    
    # Ideas from creators
    ideas: List[ProblemIdea] = Field(default_factory=list)
    
    # Expert evaluation
    expert_evaluations: List[ExpertEvaluation] = Field(default_factory=list)
    selected_idea: Optional[ProblemIdea] = ""
    regeneration_needed: bool = False
    regeneration_count: int = 0
    max_regenerations: int
    
    # Problem development
    complete_problem: Optional[CompleteProblem] = ""

    # Testcases
    testcases: List[dict] = Field(default_factory=list)
    
    # Testing phase
    tester_feedbacks: List[TesterFeedback] = Field(default_factory=list)
    revision_needed: bool = False
    revision_count: int = 0
    max_revisions: int  # Limit để tránh infinite loop
    
    # Final output
    final_problem: Optional[CompleteProblem] = ""
    
    # Control flow
    current_step: str = ""
    status: Literal["in_progress", "completed", "failed"] = "in_progress"