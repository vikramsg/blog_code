from typing import Dict
from langchain import PromptTemplate
from langchain.llms import GPT4All
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.text_splitter import CharacterTextSplitter
from model import WikiPageResponse
import requests

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


def gpt4all_summary(city_text: str, city: str) -> str:
    llm = GPT4All(
        model="ggml-gpt4all-j-v1.3-groovy.bin",
        backend="gptj",
    )

    city_string = f"Combine all the summaries on {city} provided within backticks "
    combine_prompt = PromptTemplate(
        template=(
            city_string
            + """```{text}```.
            Can you summarize it as a tourist destination in 8-10 sentences.\n"
            """
        ),
        input_variables=["text"],
    )

    chain = load_summarize_chain(
        llm, chain_type="map_reduce", combine_prompt=combine_prompt
    )
    text_splitter = CharacterTextSplitter()
    texts = text_splitter.split_text(city_text)

    docs = [Document(page_content=t) for t in texts]

    chain = load_summarize_chain(llm, chain_type="map_reduce")
    return chain.run(docs)


if __name__ == "__main__":
    city = "Allgäu"
    wiki_text = _get_wiki_page(city)

    page_summary = gpt4all_summary(wiki_text, city)
    print(page_summary)
