import csv
import os
import sys

# Increase the CSV field size limit to handle large email bodies
# On Windows, sys.maxsize can exceed C long limits, so we use the max 32-bit integer
csv.field_size_limit(2147483647)

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# Construct the full path to the CSV file
file_path = os.path.join(script_dir, 'final_cleaned_dataset.csv')

expected_column_count = 5  # subject, body, has_urls, label, source_dataset

if not os.path.exists(file_path):
    print(f"❌ Error: File not found at {file_path}")
    exit(1)

print(f"Checking file: {file_path}...")

with open(file_path, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader, None)  # Skip the header row
    
    if header and len(header) != expected_column_count:
         print(f"⚠️ Warning: Header has {len(header)} columns, expected {expected_column_count}")

    error_count = 0
    for i, row in enumerate(reader, start=2): # Start counting from line 2 (since line 1 is header)
        if len(row) != expected_column_count:
            print(f"⚠️ Error at Line {i}: Found {len(row)} columns instead of {expected_column_count}")
            print(f"Row Content Snippet: {row[:2]}...")
            error_count += 1

    if error_count == 0:
        print("✅ Success! All rows have the correct column count.")
    else:
        print(f"❌ Found {error_count} broken rows.")
