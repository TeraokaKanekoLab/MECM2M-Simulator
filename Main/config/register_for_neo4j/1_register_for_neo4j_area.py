import json
from py2neo import Graph, Node, Relationship
import sys
from dotenv import load_dotenv
import os

load_dotenv()
global_url = "bolt://localhost:" + os.getenv("NEO4J_GLOBAL_PORT_PYTHON")
global_graph = Graph(global_url, auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_GLOBAL_PASSWORD")))
global_tx = global_graph.begin()

local_url = "bolt://localhost:" + os.getenv("NEO4J_LOCAL_PORT_PYTHON")
local_graph = Graph(local_url, auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_LOCAL_PASSWORD")))
local_tx = local_graph.begin()

args = sys.argv
json_file = os.getenv("HOME") + os.getenv("PROJECT_NAME") + "/Main/config/json_files/config_main_area.json"
with open(json_file) as f:
    data = json.load(f)

areas = data["areas"]
for property in areas["area"]:
    label = property["property-label"]
    data_property = property["data-property"]
    node = Node(label, **data_property)
    global_graph.create(node)

    belonging_server_label = property["relation-label"]["Server"]
    if belonging_server_label == "S1":
        # Local GraphDB への登録
        dup_node = Node(label, **data_property)
        local_graph.create(dup_node)
    object_properties = property["object-property"]
    for object_property in object_properties:
        from_node_label = object_property["from"]["property-label"]
        from_node_property = object_property["from"]["data-property"]
        from_node_value = object_property["from"]["value"]
        to_node_label = object_property["to"]["property-label"]
        to_node_property = object_property["to"]["data-property"]
        to_node_value = object_property["to"]["value"]
        rel_type = object_property["type"]
        from_node = global_graph.nodes.match(from_node_label, **{from_node_property: from_node_value}).first()
        to_node = global_graph.nodes.match(to_node_label, **{to_node_property: to_node_value}).first()
        rel = Relationship(from_node, rel_type, to_node)
        global_graph.create(rel)
        if belonging_server_label == "S1":
            # Local GraphDB への登録
            dup_from_node = local_graph.nodes.match(from_node_label, **{from_node_property: from_node_value}).first()
            dup_to_node = local_graph.nodes.match(to_node_label, **{to_node_property: to_node_value}).first()
            dup_rel = Relationship(dup_from_node, rel_type, dup_to_node)
            local_graph.create(dup_rel)

try:
    global_graph.commit(global_tx)
except:
    print("Cannot Register Data to Global GraphDB")
else:
    print("Success: Area Instance in Global GraphDB")

# indexの付与
def create_index(graph, object, property):
    query = f"CREATE INDEX index_{object}_{property} IF NOT EXISTS FOR (n:{object}) ON (n.{property});"
    graph.run(query)

create_index(global_graph, "Area", "Label")


try:
    local_graph.commit(local_tx)
except:
    print("Cannot Register Data to Local GraphDB")
else:
    print("Success: Area Instance in Local GraphDB")

# indexの付与
def create_index(graph, object, property):
    query = f"CREATE INDEX index_{object}_{property} IF NOT EXISTS FOR (n:{object}) ON (n.{property});"
    graph.run(query)

create_index(local_graph, "Area", "Label")
