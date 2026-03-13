Write a Python CLI script to recode and analyze Likert-scale survey responses.

Input: A CSV file with columns: respondent_id, age, gender (M/F/Other), q1 through q10 (integer values 1-5 representing Likert scale: 1=Strongly Disagree to 5=Strongly Agree).

Requirements:
1. Use argparse: --input CSV path, --output directory, --reverse-items (comma-separated list of items to reverse-code, default "q3,q5,q7")
2. Reverse-code the specified items: reverse_value = 6 - original_value (so 1→5, 2→4, 3→3, 4→2, 5→1)
3. Compute two composite scores for each respondent:
   - scale_A: mean of q1, q2, q3, q4, q5 (after recoding)
   - scale_B: mean of q6, q7, q8, q9, q10 (after recoding)
4. Compute Cronbach's alpha reliability for each scale: alpha = (k/(k-1)) * (1 - sum(item_variances) / total_variance)
   where k = number of items, item_variances = variance of each item, total_variance = variance of the sum of items
5. Perform group comparison by gender: compute mean and standard deviation of each composite score per gender group
6. Output files:
   - recoded_responses.csv: original data + reverse-coded items (renamed as q3_r, etc.) + scale_A, scale_B columns
   - reliability.json: {scale_A: {alpha, n_items, items}, scale_B: {alpha, n_items, items}}
   - group_comparison.json: {gender_group: {scale_A_mean, scale_A_std, scale_B_mean, scale_B_std, n}}
7. Print: Cronbach's alpha for each scale, group means
