# provenance-storage

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
pip install -r requirements.txt

python load_crate.py crate1
python load_crate.py crate2
python query_store.py query.txt
```
