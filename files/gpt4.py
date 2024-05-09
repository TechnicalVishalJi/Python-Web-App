from g4f.client import Client
#from g4f.Provider import RetryProvider, Phind, FreeChatgpt, Liaobots

client = Client(
#provider=RetryProvider([Phind, FreeChatgpt, Liaobots, OpenAi], shuffle=False)
)

stream = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Write an article on ai"}],
    stream=True

)

print("\n\nAi Answer\n")
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content or "", end="")
