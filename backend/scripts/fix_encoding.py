import os

file_path = "backend/app/services/trial_generation_service.py"

try:
    with open(file_path, "rb") as f:
        content = f.read()

    # Try to decode as UTF-16 LE
    try:
        text = content.decode("utf-16-le")
        print("Detected UTF-16 LE")
    except:
        try:
            text = content.decode("utf-16-be")
            print("Detected UTF-16 BE")
        except:
            # Fallback to utf-8 (maybe it has mixed line endings or null bytes)
            text = content.decode("utf-8", errors="ignore")
            print("Fallback to UTF-8 (ignoring errors)")

    # Normalize line endings to \n
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove BOM if present
    if text.startswith("\ufeff"):
        text = text[1:]

    # Write back as UTF-8
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"Successfully converted {file_path} to UTF-8")

except Exception as e:
    print(f"Error: {e}")
