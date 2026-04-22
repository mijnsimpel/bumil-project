from google import genai

client = genai.Client(api_key="AIzaSyAJ7MavsUPfOuq8O0NCfYrujfwA6dm_PWg")

print("--- Mengecek Model dengan Library Baru ---")
try:
    for model in client.models.list():
        print(f"Nama Model: {model.name}")
except Exception as e:
    print(f"Gagal: {e}")
