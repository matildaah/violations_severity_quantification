# Quantifying the Severity of Conformance Violations.

This repository contains the implementation, evaluations and input data used to formalize the approach described in the master thesis: Quantifying the Severity of Conformance Violations.

### Running the approach
- Add the log in folder <code>input/logs</code> . Unzip first the *logs* folder.
- If a reference model is available, place it in <code>input/reference_model</code>. Otherwise, a process model using standard IMf will be discovered.  
- Update accordingly *log_event_key*  & *log_reference_model*, respectively with the log event key and yes/no depending on the availability of a reference process model.
- Run the approach using <code>run_evaluation.py</code>.

Output files with extracted violations and respective severity quantification degrees are generated in <code>results/evaluation</code>.

### Outline
- Violations dataset used for the training of classification models can be found here <code> results/filtered_violations_dataset.xlsx</code>.
- Results of the approach applied in the real-life event logs can be found in <code>results/evaluation</code>.
- Gold standard used for the qualitative analysis: <code> input/violations_golden_standard.xlsx </code> 
- Knowledge base of VAA activities along with the respective class annotations:  <code> input/value_added_activities.txt </code> 


To create another violations dataset from the BPMAI collection, create first the noisy logs for the selected process models by running <code>log_simulation.py</code>. Then run <code>violations_training.py</code>, by computing first the conformance checking alignments *compute_alignments_training()* and then extracting the respective conformance violations *extract_conf_violations()*.



