import os
import sys


def update_iso3_in_file(iso3, file_path="pipelines/iso3.txt"):
    iso3 = iso3.lower()
    try:
        with open(file_path, "r") as f:
            content = f.read().strip()
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        sys.exit(1)

    iso3_codes = [code.strip(" \"'") for code in content.split(",")]
    if iso3 in iso3_codes:
        print(f"ISO3 code {iso3} already exists in {file_path}")
        return False

    iso3_codes.append(iso3)
    formatted_codes = ", ".join([f'"{code}"' for code in iso3_codes])

    with open(file_path, "w") as f:
        f.write(formatted_codes)
    print(f"ISO3 code {iso3} added to {file_path}")
    return True


if __name__ == "__main__":
    iso3 = sys.argv[1]
    github_output = os.environ.get("GITHUB_OUTPUT")

    was_added = update_iso3_in_file(iso3)
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"exists={'false' if was_added else 'true'}\n")
