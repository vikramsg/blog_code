import os
from typing import Dict

import requests
from dotenv import load_dotenv
from langchain.docstore.document import Document
from langchain.text_splitter import CharacterTextSplitter
from text_generation import InferenceAPIClient

from src.model import WikiPageResponse

_WIKIVOYAGE_URL = "https://en.wikivoyage.org/w/api.php"


def _page_query_params(page_title: str) -> Dict:
    return {
        "action": "query",
        "format": "json",
        "titles": page_title,
        "prop": "extracts",
        "explaintext": True,
        "inprop": "url",
    }


def _get_wiki_page(city: str) -> str:
    content_response = requests.get(_WIKIVOYAGE_URL, params=_page_query_params(city))
    wiki_page = WikiPageResponse.parse_obj(content_response.json())
    return list(wiki_page.query.pages.values())[0].extract


def _get_client() -> InferenceAPIClient:
    load_dotenv()
    model = "OpenAssistant/oasst-sft-4-pythia-12b-epoch-3.5"
    return InferenceAPIClient(model, token=os.getenv("HF_TOKEN", None))


def predict(client: InferenceAPIClient, input: str) -> str:
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


def summary(client: InferenceAPIClient, city_text: str) -> str:
    # FIXME: How do I switch off logging for this?
    # It uses a logger which puts them as warning
    # So we could change logger level
    text_splitter = CharacterTextSplitter(chunk_size=512)

    texts = text_splitter.split_text(city_text)

    docs = [Document(page_content=t) for t in texts]
    text_summary = [
        predict(client, f"Summarize the following text.\n{doc.page_content}")
        for doc in docs
    ]

    total_summary = "".join(text_summary)

    summary_prompt = (
        "Look at the following text."
        "Describe how would I spend a day here as a tourist."
        "Don't write text that I would not expect on a travel information page."
        ""
    )
    return predict(client, f"{summary_prompt}\n{total_summary}")


if __name__ == "__main__":
    wiki_text = _get_wiki_page("Ratzeburg")

    client = _get_client()
    page_summary = summary(client, wiki_text)
    print(page_summary)
