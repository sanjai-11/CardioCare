import pandas as pd
import random

# Load the CSV file
input_file = "updated_health_data_with_risk_scores.csv"
output_file = "updated_health_data_with_risk_scores_with_doctorID.csv"

# Read the CSV into a DataFrame
df = pd.read_csv(input_file)

# Assign a random doctorID (1, 2, or 3) to each row
df["doctorID"] = [random.choice([1, 2, 3]) for _ in range(len(df))]

# Save the updated DataFrame to a new CSV file
df.to_csv(output_file, index=False)

print(f"Updated CSV saved to {output_file}")