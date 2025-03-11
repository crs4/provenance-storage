# CN-HPC Spoke 9 WP4: ProvStor provenance storage prototype

Store provenance data as an RDF graph.


## RO-Crate metadata storage with Apache Jena Fuseki

Fuseki docs: https://jena.apache.org/documentation/fuseki2


```
mkdir fuseki-data minio-data
docker compose up
```

* Open http://localhost:3030 in a browser window to access the Fuseki web UI. The admin password is set in `docker-compose.yaml`.
* Open http://localhost:9001 to access the MinIO web UI. The username is `minio` and the password `miniosecret`

Switch to another terminal window.

Install the MinIO client command line tool `mc` following the [MinIO Quickstart](https://min.io/docs/minio/linux/reference/minio-mc.html#quickstart).

Create an alias:

```
mc alias set localstore http://localhost:9000 minio miniosecret
```

The above modifies `~/.mc/config.json`, so it does not need to be re-executed if you wipe out `minio-data`.

```
python3 -m venv venv
source venv/bin/activate
pip install -e .

provstor load crate1
provstor load crate2
provstor query query.txt
```

## License

This code is distributed under the terms of the [GNU GPL-3.0 license](https://opensource.org/license/GPL-3.0).  See [COPYING](./COPYING) for details.


## Acknowledgements

This work has been partially funded by the [Italian Research Center on High Performance Computing, Big Data and Quantum Computing - Spoke
9](https://www.supercomputing-icsc.it/en/spoke-9-digital-society-smart-cities-en/).

## Copyright

Copyright © 2024-2025 [CRS4](https://www.crs4.it/)
