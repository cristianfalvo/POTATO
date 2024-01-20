from nordigen import NordigenClient
import os
from dotenv import load_dotenv

load_dotenv()

client = NordigenClient(
    secret_id=os.getenv("SECRET_ID"),
    secret_key=os.getenv("SECRET_KEY")
)

client.generate_token()

requisitions = client.requisition.get_requisitions()
for elem in requisitions["results"]:
    print(elem)
    if elem["status"] != "LN":
        client.requisition.delete_requisition(elem["id"])
