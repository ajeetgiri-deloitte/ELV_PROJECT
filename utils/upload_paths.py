# utils/upload_paths.py

import uuid
import os

# Registry to hold generated functions
upload_path_registry = {}

def get_unique_upload_path(folder, prefix):
    key = f"{folder}_{prefix}".replace('/', '_')
    func_name = f"upload_path_{key}"

    if func_name not in upload_path_registry:
        def upload_func(instance, filename):
            ext = filename.split('.')[-1]
            unique_id = uuid.uuid4().hex[:8]
            new_filename = f"{prefix}_{unique_id}.{ext}"
            return os.path.join(folder, new_filename)

        upload_func.__name__ = func_name  # give the function a real name
        upload_path_registry[func_name] = upload_func

    return upload_path_registry[func_name]
