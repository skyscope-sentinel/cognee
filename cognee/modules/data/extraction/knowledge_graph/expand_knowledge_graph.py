import asyncio
from datetime import datetime
from typing import Type
from pydantic import BaseModel
from cognee.infrastructure.databases.graph import get_graph_engine
from ...processing.chunk_types.DocumentChunk import DocumentChunk
from .extract_knowledge_graph import extract_content_graph

async def expand_knowledge_graph(data_chunks: list[DocumentChunk], graph_model: Type[BaseModel]):
    chunk_graphs = await asyncio.gather(
        *[extract_content_graph(chunk.text, graph_model) for chunk in data_chunks]
    )

    graph_engine = await get_graph_engine()

    type_ids = [generate_node_id(node.type) for chunk_graph in chunk_graphs for node in chunk_graph.nodes]
    graph_type_node_ids = list(set(type_ids))
    graph_type_nodes = await graph_engine.extract_nodes(graph_type_node_ids)
    existing_type_nodes_map = {node["id"]: node for node in graph_type_nodes}

    graph_nodes = []
    graph_edges = []

    for (chunk_index, chunk) in enumerate(data_chunks):
        graph = chunk_graphs[chunk_index]
        if graph is None:
            continue

        for node in graph.nodes:
            node_id = generate_node_id(node.id)

            graph_nodes.append((
                node_id,
                dict(
                    id = node_id,
                    chunk_id = str(chunk.chunk_id),
                    document_id = str(chunk.document_id),
                    name = node.name,
                    type = node.type.lower().capitalize(),
                    description = node.description,
                    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                )
            ))

            graph_edges.append((
                str(chunk.chunk_id),
                node_id,
                "contains",
                dict(
                    relationship_name = "contains",
                    source_node_id = str(chunk.chunk_id),
                    target_node_id = node_id,
                ),
            ))

            type_node_id = generate_node_id(node.type)

            if type_node_id not in existing_type_nodes_map:
                node_name = node.type.lower().capitalize()

                type_node = dict(
                    id = type_node_id,
                    name = node_name,
                    type = node_name,
                    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                )

                graph_nodes.append((type_node_id, type_node))
                existing_type_nodes_map[type_node_id] = type_node

            graph_edges.append((
                str(chunk.chunk_id),
                type_node_id,
                "contains_entity_type",
                dict(
                    relationship_name = "contains_entity_type",
                    source_node_id = str(chunk.chunk_id),
                    target_node_id = type_node_id,
                ),
            ))

            # Add relationship between entity type and entity itself: "Jake is Person"
            graph_edges.append((
                type_node_id,
                node_id,
                "is_entity_type",
                dict(
                    relationship_name = "is_entity_type",
                    source_node_id = type_node_id,
                    target_node_id = node_id,
                ),
            ))

            # Add relationship that came from graphs.
            for edge in graph.edges:
                graph_edges.append((
                    generate_node_id(edge.source_node_id),
                    generate_node_id(edge.target_node_id),
                    edge.relationship_name,
                    dict(
                        relationship_name = edge.relationship_name,
                        source_node_id = generate_node_id(edge.source_node_id),
                        target_node_id = generate_node_id(edge.target_node_id),
                    ),
                ))

    await graph_engine.add_nodes(graph_nodes)

    await graph_engine.add_edges(graph_edges)

    return data_chunks


def generate_node_id(node_id: str) -> str:
    return node_id.upper().replace(" ", "_").replace("'", "")
