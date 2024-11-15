from openai import OpenAI
apiKey = "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"

client = OpenAI(api_key=apiKey)
 
assistant = client.beta.assistants.create(
  name="Software developer expert",
  instructions="You are expert in develop tecnology.",
  model="gpt-4o-mini",
  tools=[{"type": "file_search"}],
)



vector_store = client.beta.vector_stores.create(name="FFF")

file_paths = ["../Uploads/20241113200628_Post instagram, Kit básico senderismo.pdf"]
file_streams = [open(path, "rb") for path in file_paths]




file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
  vector_store_id=vector_store.id, files=file_streams
)

print(file_batch.status)
print(file_batch.file_counts)


assistant = client.beta.assistants.update(
  assistant_id=assistant.id,
  tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
)

print(assistant)