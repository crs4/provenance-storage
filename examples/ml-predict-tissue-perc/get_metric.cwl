cwlVersion: v1.1
class: CommandLineTool
requirements:
  InlineJavascriptRequirement: {}
  DockerRequirement:
    dockerPull: get_metric

inputs:
  tissue_array:
    type: File
    inputBinding:
      position: 1

outputs:
  tissue_perc:
    type: float
    outputBinding:
      glob: output.txt
      loadContents: true
      outputEval: $(parseFloat(self[0].contents.trim()))

stdout: output.txt
