"""
Week 5: Agent Architecture Starter Template

Build an AI agent that answers TechCorp questions using:
- Gemini 2.5 Pro LLM (free tier via Google AI API)
- SQLite database queries
- Policy document retrieval

Complete the TODO sections marked below.
"""

import json
import sqlite3
from typing import Dict, Any
import google.genai as genai
from google.genai import types
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")


# TASK 1: Implement the Tool base class


class Tool:
    """Base class for tools the agent can call."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def execute(self, **kwargs) -> str:
        """Execute the tool.

        TODO: This is implemented by subclasses.
        Each subclass should override this method.
        """
        raise NotImplementedError


# TASK 2: Implement EmployeeLookupTool


class EmployeeLookupTool(Tool):
    """Look up employee information from SQLite database."""

    def __init__(self, db_path: str):
        super().__init__("employee_lookup", "Find employee information by name or ID")
        self.db_path = db_path

    def execute(self, employee_name: str = None, employee_id: str = None) -> str:
        """Look up employee by name or ID.

        TODO: Query the employees table:
        1. Connect to SQLite database at self.db_path
        2. If employee_id is provided:
           - SELECT * FROM employees WHERE id = ?
        3. If employee_name is provided:
           - SELECT * FROM employees WHERE name LIKE ?
        4. Convert results to JSON and return
        5. If no results found, return "Employee not found"

        Args:
            employee_name: Name to search for (partial match ok)
            employee_id: ID to search for (exact match)

        Returns:
            JSON string with employee info or error message
        """
        try:
            connection = sqlite3.connect(self.db_path)
            database_cursor = connection.cursor()

            if employee_id:
                database_cursor.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))

            elif employee_name:
                database_cursor.execute(
                    "SELECT * FROM employees WHERE name LIKE ?",
                    (f"%{employee_name}%",)
                )
            else:
                return "Employee not found"

            all_rows = database_cursor.fetchall()

            column_names = []
            for column_info in database_cursor.description:
                column_names.append(column_info[0])

            connection.close()

            if not all_rows:
                return "Employee not found"

            results = []
            for single_row in all_rows:
                row_as_dict = {}
                for index in range(len(column_names)):
                    row_as_dict[column_names[index]] = single_row[index]
                results.append(row_as_dict)

            return json.dumps(results, indent=2)

        except Exception as e:
            logger.error(f"Employee lookup error: {e}")
            return f"Error: {str(e)}"


# TASK 3: Implement PolicySearchTool


class PolicySearchTool(Tool):
    """Search policy documents by keyword."""

    def __init__(self):
        super().__init__("policy_search", "Search policy documents by keyword or topic")
        self.documents = []
        with open("data/documents.json") as documents_file:
            self.documents = json.load(documents_file)

    def execute(self, query: str, limit: int = 5) -> str:
        """Search policies by keyword.

        TODO: Implement policy search:
        1. Load documents (from JSON file in data/ folder)
        2. Search documents by keyword match
        3. Return top-N matching documents
        4. Include title and snippet (first 500 chars) for each

        Args:
            query: Search term
            limit: Max results to return

        Returns:
            Formatted string with matching documents
        """
        try:
            matching_documents = []
            for document in self.documents:
                if query.lower() in document["content"].lower():
                    matching_documents.append(document)

            top_documents = matching_documents[:limit]

            if not top_documents:
                return f"No documents found matching: {query}"

            result_text = ""
            for document in top_documents:
                document_title = document["title"]
                document_snippet = document["content"][:500]
                result_text += f"Title: {document_title}\nSnippet: {document_snippet}"

            return result_text.strip()

        except Exception as e:
            logger.error(f"Policy search error: {e}")
            return f"Error: {str(e)}"


# TASK 4: Implement ExpenseQueryTool


class ExpenseQueryTool(Tool):
    """Query expense policies and approval limits."""

    def __init__(self):
        super().__init__("expense_query", "Query expense approval limits by role")
        self.policies = {}
        with open("data/policies.json") as policies_file:
            self.policies = json.load(policies_file)

    def execute(self, role: str) -> str:
        """Query expense approval limit for a given role.

        TODO: Implement expense lookup:
        1. Look up role in self.policies["expense"]["approval_limits"]
        2. Return: "Approval limit for {role}: ${amount}"
        3. If role not found, return "Role not found: {role}"

        Args:
            role: Employee role (ic1_ic2, ic3, manager, director, vp)

        Returns:
            String with approval limit for the given role
        """
        try:
            approval_limits = self.policies["expense"]["approval_limits"]

            if role not in approval_limits:
                return f"Role not found: {role}"

            approval_amount = approval_limits[role]
            return f"Approval limit for {role}: ${approval_amount}"

        except Exception as e:
            logger.error(f"Expense query error: {e}")
            return f"Error: {str(e)}"


# TASK 5: Implement the Agent class


class Agent:
    """AI agent that answers questions using Gemini LLM + tools."""

    def __init__(self, db_path: str, api_key: str = None):
        """Initialize the agent.

        TODO:
        1. Get API key from parameter or GOOGLE_API_KEY environment variable
        2. Raise ValueError if no API key provided
        3. Initialize Google GenAI client with api_key
        4. Initialize all tools (EmployeeLookup, PolicySearch, ExpenseQuery)
        5. Initialize token and cost tracking variables

        Args:
            db_path: Path to SQLite database
            api_key: Google AI API key (or use GOOGLE_API_KEY env var)
        """
        self.db_path = db_path
        self.api_key = GOOGLE_API_KEY

        self.client = genai.Client(api_key=self.api_key)

        self.tools = {
            "employee_lookup": EmployeeLookupTool(db_path),
            "policy_search": PolicySearchTool(),
            "expense_query": ExpenseQueryTool(),
        }

        self.token_count = 0
        self.total_cost = 0.0
        self.queries_run = 0

    def _build_system_prompt(self, user_role: str) -> str:
        """Build system prompt describing available tools.

        TODO: Create a prompt that:
        1. Describes the agent's purpose
        2. Lists all available tools with descriptions
        3. Explains how to use them
        4. Sets the user's role context

        Returns:
            System prompt string
        """
        system_prompt = f"""You help TechCorp employees get answers about company policies and staff.
        The user's role is: {user_role}

        Tools you can use:
        - employee_lookup: Find employee information. Args: employee_name=<name> OR employee_id=<id>
        - policy_search: Search policy documents by keyword. Args: query=<search term>
        - expense_query: Get expense approval limit for a role. Args: role=<ic1_ic2|ic3|manager|director|vp>

        When a tool is needed, reply in this exact format:
        TOOL: <tool_name>
        ARGS: <argument_name>=<value>

        If no tool is needed, answer directly and concisely."""

        return system_prompt

    def query(self, user_query: str, user_role: str = "engineer") -> Dict[str, Any]:
        """Answer a question using LLM + tools.

        TODO: Implement the reasoning loop:

        1. Call _build_system_prompt(user_role) to build the system prompt

        2. Call Gemini LLM with system prompt + user question
           - self.client.models.generate_content(model="gemini-2.5-pro", ...)

        3. Parse LLM response to identify tool calls
           - Check if response mentions any tool names
           - Extract parameters from response

        4. Execute tools with extracted parameters
           - tool.execute() with parameters
           - Collect results

        5. Synthesize final answer
           - Pass tool results back to LLM
           - Get final answer

        6. Track tokens and cost
           - Count tokens in request/response
           - Calculate cost: (tokens / 1_000_000) * rate
           - Update totals

        Args:
            user_query: The question to answer
            user_role: User's role (for access control in future weeks)

        Returns:
            Dict with keys:
            - "answer": str - the response
            - "tokens_used": int - total tokens
            - "cost": float - cost in dollars
            - "role": str - user role
        """
        logger.info(f"Processing query: {user_query}")

        system_prompt = self._build_system_prompt(user_role)

        first_response = self.client.models.generate_content( # Get initial response from Gemini
            model="gemini-2.5-flash",
            contents=user_query,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt
            )
        )

        first_response_text = first_response.text
        input_tokens = first_response.usage_metadata.prompt_token_count
        output_tokens = first_response.usage_metadata.candidates_token_count

        tool_name = None
        tool_args = {}

        for line in first_response_text.split("\n"):
            cleaned_line = line.strip()

            if cleaned_line.startswith("TOOL:"): # Get tool name
                tool_name = cleaned_line.replace("TOOL:", "").strip()

            elif cleaned_line.startswith("ARGS:"): # Get arguments for the tool
                args_string = cleaned_line.replace("ARGS:", "").strip()
                for arg_pair in args_string.split(","):
                    if "=" in arg_pair:
                        arg_name = arg_pair.split("=")[0].strip()
                        arg_value = arg_pair.split("=")[1].strip()
                        tool_args[arg_name] = arg_value

        if tool_name and tool_name in self.tools: # Execute the tool
            tool_result = self.tools[tool_name].execute(**tool_args)

            # Use tool result to get final answer from Gemini
            follow_up_message = (
                f"Tool result:\n{tool_result} "
                f"Answer the user's question using this information: {user_query}"
            )

            second_response = self.client.models.generate_content(
                model="gemini-2.5-flash", # using flash instead of pro for cost
                contents=follow_up_message,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt
                )
            )

            final_answer = second_response.text
            input_tokens += second_response.usage_metadata.prompt_token_count
            output_tokens += second_response.usage_metadata.candidates_token_count

        else:
            final_answer = first_response_text

        total_tokens = input_tokens + output_tokens # Calculate total tokens used
        query_cost = self._estimate_query_cost(input_tokens, output_tokens) # Calculate cost

        self.token_count += total_tokens
        self.total_cost += query_cost
        self.queries_run += 1

        return {
            "answer": final_answer,
            "tokens_used": total_tokens,
            "cost": query_cost,
            "role": user_role,
        }

    def _estimate_query_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on tokens.

        Gemini 2.5 Pro pricing:
        - Input: $0.075 per 1M tokens
        - Output: $0.3 per 1M tokens
        """
        input_cost = (input_tokens / 1_000_000) * 0.075
        output_cost = (output_tokens / 1_000_000) * 0.3
        return input_cost + output_cost

    def get_metrics(self) -> Dict[str, Any]:
        """Return performance metrics.

        TODO: Return dict with:
        - total_queries: number of queries processed
        - total_tokens: cumulative tokens used
        - total_cost: cumulative cost in dollars
        - avg_cost_per_query: average cost per query
        """
        if self.queries_run == 0:
            average_cost = 0.0
        else:
            average_cost = self.total_cost / self.queries_run

        return {
            "total_queries": self.queries_run,
            "total_tokens": self.token_count,
            "total_cost": self.total_cost,
            "avg_cost_per_query": average_cost,
        }


# TASK 6: Test your implementation

if __name__ == "__main__":
    """Quick test of agent functionality."""
    import sys
    import time

    test_queries = [
        "Find employee Sarah Villegas",
        "Look up the employee with ID 3",
        "Find employee Austin Gentry",
        "What is the remote work policy?",
        "What are the hotel rate limits for travel?",
        "How many PTO days do managers get?",
        "What is the expense limit for ic3?",
        "What can a vp approve for expenses?",
        "What does IC stand for in job levels?",
        "What is TechCorp's core mission?",
    ]

    try:
        agent = Agent("data/techcorp.db")

        for test_query in test_queries:
            print(f"Query: {test_query}")
            result = agent.query(test_query)
            print(f"Answer: {result['answer']}")
            print(f"Tokens: {result['tokens_used']}")
            print(f"Cost: ${result['cost']:.6f}")
            time.sleep(60)

        metrics = agent.get_metrics()
        print(f"Total queries: {metrics['total_queries']}")
        print(f"Total tokens: {metrics['total_tokens']}")
        print(f"Total cost: ${metrics['total_cost']:.6f}")
        print(f"Avg cost per query: ${metrics['avg_cost_per_query']:.6f}")

    except Exception as e:
        print(f"Error: {e}")
        logger.exception("Error during test")
        sys.exit(1)
