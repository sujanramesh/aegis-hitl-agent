import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.tools.service_health import get_service_health
from app.tools.deployments import get_recent_deployments
from app.tools.log_search import search_logs


# Load environment variables from .env
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is not configured")


# Create Gemini client
client = genai.Client(api_key=api_key)


# Tools Gemini is allowed to request
AVAILABLE_TOOLS = [
    get_service_health,
    get_recent_deployments,
    search_logs,
]


# Actual Python functions Aegis is allowed to execute
TOOL_REGISTRY = {
    "get_service_health": get_service_health,
    "get_recent_deployments": get_recent_deployments,
    "search_logs": search_logs,
}


def generate_response(prompt: str) -> str:
    """
    Generate a standard LLM response without operational tools.
    """

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    return response.text


def investigate_incident(prompt: str) -> str:
    """
    Investigate an operational incident using available tools.

    Gemini decides which tools it wants to use, while Aegis
    retains control over the actual execution of those tools.
    """

    config = types.GenerateContentConfig(
        tools=AVAILABLE_TOOLS,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(
            disable=True
        )
    )

    # Initial conversation containing the incident
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt)
            ]
        )
    ]

    # Maximum of 5 reasoning/tool iterations
    for _ in range(5):

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=contents,
            config=config
        )

        function_calls = response.function_calls

        # If Gemini requests no more tools,
        # return its final investigation.
        if not function_calls:
            return response.text

        # Preserve Gemini's function-call request
        # in the conversation history.
        contents.append(
            response.candidates[0].content
        )

        # Execute every tool requested by Gemini.
        for function_call in function_calls:

            tool = TOOL_REGISTRY.get(
                function_call.name
            )

            # Reject tools that are not registered.
            if tool is None:
                result = {
                    "error": (
                        f"Unknown tool: "
                        f"{function_call.name}"
                    )
                }

            else:
                try:
                    result = tool(
                        **function_call.args
                    )

                except Exception as error:
                    result = {
                        "error": str(error)
                    }

            # Convert the Python tool result into
            # a structured Gemini function response.
            function_response = (
                types.Part.from_function_response(
                    name=function_call.name,
                    response={
                        "result": result
                    }
                )
            )

            # Send the tool result back to Gemini.
            #
            # For the Gemini endpoint/model currently
            # being used by Aegis, function responses
            # are returned under the "user" role.
            contents.append(
                types.Content(
                    role="user",
                    parts=[
                        function_response
                    ]
                )
            )

    return (
        "Investigation stopped after reaching "
        "the maximum number of tool iterations."
    )