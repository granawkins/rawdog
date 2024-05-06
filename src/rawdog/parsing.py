import ast
import json
import re


def parse_script(response: str) -> tuple[str, str]:
    """Split the response into a message and a script, handling variations of 'python' prefix and JSON content.

    Args:
        response (str): The input response containing a message and optionally a script.

    Returns:
        tuple[str, str]: A tuple containing the message (or error message) and the script, if valid.
    """
    try:
        # Extract message and script using split on triple backticks
        parts = response.split('```')
        if len(parts) < 3:
            return response, ""  # Not enough parts, return original message and empty script
        
        # Clean and identify parts
        message = parts[0] + parts[-1]  # Consider the first and last parts as the message
        script = '```'.join(parts[1:-1]).strip()  # Join any inner parts as the script

        # Remove 'python' or similar prefixes from the script
        script = re.sub(r"^\s*python[0-9]*\s*", "", script, flags=re.IGNORECASE)

        # Attempt to interpret script as JSON, revert if it fails
        try:
            parsed_script = json.loads(script)
            script = json.dumps(parsed_script)  # Convert back to string to validate as Python code
        except json.JSONDecodeError:
            pass  # Keep script as is if not JSON

        # Validate as Python code
        ast.parse(script)
        return message, script
    except SyntaxError as e:
        return f"Error in Python syntax: {e}", ""
    except Exception as e:
        return f"Unhandled error: {e}", ""
