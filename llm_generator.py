from groq import Groq
import os

def generate_content(paper_text: str) -> str:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    prompt = f"""
    I have a scientific paper, and I want to turn it into a series of engaging, easy-to-understand text chunks for a layman audience on social media.
    Each chunk should be brief and suitable for being read on a card that people can swipe through, like on TikTok.
    Here's how I want you to break down the content:
    - Hook: Identify the most interesting finding or surprising fact from the paper and summarize it in a catchy, attention-grabbing way to draw people in.
    - Research Problem or Question: Summarize the main problem or research question the paper addresses. Keep it simple and relatable.
    - Researcher and Institution: Provide a short introduction to the scientist(s) who conducted the research, or mention the institution they are affiliated with.
    - Research Method: Briefly explain what the researchers did to conduct the study. Keep it straightforward and avoid technical jargon.
    - Findings: Summarize the key findings of the research in a way that highlights their significance.
    - Implications: Explain why these findings matter. What impact could they have on people's lives, society, or future research?
    - Engagement Bait: End with a question or a call to action to encourage audience engagement, such as commenting their thoughts, sharing the content, or asking questions.
    Make sure each chunk is concise and suitable for a non-scientific audience. Use simple language and keep each chunk to no more than two sentences.
    Don't give intro in your answer. Just the output.
    Here is the text of the scientific paper: {paper_text}
    """

    completion = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=1,
        max_tokens=8000,
        top_p=1,
        stream=False,
        stop=None,
    )

    return completion.choices[0].message.content