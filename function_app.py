import logging
import json
import os
import azure.functions as func
from azure.cosmos import CosmosClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
connection_string = os.getenv("CONNECTION_STRING")
client = CosmosClient.from_connection_string(connection_string)


@app.function_name(name="uniqueCount")
@app.route(route="uniqueCount")
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    # Initialize Cosmos Client
    # create env vars by using export varname=whatever
    # i also created app settings for these

    # Select database
    visitorDetail = req.headers.get("X-Real-IP")
    hashedVersion = hash(visitorDetail)

    database_name = "my-database"

    database = client.get_database_client(database_name)

    # Select Container
    container_name1 = "Unique visitors"
    container1 = database.get_container_client(container_name1)

    container_name2 = "CRC-visitor count"
    container2 = database.get_container_client(container_name2)

    # Check DB to see if hashedVersion is in DB

    results = container2.query_items(
        query=f"SELECT VALUE COUNT(1) FROM c WHERE c.hashedIP = '{hashedVersion}'",
        enable_cross_partition_query=True,
    )

    item_response2 = container2.read_item(item="test2", partition_key="unique")

    result_list = list(results)
    count = result_list[0] if result_list else 0

    if count == 0:
        item_response2["count"] += 1
        container2.upsert_item(item_response2)
        container1.upsert_item(
            {"id": f"{item_response2['count']}", "hashedIP": hashedVersion}
        )
        item_response2 = container2.read_item(item="test2", partition_key="unique")

    return func.HttpResponse(json.dumps({"count": item_response2["count"]}))
