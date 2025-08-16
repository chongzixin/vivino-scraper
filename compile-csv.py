import os
import csv

def process_files():
    # Get list of all CSV files in current directory
    csv_path = './csv'
    csv_files = [f for f in os.listdir(csv_path) if f.endswith('.csv')]

    total_rows = 0
    unique_rows = 0
    seen_keys = set()
    output_rows = []
    header = None

    for filename in csv_files:
        filepath = os.path.join(csv_path, filename)
        with open(filepath, 'rb') as csvfile:
            print("Processing file: {}".format(filename))
            reader = csv.reader(csvfile)
            file_header = next(reader)
            if header is None:
                header = file_header
            # else: assume same header for all files

            for row in reader:
                total_rows += 1
                # Check duplicate based on first column truncated by last 4 chars
                key = row[0][:-4] if len(row[0]) > 4 else row[0]
                if key not in seen_keys:
                    seen_keys.add(key)
                    output_rows.append(row)
                    unique_rows += 1
            print("Processed {} rows from {}".format(total_rows, filename))

    # Write unique rows to output CSV
    output_filepath = os.path.join(csv_path, 'unique_rows.csv')
    with open(output_filepath, 'wb') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(header)
        writer.writerows(output_rows)

    print("Total rows processed: {}".format(total_rows))
    print("Total unique rows written: {}".format(unique_rows))


if __name__ == "__main__":
    process_files()
