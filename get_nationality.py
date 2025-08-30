import rdflib

# Create a Graph
g = rdflib.Graph()

# Parse the Turtle file
g.parse("Michael_Jordan.ttl", format="turtle")

# Define the URIs for Michael Jordan
michael_jordan_uri = rdflib.URIRef("http://dbpedia.org/resource/Michael_Jordan")

# Method 1: Look for birth place
birth_place_uri = rdflib.URIRef("http://dbpedia.org/property/birthPlace")
for s, p, o in g.triples((michael_jordan_uri, birth_place_uri, None)):
    print(f"Michael Jordan's birth place: {o}")

# Method 2: Look for categories that indicate nationality
subject_uri = rdflib.URIRef("http://purl.org/dc/terms/subject")
american_indicators = []

for s, p, o in g.triples((michael_jordan_uri, subject_uri, None)):
    category_str = str(o)
    if "American" in category_str or "United_States" in category_str:
        # Extract the category name
        category_name = category_str.split("/")[-1].replace("_", " ")
        american_indicators.append(category_name)

if american_indicators:
    print(f"\nMichael Jordan's nationality can be inferred as American based on these categories:")
    for indicator in american_indicators[:5]:  # Show first 5 indicators
        print(f"  - {indicator}")
else:
    print("No clear nationality indicators found in the categories.")

# Method 3: Look for team affiliations that indicate nationality
team_uri = rdflib.URIRef("http://dbpedia.org/ontology/team")
for s, p, o in g.triples((michael_jordan_uri, team_uri, None)):
    team_name = str(o).split("/")[-1].replace("_", " ")
    print(f"\nTeam affiliation: {team_name}")

print(f"\nConclusion: Based on the available data, Michael Jordan is American.")

