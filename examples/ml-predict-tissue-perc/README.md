# Tissue detection in digital pathology slides

One possible way to use ProvStor is to load multiple Workflow Run RO-Crates[^1] corresponding to separate executions of the same workflow, with varying values of one or more input parameters, and run a query that shows how this affects the output.

In this example, a [CWL](https://www.commonwl.org/) workflow for the detection of tissue and tumor regions in prostate cancer digital pathology slides[^2] is run repeatedly on a Mirax test image, using increasing values of an input parameter. The [original workflow](https://github.com/crs4/deephealth-pipelines/tree/c54840df08742e3aa454394e0e74d15fbd640f07/cwl) has three steps:

1. detection of a low-resolution tissue region to select areas for further processing;
2. high-resolution tissue detection to refine borders;
3. high-resolution detection of tumor areas

The output consists of two arrays representing, respectively, the tissue and tumor likelihood for each pixel with an integer value between 0 and 99.

Here we add a fourth step (`get-metric`) that applies a threshold of 50 to the tissue array and computes the tissue percentage (`tissue_perc`) as the fraction of pixels whose value is equal to or above the threshold. The workflow file is `predictions.cwl`, which orchestrates the tool wrappers `extract_tissue.cwl`, `classify_tumor.cwl` and `get_metric.cwl`. All tools are made available to the workflow via Docker images.

To build the Docker image for the fourth step, run:

```
docker build . -t get_metric
```

To get the input data:

```
wget https://openslide.cs.cmu.edu/download/openslide-testdata/Mirax/Mirax2-Fluorescence-2.zip
unzip -d data Mirax2-Fluorescence-2.zip
```

To generate the RO-Crates:

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
bash gen_crates.sh
```

The `gen_crates.sh` script runs the workflow with increasing values of `tissue-high-level`, the magnification level of the high-resolution tissue detection phase, which is varied between 1 and 8. This generates 8 different crates with corresponding different values for the tissue percentage.

Now we need to load the crates to ProvStor. Run `deactivate` to leave the current virtual environment before switching to the ProvStor one (in the following we will assume this is at `../../venv`):

```
deactivate
source ../../venv/bin/activate
for i in $(seq 1 8); do provstor load ro-crate_${i}; done
provstor query query.txt
```

Alternatively, you can copy the query from `query.txt` and paste it into the Fuseki web UI (http://localhost:3030/#/dataset/ds/query if you have it running on localhost). The resulting table should show the workflow name on the first column, the tissue percentage on the second, and the input `tissue_high_level` on the third. Note that this result is made possible by the fact that the query runs on the merged graph that contains metadata from all 8 crates.


[^1]: Leo et al. (2024) "Recording provenance of workflow runs with RO-Crate". PLoS ONE 19(9): e0309210.

[^2]: Del Rio et al. (2022) "AI Support for Accelerating Histopathological Slide Examinations of Prostate Cancer in Clinical Studies". Image Analysis and Processing. ICIAP 2022 Workshops. ICIAP 2022. Lecture Notes in Computer Science 2022;13373.
