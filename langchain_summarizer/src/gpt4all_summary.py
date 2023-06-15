from langchain import PromptTemplate
from langchain.llms import GPT4All
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.text_splitter import CharacterTextSplitter

template = """Question: {question}
Answer:"""
prompt = PromptTemplate(template=template, input_variables=["question"])

callbacks = [StreamingStdOutCallbackHandler()]
llm = GPT4All(
    model="ggml-gpt4all-j-v1.3-groovy.bin",
    backend="gptj",
    # callbacks=callbacks,
    # verbose=True,
)

doc = (
    "The Allgäu is the south-eastern part of Bavarian Swabia at the northside of the Alps."
    "The biggest part of it is located in Bavaria, a smaller one in Baden-Württemberg,"
    "but also on the borderland of Austria with the Kleinwalsertal belongs to Allgäu."
    "There is a political division of the Allgäu into the German counties of Oberallgäu, Ostallgäu and Lindau."
    "It also contains parts of the Württembergian county of Ravensburg."
    "The county of Unterallgäu belongs about 2% to Allgäu."
    "The rest of the county is a part of the Middle-Swabian territory."
    "In geographic aspects the Alps form the demarcation of the southern part of Allgäu."
    "The river Lech is the south-eastern border."
    "The western frontier runs by Lindau and Wangen, generally Memmingen is seen as northernmost city of Allgäu."
)
chain = load_summarize_chain(llm, chain_type="map_reduce")
text_splitter = CharacterTextSplitter()
texts = text_splitter.split_text(doc)

docs = [Document(page_content=t) for t in texts]

chain = load_summarize_chain(llm, chain_type="map_reduce")
summary = chain.run(docs)
print(f"Summary is: {summary}")
