# -*- coding: utf-8 -*-
"""Assign nodes to architectural layers based on file paths."""
import json
import os

PROJECT_ROOT = os.path.abspath('.')
INTERMEDIATE = os.path.join(PROJECT_ROOT, '.understand-anything', 'intermediate')

with open(os.path.join(INTERMEDIATE, 'assembled-graph.json'), 'r', encoding='utf-8') as f:
    graph = json.load(f)

# Define layers based on project structure
LAYER_RULES = [
    {
        'id': 'layer:api',
        'name': 'API Layer',
        'description': 'FastAPI route handlers and API endpoints',
        'patterns': ['server/app/api/', 'server/app/main.py'],
    },
    {
        'id': 'layer:models',
        'name': 'Data Models',
        'description': 'SQLAlchemy ORM models and database schemas',
        'patterns': ['server/app/models/'],
    },
    {
        'id': 'layer:services',
        'name': 'Business Services',
        'description': 'Business logic and fortune engine',
        'patterns': ['server/app/services/', 'server/fortune_engine/'],
    },
    {
        'id': 'layer:frontend',
        'name': 'Frontend',
        'description': 'React frontend components and pages',
        'patterns': ['client/src/'],
    },
    {
        'id': 'layer:config',
        'name': 'Configuration',
        'description': 'Project configuration files',
        'patterns': ['.github/', 'server/alembic', 'client/vite.config', 'client/tsconfig', 'server/requirements', '.env', '.gitignore', 'deploy.sh', 'update.sh'],
    },
    {
        'id': 'layer:docs',
        'name': 'Documentation',
        'description': 'Project documentation and specs',
        'patterns': ['docs/', 'README', 'CLAUDE.md', 'STARTUP.md', '*.md'],
    },
    {
        'id': 'layer:infra',
        'name': 'Infrastructure',
        'description': 'CI/CD, deployment, and infrastructure config',
        'patterns': ['.github/workflows/'],
    },
]

# Assign nodes to layers
layer_assignments = {layer['id']: [] for layer in LAYER_RULES}
layer_assignments['layer:other'] = []

file_types = {'file', 'config', 'document', 'service', 'pipeline', 'table', 'schema', 'resource', 'endpoint'}
file_nodes = [n for n in graph['nodes'] if n.get('type') in file_types]

for node in file_nodes:
    path = node.get('filePath', '')
    assigned = False
    for layer in LAYER_RULES:
        for pattern in layer['patterns']:
            if pattern in path or path.startswith(pattern):
                layer_assignments[layer['id']].append(node['id'])
                assigned = True
                break
        if assigned:
            break
    if not assigned:
        layer_assignments['layer:other'].append(node['id'])

# Build layers array
layers = []
for layer in LAYER_RULES:
    node_ids = layer_assignments.get(layer['id'], [])
    if node_ids:
        layers.append({
            'id': layer['id'],
            'name': layer['name'],
            'description': layer['description'],
            'nodeIds': node_ids,
        })

# Add other layer if needed
other_ids = layer_assignments.get('layer:other', [])
if other_ids:
    layers.append({
        'id': 'layer:other',
        'name': 'Other',
        'description': 'Files that do not fit into a specific architectural layer',
        'nodeIds': other_ids,
    })

# Build a simple tour
tour = [
    {
        'order': 1,
        'title': 'Project Overview',
        'description': 'The fortune-telling system with a FastAPI backend and React frontend for Chinese metaphysics calculations.',
        'nodeIds': [n['id'] for n in graph['nodes'] if n.get('filePath') == 'CLAUDE.md'][:1],
    },
    {
        'order': 2,
        'title': 'Backend Entry Point',
        'description': 'The FastAPI application entry point that initializes routes, middleware, and database connections.',
        'nodeIds': [n['id'] for n in graph['nodes'] if n.get('filePath') == 'server/app/main.py'][:1],
    },
    {
        'order': 3,
        'title': 'API Routes',
        'description': 'RESTful API endpoints for fortune calculations, user management, and daily push notifications.',
        'nodeIds': [n['id'] for n in graph['nodes'] if 'server/app/api/' in n.get('filePath', '')][:5],
    },
    {
        'order': 4,
        'title': 'Fortune Engine',
        'description': 'Core calculation engine for Bazi, Liu Yao, Qi Men Dun Jia, and other Chinese metaphysics systems.',
        'nodeIds': [n['id'] for n in graph['nodes'] if 'server/fortune_engine/' in n.get('filePath', '')][:5],
    },
    {
        'order': 5,
        'title': 'Frontend Application',
        'description': 'React + TypeScript frontend with fortune calculation forms, user dashboard, and result visualization.',
        'nodeIds': [n['id'] for n in graph['nodes'] if 'client/src/' in n.get('filePath', '')][:5],
    },
]

# Filter tour steps with valid nodeIds
tour = [step for step in tour if step['nodeIds']]

# Update assembled graph with layers and tour
graph['layers'] = layers
graph['tour'] = tour

output_path = os.path.join(INTERMEDIATE, 'assembled-graph.json')
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(graph, f, indent=2, ensure_ascii=False)

print(f'Layers: {len(layers)}')
for layer in layers:
    print(f'  {layer["name"]}: {len(layer["nodeIds"])} nodes')
print(f'Tour steps: {len(tour)}')
