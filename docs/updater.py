def update_section(old_doc, impact, code_snippet):
    prompt = f"""
You are updating existing technical documentation.

Rules:
- Update ONLY impacted parts
- Keep tone and formatting unchanged
- Do NOT rewrite entire document

Impact:
{impact}

Relevant Code:
{code_snippet}

Existing Documentation:
{old_doc}
"""
    return call_llm(prompt)
