from app.core.llm import call_llm

def generate_docs(structure):
    prompt = f"""
    Generate clean technical documentation in Markdown
    from the following Python code structure.

    Rules:
    - Do not assume missing behavior
    - Explain public classes and functions only

    Structure:
    {structure}
    """
    return call_llm(prompt)
