import os
from typing import Dict

from dotenv import load_dotenv
from langchain.docstore.document import Document
from langchain.text_splitter import CharacterTextSplitter
from text_generation import InferenceAPIClient


def get_client() -> InferenceAPIClient:
    load_dotenv()
    model = "OpenAssistant/oasst-sft-4-pythia-12b-epoch-3.5"
    return InferenceAPIClient(model, token=os.getenv("HF_TOKEN", None))


def _summary_of_summary(client: InferenceAPIClient, input: str, city: str) -> str:
    preprompt, user_name, assistant_name, sep = (
        "You are a helpful assistant.",
        "<|prompter|>",
        "<|assistant|>",
        "<|endoftext|>",
    )
    prompt = (
        f"{preprompt}\n"
        f"{sep}\n"
        f"{user_name}: I want to get a summary of {city} as a tourist destination."
        f"I have a text containing details about {city}."
        "Can you help me summarize it as a tourist destination.\n"
        f"{sep}\n"
        f"{assistant_name}\n"
        "Certainly. Give me the text.\n"
        f"{sep}\n"
        f"{user_name}\n"
        f"{input}"
        f"{sep}\n"
        f"{assistant_name}\nHere's how I would describe {city}, Germany.\n"
        f"There are many things to see and do in {city}."
        f"{city}, Germany is known for"
    )

    iterator = client.generate_stream(
        prompt,
        typical_p=0.2,
        truncate=1000,
        watermark=False,
        max_new_tokens=500,
    )

    partial_words = ""
    chat = []

    for i, response in enumerate(iterator):
        if response.token.special:
            continue

        partial_words = partial_words + response.token.text
        if partial_words.endswith(user_name.rstrip()):
            partial_words = partial_words.rstrip(user_name.rstrip())
        if partial_words.endswith(assistant_name.rstrip()):
            partial_words = partial_words.rstrip(assistant_name.rstrip())

        if i == 0:
            chat.append(" " + partial_words)
        elif response.token.text not in user_name:
            chat[-1] = partial_words

    joined_summary = "".join([text.strip() for text in chat])
    return f"{city}, Germany is known for {joined_summary}"


def _predict(client: InferenceAPIClient, input: str) -> str:
    preprompt, user_name, assistant_name, sep = (
        "",
        "<|prompter|>",
        "<|assistant|>",
        "<|endoftext|>",
    )

    total_inputs = preprompt + input + sep + assistant_name.rstrip()
    iterator = client.generate_stream(
        total_inputs,
        typical_p=0.2,
        truncate=1000,
        watermark=False,
        max_new_tokens=500,
    )

    partial_words = ""
    chat = []

    for i, response in enumerate(iterator):
        if response.token.special:
            continue

        partial_words = partial_words + response.token.text
        if partial_words.endswith(user_name.rstrip()):
            partial_words = partial_words.rstrip(user_name.rstrip())
        if partial_words.endswith(assistant_name.rstrip()):
            partial_words = partial_words.rstrip(assistant_name.rstrip())

        if i == 0:
            chat.append(" " + partial_words)
        elif response.token.text not in user_name:
            chat[-1] = partial_words

    return "".join([text.strip() for text in chat])


def summary(client: InferenceAPIClient, city_text: str, city: str) -> str:
    # FIXME: How do I switch off logging for this?
    # It uses a logger which puts them as warning
    # So we could change logger level
    text_splitter = CharacterTextSplitter(chunk_size=512)

    texts = text_splitter.split_text(city_text)

    docs = [Document(page_content=t) for t in texts]
    text_summary = [
        _predict(
            client,
            f"Summarize the following text. Ignore all text after '== Go next =='.\n{doc.page_content}",
        )
        for doc in docs
    ]

    total_summary = "".join(text_summary)

    # FIXME: Replace with gpt
    # Avoid overloading Huggingface by sleeping after every request
    return _summary_of_summary(client, total_summary, city)
