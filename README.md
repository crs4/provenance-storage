# CN-HPC Spoke 9 WP4: ProvStor provenance storage prototype

Store provenance data as an RDF graph.


## RO-Crate metadata storage with Apache Jena Fuseki

Fuseki docs: https://jena.apache.org/documentation/fuseki2


```
docker compose up
```

* Open http://localhost:3030 in a browser window to access the Fuseki web UI. The admin password is set in `docker-compose.yaml`.
* Open http://localhost:9001 to access the MinIO web UI. The username is `minio` and the password `miniosecret`
* Open http://localhost:8000/docs to access the FastAPI Swagger UI.

Switch to another terminal window.

Install the MinIO client command line tool `mc` following the [MinIO Quickstart](https://min.io/docs/minio/linux/reference/minio-mc.html#quickstart).

Create an alias:

```
mc alias set localstore http://localhost:9000 minio miniosecret
```

The above modifies `~/.mc/config.json`, so it does not need to be re-executed if you wipe out `minio-data`.


### Environment Configuration

On the server side, all environment variables are set in an `.env` file.
An example configuration is provided in `.env.example` (ports, database name, credentials, etc.).


### CLI configuration

Point the CLI to the API by editing `~/.config/provstor.config`, example:

```ini
[api]
host = localhost
port = 8000
```
With this setup, the CLI runs locally but executes operations on the remote server through the API.


#### Example usage
```
python3 -m venv venv
source venv/bin/activate
pip install -e .

provstor load tests/data/crate1
provstor load tests/data/crate2
provstor query tests/data/query.txt
```

## License

This code is distributed under the terms of the [GNU GPL-3.0 license](https://opensource.org/license/GPL-3.0).  See [COPYING](./COPYING) for details.


## Acknowledgements

This work has been partially funded by the [Italian Research Center on High Performance Computing, Big Data and Quantum Computing - Spoke
9](https://www.supercomputing-icsc.it/en/spoke-9-digital-society-smart-cities-en/).

## Copyright

Copyright © 2024-2025 [CRS4](https://www.crs4.it/)
