from grader import grade_submission

results = grade_submission(
    submission_file="solution.py",
    input_folder="inputs", 
    output_folder="outputs",
    timeout=5,
    verbose=True
)

print(results)