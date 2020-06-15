"""
Calibration task.

PYTHONPATH='.' \
luigi \
    --local-scheduler \
    --module tasks powerbi \
    --run-time 30 \
    --num-chains 3

"""
import luigi


class PowerBiUploadTask(luigi.Task):
    """
    Uploads the final PowerBI database to AWS S3
    """

    run_name = luigi.Parameter()

    def requires(self):
        return [PowerBiConvertTask(run_name=self.run_name)]

    def output(self):
        return []

    def run(self):
        pass


class PowerBiConvertTask(luigi.Task):
    """
    Uploads the final PowerBI database to AWS S3
    """

    run_name = luigi.Parameter()

    def requires(self):
        """
        Depends on all chains
        """
        return [PowerBiConvertTask(run_name=self.run_name)]

    def output(self):
        return []

    def run(self):
        pass


class ChainTask(luigi.Task):
    """
    Runs a single calibration chain
    """

    chain_idx = luigi.Parameter()
    run_time = luigi.IntParameter()

    def run(self):
        pass

    def output(self):
        pass

    def output(self):
        return luigi.LocalTarget("data/artist_streams_%s.tsv" % self.date_interval)
