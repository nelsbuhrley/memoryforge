"""All prompt templates for Claude interactions.

Central location for every prompt MemoryForge sends to Claude.
Keeps prompt engineering separate from business logic.
"""


def build_ku_extraction_prompt(
    text_chunk: str,
    subject_name: str,
    section_heading: str | None = None,
    max_kus: int = 4,
) -> str:
    heading_ctx = f"\nSection: {section_heading}" if section_heading else ""
    return f"""You are an expert educator analyzing study material for the subject "{subject_name}".{heading_ctx}

Extract the {max_kus} MOST IMPORTANT and distinct knowledge units from this text. Be selective — only extract concepts that are:
- Core ideas a student must genuinely understand (not peripheral details or examples)
- Testable through reasoning, not just vocabulary recall
- Meaningful on their own without excessive context

For each knowledge unit, provide:
- concept: A clear, complete statement of the concept (1-3 sentences)
- concept_summary: A brief label (under 10 words) for quick reference
- difficulty: 1-5 rating (1=basic definition, 5=complex synthesis)
- tags: Relevant topic tags as a list
- prerequisites: List of concept_summaries this depends on (from this batch or general knowledge)

Return valid JSON array of EXACTLY {max_kus} or fewer items. Example format:
[
  {{
    "concept": "Mitochondria produce ATP through oxidative phosphorylation...",
    "concept_summary": "Mitochondria: ATP production",
    "difficulty": 3,
    "tags": ["cell-biology", "organelles", "energy"],
    "prerequisites": ["Cell structure basics"]
  }}
]

Text to analyze:
{text_chunk}"""


def build_quiz_prompt(
    concept: str,
    concept_summary: str,
    question_format: str,
    difficulty: int,
    previous_questions: list[str] | None = None,
) -> str:
    prev_ctx = ""
    if previous_questions:
        prev_list = "\n".join(f"- {q}" for q in previous_questions[-3:])
        prev_ctx = f"\n\nPrevious questions asked about this concept (DO NOT repeat these):\n{prev_list}"

    format_instructions = {
        "free_response": "Ask an open-ended question requiring a written explanation. The student should demonstrate understanding, not just recall a definition.",
        "multiple_choice": "Create a multiple-choice question with 4 options (A-D). Include one correct answer and three plausible distractors. Indicate the correct answer.",
        "fill_in_blank": "Create a sentence with a key term or phrase blanked out. The blank should test understanding of the core concept.",
        "apply_the_concept": "Present a novel scenario or problem that requires applying this concept. The student must use the concept to analyze or solve something new.",
    }

    return f"""Generate a {question_format} question about the following concept.

Concept: {concept}
Difficulty level: {difficulty}/5
Format: {format_instructions.get(question_format, format_instructions["free_response"])}
{prev_ctx}

Generate a fresh, unique question. Vary your angle — test different aspects of understanding each time.

Return JSON:
{{
  "question": "...",
  "expected_answer": "...",
  "format": "{question_format}"
}}"""


def build_grading_prompt(
    question: str,
    student_answer: str,
    concept: str,
    strictness: int,
) -> str:
    strictness_desc = {
        1: "Lenient — accept answers that show general understanding even if imprecise or missing details",
        2: "Moderate — the answer should be substantially correct with key details present",
        3: "Strict — the answer must be precise and complete, covering all essential aspects",
    }
    return f"""Grade this student's answer.

Question: {question}
Student's answer: {student_answer}
Correct concept: {concept}
Grading strictness: {strictness_desc.get(strictness, strictness_desc[2])}

Evaluate whether the student demonstrates understanding of the concept.

Return JSON:
{{
  "quality": <0-5 integer, where 5=perfect, 4=correct with hesitation, 3=correct but difficult, 2=incorrect but close, 1=incorrect, 0=no understanding>,
  "feedback": "<brief, encouraging feedback explaining what was right/wrong>",
  "correct": <true/false>
}}"""


def build_lesson_prompt(
    concept: str,
    concept_summary: str,
    student_context: str | None = None,
) -> str:
    ctx = ""
    if student_context:
        ctx = f"\n\nStudent context (what they already know): {student_context}"
    return f"""You are a patient, encouraging tutor. Teach the following concept clearly and concisely.{ctx}

Concept to teach: {concept}
Topic: {concept_summary}

Instructions:
- Explain the concept in clear, accessible language
- Use an analogy or real-world example if helpful
- Connect to concepts the student already knows (if context provided)
- End with an elaboration prompt — ask the student how this connects to something they've previously learned
- Keep it under 200 words"""


def build_reteach_prompt(
    concept: str,
    student_answer: str,
    question: str,
    attempt_number: int,
) -> str:
    if attempt_number <= 2:
        approach = """Use the Socratic method:
- Ask a guiding question that leads the student toward the answer
- Don't give the answer directly
- Build on what the student DID know (if anything)
- Keep it to one question"""
    else:
        approach = """The student has struggled through multiple attempts. Now explain directly:
- Give a clear, direct explanation of the concept
- Use a different analogy or framing than before
- Break it into smaller pieces
- End with an elaboration prompt to check understanding"""

    return f"""A student is struggling with this concept. Help them learn it.

Question that was asked: {question}
Student's answer: {student_answer}
Correct concept: {concept}
Attempt number: {attempt_number}

{approach}"""


def build_generative_probe_prompt(
    topic: str,
    subject_name: str,
    student_knowledge_summary: str | None = None,
) -> str:
    ctx = ""
    if student_knowledge_summary:
        ctx = f"\n\nWhat the student already knows: {student_knowledge_summary}"
    return f"""You are a tutor about to introduce a new topic in {subject_name}.

Before teaching, you want to activate the student's prior knowledge and create cognitive hooks (generation effect).

New topic to introduce: {topic}
{ctx}

Ask ONE thought-provoking question that:
- Makes the student think about and predict something related to this topic
- Can be answered with reasoning even without formal knowledge
- Creates curiosity about the upcoming concept
- Is open-ended (no single correct answer)

Don't tell the student they're about to learn this topic. Just ask the question naturally.

Return JSON:
{{
  "probe_question": "...",
  "topic_connection": "brief note on how this connects to what you'll teach"
}}"""


def build_learning_plan_prompt(
    subject_name: str,
    material_outline: str,
    current_progress: str,
    deadlines: str,
) -> str:
    return f"""Create a learning plan for the subject "{subject_name}".

Available material topics: {material_outline}
Current progress (topic: mastery 0.0-1.0): {current_progress}
Deadlines: {deadlines}

Create an ordered study plan that:
- Prioritizes topics with upcoming deadlines
- Respects prerequisite dependencies
- Focuses on weak areas (low mastery)
- Introduces new topics at a sustainable pace
- Spaces review of mastered topics appropriately

Return JSON:
{{
  "ordered_topics": ["topic1", "topic2", ...],
  "milestones": [{{"topic": "...", "target_date": "YYYY-MM-DD", "reason": "..."}}],
  "focus_areas": ["topic with low mastery", ...],
  "daily_new_concepts": <recommended number of new concepts per day>
}}"""
