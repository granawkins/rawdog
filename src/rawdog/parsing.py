import ast
import json


def parse_script(response: str) -> tuple[str, str]:
    """Split the response into a message and a script.

    The function splits the response by '```' delimiters, extracting the message and script parts.
    It checks for common mistakes, such as 'python' prefix and attempts to parse the script as JSON.
    Finally, it validates the script as valid Python code using ast module.

    Args:
        response (str): The input response containing a message and optionally a script.

    Returns:
        tuple[str, str]: A tuple containing the message (or error message) and the script.
    """
    # Parse delimiter
    delimiter_count = response.count("```")
    if delimiter_count < 2:
        return response, ""

    segments = response.split("```")
    message = f"{segments[0]}\n{segments[-1]}"
    script = "```".join(segments[1:-1]).strip()  # Leave 'inner' delimiters alone

    # Check for common mistakes
    if script.startswith("python"):
        script = script[len("python"):]  # Remove 'python' prefix

    # Attempt to parse script as JSON
    try:
        script = json.loads(script)
    except json.JSONDecodeError:
        pass

    # Validate the script as valid Python code
    try:
        ast.parse(script)
    except SyntaxError as e:
        return f"Script contains invalid Python:\n{e}", ""

    return message, script
