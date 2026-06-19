import os
import sys
import zipfile
import tempfile
import json
import shutil
from PIL import Image

def save_file(pj_name ,path, image, content):
    json_ready = json.dumps(content)
    temp_path = tempfile.mkdtemp()

    try:
        with open(os.path.join(temp_path, 'content.json'), 'w') as f:
            f.write(json_ready)
            image.save(os.path.join(temp_path, f'{pj_name}.tga'))
       
        if os.path.isdir(path):
            path = os.path.join(path, f"{pj_name}.mipj")
            
        with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_BZIP2, compresslevel=9) as zipf:
            for root, dirs, files in os.walk(temp_path):
                for file in files:
                    zipf.write(os.path.join(root, file), arcname=file)
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


def open_file(path):
    global image, settings
    image = None
    settings = None
    with zipfile.ZipFile(path, 'r') as zippu:
        for file in zippu.namelist():
            if file.endswith('.tga'):
                image = Image.open(zippu.open(file))

            if file.endswith('.json'):
                settings = json.load(zippu.open(file))


    return image, settings