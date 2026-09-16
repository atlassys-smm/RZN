import yaml
import os


def resolve_refs(obj, base_dir, root_dir, resolving=None):
    if resolving is None:
        resolving = set()

    if isinstance(obj, dict):
        if '$ref' in obj and isinstance(obj['$ref'], str):
            ref = obj['$ref']

            # Don't resolve refs to components/schemas — leave them as-is
            if '#/components/schemas/' in ref:
                return obj

            if not ref.startswith('#') and not ref.startswith('http'):
                parts = ref.split('#', 1)
                file_path = parts[0]
                json_pointer = parts[1] if len(parts) > 1 else None

                full_path = os.path.normpath(os.path.join(base_dir, file_path))

                if full_path in resolving:
                    return obj

                resolving.add(full_path)
                try:
                    with open(full_path, encoding='utf-8') as f:
                        content = yaml.safe_load(f)

                    if json_pointer:
                        for key in json_pointer.strip('/').split('/'):
                            content = content[key]

                    return resolve_refs(content, os.path.dirname(full_path), root_dir, resolving)
                finally:
                    resolving.discard(full_path)
        return {k: resolve_refs(v, base_dir, root_dir, resolving) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [resolve_refs(item, base_dir, root_dir, resolving) for item in obj]
    return obj


def bundle(docs_dir, output_path):
    with open(os.path.join(docs_dir, 'openapi.yaml'), encoding='utf-8') as f:
        spec = yaml.safe_load(f)

    resolved = resolve_refs(spec, docs_dir, docs_dir)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(resolved, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
