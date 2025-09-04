import os


DEFAULT_ENV_VARS = {
    "MINIO_STORE": "minio:9000",
    "MINIO_USER": "minio",
    "MINIO_SECRET": "miniosecret",
    "MINIO_BUCKET": "crates",
    "FUSEKI_BASE_URL": "http://fuseki:3030",
    "FUSEKI_DATASET": "ds",
}


def load_env_vars():
    """\
    Sets module-level variables according to configuration files. If no
    configuration files are present, the variables are set to the fallback
    values.
    """
    g = globals()
    for key, value in DEFAULT_ENV_VARS.items():
        g[key] = os.environ.get(key, value)


load_env_vars()
