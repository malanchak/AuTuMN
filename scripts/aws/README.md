# AWS Calibration

These scripts allow you to run AuTuMN calibrations in AWS.

```
# Ensure aws requirements are installed
cd aws
pip install -r infra/requirements.txt

# Access command line tool
python -m infra

# Run calibration, first argument is a job name to refer to the job.
python -m run calibrate job1 malaysia 30 3600

# The calibration will print a "run name", which refers to the results,
# eg. malaysia-1590992312-master-b7ddb47361e6eda87bf05a18405f208ff5e3f2b0

# Run the full models for a given calibration run and burn in
python -m run full job2 malaysia-1590992312-master-b7ddb47361e6eda87bf05a18405f208ff5e3f2b0 10

# Finally, generate a PowerBI database from the full model runs
python -m run powerbi job3 malaysia-1590992312-master-b7ddb47361e6eda87bf05a18405f208ff5e3f2b0
```

## Calibration stages

There are several steps required to run a calibration and then prepare the final results for PowerBI.

### Step 1 - Calibration

Here we calibrate the parameters of the baseline model using MCMC over a time period from the model's start time to a calibration-specific end time.
The parameters required are:

- Which model to calibrate (eg. COVID Malaysia)
- How many MCMC chains to run (eg. 30)
- How many seconds to run the calibration for (eg. 3 hours = 10800 seconds)

This calibration is run on a single cloud computer (AWS EC2) in parallel. A separate database is produced for each calibration chain and stored in
cloud object storage (AWS S3 s3://autumn-data) under a "run name" which has the format {model_name}-{timestamp}-{git_branch}-{git_hash}.
Each calibration chain database is an SQLite file with the tables:

- mcmc_run: log of each MCMC iteration including parameter values, loglikelihood and run acceptance
- outputs: time series of each compartment for each model run
- derived_outputs: time series of post-processed data for each model run

Once the calibration is finished, the MCMC chain databases can be downloaded from S3 and viewed locally to determine the appropriate chain burn-in.

### Step 2 - Full model runs

Here we apply burn-in to each chain and then re-run the model for each accepted run. The mode is run over the baseline parameters and all scenarios. The models are run from the start time to the end time. The required parameters are:

- Run name (from step 1)
- Burn in (eg. 100 chains)

The resulting databases are stored in S3 with the same database format as in stage 1.

### Step 3 - Post processing

Here we use the full model runs to produce a single output database file to be uploaded to PowerBI.
The required parameters are:

- Run name (from step 1)
- Step 2 must have been run already

This step pulls down and uses the "full model run" databases from step 2.
The following steps are taken:

- For each chain database, the "outputs" table is unpivoted into the "pbi_outputs" table, and the "outputs" table is deleted; then
- All chain databases are collated into a single database file, with run idxs renamed so that they monotonically increase
- The "uncertainty" table is added, containting percentile uncertainty values for some derived outputs
- Runs are pruned from some tables ("pbi_outputs", "derived_outputs") so that only the MLE runs are kept
- The final database is uploaded to object storage, where it can be accessed and uploaded to PowerBI
