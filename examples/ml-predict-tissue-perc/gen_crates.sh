set -euo pipefail

for i in $(seq 1 8); do
    sed -i -e "s/^tissue-high-level:.*$/tissue-high-level: ${i}/" params.yaml
    grep tissue-high-level params.yaml
    cwltool --provenance ro_${i} predictions.cwl params.yaml
    runcrate convert ro_${i} -o ro-crate_${i}
done
