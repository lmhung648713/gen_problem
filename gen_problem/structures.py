from typing import TypedDict, List, Optional, Literal, Annotated
from pydantic import BaseModel, Field
import operator

# ============================================================================
# GRAPH STATE DEFINITIONS
# ============================================================================

class ProblemRequirements(BaseModel):
    """Yêu cầu đầu vào cho việc tạo đề bài"""
    difficulty_level: str = Field(..., description="Độ khó: Easy/Medium/Hard/Expert")
    topic: str = Field(..., description="Chủ đề chính: Graph, DP, String, Math, etc.")
    constraints: str = Field(..., description="Giới hạn: n ≤ 10^5, time ≤ 2s, etc.")
    special_requirements: Optional[str] = Field(None, description="Yêu cầu đặc biệt")

class ProblemIdea(BaseModel):
    """Ý tưởng bài toán từ các nhà sáng tạo"""
    title: str = Field(..., description="Tên bài toán")
    description: str = Field(..., description="Mô tả ngắn gọn, súc tích")
    
    # Technical specs
    input_format: str = Field(..., description="Format input")
    output_format: str = Field(..., description="Format output")
    sample_input: str = Field(..., description="Input mẫu")
    sample_output: str = Field(..., description="Output mẫu")
    
    # Analysis
    key_insights: List[str] = Field(..., description="Các insight quan trọng")
    time_complexity: str = Field(..., description="Độ phức tạp thời gian")
    space_complexity: str = Field(..., description="Độ phức tạp bộ nhớ")
    engagement_factor: str = Field(..., description="Tại sao bài này thú vị")
    
    # Metadata
    prerequisite_knowledge: List[str] = Field(default_factory=list, description="Kiến thức tiên quyết")

class ExpertEvaluation(BaseModel):
    """Đánh giá từ chuyên gia"""
    selected_idea_index: int = Field(..., description="Index của ý tưởng được chọn")
    score: float = Field(..., ge=0, le=10, description="Điểm đánh giá (0-10)")
    
    # Detailed scoring
    algorithm_score: float = Field(..., ge=0, le=30, description="Điểm thuật toán (0-30)")
    creativity_score: float = Field(..., ge=0, le=25, description="Điểm sáng tạo (0-25)")
    clarity_score: float = Field(..., ge=0, le=20, description="Điểm rõ ràng (0-20)")
    difficulty_appropriateness: float = Field(..., ge=0, le=15, description="Điểm phù hợp độ khó (0-15)")
    implementability_score: float = Field(..., ge=0, le=10, description="Điểm khả thi (0-10)")
    
    # Feedback
    strengths: List[str] = Field(..., description="Điểm mạnh")
    weaknesses: List[str] = Field(..., description="Điểm yếu")
    rejection_reason: Optional[str] = Field(None, description="Lý do từ chối (nếu có)")

class CompleteProblem(BaseModel):
    """Đề bài hoàn chỉnh"""
    # Basic info
    title: str = Field(..., description="Tên bài toán")
    problem_statement: str = Field(..., description="Đề bài chi tiết")
    
    # IO Specification
    input_specification: str = Field(..., description="Mô tả input chi tiết")
    output_specification: str = Field(..., description="Mô tả output chi tiết")
    
    # Examples
    sample_cases: List[dict] = Field(..., description="Các test case mẫu")
    explanation: Optional[str] = Field(None, description="Giải thích sample cases")
    
    # Solution
    solution_approach: str = Field(..., description="Hướng giải quyết")
    solution_code: str = Field(..., description="Code mẫu")
    time_complexity: str = Field(..., description="Độ phức tạp thời gian")
    space_complexity: str = Field(..., description="Độ phức tạp bộ nhớ")
    
    # Test cases
    test_cases: List[dict] = Field(..., description="Bộ test cases đầy đủ")
    edge_cases: List[dict] = Field(..., description="Các edge cases quan trọng")
    
    # Metadata
    difficulty_level: str = Field(..., description="Độ khó cuối cùng")
    estimated_solve_time: int = Field(..., description="Thời gian giải dự kiến")
    tags: List[str] = Field(..., description="Tags phân loại")

class TesterFeedback(BaseModel):
    """Feedback từ thí sinh ảo"""
    tester_id: int = Field(..., description="ID của tester")
    tester_level: str = Field(..., description="Trình độ của tester")
    
    # Test results
    solved: bool = Field(..., description="Có giải được không")
    solve_time: Optional[int] = Field(None, description="Thời gian giải (phút)")
    attempts: int = Field(..., description="Số lần thử")
    
    # Detailed feedback
    understanding_clarity: float = Field(..., ge=1, le=5, description="Độ rõ ràng đề bài (1-5)")
    difficulty_perception: str = Field(..., description="Cảm nhận về độ khó")
    
    # Issues found
    ambiguities: List[str] = Field(default_factory=list, description="Điểm không rõ ràng")
    edge_case_issues: List[str] = Field(default_factory=list, description="Vấn đề edge cases")
    test_case_problems: List[str] = Field(default_factory=list, description="Vấn đề test cases")
    
    # Suggestions
    improvement_suggestions: List[str] = Field(default_factory=list, description="Gợi ý cải thiện")
    additional_examples_needed: bool = Field(False, description="Cần thêm ví dụ không")

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
    required_algorithms: List[str] = Field(..., description="Thuật toán cần thiết")
    key_challenges: List[str] = Field(..., description="Thách thức chính")
    prerequisite_knowledge: List[str] = Field(..., description="Kiến thức tiên quyết")
    potential_pitfalls: List[str] = Field(..., description="Lỗi thường gặp")
    
    # Recommendations  
    target_audience: str = Field(..., description="Đối tượng phù hợp")
    estimated_solve_time: int = Field(..., description="Thời gian giải ước tính")

class ProblemGenerationState(TypedDict):
    """State chính của toàn bộ hệ thống"""
    
    # Input requirements
    requirements: ProblemRequirements
    
    # Ideas from creators
    ideas: List[ProblemIdea]
    
    # Expert evaluation
    # expert_evaluations: List[ExpertEvaluation]
    selected_idea: Optional[ProblemIdea]
    regeneration_needed: bool
    regeneration_count: int
    max_regenerations: int
    
    # Problem development
    complete_problem: Optional[CompleteProblem]
    
    # Testing phase
    tester_feedbacks: List[TesterFeedback]
    revision_needed: bool
    revision_count: int
    max_revisions: int  # Limit để tránh infinite loop
    
    # Assessment
    difficulty_assessment: Optional[DifficultyAssessment]
    
    # Final output
    final_problem: Optional[CompleteProblem]
    # generation_metadata: dict  # Metadata về quá trình tạo
    
    # Control flow
    current_step: str  # Track current step for debugging
    # error_messages: Annotated[List[str], operator.add]
    status: Literal["in_progress", "completed", "failed"]