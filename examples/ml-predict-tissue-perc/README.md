Original workflow from: https://github.com/crs4/deephealth-pipelines/tree/c54840df08742e3aa454394e0e74d15fbd640f07/cwl

```
docker build . -t get_metric

wget https://openslide.cs.cmu.edu/download/openslide-testdata/Mirax/Mirax2-Fluorescence-2.zip
unzip -d data Mirax2-Fluorescence-2.zip

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
bash gen_crates.sh
```
