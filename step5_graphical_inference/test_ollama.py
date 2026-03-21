from langchain_ollama import OllamaLLM
import time

llm = OllamaLLM(model="test_mlx_import2:latest")
print("Invoking...")
start = time.time()
res = llm.invoke("Ciao, come stai?")
print(f"Res: {res}")
print(f"Time: {time.time() - start}")
