# CN-HPC Spoke 9 WP4: ProvStor provenance storage prototype

Store provenance data as an RDF graph.


## RO-Crate metadata storage with Apache Jena Fuseki

Fuseki docs: https://jena.apache.org/documentation/fuseki2


```
cp .env.example .env
docker compose up
```

* Open http://localhost:3030 in a browser window to access the Fuseki web UI. The username is `admin` and the password is `admin`.
* Open http://localhost:9001 to access the MinIO web UI. The username is `minioadmin` and the password `minioadmin`.
* Open http://localhost:8000/docs to access the FastAPI Swagger UI.

To change passwords and other configuration values, edit the `.env` file before running `docker compose up`.

Switch to another terminal window.

Install the MinIO client command line tool `mc` following the [MinIO Quickstart](https://min.io/docs/minio/linux/reference/minio-mc.html#quickstart).

Create an alias:

```
mc alias set localstore http://localhost:9000 minio miniosecret
```

The above modifies `~/.mc/config.json`, so it does not need to be re-executed if you wipe out `minio-data`.


### Environment Configuration

On the server side, all environment variables are set in an `.env` file.
An example configuration is provided in `.env.example`.


### Dev mode

```
docker compose -f docker-compose.yaml -f docker-compose-dev.yaml up
```


### CLI configuration

Point the CLI to the API by editing `~/.config/provstor.config`, example:

```ini
[api]
host = 10.130.131.41
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

#### Backtracking on chained Workflow Run RO-Crates

[Workflow Run RO-Crate](https://www.researchobject.org/workflow-run-crate/) (WRROC) is a set of RO-Crate [profiles](https://www.researchobject.org/ro-crate/specification/1.2/profiles.html) for capturing the provenance of the execution of computational workflows. Crates that follow the WRROC model use (subclasses of) [Action](https://schema.org/Action) to represent a workflow run, with [object](https://schema.org/object) and [result](https://schema.org/result) pointing, respectively, to the inputs and outputs. Such crates can be "chained" in the sense that the `result` of a workflow execution can be used as `object` in another run. One of the main uses of computational provenance information is the ability to follow the history of digital objects back to the original inputs from which the chain of computations started. ProvStor has a `backtrack` functionality that can be used for this purpose.

```
provstor load tests/data/provcrate1
provstor load tests/data/proccrate1
provstor load tests/data/proccrate2
provstor backtrack file:///path/to/FOOBAR123.deepvariant.ann.norm.vcf.gz
```

The RO-Crates loaded above describe a mock variant calling pipeline (provcrate1) followed by an annotation (proccrate1) and a normalization (proccrate2). The result of the normalization, `file:///path/to/FOOBAR123.deepvariant.ann.norm.vcf.gz`, is linked back to the inputs of the pipeline with the `backtrack` command, whose output consists of (action, objects, results) tuples.


## License

This code is distributed under the terms of the [GNU GPL-3.0 license](https://opensource.org/license/GPL-3.0).  See [COPYING](./COPYING) for details.


## Acknowledgements

This work has been partially funded by the [Italian Research Center on High Performance Computing, Big Data and Quantum Computing - Spoke
9](https://www.supercomputing-icsc.it/en/spoke-9-digital-society-smart-cities-en/).

## Copyright

Copyright © 2024-2026 [CRS4](https://www.crs4.it/) \
Copyright © 2025-2026 [BSC](https://www.bsc.es/)
