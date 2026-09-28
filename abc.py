import pandas as pd

df = pd.read_csv(
    "data/analysis/overall_performance_analysis.csv"
)

print(
    df["Performance_Category"]
    .value_counts()
)

print("\nScores <= 40:")
print(
    (df["Overall_Performance_Score"] <= 40).sum()
)

print("\nTotal students:")
print(
    df["Student_ID"].nunique()
)