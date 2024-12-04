# Start up the local ollama server before using this
# ollama pull granite3-dense:8b
# ollama serve

import ollama
import timeit

start = timeit.default_timer()
response = ollama.chat(model='llama2', messages=[
  {
    'role': 'user',
    'content': 'Why is the sky blue?',
  },
])
print(response['message']['content'])
print("The inference execution time is: ", timeit.default_timer() - start)
