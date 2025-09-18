
import os,sys
import eumdac
import json


with open('inputs/id_EUMETSAT.json') as f:
    d = json.load(f)
    print(d)
consumer_key = d["consumer"]
consumer_secret = d["secret"]
token = eumdac.AccessToken((consumer_key, consumer_secret))


datastore = eumdac.DataStore(token)

# Exemple : MTG-FCI
collection = datastore.get_collection("EO:EUM:DAT:0677")

# Research on a recent period (last day)
results = collection.search(
    dtstart="2025-09-16T00:00:00Z",
    dtend="2025-09-17T00:00:00Z"
)
products = list(results)[-2:]   # Select 2 last products

for product in products:
    print("Produit :", product)

    target_dir = "./meteosat_data"
    os.makedirs(target_dir, exist_ok=True)


    # Ouverture du produit (renvoie un flux HTTP)
    with product.open() as response:
        outfile = os.path.join(target_dir, f"{product._id}.nc")
        with open(outfile, "wb") as f:
            f.write(response.read())
        print("Produit sauvegardé :", outfile)
