# -*- coding: utf-8 -*-
"""Convert extract-structure batch results into knowledge graph format."""
import json
import os
import glob

PROJECT_ROOT = os.path.abspath('.')
INTERMEDIATE = os.path.join(PROJECT_ROOT, '.understand-anything', 'intermediate')

# Node type mapping from fileCategory
CATEGORY_TO_TYPE = {
    'code': 'file',
    'config': 'config',
    'docs': 'document',
    'infra': 'service',
    'data': 'resource',
    'script': 'file',
    'markup': 'document',
}

def make_node_id(file_path, file_category):
    prefix = CATEGORY_TO_TYPE.get(file_category, 'file')
    return f"{prefix}:{file_path}"

def build_summary(result):
    """Build a summary from extract-structure results."""
    path = result['path']
    lang = result.get('language', 'unknown')
    metrics = result.get('metrics', {})
    sections = result.get('sections', [])

    parts = []
    parts.append(f"{lang} file")

    func_count = metrics.get('functionCount', 0)
    class_count = metrics.get('classCount', 0)
    if func_count > 0:
        parts.append(f"{func_count} functions")
    if class_count > 0:
        parts.append(f"{class_count} classes")
    if sections:
        section_names = [s['heading'] for s in sections[:3]]
        parts.append(f"sections: {', '.join(section_names)}")

    return f"{os.path.basename(path)}: {', '.join(parts)}"

def build_tags(result):
    tags = []
    lang = result.get('language', 'unknown')
    cat = result.get('fileCategory', 'code')
    tags.append(lang)
    tags.append(cat)
    metrics = result.get('metrics', {})
    if metrics.get('functionCount', 0) > 0:
        tags.append('has-functions')
    if metrics.get('classCount', 0) > 0:
        tags.append('has-classes')
    return tags

# Load batches.json for import data
batches_path = os.path.join(INTERMEDIATE, 'batches.json')
with open(batches_path, 'r', encoding='utf-8') as f:
    batches_data = json.load(f)

# Load scan-result.json for file metadata
scan_path = os.path.join(INTERMEDIATE, 'scan-result.json')
with open(scan_path, 'r', encoding='utf-8') as f:
    scan_data = json.load(f)

# Build file metadata lookup
file_meta = {}
for f_info in scan_data.get('files', []):
    file_meta[f_info['path']] = f_info

# Process all batch results
nodes = []
edges = []
node_ids = set()

batch_files = sorted(glob.glob(os.path.join(INTERMEDIATE, 'batch-*.json')))
for bf in batch_files:
    if 'part' in bf:
        continue  # Skip multi-part for now
    with open(bf, 'r', encoding='utf-8') as f:
        batch_result = json.load(f)

    for result in batch_result.get('results', []):
        path = result['path']
        cat = result.get('fileCategory', 'code')
        node_id = make_node_id(path, cat)

        if node_id in node_ids:
            continue

        node = {
            'id': node_id,
            'type': CATEGORY_TO_TYPE.get(cat, 'file'),
            'name': os.path.basename(path),
            'filePath': path,
            'summary': build_summary(result),
            'tags': build_tags(result),
            'language': result.get('language', 'unknown'),
            'complexity': 'simple' if result.get('totalLines', 0) < 100 else 'moderate' if result.get('totalLines', 0) < 300 else 'complex',
        }
        nodes.append(node)
        node_ids.add(node_id)

# Build import edges from batches.json import data
for batch in batches_data.get('batches', []):
    import_data = batch.get('batchImportData', {})
    for source_file, imports in import_data.items():
        source_id = make_node_id(source_file, file_meta.get(source_file, {}).get('fileCategory', 'code'))
        for imp in imports:
            if isinstance(imp, dict):
                target_path = imp.get('resolved', imp.get('source', ''))
            else:
                target_path = str(imp)
            # Try to find the target node
            target_id = None
            for nid in node_ids:
                if nid.endswith(f':{target_path}') or target_path in nid:
                    target_id = nid
                    break
            if target_id and source_id in node_ids:
                edges.append({
                    'id': f'edge:{source_id}:{target_id}:imports',
                    'source': source_id,
                    'target': target_id,
                    'type': 'imports',
                    'weight': 0.7,
                })

# Build contains edges for functions/classes within files
for bf in batch_files:
    if 'part' in bf:
        continue
    with open(bf, 'r', encoding='utf-8') as f:
        batch_result = json.load(f)

    for result in batch_result.get('results', []):
        path = result['path']
        cat = result.get('fileCategory', 'code')
        parent_id = make_node_id(path, cat)
        if parent_id not in node_ids:
            continue

        metrics = result.get('metrics', {})
        # Add function nodes
        for section in result.get('sections', []):
            heading = section.get('heading', '')
            if heading and heading not in ('imports', 'exports', 'from', 'class', 'def'):
                func_id = f'function:{path}:{heading}'
                if func_id not in node_ids:
                    func_node = {
                        'id': func_id,
                        'type': 'function',
                        'name': heading,
                        'filePath': path,
                        'summary': f'Function/section {heading} in {os.path.basename(path)}',
                        'tags': [result.get('language', 'unknown')],
                    }
                    nodes.append(func_node)
                    node_ids.add(func_id)
                    edges.append({
                        'id': f'edge:{parent_id}:{func_id}:contains',
                        'source': parent_id,
                        'target': func_id,
                        'type': 'contains',
                        'weight': 1.0,
                    })

# Deduplicate edges
seen_edges = set()
unique_edges = []
for e in edges:
    key = (e['source'], e['target'], e['type'])
    if key not in seen_edges:
        seen_edges.add(key)
        unique_edges.append(e)

# Write assembled graph
graph = {
    'nodes': nodes,
    'edges': unique_edges,
}

output_path = os.path.join(INTERMEDIATE, 'assembled-graph.json')
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(graph, f, indent=2, ensure_ascii=False)

print(f'Nodes: {len(nodes)}')
print(f'Edges: {len(unique_edges)}')
print(f'Output: {output_path}')
