import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from bundle_openapi import bundle


def on_post_build(config):
    docs_dir = os.path.join(config['docs_dir'], 'api')
    output_path = os.path.join(config['site_dir'], 'api', 'openapi.yaml')
    bundle(docs_dir, output_path)
