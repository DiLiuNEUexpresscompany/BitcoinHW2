#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Initialize the OpenAI client with the API key from environment variables
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def text_to_sql(schema: str, question: str) -> str:
    """
    Generate an SQL query based on the provided SQL schema and natural language question.
    """
    # Construct the prompt containing the SQL schema and question
    prompt = f"""
    Given the following SQL schema:
    {schema}

    Convert the following natural language question into an SQL query:
    {question}
    """

    # Call the ChatCompletion API, using a system message to specify the model's role and task description
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant that can convert natural language questions into SQL queries. "
                    "Given an SQL schema and a question, please return only the SQL query that answers the question."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,  # Use deterministic output for reproducible results
    )

    # Extract the generated SQL query from the API response
    sql_query = response.choices[0].message.content
    return sql_query.strip()

def main():
    # Example SQL schema
    schema = """
    CREATE TABLE employees (
        id INTEGER PRIMARY KEY,
        name TEXT,
        department TEXT,
        salary INTEGER
    );
    """

    # Example natural language question
    question = "Find the names of all employees in the 'Sales' department with a salary greater than 50000."

    # Generate SQL query
    sql_query = text_to_sql(schema, question)
    print("Generated SQL query:")
    print(sql_query)

if __name__ == "__main__":
    main()