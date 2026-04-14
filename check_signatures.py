import inspect

from langfuse import Langfuse

client = Langfuse(
    public_key="pk-123", secret_key="sk-123", host="https://cloud.langfuse.com"
)

print("--- Langfuse methods ---")
# print(dir(client))

# Check start_as_current_observation signature
print("\n--- start_as_current_observation signature ---")
print(inspect.signature(client.start_as_current_observation))

# Check create_score signature
print("\n--- create_score signature ---")
print(inspect.signature(client.create_score))

# Check flush signature
print("\n--- flush signature ---")
print(inspect.signature(client.flush))
